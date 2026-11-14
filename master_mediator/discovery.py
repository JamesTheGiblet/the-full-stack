"""Master Mediator — discovery. Finds every consumer's exported
Sub-Mediator digest by globbing consumer/**/sc/*.sc.json and filtering
for declaration.type ending in "_digest" (the convention every real
digest producer built so far follows: usage_digest, chronoscribe_digest,
leighton_digest, hal_digest, primitive_digest). Read-only — never writes
anywhere, matching every other Mediator component's discipline.

consumer/ccemk2/ROADMAP.md Part II, Phase 20 ("Master Mediator —
Maturity Classifier"). No CLI parsing, no trading imports — pure
discovery + loading.
"""
import json
from pathlib import Path
from typing import Any, Dict, List


def find_digest_paths(root: Path) -> List[Path]:
    """Every *.sc.json under consumer/**/sc/ whose declaration.type ends
    in "_digest". Malformed or unreadable files are skipped, not raised —
    discovery must survive one consumer's broken capsule (see
    keystone_gate's build_loop/ example) without failing for everyone
    else."""
    root = Path(root)
    found = []
    for path in sorted(root.glob("consumer/**/sc/*.sc.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        decl_type = data.get("declaration", {}).get("type", "")
        if isinstance(decl_type, str) and decl_type.endswith("_digest"):
            found.append(path)
    return found


def load_digests(root: Path) -> List[Dict[str, Any]]:
    """Load every discovered digest capsule as a plain dict — the Master
    doesn't need CCE's ScEnvelope/Pydantic machinery any more than
    Keystone Gate's own digest producer did; it only ever reads the
    already-exported, already-schema-valid JSON files.

    A capsule that vanishes, breaks or stops being a digest between
    discovery and loading is skipped, as discovery itself skips one
    (hardening 6.1, M3): one consumer's file must never stop the scan."""
    digests = []
    for path in find_digest_paths(root):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            continue
        decl_type = data.get("declaration", {}).get("type", "") if isinstance(data, dict) else ""
        if not (isinstance(decl_type, str) and decl_type.endswith("_digest")):
            continue
        data["_source_path"] = str(path)
        digests.append(data)
    return digests
