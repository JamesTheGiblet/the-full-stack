# Changelog

2026-08-08 10:12

## The Good 0.2
Confidence rating: 1.84/2.00

- Tightened `ledger.py append-pins` document scope from broad `docs/*.md` sweep to capsule-referenced documents, reducing accidental pin drift.
- Added `sc/forge-stack-manifest-v3.sc.json` with explicit scope language and `supersedes: forge-stack/manifest-v2` for machine-traceable lineage.
- Implemented and validated append preview safety (`--dry-run`) and kept live append immutable; only genuinely new pins were appended.
- End-to-end checks remain green after the update: `sign.py --verify` passed and `ledger.py verify` passed.

## The Bad 0.2
Risk rating: 0.88/2.00

- The refined rule is now "capsule-referenced documents" rather than "docs-only", which still allows non-markdown artefacts to be pinned when referenced (for example the lifeforge HTML artefact).
- Manifest policy remains strict and explicit: author-level capsules are still intentionally out of manifest membership, which can surprise readers unless they read the intent text.

## The Ugly 0.2
Severity rating: 0.54/2.00

- Resolved drift from prior pass: changelog rating labels no longer use Leighton Weight terminology, preventing collision with the ratified λ trust-score model.
- Resolved operational ambiguity: append scope behavior is now deterministic and testable with dry-run before live writes.

---

2026-08-08 09:58

## The Good 0.1
Confidence rating: 1.78/2.00

- Built a proper append path for ChronoSCRIBE via `ledger.py` (`verify`, `append`, `append-pins`) with verify-on-write and append-only chaining.
- Embedded resolvable identity across signing surfaces: capsule `signature.key_id` uses `did:key:z6MktudRY5LBZJeE13BiF4BeisAwWs7gvg6srh2GwLAMKDwJ`; ledger append signatures now also include `key_id`.
- Minted and integrated AXIOM scope updates: added `sc/axiom-v1.sc.json`, added `sc/forge-stack-manifest-v2.sc.json`, froze hashes, signed, appended ledger pins, and verified chain integrity.
- Confirmed end-to-end health after changes: `sign.py --verify` passed and `ledger.py verify` passed.

## The Bad 0.1
Risk rating: 0.96/2.00

- The change set is intentionally broad (many capsule rewrites) because identity and signature metadata were normalised across the full set.
- Ledger output is noisy during `append-pins` due to idempotency checks (`SKIP duplicate` lines), which is correct but harder to scan quickly.
- Manifest policy boundaries still need explicit narrative discipline: author-level artefacts (like `james-style`) are ledgered but not manifest members by design.

## The Ugly 0.1
Severity rating: 0.71/2.00

- Resolved error: initial signature verification showed 55 failures; root cause was unsigned capsules and stale/misaligned references, fixed by signing pass and targeted capsule correction.
- Resolved error: `sc/james-style-v1.sc.json` referenced `james-style.md` at repo root; corrected to `docs/james-style.md` and regenerated sidecar signature.
- Resolved error: bulk replacement introduced UTF-8 BOM into `.sc.json` files, causing JSON parse failures; BOM bytes were stripped from all affected capsule files.
- Resolved error: no append path existed (`genesis.py` is genesis-only); addressed by creating `ledger.py` append workflow and preserving immutable history.

---
