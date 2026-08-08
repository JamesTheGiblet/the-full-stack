# DataCube

**Stage 2 of the Forge Stack spine: Classify.** Terminology inherited from `docs/glossary.md` via `forge-stack/governance-v1`.

DataCube is the classification system. Its artefact is the **cube** — an epistemic knowledge unit classified through six lenses. DataCube classifies what came in; it makes no trust claims (that is the Leighton Weight Engine's job) and keeps no authoritative history (that is ChronoSCRIBE's).

## The Six Lenses

The Six Lenses are DataCube's classification mechanism — not the stage name. A lens is one of six bins material is sorted into. Lenses are bins, not scores.

| Lens | Holds |
|---|---|
| FACT | Verifiable, objective data — including supporting evidence |
| COUNTER | Counterevidence: material contradicting a proposition or hypothesis |
| OPINION | Subjective perspective |
| FICTION | Speculative or unverified material |
| CONTEXT | Situational framing |
| UNKNOWN | Unclassified or undetermined material |

Every cube must fill all six lenses to be complete. An empty COUNTER bin is itself a signal: disconfirming evidence has not been sought.

## Integrity Grades

A cube's completeness across its lenses is graded:

| Grade | Completeness |
|---|---|
| CRYSTALLINE | 90%+ |
| COHERENT | 70–89% |
| FORMING | 40–69% |
| SPARSE | <40% |

## Namespaces

Cube namespaces are internal key spaces — where values live inside a cube: `event.*`, `state.*`, `domain.*`, `behaviour.*`.

Namespaces are a taxonomy independent of lens names. The overlap between `state.*` and consumer-side "current state" is incidental and crosses component boundaries. In formal docs, always specify which taxonomy is meant.

## The Store

DataCube's record of classifications and decisions is the **store**: append-only JSONL. It is never called a ledger — that word is reserved for ChronoSCRIBE. The store records what DataCube decided; the ledger proves when.

## Decay

Cubes age under Forge Theory: N(t) = N₀ × e^(−kt), with k calibrated per-domain (see `leighton-weight.md`). Classification confidence is not permanent; a CRYSTALLINE cube left untended degrades.

---

*Governed by `forge-stack/governance-v1` · Licence: MSL-1.0*
