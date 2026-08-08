# DataCube - Implementation Definition

How to build the Classify stage. This defines behaviour, structures and
boundaries; it does not specify code. Read alongside `datacube.md`, which
defines what DataCube *is*.

---

## 1. What DataCube does, and what it must not do

DataCube sits between Declare and Trust-score. It answers one question:

> **What is known about this subject, and how is that knowledge distributed
> across the six lenses?**

It is bookkeeping, not judgement. Three hard boundaries follow, and every one
of them will be tempting to cross during implementation:

- **DataCube does not compute lambda.** It produces the input the Leighton Weight
Engine scores. A cube that reports its own trust score has absorbed the next
stage.
- **DataCube does not infer.** It records classifications that were made; it
does not decide what a claim means or which lens it belongs in. No model in
the classification path.
- **DataCube does not adjudicate truth.** A claim in FACT is not true - it is
a claim that was recorded as supporting evidence by an identified party.

The stage is deterministic. Given the same store contents and the same
parameters, it must produce byte-identical cubes.

---

## 2. The artefact: cube

**System / artefact symmetry:** DataCube produces the *cube*, lowercase,
parallel to `sc` and `ledger`.

**Proposed extension:** `.cube.json`, parallel to `.sc.json`. Needs ratifying
before the first cube is written, since it will be pinned by filename in any
tooling that falls back to names.

A cube is **not a hand-edited file**. It is a *projection* - a materialised
view computed from the store at a given offset. This is the load-bearing
architectural decision in the whole design, and section 5 explains why.

---

## 3. The six lenses, defined precisely

Lenses are **bins, not scores**. An entry lands in exactly one lens. Nothing
about which lens an entry occupies implies how much it is worth.

**FACT** - recorded supporting evidence for the subject. Assertions offered as
holding, with a source.

**COUNTER** - counterevidence *only*. Evidence that disconfirms, contradicts or
undercuts. Supporting evidence never lands here.

An empty COUNTER bin does not mean nothing contradicts the subject. It means
**disconfirmation was not sought**. That distinction is the single most
valuable signal in DataCube and must survive implementation intact: a cube with
forty FACT entries and zero COUNTER entries is not strong, it is unexamined.

**OPINION** - positions held by identified parties, recorded as positions.
Attribution is mandatory here in a way it is not elsewhere; an unattributed
opinion is not a classifiable entry.

**FICTION** - content deliberately held as not-true: narrative, hypothetical,
counterfactual, worked example. This lens is what lets a fiction consumer keep
canon in the same cube as facts about the canon without contaminating FACT.

**CONTEXT** - surrounding conditions that bear on interpretation. Circumstances
under which the other lenses' contents hold or fail to hold.

Note the collision already handled at terminology level: the CONTEXT *lens* is
unrelated to the store's `domain.*` namespace, which was renamed precisely to
keep these apart. Implementation must not reintroduce the overlap by using
"context" as a namespace, field name or variable.

**UNKNOWN** - recorded known-unknowns. Explicit statements of what has not been
established.

UNKNOWN is the lens most likely to be implemented wrongly. It is **not** "the
bin that is empty because we have no data". It is a bin you *fill* by writing
down the questions you know are open. If UNKNOWN is treated as absence, it can
never be populated, no cube can ever be complete, and the completeness rule
becomes unreachable.

---

## 4. The store

DataCube has a **store**, never a ledger. That word belongs to ChronoSCRIBE.

**Append-only JSONL.** Records are written, never modified, never deleted. A
retraction is a new record that supersedes an earlier one; the earlier record
stays.

**Four namespaces**, independent of the lens names:

- `event.*` - something happened
- `state.*` - something is the case at a point in time
- `domain.*` - subject-matter knowledge
- `behaviour.*` - how something acts

Namespace and lens are orthogonal axes. A `domain.*` record can be FACT,
COUNTER, FICTION or any other lens. Do not collapse them.

**Minimum record fields:**

Field
Purpose

`record_id`
Stable identity for this record

`subject`
What the record is about - usually an `scp_id`

`namespace`
One of the four above

`lens`
One of the six

`content`
The claim itself

`source`
Where it came from

`assigned_by`
Identity that placed it in this lens

`created`
ISO 8601 UTC

`supersedes`
Optional `record_id` this replaces

`assigned_by` matters more than it looks. A lens assignment made by a person
carries different weight from one made by a script, and the Trust-score stage
cannot distinguish them if the store does not record which. This is also the
natural attachment point for HAL's Fact Validator role: a validated FACT
assignment is one where an identified validator with sufficient lambda stands behind
the placement.

---

## 5. Cube as projection

A cube is computed, not authored:

```
store records (subject, offset) -> projection -> cube
```

Why this matters:

- **New evidence never mutates an artefact.** Adding a FACT record appends to
the store. The old cube remains exactly what it was; a *new* cube is
projected. This is the same discipline as `sc` versioning and the ledger, and
it means the Classify stage does not need capsule re-mints every time
something is learned.
- **Cubes are reproducible.** A cube pinned at store offset N can be
regenerated byte-for-byte from the same store prefix. Anyone can check the
projection was honest.
- **The store is the truth; the cube is a photograph.** Disagreement about a
cube is resolved by recomputing it, not by arguing about the file.

Every cube therefore carries the store offset (or store head hash) it was
projected from. A cube without that reference is unverifiable and should be
rejected.

---

## 6. Integrity

Grades: **CRYSTALLINE** 90%+, **COHERENT** 70-89%, **FORMING** 40-69%,
**SPARSE** below 40%.

**This is the least-specified part of the existing design and needs a decision
before implementation.** The grades give bands but nothing states what the
percentage measures.

