# Build Loop

Applies the Keystone Gate pattern to code generation: a deterministic
step interpreter does the mechanical work, a local model handles the
narrow generative gaps a template can't cover, and repeated failures
that get escalated to Claude are cached as new sc capsules so the same
fix doesn't cost a fresh AI call twice. Lives inside `keystone_gate`
rather than as its own consumer because it reuses Keystone's capsule and
cache machinery directly instead of reinventing it for code specifically.

**Status: Phase 0 — documentation only.** No interpreter, no templates,
no model wiring yet. This phase exists to find the schema's edge cases
by writing example specs by hand before any code has to make those
decisions at runtime.

## Contents

- [`docs/step-spec.md`](./docs/step-spec.md) — the step-spec format: how a
  step is authored inside a README, and the edge cases it has to survive
  (unverified steps, `run_test` vs `run_command`, id stability for the
  future cache, etc).
- [`docs/step-spec.schema.json`](./docs/step-spec.schema.json) — the
  formal schema for a single step object.
- [`sc/step-spec-v1.sc.json`](./sc/step-spec-v1.sc.json) — the sc capsule
  pinning the spec doc, inheriting `forge-stack/governance-v6`. Unsigned;
  run `freeze.py` then `sign.py` when this is ready to be frozen for
  real.
- [`examples/`](./examples/) — three hand-written step-specs in the
  format: a trivial npm scaffold, a Python script with a pytest gate, and
  a spec built specifically to exercise the format's edge cases.

## Next (roadmap step 2)

Build the deterministic interpreter: read a step-spec README, walk its
steps in order, execute `create_file`/`edit_file`/`run_command` and run
`acceptance` checks — no model calls at all yet. Prove it end to end on
[`examples/01-hello-npm`](./examples/01-hello-npm/README.md) before
anything else gets added.
