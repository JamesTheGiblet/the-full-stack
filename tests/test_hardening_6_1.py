"""Hardening 6.1 — forge_core key handling and the Master Mediator.

Written before the fixes and run red first. Each test names the gap it
closes (CHANGELOG "The Good 6.1"):

K1  sign.py never creates a signing identity unless asked (--init-key):
    a wrong or moved FORGE_KEY_PATH used to sign under a brand-new
    did:key without stopping.
K2  forge_core.create_private_key never overwrites an existing key and
    writes the new one owner-only; load_or_create_private_key creates
    through it.
K3  forge_core.verify_canonical returns False for an unverifiable
    signature, but an object that cannot be canonicalised is a bug and
    raises instead of reading as "invalid signature".
K4  forge_core.sign_exported_capsule replaces the file atomically: a
    failure mid-write leaves the original capsule untouched.
M1  Three consumers make a field Fact only once it has been seen for
    30 days (they used to make it Fact on day one).
M2  A spine-update proposal inherits the governance in force now (the
    one no other governance capsule supersedes), not governance-v1.
M3  load_digests survives a capsule that vanishes or breaks between
    discovery and loading.
"""
import json
import os
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import forge_core  # noqa: E402
import sign  # noqa: E402
from master_mediator import discovery, proposal  # noqa: E402
from master_mediator.classifier import TIER_FACT, FieldObservation, MaturityFinding, classify  # noqa: E402


def _obs(consumer, age, count=50):
    return FieldObservation(consumer=consumer, declaration_type="usage_digest", field_key=("ns", "FACT"),
                            observation_count=count, age_days=age)


# K1
def test_sign_py_refuses_to_create_a_key_unless_asked(tmp_path, monkeypatch):
    missing = tmp_path / "moved" / "forge-signing.key"
    monkeypatch.setattr(sign, "KEY_FILE", missing)
    with pytest.raises(SystemExit):
        sign.load_or_create_key()
    assert not missing.exists()
    missing.parent.mkdir()
    key = sign.load_or_create_key(create=True)
    assert missing.exists()
    assert forge_core.public_key_b64(sign.load_or_create_key()) == forge_core.public_key_b64(key)


# K2
def test_create_private_key_never_overwrites_and_is_owner_only(tmp_path):
    path = tmp_path / "k.key"
    key = forge_core.create_private_key(path)
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        forge_core.create_private_key(path)
    assert path.read_bytes() == before
    assert forge_core.public_key_b64(forge_core.load_private_key(path)) == forge_core.public_key_b64(key)
    if os.name == "posix":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    again = forge_core.load_or_create_private_key(path)
    assert forge_core.public_key_b64(again) == forge_core.public_key_b64(key)


# K3
def test_verify_canonical_false_for_bad_signatures_but_raises_for_bugs(tmp_path):
    key = forge_core.create_private_key(tmp_path / "k.key")
    pub = key.public_key()
    body = {"a": 1}
    good = forge_core.make_signature_block(body, key, "did:key:test")["value"]
    assert forge_core.verify_canonical(body, good, pub) is True
    assert forge_core.verify_canonical({"a": 2}, good, pub) is False
    for bad in (None, "!!!not base64!!!", "", 12):
        assert forge_core.verify_canonical(body, bad, pub) is False
    with pytest.raises(TypeError):
        forge_core.verify_canonical({"a": object()}, good, pub)


# K4
def test_sign_exported_capsule_is_atomic(tmp_path, monkeypatch):
    key = forge_core.create_private_key(tmp_path / "k.key")
    path = tmp_path / "c.sc.json"
    path.write_text(json.dumps({"scp_id": "x/y-v1", "signature": None}, indent=2) + "\n", encoding="utf-8")
    original = path.read_bytes()

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        forge_core.sign_exported_capsule(path, key, "did:key:test")
    assert path.read_bytes() == original
    assert [p.name for p in tmp_path.iterdir() if p.name not in ("k.key", "c.sc.json")] == []
    monkeypatch.undo()
    forge_core.sign_exported_capsule(path, key, "did:key:test")
    signed = json.loads(path.read_text(encoding="utf-8"))
    body = {k: v for k, v in signed.items() if k != "signature"}
    assert forge_core.verify_canonical(body, signed["signature"]["value"], key.public_key())


# M1
def test_three_consumers_need_thirty_days_for_fact():
    assert classify([_obs("a", 0), _obs("b", 0), _obs("c", 0)])[0].tier != TIER_FACT
    assert classify([_obs("a", 29), _obs("b", 29), _obs("c", 29)])[0].tier != TIER_FACT
    assert classify([_obs("a", 30), _obs("b", 30), _obs("c", 30)])[0].tier == TIER_FACT
    assert classify([_obs("a", 95), _obs("b", 95)])[0].tier == TIER_FACT  # unchanged


# M2
def test_proposal_inherits_the_governance_in_force():
    current = proposal.current_governance(ROOT)
    numbers = sorted(int(p.stem.split("-v")[-1].split(".")[0]) for p in (ROOT / "sc").glob("forge-stack-governance-v*.sc.json"))
    assert current == f"forge-stack/governance-v{numbers[-1]}"
    superseded = set()
    for p in (ROOT / "sc").glob("forge-stack-governance-v*.sc.json"):
        sup = json.loads(p.read_text(encoding="utf-8")).get("declaration", {}).get("supersedes")
        if sup:
            superseded.add(sup)
    assert current not in superseded
    finding = MaturityFinding(declaration_type="usage_digest", field_key=("ns", "FACT"), tier=TIER_FACT,
                              consumers=["a", "b", "c"], total_observation_count=150, max_age_days=40.0)
    assert proposal.build_spine_update_capsule(finding)["inherits"] == current
    assert proposal.build_spine_update_capsule(finding, inherits="forge-stack/governance-v9")["inherits"] == \
        "forge-stack/governance-v9"


# M3
def test_load_digests_survives_a_capsule_that_changes_after_discovery(tmp_path, monkeypatch):
    good = tmp_path / "good.sc.json"
    good.write_text(json.dumps({"declaration": {"type": "usage_digest", "consumer": "a"}}), encoding="utf-8")
    broken = tmp_path / "broken.sc.json"
    broken.write_text("{ not json", encoding="utf-8")
    gone = tmp_path / "gone.sc.json"
    monkeypatch.setattr(discovery, "find_digest_paths", lambda root: [good, broken, gone])
    digests = discovery.load_digests(tmp_path)
    assert [d["_source_path"] for d in digests] == [str(good)]
