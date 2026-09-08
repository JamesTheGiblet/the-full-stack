"""Keystone Gate's Sub-Mediator digest — the second real pilot of the
Mediator telemetry contract (consumer/ccemk2/ROADMAP.md Part II, Phase
20), proving the pattern generalizes beyond CCE's stack.

Keystone Gate has no Pydantic/`ScEnvelope` machinery (it's pure stdlib —
see keystone_gate/core.py, keystone_gate/primitives.py) and doesn't need
any: "the consumer need only have what it requires." This builds the
same real `.sc.json` envelope shape as a plain dict, using only
`forge_core` (already a shared, pure-stdlib-plus-cryptography package)
for the ratified scp_id/created rules — no new dependency introduced.

Digest source: `capsule_primitives.json` (via PrimitiveManager) — the
living field vocabulary every capsule processed through the gate
contributes to. Its own schema (`{type, first_seen, count}` per field
path) is already almost exactly Mediator's field-usage shape; this
module just wraps it, not reinvents it. Read-only: never calls
`PrimitiveManager.save()` or otherwise mutates the vocabulary.
"""
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import forge_core

SCP_ID = "keystone-gate/mediator/primitive-digest-v1"
# Correction (2026-09-08): governance-v6 was ratified 2026-08-10, before
# this digest was ever first signed — "-v1" was never actually current
# for this capsule (the CCE copy of this same constant had the identical
# bug, from the same unverified-latest-version assumption).
GOVERNANCE_INHERITS = "forge-stack/governance-v6"


@dataclass(frozen=True)
class PrimitiveUsage:
    field_path: str
    field_type: str
    first_seen: str
    observation_count: int


def _reformat_first_seen(raw: str) -> str:
    """capsule_primitives.json's own first_seen values come from
    primitives.py's _utc_now() (datetime.isoformat() + "Z"), which
    includes microseconds — not the ratified strict
    YYYY-MM-DDTHH:MM:SSZ format (forge_core.ISO_UTC_RE has no fractional
    seconds). Reformat rather than pass through raw, so every timestamp
    in the exported digest is genuinely ratified-compliant, not just the
    envelope's own top-level created/generated_at fields. datetime's own
    fromisoformat (not forge_core.parse_iso_utc, which rejects this exact
    non-strict shape by design) handles the "Z" suffix from Python 3.11+;
    this repo's root venv is 3.9, so "Z" is swapped for "+00:00" first."""
    if not raw:
        return forge_core.format_iso_utc(datetime.now(timezone.utc))
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return forge_core.format_iso_utc(datetime.now(timezone.utc))
    return forge_core.format_iso_utc(parsed)


def compute_primitive_usage(primitive_file: Path) -> List[PrimitiveUsage]:
    """Read capsule_primitives.json directly rather than going through
    PrimitiveManager: this is a read-only reporting concern, not part of
    the gate's own validation path, and avoids taking a dependency from
    mediator/ back into keystone_gate/ for a single JSON read."""
    primitive_file = Path(primitive_file)
    if not primitive_file.exists():
        return []
    try:
        data = json.loads(primitive_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [
        PrimitiveUsage(
            field_path=field_path,
            field_type=meta.get("type", "unknown"),
            first_seen=_reformat_first_seen(meta.get("first_seen", "")),
            observation_count=meta.get("count", 0),
        )
        for field_path, meta in data.items()
    ]


def build_digest_envelope(consumer: str, usages: List[PrimitiveUsage]) -> dict:
    """A plain dict matching the real .sc.json envelope shape exactly —
    no Pydantic needed for a structure this simple. scp_id uses
    "keystone-gate" (hyphenated), not the package's own "keystone_gate"
    (underscored): the ratified scp_id pattern
    (forge_core.SCP_ID_RE, mirroring sign.py's SCP_ID_RE) only allows
    a-z/0-9/hyphen per segment — the existing
    consumer/keystone_gate/build_loop/sc/step-spec-v1.sc.json capsule
    already fails the shared root schema gate for exactly this reason
    (uses the underscored form); this digest deliberately doesn't repeat
    that mistake."""
    assert forge_core.SCP_ID_RE.match(SCP_ID), f"generated scp_id fails the ratified format: {SCP_ID!r}"
    now = datetime.now(timezone.utc)
    return {
        "scp_id": SCP_ID,
        "scp_version": "1.2.0",
        "created": forge_core.format_iso_utc(now),
        "inherits": GOVERNANCE_INHERITS,
        "declaration": {
            "type": "primitive_digest",
            "consumer": consumer,
            "generated_at": forge_core.format_iso_utc(now),
            "fields": [
                {
                    "field_path": usage.field_path,
                    "field_type": usage.field_type,
                    "first_seen": usage.first_seen,
                    "observation_count": usage.observation_count,
                }
                for usage in usages
            ],
        },
        "licence": "MSL-1.0",
        "signature": None,
    }


def export_digest(primitive_file: Path, sc_export_dir: Path, consumer: str = "keystone_gate") -> Path:
    """Compute, wrap, and export Keystone Gate's current primitive-usage
    digest as consumer/keystone_gate/sc/*.sc.json — the same file
    convention every other consumer's stable capsules use."""
    usages = compute_primitive_usage(primitive_file)
    envelope = build_digest_envelope(consumer, usages)

    sc_export_dir = Path(sc_export_dir)
    sc_export_dir.mkdir(parents=True, exist_ok=True)
    filename = envelope["scp_id"].rsplit("/", 1)[-1] + ".sc.json"
    path = sc_export_dir / filename
    path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
