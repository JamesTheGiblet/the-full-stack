"""Hardening 6.2 — the Saboteur's findings (the-saboteur v2, 2026-11-15).

Written before the fixes and run red first. Each test names the gap it
closes (CHANGELOG "The Good 6.2"). Every fix is a new layer; sign.py,
ledger.py, hal.py and hal_v2.py are not edited.

S1  sign_v2 --verify: every document a capsule references must exist and
    have a .sig. sign.py --verify checks only the .sig files it finds,
    so deleting one was a silent pass (Saboteur threat 03).
S2  sign_v2 --verify: no fractional JSON number anywhere in a capsule; a
    fraction is a fixed-place decimal string (James: "yes", 2026-11-15).
L1  ledger_v2 verify names a row that is not valid JSON instead of
    crashing with a traceback (threat 05).
L2  ledger_v2 verify names a replay: a row carrying another row's
    signature (threat 12).
H1  hal_v3 seal refuses a stale authoriser score (as_of older than
    --max-score-age-days, default 30), one dated in the future, and one
    with no valid as_of (threat 11).
"""
import base64
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import hal_v3  # noqa: E402
import ledger_v2  # noqa: E402
import sign_v2  # noqa: E402


def _capsule(path, doc=None, extra=None):
    decl = {"intent": "test", "parameters": {"document": doc} if doc else {}}
    cap = {"scp_id": "forge-stack/test-v1", "created": "2026-11-15T00:00:00Z", "declaration": decl}
    cap.update(extra or {})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cap), encoding="utf-8")


# S1
def test_s1_referenced_documents_need_a_sig(tmp_path):
    _capsule(tmp_path / "sc" / "a.sc.json", "docs/a.md")
    _capsule(tmp_path / "sc" / "b.sc.json", "docs/gone.md")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("hello\n")
    fails = sign_v2.missing_signatures(tmp_path)
    assert any("a.md" in f and ".sig" in f for f in fails)
    assert any("gone.md" in f and "not found" in f for f in fails)
    (tmp_path / "docs" / "a.md.sig").write_text("{}")
    fails = sign_v2.missing_signatures(tmp_path)
    assert not any("a.md" in f and ".sig" in f for f in fails) and len(fails) == 1


def test_s1_the_real_repo_has_every_referenced_sig():
    # One known gap, found by this layer on 2026-11-15 (CHANGELOG Ugly 6.2):
    # keystone_gate's unfinished step-spec capsule names a document that was
    # never written. Anything else missing fails here.
    known = {"docs/step-spec.md: referenced by consumer/keystone_gate/build_loop/sc/step-spec-v1.sc.json, not found"}
    fails = set(sign_v2.missing_signatures(ROOT))
    assert fails <= known, fails - known


# S2
def test_s2_fractional_numbers(tmp_path):
    _capsule(tmp_path / "sc" / "f.sc.json", extra={"declaration": {"intent": "x", "parameters": {
        "k": 0.1009, "n": 3, "flag": True, "s": "0.6", "list": [1, 2.5]}}})
    fails = sign_v2.fractional_numbers(tmp_path)
    assert len(fails) == 2
    assert any("declaration.parameters.k" in f and "0.1009" in f for f in fails)
    assert any("declaration.parameters.list[1]" in f for f in fails)
    assert all("decimal string" in f for f in fails)


# L1, L2
def _ledger(tmp_path, rows):
    p = tmp_path / "ledger.jsonl"
    p.write_text("".join(r + "\n" for r in rows), encoding="utf-8")
    return p


def test_l1_broken_row_is_named(tmp_path):
    good = json.dumps({"seq": 0, "prev": "GENESIS", "signature": {"value": "AAAA"}})
    fails = ledger_v2.precheck(_ledger(tmp_path, [good, '{"seq": 1, "prev": "ab']))
    assert fails and "line 2" in fails[0] and "not valid JSON" in fails[0]


def test_l2_replay_is_named(tmp_path):
    a = json.dumps({"seq": 0, "prev": "GENESIS", "signature": {"value": "AAAA"}})
    b = json.dumps({"seq": 1, "prev": "x", "signature": {"value": "BBBB"}})
    fails = ledger_v2.precheck(_ledger(tmp_path, [a, b, a]))
    assert fails and "line 3" in fails[0] and "replay" in fails[0] and "line 1" in fails[0]
    assert ledger_v2.precheck(_ledger(tmp_path, [a, "", b])) == []


def test_l_real_ledgers_pass_precheck():
    for led in [ROOT / "ledger.jsonl", *sorted((ROOT / "consumer").glob("*/ledger.jsonl"))]:
        assert ledger_v2.precheck(led) == [], led


def test_l_verify_names_instead_of_crashing(tmp_path, monkeypatch, capsys):
    led = _ledger(tmp_path, ['{"seq": 0, "prev": "GEN'])
    monkeypatch.setattr(ledger_v2.ledger, "get_ledger_path", lambda scope: led)
    monkeypatch.setattr(sys, "argv", ["ledger_v2.py", "verify"])
    assert ledger_v2.main() == 1
    out = capsys.readouterr().out
    assert "FAILED" in out and "not valid JSON" in out and "Traceback" not in out


# H1
def _score(tmp_path, as_of):
    p = tmp_path / "score.json"
    body = {"entity_id": "person:x", "result": {"lambda": 1.2}}
    if as_of is not None:
        body["as_of"] = as_of
    p.write_text(json.dumps(body), encoding="utf-8")
    return p


def test_h1_freshness(tmp_path):
    now = datetime(2026, 11, 15, 12, 0, 0, tzinfo=timezone.utc)
    iso = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: E731
    assert hal_v3.score_freshness(_score(tmp_path, iso(now - timedelta(days=29))), 30, now) is None
    stale = hal_v3.score_freshness(_score(tmp_path, iso(now - timedelta(days=31))), 30, now)
    assert stale and "stale" in stale and "31" in stale
    assert "future" in hal_v3.score_freshness(_score(tmp_path, iso(now + timedelta(hours=1))), 30, now)
    assert "as_of" in hal_v3.score_freshness(_score(tmp_path, None), 30, now)
    assert "as_of" in hal_v3.score_freshness(_score(tmp_path, "yesterday"), 30, now)
    assert hal_v3.DEFAULT_MAX_SCORE_AGE_DAYS == 30


def test_h1_seal_refuses_a_stale_score_before_hal(tmp_path, monkeypatch, capsys):
    score = _score(tmp_path, "2025-01-01T00:00:00Z")
    called = []
    monkeypatch.setattr(hal_v3.hal_v2, "main", lambda: called.append(1) or 0)
    monkeypatch.setattr(sys, "argv", ["hal_v3.py", "seal", "--seal-id", "t", "--authoriser-score-file", str(score),
                                      "--max-score-age-days", "30"])
    assert hal_v3.main() == 1 and not called
    assert "stale" in capsys.readouterr().out
    fresh = _score(tmp_path, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    monkeypatch.setattr(sys, "argv", ["hal_v3.py", "seal", "--authoriser-score-file", str(fresh)])
    assert hal_v3.main() == 0 and called
    assert "--max-score-age-days" not in sys.argv
