# Nova-bot Consumer Changelog

*This changelog will document the build history of the Nova-bot project. Entries should run in the order they happened, oldest first.*

---

## The Good 0.1
Confidence rating: 9.5/10

- **Project bootstrapped.** Established the `Nova-bot` consumer project with its foundational documents, including a detailed `README.md` and `ROADMAP.md`.
- **Hardware formally declared.** Created and signed the `hardware-manifest-v1.sc.json` capsule, providing a verifiable "birth certificate" for the robot.
- **Audit trail initiated.** Created the consumer-specific `ledger.jsonl`, correctly anchored to the root ledger's head to establish a provable chain of custody.
- **Initial milestones witnessed.** The ledger now contains verifiable, signed entries for the hardware manifest pinning and the official start of firmware development.
- **Integrity confirmed.** The final state of the `Nova-bot` ledger passes all `ledger.py verify --scope nova-bot` checks.

## The Bad 0.1
Risk rating: 3.0/10

- **Tooling fragility exposed.** The very first write to the new consumer ledger introduced a data corruption bug, suggesting the append logic in `ledger.py` may be less robust when creating a new file from scratch versus appending to an existing one.

## The Ugly 0.1
Severity rating: 2.0/10

- **Verification failed on first entry.** A bug in `ledger.py` caused the signature value in the first ledger entry to be duplicated, immediately breaking the chain's integrity. This required manual file editing to repair the corrupted JSON before verification could pass. It serves as a stark reminder to verify the output of the core tooling itself.

---

## The Good 0.2
Confidence rating: 10/10

- **Project naming and structure corrected.** Renamed the consumer directory and all internal identifiers from `Nova_bot` (or `nova_bot`) to `nova-bot`, enforcing the stack's hyphenation convention.
- **Capsules are now fully schema-compliant.** Updated `hardware-manifest-v1.sc.json` and `pin-configuration-v1.sc.json` to include the required `scp_version`, `inherits`, and `licence` fields, making them valid v1.2 capsules.
- **Project integrity restored.** After correcting all file paths and capsule content, a full `python sign.py` pass now completes successfully without schema validation errors.

## The Bad 0.2
Risk rating: 3.0/10

- **Ledger reset required.** Because the immutable `scp_id` of the core capsules changed, the original (and corrupted) `ledger.jsonl` had to be deleted. The project's auditable history is being reset from a clean state.

## The Ugly 0.2
Severity rating: 4.0/10

- **A subtle regex bite.** The root cause of the signing failure was an underscore in the `scp_id`, which was disallowed by the schema's regular expression. The generic error message made this difficult to diagnose, highlighting a need for more specific validation feedback in the tooling. This was a critical fix to make before the project's identity was immutably recorded.

---

## The Good 0.3
Confidence rating: 10/10

- **Clean ledger created.** Successfully ran `ledger.py append-pins --scope nova-bot` to create a new, clean ledger after the project's naming conventions were corrected.
- **Capsules witnessed correctly.** The new ledger is properly anchored to the root chain and contains the initial pin entries for the schema-compliant `hardware-manifest-v1` and `pin-configuration-v1` capsules.

## The Bad 0.3
Risk rating: 1.0/10

- **No bad items.** This step successfully re-established the project's auditable history from a clean, verifiable state.

---

## The Good 0.4
Confidence rating: 10/10

- **Ledger integrity confirmed.** A full `python ledger.py verify --scope nova-bot` pass completed successfully, confirming the new ledger's hash chain and all signatures are valid.
- **Project is now in a clean state.** This successful verification marks the end of the project's structural and governance cleanup. The `nova-bot` consumer is now correctly anchored and has a verifiable audit trail from its genesis.

## The Bad 0.4
Risk rating: 1.0/10

- **No bad items.** This pass was a clean verification of a correct state.

## The Ugly 0.4
Severity rating: 1.0/10

- **Finally, a clean slate.** This successful verification finally closes a long and painful loop of debugging, file migration, and tooling fixes. The project is now ready for forward progress.

---

## The Good 0.5
Confidence rating: 9.0/10

- **Initial firmware created.** Wrote the first C++ sketch for the project, `src/motor_control.cpp`, providing basic functions for mobility (forward, backward, turn, stop).
- **Configuration externalized.** In a good application of the stack's principles, the hardware pinout was immediately refactored out of the code and into a dedicated, signed semantic capsule (`pin-configuration-v1.sc.json`).

## The Bad 0.5
Risk rating: 5.0/10

- **Firmware is untested.** The `motor_control.cpp` sketch has been written but has not been compiled, flashed, or tested on the physical ESP32 hardware. Its correctness is purely theoretical at this point.

## The Ugly 0.5
Severity rating: 1.0/10

- **No ugly items.** This was a clean, forward-progress step in implementing the roadmap.