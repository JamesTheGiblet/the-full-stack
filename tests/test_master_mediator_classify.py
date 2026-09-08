"""Tests for the Master Mediator (master_mediator/discovery.py,
master_mediator/classifier.py) — consumer/ccemk2/ROADMAP.md Part II,
Phase 20's "Master Mediator — Maturity Classifier."
"""
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from master_mediator.classifier import (  # noqa: E402
    TIER_CANDIDATE,
    TIER_EMERGENT,
    TIER_EXPERIMENTAL,
    TIER_FACT,
    TIER_HYPOTHESIS,
    FieldObservation,
    classify,
    extract_observations,
)
from master_mediator.discovery import find_digest_paths, load_digests  # noqa: E402


def _write_capsule(sc_dir: Path, name: str, decl_type: str, extra_decl: dict = None):
    sc_dir.mkdir(parents=True, exist_ok=True)
    body = {
        "scp_id": f"test/{name}-v1",
        "created": "2026-01-01T00:00:00Z",
        "declaration": {"type": decl_type, "consumer": "test-consumer", **(extra_decl or {})},
        "signature": None,
    }
    (sc_dir / f"{name}.sc.json").write_text(json.dumps(body), encoding="utf-8")


# --- discovery ---

def test_find_digest_paths_filters_by_declaration_type_suffix():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _write_capsule(root / "consumer" / "a" / "sc", "usage-digest", "usage_digest")
        _write_capsule(root / "consumer" / "a" / "sc", "some-ruleset", "ruleset")
        found = find_digest_paths(root)
        assert len(found) == 1
        assert found[0].name == "usage-digest.sc.json"


def test_find_digest_paths_skips_malformed_json_without_crashing():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        sc_dir = root / "consumer" / "a" / "sc"
        sc_dir.mkdir(parents=True)
        (sc_dir / "broken.sc.json").write_text("not valid json{{{", encoding="utf-8")
        _write_capsule(sc_dir, "usage-digest", "usage_digest")
        found = find_digest_paths(root)
        assert len(found) == 1


def test_load_digests_returns_parsed_dicts_with_source_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _write_capsule(root / "consumer" / "a" / "sc", "usage-digest", "usage_digest")
        digests = load_digests(root)
        assert len(digests) == 1
        assert digests[0]["declaration"]["type"] == "usage_digest"
        assert "_source_path" in digests[0]


def test_discovery_finds_real_digests_in_the_actual_repo():
    """The real proof: run discovery against the actual repo root, not a
    synthetic fixture."""
    digests = load_digests(ROOT)
    consumers = {d["declaration"].get("consumer") for d in digests}
    assert "ccemk2" in consumers
    assert "keystone_gate" in consumers
    decl_types = {d["declaration"]["type"] for d in digests}
    assert {"usage_digest", "chronoscribe_digest", "leighton_digest", "hal_digest", "primitive_digest"} <= decl_types


# --- classifier: extract_observations ---

def test_extract_observations_reads_usage_digest_shape():
    digests = [{
        "declaration": {
            "type": "usage_digest", "consumer": "ccemk2",
            "fields": [{"namespace": "domain.trading.btc", "lens": "FACT", "observation_count": 50, "first_seen": "2026-01-01T00:00:00Z"}],
        },
    }]
    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    obs = extract_observations(digests, now=now)
    assert len(obs) == 1
    assert obs[0].consumer == "ccemk2"
    assert obs[0].field_key == ("domain.trading.btc", "FACT")
    assert obs[0].observation_count == 50
    assert obs[0].age_days == 31.0


def test_extract_observations_reads_hal_digest_seal_count_field():
    """hal_digest uses "seal_count", not "observation_count" — the real
    naming inconsistency DIGEST_SPECS exists to paper over correctly."""
    digests = [{
        "declaration": {
            "type": "hal_digest", "consumer": "ccemk2",
            "seals": [{"entity_class": "se", "tier": 3, "seal_count": 4, "distinct_entities": 1, "first_seen": "2026-01-01T00:00:00Z"}],
        },
    }]
    obs = extract_observations(digests)
    assert obs[0].field_key == ("se", "3")
    assert obs[0].observation_count == 4


def test_extract_observations_skips_unknown_declaration_type():
    digests = [{"declaration": {"type": "some_future_digest", "consumer": "x", "items": []}}]
    assert extract_observations(digests) == []


