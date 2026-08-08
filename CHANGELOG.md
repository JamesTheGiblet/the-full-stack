# Changelog

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
