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
import hashlib
import json
import os
import pathlib
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = pathlib.Path(__file__).parent
# Honours FORGE_KEY_PATH exactly as sign.py does — the signing key is
# gitignored and normally lives outside this tree, so hardcoding the repo
# path (as this script used to) meant it could never find a key at all.
KEY_FILE = pathlib.Path(os.environ.get("FORGE_KEY_PATH", str(ROOT / "forge-signing.key")))
PUB_FILE = ROOT / "forge-signing.pub"
# Same value sign.py/ledger.py/hal.py/datacube.py/leighton_weight.py each
# declare. key_id is an *identifier* for the signing identity, never key
# material — the public key itself always comes from PUB_FILE. Writing the
# raw base64 pubkey here instead (as this script used to) produced sidecars
# that disagreed with every other .sig in the repo.
KEY_ID = "did:key:z6MktudRY5LBZJeE13BiF4BeisAwWs7gvg6srh2GwLAMKDwJ"


def sig_path(target: pathlib.Path) -> pathlib.Path:
    return target.with_name(target.name + ".sig")


def sign(target: pathlib.Path) -> int:
    if not KEY_FILE.exists():
        print(f"No signing key found at {KEY_FILE} — set FORGE_KEY_PATH to point at it, "
              "or run sign.py first to establish the identity.")
        return 1
    key = Ed25519PrivateKey.from_private_bytes(KEY_FILE.read_bytes())
    data = target.read_bytes()
    signature = key.sign(data)

    sidecar = {
        "signed_file": target.name,
        "file_sha256_hint": hashlib.sha256(data).hexdigest(),
        "algorithm": "Ed25519",
        "key_id": KEY_ID,
        "value": base64.b64encode(signature).decode(),
        "note": "Detached signature over the exact raw bytes of signed_file at sign time. "
                "Distinct mechanism from sc capsule signing (which signs canonicalised JSON). "
                "Same key as every capsule in this repo — that shared identity is the link, "
                "not a modification of the signature value itself.",
    }

    sig_path(target).write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    print(f"signed  {target.name} -> {sig_path(target).name}")
    return 0


def verify(target: pathlib.Path) -> int:
    sp = sig_path(target)
    if not sp.exists():
        print(f"no signature found for {target.name} (expected {sp.name})")
        return 1
    if not PUB_FILE.exists():
        print(f"no public key found at {PUB_FILE.name} — run sign.py first to establish the identity.")
        return 1
    sidecar = json.loads(sp.read_text())
    # The public key comes from PUB_FILE, exactly as sign.py's verify_all()
    # does — NOT from sidecar["key_id"], which is a did:key identifier and is
    # not decodable as key material. Reading it from key_id made this command
    # crash on every sidecar the repo actually contains.
    pub = Ed25519PublicKey.from_public_bytes(
        base64.b64decode(PUB_FILE.read_text().strip())
    )
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
