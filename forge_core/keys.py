"""Ed25519 key loading and signing/verification over forge-c14n-1
canonical bytes. Every function takes explicit paths/keys as arguments —
no hardcoded KEY_FILE/PUB_FILE constant, no ROOT-relative path
assumptions (CORE_CONSOLIDATION_ROADMAP.md Phase 1's "no file-path
assumptions"). Callers (root scripts, consumers) own where their keys
live and pass the path in.
"""
import base64
import json
import pathlib
from typing import Any, Dict

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from forge_core.canon import canonicalise


def load_private_key(key_path: pathlib.Path) -> Ed25519PrivateKey:
    """Fails loud if the key doesn't exist — the behavior datacube.py,
    leighton_weight.py, hal.py, and ledger.py all want."""
    if not key_path.exists():
        raise FileNotFoundError(f"key file not found: {key_path}")
    return Ed25519PrivateKey.from_private_bytes(key_path.read_bytes())


def load_or_create_private_key(key_path: pathlib.Path) -> Ed25519PrivateKey:
    """sign.py's variant: generates and persists a new key if none exists
    yet. Kept as a distinct function rather than a flag on
    load_private_key, so a caller's choice between "fail if missing" and
    "create if missing" stays visible at the call site."""
    if key_path.exists():
        return Ed25519PrivateKey.from_private_bytes(key_path.read_bytes())
    key = Ed25519PrivateKey.generate()
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption(),
        )
    )
    return key


def load_public_key(pub_path: pathlib.Path) -> Ed25519PublicKey:
    if not pub_path.exists():
        raise FileNotFoundError(f"public key file not found: {pub_path}")
    return Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_path.read_text(encoding="utf-8").strip()))


def public_key_b64(key: Ed25519PrivateKey) -> str:
    return base64.b64encode(
        key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).decode()


def sign_canonical(obj: Dict[str, Any], key: Ed25519PrivateKey) -> bytes:
    """Raw Ed25519 signature bytes over obj's canonical JSON. `obj` must
    already exclude whatever field the resulting signature will occupy
    (e.g. its own "signature" key) — this function doesn't strip one."""
    return key.sign(canonicalise(obj).encode("utf-8"))


def verify_canonical(obj: Dict[str, Any], signature_b64: str, pub: Ed25519PublicKey) -> bool:
    """True if signature_b64 verifies over obj's canonical bytes; False
    (never raises) on any malformed signature or mismatch. Callers that
    need the underlying exception should call pub.verify() directly."""
    try:
        pub.verify(base64.b64decode(signature_b64), canonicalise(obj).encode("utf-8"))
        return True
    except Exception:
        return False


def make_signature_block(obj: Dict[str, Any], key: Ed25519PrivateKey, key_id: str) -> Dict[str, str]:
    """The {key_id, algorithm, value} envelope every root script builds
    inline today — one place for that pattern instead of five."""
    signature = sign_canonical(obj, key)
    return {
        "key_id": key_id,
        "algorithm": "Ed25519",
        "value": base64.b64encode(signature).decode(),
    }


def sign_exported_capsule(path: pathlib.Path, key: Ed25519PrivateKey, key_id: str) -> None:
    """Sign an already-exported .sc.json capsule file in place, exactly
    as sign.py's own sign_all() signs each capsule it finds: read the
    file (the file is the thing being signed, not some in-memory
    object), canonicalise every field except "signature", sign, write
    the {key_id, algorithm, value} block back. Consumer-agnostic —
    originally written for consumer/ccemk2, promoted here once a second
    consumer (keystone_gate) needed the identical logic, per
    CORE_CONSOLIDATION_ROADMAP's "one tested implementation of each
    shared protocol primitive" exit criterion."""
    path = pathlib.Path(path)
    capsule = json.loads(path.read_text(encoding="utf-8"))
    body = {k: v for k, v in capsule.items() if k != "signature"}
    capsule["signature"] = make_signature_block(body, key, key_id)
    path.write_text(json.dumps(capsule, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
