"""Hardening 6.7 — the six-stage spine (James, 2026-11-17).

Written before the documents and capsules, and run red first.

The ratified glossary (docs/glossary.md, 2026-08-08) gives five stages;
James's identity capsule gives six, adding Decide (RuleEngine / ruleset),
and says "all five original stages" were implemented on 2026-08-08.
James chose to ratify six (audit architectural-gaps-v1, spine-stage-count).

S1  docs/glossary-v2.md is a new document; docs/glossary.md is unchanged
    and still matches the hash governance-v7 and v8 pin.
S2  glossary-v2 gives six stages in order, Decide third, RuleEngine /
    ruleset in the symmetry, and records that August verified five.
S3  sc/glossary-v2.sc.json pins glossary-v2 and supersedes glossary-v1.
S4  governance-v9 keeps every v8 constraint, pins glossary-v2 as the
    terminology authority, and adds the spine constraint.
S5  manifest-v13 witnesses governance-v9, with glossary-v2 in place of
    glossary-v1 and the other members unchanged.
S6  all of it obeys the number rule.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import forge_core  # noqa: E402
import sign_v3  # noqa: E402

GLOSS1 = ROOT / "docs" / "glossary.md"
GLOSS2 = ROOT / "docs" / "glossary-v2.md"
GCAP2 = ROOT / "sc" / "glossary-v2.sc.json"
GOV8 = ROOT / "sc" / "forge-stack-governance-v8.sc.json"
GOV9 = ROOT / "sc" / "forge-stack-governance-v9.sc.json"
MAN12 = ROOT / "sc" / "forge-stack-manifest-v12.sc.json"
MAN13 = ROOT / "sc" / "forge-stack-manifest-v13.sc.json"
STAGES = ["Declare", "Classify", "Decide", "Trust-score", "Audit", "Act"]


def _load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def _sha(p):
    return forge_core.sha256_hex(p.read_bytes())


# S1
def test_s1_glossary_v1_unchanged():
    pin = _load(GOV8)["declaration"]["parameters"]["terminology_authority"]
    assert pin["document"] == "docs/glossary.md"
    assert _sha(GLOSS1) == pin["document_sha256"]
    assert GLOSS2.exists()


# S2
def test_s2_glossary_v2_six_stages():
    text = GLOSS2.read_text(encoding="utf-8")
    assert "The six stages in order: Declare (SCP) → Classify (DataCube) → Decide (RuleEngine) → " \
           "Trust-score (Leighton Weight) → Audit (ChronoSCRIBE) → Act (HAL)." in text
    assert "RuleEngine → ruleset" in text
    for n, name in enumerate(STAGES, 1):
        assert f"## Stage {n} — {name}" in text, name
    assert "**ruleset**" in text and "**RuleEngine**" in text
    assert "2026-08-08" in text and "five" in text
    assert "The six-stage spine architecture" in text
    assert b"\r\n" not in GLOSS2.read_bytes()


# S3
def test_s3_glossary_v2_capsule():
    c = _load(GCAP2)
    assert c["scp_id"] == "forge-stack/docs/glossary-v2"
    p = c["declaration"]["parameters"]
    assert p["document"] == "docs/glossary-v2.md"
    assert p["document_sha256"] == _sha(GLOSS2)
    assert p["supersedes"] == "forge-stack/docs/glossary-v1"


# S4
def test_s4_governance_v9():
    v8, v9 = _load(GOV8), _load(GOV9)
    assert v9["scp_id"] == "forge-stack/governance-v9"
    assert v9["inherits"] is None
    p9 = v9["declaration"]["parameters"]
    assert p9["supersedes"] == "forge-stack/governance-v8"
    assert p9["terminology_authority"] == {"document": "docs/glossary-v2.md", "document_sha256": _sha(GLOSS2)}
    c8, c9 = v8["declaration"]["constraints"], v9["declaration"]["constraints"]
    for key, value in c8.items():
        assert c9[key] == value, key
    spine = c9["spine"]
    assert [s["stage"] for s in spine["stages"]] == STAGES
    assert spine["stages"][2] == {"stage": "Decide", "system": "RuleEngine", "artefact": "ruleset"}
    assert "2026-08-08" in spine["history"] and "five" in spine["history"]
    assert spine["applies_from"] == "forge-stack/governance-v9"


# S5
def test_s5_manifest_v13():
    m12, m13 = _load(MAN12), _load(MAN13)
    assert m13["scp_id"] == "forge-stack/manifest-v13"
    assert m13["inherits"] == "forge-stack/governance-v9"
    p12, p13 = m12["declaration"]["parameters"], m13["declaration"]["parameters"]
    assert p13["members"] == ["forge-stack/docs/glossary-v2" if m == "forge-stack/docs/glossary-v1" else m
                              for m in p12["members"]]
    assert p13["governance"] == "forge-stack/governance-v9"
    assert p13["supersedes"] == "forge-stack/manifest-v12"


# S6
def test_s6_number_rule():
    assert sign_v3.fractional_numbers_v3(ROOT, only=[GCAP2, GOV9, MAN13])[0] == []
