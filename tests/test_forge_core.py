"""Phase 15/16 exit criteria (consumer/ccemk2/ROADMAP.md Part II):
forge_core and every root script that used to duplicate these primitives
inline must produce identical canonical bytes, identical hashes, and
agree on which capsules verify. Compares forge_core directly against the
live root scripts (imported as modules, not re-implemented expectations),
so a future edit to any script's inline copy that drifts from forge_core
fails this suite immediately — exactly the kind of silent-drift these
phases exist to close off.
"""
import base64
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import forge_core  # noqa: E402
import datacube  # noqa: E402
import hal  # noqa: E402
import leighton_weight  # noqa: E402
import ledger  # noqa: E402
import sign  # noqa: E402

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

# Every root script that had its own canonicalise() before this extraction.
_SCRIPTS_WITH_CANON = [sign, datacube, leighton_weight, hal, ledger]
# sign.py never defined its own sha256_hex() — it calls hashlib inline
# for its one use (artifact file hints) — so it's excluded here.
_SCRIPTS_WITH_SHA256 = [datacube, leighton_weight, hal, ledger]
_SCRIPTS_WITH_UTC = [datacube, leighton_weight]  # sign.py/hal.py/ledger.py never had utc_now/parse_iso_utc

_FIXTURE_OBJECTS = [
    {"a": 1, "b": 2},
    {"z": 1, "a": 2, "m": 3},  # key order must not affect output
    {"nested": {"b": [3, 1, 2], "a": None}},
    {"unicode": "café ☃", "emoji": "🔥"},
    {"bool": True, "null": None, "float": 1.5, "negzero": -0.0},
    [],
    {},
]


def test_canonicalise_matches_every_root_script_byte_for_byte():
    for obj in _FIXTURE_OBJECTS:
        expected = forge_core.canonicalise(obj)
        for script in _SCRIPTS_WITH_CANON:
            assert script.canonicalise(obj) == expected, f"{script.__name__} diverges on {obj!r}"


def test_sha256_hex_matches_every_root_script():
    for payload in (b"", b"hello", "café".encode("utf-8"), b"\x00\x01\x02"):
        expected = forge_core.sha256_hex(payload)
        for script in _SCRIPTS_WITH_SHA256:
            assert script.sha256_hex(payload) == expected


def test_iso_utc_regex_is_byte_identical_to_sign_py():
    assert forge_core.ISO_UTC_RE.pattern == sign.ISO_UTC_RE.pattern


def test_scp_id_regex_is_byte_identical_to_sign_py():
    assert forge_core.SCP_ID_RE.pattern == sign.SCP_ID_RE.pattern


def test_scp_id_regex_agrees_with_sign_py_on_a_fixture_table():
    cases = [
        ("ccemk2/ruleset/se-cascade-se-crypto-v1", True),
        ("cobblewright/chronicle-engine-v1", True),
        ("lifeforge/consumer-v1", True),
        ("ruleset:se-cascade:se-crypto", False),
        ("ccemk2/ruleset/se-cascade", False),
        ("CCEMK2/ruleset-v1", False),
        ("", False),
    ]
    for scp_id, expected in cases:
        assert bool(forge_core.SCP_ID_RE.match(scp_id)) == expected
        assert bool(sign.SCP_ID_RE.match(scp_id)) == expected


def test_utc_now_format_matches_datacube_and_leighton_weight():
    for script in _SCRIPTS_WITH_UTC:
        value = script.utc_now()
        assert forge_core.ISO_UTC_RE.match(value)
        assert forge_core.ISO_UTC_RE.match(forge_core.utc_now())


def test_parse_iso_utc_agrees_with_datacube_and_leighton_weight():
    fixed = "2026-01-01T12:30:45Z"
    expected = forge_core.parse_iso_utc(fixed)
    for script in _SCRIPTS_WITH_UTC:
        assert script.parse_iso_utc(fixed) == expected
    assert expected == datetime(2026, 1, 1, 12, 30, 45, tzinfo=timezone.utc)


def test_format_iso_utc_round_trips_with_parse_iso_utc():
    fixed = datetime(2026, 1, 1, 12, 30, 45, tzinfo=timezone.utc)
    assert forge_core.format_iso_utc(fixed) == "2026-01-01T12:30:45Z"
    naive = datetime(2026, 1, 1, 12, 30, 45)
    assert forge_core.format_iso_utc(naive) == "2026-01-01T12:30:45Z"
    assert forge_core.parse_iso_utc(forge_core.format_iso_utc(fixed)) == fixed


def test_parse_iso_utc_rejects_non_utc_format_same_as_root_scripts():
    for bad in ("2026-01-01T12:30:45", "2026-01-01T12:30:45+00:00", "not a date"):
        try:
            forge_core.parse_iso_utc(bad)
            assert False, f"forge_core accepted invalid value: {bad!r}"
        except ValueError:
            pass
        for script in _SCRIPTS_WITH_UTC:
            try:
                script.parse_iso_utc(bad)
                assert False, f"{script.__name__} accepted invalid value: {bad!r}"
            except ValueError:
                pass


def test_signature_block_verifies_under_sign_py_own_verify_logic(tmp_path):
    """The real cross-compatibility proof: a signature forge_core
    produces must verify using sign.py's own inline verification code
    (reimplemented here exactly as verify_all() does it), not just
    forge_core's own verify_canonical()."""
    key = Ed25519PrivateKey.generate()
    pub = key.public_key()

    body = {"scp_id": "ccemk2/ruleset/test-v1", "created": forge_core.utc_now(), "declaration": {"type": "ruleset"}}
    sig_block = forge_core.make_signature_block(body, key, key_id="did:key:test")

    # sign.py's verify_all(), inlined: canonicalise(body) then pub.verify(...).
    pub.verify(base64.b64decode(sig_block["value"]), sign.canonicalise(body).encode("utf-8"))

    assert forge_core.verify_canonical(body, sig_block["value"], pub)
    tampered = {**body, "declaration": {"type": "tampered"}}
    assert not forge_core.verify_canonical(tampered, sig_block["value"], pub)


def test_sign_exported_capsule_produces_a_signature_sign_py_itself_would_accept(tmp_path):
    """sign_exported_capsule was originally consumer/ccemk2-only, promoted
    here once keystone_gate needed the identical logic (Phase 20) — same
    cross-compatibility proof as above, but through the file-based API."""
    key = Ed25519PrivateKey.generate()
    pub = key.public_key()

    path = tmp_path / "test-v1.sc.json"
    path.write_text(json.dumps({
        "scp_id": "test/mediator/test-v1", "scp_version": "1.2.0",
        "created": forge_core.utc_now(), "declaration": {"type": "test_digest"},
        "licence": "MSL-1.0", "signature": None,
    }), encoding="utf-8")

    forge_core.sign_exported_capsule(path, key, key_id="did:key:test")

    capsule = json.loads(path.read_text(encoding="utf-8"))
    assert capsule["signature"]["key_id"] == "did:key:test"
    body = {k: v for k, v in capsule.items() if k != "signature"}
    pub.verify(base64.b64decode(capsule["signature"]["value"]), sign.canonicalise(body).encode("utf-8"))


def test_key_round_trip_load_or_create_then_load(tmp_path):
    key_path = tmp_path / "test.key"
    created = forge_core.load_or_create_private_key(key_path)
    assert key_path.exists()
    loaded = forge_core.load_private_key(key_path)
    assert forge_core.public_key_b64(created) == forge_core.public_key_b64(loaded)


def test_load_private_key_fails_loud_when_missing(tmp_path):
    try:
        forge_core.load_private_key(tmp_path / "nonexistent.key")
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass
