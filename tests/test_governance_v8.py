"""Hardening 6.6 — governance-v8 ratifies consolidation (James, 2026-11-16).

Written before the capsules and run red first.

James, 2026-11-16: "when we get to a particular point we need to
consolidate the code, archive the versions and take that as the next
stable point, otherwise we have v100 v1000 in the end", then "consolidate
what is; if adding more it's a new v".

G1  sc/forge-stack-governance-v8.sc.json supersedes v7, keeps every v7
    constraint unchanged, and adds consolidation: a consolidation keeps
    behaviour (the tests of what is still pass, nothing added); anything
    new is a new version; the old layers are archived byte-identical and
    tagged, never edited or deleted; the trigger; consumers first, and a
    file pinned by a signed capsule stays where it is.
G2  sc/forge-stack-manifest-v12.sc.json witnesses governance-v8 with
    manifest-v11's members unchanged.
N1  both obey governance-v7's number rule.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import forge_core  # noqa: E402
import sign_v3  # noqa: E402

GOV7 = ROOT / "sc" / "forge-stack-governance-v7.sc.json"
GOV8 = ROOT / "sc" / "forge-stack-governance-v8.sc.json"
MAN11 = ROOT / "sc" / "forge-stack-manifest-v11.sc.json"
MAN12 = ROOT / "sc" / "forge-stack-manifest-v12.sc.json"


def _load(p):
    return json.loads(p.read_text(encoding="utf-8"))


# G1
def test_g1_governance_v8_keeps_v7():
    v7, v8 = _load(GOV7), _load(GOV8)
    assert v8["scp_id"] == "forge-stack/governance-v8"
    assert v8["inherits"] is None
    assert v8["declaration"]["parameters"]["supersedes"] == "forge-stack/governance-v7"
    c7, c8 = v7["declaration"]["constraints"], v8["declaration"]["constraints"]
    for key, value in c7.items():
        assert c8[key] == value, key


def test_g1_consolidation():
    con = _load(GOV8)["declaration"]["constraints"]["consolidation"]
    assert "same behaviour" in con["rule"] and "new version" in con["rule"]
    assert con["applies_from"] == "forge-stack/governance-v8"
    for word in ("archive", "byte-identical", "tag"):
        assert word in con["archive"], word
    assert "never edited or deleted" in con["archive"]
    assert con["trigger"]["max_chain_depth"] == 5
    assert "patch" in con["trigger"]["or"]
    assert "consumers" in con["scope"].lower() and "pinned" in con["scope"]
    assert "major" in con["version"]
    assert "immutability" in con["relation_to_immutability"]


def test_g1_v8_pins_the_glossary_as_it_is_now():
    term = _load(GOV8)["declaration"]["parameters"]["terminology_authority"]
    doc = ROOT / term["document"]
    assert forge_core.sha256_hex(doc.read_bytes()) == term["document_sha256"]


# G2
def test_g2_manifest_v12():
    m11, m12 = _load(MAN11), _load(MAN12)
    assert m12["scp_id"] == "forge-stack/manifest-v12"
    assert m12["inherits"] == "forge-stack/governance-v8"
    p11, p12 = m11["declaration"]["parameters"], m12["declaration"]["parameters"]
    assert p12["members"] == p11["members"]
    assert p12["governance"] == "forge-stack/governance-v8"
    assert p12["supersedes"] == "forge-stack/manifest-v11"


# N1
def test_n1_v8_obeys_the_number_rule():
    assert sign_v3.fractional_numbers_v3(ROOT, only=[GOV8, MAN12])[0] == []
