# ChronoSCRIBE

**Stage 4 of the Forge Stack spine: Audit.** Terminology inherited from `docs/glossary.md` via `forge-stack/governance-v1`.

**SCRIBE — Signed Chronological Record of Immutable Behavioural Events.** The expansion earns the caps; every word is true of the mechanism: entries are Ed25519-signed, hash-chained in time order, append-only, and record events.

Full name always in formal docs; no shortening. ("Chrono" is permitted only in informal chat.) Not to be confused with ChronoMotion, a separate motion-generation project. "Scribe" alone is a retired term and is never reused.

## The Ledger

ChronoSCRIBE's artefact is the **ledger**: the authoritative, time-ordered, hash-chained record of state changes. The word "ledger" is reserved for ChronoSCRIBE throughout the stack — DataCube's append-only record is a store, never a ledger.

What lands in the ledger:

- Every document and capsule hash (the immutability rule's enforcement point)
- Every seal a HAL validator produces
- State-change events from stack components

## Mechanism

- **Hash chaining** — each entry commits to its predecessor; tampering with history breaks the chain visibly.
- **Signing** — entries carry Ed25519 signatures under the same canonicalisation and signing procedure as capsules (`scp-spec-v1.2.md` §4 — resolve the VERIFY markers there before citing this).
- **Export** — W3C PROV / JSON-LD, so provenance is consumable outside the stack. Provenance is ChronoSCRIBE's job; individual capsules do not carry provenance blocks.

## Role in the Spine

ChronoSCRIBE makes the rest of the spine honest. SCP declares, DataCube classifies, the Leighton Weight Engine scores — and the ledger proves what happened and when, including that the decay clock itself is running honestly. Without the audit stage, decay values and trust scores are assertions; with it, they are verifiable history.

---

*Governed by `forge-stack/governance-v1` · Licence: MSL-1.0*
