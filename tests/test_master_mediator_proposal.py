"""Tests for master_mediator/proposal.py — the Master's spine-update capsule
generation (consumer/ccemk2/ROADMAP.md Part II, Phase 20).
"""
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from master_mediator.classifier import TIER_CANDIDATE, TIER_FACT, MaturityFinding  # noqa: E402
from master_mediator.proposal import build_spine_update_capsule, export_proposal  # noqa: E402

_SCP_ID_RE = re.compile(r"^[a-z0-9-]+(?:/[a-z0-9-]+)*-v[0-9]+$")
_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _fact_finding(field_key=("domain.trading.btc", "FACT")):
    return MaturityFinding(
        declaration_type="usage_digest", field_key=field_key, tier=TIER_FACT,
        consumers=["ccemk2", "lifeforge", "cobblewright"], total_observation_count=5000, max_age_days=120.0,
    )


def test_build_spine_update_capsule_has_ratified_scp_id_and_shape():
    capsule = build_spine_update_capsule(_fact_finding())
    assert _SCP_ID_RE.match(capsule["scp_id"])
    assert _ISO_UTC_RE.match(capsule["created"])
    assert capsule["declaration"]["type"] == "spine_update_proposal"
    assert capsule["declaration"]["evidence"]["tier"] == "Fact"
    assert capsule["declaration"]["evidence"]["consumers"] == ["ccemk2", "lifeforge", "cobblewright"]
    assert capsule["signature"] is None


def test_build_spine_update_capsule_rejects_non_fact_findings():
    candidate = MaturityFinding(
        declaration_type="usage_digest", field_key=("x", "FACT"), tier=TIER_CANDIDATE,
        consumers=["ccemk2"], total_observation_count=150, max_age_days=40.0,
    )
    try:
        build_spine_update_capsule(candidate)
        assert False, "expected ValueError for a non-Fact finding"
    except ValueError:
        pass


def test_scp_id_slugifies_field_keys_with_illegal_characters():
    """Real field keys contain dots/colons (namespaces, entity_class
    pairs) — must not break the ratified scp_id pattern."""
    capsule = build_spine_update_capsule(_fact_finding(field_key=("domain.trading.btc", "FACT")))
    assert "." not in capsule["scp_id"]
    assert _SCP_ID_RE.match(capsule["scp_id"])


def test_export_proposal_writes_schema_valid_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        sc_dir = Path(tmpdir) / "sc" / "mediator"
        path = export_proposal(_fact_finding(), sc_dir)
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert _SCP_ID_RE.match(data["scp_id"])
        assert data["declaration"]["type"] == "spine_update_proposal"
