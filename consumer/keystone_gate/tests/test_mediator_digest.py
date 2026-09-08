"""Tests for keystone_gate/mediator/digest.py — Keystone Gate's pilot of
the Sub-Mediator telemetry contract (consumer/ccemk2/ROADMAP.md Part II,
Phase 20), the second real consumer after CCE.
"""
import json
import re
import tempfile
from pathlib import Path

from mediator.digest import build_digest_envelope, compute_primitive_usage, export_digest

_SCP_ID_RE = re.compile(r"^[a-z0-9-]+(?:/[a-z0-9-]+)*-v[0-9]+$")
_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _write_primitives(tmpdir, data):
    path = Path(tmpdir) / "capsule_primitives.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_compute_primitive_usage_reads_real_shape():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_primitives(tmpdir, {
            "scp_id": {"type": "str", "first_seen": "2026-01-01T00:00:00Z", "count": 5},
            "declaration.intent": {"type": "str", "first_seen": "2026-01-02T00:00:00Z", "count": 3},
        })
        usages = {u.field_path: u for u in compute_primitive_usage(path)}
        assert usages["scp_id"].observation_count == 5
        assert usages["scp_id"].field_type == "str"
        assert usages["declaration.intent"].observation_count == 3


def test_compute_primitive_usage_reformats_microsecond_timestamps():
    """Regression: capsule_primitives.json's real first_seen values come
    from primitives.py's own _utc_now(), which includes microseconds —
    not the ratified strict format. Must be reformatted, not passed
    through raw."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = _write_primitives(tmpdir, {
            "scp_id": {"type": "str", "first_seen": "2026-01-01T12:30:45.383512Z", "count": 1},
        })
        usages = compute_primitive_usage(path)
        assert _ISO_UTC_RE.match(usages[0].first_seen)
        assert usages[0].first_seen == "2026-01-01T12:30:45Z"


def test_compute_primitive_usage_missing_file_returns_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert compute_primitive_usage(Path(tmpdir) / "nonexistent.json") == []


def test_compute_primitive_usage_corrupt_file_returns_empty_not_crash():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "capsule_primitives.json"
        path.write_text("not valid json{{{", encoding="utf-8")
        assert compute_primitive_usage(path) == []


def test_build_digest_envelope_has_ratified_scp_id_and_valid_shape():
    from mediator.digest import PrimitiveUsage
    envelope = build_digest_envelope("keystone_gate", [
        PrimitiveUsage("scp_id", "str", "2026-01-01T00:00:00Z", 5),
    ])
    assert _SCP_ID_RE.match(envelope["scp_id"])
    assert _ISO_UTC_RE.match(envelope["created"])
    assert envelope["declaration"]["type"] == "primitive_digest"
    assert envelope["declaration"]["consumer"] == "keystone_gate"
    assert envelope["declaration"]["fields"][0]["field_path"] == "scp_id"
    assert envelope["signature"] is None
    assert envelope["licence"] == "MSL-1.0"


def test_scp_id_uses_hyphenated_form_not_the_packages_underscored_name():
    """Regression: consumer/keystone_gate/build_loop/sc/step-spec-v1.sc.json
    already fails the shared root schema gate for using the underscored
    "keystone_gate" in its scp_id. This digest must not repeat that."""
    envelope = build_digest_envelope("keystone_gate", [])
    assert "keystone_gate" not in envelope["scp_id"]
    assert "keystone-gate" in envelope["scp_id"]


def test_export_digest_writes_schema_valid_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        primitives_path = _write_primitives(tmpdir, {
            "scp_id": {"type": "str", "first_seen": "2026-01-01T00:00:00Z", "count": 1},
        })
        sc_dir = Path(tmpdir) / "sc"
        path = export_digest(primitives_path, sc_dir)

        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert _SCP_ID_RE.match(data["scp_id"])
        assert data["declaration"]["type"] == "primitive_digest"


def test_export_digest_is_idempotent_filename_across_reruns():
    with tempfile.TemporaryDirectory() as tmpdir:
        primitives_path = _write_primitives(tmpdir, {})
        sc_dir = Path(tmpdir) / "sc"
        path1 = export_digest(primitives_path, sc_dir)
        path2 = export_digest(primitives_path, sc_dir)
        assert path1 == path2
        assert len(list(sc_dir.glob("*.sc.json"))) == 1
