#!/usr/bin/env python3
"""freeze_v2.py — strict layer over freeze.py: adds --check and --scan.

Function:
    Freeze layer v2. Adds verification mode to freeze.py. The original
    freeze.py has no way to ask "are there unresolved placeholders?" —
    it just fills them and exits 0. That is a silent pass.

    v2 adds:
    - --check: scan all sc/ and consumer/ .sc.json files. If ANY
      document_sha256 is still "COMPUTE-ON-FREEZE", print it and exit 1.
      Otherwise exit 0.
    - --scan: print every (capsule, document, sha256) triple for
      auditing. Exit 0.

    Default behaviour (no flag) delegates to freeze.py, so existing
    pipelines work unchanged.

Tier:     P3 (Freeze), v2 layer
Depends:  freeze.py
Version:  1.0.0
Licence:  MSL-1.0
"""

import argparse
import json
import pathlib
import sys

import freeze


ROOT = pathlib.Path(__file__).parent


def iter_capsules():
    """Yield every (path, capsule_dict) for sc/ and consumer/ capsules."""
    for capsule_path in sorted(
        list(ROOT.glob("sc/**/*.sc.json"))
        + list(ROOT.glob("consumer/**/*.sc.json"))
    ):
        try:
            capsule = json.loads(capsule_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"INVALID JSON: {capsule_path}: {e}", file=sys.stderr)
            yield capsule_path, None
            continue
        yield capsule_path, capsule


def iter_targets(capsule):
    """Yield every params dict that holds a document/document_sha256 pair."""
    params = capsule.get("declaration", {}).get("parameters", {}) \
             or capsule.get("declaration", {}).get("constraints", {})
    if not isinstance(params, dict):
        return
    if "document" in params and "document_sha256" in params:
        yield params
    ta = params.get("terminology_authority")
    if isinstance(ta, dict) and "document" in ta:
        yield ta


def cmd_check() -> int:
    """Scan for unresolved placeholders. Exit 1 if any remain."""
    unresolved = 0
    for capsule_path, capsule in iter_capsules():
        if capsule is None:
            return 1
        for t in iter_targets(capsule):
            if t.get("document_sha256") == "COMPUTE-ON-FREEZE":
                print(
                    f"UNRESOLVED: {capsule_path.name} -> {t.get('document', '?')}",
                    file=sys.stderr,
                )
                unresolved += 1
    if unresolved:
        print(f"{unresolved} unresolved placeholder(s). FAIL.", file=sys.stderr)
        return 1
    print("all document_sha256 placeholders resolved.")
    return 0


def cmd_scan() -> int:
    """Print every (capsule, document, sha256) triple. Exit 0."""
    count = 0
    for capsule_path, capsule in iter_capsules():
        if capsule is None:
            return 1
        for t in iter_targets(capsule):
            print(f"{capsule_path.name}\t{t.get('document', '?')}\t{t.get('document_sha256', '?')[:16]}")
            count += 1
    print(f"\n{count} target(s) scanned.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="freeze_v2", description="Strict freeze layer.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Exit 1 if any placeholder remains unresolved.")
    group.add_argument("--scan", action="store_true", help="Print all (capsule, doc, sha256) triples.")
    args = parser.parse_args()

    if args.check:
        return cmd_check()
    if args.scan:
        return cmd_scan()
    # Default: delegate to original freeze
    return freeze.main()


if __name__ == "__main__":
    sys.exit(main())
