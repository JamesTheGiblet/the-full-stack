"""Master Mediator — spine-update capsule generation
(consumer/ccemk2/ROADMAP.md Part II, Phase 20's "Master Mediator — Spine
Update Capsule + HAL Negotiation").

Builds the signed proposal a Fact-tier finding (or a lens proposal)
generates — evidence, lineage, and the concrete spine files it would
affect — as a real, ratified-format .sc.json capsule, the same shape
every other stable artifact in this repo uses. Does NOT apply anything:
per Decision 5, ratifying this capsule (once HAL approves) is a manual,
human-driven edit to datacube.py/docs/scp-spec-v1.2.md/etc. — this
module's job ends at "here is the proposal," not "here is the merge."
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import forge_core

from master_mediator.classifier import MaturityFinding

GOVERNANCE_INHERITS = "forge-stack/governance-v1"


def _proposal_scp_id(finding: MaturityFinding) -> str:
    """Slug the field key into the ratified a-z0-9-/ alphabet — field
    keys come from consumer data (namespaces, entity classes, field
    paths) and may contain characters the shared root schema gate
    rejects (dots, colons, underscores), so this is a real transform,
    not just a join."""
    def _slug(part: str) -> str:
        return "".join(c if c.isalnum() else "-" for c in part.lower()).strip("-") or "field"

    key_slug = "-".join(_slug(part) for part in finding.field_key)
    type_slug = _slug(finding.declaration_type)
    return f"forge-stack/mediator/spine-update-{type_slug}-{key_slug}-v1"


def build_spine_update_capsule(finding: MaturityFinding) -> Dict[str, Any]:
    """A real, ratified-format .sc.json capsule proposing a Fact-tier
    field for spine inclusion. Unsigned (signature: null) — same
    honesty-over-convenience choice every other digest producer this
    session built makes; HAL approval and a human's deliberate
    re-signing come first."""
    if finding.tier != "Fact":
        raise ValueError(f"only Fact-tier findings warrant a spine-update proposal, got {finding.tier!r}")

    scp_id = _proposal_scp_id(finding)
    assert forge_core.SCP_ID_RE.match(scp_id), f"generated scp_id fails the ratified format: {scp_id!r}"
    now = forge_core.format_iso_utc(datetime.now(timezone.utc))

    return {
        "scp_id": scp_id,
        "scp_version": "1.2.0",
        "created": now,
        "inherits": GOVERNANCE_INHERITS,
        "declaration": {
            "type": "spine_update_proposal",
            "intent": (
                f"Promote {finding.declaration_type}'s field {list(finding.field_key)!r} to spine-recognized "
                f"status: observed across {len(finding.consumers)} consumer(s) "
                f"({', '.join(finding.consumers)}) for {finding.max_age_days:.0f} days, "
                f"{finding.total_observation_count} total observations."
            ),
            "evidence": {
                "declaration_type": finding.declaration_type,
                "field_key": list(finding.field_key),
                "consumers": finding.consumers,
                "total_observation_count": finding.total_observation_count,
                "max_age_days": finding.max_age_days,
                "tier": finding.tier,
            },
            "affected_spine_files": [
                "datacube.py (NAMESPACES/LENSES, if this field represents a new namespace or lens)",
                "docs/scp-spec-v1.2.md (if this changes the ratified schema)",
            ],
        },
        "licence": "MSL-1.0",
        "signature": None,
    }


def export_proposal(finding: MaturityFinding, sc_dir: Path) -> Path:
    """Write the proposal as forge-stack/sc/mediator/*.sc.json — the same
    file convention every other stable capsule in this repo uses, so
    it's discoverable by the same sign.py/ledger.py tooling once a human
    reviews and signs it."""
    capsule = build_spine_update_capsule(finding)
    sc_dir = Path(sc_dir)
    sc_dir.mkdir(parents=True, exist_ok=True)
    filename = capsule["scp_id"].rsplit("/", 1)[-1] + ".sc.json"
    path = sc_dir / filename
    path.write_text(json.dumps(capsule, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
