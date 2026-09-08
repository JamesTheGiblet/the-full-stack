# ChronoSCRIBE in CobbleWright

ChronoSCRIBE is CobbleWright's append-only audit/provenance layer.

It records high-value runtime events (commands, advice generation, memory persistence, learning profile saves) into a signed hash chain so integrity can be verified later.

## What It Guarantees

- Authenticity: each record is signed with Ed25519.
- Integrity: each record links to the previous record via `prev_hash`.
- Tamper detection: changing one record breaks the chain from that point onward.

ChronoSCRIBE does not provide encryption/confidentiality by itself.

## Storage

ChronoSCRIBE stores data in:

- `cobblewright/data/chronoscribe/ledger.ndjson` (append-only records)
- `cobblewright/data/chronoscribe/state.json` (head pointer and sequence)
- `cobblewright/data/chronoscribe/ed25519_keypair.json` (local signing keypair, if not supplied via config)

## Configuration

Add to `config.json`:

```json
{
  "CHRONOSCRIBE_ENABLED": true,
  "CHRONOSCRIBE_KEY_ID": "cobblewright-ed25519-v2",
  "CHRONOSCRIBE_MAX_PAYLOAD_CHARS": 5000
}
```

Optional external keys:

- `CHRONOSCRIBE_PRIVATE_KEY_PEM`
- `CHRONOSCRIBE_PUBLIC_KEY_PEM`

If those are set, ChronoSCRIBE uses them instead of generating/storing a local keypair.

## Key rotation — `v1` is compromised

`cobblewright-ed25519-v1` was committed to a **public** repository inside
`ed25519_keypair.json`, from the first commit until it was untracked. Treat it
as permanently compromised: anyone who fetched the repository in that window
holds the private key and can forge entries that verify under `v1`.

The keys have been rotated to `cobblewright-ed25519-v2` and both ledgers
re-signed. Event hashes and the `prev_hash` chain were left byte-identical, so
only the `signature` field changed — the history itself was not rewritten.

Two consequences worth being clear about:

- **Entries created before the rotation are not trustworthy**, even though they
  now verify under `v2`. They are re-attestations of records that were
  forgeable while `v1` was public. Verification proves they have not been
  altered *since* the rotation; it does not prove they were genuine before it.
- **A running bot still holding the `v1` keypair will produce entries that fail
  verification.** Any deployment must pick up the new keypair file (or have
  `CHRONOSCRIBE_PRIVATE_KEY_PEM` updated) before it next appends.

`ed25519_keypair.json` is now gitignored, so the private key is no longer
committed. The public half is published alongside each ledger as
`ed25519_public.pem` so the chain stays verifiable without exposing the key.

## Chat Commands

- `audit` or `verify`: verify chain integrity and signature validity.
- `audit path`: show the local ledger file path.

## Boot Attestation

On bot login, ChronoSCRIBE writes a `session_genesis` anchor record for session provenance.
