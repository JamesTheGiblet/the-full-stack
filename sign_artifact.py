#!/usr/bin/env python3
"""sign_artifact.py — detached Ed25519 signature over a raw file's exact bytes.

Distinct from sign.py, which signs canonicalised JSON inside an sc capsule.
This signs a file directly — appropriate for anything that isn't itself an
sc capsule (HTML, images, binaries, whatever). Produces a sidecar <file>.sig
next to the original, same base filename, so the link between file and
signature is discoverable by naming convention, not by editing the
signature value itself (which is not possible — a signature is a fixed
output over exact input bytes, not a string you can append to).

Uses the SAME key as sign.py (forge-signing.key), so both mechanisms trace
back to one identity — that's the real link, not a modified signature.

Usage:
  python sign_artifact.py path/to/file.html            # sign
  python sign_artifact.py --verify path/to/file.html    # verify against file.html.sig
"""
import base64
import json
import pathlib
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = pathlib.Path(__file__).parent
KEY_FILE = ROOT / "forge-signing.key"
PUB_FILE = ROOT / "forge-signing.pub"


def sig_path(target: pathlib.Path) -> pathlib.Path:
    return target.with_name(target.name + ".sig")


def sign(target: pathlib.Path) -> int:
    if not KEY_FILE.exists():
        print("No forge-signing.key found — run sign.py first to establish the identity.")
        return 1
    key = Ed25519PrivateKey.from_private_bytes(KEY_FILE.read_bytes())
    data = target.read_bytes()
    signature = key.sign(data)

    sidecar = {
        "signed_file": target.name,
        "file_sha256_hint": None,  # optional, filled below for human readability
        "algorithm": "Ed25519",
        "key_id": PUB_FILE.read_text().strip() if PUB_FILE.exists() else "UNKNOWN — run sign.py first",
        "value": base64.b64encode(signature).decode(),
        "note": "Detached signature over the exact raw bytes of signed_file at sign time. "
                "Distinct mechanism from sc capsule signing (which signs canonicalised JSON). "
                "Same key as every capsule in this repo — that shared identity is the link, "
                "not a modification of the signature value itself.",
    }
    import hashlib
    sidecar["file_sha256_hint"] = hashlib.sha256(data).hexdigest()

    sig_path(target).write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    print(f"signed  {target.name} -> {sig_path(target).name}")
    return 0


def verify(target: pathlib.Path) -> int:
    sp = sig_path(target)
    if not sp.exists():
        print(f"no signature found for {target.name} (expected {sp.name})")
        return 1
    sidecar = json.loads(sp.read_text())
    pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(sidecar["key_id"]))
    data = target.read_bytes()
    try:
        pub.verify(base64.b64decode(sidecar["value"]), data)
        print(f"OK      {target.name} — signature matches current file bytes exactly")
        return 0
    except Exception:
        print(f"FAILED  {target.name} — file has changed since it was signed, or signature is invalid")
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "--verify":
        sys.exit(verify(pathlib.Path(sys.argv[2])))
    sys.exit(sign(pathlib.Path(sys.argv[1])))
