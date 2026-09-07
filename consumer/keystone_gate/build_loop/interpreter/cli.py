"""cli.py - Command-line entry point for the Build Loop interpreter.

Usage:
    python -m interpreter <path-to-README.md> [--workdir DIR]

Run from consumer/keystone_gate/build_loop/. --workdir defaults to the
README's own directory (per step-spec.md); pass it explicitly to run a
spec against a scratch directory instead of wherever the README lives.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .executor import run_spec
from .spec import StepSpecError, parse_spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a Build Loop step-spec README.")
    parser.add_argument("readme", type=Path, help="Path to the step-spec README.md")
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Working directory steps run in (default: the README's own directory)",
    )
    args = parser.parse_args(argv)

    readme_path = args.readme.resolve()
    if not readme_path.exists():
        print(f"no such file: {readme_path}", file=sys.stderr)
        return 2
    workdir = (args.workdir or readme_path.parent).resolve()

    try:
        steps = parse_spec(readme_path)
    except StepSpecError as exc:
        print(f"spec error: {exc}", file=sys.stderr)
        return 2

    if not steps:
        # step-spec.md edge case 6: zero steps is a no-op success, not an error.
        print("0 steps found")
        return 0

    print(f"{len(steps)} step(s) found. workdir: {workdir}")
    results = run_spec(steps, workdir)

    failed = [r for r in results if not r.ok]
    print(f"\n{len(results)}/{len(steps)} step(s) attempted, {'FAILED' if failed else 'all passed'}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
