"""Hardening 6.4 — pinned document hashes are checked (2026-11-15).

Written before freeze_v3.py and run red first.

P1  freeze_v3 --check: a live capsule's document_sha256 must equal the
    sha256 of the document it names (resolved as sign.py resolves it).
    Nothing checked this: governance-v2..v6 pinned a glossary hash that
    never matched, and datacube-v1 / hal-v1 still pin their documents as
    they were before a two-line edit.
P2  a live capsule still holding COMPUTE-ON-FREEZE, or naming a document
    that does not exist, is FAILED (freeze_v2's placeholder check, kept).
P3  a superseded capsule is history: its mismatch is a NOTE, not a
    FAILED. Superseded = another capsule declares `supersedes` it, or a
    capsule with the same scp_id stem has a higher -vN.
P4  a capsule that pins no hash (document only) is not checked here; its
    document's .sig is sign_v2's S1.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import freeze_v3  # noqa: E402


def _cap(root, name, scp_id, doc=None, sha=None, **params):
    p = dict(params)
    if doc is not None:
        p["document"] = doc
    if sha is not None:
        p["document_sha256"] = sha
    cap = {"scp_id": scp_id, "created": "2026-11-15T00:00:00Z",
           "declaration": {"intent": "t", "parameters": p}}
    path = root / "sc" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(cap, indent=2) + "\n").encode())
    return path


def _doc(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode())
    return hashlib.sha256(text.encode()).hexdigest()


def test_p1_mismatch_is_failed_match_is_clean(tmp_path):
    good = _doc(tmp_path, "docs/a.md", "a\n")
    _doc(tmp_path, "docs/b.md", "b, edited\n")
    _cap(tmp_path, "a.sc.json", "x/a-v1", "docs/a.md", good)
    _cap(tmp_path, "b.sc.json", "x/b-v1", "docs/b.md", "0" * 64)
    fails, notes = freeze_v3.check(tmp_path)
    assert len(fails) == 1 and "b.sc.json" in fails[0] and "does not match" in fails[0]
    assert "docs/b.md" in fails[0] and notes == []


def test_p1_terminology_authority_is_checked(tmp_path):
    _doc(tmp_path, "docs/g.md", "g\n")
    cap = {"scp_id": "x/gov-v1", "created": "2026-11-15T00:00:00Z", "declaration": {
        "intent": "t", "parameters": {"terminology_authority": {"document": "docs/g.md",
                                                                "document_sha256": "1" * 64}}}}
    (tmp_path / "sc").mkdir()
    (tmp_path / "sc" / "g.sc.json").write_bytes(json.dumps(cap).encode())
    fails, _ = freeze_v3.check(tmp_path)
    assert len(fails) == 1 and "docs/g.md" in fails[0]


def test_p2_placeholder_and_missing_document(tmp_path):
    _doc(tmp_path, "docs/a.md", "a\n")
    _cap(tmp_path, "p.sc.json", "x/p-v1", "docs/a.md", "COMPUTE-ON-FREEZE")
    _cap(tmp_path, "m.sc.json", "x/m-v1", "docs/gone.md", "2" * 64)
    fails, _ = freeze_v3.check(tmp_path)
    assert any("p.sc.json" in f and "COMPUTE-ON-FREEZE" in f for f in fails)
    assert any("m.sc.json" in f and "not found" in f for f in fails)


def test_p3_superseded_is_a_note(tmp_path):
    now = _doc(tmp_path, "docs/a.md", "a, edited\n")
    _cap(tmp_path, "a1.sc.json", "x/a-v1", "docs/a.md", "3" * 64)
    _cap(tmp_path, "a2.sc.json", "x/a-v2", "docs/a.md", now)
    _cap(tmp_path, "old.sc.json", "x/old-v1", "docs/a.md", "COMPUTE-ON-FREEZE")
    _cap(tmp_path, "new.sc.json", "x/renamed-v1", None, None, supersedes="x/old-v1")
    fails, notes = freeze_v3.check(tmp_path)
    assert fails == []
    assert any("a1.sc.json" in n and "superseded by x/a-v2" in n for n in notes)
    assert any("old.sc.json" in n and "superseded by x/renamed-v1" in n for n in notes)


def test_p4_document_without_a_pinned_hash_is_not_checked(tmp_path):
    _cap(tmp_path, "d.sc.json", "x/d-v1", "docs/whatever.md")
    assert freeze_v3.check(tmp_path) == ([], [])


def test_main_exit_codes(tmp_path, capsys):
    _doc(tmp_path, "docs/a.md", "a\n")
    _cap(tmp_path, "a.sc.json", "x/a-v1", "docs/a.md", "4" * 64)
    assert freeze_v3.main(["--check"], root=tmp_path) == 1
    assert "FAILED" in capsys.readouterr().out
    _cap(tmp_path, "a.sc.json", "x/a-v1", "docs/a.md", hashlib.sha256(b"a\n").hexdigest())
    assert freeze_v3.main(["--check"], root=tmp_path) == 0


def test_real_repo_has_no_live_hash_failure():
    fails, notes = freeze_v3.check(ROOT)
    assert fails == [], fails
    assert any("governance-v6" in n for n in notes)
