#!/usr/bin/env python3
"""Leighton Weight Engine implementation.

Implements a DataCube-style end-to-end pipeline for Stage 3:
1) Observation writer (append-only JSONL)
2) Observation verifier (signature + supersedes integrity)
3) Deterministic lambda scorer (neutral-attractor decay)
4) Score signing + verification
5) Ledger pin helper for score materialisation
6) Worked example bootstrap command

Usage examples:
  python leighton_weight.py write --store leighton/store.jsonl --observation-file obs.json
  python leighton_weight.py verify-store --store leighton/store.jsonl
  python leighton_weight.py score --store leighton/store.jsonl --entity-id person:validator-01 \
    --score-id forge-stack/leighton/person-validator-01-score-v1 \
    --as-of 2026-08-08T15:00:00Z --output leighton/scores/validator-01.score.json
  python leighton_weight.py verify-score --score leighton/scores/validator-01.score.json
  python leighton_weight.py pin-score --score leighton/scores/validator-01.score.json
  python leighton_weight.py worked-example --output-dir leighton/example
"""

from __future__ import annotations

import argparse
import base64
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

ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


OUTCOME_INFLUENCE = {
    "succeeded": 0.20,
    "held": 0.20,
    "confirmed": 0.20,
    "failed": -0.20,
    "broke": -0.20,
    "refuted": -0.20,
}


