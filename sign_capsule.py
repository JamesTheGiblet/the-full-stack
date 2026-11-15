#!/usr/bin/env python3
"""sign_capsule.py — sign exactly the capsules named, and nothing else.

Function:
    Hardening 6.3. sign.py signs every capsule in sc/ and consumer/** in
    one pass, so ratifying one new capsule re-signs (and rewrites) all of
    them, including unfinished consumer capsules that were left unsigned
    on purpose (keystone_gate's step-spec-v1). This tool signs only the
    paths it is given, with sign.py's own key, key_id and canonical form.

    For each path it refuses, with a named FAILED line and exit 1 before
    anything is written:
      - a capsule that already has a signature (signed capsules are
        immutable; a revision is a new capsule);
      - a capsule that fails sign.py's schema gate;
      - a fractional JSON number in a capsule the number rule covers
        (governance-v7 number_encoding; sign_v3.capsule_is_covered).
    Every check runs on every path first, so either all are signed or
    none is. Files are written atomically, LF only.

    Usage: python sign_capsule.py sc/forge-stack-governance-v7.sc.json [more.sc.json ...]
    The key is FORGE_KEY_PATH, as for sign.py.

Tier:     P2 (Sign), single-capsule tool
Depends:  sign.py, sign_v3.py, forge_core
Version:  1.0.0-dev
Licence:  MSL-1.0
"""

import json
import os
import pathlib
import sys
import tempfile

import forge_core
import sign
import sign_v3


def _check(path):
    """FAILED lines for one capsule; empty if it may be signed."""
    try:
        capsule = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{path}: unreadable: {exc}"], None
    if not isinstance(capsule, dict):
        return [f"{path}: capsule root must be a JSON object"], None
    fails = []
    if "signature" in capsule:
        fails.append(f"{path}: already signed (signed capsules are immutable; write a new version)")
    fails += [f"{e}" for e in sign.validate_capsule_schema(capsule, path)]
    if sign_v3.capsule_is_covered(capsule):
        found = []
        sign_v3.walk_numbers({k: v for k, v in capsule.items() if k != "signature"}, "", found)
        fails += [f"{path}: fractional number at {w}: {v!r} (governance-v7 number_encoding)" for w, v in found]
    return fails, capsule


def _write_lf(path, capsule):
    data = (json.dumps(capsule, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, str(path))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    paths = [pathlib.Path(a) for a in argv if not a.startswith("-")]
    if not paths:
        print("usage: python sign_capsule.py CAPSULE.sc.json [...]")
        return 2
    checked, fails = [], []
    for path in paths:
        if not path.name.endswith(".sc.json"):
            fails.append(f"{path}: not a .sc.json capsule")
            continue
        f, capsule = _check(path)
        fails += f
        checked.append((path, capsule))
    if fails:
        for line in fails:
            print(f"FAILED  {line}")
        print("nothing signed.")
        return 1
    key = sign.load_or_create_key(create=False)
    for path, capsule in checked:
        body = {k: v for k, v in capsule.items() if k != "signature"}
        capsule["signature"] = forge_core.make_signature_block(body, key, sign.KEY_ID)
        _write_lf(path, capsule)
        print(f"signed  {path}")
    print("done. Run 'python sign_v3.py --verify' to prove it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
