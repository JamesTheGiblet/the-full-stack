#!/usr/bin/env python3
"""master_mediator_cli.py — Master Mediator command-line entry point.

consumer/ccemk2/ROADMAP.md Part II, Phase 20. Matches the
sign.py/ledger.py/hal.py/datacube.py/leighton_weight.py sibling-script
convention: one-shot CLI, no daemon (the Open Question on Master's
cadence resolved this way, per the roadmap's own default assumption).

Named master_mediator (not mediator) to avoid a real Python import
collision: consumer/keystone_gate/mediator/ shares this same process's
sys.path (keystone_gate has no venv of its own, unlike CCE), so a
top-level "mediator" package here would shadow — or be shadowed by —
keystone_gate's own Sub-Mediator package depending on import order.

Usage:
  python master_mediator_cli.py scan             # discover, classify, report
  python master_mediator_cli.py scan --propose    # also export Fact-tier proposals
"""
import argparse
import pathlib
import sys

from master_mediator.classifier import TIER_FACT, classify, extract_observations
from master_mediator.discovery import load_digests
from master_mediator.proposal import export_proposal

ROOT = pathlib.Path(__file__).parent


def cmd_scan(args) -> int:
    digests = load_digests(ROOT)
    if not digests:
        print("no Sub-Mediator digests found under consumer/**/sc/*.sc.json")
        return 0

    consumers = sorted({d["declaration"].get("consumer", "unknown") for d in digests})
    print(f"discovered {len(digests)} digest(s) from {len(consumers)} consumer(s): {', '.join(consumers)}")

    observations = extract_observations(digests)
    findings = classify(observations)
    findings.sort(key=lambda f: (f.tier, f.declaration_type, f.field_key))

    print(f"\n{len(findings)} field(s) classified:")
    for finding in findings:
        key = "/".join(finding.field_key)
        print(
            f"  [{finding.tier:12s}] {finding.declaration_type:20s} {key:40s} "
            f"consumers={finding.consumers} count={finding.total_observation_count} "
            f"age={finding.max_age_days:.1f}d"
        )

    fact_findings = [f for f in findings if f.tier == TIER_FACT]
    if not fact_findings:
        print("\nno Fact-tier findings — nothing to propose to HAL.")
        return 0

    print(f"\n{len(fact_findings)} Fact-tier finding(s) ready for a spine-update proposal:")
    for finding in fact_findings:
        if args.propose:
            path = export_proposal(finding, ROOT / "sc" / "mediator")
            print(f"  wrote {path.relative_to(ROOT)} — unsigned, for human review")
        else:
            print(f"  {finding.declaration_type} {'/'.join(finding.field_key)} (pass --propose to export)")

    if args.propose:
        print(
            "\nNo Telegram/HAL integration exists at the root level yet (see "
            "ROADMAP.md's negotiation-depth Open Question) — these proposals are "
            "NOT sent anywhere automatically. A human must review each exported "
            "capsule, decide, and (if approved) manually edit the affected spine "
            "files and re-run sign.py, per Decision 5."
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Master Mediator — cross-consumer field maturity classifier")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_scan = subparsers.add_parser("scan", help="discover consumer digests, classify field maturity, report")
    p_scan.add_argument("--propose", action="store_true", help="export a spine-update proposal for every Fact-tier finding")
    p_scan.set_defaults(func=cmd_scan)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
