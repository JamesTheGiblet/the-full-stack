#!/usr/bin/env python3
"""DataCube Classify stage implementation.

Implements the Classify pipeline end-to-end:
1) Store writer (append-only JSONL)
2) Store verifier (signature + supersedes integrity)
3) Projector (deterministic cube projection)
4) Integrity calculator (coverage, saturation, decay)
5) Signing + pin emission helper
6) Worked example bootstrap command

Usage examples:
  python datacube.py write --store datacube/store.jsonl --record-file rec.json
  python datacube.py verify-store --store datacube/store.jsonl
  python datacube.py project --store datacube/store.jsonl --subject forge-stack/docs/datacube-v1 \
    --cube-id forge-stack/docs/datacube-v1-cube-v1 --output datacube/cubes/datacube-v1.cube.json
  python datacube.py verify-cube --cube datacube/cubes/datacube-v1.cube.json
  python datacube.py pin-cube --cube datacube/cubes/datacube-v1.cube.json
  python datacube.py worked-example --output-dir datacube/example
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import math
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = pathlib.Path(__file__).parent
KEY_FILE = pathlib.Path(os.environ.get("FORGE_KEY_PATH", str(ROOT / "forge-signing.key")))
PUB_FILE = ROOT / "forge-signing.pub"
KEY_ID = "did:key:z6MktudRY5LBZJeE13BiF4BeisAwWs7gvg6srh2GwLAMKDwJ"

NAMESPACES = {"event", "state", "domain", "behaviour"}
LENSES = {"FACT", "COUNTER", "OPINION", "FICTION", "CONTEXT", "UNKNOWN"}
GRADE_BANDS = (
    (90.0, "CRYSTALLINE"),
    (70.0, "COHERENT"),
    (40.0, "FORMING"),
    (0.0, "SPARSE"),
)
ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def canonicalise(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_utc(value: str) -> datetime:
    if not ISO_UTC_RE.match(value):
        raise ValueError(f"created must be ISO 8601 UTC with Z suffix: {value}")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def display_path(path: pathlib.Path) -> str:
    p = path if path.is_absolute() else (ROOT / path)
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


def load_private_key() -> Ed25519PrivateKey:
    if not KEY_FILE.exists():
        raise FileNotFoundError(f"key file not found: {KEY_FILE}")
    return Ed25519PrivateKey.from_private_bytes(KEY_FILE.read_bytes())


def load_public_key() -> Ed25519PublicKey:
    if not PUB_FILE.exists():
        raise FileNotFoundError("forge-signing.pub not found")
    return Ed25519PublicKey.from_public_bytes(base64.b64decode(PUB_FILE.read_text(encoding="utf-8").strip()))


def is_valid_namespace(value: str) -> bool:
    return any(value == ns or value.startswith(f"{ns}.") for ns in NAMESPACES)


def validate_record_body(body: dict[str, Any]) -> None:
    required = [
        "record_id",
        "subject",
        "namespace",
        "lens",
        "content",
        "source",
        "assigned_by",
        "created",
    ]
    for key in required:
        if key not in body:
            raise ValueError(f"missing required field: {key}")

    for key in ("record_id", "subject", "namespace", "lens", "source", "assigned_by", "created"):
        if not isinstance(body.get(key), str) or not body[key].strip():
            raise ValueError(f"field '{key}' must be a non-empty string")

    if not is_valid_namespace(body["namespace"]):
        raise ValueError(f"namespace must be one of event.*|state.*|domain.*|behaviour.*: {body['namespace']}")

    if body["lens"] not in LENSES:
        raise ValueError(f"lens must be one of {sorted(LENSES)}: {body['lens']}")

    if not isinstance(body["content"], (str, dict, list, int, float, bool)) and body["content"] is not None:
        raise ValueError("content must be JSON-serialisable scalar/object/list")

    parse_iso_utc(body["created"])

    supersedes = body.get("supersedes")
    if supersedes is not None and (not isinstance(supersedes, str) or not supersedes.strip()):
        raise ValueError("supersedes must be omitted or a non-empty string")

    if body["lens"] == "OPINION" and not body["assigned_by"].strip():
        raise ValueError("OPINION records require non-empty assigned_by attribution")


def sign_body(body: dict[str, Any], key: Ed25519PrivateKey) -> dict[str, Any]:
    sig = key.sign(canonicalise(body).encode("utf-8"))
    out = dict(body)
    out["signature"] = {
        "key_id": KEY_ID,
        "algorithm": "Ed25519",
        "value": base64.b64encode(sig).decode(),
    }
    return out


def record_line(entry: dict[str, Any]) -> str:
    return canonicalise(entry)


def read_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    out: list[dict[str, Any]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: line {i} invalid JSON: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"{path}: line {i} must be a JSON object")
        out.append(obj)
    return out


def append_store_entries(store_path: pathlib.Path, bodies: list[dict[str, Any]]) -> int:
    key = load_private_key()
    store_path.parent.mkdir(parents=True, exist_ok=True)

    existing = read_jsonl(store_path)
    seen_ids = {str(x.get("record_id")) for x in existing}

    signed_lines: list[str] = []
    for body in bodies:
        validate_record_body(body)
        rid = body["record_id"]
        if rid in seen_ids:
            raise ValueError(f"duplicate record_id: {rid}")
        signed = sign_body(body, key)
        signed_lines.append(record_line(signed))
        seen_ids.add(rid)

    with store_path.open("a", encoding="utf-8", newline="\n") as fh:
        for line in signed_lines:
            fh.write(line + "\n")

    print(f"appended {len(signed_lines)} record(s) to {display_path(store_path)}")
    return 0


def verify_store(store_path: pathlib.Path, print_rows: bool = True) -> tuple[int, str, int]:
    pub = load_public_key()
    records = read_jsonl(store_path)
    failed = 0

    ids: set[str] = set()
    supersedes_targets: list[tuple[str, str]] = []

    line_hash_prev = "GENESIS"
    for idx, obj in enumerate(records):
        body = {k: v for k, v in obj.items() if k != "signature"}
        sig = obj.get("signature", {})

        try:
            validate_record_body(body)
        except Exception as exc:
            failed += 1
            if print_rows:
                print(f"FAILED  #{idx:04d}  schema  {exc}")
            continue

        rid = body["record_id"]
        if rid in ids:
            failed += 1
            if print_rows:
                print(f"FAILED  #{idx:04d}  duplicate record_id  {rid}")
            continue
        ids.add(rid)

        supersedes = body.get("supersedes")
        if isinstance(supersedes, str):
            supersedes_targets.append((rid, supersedes))

        ok_sig = False
        try:
            pub.verify(base64.b64decode(sig["value"]), canonicalise(body).encode("utf-8"))
            ok_sig = True
        except Exception:
            ok_sig = False

        line = record_line(obj)
        line_hash_prev = sha256_hex(line.encode("utf-8"))

        if print_rows:
            status = "OK" if ok_sig else "FAILED"
            print(f"{status:6s} #{idx:04d}  {body['record_id']}  {body['lens']}  {body['subject']}")

        if not ok_sig:
            failed += 1

    for rid, target in supersedes_targets:
        if target not in ids:
            failed += 1
            if print_rows:
                print(f"FAILED  supersedes unresolved: {rid} -> {target}")

    if print_rows:
        print("store verifies." if failed == 0 else f"{failed} failure(s).")

    return len(records), line_hash_prev, failed


def load_records_from_json(path: pathlib.Path) -> list[dict[str, Any]]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        if not all(isinstance(x, dict) for x in parsed):
            raise ValueError("record list must contain objects only")
        return parsed
    raise ValueError("record file must be a JSON object or array of objects")


def parse_record_json(raw: str) -> dict[str, Any]:
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("--record-json must be a JSON object")
    return parsed


def project_cube(
    store_path: pathlib.Path,
    subject: str,
    cube_id: str,
    output_path: pathlib.Path,
    offset: Optional[int],
    k_per_day: float,
    saturation_count: int,
    as_of: Optional[str],
) -> int:
    total, store_head_hash, failed = verify_store(store_path, print_rows=False)
    if failed:
        print("refusing projection: store verification failed")
        return 1

    records = read_jsonl(store_path)
    if offset is None:
        end_idx = len(records)
    else:
        if offset < 0 or offset > len(records):
            raise ValueError(f"offset must be between 0 and {len(records)}")
        end_idx = offset

    subset = records[:end_idx]
    subject_rows: list[dict[str, Any]] = []
    for row in subset:
        body = {k: v for k, v in row.items() if k != "signature"}
        if body.get("subject") == subject:
            subject_rows.append(body)

    by_id: dict[str, dict[str, Any]] = {}
    superseded_ids: set[str] = set()
    for row in subject_rows:
        rid = row["record_id"]
        by_id[rid] = row
        sup = row.get("supersedes")
        if isinstance(sup, str):
            superseded_ids.add(sup)

    active_rows = [r for rid, r in by_id.items() if rid not in superseded_ids]
    active_rows.sort(key=lambda x: (x["created"], x["record_id"]))

    if as_of:
        as_of_dt = parse_iso_utc(as_of)
    elif active_rows:
        as_of_dt = parse_iso_utc(max(r["created"] for r in active_rows))
    else:
        as_of_dt = parse_iso_utc(utc_now())

    lens_rows: dict[str, list[dict[str, Any]]] = {lens: [] for lens in sorted(LENSES)}
    for row in active_rows:
        lens_rows[row["lens"]].append(row)

    lens_contrib: dict[str, float] = {}
    for lens, rows in lens_rows.items():
        weight_sum = 0.0
        for row in rows:
            age_days = max(0.0, (as_of_dt - parse_iso_utc(row["created"])).total_seconds() / 86400.0)
            weight_sum += math.exp(-k_per_day * age_days)
        capped = min(1.0, weight_sum / float(saturation_count))
        lens_contrib[lens] = capped

    integrity_score = (sum(lens_contrib.values()) / 6.0) * 100.0
    integrity_score = round(integrity_score, 6)

    grade = "SPARSE"
    for threshold, name in GRADE_BANDS:
        if integrity_score >= threshold:
            grade = name
            break

    completeness = all(len(rows) > 0 for rows in lens_rows.values())

    cube_body: dict[str, Any] = {
        "cube_id": cube_id,
        "cube_version": "1.0.0",
        "subject": subject,
        "created": utc_now(),
        "projected_from": {
            "store_path": display_path(store_path),
            "offset": end_idx,
            "store_head_hash": store_head_hash,
            "as_of": as_of_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "store_records_total": total,
        },
        "parameters": {
            "k_per_day": k_per_day,
            "saturation_count": saturation_count,
        },
        "completeness": {
            "all_lenses_non_empty": completeness,
            "non_empty_lenses": sum(1 for rows in lens_rows.values() if rows),
            "required_lenses": 6,
        },
        "integrity": {
            "score_percent": integrity_score,
            "grade": grade,
            "lens_contribution": {k: round(v, 6) for k, v in sorted(lens_contrib.items())},
        },
        "lenses": {
            lens: [
                {
                    "record_id": row["record_id"],
                    "namespace": row["namespace"],
                    "created": row["created"],
                    "source": row["source"],
                    "assigned_by": row["assigned_by"],
                    "content": row["content"],
                }
                for row in lens_rows[lens]
            ]
            for lens in sorted(lens_rows)
        },
    }

    key = load_private_key()
    cube_signed = sign_body(cube_body, key)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(record_line(cube_signed) + "\n", encoding="utf-8")

    print(f"cube written: {display_path(output_path)}")
    print(f"completeness: {cube_signed['completeness']['all_lenses_non_empty']}")
    print(f"integrity: {cube_signed['integrity']['score_percent']} ({cube_signed['integrity']['grade']})")
    return 0


def verify_cube(cube_path: pathlib.Path) -> int:
    pub = load_public_key()
    obj = json.loads(cube_path.read_text(encoding="utf-8"))
    body = {k: v for k, v in obj.items() if k != "signature"}

    if "cube_id" not in body or not isinstance(body["cube_id"], str) or not body["cube_id"].strip():
        print("FAILED  cube schema: cube_id missing")
        return 1

    projected_from = body.get("projected_from", {})
    if not isinstance(projected_from, dict) or "offset" not in projected_from:
        print("FAILED  cube schema: projected_from.offset missing")
        return 1

    try:
        pub.verify(base64.b64decode(obj["signature"]["value"]), canonicalise(body).encode("utf-8"))
    except Exception:
        print("FAILED  cube signature invalid")
        return 1

    print(f"OK      {cube_path.name}  (cube signature valid)")
    return 0


def pin_cube(cube_path: pathlib.Path, scope: Optional[str]) -> int:
    cube_obj = json.loads(cube_path.read_text(encoding="utf-8"))
    cube_body = {k: v for k, v in cube_obj.items() if k != "signature"}

    cube_id = cube_body.get("cube_id")
    projected_from = cube_body.get("projected_from", {})
    if not isinstance(cube_id, str) or not cube_id:
        raise ValueError("cube_id missing in cube")
    if not isinstance(projected_from, dict) or "offset" not in projected_from or "store_head_hash" not in projected_from:
        raise ValueError("cube projected_from metadata incomplete")

    cube_sha = sha256_hex(cube_path.read_bytes())
    store_head_hash = str(projected_from["store_head_hash"])
    offset = int(projected_from["offset"])

    events = [
        {
            "event": "event.cube.pinned",
            "subject": cube_id,
            "sha256": cube_sha,
            "created": utc_now(),
        },
        {
            "event": "event.cube.store.checkpoint",
            "subject": f"{cube_id}@offset:{offset}",
            "sha256": store_head_hash,
            "created": utc_now(),
        },
    ]

    tmp_path = ROOT / ".datacube-pin-events.tmp.json"
    tmp_path.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")

    cmd = [sys.executable, str(ROOT / "ledger.py"), "append", "--entries-file", str(tmp_path)]
    if scope:
        cmd.extend(["--scope", scope])

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def worked_example(output_dir: pathlib.Path) -> int:
    store = output_dir / "store.jsonl"
    cube = output_dir / "example.cube.json"
    subject = "forge-stack/docs/datacube-v1"

    output_dir.mkdir(parents=True, exist_ok=True)

    records = [
        {
            "record_id": "dc-rec-0001",
            "subject": subject,
            "namespace": "domain.reference",
            "lens": "FACT",
            "content": "DataCube defines six lenses.",
            "source": "docs/datacube.md",
            "assigned_by": KEY_ID,
            "created": "2026-08-08T12:00:00Z",
        },
        {
            "record_id": "dc-rec-0002",
            "subject": subject,
            "namespace": "domain.reference",
            "lens": "COUNTER",
            "content": "Current integrity grading bands are under-specified without denominator policy.",
            "source": "docs/datacube-implementation-definition.md",
            "assigned_by": KEY_ID,
            "created": "2026-08-08T12:01:00Z",
        },
        {
            "record_id": "dc-rec-0003",
            "subject": subject,
            "namespace": "state.annotation",
            "lens": "OPINION",
            "content": "Saturation count should be ratified at 3 for first production rollout.",
            "source": "architecture-review",
            "assigned_by": "did:key:z6MktudRY5LBZJeE13BiF4BeisAwWs7gvg6srh2GwLAMKDwJ",
            "created": "2026-08-08T12:02:00Z",
        },
        {
            "record_id": "dc-rec-0004",
            "subject": subject,
            "namespace": "domain.example",
            "lens": "FICTION",
            "content": "Hypothetical future cube where every lens is fully covered.",
            "source": "design-workshop",
            "assigned_by": KEY_ID,
            "created": "2026-08-08T12:03:00Z",
        },
        {
            "record_id": "dc-rec-0005",
            "subject": subject,
            "namespace": "state.condition",
            "lens": "CONTEXT",
            "content": "Subject is specification text, not runtime telemetry.",
            "source": "docs/datacube.md",
            "assigned_by": KEY_ID,
            "created": "2026-08-08T12:04:00Z",
        },
        {
            "record_id": "dc-rec-0006",
            "subject": subject,
            "namespace": "event.open-question",
            "lens": "UNKNOWN",
            "content": "Store signing granularity (per-record vs per-batch) still pending ratification.",
            "source": "docs/datacube-implementation-definition.md",
            "assigned_by": KEY_ID,
            "created": "2026-08-08T12:05:00Z",
        },
    ]

    if store.exists():
        store.unlink()

    append_store_entries(store, records)
    verify_store(store, print_rows=True)

    rc = project_cube(
        store_path=store,
        subject=subject,
        cube_id="forge-stack/docs/datacube-v1-cube-v1",
        output_path=cube,
        offset=None,
        k_per_day=0.1009,
        saturation_count=3,
        as_of="2026-08-08T12:05:00Z",
    )
    if rc != 0:
        return rc

    rc = verify_cube(cube)
    if rc != 0:
        return rc

    # Determinism check: re-project with same params and compare bytes.
    cube_again = output_dir / "example-2.cube.json"
    rc = project_cube(
        store_path=store,
        subject=subject,
        cube_id="forge-stack/docs/datacube-v1-cube-v1",
        output_path=cube_again,
        offset=None,
        k_per_day=0.1009,
        saturation_count=3,
        as_of="2026-08-08T12:05:00Z",
    )
    if rc != 0:
        return rc

    if cube.read_bytes() != cube_again.read_bytes():
        print("FAILED  determinism check: projections differ")
        return 1

    print("OK      determinism check: projections are byte-identical")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DataCube Classify stage tooling")
    sub = p.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write", help="append record(s) to store")
    w.add_argument("--store", required=True, help="store JSONL path")
    w.add_argument("--record-file", help="JSON object or array file")
    w.add_argument("--record-json", help="inline JSON object")

    vs = sub.add_parser("verify-store", help="verify store signatures and supersedes")
    vs.add_argument("--store", required=True, help="store JSONL path")

    pj = sub.add_parser("project", help="project deterministic cube from store")
    pj.add_argument("--store", required=True, help="store JSONL path")
    pj.add_argument("--subject", required=True, help="subject to project")
    pj.add_argument("--cube-id", required=True, help="cube identity")
    pj.add_argument("--output", required=True, help="output cube file path")
    pj.add_argument("--offset", type=int, help="project from store prefix length")
    pj.add_argument("--k-per-day", type=float, default=0.1009, help="decay constant")
    pj.add_argument("--saturation-count", type=int, default=3, help="entries to saturate lens coverage")
    pj.add_argument("--as-of", help="ISO 8601 UTC time for deterministic decay")

    vc = sub.add_parser("verify-cube", help="verify cube signature and required metadata")
    vc.add_argument("--cube", required=True, help="cube path")

    pc = sub.add_parser("pin-cube", help="append cube pin events to ledger")
    pc.add_argument("--cube", required=True, help="cube path")
    pc.add_argument("--scope", help="optional consumer ledger scope for pin events")

    we = sub.add_parser("worked-example", help="run end-to-end demonstrator")
    we.add_argument("--output-dir", default="datacube/example", help="where to write example files")

    return p


def main() -> int:
    args = build_parser().parse_args()

    if args.cmd == "write":
        records: list[dict[str, Any]] = []
        if args.record_file:
            records.extend(load_records_from_json(pathlib.Path(args.record_file)))
        if args.record_json:
            records.append(parse_record_json(args.record_json))
        if not records:
            print("nothing to write: provide --record-file or --record-json")
            return 1
        return append_store_entries(pathlib.Path(args.store), records)

    if args.cmd == "verify-store":
        _, _, failed = verify_store(pathlib.Path(args.store), print_rows=True)
        return 1 if failed else 0

    if args.cmd == "project":
        if args.saturation_count <= 0:
            raise ValueError("--saturation-count must be > 0")
        if args.k_per_day < 0:
            raise ValueError("--k-per-day must be >= 0")
        return project_cube(
            store_path=pathlib.Path(args.store),
            subject=args.subject,
            cube_id=args.cube_id,
            output_path=pathlib.Path(args.output),
            offset=args.offset,
            k_per_day=args.k_per_day,
            saturation_count=args.saturation_count,
            as_of=args.as_of,
        )

    if args.cmd == "verify-cube":
        return verify_cube(pathlib.Path(args.cube))

    if args.cmd == "pin-cube":
        return pin_cube(pathlib.Path(args.cube), args.scope)

    if args.cmd == "worked-example":
        return worked_example(pathlib.Path(args.output_dir))

    return 1


if __name__ == "__main__":
    sys.exit(main())
