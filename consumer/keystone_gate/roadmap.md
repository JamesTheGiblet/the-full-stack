# **Keystone Gate — Consumer Roadmap**

> This roadmap outlines the planned features and development direction for the Keystone Gate consumer. It is derived from the "Planned" section of the `README.md` and will be updated as the project evolves.

---

## **Core Feature Development**

This section covers the primary features planned for implementation.

### **v1.3 — Self-Calibration and Vocabulary Management**

-   **Meta-Gate Self-Calibration:**
    -   **Goal:** Implement a self-calibrating mechanism for the gate's thresholds (e.g., similarity, confidence).
    -   **Description:** Instead of using fixed, hardcoded thresholds, the Meta-Gate will analyze the corpus of approved and rejected capsules to dynamically adjust its own parameters, improving accuracy over time.

-   **Field Expiration and Pruning:**
    -   **Goal:** Introduce a lifecycle for discovered fields to prevent vocabulary bloat.
    -   **Description:** Implement a mechanism to track field usage frequency and age. Fields that are rarely used or have become obsolete will be automatically pruned from the `capsule_primitives.json` vocabulary.

### **v1.4 — Tooling and Integration**

-   **Migration Tooling (LLM-assisted):**
    -   **Goal:** Create tools to simplify the migration of capsules when breaking schema changes occur.
    -   **Description:** Develop a CLI tool that uses an LLM to intelligently rewrite capsule content to conform to a new schema version, reducing the manual effort of migrations.

-   **Full HAL Integration (Multi-validator flow):**
    -   **Goal:** Integrate with a multi-validator HAL workflow.
    -   **Description:** Enhance the gate to support scenarios where multiple authorisers (with distinct keys and λ scores) are required to seal a decision, moving beyond the current single-operator model.

### **v1.5 — Analytics and Performance**

-   **Performance Benchmarking:**
    -   **Goal:** Establish performance benchmarks for core operations like processing, mutation, and validation.
    -   **Description:** Create a standardized test suite to measure and track performance over time, identifying bottlenecks and ensuring the system remains efficient as the capsule corpus grows.

-   **Visualisation Dashboard:**
    -   **Goal:** Create a web-based dashboard for visualizing gate activity.
    -   **Description:** Develop a simple dashboard to display key metrics, such as capsule approval rates, field discovery trends, and lineage graphs, providing an intuitive overview of the system's health and evolution.
