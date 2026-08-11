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
import argparse
import json
import pathlib
import sys
import os
import re

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = pathlib.Path(__file__).parent
KEY_FILE = pathlib.Path(os.environ.get("FORGE_KEY_PATH", str(ROOT / "forge-signing.key")))
PUB_FILE = ROOT / "forge-signing.pub"
KEY_ID = "did:key:z6MktudRY5LBZJeE13BiF4BeisAwWs7gvg6srh2GwLAMKDwJ"
ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SCP_ID_RE = re.compile(r"^[a-z0-9-]+(?:/[a-z0-9-]+)*-v[0-9]+$")
FULL_SCP_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def is_full_v12_capsule(capsule: dict) -> bool:
    # Full capsules are identified by explicit declaration structure.
    # Version strings alone are not reliable across legacy consumer-local dialects.
    declaration = capsule.get("declaration")
    return isinstance(declaration, dict) and ("parameters" in declaration or "constraints" in declaration)


def validate_capsule_schema(capsule: dict, path: pathlib.Path):
    """Return a list of schema violations that must block signing/verifying."""
    errors = []

    if not isinstance(capsule, dict):
        return [f"{path}: capsule root must be a JSON object"]

    scp_id = capsule.get("scp_id")
    if not isinstance(scp_id, str) or not scp_id.strip():
        errors.append(f"{path}: missing required non-empty string field 'scp_id'")
    elif not SCP_ID_RE.match(scp_id):
        errors.append(
            f"{path}: scp_id must use lowercase, hyphens, and slashes, and end in -vN: {scp_id}"
        )

    created = capsule.get("created")
    if not isinstance(created, str) or not created.strip():
        errors.append(f"{path}: missing required non-empty string field 'created'")
    elif not ISO_UTC_RE.match(created):
        errors.append(f"{path}: created must be ISO 8601 UTC (YYYY-MM-DDTHH:MM:SSZ): {created}")

    if is_full_v12_capsule(capsule):
        declaration = capsule.get("declaration")
        if not isinstance(declaration, dict):
            errors.append(f"{path}: full v1.2 capsule requires object field 'declaration'")
        else:
            intent = declaration.get("intent")
            if not isinstance(intent, str) or not intent.strip():
                errors.append(f"{path}: full v1.2 capsule requires non-empty string 'declaration.intent'")

    return errors


def collect_schema_errors(capsule_paths: list[pathlib.Path]) -> list[str]:
    errors: list[str] = []
    for path in capsule_paths:
        try:
            capsule = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON ({exc})")
            continue
        errors.extend(validate_capsule_schema(capsule, path))
    return errors


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
    return sorted(
        list(ROOT.glob("sc/**/*.sc.json"))
        + list(ROOT.glob("consumer/**/*.sc.json"))
    )


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


def sign_all(skip_schema: bool = False, dry_run: bool = False) -> int:
    if KEY_ID.startswith("REPLACE"):
        print("Set KEY_ID at the top of this script first (your DID or KERI AID).")
        return 1
    key = load_or_create_key()
    pub_b64 = base64.b64encode(
        key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
    ).decode()

    if not dry_run:
        print(f"public key (b64): {pub_b64}")
        PUB_FILE.write_text(pub_b64 + "\n", encoding="utf-8")

    capsule_paths = all_capsule_paths()
    referenced_docs = set()
    schema_errors = []

    # Preflight schema gate: do not sign anything if any capsule is invalid.
    if not skip_schema:
        schema_errors = collect_schema_errors(capsule_paths)

    if schema_errors and not skip_schema:
        print("schema gate failed; refusing to sign until all capsules are fixed:")
        for err in schema_errors:
            print(f"  - {err}")
        print("Use '--skip-schema' only as a temporary escape hatch for migration passes.")
        return 1

    for path in capsule_paths:
        capsule = json.loads(path.read_text(encoding="utf-8"))
        if not dry_run:
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
        else:
            print(f"would sign  {path.name}")

        for doc in find_referenced_documents(capsule):
            referenced_docs.add((path.parent, doc))

    if referenced_docs:
        if not dry_run:
            print("\nSigning artifacts referenced by capsule document fields:")
        else:
            print("\nWould sign artifacts referenced by capsule document fields:")

        resolved_docs: set[pathlib.Path] = set()
        for parent_dir, doc_ref in sorted(referenced_docs):
            # Logic to resolve relative paths from capsule location or absolute from root
            candidate = parent_dir / doc_ref
            if not candidate.exists():
                candidate = ROOT / doc_ref
            if candidate.exists():
                resolved_docs.add(candidate.resolve())

        for doc_path in sorted(list(resolved_docs)):
            sign_artifact(key, doc_path, pub_b64)

    print("\ndone. Run 'python sign.py --verify' to prove it.")
    return 0


def verify_all(skip_schema: bool = False) -> int:
    pub = Ed25519PublicKey.from_public_bytes(
        base64.b64decode(PUB_FILE.read_text().strip())
    )
    failed = 0

    capsule_paths = all_capsule_paths()
    if not skip_schema:
        schema_errors = collect_schema_errors(capsule_paths)
        if schema_errors:
            for err in schema_errors:
                print(f"FAILED  {err}")
            failed += len(schema_errors)

    for path in capsule_paths:
        capsule = json.loads(path.read_text(encoding="utf-8"))
        if not skip_schema:
            row_errors = validate_capsule_schema(capsule, path)
            if row_errors:
                continue
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
    parser = argparse.ArgumentParser(description="Sign or verify all capsules and referenced artifacts")
    parser.add_argument("--verify", action="store_true", help="verify capsule and artifact signatures")
    parser.add_argument(
        "--skip-schema",
        action="store_true",
        help="skip schema gate (temporary migration escape hatch)",
    )
    args = parser.parse_args()
    sys.exit(verify_all(skip_schema=args.skip_schema) if args.verify else sign_all(skip_schema=args.skip_schema))