def canonicalise(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_utc(value: str) -> datetime:
    if not ISO_UTC_RE.match(value):
        raise ValueError(f"created/as_of must be ISO 8601 UTC with Z suffix: {value}")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


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


def validate_observation_body(body: dict[str, Any]) -> None:
    required = [
        "observation_id",
        "entity_id",
        "kind",
        "outcome",
        "attester_id",
        "attester_lambda",
        "confidence",
        "created",
    ]
    for key in required:
        if key not in body:
            raise ValueError(f"missing required field: {key}")

    for key in ("observation_id", "entity_id", "kind", "outcome", "attester_id", "created"):
        if not isinstance(body.get(key), str) or not body[key].strip():
            raise ValueError(f"field '{key}' must be a non-empty string")

    if body["kind"] not in {"attestation", "observation"}:
        raise ValueError("kind must be 'attestation' or 'observation'")

    outcome = body["outcome"].strip().lower()
    if outcome not in OUTCOME_INFLUENCE:
        raise ValueError(f"outcome must be one of {sorted(OUTCOME_INFLUENCE)}")

    attester_lambda = body["attester_lambda"]
    if not isinstance(attester_lambda, (int, float)):
        raise ValueError("attester_lambda must be a number")
    if float(attester_lambda) < 0.0 or float(attester_lambda) > 2.0:
        raise ValueError("attester_lambda must be in [0.0, 2.0]")

    confidence = body["confidence"]
    if not isinstance(confidence, (int, float)):
        raise ValueError("confidence must be a number")
    if float(confidence) < 0.0 or float(confidence) > 1.0:
        raise ValueError("confidence must be in [0.0, 1.0]")

    parse_iso_utc(body["created"])

    supersedes = body.get("supersedes")
    if supersedes is not None and (not isinstance(supersedes, str) or not supersedes.strip()):
        raise ValueError("supersedes must be omitted or a non-empty string")

    source_event_hash = body.get("source_event_hash")
    if source_event_hash is not None:
        if not isinstance(source_event_hash, str) or not source_event_hash.strip():
            raise ValueError("source_event_hash must be omitted or a non-empty string")


def append_store_entries(store_path: pathlib.Path, bodies: list[dict[str, Any]]) -> int:
    key = load_private_key()
    store_path.parent.mkdir(parents=True, exist_ok=True)

    existing = read_jsonl(store_path)
    seen_ids = {str(x.get("observation_id")) for x in existing}

    signed_lines: list[str] = []
    for body in bodies:
        validate_observation_body(body)
        oid = body["observation_id"]
        if oid in seen_ids:
            raise ValueError(f"duplicate observation_id: {oid}")
        signed = sign_body(body, key)
        signed_lines.append(record_line(signed))
        seen_ids.add(oid)

    with store_path.open("a", encoding="utf-8", newline="\n") as fh:
        for line in signed_lines:
            fh.write(line + "\n")

    print(f"appended {len(signed_lines)} observation(s) to {display_path(store_path)}")
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
            validate_observation_body(body)
        except Exception as exc:
            failed += 1
            if print_rows:
                print(f"FAILED  #{idx:04d}  schema  {exc}")
            continue

        oid = body["observation_id"]
        if oid in ids:
            failed += 1
            if print_rows:
                print(f"FAILED  #{idx:04d}  duplicate observation_id  {oid}")
            continue
        ids.add(oid)

        supersedes = body.get("supersedes")
        if isinstance(supersedes, str):
            supersedes_targets.append((oid, supersedes))

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
            print(f"{status:6s} #{idx:04d}  {body['observation_id']}  {body['outcome']}  {body['entity_id']}")

        if not ok_sig:
            failed += 1

    for oid, target in supersedes_targets:
        if target not in ids:
            failed += 1
            if print_rows:
                print(f"FAILED  supersedes unresolved: {oid} -> {target}")

    if print_rows:
        print("store verifies." if failed == 0 else f"{failed} failure(s).")

    return len(records), line_hash_prev, failed


def score_entity(
    store_path: pathlib.Path,
    entity_id: str,
    score_id: str,
    as_of: str,
    output_path: pathlib.Path,
    k_per_day: float,
    neutral: float,
    floor_value: float,
    ceiling_value: float,
) -> int:
    if k_per_day < 0:
        raise ValueError("--k-per-day must be >= 0")
    if not (0.0 <= floor_value < ceiling_value <= 2.0):
        raise ValueError("floor/ceiling must satisfy 0.0 <= floor < ceiling <= 2.0")

    total, store_head_hash, failed = verify_store(store_path, print_rows=False)
    if failed:
        print("refusing score: store verification failed")
        return 1

    as_of_dt = parse_iso_utc(as_of)
    records = read_jsonl(store_path)

    entity_rows: list[dict[str, Any]] = []
    for row in records:
        body = {k: v for k, v in row.items() if k != "signature"}
        if body.get("entity_id") == entity_id and parse_iso_utc(body["created"]) <= as_of_dt:
            entity_rows.append(body)

    by_id: dict[str, dict[str, Any]] = {}
    superseded_ids: set[str] = set()
    for row in entity_rows:
        oid = row["observation_id"]
        by_id[oid] = row
        sup = row.get("supersedes")
        if isinstance(sup, str):
            superseded_ids.add(sup)

    active_rows = [r for oid, r in by_id.items() if oid not in superseded_ids]
    active_rows.sort(key=lambda x: (x["created"], x["observation_id"]))

    contributions: list[dict[str, Any]] = []
    deviation_sum = 0.0

    for row in active_rows:
        outcome_key = row["outcome"].strip().lower()
        influence = OUTCOME_INFLUENCE[outcome_key]
        age_days = max(0.0, (as_of_dt - parse_iso_utc(row["created"])).total_seconds() / 86400.0)
        decay = math.exp(-k_per_day * age_days)
        weighted_attester = clamp(float(row["attester_lambda"]) / 2.0, 0.0, 1.0)
        confidence = clamp(float(row["confidence"]), 0.0, 1.0)

        delta = influence * weighted_attester * confidence * decay
        deviation_sum += delta

        contributions.append(
            {
                "observation_id": row["observation_id"],
                "kind": row["kind"],
                "outcome": outcome_key,
                "created": row["created"],
                "age_days": round(age_days, 6),
                "attester_id": row["attester_id"],
                "attester_lambda_as_of": float(row["attester_lambda"]),
                "confidence": confidence,
                "decay_multiplier": round(decay, 8),
                "delta": round(delta, 8),
            }
        )

    lambda_value = clamp(neutral + deviation_sum, floor_value, ceiling_value)
    lambda_value = round(lambda_value, 8)

    score_body: dict[str, Any] = {
        "score_id": score_id,
        "score_version": "1.0.0",
        "entity_id": entity_id,
        "created": utc_now(),
        "as_of": as_of,
        "projected_from": {
            "store_path": display_path(store_path),
            "offset": total,
            "store_head_hash": store_head_hash,
            "store_records_total": total,
        },
        "parameters": {
            "k_per_day": k_per_day,
            "neutral": neutral,
            "floor": floor_value,
            "ceiling": ceiling_value,
            "outcome_influence": OUTCOME_INFLUENCE,
        },
        "result": {
            "lambda": lambda_value,
            "observations_used": len(active_rows),
            "deviation_sum": round(deviation_sum, 8),
        },
        "contributions": contributions,
    }

    key = load_private_key()
    score_signed = sign_body(score_body, key)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(record_line(score_signed) + "\n", encoding="utf-8")

    print(f"score written: {display_path(output_path)}")
    print(f"lambda({entity_id}, as_of={as_of}) = {score_signed['result']['lambda']}")
    print(f"observations used: {score_signed['result']['observations_used']}")
    return 0


def verify_score(score_path: pathlib.Path) -> int:
    pub = load_public_key()
    obj = json.loads(score_path.read_text(encoding="utf-8"))
    body = {k: v for k, v in obj.items() if k != "signature"}

    for key in ("score_id", "entity_id", "as_of", "result", "projected_from"):
        if key not in body:
            print(f"FAILED  score schema: missing {key}")
            return 1

    try:
        parse_iso_utc(str(body["as_of"]))
    except Exception as exc:
        print(f"FAILED  score schema: invalid as_of ({exc})")
        return 1

    result = body.get("result", {})
    if not isinstance(result, dict) or "lambda" not in result:
        print("FAILED  score schema: result.lambda missing")
        return 1

    try:
        pub.verify(base64.b64decode(obj["signature"]["value"]), canonicalise(body).encode("utf-8"))
    except Exception:
        print("FAILED  score signature invalid")
        return 1

    print(f"OK      {score_path.name}  (score signature valid)")
    return 0


def pin_score(score_path: pathlib.Path, scope: Optional[str]) -> int:
    score_obj = json.loads(score_path.read_text(encoding="utf-8"))
    score_body = {k: v for k, v in score_obj.items() if k != "signature"}

    score_id = score_body.get("score_id")
    entity_id = score_body.get("entity_id")
    projected_from = score_body.get("projected_from", {})

    if not isinstance(score_id, str) or not score_id:
        raise ValueError("score_id missing in score")
    if not isinstance(entity_id, str) or not entity_id:
        raise ValueError("entity_id missing in score")
    if not isinstance(projected_from, dict) or "offset" not in projected_from or "store_head_hash" not in projected_from:
        raise ValueError("score projected_from metadata incomplete")

    score_sha = sha256_hex(score_path.read_bytes())
    store_head_hash = str(projected_from["store_head_hash"])
    offset = int(projected_from["offset"])

    events = [
        {
            "event": "event.leighton.score.pinned",
            "subject": score_id,
            "sha256": score_sha,
            "created": utc_now(),
        },
        {
            "event": "event.leighton.store.checkpoint",
            "subject": f"{entity_id}@offset:{offset}",
            "sha256": store_head_hash,
            "created": utc_now(),
        },
    ]

    tmp_path = ROOT / ".leighton-pin-events.tmp.json"
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


def load_observations_from_json(path: pathlib.Path) -> list[dict[str, Any]]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        if not all(isinstance(x, dict) for x in parsed):
            raise ValueError("observation list must contain objects only")
        return parsed
    raise ValueError("observation file must be a JSON object or array of objects")


def parse_observation_json(raw: str) -> dict[str, Any]:
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("--observation-json must be a JSON object")
    return parsed


def worked_example(output_dir: pathlib.Path, k_per_day: float) -> int:
    store = output_dir / "store.jsonl"
    score = output_dir / "validator-01.score.json"
    score_again = output_dir / "validator-01-repeat.score.json"

    entity_id = "person:validator-01"
    score_id = "forge-stack/leighton/person-validator-01-score-v1"
    as_of = "2026-08-08T15:00:00Z"

    output_dir.mkdir(parents=True, exist_ok=True)

    observations = [
        {
            "observation_id": "lw-obs-0001",
            "entity_id": entity_id,
            "kind": "attestation",
            "outcome": "succeeded",
            "attester_id": "person:validator-99",
            "attester_lambda": 1.8,
            "confidence": 0.95,
            "source_event_hash": "E-123",
            "created": "2026-08-08T12:00:00Z",
        },
        {
            "observation_id": "lw-obs-0002",
            "entity_id": entity_id,
            "kind": "attestation",
            "outcome": "failed",
            "attester_id": "agent:monitor-04",
            "attester_lambda": 0.7,
            "confidence": 0.8,
            "source_event_hash": "E-124",
            "created": "2026-08-08T13:30:00Z",
        },
        {
            "observation_id": "lw-obs-0003",
            "entity_id": entity_id,
            "kind": "observation",
            "outcome": "confirmed",
            "attester_id": "person:validator-12",
            "attester_lambda": 1.5,
            "confidence": 0.9,
            "source_event_hash": "E-125",
            "created": "2026-08-08T14:15:00Z",
        },
    ]

    if store.exists():
        store.unlink()

    append_store_entries(store, observations)
    verify_store(store, print_rows=True)

    rc = score_entity(
        store_path=store,
        entity_id=entity_id,
        score_id=score_id,
        as_of=as_of,
        output_path=score,
        k_per_day=k_per_day,
        neutral=1.0,
        floor_value=0.0,
        ceiling_value=2.0,
    )
    if rc != 0:
        return rc

    rc = verify_score(score)
    if rc != 0:
        return rc

    rc = score_entity(
        store_path=store,
        entity_id=entity_id,
        score_id=score_id,
        as_of=as_of,
        output_path=score_again,
        k_per_day=k_per_day,
        neutral=1.0,
        floor_value=0.0,
        ceiling_value=2.0,
    )
    if rc != 0:
        return rc

    original = json.loads(score.read_text(encoding="utf-8"))
    repeat = json.loads(score_again.read_text(encoding="utf-8"))

    original_body = {k: v for k, v in original.items() if k not in {"signature", "created"}}
    repeat_body = {k: v for k, v in repeat.items() if k not in {"signature", "created"}}

    if canonicalise(original_body) != canonicalise(repeat_body):
        print("FAILED  determinism check: score projections differ")
        return 1

    print("OK      determinism check: score projections are equivalent")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Leighton Weight Engine tooling")
    sub = p.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write", help="append observation(s) to store")
    w.add_argument("--store", required=True, help="store JSONL path")
    w.add_argument("--observation-file", help="JSON object or array file")
    w.add_argument("--observation-json", help="inline JSON object")

    vs = sub.add_parser("verify-store", help="verify store signatures and supersedes")
    vs.add_argument("--store", required=True, help="store JSONL path")

    s = sub.add_parser("score", help="compute lambda for an entity at as_of")
    s.add_argument("--store", required=True, help="store JSONL path")
    s.add_argument("--entity-id", required=True, help="entity identifier")
    s.add_argument("--score-id", required=True, help="score identity")
    s.add_argument("--as-of", required=True, help="ISO 8601 UTC time for deterministic scoring")
    s.add_argument("--output", required=True, help="output score file path")
    s.add_argument("--k-per-day", type=float, required=True, help="decay constant (must be calibrated per-domain)")
    s.add_argument("--neutral", type=float, default=1.0, help="neutral attractor")
    s.add_argument("--floor", type=float, default=0.0, help="lower clamp for lambda")
    s.add_argument("--ceiling", type=float, default=2.0, help="upper clamp for lambda")

    vsc = sub.add_parser("verify-score", help="verify score signature and required metadata")
    vsc.add_argument("--score", required=True, help="score path")

    psc = sub.add_parser("pin-score", help="append score pin events to ledger")
    psc.add_argument("--score", required=True, help="score path")
    psc.add_argument("--scope", help="optional consumer ledger scope for pin events")

    we = sub.add_parser("worked-example", help="run end-to-end demonstrator")
    we.add_argument("--output-dir", default="leighton/example", help="where to write example files")
    we.add_argument("--k-per-day", type=float, default=0.1009, help="decay constant for the example")

    return p


def main() -> int:
    args = build_parser().parse_args()

    if args.cmd == "write":
        observations: list[dict[str, Any]] = []
        if args.observation_file:
            observations.extend(load_observations_from_json(pathlib.Path(args.observation_file)))
        if args.observation_json:
            observations.append(parse_observation_json(args.observation_json))
        if not observations:
            print("nothing to write: provide --observation-file or --observation-json")
            return 1
        return append_store_entries(pathlib.Path(args.store), observations)

    if args.cmd == "verify-store":
        _, _, failed = verify_store(pathlib.Path(args.store), print_rows=True)
        return 1 if failed else 0

    if args.cmd == "score":
        return score_entity(
            store_path=pathlib.Path(args.store),
            entity_id=args.entity_id,
            score_id=args.score_id,
            as_of=args.as_of,
            output_path=pathlib.Path(args.output),
            k_per_day=args.k_per_day,
            neutral=args.neutral,
            floor_value=args.floor,
            ceiling_value=args.ceiling,
        )

    if args.cmd == "verify-score":
        return verify_score(pathlib.Path(args.score))

    if args.cmd == "pin-score":
        return pin_score(pathlib.Path(args.score), args.scope)

    if args.cmd == "worked-example":
        return worked_example(pathlib.Path(args.output_dir), args.k_per_day)

    return 1


if __name__ == "__main__":
    sys.exit(main())
