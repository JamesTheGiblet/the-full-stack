# SCP Specification v1.2

**SCP — Semantic Capsule Protocol.** Not to be confused with Secure Copy Protocol or the SCP Foundation. The protocol for producing, validating, and consuming sc artefacts.

Terminology in this document is defined by the Forge Stack glossary (`docs/glossary.md`), inherited via the root governance capsule (`forge-stack/governance-v1`). This specification defines the protocol; the glossary defines the words.

Worked example: `docs/examples/minimal.sc.json`, referenced line-by-line in §8.

---

## 1. Overview

SCP is a declarative, agnostic protocol. An sc (Semantic Capsule) is a signed declaration of meaning — intent, parameters, and constraints — that downstream systems can validate, inherit from, and act on. An sc can declare text, define a function, automate a task, or bind an AI system via its knowledge gate. Capsules run anywhere JSON does: servers, bare-metal microcontrollers, phones.

The protocol occupies the Declare stage of the Forge Stack spine: Declare (SCP) → Classify (DataCube) → Trust-score (Leighton Weight) → Audit (ChronoSCRIBE) → Act (HAL).

## 2. The sc Artefact

File extension: `.sc.json`, no exceptions.

### 2.1 Root fields

| Field | Required | Description |
|---|---|---|
| `scp_id` | Yes | Capsule identity. Content revisions bump the `-vN` suffix, creating a new identity. There is no separate revision field. |
| `scp_version` | Yes | Protocol version, e.g. `"1.2.0"`. |
| `created` | Yes | ISO 8601 UTC timestamp. Used for merge-conflict ordering. |
| `inherits` | Conditional | Parent `scp_id`. Mandatory for project-level capsules. Omitted (not null) only by the root governance capsule. |
| `declaration` | Yes | Freeform payload — typically `intent`, `parameters`, `constraints`. |
| `licence` | Conditional | `MSL-1.0` default. Full capsules declare explicitly or cite the root; Lite scs may omit and inherit from the root. |
| `signature` | Yes | Signature block, §4. Mandatory across all capsules. |

### 2.2 The declaration block

`declaration` is freeform but conventionally contains:

- `intent` — what this capsule declares, in one string
- `parameters` — values the declaration is parameterised by
- `constraints` — rules the declaration imposes on inheritors

## 3. SCP Lite

A signed minimal subset of v1.2. (The earlier unsigned sidecar dialect is deprecated; signature is mandatory across all capsules.)

A Lite sc contains only: `scp_id`, `scp_version`, `created`, `declaration` (must contain an `intent` string; optional flat `parameters`; no `constraints`, no nesting), and `signature`. It omits `inherits` and `licence`; licence coverage arrives via the governance default.

The protocol has modes; the artefact is always just an sc.

## 4. Signature

Signature block shape:

```json
"signature": {
  "key_id": "<DID or KERI AID>",
  "algorithm": "Ed25519",
  "value": "<base64 signature>"
}
```

`key_id` lives inside the signature block, not at capsule root.

### 4.1 Canonicalisation

The signature is computed over the canonicalised JSON of the capsule **excluding the signature object**.

Canonicalisation algorithm (reference implementation):

```python
def canonicalise(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
```

This produces deterministic, whitespace-free JSON with sorted keys and Unicode escapes for all non-ASCII characters (λ → `\u03bb`, → → `\u2192`). This is **not** RFC 8785 (JCS); it is the reference implementation's own deterministic form, and independent implementations must reproduce it exactly rather than substituting JCS.

### 4.2 Signing procedure

Ed25519 signs the UTF-8 encoded canonical bytes **directly**. No pre-hashing. Standard Ed25519, not Ed25519ph.

```python
canonical = canonicalise(capsule_without_signature)
signature = private_key.sign(canonical.encode('utf-8'))
```

Verification recomputes the same canonical form and verifies against the raw bytes:

```python
capsule_copy = capsule.copy()
sig = capsule_copy.pop('signature')
canonical = canonicalise(capsule_copy)
public_key.verify(sig['value'], canonical.encode('utf-8'))
```

The public key is resolved from `key_id`.

## 5. Inheritance

Every capsule except the root names its parent in `inherits`. Inheritance carries the governance constraints downward: terminology authority, immutability, licence default, conventions, and scope. A child may extend its parent's declaration; it may not override root governance terms.

## 6. Immutability and Versioning

Capsules and their paired documents are never edited in place. A revision is a new capsule identity — the `-vN` suffix bump — inheriting from its predecessor. Every capsule and document hash lands in the ledger (ChronoSCRIBE). The old identity remains valid, verifiable history.

The glossary is pinned by hash in the governance capsule; a glossary revision therefore requires a new governance capsule version (the cascade rule). Authority, not a pointer.

## 7. Bindings

A binding sc governs trust, permissions, or integration between systems — including binding an LLM or AI system via its knowledge gate, the enforcement point where a capsule's declared constraints are checked against a system's inputs and outputs. The gate pattern itself is specified in `docs/gate-pattern.md`.

## 8. Worked Example

See `docs/examples/minimal.sc.json`. Line-by-line commentary:

> **TODO after §4 is verified:** example must carry a real signature produced by the reference implementation, so the example doubles as a verification test vector.

---

*Protocol: SCP v1.2.0 · Licence: MSL-1.0 · Governed by `forge-stack/governance-v1`*
