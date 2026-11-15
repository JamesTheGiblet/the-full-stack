#!/usr/bin/env python3
"""sign_v3.py — layer over sign_v2.py: the number rule as governance-v7 ratifies it.

Function:
    Sign layer v3 (hardening 6.3). sign.py and sign_v2.py are not edited.

    sign_v2 enforced "no fractional JSON numbers" on every capsule, on
    James's "yes" before any governance said so. governance-v7
    (number_encoding) now ratifies the rule and says it is not
    retroactive: documents and capsules are never edited in place, so a
    capsule signed under governance-v1..v6 keeps its numbers.

    v3 applies the rule to a capsule that is covered by it:
      - a governance capsule forge-stack/governance-vN with N >= 7;
      - a capsule whose inherits is forge-stack/governance-vN, N >= 7;
      - a capsule that names no governance at all (strict by default).
    A capsule inheriting governance-v1..v6 that carries fractions gets a
    NOTE line (grandfathered), not a FAILED one. When it is revised, the
    new version inherits v7 and must use decimal strings.

    `python sign_v3.py --verify [--skip-schema]` runs sign.py's check
    unchanged, sign_v2's S1 (every referenced artefact has its .sig),
    then the v7 number rule. Exit 1 on any FAILED. Without --verify it
    runs sign.py exactly as before.

Tier:     P2 (Sign), v3 layer
Depends:  sign_v2.py
Version:  1.0.0-dev
Licence:  MSL-1.0
"""

import json
import pathlib
import re
import sys

import sign_v2

ROOT = pathlib.Path(__file__).parent
RULE_FROM = 7
_GOV = re.compile(r"^forge-stack/governance-v(\d+)$")


def _gov_number(value):
    m = _GOV.match(value) if isinstance(value, str) else None
    return int(m.group(1)) if m else None


def capsule_is_covered(capsule):
    """True if governance-v7 number_encoding applies to this capsule."""
    own = _gov_number(capsule.get("scp_id"))
    if own is not None:
        return own >= RULE_FROM
    inherited = _gov_number(capsule.get("inherits"))
    return inherited is None or inherited >= RULE_FROM


def walk_numbers(value, where, out):
    """Collect (path, value) for every fractional JSON number."""
    sign_v2._walk(value, where, out)


def fractional_numbers_v3(root=ROOT, only=None):
    """(fails, notes): fractions in covered capsules, and grandfathered ones."""
    root = pathlib.Path(root)
    fails, notes = [], []
    paths = only if only is not None else sign_v2._capsules(root)
    for path in paths:
        path = pathlib.Path(path)
        try:
            capsule = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(capsule, dict):
            continue
        found = []
        walk_numbers({k: v for k, v in capsule.items() if k != "signature"}, "", found)
        if not found:
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.as_posix()
        if capsule_is_covered(capsule):
            for where, value in found:
                fails.append(f"{rel}: fractional number at {where}: {value!r} "
                             "(governance-v7 number_encoding: use a fixed-place decimal string)")
        else:
            notes.append(f"{rel}: {len(found)} fractional numbers, grandfathered "
                         f"(inherits {capsule.get('inherits')}, before governance-v7)")
    return fails, notes


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--verify" not in argv:
        return sign_v2.main(argv)
    sys.path.insert(0, str(ROOT))
    import sign
    rc = sign.verify_all(skip_schema="--skip-schema" in argv)
    fails, notes = fractional_numbers_v3(ROOT)
    extra = sign_v2.missing_signatures(ROOT) + fails
    for line in notes:
        print(f"NOTE    {line}")
    for line in extra:
        print(f"FAILED  {line}")
    if extra:
        print(f"sign_v3: {len(extra)} more FAILED (artefact signatures, governance-v7 numbers).")
    return 1 if rc or extra else 0


if __name__ == "__main__":
    sys.exit(main())
