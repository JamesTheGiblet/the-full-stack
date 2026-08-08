# The Gate Pattern

**How the spine gets enforced.** Terminology inherited from `docs/glossary.md` via `forge-stack/governance-v1`.

The five stages are the theory; gates are the enforcement points where the theory actually stops something. A **knowledge gate** is a checkpoint that filters input before it enters state (ingress) or validates actions before they mutate the world (egress).

The gate pattern is not a spine stage. It is the pattern every stack-compliant system instantiates to make the spine bite at runtime — which makes it the most reusable piece in the stack: every build gets its own gates, but they are all instances of this one pattern.

## The Loop

```
raw input → ingress gate → current state → egress gate → world mutation → update state → repeat
```

Two gates. One protects the system's state. One protects the world.

**The world is the thing you can't undo.** Egress gates matter more than ingress gates for exactly that reason.

## Ingress Gates

Protect state from bad input. The gate asks: *should I even consider this?*

Typical instances: schema and bounds validation on generated artefacts before storage; input hardening (path, type, size) before processing; retention policy (max entries, max age) before insertion.

## Egress Gates

Protect the world from bad actions. The gate asks: *should this be allowed to happen?*

Typical instances: protection checks before destructive actions; safety limits before mutations; capability and availability checks before attempts.

For consequence classes above a consumer-defined threshold, the egress gate's answer is a HAL seal: the action waits for a signed authorisation from a validator whose tier covers it (`hal.md`).

## Current State

The live mutable snapshot of everything the system knows — its runtime context, not a database. Gates guard both doors of it: ingress gates decide what enters; egress gates decide what state is allowed to cause.

The gate guarantee only holds if gates are the *only* path. A component with raw access to state or to world-mutation handles bypasses the pattern entirely. Stack-compliant systems either wrap both behind gatekeeper APIs or explicitly document the trusted context in which raw access is permitted.

## Where the Spine Touches the Gate

| Stage | At the gate |
|---|---|
| SCP | A binding sc declares what the gate enforces — the rules, checked against inputs and outputs |
| DataCube | Classification decides which bin incoming material lands in, and whether it may enter state at all |
| Leighton Weight | λ thresholds decide whether a source, actor, or validator clears the gate |
| ChronoSCRIBE | Every gate decision — pass or block — is a ledger event |
| HAL | Above the consequence threshold, the gate demands a seal |

## Worked Instance: CobbleWright

CobbleWright (a consumer, not part of the stack) runs the full loop in Minecraft: ingress gates validate AI-generated blueprints, harden vision input, and enforce memory retention; egress gates protect player-built structures from harvesting, enforce placement bounds, and check tool availability before gathering. Its Leighton Loop scores advice against what actually changed in the world — before-state and after-state compared across the gates.

Consumer internals live in the consumer's own docs; CobbleWright appears here only as the reference instance of the pattern.

---

*Governed by `forge-stack/governance-v1` · Licence: MSL-1.0*
