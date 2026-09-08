"""forge_core — the shared, pure protocol primitives every Forge Stack
root script (sign.py, datacube.py, leighton_weight.py, hal.py, ledger.py)
and consumer needs: forge-c14n-1 canonicalisation, UTC timestamp
handling, SCP identifier validation, SHA-256 hashing, and Ed25519 key
loading/signing/verification over canonical bytes.

See consumer/ccemk2/ROADMAP.md Part II ("Forge Stack Spine Alignment")
for the phases that built this out — Phase 15/16 (extraction, root
scripts rewired), Phase 18 (real did:key signing added
sign_exported_capsule, promoted here once a second consumer needed the
identical logic). No CLI parsing, no hardcoded file paths, no
trading/domain imports — every path this package touches is passed in by
the caller.

version: 0.2.0 — added sign_exported_capsule for Phase 18/20.
"""
from forge_core.canon import (
    ISO_UTC_RE,
    SCP_ID_RE,
    canonicalise,
    format_iso_utc,
    is_ratified_scp_id,
    parse_iso_utc,
    sha256_hex,
    utc_now,
)
from forge_core.keys import (
    load_or_create_private_key,
    load_private_key,
    load_public_key,
    make_signature_block,
    public_key_b64,
    sign_canonical,
    sign_exported_capsule,
    verify_canonical,
)

__version__ = "0.2.0"

__all__ = [
    "ISO_UTC_RE",
    "SCP_ID_RE",
    "canonicalise",
    "format_iso_utc",
    "is_ratified_scp_id",
    "parse_iso_utc",
    "sha256_hex",
    "utc_now",
    "load_or_create_private_key",
    "load_private_key",
    "load_public_key",
    "make_signature_block",
    "public_key_b64",
    "sign_canonical",
    "sign_exported_capsule",
    "verify_canonical",
]
