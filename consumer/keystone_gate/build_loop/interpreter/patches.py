"""patches.py - Deterministic, known-pattern edits for edit_file steps.

Each patch type is a pure function of (current file text, params) -> new
file text - no model involved. This covers the subset of edit_file work
that's a recognisable pattern rather than an open-ended instruction; see
docs/step-spec.md, "Templated tier".
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

PatchFn = Callable[[str, Dict[str, Any]], str]

_REGISTRY: Dict[str, PatchFn] = {}


def register(patch_type: str) -> Callable[[PatchFn], PatchFn]:
    def deco(fn: PatchFn) -> PatchFn:
        _REGISTRY[patch_type] = fn
        return fn

    return deco


def apply(patch_type: str, text: str, params: Dict[str, Any]) -> str:
    """Raises KeyError if `patch_type` isn't registered."""
    return _REGISTRY[patch_type](text, params or {})


def available() -> List[str]:
    return sorted(_REGISTRY)


@register("set_json_field")
def _set_json_field(text: str, params: Dict[str, Any]) -> str:
    """Set a (possibly dotted) key path in a JSON object to a value."""
    if "path" not in params or "value" not in params:
        raise ValueError("set_json_field requires 'path' and 'value' params")
    data = json.loads(text)
    keys = str(params["path"]).split(".")
    node = data
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = params["value"]
    return json.dumps(data, indent=2) + "\n"
