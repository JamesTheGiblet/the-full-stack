"""Regression test for a real bug found while onboarding CCE as a
consumer: append_entries() decided whether to prepend a newline based on
"is the file non-empty" rather than "does the file already end with
one" — every write already ends with "\n" (see content_to_write), so
every append after the first wrote a second, blank line between
entries. That blank line isn't part of any signed content (the hash
chain only ever hashes canonicalise(signed), the JSON line itself — not
raw file bytes/spacing), so it never corrupted anything cryptographically,
but it did break parse_entries()'s naive json.loads() per line, which
made every read (verify, later appends) fail outright.

Fixed on both sides: append_entries() now checks the file's actual
trailing byte, and parse_entries() tolerates a blank line regardless
(for ledgers written before this fix).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import forge_core  # noqa: E402
import ledger  # noqa: E402


def _sha256_of(text: str) -> str:
    return forge_core.sha256_hex(text.encode("utf-8"))


def test_sequential_appends_never_write_a_blank_line(tmp_path, monkeypatch):
    key_path = tmp_path / "test.key"
    key = forge_core.load_or_create_private_key(key_path)
    monkeypatch.setattr(ledger, "KEY_FILE", key_path)
    # PUB_FILE is bound to the real repo's forge-signing.pub at ledger.py's
    # own import time — patching KEY_FILE alone would sign with a fake key
    # but verify against the real public key. Point PUB_FILE at the fake
    # key's own derived public key too.
    pub_path = tmp_path / "test.pub"
    pub_path.write_text(forge_core.public_key_b64(key), encoding="utf-8")
    monkeypatch.setattr(ledger, "PUB_FILE", pub_path)
    # Isolate from the real repo root entirely: get_root_ledger_path() and
    # append_entries()'s own relative_to(ROOT) print both key off ROOT.
    monkeypatch.setattr(ledger, "ROOT", tmp_path)

    # Use the (fake) root ledger path itself, matching get_root_ledger_path()
    # under the monkeypatched ROOT — sidesteps the separate "new consumer
    # ledger must anchor to a real, already-verifying root" requirement,
    # which isn't what this test is about.
    ledger_path = tmp_path / "ledger.jsonl"

    for i in range(3):
        candidate = {"event": "event.test.appended", "subject": f"item-{i}", "sha256": _sha256_of(f"item-{i}")}
        result = ledger.append_entries([candidate], ledger_path, allow_duplicates=False)
        assert result == 0

    raw = ledger_path.read_text(encoding="utf-8")
    assert "\n\n" not in raw, f"blank line found in ledger content:\n{raw!r}"

    lines = ledger.read_ledger_lines(ledger_path)
    assert all(line.strip() for line in lines), "read_ledger_lines returned a blank line"
    assert len(lines) == 3

    _, head, _, failed, _ = ledger.verify_chain(ledger_path, print_rows=False)
    assert failed == 0
    assert head != "GENESIS"


def test_parse_entries_tolerates_a_pre_existing_blank_line():
    """Backward compatibility: a ledger written before this fix may
    already have a blank line in it (as CCE's real consumer ledger did) —
    parse_entries must still read it correctly rather than crash."""
    valid_line = '{"event": "e", "subject": "s", "sha256": "x"}'
    lines = [valid_line, "", valid_line]
    parsed = ledger.parse_entries(lines)
    assert len(parsed) == 2
