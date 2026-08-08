#!/usr/bin/env python3
"""sign.py — sign (and verify) every sc capsule in sc/ and consumer/**, AND
automatically detached-sign any non-JSON artifact a capsule's document field
points at (HTML, code, whatever). One command, both mechanisms.

Two distinct signature types, same key, same identity:
  - Capsule signing: Ed25519 over canonicalised JSON (RFC per scp-spec-v1.2.md §4)
  - Artifact signing: Ed25519 over a file's raw bytes directly, sidecar
    <file>.sig, same base filename so the link is discoverable at a glance

Ratified rule: EVERY non-JSON artifact referenced by a capsule's document
field gets a detached signature. Not opt-in, not case-by-case — automatic,
so it can't be forgotten the way a manual second script can be.

Usage:
  python sign.py            # sign every capsule, then every artifact they reference
  python sign.py --verify   # verify every capsule signature and every artifact sidecar
"""
import base64
import hashlib
import json
import pathlib
import sys
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = pathlib.Path(__file__).parent
KEY_FILE = pathlib.Path(os.environ.get("FORGE_KEY_PATH", str(ROOT / "forge-signing.key")))
PUB_FILE = ROOT / "forge-signing.pub"
KEY_ID = "did:key:z6MktudRY5LBZJeE13BiF4BeisAwWs7gvg6srh2GwLAMKDwJ"


def canonicalise(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_or_create_key() -> Ed25519PrivateKey:
    if KEY_FILE.exists():
        return Ed25519PrivateKey.from_private_bytes(KEY_FILE.read_bytes())
    key = Ed25519PrivateKey.generate()
    KEY_FILE.write_bytes(
        key.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
    )
    print(f"generated NEW key -> {KEY_FILE}  (back it up; never commit it)")
    return key


def all_capsule_paths():
    return sorted(list(ROOT.glob("sc/*.sc.json")) + list(ROOT.glob("consumer/**/*.sc.json")))


def sig_path(target: pathlib.Path) -> pathlib.Path:
    return target.with_name(target.name + ".sig")


def sign_artifact(key: Ed25519PrivateKey, target: pathlib.Path, pub_b64: str):
    if not target.exists():
        print(f"  ! artifact not found, skipping: {target}")
        return
    data = target.read_bytes()
    signature = key.sign(data)
    sidecar = {
        "signed_file": target.name,
        "file_sha256_hint": hashlib.sha256(data).hexdigest(),
        "algorithm": "Ed25519",
        "key_id": pub_b64,
        "value": base64.b64encode(signature).decode(),
        "note": "Detached signature over signed_file's exact raw bytes at sign time. "
                "Same key as every capsule in this repo. Automatically produced because "
                "a capsule's document field references this file — see sign.py.",
    }
    sig_path(target).write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    print(f"  artifact signed  {target.name} -> {sig_path(target).name}")


def find_referenced_documents(capsule: dict):
    """Walk a capsule's declaration for any 'document' field pointing at a
    non-.sc.json file. Handles both the flat parameters.document convention
    and the nested constraints.terminology_authority.document convention."""
    found = []
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


def sign_all() -> int:
    if KEY_ID.startswith("REPLACE"):
        print("Set KEY_ID at the top of this script first (your DID or KERI AID).")
        return 1
    key = load_or_create_key()
    pub_b64 = base64.b64encode(
        key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
    ).decode()
    print(f"public key (b64): {pub_b64}")
    PUB_FILE.write_text(pub_b64 + "\n", encoding="utf-8")

    capsule_paths = all_capsule_paths()
    referenced_docs = set()

    for path in capsule_paths:
        capsule = json.loads(path.read_text(encoding="utf-8"))
        body = {k: v for k, v in capsule.items() if k != "signature"}
        sig = key.sign(canonicalise(body).encode("utf-8"))
        capsule["signature"] = {
            "key_id": KEY_ID,
            "algorithm": "Ed25519",
            "value": base64.b64encode(sig).decode(),
        }
        path.write_text(
            json.dumps(capsule, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"signed  {path.name}")
        for doc in find_referenced_documents(capsule):
            referenced_docs.add((path.parent, doc))

    if referenced_docs:
        print("\nSigning artifacts referenced by capsule document fields:")
        for parent_dir, doc in sorted(referenced_docs):
            candidate = (parent_dir / doc) if not doc.startswith("docs/") else ROOT / doc
            if not candidate.exists():
                candidate = ROOT / doc
            sign_artifact(key, candidate, pub_b64)

    print("\ndone. Run 'python sign.py --verify' to prove it.")
    return 0


def verify_all() -> int:
    pub = Ed25519PublicKey.from_public_bytes(
        base64.b64decode(PUB_FILE.read_text().strip())
    )
    failed = 0

    for path in all_capsule_paths():
        capsule = json.loads(path.read_text(encoding="utf-8"))
        sig = capsule.get("signature", {})
        body = {k: v for k, v in capsule.items() if k != "signature"}
        try:
            pub.verify(base64.b64decode(sig["value"]), canonicalise(body).encode("utf-8"))
            print(f"OK      {path.name}")
        except Exception:
            print(f"FAILED  {path.name}")
            failed += 1

    for sig_file in sorted(ROOT.glob("**/*.sig")):
        sidecar = json.loads(sig_file.read_text())
        target = sig_file.with_name(sidecar["signed_file"])
        try:
            pub2 = Ed25519PublicKey.from_public_bytes(base64.b64decode(sidecar["key_id"]))
            pub2.verify(base64.b64decode(sidecar["value"]), target.read_bytes())
            print(f"OK      {target.name}  (artifact)")
        except Exception:
            print(f"FAILED  {target.name}  (artifact)")
            failed += 1

    print("all signatures verify." if failed == 0 else f"{failed} FAILED.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(verify_all() if "--verify" in sys.argv else sign_all())
