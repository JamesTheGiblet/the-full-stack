# Leighton Weight

**Stage 3 of the Forge Stack spine: Trust-score.** Terminology inherited from `docs/glossary.md` via `forge-stack/governance-v1`.

Three distinct things live here, and the names never blur:

- **Forge Theory** owns the formula.
- **Leighton Weight** is the score an entity holds.
- **The Leighton Weight Engine** is the spine stage that computes it.

## Forge Theory

The theory of trust decay over time. Its decay formula:

N(t) = N₀ × e^(−kt)

Forge Theory is the universal stack foundation. The formula belongs here — not to Leighton Weight, which merely applies it.

## The Score: λ

**Leighton Weight** is the trust score an entity holds. Symbol **λ**, range 0.00–2.00. Quarantine below 0.60: no sealing authority (see `hal.md`). λ is per-entity and changes over time — computed and updated by the engine.

## The Decay Constant: k

**k** is the decay constant — always the parameter, never the score.

**k is per-domain.** It is calibrated separately for each context in which Forge Theory applies. A k calibrated on one domain (for example, k = 0.1009/day against git repositories, half-life ≈ 6.87 days) does not transfer to another. Consumers calibrate their own k against observed outcomes in their own domain.

### Symbol rule

λ = the trust score. k = the decay constant. Always lowercase, never interchanged. Standard maths notation uses λ for the decay constant; this stack does not. The distinction is enforced in every document, schema, and identifier.

## The Engine

The Leighton Weight Engine is the spine stage that computes, applies, and updates λ. The name stays with the function, not any implementation — implementations come and go; the stage does not.

## The Leighton Loop

The stack pattern that closes the trust cycle:

**score → act → observe outcomes → update score → repeat**

Trust is scored against observed outcomes, not claimed ones. Consumer implementations are instances of this pattern; the pattern itself is stack-level. Enforcement points where the loop touches runtime are specified in `docs/gate-pattern.md`.

## Decay Is a Feature

λ decays under Forge Theory. Authority, classification confidence, and trust all fade without reinforcement — deliberately. Use it or lose it. Consequences for HAL tier standing are declared in `hal.md`.

---

*Governed by `forge-stack/governance-v1` · Licence: MSL-1.0*
