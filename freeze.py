#!/usr/bin/env python3
"""freeze.py — fill document hashes into their sc capsules.

Run at freeze time, after all docs are final and VERIFY markers are
resolved. Replaces every COMPUTE-ON-FREEZE placeholder with the real
SHA-256 of the referenced document. Signing remains a separate, local
step (see scp-spec-v1.2.md section 4).

Usage: python3 freeze.py  (from the repo root; expects docs/ and capsules
adjacent — adjust PATHS if your layout differs)
"""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent

def sha256_of(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    changed = 0
    for capsule_path in sorted(
        list(ROOT.glob("sc/**/*.sc.json"))
        + list(ROOT.glob("consumer/**/*.sc.json"))
    ):
        capsule = json.loads(capsule_path.read_text(encoding="utf-8"))
        params = capsule.get("declaration", {}).get("parameters", {}) \
                 or capsule.get("declaration", {}).get("constraints", {})
        # governance capsule keeps its pin under constraints.terminology_authority
        targets = []
        if isinstance(params, dict):
            if "document" in params and "document_sha256" in params:
                targets.append(params)
            ta = params.get("terminology_authority")
            if isinstance(ta, dict) and "document" in ta:
                targets.append(ta)
        for t in targets:
            if t.get("document_sha256") != "COMPUTE-ON-FREEZE":
                continue
            doc = ROOT / t["document"].replace("docs/", "")
            if not doc.exists():
                doc = ROOT / t["document"]
            if not doc.exists():
                print(f"MISSING: {t['document']} (referenced by {capsule_path.name})")
                return 1
            t["document_sha256"] = sha256_of(doc)
            changed += 1
            print(f"{capsule_path.name}: {t['document']} -> {t['document_sha256'][:16]}…")
        capsule_path.write_text(
            json.dumps(capsule, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(f"filled {changed} hash(es). Now sign each capsule locally.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
