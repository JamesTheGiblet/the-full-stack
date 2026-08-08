#!/usr/bin/env python3
"""ledger.py - append and verify ChronoSCRIBE's hash-chained ledger.

This is intentionally separate from genesis.py:
  - genesis.py mints the first immutable batch.
  - ledger.py verifies and appends subsequent immutable batches.

Usage:
  python ledger.py verify
  python ledger.py [--scope <consumer>] append --event <event> --subject <subject> --sha256 <hex>
  python ledger.py append --entries-file entries.json
  python ledger.py append-pins
"""

import argparse
import base64
import hashlib
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone
from typing import Iterable, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = pathlib.Path(__file__).parent
KEY_FILE = pathlib.Path(os.environ.get("FORGE_KEY_PATH", str(ROOT / "forge-signing.key")))
PUB_FILE = ROOT / "forge-signing.pub"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
KEY_ID = "did:key:z6MktudRY5LBZJeE13BiF4BeisAwWs7gvg6srh2GwLAMKDwJ"


def canonicalise(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_seq(seq_value) -> str:
    try:
        return f"{int(seq_value):02d}"
    except (TypeError, ValueError):
        return "??"


def parse_entries(lines: list[str]) -> list[dict]:
    out = []
    for i, line in enumerate(lines):
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"ledger line {i + 1} is not valid JSON: {exc}") from exc
    return out


def entry_identity(entry: dict) -> tuple[str, str, str]:
    return (
        str(entry.get("event", "")),
        str(entry.get("subject", "")),
        str(entry.get("sha256", "")),
    )


def find_referenced_documents(capsule: dict) -> list[str]:
    """Collect non-.sc.json document references from known declaration fields."""
    found: list[str] = []
    decl = capsule.get("declaration", {})
    for section in (decl.get("parameters", {}), decl.get("constraints", {})):
        if not isinstance(section, dict):
            continue
        doc = section.get("document")
        if doc and not doc.endswith(".sc.json"):
            found.append(doc)
        ta = section.get("terminology_authority")
        if isinstance(ta, dict):
            doc2 = ta.get("document")
            if doc2 and not doc2.endswith(".sc.json"):
                found.append(doc2)
    return found


def get_ledger_path(scope: Optional[str]) -> pathlib.Path:
    if not scope:
        return ROOT / "ledger.jsonl"
    return ROOT / "consumer" / scope / "ledger.jsonl"


def read_ledger_lines(ledger_path: pathlib.Path) -> list[str]:
    if not ledger_path.exists():
        return []
    text = ledger_path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    return text.splitlines()


def verify_chain(ledger_path: pathlib.Path, print_rows: bool = True) -> tuple[int, str, set[tuple[str, str, str]], int]:
    # If a ledger file doesn't exist, it's not an error; it's a new chain.
    # Return the genesis state.
    if not ledger_path.exists():
        return 0, "GENESIS", set(), 0
    if not PUB_FILE.exists():
        raise FileNotFoundError("forge-signing.pub not found")

    pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(PUB_FILE.read_text().strip()))

    lines = read_ledger_lines(ledger_path)
    entries = parse_entries(lines)
    prev = "GENESIS"
    failed = 0
    seen: set[tuple[str, str, str]] = set()

    for i, entry in enumerate(entries):
        sig = entry.get("signature")
        body = {k: v for k, v in entry.items() if k != "signature"}

        ok_chain = body.get("prev") == prev
        ok_sig = False
        if isinstance(sig, dict) and "value" in sig:
            try:
                pub.verify(base64.b64decode(sig["value"]), canonicalise(body).encode("utf-8"))
                ok_sig = True
            except Exception:
                ok_sig = False

        status = "OK    " if (ok_chain and ok_sig) else "FAILED"
        if not (ok_chain and ok_sig):
            failed += 1
            detail = []
            if not ok_chain:
                detail.append("chain")
            if not ok_sig:
                detail.append("signature")
            status += f" ({','.join(detail)})"

        seq = body.get("seq", "?")
        event = str(body.get("event", ""))
        subject = str(body.get("subject", ""))
        if print_rows:
            print(f"{status}  #{format_seq(seq)}  {event:24s}  {subject}")

        prev = sha256_hex(lines[i].encode("utf-8"))
        seen.add(entry_identity(body))

    if print_rows:
        if failed == 0:
            print("chain and signatures verify.")
        else:
            print(f"{failed} entries FAILED.")

    next_seq = (entries[-1].get("seq", -1) + 1) if entries else 0
    return next_seq, prev, seen, failed


