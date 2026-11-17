"""Audit — architectural gaps v1, checked against the code (James, 2026-11-16: "redo but honest").

Written before the capsule and run red first.

A1  sc/audit-architectural-gaps-v1.sc.json is well formed under
    governance-v8, signed with the foundation key (James, 2026-11-17; it
    was an unsigned draft when this test was written), with no status
    field (the signature is the status) and no fractional numbers.
A2  it names no private person or employer as its source.
A3  every finding has a verdict from a fixed set and checkable evidence.
A4  the findings the code contradicts are marked so, not repeated: HAL
    failure exits are non-zero, and the primitives run in-process.
A5  the measured facts it quotes are true of the repository now.
A6  the spine stage count (five in the glossary, six in the identity
    capsule) is recorded with both sources, for James to decide.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import sign_v3  # noqa: E402

CAP = ROOT / "sc" / "audit-architectural-gaps-v1.sc.json"
VERDICTS = {"confirmed", "partly confirmed", "not confirmed", "out of scope"}


def _cap():
    return json.loads(CAP.read_text(encoding="utf-8"))


# A1
def test_a1_signed_under_v8():
    c = _cap()
    assert c["scp_id"] == "forge-stack/audit/architectural-gaps-v1"
    assert c["inherits"] == "forge-stack/governance-v8"
    gov = json.loads((ROOT / "sc" / "forge-stack-governance-v8.sc.json").read_text(encoding="utf-8"))
    assert c["signature"]["key_id"] == gov["signature"]["key_id"]  # signed by James, 2026-11-17
    assert "status" not in c["declaration"]
    assert sign_v3.fractional_numbers_v3(ROOT, only=[CAP])[0] == []
    assert b"\r\n" not in CAP.read_bytes()


# A2
def test_a2_no_private_person():
    text = CAP.read_text(encoding="utf-8").lower()
    for word in ("michael", "axion", "interview"):
        assert word not in text, word


# A3
def test_a3_findings_have_verdicts_and_evidence():
    findings = _cap()["declaration"]["findings"]
    assert len(findings) >= 6
    for f in findings:
        assert f["verdict"] in VERDICTS, f["id"]
        assert f["evidence"], f["id"]
        assert f["next"], f["id"]


# A4
def test_a4_contradicted_claims_are_marked():
    by_id = {f["id"]: f for f in _cap()["declaration"]["findings"]}
    assert by_id["hal-exit-codes"]["verdict"] == "not confirmed"
    assert by_id["process-per-call"]["verdict"] == "not confirmed"
    assert by_id["cross-repo-integration"]["verdict"] == "confirmed"
    assert by_id["ledger-event-types"]["verdict"] == "confirmed"


# A6
def test_a6_spine_stage_count_recorded():
    f = {f["id"]: f for f in _cap()["declaration"]["findings"]}["spine-stage-count"]
    assert f["verdict"] == "confirmed"
    glossary = (ROOT / "docs" / "glossary.md").read_text(encoding="utf-8")
    assert "The five stages in order" in glossary and "five stages in order" in f["evidence"]
    assert "Decide (RuleEngine / ruleset)" in f["evidence"] and "five original stages" in f["evidence"]
    assert "James decides" in f["next"]


# A5
def test_a5_quoted_facts_hold():
    facts = _cap()["declaration"]["measured"]
    rows = [l for l in (ROOT / "ledger.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert facts["root_ledger_rows"] <= len(rows)
    ledger_src = (ROOT / "ledger.py").read_text(encoding="utf-8")
    assert "--allow-duplicates" in ledger_src
    for p in (ROOT / "hal.py", ROOT / "hal_v3.py"):
        assert "return 1" in p.read_text(encoding="utf-8")
