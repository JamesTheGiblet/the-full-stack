# HAL — Human Accountability Layer

**Stage 5 of the Forge Stack spine: Act.** Terminology inherited from `docs/glossary.md` via `forge-stack/governance-v1`.

Implementation definition: see `docs/hal-implementation-definition.md`.

Named in reference to HAL 9000. Unlike the fictional HAL, this system's authority is earned through trust (λ) and can be revoked by decay. The name is homage, not aspiration.

HAL is the stage where actions meet human authority. Humans hold Leighton Weight scores (λ) like every other entity in the stack, and occupy validator roles whose authority is earned, legible, and perishable.

## Roles

HAL recognises two core roles:

- **Fact Validator** — verifies input data.
- **Consequence Authoriser** — seals actions based on λ threshold.

These are the complete set for the current specification; future extensions may add roles.

## The Seal

The **seal** is HAL's artefact: the signed validation artefact a validator produces. It records the authorisation decision and the authoriser's identity, and is appended to the ledger. Every validation is a ledger event — no silent authority.

## Tiers

Tiers are five levels of authorisation, mapped to λ thresholds. **Tiers are defined by consequence class: the stack provides the ladder; consumers define what each rung means in their domain.** The classes below run from reversible/local to irreversible/global.

| Tier | λ range | Consequence class |
|---|---|---|
| — (quarantine) | < 0.60 | No sealing authority |
| Tier 1 | 0.60 – 0.89 | Low-consequence, easily reversible actions |
| Tier 2 | 0.90 – 1.19 | Medium-consequence, locally scoped actions |
| Tier 3 | 1.20 – 1.49 | Significant, multi-step or persistent actions |
| Tier 4 | 1.50 – 1.79 | Major, hard-to-reverse or system-wide actions |
| Tier 5 | 1.80 – 2.00 | Root council: any action, including overrides and policy changes |

A consumer maps its own actions onto these classes. In CobbleWright (the worked instance), Tier 1 covers routine block placements, Tier 3 covers blueprints and multi-step projects, Tier 4 covers large blueprints and server-wide actions — the same ladder, with rungs named in Minecraft terms.

## Decay Erodes Tier — Feature, Not Bug

λ decays over time according to Forge Theory. A Tier 3 authoriser whose λ drops below 1.20 becomes Tier 2 until their λ recovers. This is not a bug; it is the system's mechanism for ensuring authority remains earned. Dormant authority fades.

λ is regained the same way it was earned: through the Leighton Loop — actions whose observed outcomes score well. Consumers must document their domain's recovery path alongside their consequence classes, and choose their k (see `leighton-weight.md`) with decay-to-quarantine timelines in mind: a half-life tuned for one domain's activity rhythm may strip a validator unreasonably fast in another.

## Multi-Agent Coordination

The Spine governs stage interaction and agent coordination; multi-agent coordination is Spine-level, not root-level (per `forge-stack/governance-v1`). HAL's contribution to coordination is the seal: agents act, humans seal, the ledger arbitrates.

---

*Governed by `forge-stack/governance-v1` · Licence: MSL-1.0*
