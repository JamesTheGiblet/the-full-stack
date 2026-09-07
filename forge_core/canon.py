"""Canonicalisation (forge-c14n-1), UTC timestamp handling, and SCP
identifier validation. Pure functions only — no I/O, no file paths, no
CLI parsing (CORE_CONSOLIDATION_ROADMAP.md Phase 1).

canonicalise()/sha256_hex() were, before this extraction, duplicated
byte-for-byte across sign.py, datacube.py, leighton_weight.py, hal.py,
and ledger.py — confirmed by direct read of each file's implementation,
not assumed from the spec doc. ISO_UTC_RE/parse_iso_utc/utc_now were
duplicated across three of those five (sign.py only needed the regex,
not the parse/format pair; hal.py and ledger.py had neither). SCP_ID_RE
existed only in sign.py.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

# Matches sign.py's ISO_UTC_RE / SCP_ID_RE exactly.
ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SCP_ID_RE = re.compile(r"^[a-z0-9-]+(?:/[a-z0-9-]+)*-v[0-9]+$")


def canonicalise(obj: Any) -> str:
    """forge-c14n-1: sorted keys, compact separators, ASCII-only output."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_iso_utc(when: datetime) -> str:
    """Format an arbitrary datetime (naive treated as UTC) as the ratified
    string. utc_now() is this applied to the current instant; kept as a
    separate function since formatting a given datetime and formatting
    "now" are different callers' needs, not one call site with a default."""
    when = when.astimezone(timezone.utc) if when.tzinfo else when.replace(tzinfo=timezone.utc)
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_utc(value: str) -> datetime:
    if not ISO_UTC_RE.match(value):
        raise ValueError(f"value must be ISO 8601 UTC with a literal Z suffix: {value!r}")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def is_ratified_scp_id(scp_id: str) -> bool:
    return bool(SCP_ID_RE.match(scp_id))
