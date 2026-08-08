# AXIOM

**Status: not part of the Forge Stack.** AXIOM is a standalone tool maintained
in its own repository. It is documented here because the glossary references it
and because it was, for a period, a candidate spine component. Nothing in this
document defines stack behaviour.

---

## What AXIOM is

AXIOM is a proxy that sits in front of a language model. It is not a pipeline
you build within, and it is not a framework a project adopts. Requests pass
through it on their way to whichever model is behind it; responses pass back
through it on the way out. The model is unmodified and, in principle,
interchangeable.

Its purpose is accountability: making it possible to say, after the fact, what a
model was given, what it was permitted to draw on, and how the resulting output
relates to that input.

## Components

**AXIOM Ingest** — deterministic intake. Input is normalised into a fixed form
before it reaches the model, so that the same input produces the same
intermediate representation every time. Determinism here is what makes anything
downstream reproducible.

**AXIOM Justify** — the scoring engine. Justify was an implementation of the
Leighton Weight Engine, not a competing mechanism. The distinction matters and
is recorded in the glossary: the name *Leighton Weight Engine* stays with the
function, never with an implementation of it. AXIOM leaving the stack did not
take the trust-scoring stage with it.

**AXIOM Present** — the presentation layer, using constrained decoding to hold
output within a bounded space derived from the ingested material.

## On the claim that was withdrawn

Earlier descriptions of AXIOM Present stated that it was *architecturally
incapable of hallucination*. That claim is withdrawn and should not be repeated.

Constrained decoding narrows what a model may emit. It does not make the
resulting output true, and it does not make a false statement unreachable — it
makes a class of unsupported output harder to reach, which is a different and
smaller claim. Describing that as architectural incapability overstates it in a
way that would not survive adversarial testing.

The accurate framing is **traceability**: AXIOM's value is that an output can be
traced back to what was ingested and what was scored, so a claim can be checked
against its inputs rather than trusted on assertion. That is a property of the
audit trail, not a guarantee about the content.

The distinction is recorded here deliberately. A retired component whose
strongest claim was rescinded should say so where it can be read, rather than
leaving the original wording alive in older material.

## Why AXIOM is not in the stack

AXIOM was scoped out as a tool rather than a spine stage. The Act stage remains
in the spine; **HAL** — the Human Accountability Layer — is its core component.

This was a scope decision, not a supersession. AXIOM was not replaced by HAL and
did not fail; the two answer different questions. HAL asks *which human
authorised this consequence, and on what standing*. AXIOM asks *what was this
output derived from*. A build may reasonably use both, neither, or one.

Two further components left the stack alongside AXIOM:

- **SCRIBE** — an audit proxy daemon. The bare name is retired stack-side and is
  never reused; ChronoSCRIBE is unrelated and keeps its own expansion.
- **LENS** — a live capsule store presenter.

## Relationship to the stack today

None enforced. AXIOM does not inherit the governance capsule, is not pinned in
the manifest, and is not covered by the ledger.

A project may put AXIOM in front of a model and separately declare an `sc`,
score with the Leighton Weight Engine, or record to a ledger. Those remain
independent decisions. Nothing about using AXIOM makes a build stack-compliant,
and nothing about being stack-compliant requires AXIOM.

## Where it lives

The public repository presents AXIOM as an architecture proof of concept under
the heading *Epistemic Infrastructure for AI Accountability*. The full technical
brief is held separately under NDA and is not part of the public material.

---

*Retired from the Forge Stack spine. Retained as a standalone tool. Out of
scope, not superseded.*