The naive reading - proportion of lenses that are non-empty - produces only
seven possible values (0, 17, 33, 50, 67, 83, 100%) and lands awkwardly:
4 of 6 lenses filled is 67%, FORMING; 5 of 6 is 83%, COHERENT. Workable, but it
means a cube with one token entry per lens grades CRYSTALLINE, which is clearly
wrong.

**Recommended: integrity is lens coverage weighted by evidential depth,
capped per lens.** Each lens contributes up to 1/6 of the total. A lens's
contribution rises with the number of distinct, non-superseded, decayed-weighted
entries in it, saturating at some small count - three or four - so that a lens
is "covered" once it has been genuinely addressed and not before, and stuffing
it further buys nothing.

That gives three properties worth having:

- One entry per lens does not reach CRYSTALLINE.
- Volume in FACT cannot compensate for an empty COUNTER - the cap makes lenses
non-substitutable, which is the whole point of the six-lens structure.
- The measure is continuous rather than seven-valued, so grade transitions mean
something.

The saturation count is a parameter to ratify, not to guess at implementation
time. It belongs in the governance capsule, not in a constant in the code.

**Completeness and integrity are different things.** A cube is *complete* when
all six lenses are non-empty. It is *CRYSTALLINE* when it is well covered.
Complete is a boolean; integrity is a grade. Keep them as separate reported
fields.

---

## 7. Decay

DataCube uses the Forge Theory formula, unchanged:

```
N(t) = N0 * e^(-kt)
```

An entry's contribution to integrity decays from its `created` timestamp. The
consequence is deliberate and should be stated in the doc rather than
discovered: **a cube that is not maintained degrades.** CRYSTALLINE erodes to
COHERENT and onwards, without anyone editing anything.

That mirrors HAL, where lambda decay eroding a tier is declared a feature -
"authority remains earned". Here the equivalent line is that *knowledge remains
current or it stops counting as current*.

`k` is per-domain and calibrated separately. The git-repo calibration of
0.1009/day does not transfer, and a DataCube deployment must establish its own.
The decay rate for a fast-moving technical subject is not the decay rate for a
settled historical one, and forcing one constant across both is a modelling
error, not a simplification.

lambda is never used for the decay constant. `k` is `k`.

---

## 8. Identity, versioning, signing

- Cubes carry a `cube_id` following the same `-vN` suffix convention as
`scp_id`. A recomputed cube at a later store offset is a **new identity**,
not a revision of the old one.
- Cubes are signed with the same Ed25519 identity and the same canonicalisation
as everything else: `json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=True)`, signed over raw UTF-8 canonical bytes, no pre-hash,
signature computed excluding the `signature` object, `key_id` present and
resolvable.
- The store itself is signed per-record or per-batch. Decide which before the
first write; per-record is simpler to reason about and more expensive.
- Cube materialisations are pinned to the ledger as `event.cube.pinned`,
recording both the cube's sha256 and the store offset it was projected from.

---

## 9. Integration points

**From SCP.** A cube's `subject` is normally an `scp_id`. The `sc` declares
intent; the cube records what is known about the thing declared. One `sc` may
have many cubes over time - that is the expected pattern, not a smell.

**To the Leighton Weight Engine.** The cube is the engine's input. The engine
reads lens distribution, entry counts, ages and `assigned_by` provenance, and
produces lambda. Nothing flows back into the cube.

**To ChronoSCRIBE.** Cube pins and store checkpoints are ledger events. This is
what makes a classification claim auditable after the fact.

**To HAL.** Fact Validator is the role that stands behind a lens assignment.
A seal over a cube materialisation is the mechanism by which a human takes
responsibility for a classification - which is the point at which the Classify
stage stops being bookkeeping and starts carrying accountability.

---

## 10. Build order

Each step ends in something verifiable. Do not proceed past a step that cannot
be demonstrated.

1. **Store writer.** Append records, validate the field set, reject unknown
namespaces and lenses. Demonstrate: a store with records in all four
namespaces and all six lenses.
2. **Store verifier.** Read back, check signatures, check `supersedes` chains
resolve. Demonstrate: a tampered record is detected.
3. **Projector.** Store + subject + offset -> cube, with completeness computed.
Demonstrate: same inputs produce byte-identical output twice.
4. **Integrity calculator.** Add weighting, saturation and decay. Demonstrate:
a cube's grade drops when the clock advances with no new entries.
5. **Signing and pinning.** Sign the cube, pin it to the ledger with its store
offset. Demonstrate: a pinned cube regenerates identically from the store
prefix.
6. **Worked example.** One real subject, carried end to end, referenced
line-by-line from `datacube.md` the way the spec references its examples.

Step 6 is the one that proves the stage exists. Steps 1-5 without it are
scaffolding.

---

## 11. Open decisions to ratify first

None of these should be settled by whatever the implementation happens to do.

1. **Cube file extension** - `.cube.json` proposed.
2. **Integrity denominator** - the weighting scheme in section 6, and the saturation
count per lens.
3. **Store granularity** - one store per subject, per consumer, or one global
store partitioned by subject.
4. **Store signing granularity** - per record or per batch.
5. **`k` calibration method** - how a deployment establishes its own decay
constant, and where that value is declared.
6. **Whether cubes are manifest members** - or whether, like consumer capsules,
they live outside the stack manifest and are pinned only.
7. **Scope** - whether the stack ships a reference DataCube at all, or defines
the protocol and lets consumers implement. The same question AXIOM lost.

---

*Classify stage. DataCube produces cubes. Cubes are projections over an
append-only store, signed, pinned, and decaying.*
