"""spec.py - Parse a step-spec README.md into an ordered list of Step objects.

Format and edge cases: ../docs/step-spec.md
Field schema: ../docs/step-spec.schema.json
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

VALID_ACTIONS = {"create_file", "edit_file", "run_command", "run_test"}
VALID_ON_FAIL = {"retry_local", "escalate"}

# Non-greedy so multiple ```step blocks in one file are each matched separately.
STEP_BLOCK_RE = re.compile(r"```step\s*\n(.*?)\n```", re.DOTALL)


class StepSpecError(ValueError):
    """Raised when a step-spec README fails to parse or fails schema validation."""


@dataclass
class Acceptance:
    command: str
    expected_exit_code: int = 0
    expected_output_pattern: Optional[str] = None


@dataclass
class Step:
    id: str
    action: str
    on_fail: str
    target: Optional[str] = None
    content: Optional[str] = None
    command: Optional[str] = None
    description: Optional[str] = None
    acceptance: Optional[Acceptance] = None
    template: Optional[str] = None
    template_params: Optional[Dict[str, Any]] = None
    patch: Optional[Dict[str, Any]] = None
    source_line: int = 0  # 1-based line the ```step block starts on, for error messages.


def parse_spec(readme_path: Path) -> List[Step]:
    """Extract and validate the ordered list of steps from a step-spec README.

    Only fenced ```step blocks are parsed; everything else in the file is
    prose for the human author and is ignored (see step-spec.md, "Why a
    README and not raw JSON").
    """
    text = readme_path.read_text(encoding="utf-8")
    steps: List[Step] = []
    seen_ids: Set[str] = set()

    for match in STEP_BLOCK_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        where = f"{readme_path}:{line_no}"
        try:
            raw = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            raise StepSpecError(f"{where}: invalid YAML in step block: {exc}") from exc

        if not isinstance(raw, dict):
            raise StepSpecError(f"{where}: step block must be a YAML mapping")

        step = _build_step(raw, where, line_no)

        if step.id in seen_ids:
            raise StepSpecError(f"{where}: duplicate step id '{step.id}'")
        seen_ids.add(step.id)
        steps.append(step)

    return steps


def _build_step(raw: Dict[str, Any], where: str, line_no: int) -> Step:
    for required in ("id", "action", "on_fail"):
        if required not in raw:
            raise StepSpecError(f"{where}: step missing required field '{required}'")

    action = raw["action"]
    if action not in VALID_ACTIONS:
        raise StepSpecError(
            f"{where}: unknown action '{action}' (expected one of {sorted(VALID_ACTIONS)})"
        )

    on_fail = raw["on_fail"]
    if on_fail not in VALID_ON_FAIL:
        raise StepSpecError(
            f"{where}: unknown on_fail '{on_fail}' (expected one of {sorted(VALID_ON_FAIL)})"
        )

    if action == "run_command" and not raw.get("command"):
        raise StepSpecError(f"{where}: action 'run_command' requires a 'command'")

    if action in ("create_file", "edit_file") and not raw.get("target"):
        raise StepSpecError(f"{where}: action '{action}' requires a 'target'")

    # "Neither" is valid for create_file/edit_file: it means this step has
    # no literal content and no matching template/patch, so it falls
    # through to the generative tier (roadmap step 4) at execution time.
    # Only "both" is a spec error - two content sources is ambiguous.
    if action == "create_file":
        if raw.get("content") is not None and raw.get("template") is not None:
            raise StepSpecError(
                f"{where}: create_file cannot set both 'content' and 'template' - "
                "pick one (or neither, to defer to the generative tier)"
            )

    if action == "edit_file":
        if raw.get("content") is not None and raw.get("patch") is not None:
            raise StepSpecError(
                f"{where}: edit_file cannot set both 'content' and 'patch' - "
                "pick one (or neither, to defer to the generative tier)"
            )
        if raw.get("patch") is not None and "type" not in raw["patch"]:
            raise StepSpecError(f"{where}: edit_file 'patch' block requires a 'type'")

    acceptance_raw = raw.get("acceptance")
    acceptance: Optional[Acceptance] = None
    if acceptance_raw is not None:
        if not isinstance(acceptance_raw, dict) or "command" not in acceptance_raw:
            raise StepSpecError(f"{where}: acceptance block requires a 'command'")
        acceptance = Acceptance(
            command=acceptance_raw["command"],
            expected_exit_code=acceptance_raw.get("expected_exit_code", 0),
            expected_output_pattern=acceptance_raw.get("expected_output_pattern"),
        )

    # Edge case 2 (step-spec.md): run_test needs a command of its own, from
    # either `command` or `acceptance.command` - it can't have neither.
    if action == "run_test" and not raw.get("command") and acceptance is None:
        raise StepSpecError(f"{where}: run_test needs either 'command' or 'acceptance.command'")

    return Step(
        id=raw["id"],
        action=action,
        on_fail=on_fail,
        target=raw.get("target"),
        content=raw.get("content"),
        command=raw.get("command"),
        description=raw.get("description"),
        acceptance=acceptance,
        template=raw.get("template"),
        template_params=raw.get("template_params"),
        patch=raw.get("patch"),
        source_line=line_no,
    )
