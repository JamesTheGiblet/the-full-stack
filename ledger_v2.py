#!/usr/bin/env python3
"""ledger_v2.py — strict layer over ledger.py: named broken rows and replays.

Function:
    Ledger layer v2 (hardening 6.2). ledger.py is not edited.

    - L1: ledger.py's parse_entries raises a clear ValueError for a row
      that is not valid JSON, but `ledger.py verify` never catches it,
      so a ledger cut mid-row ends in a Python traceback, not a named
      error (the-saboteur v2, threat 05).
    - L2: ledger.py checks the chain and each signature but has no
      replay check: a row copied onto the end is reported only as a
      broken chain (threat 12). A signature covers its row's seq and
      prev, so two rows with the same signature value are the same
      signed row twice: a replay.

    `python ledger_v2.py verify [--scope S]` reads the ledger first and
    prints one FAILED line per broken row (with its line number) and per
    replay (naming both lines), exiting 1. If the ledger reads cleanly
    it runs ledger.py's verify unchanged, and any exception it raises
    becomes a FAILED line and exit 1, never a traceback. Every other
    command is ledger.py's.

    Note: ledger.py's verify_chain skips blank lines when parsing but
    indexes the raw lines when hashing, so a blank line in the middle
    shifts every hash after it. precheck() names a blank line inside
    the ledger as a warning-level FAILED so it is fixed, not hidden.

Tier:     P4 (Ledger / ChronoSCRIBE), v2 layer
Depends:  ledger.py
Version:  1.0.0 (frozen 2026-11-15)
Licence:  MSL-1.0
"""

import json
import pathlib
import sys

import ledger


def precheck(ledger_path):
    """FAILED lines for rows that are not JSON, replays, and inner blank lines."""
    path = pathlib.Path(ledger_path)
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8").splitlines()
    while raw and not raw[-1].strip():
        raw.pop()
    fails, seen = [], {}
    for n, line in enumerate(raw, 1):
        if not line.strip():
            fails.append(f"{path.name} line {n}: blank line inside the ledger (it shifts every later hash)")
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            fails.append(f"{path.name} line {n}: not valid JSON, truncated or corrupted ({exc.msg})")
            continue
        sig = row.get("signature") if isinstance(row, dict) else None
        value = sig.get("value") if isinstance(sig, dict) else None
        if isinstance(value, str) and value:
            if value in seen:
                fails.append(f"{path.name} line {n}: replay — same signed row as line {seen[value]}")
            else:
                seen[value] = n
    # A blank line in the middle was ledger.py's tolerated legacy; only name it
    # when something else is wrong too, so existing ledgers keep verifying.
    if all("blank line" in f for f in fails):
        return []
    return fails


def _scope(argv):
    for i, a in enumerate(argv):
        if a == "--scope" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--scope="):
            return a.split("=", 1)[1]
    return None


def main():
    argv = sys.argv[1:]
    if argv[:1] == ["verify"]:
        path = ledger.get_ledger_path(_scope(argv))
        fails = precheck(path)
        if fails:
            for line in fails:
                print(f"FAILED  {line}")
            print(f"{len(fails)} entries FAILED.")
            return 1
        try:
            return ledger.main()
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 1
        except Exception as exc:  # named, never a traceback
            print(f"FAILED  {path.name}: {type(exc).__name__}: {exc}")
            return 1
    return ledger.main()


if __name__ == "__main__":
    sys.exit(main())
