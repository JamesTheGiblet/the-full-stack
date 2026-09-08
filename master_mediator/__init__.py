"""Master Mediator — the spine-level half of Mediator's two-tier
architecture (consumer/ccemk2/ROADMAP.md Part II, Phase 20). Reads every
consumer's Sub-Mediator digest, classifies field maturity across
consumers, and (once a field reaches Fact, or a lens proposal arrives)
takes a proposal to HAL. A Sub-Mediator never talks to HAL directly —
only the Master does.

No CLI parsing here — see master_mediator_cli.py at the repo root for the
`python master_mediator_cli.py scan` entry point, matching the
sign.py/ledger.py/hal.py sibling-script convention. Named
master_mediator (not mediator) to avoid a real import collision with
consumer/keystone_gate/mediator/, which shares this process's sys.path.
"""
