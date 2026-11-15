#!/usr/bin/env python3
"""sign_v2.py — strict layer over sign.py: required artefact signatures and no fractional numbers.

Function:
    Sign layer v2 (hardening 6.2). sign.py is not edited.

    sign.py's ratified rule is that EVERY non-JSON artefact a capsule's
    document field references gets a detached .sig. But `sign.py
    --verify` walks the .sig files that exist: delete one and the
    artefact simply stops being checked, and it still exits 0 if all
    else is well. The Saboteur proved it (the-saboteur v2, threat 03).

    `python sign_v2.py --verify` runs sign.py's verification unchanged,
    then two more checks, each printing a named FAILED line:

    - S1: every document a capsule references must exist and have its
      .sig (resolved as sign.py resolves it: next to the capsule first,
      then from the repo root);
    - S2: no fractional JSON number anywhere in a capsule; a fraction
      is a fixed-place decimal string ("0.6", not 0.6). James, 2026-11-15:
      "yes" to enforcing it. The rule is in his identity capsule's
      description of forge-c14n-1 but not yet in this repo's governance.

    It exits 1 if sign.py's check or either new check fails. Without
    --verify it runs sign.py exactly as before.

    Usage: python sign_v2.py --verify [--skip-schema]
           python sign_v2.py [sign.py's own options]

Tier:     P2 (Sign), v2 layer
Depends:  sign.py
Version:  1.0.0-dev
Licence:  MSL-1.0
"""

import json
import pathlib
import runpy
import sys

ROOT = pathlib.Path(__file__).parent


def _capsules(root):
    root = pathlib.Path(root)
    return sorted(list(root.glob("sc/**/*.sc.json")) + list(root.glob("consumer/**/*.sc.json")))


def _documents(capsule):
    """Every non-.sc.json document a capsule references (sign.py's rule)."""
    found = []
    decl = capsule.get("declaration", {})
    if not isinstance(decl, dict):
        return found
    for section in (decl.get("parameters", {}), decl.get("constraints", {})):
        if not isinstance(section, dict):
            continue
        for holder in (section, section.get("terminology_authority")):
            if isinstance(holder, dict):
                doc = holder.get("document")
                if isinstance(doc, str) and doc and not doc.endswith(".sc.json"):
                    found.append(doc)
    return found


def missing_signatures(root=ROOT):
    """S1. FAILED lines for referenced documents that are missing or have no .sig."""
    root = pathlib.Path(root)
    fails = []
    for path in _capsules(root):
        try:
            capsule = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue  # sign.py's own check names an unreadable capsule
        for doc in _documents(capsule):
            candidate = path.parent / doc
            if not candidate.exists():
                candidate = root / doc
            rel = path.relative_to(root).as_posix()
            if not candidate.exists():
                fails.append(f"{doc}: referenced by {rel}, not found")
            elif not candidate.with_name(candidate.name + ".sig").exists():
                fails.append(f"{doc}: referenced by {rel}, has no .sig (every referenced artefact must be signed)")
    return sorted(set(fails))


def _walk(value, where, out):
    if isinstance(value, bool):
        return
    if isinstance(value, float):
        out.append((where, value))
    elif isinstance(value, dict):
        for k, v in value.items():
            _walk(v, f"{where}.{k}" if where else str(k), out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _walk(v, f"{where}[{i}]", out)


def fractional_numbers(root=ROOT):
    """S2. FAILED lines for every fractional JSON number in a capsule."""
    root = pathlib.Path(root)
    fails = []
    for path in _capsules(root):
        try:
            capsule = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        found = []
        _walk({k: v for k, v in capsule.items() if k != "signature"}, "", found)
        rel = path.relative_to(root).as_posix()
        for where, value in found:
            fails.append(f"{rel}: fractional number at {where}: {value!r} (use a fixed-place decimal string)")
    return fails


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--verify" not in argv:
        sys.argv = ["sign.py", *argv]
        runpy.run_path(str(ROOT / "sign.py"), run_name="__main__")
        return 0
    sys.path.insert(0, str(ROOT))
    import sign
    rc = sign.verify_all(skip_schema="--skip-schema" in argv)
    extra = missing_signatures(ROOT) + fractional_numbers(ROOT)
    for line in extra:
        print(f"FAILED  {line}")
    if extra:
        print(f"sign_v2: {len(extra)} more FAILED (artefact signatures, fractional numbers).")
    return 1 if rc or extra else 0


if __name__ == "__main__":
    sys.exit(main())