def validate_candidate(entry: dict) -> None:
    for k in ("event", "subject", "sha256"):
        if k not in entry or not str(entry[k]).strip():
            raise ValueError(f"missing required field: {k}")
    if not SHA256_RE.match(str(entry["sha256"])):
        raise ValueError(f"sha256 must be lowercase 64-char hex: {entry['sha256']}")

    # Attestations have an extra body that needs validation
    if entry.get("event") == "event.attestation.issued":
        if "body" not in entry or "outcome" not in entry["body"]:
            raise ValueError("attestation entries must have a body with an outcome")


def validate_capsule_document_hashes(capsule: dict, capsule_path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    decl = capsule.get("declaration", {})
    if not isinstance(decl, dict):
        return errors

    for section_name in ("parameters", "constraints"):
        section = decl.get(section_name, {})
        if not isinstance(section, dict):
            continue

        if "document" in section and "document_sha256" in section:
            digest = str(section.get("document_sha256", "")).strip()
            if digest == "COMPUTE-ON-FREEZE":
                errors.append(
                    f"{capsule_path}: unresolved placeholder document_sha256 for {section.get('document')}"
                )
            elif not SHA256_RE.match(digest):
                errors.append(
                    f"{capsule_path}: invalid document_sha256 for {section.get('document')} ({digest})"
                )

        ta = section.get("terminology_authority")
        if isinstance(ta, dict) and "document" in ta and "document_sha256" in ta:
            digest = str(ta.get("document_sha256", "")).strip()
            if digest == "COMPUTE-ON-FREEZE":
                errors.append(
                    f"{capsule_path}: unresolved placeholder terminology_authority.document_sha256 for {ta.get('document')}"
                )
            elif not SHA256_RE.match(digest):
                errors.append(
                    f"{capsule_path}: invalid terminology_authority.document_sha256 for {ta.get('document')} ({digest})"
                )

    return errors


def sign_body(key: Ed25519PrivateKey, body: dict) -> dict:
    sig = key.sign(canonicalise(body).encode("utf-8"))
    signed = dict(body)
    signed["signature"] = {
        "key_id": KEY_ID,
        "algorithm": "Ed25519",
        "value": base64.b64encode(sig).decode(),
    }
    return signed


def append_entries(candidates: Iterable[dict], ledger_path: pathlib.Path, allow_duplicates: bool, dry_run: bool = False) -> int:
    if not KEY_FILE.exists():
        print(f"key file not found: {KEY_FILE}")
        return 1

    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    # If creating a new consumer ledger, anchor it to the root ledger's head.
    is_new_consumer_ledger = not ledger_path.exists() and ledger_path.name != "ledger.jsonl"
    if is_new_consumer_ledger:
        print(f"New consumer ledger; anchoring to root ledger head...")
        root_ledger_path = get_ledger_path(None)
        _, root_head, _, root_failed = verify_chain(root_ledger_path, print_rows=False)
        next_seq, prev, seen, failed = 0, root_head, set(), root_failed
    else:
        next_seq, prev, seen, failed = verify_chain(ledger_path, print_rows=False)
    if failed:
        print("refusing append: ledger verify failed; repair chain first")
        return 1

    key = Ed25519PrivateKey.from_private_bytes(KEY_FILE.read_bytes())

    created_default = utc_now()
    appended = 0
    skipped = 0
    new_lines: list[str] = []

    for raw in candidates:
        validate_candidate(raw)

        ident = entry_identity(raw)
        if not allow_duplicates and ident in seen:
            skipped += 1
            print(f"SKIP    duplicate  {raw['event']}  {raw['subject']}")
            continue

        body = {
            "seq": next_seq,
            "created": str(raw.get("created", created_default)),
            "event": str(raw["event"]),
            "subject": str(raw["subject"]),
            "sha256": str(raw["sha256"]),
            "prev": prev,
        }
        # For attestations, embed the attestation body inside the ledger entry body
        # This makes the attestation's content part of the signed, auditable record.
        if raw.get("event") == "event.attestation.issued" and "body" in raw:
            body["body"] = raw["body"]
        signed = sign_body(key, body)
        line = canonicalise(signed)
        new_lines.append(line)

        prev = sha256_hex(line.encode("utf-8"))
        seen.add(ident)
        action = "WOULD   " if dry_run else "APPEND  "
        print(f"{action}#{next_seq:02d}  {body['event']:24s}  {body['subject']}")
        next_seq += 1
        appended += 1

    if new_lines and not dry_run:
        with ledger_path.open("a", encoding="utf-8", newline="\n") as fh:
            for line in new_lines:
                fh.write(line + "\n")

    mode = "dry-run" if dry_run else "live"
    print(f"append complete for {ledger_path.relative_to(ROOT)} ({mode}): {appended} {'would append' if dry_run else 'appended'}, {skipped} skipped")
    return 0


def digest_docs_and_capsules(scope: Optional[str]) -> list[dict]:
    items: list[dict] = []
    if scope:
        # Consumer scope: only capsules within that consumer's directory
        cap_paths = sorted(list((ROOT / "consumer" / scope).glob("**/*.sc.json")))
    else:
        # Root scope: only capsules in sc/, excluding consumer/
        cap_paths = sorted(list((ROOT / "sc").glob("**/*.sc.json")))

    placeholder_errors: list[str] = []
    for cap in cap_paths:
        capsule_obj = json.loads(cap.read_text(encoding="utf-8"))
        placeholder_errors.extend(validate_capsule_document_hashes(capsule_obj, cap))

    if placeholder_errors:
        joined = "\n".join(f"  - {err}" for err in placeholder_errors)
        raise ValueError(
            "append-pins refused: unresolved or invalid capsule document hashes detected:\n"
            + joined
        )

    referenced_docs: set[tuple[pathlib.Path, str]] = set()
    for cap in cap_paths:
        capsule_obj = json.loads(cap.read_text(encoding="utf-8"))
        for doc_ref in find_referenced_documents(capsule_obj):
            referenced_docs.add((cap.parent, doc_ref))

    resolved_docs: dict[str, pathlib.Path] = {}
    for parent_dir, doc_ref in referenced_docs:
        candidate = (parent_dir / doc_ref) if not doc_ref.startswith("docs/") else (ROOT / doc_ref)
        if not candidate.exists():
            candidate = ROOT / doc_ref
        if candidate.exists():
            subject = f"docs/{candidate.name}" if candidate.parent == (ROOT / "docs") else str(candidate.relative_to(ROOT)).replace("\\", "/")
            resolved_docs[subject] = candidate

    for subject in sorted(resolved_docs):
        doc = resolved_docs[subject]
        items.append(
            {
                "event": "event.document.pinned",
                "subject": subject,
                "sha256": sha256_hex(doc.read_bytes()),
            }
        )

    for cap in cap_paths:
        obj = json.loads(cap.read_text(encoding="utf-8"))
        items.append(
            {
                "event": "event.capsule.pinned",
                "subject": obj.get("scp_id", cap.name),
                "sha256": sha256_hex(cap.read_bytes()),
            }
        )
    return items


def load_entries_file(path: pathlib.Path) -> list[dict]:
    data = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in data.splitlines() if line.strip()]
    parsed = json.loads(data)
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return parsed
    raise ValueError("entries file must be JSON object/list or JSONL lines")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify and append ChronoSCRIBE ledger entries")
    sub = parser.add_subparsers(dest="command", required=True)

    p_verify = sub.add_parser("verify", help="verify full ledger chain and signatures")
    p_verify.add_argument("--scope", help="Operate on a specific consumer ledger. Defaults to root.")

    p_append = sub.add_parser("append", help="append one or more custom events")
    p_append.add_argument("--scope", help="Operate on a specific consumer ledger. Defaults to root.")
    p_append.add_argument("--event", help="event name (e.g., event.capsule.pinned)")
    p_append.add_argument("--subject", help="event subject")
    p_append.add_argument("--sha256", help="sha256 digest (64-char lowercase hex)")
    p_append.add_argument("--created", help="timestamp override (default: now UTC)")
    p_append.add_argument("--entries-file", help="JSON/JSONL file of entries to append")
    p_append.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="allow appending entries that already exist by event+subject+sha256",
    )
    p_append.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and preview append operations without writing to ledger.jsonl",
    )

    p_pins = sub.add_parser(
        "append-pins",
        help="append pins for all capsules and their referenced documents within the current scope (root or consumer) idempotently",
    )
    p_pins.add_argument("--scope", help="Operate on a specific consumer ledger. Defaults to root.")
    p_pins.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="allow appending duplicate pin entries",
    )
    p_pins.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and preview append operations without writing to ledger.jsonl",
    )

    p_attest = sub.add_parser("attest", help="issue an attestation about a prior ledger event")
    p_attest.add_argument("--scope", help="Operate on a specific consumer ledger. Defaults to root.")
    p_attest.add_argument("subject_event_hash", help="The SHA256 hash of the ledger entry being attested to.")
    p_attest.add_argument("outcome", help="The outcome of the attestation (e.g., 'succeeded', 'failed', 'confirmed').")
    p_attest.add_argument("--rationale", help="An optional, human-readable justification for the outcome.")
    p_attest.add_argument("--dry-run", action="store_true", help="Preview the attestation without writing to the ledger.")
    p_attest.add_argument("--allow-duplicates", action="store_true", help="Allow issuing a duplicate attestation.")


    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ledger_path = get_ledger_path(args.scope)

    if args.command == "verify":
        _, _, _, failed = verify_chain(ledger_path, print_rows=True)
        return 1 if failed else 0

    if args.command == "append-pins":
        try:
            candidates = digest_docs_and_capsules(args.scope)
        except ValueError as exc:
            print(str(exc))
            return 1
        return append_entries(
            candidates=candidates,
            ledger_path=ledger_path,
            allow_duplicates=args.allow_duplicates,
            dry_run=args.dry_run,
        )

    if args.command == "attest":
        attestation_body = {
            "attester_id": KEY_ID,
            "outcome": args.outcome,
        }
        if args.rationale:
            attestation_body["rationale"] = args.rationale

        candidate = {
            "event": "event.attestation.issued",
            "subject": args.subject_event_hash,
            "sha256": sha256_hex(canonicalise(attestation_body).encode("utf-8")),
            "body": attestation_body,
        }
        return append_entries(
            candidates=[candidate],
            ledger_path=ledger_path,
            allow_duplicates=args.allow_duplicates,
            dry_run=args.dry_run,
        )

    if args.command == "append":
        entries: list[dict] = []
        if args.entries_file:
            entries.extend(load_entries_file(pathlib.Path(args.entries_file)))

        if args.event or args.subject or args.sha256:
            if not (args.event and args.subject and args.sha256):
                print("when appending a single entry, --event --subject --sha256 are all required")
                return 1
            single = {
                "event": args.event,
                "subject": args.subject,
                "sha256": args.sha256,
            }
            if args.created:
                single["created"] = args.created
            entries.append(single)

        if not entries:
            print("nothing to append: provide --entries-file or --event/--subject/--sha256")
            return 1

        return append_entries(
            candidates=entries,
            ledger_path=ledger_path,
            allow_duplicates=args.allow_duplicates,
            dry_run=args.dry_run,
        )

    return 1


if __name__ == "__main__":
    sys.exit(main())
