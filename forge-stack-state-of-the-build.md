# The Forge Stack — State of the Build

*One day, one signed foundation, two proofs it works.*

---

## 1. The Foundation — Forge Stack v1

**Status: frozen, signed, witnessed.**

The five-stage spine, each stage documented and capsulised:

| Stage | Component | Artefact | Doc |
|---|---|---|---|
| Declare | SCP | sc | `scp-spec-v1.2.md` |
| Classify | DataCube | cube | `datacube.md` |
| Trust-score | Leighton Weight | λ | `leighton-weight.md` |
| Audit | ChronoSCRIBE | ledger | `chronoscribe.md` |
| Act | HAL | seal | `hal.md` |

Enforced at runtime by the **gate pattern** (`gate-pattern.md`) — ingress gates protect state, egress gates protect the world, because the world is the thing you can't undo.

Governed by `forge-stack/governance-v1`, terminology fixed by `docs/glossary.md`, the whole set pinned by `forge-stack/manifest-v1`.

**What actually happened to it today:**
- Every term fought over and ratified — SCP vs sc, λ vs k, ledger vs store, tier vs TIER — until one word meant one thing everywhere.
- §4's crypto section rewritten from a placeholder into the literal truth of the reference implementation (canonicalisation, raw-byte Ed25519 signing) — no aspirational spec, only what the code actually does.
- Eleven capsules signed with a sovereign identity minted on your own phone from your own keypair — a `did:key`, not borrowed from anyone.
- One key exposure, caught, rotated, and re-signed before anything shipped — the first real lesson in why HAL's seals and key hygiene matter, learned the cheap way.
- Nineteen genesis entries written to `ledger.jsonl`, hash-chained and signed — ChronoSCRIBE's first act on record is witnessing the constitution that defines ChronoSCRIBE.
- Your own author-level style capsule (`giblets-forge/style/james-style-v1`) drafted alongside it, seven of eight sections filled from what you actually said, one left honestly open rather than invented.

The foundation doesn't just describe the stack. It's the first thing the stack ever verified.

---

## 2. Consumer One — CobbleWright *(in progress)*

Minecraft AI companion bot. The stack's proof that the spine survives contact with a real, live, adversarial-ish environment (players, griefers, bad AI-generated blueprints).

- **Knowledge gates**, formalised into ingress (protects state) and egress (protects the world) — the CobbleWright work is where the gate pattern doc actually originated.
- **The Leighton Loop** in the wild: advice → player acts → bot checks the world before/after → learns. Trust scored against observed outcomes, not claimed ones — the whole stack's pitch, demonstrated somewhere people can literally watch the before/after.
- **Plugin trust hole** found and named honestly: raw `sharedState` and the raw mineflayer bot object both bypass every gate today. Long-term fix is a gatekeeper API; the interim is a documented trusted-context caveat, written down before the Day 3 post rather than discovered after.
- Naming cleanup against the now-frozen glossary is the one thing still blocking that post.

CobbleWright proves the spine works when the thing being governed is code and a Minecraft world.

---

## 3. Consumer Two — The Dust Margin *(Part One complete)*

A from-scratch space western, canon-engine native from its first sentence — the stack's proof that the spine works on something with no code at all: a story.

**The universe:** dusty and desperate, hope rationed like fuel. Four hard rules, λ 2.0, Tier 5 to break: no FTL, death is final, water is the scarcity, the frontier is a state, not a map.

**The mechanism:** every character's claim — hero and antagonist alike — goes into DataCube's lenses as OPINION until something independently confirms it. No exceptions for sympathetic speakers or dramatic momentum. That single rule, held for forty-one scenes, is what makes this the sharpest proof-of-concept in the whole stack:

- **It caught real contradictions before they shipped** — Rena's scene-three lie, Kael's two conflicting confessions, a five-year gap in his own timeline — each one turned into characterisation instead of an embarrassing plot hole, because the graph refused to trust a confident speaker on their word alone.
- **It survived its own hardest test.** Every lens slip that happened — six of them — occurred during the highest-drama reveals, exactly when it's easiest to just believe the story. By scene forty, at the arc's biggest confrontation, the standing rule held clean on the first draft. The discipline generalised.
- **It left honest debt on the books.** Two threads — the empty water tank, the unmeasured FTL distance, both from scene one — were promised resolution "before the arc closes." They weren't delivered. The ledger says so, in the open, rather than quietly dropping them.
- **It ended on the story's own thesis, earned rather than stated:** Rena refuses House Voss's claim not through Jax, but directly, on her own terms — "It will be my choice. Not yours. Not his. Mine." Forty scenes of everyone else's choices being made for her, resolved by the one choice nobody made for her.

Forty-one scenes. Thirteen named cubes. Zero contradictions left unlogged. One broken promise, kept honest by being named instead of hidden.

**Files:** `the-dust-margin.md` (the manuscript — clean prose, no scaffolding) and `dust-margin-canon.md` (the full graph — every cube, every lens, every open thread, ranked).

---

## What This Actually Proves

Two consumers, two completely different domains — a game bot and a piece of fiction — governed by the same five-stage spine, the same gate pattern, the same evidentiary standard. Neither is a toy demo. CobbleWright has real players and real griefing risk. The Dust Margin has a real reader who can be genuinely fooled by an unreliable narrator, the same way a DataCube reader can be fooled by an unverified claim.

The stack's actual claim was never "AI infrastructure." It was: *declare what you mean, classify what you're told, score how much to trust it, prove what happened, and act only once someone accountable has signed off.* That claim doesn't care whether the thing being governed is a git repo, a Minecraft build, or a lie a fictional smuggler tells a fictional water-hauler. It held in both places today.

---

*Forge Stack v1: signed, ledgered, live. Two consumers built on it. One documentation gap (CobbleWright naming) and one unresolved contradiction (Voss vs. Corvus) are the honest state of things — not hidden, just carried forward, the same discipline the stack was built to enforce on everything else.*
