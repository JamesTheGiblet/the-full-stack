# HAL - Implementation Definition

How to build the Act stage. This defines behaviour, structures and boundaries;
it does not specify code. Read alongside `hal.md`, which defines what HAL *is*.

---

## 7. What HAL does

It answers:

> **Which human is accountable for this consequence, and did they have the
> standing to authorise it?**

**Boundaries:**

- **HAL does not score.** It reads lambda from the engine.
- **HAL does not act.** It authorises; execution is elsewhere.
- **HAL does not generate consequence classes.** The stack provides the ladder;
  consumers define which rung each of their consequences sits on.

## 8. The seal

The artefact. A seal records that an identified human authorised a specific
consequence at a specific time with a specific standing.

**Minimum contents:**

| Field | Purpose |
|---|---|
| `seal_id` | Stable identity |
| `subject` | What is being authorised - `scp_id`, `cube_id`, or an action reference |
| `role` | Fact Validator or Consequence Authoriser |
| `decision` | Authorised or refused - **refusals are sealed too** |
| `authoriser` | The `did:key` of the human |
| `lambda_at_seal` | Their lambda, with its `as_of` |
| `tier_claimed` | The rung this consequence sits on |
| `created` | ISO 8601 UTC |
| `signature` | Ed25519, same canonicalisation as everything else |

Sealing a refusal matters. A ledger that records only approvals is a record of
what was permitted, not a record of what was decided, and the refusals are
usually the more interesting half.

`lambda_at_seal` is captured *into* the seal deliberately. lambda moves; the
seal must record the standing that actually applied at the moment of
authorisation, so the decision remains auditable without recomputing history.

Seals append to the ledger as `event.seal.recorded`.

## 9. Decay, tiers and retroactivity

Ratified: lambda decay eroding a tier is a feature - authority remains earned.

The implementation consequence needs stating explicitly, because the naive
reading is dangerous:

**Decay blocks future actions. It never invalidates past seals.**

A seal is a true historical record: this person, with this standing,
authorised this at this time. If their lambda later falls, that does not
retroactively un-authorise anything. It means they can no longer seal at that
tier *going forward*.

The alternative - treating past seals as invalid once standing lapses - makes
the entire audit trail unstable and means the record of what was decided
changes over time without anyone deciding anything. That is the same failure as
deleting a ledger to match a later rule.

## 10. The single-operator problem

This needs saying plainly, because the whole design presupposes something that
is not currently true.

HAL describes validator roles, a five-tier ladder, quarantine thresholds and
separation between the party who asserts and the party who authorises. **All of
that presupposes more than one human and more than one key.** Right now there
is one operator, one `did:key`, and no separation is mechanically possible.
Self-sealing is the only mode available.

That is not a flaw in the design, but pretending otherwise would be a flaw in
the record. Two honest options:

- **Declare HAL spec-ahead-of-use.** The ladder is defined for a multi-party
  future; the current deployment runs single-operator, and that is stated in
  the doc rather than left for a reader to infer. Seals are then a record of
  intent and deliberation, not a control.
- **Define single-operator mode explicitly.** Self-sealing permitted, marked as
  such in the seal (`separation: none`), so a later reader can distinguish a
  self-sealed decision from a genuinely separated one.

The second is better, and it costs one field. Without it, every seal in the
early record is ambiguous forever - and the ambiguity is precisely about the
property HAL exists to guarantee.

Tier 5's "root council" also needs an answer: whether it requires quorum, and
what a quorum of one means. Same question, sharper edge.
