<div align="center">

# ⚒️ THE FORGE STACK

### A sovereign AI stack, forged not framed.

*Declare intent. Classify what's known. Score what it's worth.*
*Record it immutably. Gate action behind a human.*

[![Licence: MSL-1.0](https://img.shields.io/badge/licence-MSL--1.0-orange)](#governance)
[![Spine](https://img.shields.io/badge/spine-5%2F5%20implemented-brightgreen)](#status)
[![Signing](https://img.shields.io/badge/signing-Ed25519-blue)](#cryptography)
[![Built](https://img.shields.io/badge/built-AI--assisted-purple)](#status)

**[Status](#status)** · **[The Spine](#the-spine)** · **[Cryptography](#cryptography)** · **[Governance](#governance)** · **[Verify It Yourself](#verifying-this-repository)** · **[Known Limitations](#known-limitations)**

---

</div>

> *"I wanted it. So I forged it. Now forge yours."*

Built by **Giblets Forge**. Licensed under the **Meaning Sovereignty Licence
v1.0 (MSL-1.0)**.

This is an AI-assisted build — architecture, decisions, and verification
are mine; implementation velocity comes from working alongside AI. See
[`CHANGELOG.md`](./CHANGELOG.md) for the full build history, in order,
oldest first.

---

## 🔥 Status

<div align="center">

### All five spine stages are implemented, signed, ledgered, and verified from a clean clone.

**Not just designed. Built.**

</div>

That happened for the first time on **09/08/2026**.

| Stage | System | Artefact | Status |
|:---:|:---|:---:|:---:|
| **①** Declare | SCP | `sc` | ✅ Implemented |
| **②** Classify | DataCube | cube | ✅ Implemented |
| **③** Trust-score | Leighton Weight Engine | λ | ✅ Implemented |
| **④** Audit | ChronoSCRIBE | ledger | ✅ Implemented |
| **⑤** Act | HAL | seal | ✅ Implemented *(single-operator)* |

Some pieces are provisional rather than finished: DataCube's integrity
denominator is a configurable model pending governance ratification,
Leighton's `k` values in the worked examples are demonstration constants
rather than per-domain calibrations, and HAL's `separation` field is honest
about the fact that one signing key currently authorises everything. None
of that is hidden — see **[Known limitations](#known-limitations)** below.

---

## ⚙️ The Spine

Every system produces exactly **one** named artefact. The symmetry is
stack-wide and enforced, not decorative — the filename tells you which
stage produced a thing and which document governs it.

### ① Declare — SCP

SCP (Semantic Capsule Protocol) declares intent. It produces an `sc` —
always lowercase, always `.sc.json`, no exceptions. "Capsule" is a
prose-only synonym; it never appears in a schema, filename, or identifier.

An `sc` v1.2 root: `scp_id`, `scp_version`, `created`, `inherits`,
`declaration`, `licence`, `signature`. A content revision bumps the `-vN`
suffix on `scp_id` — a revised `sc` is a **new identity**, not a mutation.
**SCP Lite** is a signed minimal subset for lightweight bindings.

### ② Classify — DataCube

DataCube scores knowledge across six lenses — **FACT · COUNTER · OPINION ·
FICTION · CONTEXT · UNKNOWN** — and produces a `cube`. Lenses are bins, not
scores: an empty COUNTER means disconfirmation wasn't sought, not that none
exists. DataCube keeps a *store*; "ledger" is reserved for ChronoSCRIBE.

### ③ Trust-score — Leighton Weight Engine

Forge Theory owns the decay formula. λ (the **Leighton Weight**) is
computed on the fly from an observation stream — never stored — using a
neutral-attractor curve:

```
λ(t) = 1.00 + (λ₀ − 1.00) × e^(−kt)
```

Decay pulls **toward neutral** (1.00), not toward zero, so an entity that
goes quiet drifts toward *unknown* rather than *distrusted*. `k` is the
decay constant and is always calibrated per domain — it is never called λ,
and the tooling refuses to run without an explicit value.

The **Leighton Loop** — score → observe outcomes → update — closes via
**Attestations**: signed ledger events that record a judgement on a past
event, hash-linked to it. Disputes are resolved using the disputing
attester's λ as it stood *before* the attestation, which stops a winning
dispute from retroactively inflating the standing that won it.

### ④ Audit — ChronoSCRIBE

**S**igned **C**hronological **R**ecord of **I**mmutable **B**ehavioural
**E**vents. Produces the *ledger*: hash-chained, append-only, one entry per
event, each carrying the hash of its predecessor.

The root ledger is the constitution's record only. Every consumer gets its
own ledger, **cryptographically anchored** to the root chain's head at
creation — so a consumer's history is provably rooted in a specific state
of the constitution, not just declared to be.

### ⑤ Act — HAL

The Human Accountability Layer. Humans hold a λ and occupy validator roles
— **Fact Validator**, **Consequence Authoriser** — across a five-tier
ladder gated by λ thresholds (quarantine below 0.60). Each validation
produces a signed *seal*, appended to the ledger — **including refusals.**

Named in homage to HAL 9000. Homage, not aspiration.

---

## 🔐 Cryptography

Every artefact is signed **Ed25519** under a single `did:key` identity,
resolvable and embedded in every capsule's `signature.key_id`.

Canonicalisation is exactly:

```python
json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
```

This is **not** RFC 8785 / JCS. Implementations must reproduce this
byte-for-byte or signatures won't verify. Signing is over the raw UTF-8
canonical bytes, no pre-hash, excluding the `signature` object itself.

Non-JSON artefacts (docs, HTML) get a capsule hash-pin **and** a detached
signature over the raw file bytes (`.sig` sidecar) — two independent
verification paths per file, no exceptions.

---

## 🏛️ Governance
`sc/forge-stack-governance-v6.sc.json` is the root capsule. Its `inherits`
lineage is **historical**, not a live pointer: a capsule's `inherits`
records which constitution was in force *at signing*. Superseding
governance never invalidates an old capsule's declaration — supersession
is carried solely by the `supersedes` field and manifest membership, never
by renaming files.

`sc/forge-stack-manifest-v9.sc.json` pins the current documentation set.

British English throughout, including code identifiers (`-ise` not
`-ize`): authorise, artefact.

### Scope

**The Forge Stack defines the stack, not the builds.**

Consumers — CobbleWright, Dust Margin, LifeForge, The Last Full Stop,
`giblets-forge` (author-tier) — are separate entities built *using* the
stack. They inherit the constitution through their own capsules, get their
own root-anchored ledger, and live outside this glossary.

Explicitly **out of scope**: AXIOM, ANCHOR, ALETHEIA, LEGION, FORGEMIND,
Mimir — tools built with the stack, not parts of it. AXIOM retains a
gravestone entry (`docs/AXIOM.md`) for historical context; a claim it once
made about being architecturally incapable of hallucination has been
formally withdrawn in favour of a traceability framing.

---

## 📁 Repository Layout

```
the-full-stack/
├── docs/                 v1 documentation set — sha256-pinned
├── sc/                   root capsules (governance, manifest, one per doc)
├── consumer/             consumer capsules + their own root-anchored ledgers
├── datacube.py           Classify stage implementation
├── leighton_weight.py    Trust-score stage implementation
├── hal.py                Act stage implementation
├── freeze.py             fills document_sha256 placeholders before signing
├── sign.py               signs capsules + referenced non-JSON artefacts
├── ledger.py             verify / append / append-pins for ChronoSCRIBE
├── genesis.py            mints a ledger's first immutable batch (root only)
├── ledger.jsonl          the root ledger
└── CHANGELOG.md          full build history, oldest first
```

---

## ✅ Verifying This Repository

**Don't trust a local pass — verify from a genuinely fresh clone.**

Signature verification is immune to line-ending damage for capsules
(canonicalised JSON) but *not* for artefact sidecars, which sign raw
bytes.

```bash
git clone https://github.com/JamesTheGiblet/the-full-stack.git
cd the-full-stack
python sign.py --verify
python ledger.py verify
python ledger.py verify --scope <consumer-name>
```

All should report every signature and chain intact.

---

## ⚠️ Known Limitations

- **Single operator.** Right now one `did:key` signs everything, including
  an authoriser's own λ score file. HAL's `separation` field is honest
  about this — `none` means the sealing key and the scored key are the
  same — rather than pretending the tier check proves independence it
  can't yet prove.
- **DataCube's integrity denominator** is a configurable saturation model,
  not yet a governance-ratified formula.
- **Leighton's `k`** in the worked examples is a demonstration constant.
  Per-domain calibration is required before production use, and the
  tooling refuses to run without an explicit value — but nothing yet
  validates that the value supplied is actually calibrated.
- **Observation ingestion is v1-minimal** — explicit records only, no
  auto-extraction of attestations from a ledger yet.
- **Outcome-to-λ-delta mapping is hardcoded**, not yet ratified policy.

None of the above blocks using the stack. All of it is recorded here so
nobody mistakes "implemented" for "finished."

<div align="center">

---

### ⚒️ *"I wanted it. So I forged it. Now forge yours."*

</div>