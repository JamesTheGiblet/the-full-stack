#!/usr/bin/env python3
"""HAL (Human Accountability Layer) implementation.

Implements the end-to-end pipeline for Stage 5:
1) Seal writer (creates a signed authorisation decision)
2) Seal verifier (validates signature)
3) Ledger pin helper for seal materialisation

Usage examples:
  python hal.py seal --subject-event-hash <hash> --decision allow --tier-req 4 \
    --authoriser-lambda 1.8 --output my.seal.json
  python hal.py verify-seal --seal my.seal.json
  python hal.py pin-seal --seal my.seal.json
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
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

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

TIER_MIN_LAMBDA = {
    1: 0.60,
    2: 0.90,
    3: 1.20,
    4: 1.50,
    5: 1.80,
}


def canonicalise(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def sign_body(body: dict[str, Any], key: Ed25519PrivateKey) -> dict[str, Any]:
    sig = key.sign(canonicalise(body).encode("utf-8"))
    out = dict(body)
    out["signature"] = {
        "key_id": KEY_ID,
        "algorithm": "Ed25519",
        "value": base64.b64encode(sig).decode(),
    }
    return out


def create_seal(
    seal_id: str,
    subject_event_hash: str,
    decision: str,
    tier_req: int,
    authoriser_score_path: pathlib.Path,
    rationale: Optional[str],
    output_path: pathlib.Path,
) -> int:
    if not SHA256_RE.match(subject_event_hash):
        raise ValueError("subject_event_hash must be a valid SHA-256 hash")
    if decision not in {"allow", "deny"}:
        raise ValueError("decision must be 'allow' or 'deny'")
    if not (1 <= tier_req <= 5):
        raise ValueError("tier_req must be between 1 and 5")

    # Verify the score file and extract the lambda value
    if verify_seal(authoriser_score_path, quiet=True) != 0:
        print(f"FAILED  authoriser score file signature is invalid: {authoriser_score_path}")
        return 1

    score_obj = json.loads(authoriser_score_path.read_text(encoding="utf-8"))
    authoriser_lambda = score_obj.get("result", {}).get("lambda")
    if not isinstance(authoriser_lambda, (int, float)):
        raise ValueError("authoriser score file is missing 'result.lambda'")

    authoriser_id_from_score = score_obj.get("entity_id")
    if not isinstance(authoriser_id_from_score, str) or not authoriser_id_from_score:
        raise ValueError("authoriser score file is missing 'entity_id'")

    min_lambda_for_tier = TIER_MIN_LAMBDA[tier_req]
    if authoriser_lambda < min_lambda_for_tier:
        print(f"FAILED  authoriser lambda {authoriser_lambda} is insufficient for Tier {tier_req} (requires {min_lambda_for_tier})")
        return 1

    seal_body = {
        "seal_id": seal_id,
        "seal_version": "1.0.0",
        "created": utc_now(),
        "authoriser_id": authoriser_id_from_score,
        "sealing_key_id": KEY_ID, # The key that actually signed this seal
        "authoriser_lambda": authoriser_lambda,
        "subject_event_hash": subject_event_hash,
        "decision": decision,
        "separation": "none" if authoriser_id_from_score == KEY_ID else "verified",
        "tier_requirement": tier_req,
    }
    if rationale:
        seal_body["rationale"] = rationale

    key = load_private_key()
    seal_signed = sign_body(seal_body, key)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonicalise(seal_signed) + "\n", encoding="utf-8")

    print(f"seal written: {display_path(output_path)}")
    return 0


def verify_seal(seal_path: pathlib.Path, quiet: bool = False) -> int:
    pub = load_public_key()
    obj = json.loads(seal_path.read_text(encoding="utf-8"))
    body = {k: v for k, v in obj.items() if k != "signature"}

    # A score file has a different schema than a seal file.
    required_keys = ("seal_id", "subject_event_hash", "decision", "separation") if "seal_id" in body else ("score_id", "entity_id", "result")
    for key in required_keys:
        if key not in body:
            if not quiet: print(f"FAILED  artifact schema: missing {key}")
            return 1

    try:
        pub.verify(base64.b64decode(obj["signature"]["value"]), canonicalise(body).encode("utf-8"))
    except Exception:
        if not quiet: print(f"FAILED  {seal_path.name} signature invalid")
        return 1

    print(f"OK      {seal_path.name}  (seal signature valid)")
    return 0


def pin_seal(seal_path: pathlib.Path, scope: Optional[str]) -> int:
    seal_obj = json.loads(seal_path.read_text(encoding="utf-8"))
    seal_body = {k: v for k, v in seal_obj.items() if k != "signature"}

    seal_id = seal_body.get("seal_id")
    if not isinstance(seal_id, str) or not seal_id:
        raise ValueError("seal_id missing in seal")

    seal_sha = sha256_hex(seal_path.read_bytes())

    event = {
        "event": "event.hal.seal.pinned",
        "subject": seal_id,
        "sha256": seal_sha,
        "created": utc_now(),
    }

    tmp_path = ROOT / ".hal-pin-events.tmp.json"
    tmp_path.write_text(json.dumps([event], indent=2) + "\n", encoding="utf-8")

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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="HAL (Human Accountability Layer) tooling")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("seal", help="create a new signed authorisation seal")
    s.add_argument("--seal-id", required=True, help="unique identifier for this seal")
    s.add_argument("--subject-event-hash", required=True, help="SHA-256 hash of the ledger event being authorised")
    s.add_argument("--decision", required=True, choices=["allow", "deny"], help="the authorisation decision")
    s.add_argument("--tier-req", required=True, type=int, help="the required HAL tier for this decision (1-5)")
    s.add_argument("--authoriser-score-file", required=True, help="path to the authoriser's signed Leighton Weight score file")
    s.add_argument("--rationale", help="optional human-readable justification")
    s.add_argument("--output", required=True, help="output seal file path")

    vs = sub.add_parser("verify-seal", help="verify a seal's signature")
    vs.add_argument("--seal", required=True, help="path to the seal file")

    ps = sub.add_parser("pin-seal", help="append a seal pin event to a ledger")
    ps.add_argument("--seal", required=True, help="path to the seal file")
    ps.add_argument("--scope", help="optional consumer ledger scope for the pin event")

    return p


def main() -> int:
    args = build_parser().parse_args()

    if args.cmd == "seal":
        return create_seal(
            seal_id=args.seal_id,
            subject_event_hash=args.subject_event_hash,
            decision=args.decision,
            tier_req=args.tier_req,
            authoriser_score_path=pathlib.Path(args.authoriser_score_file),
            rationale=args.rationale,
            output_path=pathlib.Path(args.output),
        )

    if args.cmd == "verify-seal":
        return verify_seal(pathlib.Path(args.seal))

    if args.cmd == "pin-seal":
        return pin_seal(pathlib.Path(args.seal), args.scope)

    return 1


if __name__ == "__main__":
    sys.exit(main())