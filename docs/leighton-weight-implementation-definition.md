# Leighton Weight Implementation Definition

This document defines the shipped v1 runtime behavior for the Leighton Weight Engine implementation in leighton_weight.py.

---

## 1. Scope

The implementation covers:

- append-only observation store write
- observation store signature verification
- deterministic lambda scoring at explicit as_of
- signed score artifact output
- score verification
- ledger witness pin helper
- worked example bootstrap

The implementation does not infer observations from generic ledgers automatically in v1. Observations are explicitly written to the engine store.

## 2. Commands

The CLI commands are:

- python leighton_weight.py write --store <path> --observation-file <json>
- python leighton_weight.py verify-store --store <path>
- python leighton_weight.py score --store <path> --entity-id <id> --score-id <id> --as-of <UTC_Z> --output <path>
- python leighton_weight.py verify-score --score <path>
- python leighton_weight.py pin-score --score <path> [--scope <consumer>]
- python leighton_weight.py worked-example --output-dir <path>

## 3. Observation Record Contract

Each observation entry requires:

- observation_id: unique string
- entity_id: target entity string
- kind: attestation or observation
- outcome: one of succeeded, held, confirmed, failed, broke, refuted
- attester_id: attesting entity string
- attester_lambda: number in [0.0, 2.0]
- confidence: number in [0.0, 1.0]
- created: ISO 8601 UTC timestamp with Z suffix

Optional fields:

- source_event_hash
- supersedes

Each record is signed with Ed25519 under the stack key identity.

## 4. Score Semantics

For a given entity and as_of timestamp:

1. Filter observations for the entity with created <= as_of.
2. Apply supersedes resolution so superseded observations are excluded.
3. Sort deterministically by created then observation_id.
4. Compute weighted per-observation delta and sum deviations from neutral.
5. Clamp lambda into the configured floor/ceiling range.

The scorer uses a neutral attractor at 1.00 and exponential age decay.

## 5. Influence Map and Weighting

Outcome influence map in v1:

- succeeded: +0.20
- held: +0.20
- confirmed: +0.20
- failed: -0.20
- broke: -0.20
- refuted: -0.20

Per observation:

- age_days = max(0, as_of - created)
- decay = exp(-k * age_days)
- attester weight = clamp(attester_lambda / 2.0, 0, 1)
- confidence weight = clamp(confidence, 0, 1)
- delta = influence * attester_weight * confidence_weight * decay

Final score:

lambda = clamp(neutral + sum(delta), floor, ceiling)

Default runtime parameters:

- k_per_day = 0.1009
- neutral = 1.00
- floor = 0.00
- ceiling = 2.00

## 6. Produced Artifacts

Score output is a signed JSON object containing:

- score_id, score_version, entity_id, created, as_of
- projected_from metadata (store path, offset, store head hash, total records)
- parameters
- result (lambda, observations_used, deviation_sum)
- per-observation contribution breakdown

The pin helper emits:

- event.leighton.score.pinned (score file hash)
- event.leighton.store.checkpoint (store head hash at offset)

## 7. Determinism Rule

Given the same signed store contents and identical scoring parameters including as_of, score payload fields excluding runtime created/signature must be equivalent across repeated runs.

The worked-example command executes this determinism check.

## 8. Change Discipline

Any change to scoring behavior, influence map, parameter defaults, or output schema requires:

- update to this document
- new witness capsule version
- freeze, sign, append-pins, verify cycle

---

Governed by forge-stack/governance-v3
