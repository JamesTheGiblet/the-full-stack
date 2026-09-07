"""executor.py - Deterministic step-walker for Build Loop step-specs.

Executes create_file / edit_file / run_command / run_test steps in order
and checks each against its acceptance test where one exists. No model
calls happen here: `on_fail` is recorded on every result but not acted
on yet - retry_local (roadmap step 5) and escalate (roadmap step 6) both
require a model in the loop. For now, any failure just stops the run.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from . import patches, templates
from .spec import Acceptance, Step

DIFF_HEADER_RE = re.compile(r"^(---|\+\+\+|@@)\s", re.MULTILINE)


class StepExecutionError(RuntimeError):
    """The step's action could not be carried out (bad spec, bad env, or the action command itself failed)."""


@dataclass
class AcceptanceResult:
    passed: bool
    exit_code: int
    output: str
    reason: Optional[str] = None


@dataclass
class StepResult:
    step: Step
    ran: bool
    acceptance: Optional[AcceptanceResult]
    error: Optional[str] = None

    @property
    def unverified(self) -> bool:
        return self.ran and self.error is None and self.acceptance is None

    @property
    def ok(self) -> bool:
        if self.error is not None:
            return False
        if self.acceptance is None:
            return self.ran
        return self.acceptance.passed


def run_spec(steps: List[Step], workdir: Path, log: Callable[[str], None] = print) -> List[StepResult]:
    """Run steps in order, stopping at the first failure.

    workdir is the spec's working directory - step-spec.md documents this
    as defaulting to the README's own directory, but callers (tests, the
    CLI's --workdir) may point it elsewhere so a proof run doesn't write
    into the repo.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    results: List[StepResult] = []

    for step in steps:
        log(f"[{step.id}] {step.action} ...")
        try:
            _execute_action(step, workdir)
        except StepExecutionError as exc:
            result = StepResult(step=step, ran=False, acceptance=None, error=str(exc))
            results.append(result)
            log(f"[{step.id}] FAILED (on_fail={step.on_fail}, not yet wired): {exc}")
            break

        if step.acceptance is None:
            log(f"[{step.id}] ran unverified (no acceptance test)")
            results.append(StepResult(step=step, ran=True, acceptance=None))
            continue

        acceptance_result = _check_acceptance(step.acceptance, workdir)
        results.append(StepResult(step=step, ran=True, acceptance=acceptance_result))

        if acceptance_result.passed:
            log(f"[{step.id}] PASS")
        else:
            log(
                f"[{step.id}] FAILED acceptance (on_fail={step.on_fail}, not yet wired): "
                f"{acceptance_result.reason}"
            )
            break

    return results


def _execute_action(step: Step, workdir: Path) -> None:
    if step.action == "create_file":
        _create_file(step, workdir)
    elif step.action == "edit_file":
        _edit_file(step, workdir)
    elif step.action == "run_command":
        _run(step.command, _resolve_cwd(step, workdir))
    elif step.action == "run_test":
        if step.command:
            _run(step.command, _resolve_cwd(step, workdir))
        # else: acceptance.command below IS the action (step-spec.md edge case 2).
    else:  # pragma: no cover - spec.py rejects unknown actions before this runs
        raise StepExecutionError(f"unknown action '{step.action}'")


def _resolve_cwd(step: Step, workdir: Path) -> Path:
    cwd = workdir / step.target if step.target else workdir
    if not cwd.exists():
        raise StepExecutionError(f"working directory '{cwd}' does not exist")
    return cwd


def _create_file(step: Step, workdir: Path) -> None:
    target = workdir / step.target
    if target.exists():
        # step-spec.md edge case 3: fail fast rather than overwrite, so a
        # partial re-run stops at the first step it hasn't done yet.
        raise StepExecutionError(
            f"create_file target '{step.target}' already exists (use edit_file for existing files)"
        )
    content = _resolve_create_content(step)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _resolve_create_content(step: Step) -> str:
    if step.content is not None:
        return step.content
    if step.template is None:
        # spec.py allows content and template to both be absent - it means
        # no template matches this step, so it needs the generative tier.
        raise StepExecutionError(
            f"create_file step '{step.id}' has no literal content and no template - this "
            "needs the generative tier (roadmap step 4), not available in the deterministic "
            "interpreter"
        )
    try:
        return templates.render(step.template, step.template_params or {})
    except KeyError:
        raise StepExecutionError(
            f"create_file step '{step.id}' references unknown template '{step.template}' "
            f"(available: {', '.join(templates.available()) or 'none'})"
        )
    except ValueError as exc:
        raise StepExecutionError(f"create_file step '{step.id}' template error: {exc}") from exc


def _edit_file(step: Step, workdir: Path) -> None:
    target = workdir / step.target
    if not target.exists():
        raise StepExecutionError(f"edit_file target '{step.target}' does not exist")

    if step.patch is not None:
        _apply_patch(step, target)
        return

    if step.content is None:
        # spec.py allows content and patch to both be absent - it means no
        # patch matches this step, so it needs the generative tier.
        raise StepExecutionError(
            f"edit_file step '{step.id}' has no content and no patch - this needs the "
            "generative tier (roadmap step 4), not available in the deterministic interpreter"
        )

    if DIFF_HEADER_RE.search(step.content):
        raise StepExecutionError(
            f"edit_file step '{step.id}' provides a unified diff; diff application isn't "
            "implemented in the deterministic interpreter yet"
        )
    raise StepExecutionError(
        f"edit_file step '{step.id}' provides a free-text instruction with no known patch "
        "type - this needs the generative tier (roadmap step 4), not available in the "
        "deterministic interpreter"
    )


def _apply_patch(step: Step, target: Path) -> None:
    patch_type = step.patch.get("type")
    params = {k: v for k, v in step.patch.items() if k != "type"}
    try:
        new_text = patches.apply(patch_type, target.read_text(encoding="utf-8"), params)
    except KeyError:
        raise StepExecutionError(
            f"edit_file step '{step.id}' references unknown patch type '{patch_type}' "
            f"(available: {', '.join(patches.available()) or 'none'})"
        )
    except (ValueError, json.JSONDecodeError) as exc:
        raise StepExecutionError(f"edit_file step '{step.id}' patch error: {exc}") from exc
    target.write_text(new_text, encoding="utf-8")


def _run(command: str, cwd: Path) -> None:
    proc = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise StepExecutionError(
            f"command failed (exit {proc.returncode}): {command}\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
        )


def _check_acceptance(acceptance: Acceptance, workdir: Path) -> AcceptanceResult:
    proc = subprocess.run(acceptance.command, shell=True, cwd=workdir, capture_output=True, text=True)
    output = proc.stdout + proc.stderr

    if proc.returncode != acceptance.expected_exit_code:
        return AcceptanceResult(
            passed=False,
            exit_code=proc.returncode,
            output=output,
            reason=f"exit code {proc.returncode} != expected {acceptance.expected_exit_code}",
        )

    if acceptance.expected_output_pattern and not re.search(acceptance.expected_output_pattern, output):
        return AcceptanceResult(
            passed=False,
            exit_code=proc.returncode,
            output=output,
            reason=f"output did not match pattern '{acceptance.expected_output_pattern}'",
        )

    return AcceptanceResult(passed=True, exit_code=proc.returncode, output=output)
