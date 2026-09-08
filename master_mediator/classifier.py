"""Master Mediator — maturity classifier. consumer/ccemk2/ROADMAP.md
Part II, Phase 20's field/namespace track: a real algorithm with
concrete thresholds, not a judgment call (Decision 2).

Every real digest type built so far uses a different container key and
field-name for the same underlying concepts (a usage entry's key
dimension, its occurrence count, its first-seen timestamp) —
DIGEST_SPECS normalizes that here, rather than forcing one universal
shape onto every consumer's producer. A new consumer's new digest type
needs one new entry in this registry, not a change to how it already
reports.

Cross-consumer tiers (Emergent, Fact) only ever compare observations
that share the same declaration_type: CCE's (namespace, lens) key space
and Keystone Gate's field_path key space are different universes of
meaning, and nothing here pretends otherwise by matching across them.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import forge_core

# declaration.type -> where to find its usage entries and how to read them.
DIGEST_SPECS: Dict[str, Dict[str, Any]] = {
    "usage_digest": {
        "list_key": "fields", "key_fields": ("namespace", "lens"), "count_field": "observation_count",
    },
    "chronoscribe_digest": {
        "list_key": "event_types", "key_fields": ("event_type",), "count_field": "observation_count",
    },
    "leighton_digest": {
        "list_key": "entities", "key_fields": ("entity_id",), "count_field": "observation_count",
    },
    "hal_digest": {
        "list_key": "seals", "key_fields": ("entity_class", "tier"), "count_field": "seal_count",
    },
    "primitive_digest": {
        "list_key": "fields", "key_fields": ("field_path",), "count_field": "observation_count",
    },
}

TIER_HYPOTHESIS = "Hypothesis"
TIER_EXPERIMENTAL = "Experimental"
TIER_CANDIDATE = "Candidate"
TIER_EMERGENT = "Emergent"
TIER_FACT = "Fact"


@dataclass(frozen=True)
class FieldObservation:
    consumer: str
    declaration_type: str
    field_key: Tuple[str, ...]
    observation_count: int
    age_days: float


@dataclass(frozen=True)
class MaturityFinding:
    declaration_type: str
    field_key: Tuple[str, ...]
    tier: str
    consumers: List[str]
    total_observation_count: int
    max_age_days: float


def _age_days(first_seen: str, now: datetime) -> float:
    """Tolerant of a missing/malformed first_seen (treated as age 0, the
    conservative choice — an unparsable timestamp should never itself
    inflate a field's maturity tier) rather than raising and losing every
    other, well-formed observation in the same digest."""
    if not first_seen:
        return 0.0
    try:
        dt = forge_core.parse_iso_utc(first_seen)
    except ValueError:
        return 0.0
    return max(0.0, (now - dt).total_seconds() / 86400.0)


def extract_observations(digests: List[Dict[str, Any]], now: datetime = None) -> List[FieldObservation]:
    """Flatten every discovered digest's usage entries into one list of
    per-field observations, skipping unknown declaration types and
    malformed entries rather than failing the whole scan for one bad
    consumer."""
    now = now or datetime.now(timezone.utc)
    observations: List[FieldObservation] = []
    for digest in digests:
        decl = digest.get("declaration", {})
        decl_type = decl.get("type")
        spec = DIGEST_SPECS.get(decl_type)
        if spec is None:
            continue
        consumer = decl.get("consumer", "unknown")
        for entry in decl.get(spec["list_key"], []):
            try:
                key = tuple(str(entry[k]) for k in spec["key_fields"])
                count = int(entry.get(spec["count_field"], 0))
            except (KeyError, TypeError, ValueError):
                continue
            observations.append(FieldObservation(
                consumer=consumer,
                declaration_type=decl_type,
                field_key=key,
                observation_count=count,
                age_days=_age_days(entry.get("first_seen", ""), now),
            ))
    return observations


def _classify_one(
    declaration_type: str, field_key: Tuple[str, ...], group: List[FieldObservation],
) -> MaturityFinding:
    consumers = sorted({obs.consumer for obs in group})
    total_count = sum(obs.observation_count for obs in group)
    max_age = max(obs.age_days for obs in group)
    n_consumers = len(consumers)

    if n_consumers >= 3 or (n_consumers >= 2 and max_age >= 90):
        tier = TIER_FACT
    elif n_consumers >= 2 and max_age >= 30:
        tier = TIER_EMERGENT
    elif total_count >= 100 and max_age >= 30:
        tier = TIER_CANDIDATE
    elif total_count >= 10 and max_age >= 7:
        tier = TIER_EXPERIMENTAL
    else:
        tier = TIER_HYPOTHESIS

    return MaturityFinding(
        declaration_type=declaration_type,
        field_key=field_key,
        tier=tier,
        consumers=consumers,
        total_observation_count=total_count,
        max_age_days=round(max_age, 2),
    )


def classify(observations: List[FieldObservation]) -> List[MaturityFinding]:
    """Group observations by (declaration_type, field_key) — never across
    declaration types, per this module's docstring — and classify each
    group's maturity tier per the thresholds in
    consumer/ccemk2/ROADMAP.md Part II, Phase 20."""
    groups: Dict[Tuple[str, Tuple[str, ...]], List[FieldObservation]] = {}
    for obs in observations:
        groups.setdefault((obs.declaration_type, obs.field_key), []).append(obs)

    return [
        _classify_one(decl_type, field_key, group)
        for (decl_type, field_key), group in groups.items()
    ]
