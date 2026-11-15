"""Hardening 6.3 — governance-v7 ratifies two rules (James, 2026-11-15).

Written before the capsule and the layers and run red first.

G1  sc/forge-stack-governance-v7.sc.json supersedes v6, keeps every v6
    constraint unchanged, and adds number_encoding (no fractional JSON
    numbers; fixed-place decimal strings) and hal_score_freshness (an
    authoriser score at most 30 days old). It is not retroactive.
G2  sc/forge-stack-manifest-v10.sc.json witnesses governance-v7 with
    manifest-v9's members unchanged.
C1  sign_capsule.py signs exactly the capsules it is given, refuses one
    already signed, and refuses a capsule that fails the schema gate.
N1  sign_v3: the number rule applies to a capsule under governance-v7 or
    later (or naming none); a capsule that inherits governance-v1..v6 was
    signed before the rule and is grandfathered (a NOTE, not a FAILED).
"""
import base64
import json
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import forge_core  # noqa: E402
import sign_capsule  # noqa: E402
import sign_v3  # noqa: E402

GOV6 = ROOT / "sc" / "forge-stack-governance-v6.sc.json"
GOV7 = ROOT / "sc" / "forge-stack-governance-v7.sc.json"
MAN9 = ROOT / "sc" / "forge-stack-manifest-v9.sc.json"
MAN10 = ROOT / "sc" / "forge-stack-manifest-v10.sc.json"


def _load(p):
    return json.loads(p.read_text(encoding="utf-8"))


# G1
def test_g1_governance_v7():
    v6, v7 = _load(GOV6), _load(GOV7)
    assert v7["scp_id"] == "forge-stack/governance-v7"
    assert v7["inherits"] is None
    assert v7["declaration"]["parameters"]["supersedes"] == "forge-stack/governance-v6"
    c6, c7 = v6["declaration"]["constraints"], v7["declaration"]["constraints"]
    for key, value in c6.items():
        assert c7[key] == value, key
    num = c7["number_encoding"]
    assert "fractional" in num["rule"] and "decimal string" in num["rule"]
    assert num["applies_from"] == "forge-stack/governance-v7"
    assert "1.4589999999999999" in num["why"]
    hal = c7["hal_score_freshness"]
    assert hal["max_score_age_days"] == 30
    assert "hal_v3.py" in hal["enforced_by"]
    assert "sign_v3.py" in num["enforced_by"]


def test_g1_v7_pins_the_glossary_as_it_is_now():
    term = _load(GOV7)["declaration"]["parameters"]["terminology_authority"]
    doc = ROOT / term["document"]
    assert forge_core.sha256_hex(doc.read_bytes()) == term["document_sha256"]


def test_g1_v7_obeys_its_own_rule():
    assert sign_v3.fractional_numbers_v3(ROOT, only=[GOV7, MAN10])[0] == []


# G2
def test_g2_manifest_v10():
    m9, m10 = _load(MAN9), _load(MAN10)
    assert m10["scp_id"] == "forge-stack/manifest-v10"
    assert m10["inherits"] == "forge-stack/governance-v7"
    p9, p10 = m9["declaration"]["parameters"], m10["declaration"]["parameters"]
    assert p10["members"] == p9["members"]
    assert p10["governance"] == "forge-stack/governance-v7"
    assert p10["supersedes"] == "forge-stack/manifest-v9"


# C1
def _key(tmp_path):
    key = Ed25519PrivateKey.generate()
    path = tmp_path / "throwaway.key"
    path.write_bytes(key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                       serialization.NoEncryption()))
    return key, path


def _capsule(path, **extra):
    cap = {"scp_id": "forge-stack/test-v1", "scp_version": "1.2.0", "created": "2026-11-15T00:00:00Z",
           "inherits": "forge-stack/governance-v7",
           "declaration": {"intent": "test", "parameters": {"n": 1}}, "licence": "MSL-1.0"}
    cap.update(extra)
    path.write_text(json.dumps(cap, indent=2) + "\n", encoding="utf-8")
    return path


def test_c1_signs_exactly_the_named_capsule(tmp_path, monkeypatch):
    key, key_path = _key(tmp_path)
    monkeypatch.setattr(sign_capsule.sign, "KEY_FILE", key_path)
    a, b = _capsule(tmp_path / "a.sc.json"), _capsule(tmp_path / "b.sc.json")
    before_b = b.read_bytes()
    assert sign_capsule.main([str(a)]) == 0
    signed = _load(a)
    body = {k: v for k, v in signed.items() if k != "signature"}
    key.public_key().verify(base64.b64decode(signed["signature"]["value"]),
                            forge_core.canonicalise(body).encode("utf-8"))
    assert signed["signature"]["key_id"] == sign_capsule.sign.KEY_ID
    assert b.read_bytes() == before_b
    assert b"\r\n" not in a.read_bytes()


def test_c1_refuses_a_signed_capsule(tmp_path, monkeypatch, capsys):
    _, key_path = _key(tmp_path)
    monkeypatch.setattr(sign_capsule.sign, "KEY_FILE", key_path)
    a = _capsule(tmp_path / "a.sc.json", signature={"key_id": "x", "algorithm": "Ed25519", "value": "AAAA"})
    before = a.read_bytes()
    assert sign_capsule.main([str(a)]) == 1
    assert a.read_bytes() == before
    assert "already signed" in capsys.readouterr().out


def test_c1_refuses_a_capsule_that_fails_the_schema_gate(tmp_path, monkeypatch, capsys):
    _, key_path = _key(tmp_path)
    monkeypatch.setattr(sign_capsule.sign, "KEY_FILE", key_path)
    a = _capsule(tmp_path / "a.sc.json", scp_id="Bad_Id")
    before = a.read_bytes()
    assert sign_capsule.main([str(a)]) == 1
    assert a.read_bytes() == before
    assert "FAILED" in capsys.readouterr().out


def test_c1_refuses_a_fractional_number_under_v7(tmp_path, monkeypatch, capsys):
    _, key_path = _key(tmp_path)
    monkeypatch.setattr(sign_capsule.sign, "KEY_FILE", key_path)
    a = _capsule(tmp_path / "a.sc.json", declaration={"intent": "t", "parameters": {"w": 0.6}})
    assert sign_capsule.main([str(a)]) == 1
    assert "fractional" in capsys.readouterr().out


# N1
def test_n1_grandfathered_before_v7(tmp_path):
    (tmp_path / "sc").mkdir()
    old = _capsule(tmp_path / "sc" / "old.sc.json", inherits="forge-stack/governance-v6",
                   declaration={"intent": "t", "parameters": {"w": 1.5}})
    new = _capsule(tmp_path / "sc" / "new.sc.json",
                   declaration={"intent": "t", "parameters": {"w": 2.5}})
    none = _capsule(tmp_path / "sc" / "none.sc.json", inherits=None,
                    declaration={"intent": "t", "parameters": {"w": 3.5}})
    fails, notes = sign_v3.fractional_numbers_v3(tmp_path)
    assert len(fails) == 2 and any("new.sc.json" in f for f in fails) and any("none.sc.json" in f for f in fails)
    assert len(notes) == 1 and "old.sc.json" in notes[0] and "governance-v6" in notes[0]
    assert old and new and none


def test_n1_real_repo_has_no_fractional_failure_under_v7():
    fails, notes = sign_v3.fractional_numbers_v3(ROOT)
    assert fails == [], fails
    assert any("ccemk2" in n for n in notes)
