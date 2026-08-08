# Forge Stack Glossary

> This glossary defines the Forge Stack. Projects built on the stack (CobbleWright, ChronoMotion, etc.) are consumers; their internal terminology is defined in their own repositories. The glossary is not a directory of projects.

All stack documentation inherits this glossary via the root governance capsule. Terms are defined exactly once, here. Content revisions to this document create a new capsule identity (`-vN` suffix bump); this document is never edited in place.

---

## The Stack

**Forge Stack** — The five-stage spine architecture: SCP, DataCube, Leighton Weight, ChronoSCRIBE, and HAL. The foundational protocol and component set upon which all stack-compliant systems are built. Written "the Forge Stack" in prose, `forge_stack` in code and repository contexts, "the stack" informally.

**Spine** — The five stages in order: Declare (SCP) → Classify (DataCube) → Trust-score (Leighton Weight) → Audit (ChronoSCRIBE) → Act (HAL).

**System/artefact symmetry** — Each stage pairs a formally named system with a lowercase artefact noun: SCP → sc, DataCube → cube, ChronoSCRIBE → ledger, HAL → seal. Leighton Weight's output is a number (λ) and keeps its symbol.

---

## Stage 1 — Declare

**SCP** — Semantic Capsule Protocol. Not to be confused with Secure Copy Protocol or the SCP Foundation; spelled out at first use in every document. The protocol for producing, validating, and consuming sc artefacts. Protocol layer only. Always capitalised.

**sc** — The artefact: the individual Semantic Capsule an SCP process produces. Always lowercase. File extension `.sc.json`, no exceptions.

**capsule** — Permitted informal synonym for sc in prose. Never appears in schemas, filenames, or code.

**SCP Lite** — Protocol subset. A conforming capsule is a "Lite sc." The protocol has modes; the artefact is always just an sc. Signature mandatory, as for all capsules.

**binding** — A subtype of sc that governs trust, permissions, or integration between systems. Written "binding sc" in prose or metadata. Extension remains `.sc.json`.

---

## Stage 2 — Classify

**DataCube** — The classification system. One word, camel case. Classifies inputs through six lenses.

**cube** — The artefact. Lowercase, parallel to sc. Every cube must fill all six lenses to be complete.

**Six Lenses** — The classification mechanism inside DataCube. Refers to the mechanism, not the component; retired as a stage name.

**lens** — One of the six classification axes: FACT, COUNTER, OPINION, FICTION, CONTEXT, UNKNOWN. Lenses are bins material is sorted into, not scores.

**COUNTER** — Counterevidence. The lens that holds material contradicting a proposition or hypothesis. Supporting evidence lives in FACT. An empty COUNTER bin is a signal that disconfirming evidence has not been sought.

**Cube namespaces** — `event.*`, `state.*`, `domain.*`, `behaviour.*`. Internal cube key spaces, distinct from lens names; the overlap between `state.*` and consumer-side "current state" is incidental and crosses component boundaries. In formal docs, always specify which taxonomy is meant.

**store** — DataCube's append-only record of classifications and decisions. Never called a ledger; that term is reserved for ChronoSCRIBE.

**Integrity grades** — CRYSTALLINE (90%+), COHERENT (70–89%), FORMING (40–69%), SPARSE (<40%). Grades a cube's completeness across its lenses.

---

## Stage 3 — Trust-score

**Forge Theory** — The theory of trust decay over time, including the decay formula N(t) = N₀ × e^(−kt). Universal stack foundation; the formula belongs here, not to Leighton Weight.

**Leighton Weight** — The trust score an entity holds. Symbol λ, range 0.00–2.00, quarantine below 0.60. Per entity; computed and updated by the engine.

**Leighton Weight Engine** — The spine stage that computes, applies, and updates λ. The name stays with the function, not any implementation.

**λ** — The trust score. Always lowercase. Always the value, never the decay constant.

**k** — The decay constant. Always lowercase. Always the parameter, never the trust score. Per-domain: calibrated separately for each context in which Forge Theory applies. A k calibrated on one domain (e.g. git repositories) does not transfer to another.

**Leighton Loop** — The stack pattern of scoring, observing outcomes, and updating scores. Universal pattern; consumer implementations are instances of it.

---

## Stage 4 — Audit

**ChronoSCRIBE** — SCRIBE: Signed Chronological Record of Immutable Behavioural Events. The spine stage that maintains the authoritative time-ordered ledger of state changes, with hash chaining and signed entries. Full name always in formal docs; no shortening. "Chrono" permitted only in informal chat. Not to be confused with ChronoMotion (a separate motion-generation project).

**ledger** — The artefact ChronoSCRIBE produces: the authoritative, time-ordered, hash-chained record. The word "ledger" is reserved for ChronoSCRIBE throughout the stack.

**Scribe** — Retired term. Formerly a component that left the stack with AXIOM; never reused.

---

## Stage 5 — Act

**HAL** — Human Accountability Layer. The spine stage in which humans hold λ scores and occupy validator roles. Named in reference to HAL 9000; unlike the fictional HAL, this system's authority is earned through trust (λ) and can be revoked by decay. The name is homage, not aspiration.

**seal** — The signed validation artefact a HAL validator produces. Records the authorisation decision and the authoriser's identity. Appended to the ledger.

**tier** — Common noun, no caps. Five levels of authorisation within HAL, mapped to λ thresholds; written Tier 1 through Tier 5. Tier 1 is entry, Tier 5 is root council. Tiers are defined by consequence class: the stack provides the ladder, consumers define what each rung means. Full enumeration in `hal.md`.

**Fact Validator** — HAL role: verifies input data. One of two core roles.

**Consequence Authoriser** — HAL role: seals actions based on λ threshold. One of two core roles. These two are the complete set for the current specification; future extensions may add roles.

---

## Retired and Out of Scope

**AXIOM** — Retired from the stack as a core component. Remains a standalone tool in its own repository. No longer part of the Forge Stack spine. See `AXIOM.md` for historical context and standalone usage.

**Mimir** — Removed from the spine. SCP's context engine replaced its role.

**ANCHOR, ALETHEIA, LEGION, FORGEMIND** — Modules used to build the stack's individual modules; not part of the stack itself. Out of scope for `forge_stack`.

---

## Conventions

**British English** — Throughout, including code identifiers. -ise, not -ize (Oxford spelling not adopted): authorise, authorisation, behaviour, artefact. No exceptions.

**Capitalisation must be earned** — All-caps names are acronyms with a stated expansion (SCP, HAL, SCRIBE, lens names). Ordinary words are lowercase (sc, cube, ledger, seal, tier, lens).

**Immutability** — Documents are never edited in place. A revision is a new capsule identity (scp_id `-vN` bump) inheriting from its predecessor; every document hash lands in the ledger.
