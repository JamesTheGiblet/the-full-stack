"""forge_core — the shared, pure protocol primitives every Forge Stack
root script (sign.py, datacube.py, leighton_weight.py, hal.py, ledger.py)
and consumer needs: forge-c14n-1 canonicalisation, UTC timestamp
handling, SCP identifier validation, SHA-256 hashing, and Ed25519 key
loading/signing/verification over canonical bytes.

CORE_CONSOLIDATION_ROADMAP.md Phase 0 + Phase 1. No CLI parsing, no
hardcoded file paths, no trading/domain imports — every path this
package touches is passed in by the caller. Root scripts keep owning
their own KEY_FILE/PUB_FILE/KEY_ID (each already computes these
correctly relative to its own __file__) and become thin adapters over
these functions; that rewiring is a separate, deliberately not-yet-done
step (see CORE_CONSOLIDATION_ROADMAP.md's Phase 1 exit criteria) — this
package existing does not yet change any root script's behavior.

version: 0.1.0 — Phase 0's "small versioned API."
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
    verify_canonical,
)

__version__ = "0.1.0"

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
    "verify_canonical",
]
