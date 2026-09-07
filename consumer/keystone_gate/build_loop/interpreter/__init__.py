"""interpreter - The Build Loop deterministic step-walker.

Reads a step-spec README (see ../docs/step-spec.md) and executes its
steps in order: file writes and shell commands only, no model calls.
That comes later (roadmap steps 3-4); this package is the known-good
baseline everything else builds on.
"""

from .spec import Step, Acceptance, StepSpecError, parse_spec
from .executor import StepResult, AcceptanceResult, StepExecutionError, run_spec

__all__ = [
    "Step",
    "Acceptance",
    "StepSpecError",
    "parse_spec",
    "StepResult",
    "AcceptanceResult",
    "StepExecutionError",
    "run_spec",
]