def test_extract_observations_skips_malformed_entries_without_crashing():
    digests = [{
        "declaration": {
            "type": "usage_digest", "consumer": "ccemk2",
            "fields": [
                {"namespace": "ok", "lens": "FACT", "observation_count": 5, "first_seen": "2026-01-01T00:00:00Z"},
                {"namespace": "broken"},  # missing lens, observation_count
            ],
        },
    }]
    obs = extract_observations(digests)
    assert len(obs) == 1
    assert obs[0].field_key == ("ok", "FACT")


def test_extract_observations_tolerates_malformed_first_seen():
    digests = [{
        "declaration": {
            "type": "usage_digest", "consumer": "ccemk2",
            "fields": [{"namespace": "ok", "lens": "FACT", "observation_count": 5, "first_seen": "not a date"}],
        },
    }]
    obs = extract_observations(digests)
    assert obs[0].age_days == 0.0


# --- classifier: classify tiers ---

def _obs(consumer, decl_type, key, count, age_days):
    return FieldObservation(consumer=consumer, declaration_type=decl_type, field_key=key, observation_count=count, age_days=age_days)


def test_classify_hypothesis_tier_low_count_and_young():
    findings = classify([_obs("a", "usage_digest", ("ns", "FACT"), 3, 1)])
    assert findings[0].tier == TIER_HYPOTHESIS


def test_classify_experimental_tier():
    findings = classify([_obs("a", "usage_digest", ("ns", "FACT"), 15, 10)])
    assert findings[0].tier == TIER_EXPERIMENTAL


def test_classify_candidate_tier():
    findings = classify([_obs("a", "usage_digest", ("ns", "FACT"), 150, 35)])
    assert findings[0].tier == TIER_CANDIDATE


def test_classify_emergent_tier_needs_two_consumers_and_thirty_days():
    findings = classify([
        _obs("a", "usage_digest", ("ns", "FACT"), 150, 35),
        _obs("b", "usage_digest", ("ns", "FACT"), 20, 35),
    ])
    assert findings[0].tier == TIER_EMERGENT
    assert findings[0].consumers == ["a", "b"]


def test_classify_two_consumers_but_too_young_is_not_yet_emergent():
    """2 consumers isn't enough on its own — Emergent also needs
    max_age >= 30d (not met here, age=10), and falling through to
    Candidate needs its own age >= 30d too (also not met) — so this
    correctly resolves to whatever tier the count/age qualifies for
    regardless of consumer count, not a special "almost emergent" tier."""
    findings = classify([
        _obs("a", "usage_digest", ("ns", "FACT"), 150, 10),
        _obs("b", "usage_digest", ("ns", "FACT"), 20, 10),
    ])
    assert findings[0].tier == TIER_EXPERIMENTAL


def test_classify_fact_tier_three_consumers():
    findings = classify([
        _obs("a", "usage_digest", ("ns", "FACT"), 50, 40),
        _obs("b", "usage_digest", ("ns", "FACT"), 50, 40),
        _obs("c", "usage_digest", ("ns", "FACT"), 50, 40),
    ])
    assert findings[0].tier == TIER_FACT


def test_classify_fact_tier_two_consumers_ninety_days():
    findings = classify([
        _obs("a", "usage_digest", ("ns", "FACT"), 50, 95),
        _obs("b", "usage_digest", ("ns", "FACT"), 50, 95),
    ])
    assert findings[0].tier == TIER_FACT


def test_classify_never_merges_across_declaration_types():
    """The real design point this whole registry exists for: CCE's
    (namespace, lens) key space and Keystone Gate's field_path key space
    are different universes of meaning — even an accidentally identical
    field_key tuple must not merge across declaration_type."""
    findings = classify([
        _obs("ccemk2", "usage_digest", ("same", "key"), 200, 100),
        _obs("keystone_gate", "primitive_digest", ("same", "key"), 200, 100),
    ])
    assert len(findings) == 2
    assert all(f.tier != TIER_FACT for f in findings)  # each is single-consumer within its own type


def test_classify_real_repo_data_has_no_false_emergent_or_fact_findings():
    """The honest real-data proof: CCE and Keystone Gate report
    completely different declaration types today, so nothing should have
    reached Emergent/Fact yet — asserting this stays true guards against
    ever silently merging across those two different universes of
    meaning."""
    digests = load_digests(ROOT)
    observations = extract_observations(digests)
    findings = classify(observations)
    assert any(f.declaration_type == "usage_digest" for f in findings)
    assert any(f.declaration_type == "primitive_digest" for f in findings)
    assert not any(f.tier in (TIER_EMERGENT, TIER_FACT) for f in findings)
