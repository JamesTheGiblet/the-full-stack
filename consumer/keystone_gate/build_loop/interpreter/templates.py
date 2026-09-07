"""templates.py - Deterministic content generators for create_file steps.

Every template is a pure function of its params - no model involved.
This is the tier the roadmap calls "pure substitution": scaffolding and
boilerplate that a fixed function can produce directly. See
docs/step-spec.md, "Templated tier".
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

TemplateFn = Callable[[Dict[str, Any]], str]

_REGISTRY: Dict[str, TemplateFn] = {}


def register(name: str) -> Callable[[TemplateFn], TemplateFn]:
    def deco(fn: TemplateFn) -> TemplateFn:
        _REGISTRY[name] = fn
        return fn

    return deco


def render(name: str, params: Dict[str, Any]) -> str:
    """Raises KeyError if `name` isn't registered."""
    return _REGISTRY[name](params or {})


def available() -> List[str]:
    return sorted(_REGISTRY)


@register("npm/package_json")
def _npm_package_json(params: Dict[str, Any]) -> str:
    if "name" not in params:
        raise ValueError("npm/package_json requires a 'name' param")
    data: Dict[str, Any] = {
        "name": params["name"],
        "version": params.get("version", "1.0.0"),
    }
    if params.get("private", True):
        data["private"] = True
    for optional in ("description", "scripts", "dependencies"):
        if optional in params:
            data[optional] = params[optional]
    return json.dumps(data, indent=2) + "\n"


@register("text/gitignore_node")
def _gitignore_node(_params: Dict[str, Any]) -> str:
    return "node_modules/\n*.log\n.env\n"
