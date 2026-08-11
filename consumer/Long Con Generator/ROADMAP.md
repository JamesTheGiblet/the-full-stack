# ROADMAP

This document outlines what is not yet built and what is intentionally deferred for the Long Con Generator. It is the forward-looking complement to `CHANGELOG.md`'s backward-looking record.

When an item here is completed, it is removed from this document and a corresponding entry is made in `CHANGELOG.md`.

---

## Keystone Gate & Scoring

### Leighton Weight Calibration
*   **What is missing:** The weights and thresholds for the Leighton Weight scoring dimensions are currently demonstration constants hardcoded in the tool.
*   **Why it matters:** For the novelty and quality scores to be meaningful, the weights must be calibrated against a real dataset of concepts. Uncalibrated scores can lead to misclassifying generated concepts (e.g., flagging a genuinely novel idea as uninspired).
*   **What blocks it:** A **capability not yet buildable**. This requires a sufficiently large and diverse corpus of generated capsules to perform meaningful calibration.

### Correction Prompt Library
*   **What is missing:** A pre-built, dynamic library of correction prompts for common rejection reasons. Currently, rejection messages are generic.
*   **Why it matters:** Specific, targeted feedback would allow the upstream LLM to "learn" the schema and quality requirements more quickly, reducing the number of rejected generations over time.
*   **What blocks it:** A **decision not yet made**. The design for how to store, select, and format these prompts needs to be defined and ratified.

## ChronoScribe & Data Persistence

### Persistent Capsule Database
*   **What is missing:** The `capsule_db.json` file is an in-memory demonstration store. There is no persistent, scalable database solution.
*   **Why it matters:** The current implementation cannot handle a large number of capsules and loses its state on restart, making it unsuitable for continuous operation or for building a meaningful history of generated concepts.
*   **What blocks it:** A **decision not yet made**. The choice of database technology (e.g., stick with SQLite like ChronoScribe, move to a document DB) needs to be evaluated and decided upon.

### Semantic Embedding Caching
*   **What is missing:** A caching mechanism (e.g., Redis, or a simple file-based cache) for the sentence-transformer embeddings used for similarity checks.
*   **Why it matters:** Calculating embeddings is computationally expensive. Without caching, the `Keystone Gate`'s performance will degrade significantly as the number of capsules in the database grows, as it must re-compute or re-load embeddings on every run.
*   **What blocks it:** A **decision not yet made**. This is dependent on the choice of the persistent database solution, as that will inform the optimal caching strategy.

## Sandbox & Simulation

### Sandbox Simulation Implementation
*   **What is missing:** The sandbox, intended for agent-based modeling of generated cons, is currently a non-functional stub.
*   **Why it matters:** The ultimate validation of a generated "long con" concept is to test its logical coherence and potential effectiveness in a simulated environment. Without this, the "Approved" status is based only on structural and novelty scores, not on functional viability.
*   **What blocks it:** A **capability not yet buildable**. This is a significant engineering effort that requires a full design for agent behaviour, world modeling, and success/failure metrics.

## Governance & Process

### Formalised Outcome-to-Score Mapping
*   **What is missing:** The policy for how results from the (future) sandbox simulation map to changes in a capsule's score or status is not defined.
*   **Why it matters:** To create a true feedback loop, the outcomes of sandbox tests (success, failure, detection) must be able to influence the scoring of the capsule and its descendants. This is key to the system's ability to learn which patterns are effective.
*   **What blocks it:** A **decision not yet made**. This is a governance-level policy that cannot be defined until the Sandbox Simulation is implemented and produces observable results.