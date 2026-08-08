# Design — The Leighton Weight Engine

This document outlines the design and core principles for the Leighton Weight Engine, the third stage of the Forge Stack spine.

---

## 1. What the engine does

It answers:

> How much is this entity's word worth right now?

"Right now" is the whole design. λ is a function of time, not a property of a record.

**Boundaries:**

- The engine does not classify. It consumes cubes; it does not decide which lens anything belongs in.
- The engine does not authorise. It produces a number. Whether that number is sufficient for an action is HAL's question.
- The engine does not store λ. See §3 — this is the mistake to avoid.

## 2. What holds a λ

Ratified: λ is the trust score an entity holds. Implementation needs the set of entity classes fixed before anything is written, because the calibration of k differs per class and cannot be retrofitted.

**Proposed classes:**

| Class  | Example          | What its λ means                         |
| :----- | :--------------- | :--------------------------------------- |
| Person | a HAL validator  | How much their validation is worth       |
| Agent  | a bot, a script  | How much its automated output is worth   |
| Source | a feed, a repository | How much material originating there is worth |

A capsule does not hold λ. A capsule is signed or it is not; that is a binary cryptographic fact, and giving artefacts a trust score confuses provenance with reliability. Cubes do not hold λ either — they carry an integrity grade, which is a different measure of a different thing. Keep the two vocabularies apart in code as strictly as they are kept apart in the glossary.

## 3. λ is computed, never stored

This is the same architectural decision as cube-as-projection, and for the same reason.

Decay means λ changes continuously with no event occurring. A stored λ is therefore wrong the moment after it is written, and a system that reads stored λ values is reading stale numbers that look authoritative.

So:

> observation stream (entity, up to time t) → compute → λ(t)

- Store observations. Append-only, signed, same discipline as the ledger.
- Compute λ on read, always with an explicit `as_of` timestamp.
- Any λ quoted anywhere must carry its `as_of`. A bare λ in a log line, a seal, or a report is meaningless.

An observation records: the entity, what happened, the outcome, who observed it, and when. Nothing else. Interpretation is the engine's job, not the record's.

## 4. The Leighton Loop

Score → observe outcomes → update. Implementation needs each arrow defined.

- **Score.** Compute λ from the observation stream at `as_of`, applying N(t) = N₀ × e^(−kt) to each observation's contribution.
- **Observe outcomes.** This is the arrow that does not currently exist anywhere in the stack, and it is the hard part. An outcome is a later judgement about an earlier claim or action: the validated fact held or it did not; the authorised build worked or it broke.
- **Update.** Nothing to update, because nothing is stored. The next computation simply includes the new observation. This is the payoff of §3.

Without a mechanism that closes this arrow, the engine is a decay function applied to nothing. Define, before building:

- What generates outcome observations
- How long after the fact they may arrive
- Whether an outcome can itself be disputed, and what happens if so

## 5. Scale and starting position

λ runs 0.00–2.00, with quarantine below 0.60 and Tier 1 beginning there.

Two things need ratifying:

- **What N₀ is for a new entity.** If a new entity starts at 0.00, it is quarantined until it earns its way out — which is defensible ("authority remains earned") but means a new participant can do nothing at all, including the things that would generate the observations that raise their λ. That is a deadlock, and it needs an explicit answer: either a sponsored entry (an existing Tier 4+ entity vouches, generating an initial observation), or a provisional band below Tier 1 where limited action generates history.
- **What 1.00 means.** The scale is not a probability and not a percentage. If 1.00 is "neutral, no evidence either way", then decay toward 0 is decay toward distrust, which is a strong claim — an entity that simply goes quiet becomes untrusted rather than unknown. If instead decay pulls toward a neutral floor, absence is treated as absence. Pick one and write it down; the difference changes what the whole stage means.

## 6. Calibrating k

Ratified: k is per-domain and calibrated separately. The git-repo figure of 0.1009/day (half-life ~6.87 days) does not transfer.

Implementation needs a stated method, because "calibrate it" is not a procedure. Minimum: a domain declares its k in a capsule, with the reasoning and the data it was derived from recorded alongside. An uncalibrated deployment should refuse to compute λ rather than silently using someone else's constant — inheriting the git-repo k by default is exactly the failure this rule exists to prevent.

k is never written as λ.