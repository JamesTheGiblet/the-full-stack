#!/usr/bin/env python3
"""genesis.py — create ChronoSCRIBE's ledger and write the genesis entries.

The ledger is append-only JSONL (ledger.jsonl). Each entry is:
  - hash-chained: prev = SHA-256 of the previous entry's full line
    (genesis entries chain from the literal string "GENESIS")
  - signed: Ed25519 over the §4 canonical form of the entry body
    (everything except the signature), same key as the capsules.

Genesis seeds the ledger with every document and capsule hash in the
frozen v1 set — the audit stage witnessing its own constitution.

Usage:
  python genesis.py           # create ledger.jsonl (refuses if it exists)
  python genesis.py --verify  # verify the chain and every signature
"""
import base64
import hashlib
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = pathlib.Path(__file__).parent
LEDGER = ROOT / "ledger.jsonl"
KEY_FILE = pathlib.Path(os.environ.get("FORGE_KEY_PATH", str(ROOT / "forge-signing.key")))
PUB_FILE = ROOT / "forge-signing.pub"


def canonicalise(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def genesis() -> int:
    if LEDGER.exists():
        print("ledger.jsonl already exists — genesis.py is genesis-only and will not overwrite it. Use ledger.py to append.")
        return 1
    key = Ed25519PrivateKey.from_private_bytes(KEY_FILE.read_bytes())
    key_id = "did:key-holder"  # informational; identity is proven by signature
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    subjects = []
    for doc in sorted((ROOT / "docs").glob("*.md")):
        subjects.append(("event.document.pinned", f"docs/{doc.name}", sha256_hex(doc.read_bytes())))
    for cap in sorted((ROOT / "sc").glob("*.sc.json")):
        c = json.loads(cap.read_text(encoding="utf-8"))
        subjects.append(("event.capsule.pinned", c.get("scp_id", cap.name), sha256_hex(cap.read_bytes())))

    prev = "GENESIS"
    lines = []
    for seq, (event, subject, digest) in enumerate(subjects):
        body = {
            "seq": seq,
            "created": now,
            "event": event,
            "subject": subject,
            "sha256": digest,
            "prev": prev,
        }
        sig = key.sign(canonicalise(body).encode("utf-8"))
        entry = dict(body)
        entry["signature"] = {
            "algorithm": "Ed25519",
            "value": base64.b64encode(sig).decode(),
        }
        line = canonicalise(entry)
        lines.append(line)
        prev = sha256_hex(line.encode("utf-8"))

    LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"ledger.jsonl created: {len(lines)} genesis entries, chain head {prev[:16]}…")
    return 0


def verify() -> int:
    pub = Ed25519PublicKey.from_public_bytes(
        base64.b64decode(PUB_FILE.read_text().strip())
    )
    prev = "GENESIS"
    failed = 0
    for i, line in enumerate(LEDGER.read_text(encoding="utf-8").splitlines()):
        entry = json.loads(line)
        sig = entry.pop("signature")
        ok_chain = entry.get("prev") == prev
        try:
            pub.verify(base64.b64decode(sig["value"]), canonicalise(entry).encode("utf-8"))
            ok_sig = True
        except Exception:
            ok_sig = False
        status = "OK    " if (ok_chain and ok_sig) else "FAILED"
        if not (ok_chain and ok_sig):
            failed += 1
            detail = [] if ok_chain else ["chain"]
            detail += [] if ok_sig else ["signature"]
            status += f" ({','.join(detail)})"
        print(f"{status}  #{entry['seq']:02d}  {entry['event']:24s}  {entry['subject']}")
        prev = sha256_hex(line.encode("utf-8"))
    print("chain and signatures verify." if failed == 0 else f"{failed} entries FAILED.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(verify() if "--verify" in sys.argv else genesis())
