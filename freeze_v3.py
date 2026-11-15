#!/usr/bin/env python3
"""freeze_v3.py — layer over freeze_v2.py: pinned document hashes must match.

Function:
    Freeze layer v3 (hardening 6.4). freeze.py and freeze_v2.py are not
    edited.

    A capsule pins a document by document_sha256, but no tool ever
    compared that hash with the document. sign.py checks the document's
    detached .sig, which is re-made whenever the document is re-signed,
    so a document could change under a capsule and every check stayed
    green. Found on 2026-11-15: governance-v2..v6 pin a glossary hash
    that never matched the committed glossary, and datacube-v1 / hal-v1
    pin their documents as they were before a two-line edit.

    `python freeze_v3.py --check` names, with a FAILED line, every live
    capsule whose pinned document:
      - does not match its pinned sha256;
      - still holds COMPUTE-ON-FREEZE (freeze_v2's check, kept);
      - does not exist.
    A superseded capsule is history and cannot be edited, so the same
    findings there are NOTE lines. Superseded means another capsule
    declares `supersedes` it, or a capsule with the same scp_id stem has
    a higher -vN. Exit 1 on any FAILED. Every other use is freeze_v2's.

    Usage: python freeze_v3.py --check
           python freeze_v3.py [freeze_v2's options]

Tier:     P3 (Freeze), v3 layer
Depends:  freeze_v2.py
Version:  1.0.0-dev
Licence:  MSL-1.0
"""

import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
PLACEHOLDER = "COMPUTE-ON-FREEZE"
_VERSION = re.compile(r"^(.*)-v(\d+)$")


def _capsules(root):
    root = pathlib.Path(root)
    out = []
    for path in sorted(list(root.glob("sc/**/*.sc.json")) + list(root.glob("consumer/**/*.sc.json"))):
        try:
            capsule = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue  # sign.py names an unreadable capsule
        if isinstance(capsule, dict):
            out.append((path, capsule))
    return out


def _supersedes(capsule):
    decl = capsule.get("declaration")
    if not isinstance(decl, dict):
        return []
    found = []
    for holder in (decl, decl.get("parameters")):
        if isinstance(holder, dict) and isinstance(holder.get("supersedes"), str):
            found.append(holder["supersedes"])
    return found


def superseded_by(capsules):
    """{scp_id: the scp_id that supersedes it}."""
    out, latest = {}, {}
    for _, c in capsules:
        sid = c.get("scp_id")
        for old in _supersedes(c):
            out.setdefault(old, sid)
        m = _VERSION.match(sid) if isinstance(sid, str) else None
        if m:
            stem, n = m.group(1), int(m.group(2))
            if stem not in latest or n > latest[stem][0]:
                latest[stem] = (n, sid)
    for _, c in capsules:
        sid = c.get("scp_id")
        m = _VERSION.match(sid) if isinstance(sid, str) else None
        if m and latest[m.group(1)][0] > int(m.group(2)):
            out.setdefault(sid, latest[m.group(1)][1])
    return out


def _pins(capsule):
    """Every {document, document_sha256} holder in a capsule."""
    decl = capsule.get("declaration")
    if not isinstance(decl, dict):
        return []
    found = []
    for section in (decl.get("parameters"), decl.get("constraints")):
        if not isinstance(section, dict):
            continue
        for holder in (section, section.get("terminology_authority")):
            if isinstance(holder, dict) and "document_sha256" in holder:
                found.append(holder)
    return found


def check(root=ROOT):
    """(fails, notes) for every pinned document hash."""
    root = pathlib.Path(root)
    capsules = _capsules(root)
    later = superseded_by(capsules)
    fails, notes = [], []
    for path, capsule in capsules:
        rel = path.relative_to(root).as_posix()
        sid = capsule.get("scp_id")
        for pin in _pins(capsule):
            doc, want = pin.get("document"), pin.get("document_sha256")
            problem = None
            if want == PLACEHOLDER:
                problem = f"{doc}: still {PLACEHOLDER}, never frozen"
            elif not isinstance(doc, str) or not doc:
                problem = "pins a hash but names no document"
            else:
                target = path.parent / doc
                if not target.exists():
                    target = root / doc
                if not target.exists():
                    problem = f"{doc}: not found"
                else:
                    got = hashlib.sha256(target.read_bytes()).hexdigest()
                    if got != want:
                        problem = (f"{doc}: pinned sha256 {str(want)[:12]}... does not match "
                                   f"the document ({got[:12]}...)")
            if problem is None:
                continue
            if sid in later:
                notes.append(f"{rel}: {problem} (superseded by {later[sid]}; history, not edited)")
            else:
                fails.append(f"{rel}: {problem}")
    return fails, notes


def main(argv=None, root=ROOT):
    argv = sys.argv[1:] if argv is None else argv
    if "--check" not in argv:
        import freeze_v2
        sys.argv = ["freeze_v2.py", *argv]
        return freeze_v2.main()
    fails, notes = check(root)
    for line in notes:
        print(f"NOTE    {line}")
    for line in fails:
        print(f"FAILED  {line}")
    if fails:
        print(f"freeze_v3: {len(fails)} FAILED (pinned document hashes).")
        return 1
    print("every live pinned document hash matches.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
