"""
cli.py - Command-Line Interface for the Keystone Gate.

This module provides CLI commands for processing, mutating, and querying
capsules as outlined in the README.md.
"""

import argparse
import json
import sys
from pathlib import Path

from .core import KeystoneGate
from .mutation import MutationEngine

# Assume the CLI is run from the root of the `consumer/keystone_gate` directory.
DEFAULT_PRIMITIVES_FILE = Path("capsule_primitives.json")
DEFAULT_CACHE_FILE = Path("capsule_cache.json")


def handle_process(args):
    """Handler for the 'process' command."""
    gate = KeystoneGate(
        primitive_file=DEFAULT_PRIMITIVES_FILE, cache_file=DEFAULT_CACHE_FILE
    )
    try:
        with args.input as f:
            capsule_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in input file: {args.input.name}", file=sys.stderr)
        return 1

    result = gate.process(capsule_data)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in ["approved", "flagged"] else 1


def handle_mutate(args):
    """Handler for the 'mutate' command."""
    gate = KeystoneGate(
        primitive_file=DEFAULT_PRIMITIVES_FILE, cache_file=DEFAULT_CACHE_FILE
    )
    mutator = MutationEngine(gate, gate.primitive_manager)

    source_ids = [item.strip() for item in args.ids.split(",")]

    try:
        new_capsule = mutator.mutate(source_ids=source_ids, operation=args.operation)
        print(json.dumps(new_capsule, indent=2))
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Keystone Gate CLI for semantic capsule governance."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Process Command ---
    parser_process = subparsers.add_parser(
        "process", help="Process an LLM output or capsule through the gate."
    )
    parser_process.add_argument(
        "--input",
        type=argparse.FileType("r"),
        required=True,
        help="Path to the input JSON file containing the capsule data.",
    )
    parser_process.set_defaults(func=handle_process)

    # --- Mutate Command ---
    parser_mutate = subparsers.add_parser("mutate", help="Perform a mutation on existing capsules.")
    parser_mutate.add_argument(
        "--ids",
        type=str,
        required=True,
        help="Comma-separated list of scp_id's for the source capsules.",
    )
    parser_mutate.add_argument(
        "--operation",
        type=str,
        required=True,
        choices=["merge", "extend", "invert", "substitute", "evolve", "optimise"],
        help="The mutation operation to perform.",
    )
    parser_mutate.set_defaults(func=handle_mutate)

    # --- Placeholder commands from README ---
    subparsers.add_parser("lineage", help="[NOT IMPLEMENTED] Show lineage for a capsule.")
    subparsers.add_parser("list", help="[NOT IMPLEMENTED] List approved capsules.")

    args = parser.parse_args()

    if hasattr(args, "func"):
        sys.exit(args.func(args))
    else:
        print(f"Command '{args.command}' is not yet implemented.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()