# README.md

# Long Con Generator

## A Sovereign AI Stack for Novel Concept Generation & Validation

This is an AI-assisted build: architecture, decisions, and verification are mine; implementation velocity comes from working alongside AI.

---

## Status

| Stage | System | Artefact | Status |
|-------|--------|----------|--------|
| **Declare** | SCP | `sc` | ✅ Implemented |
| **Classify** | DataCube | `cube` | 🔄 In progress |
| **Trust-score** | Leighton Weight Engine | `λ` | ✅ Implemented |
| **Audit** | ChronoSCRIBE | `ledger` | ✅ Implemented |
| **Act** | HAL | `seal` | ⏳ Not started |

---

## Overview

The Long Con Generator is a modular, auditable system for generating, validating, and tracking novel patterns using semantic capsules, confidence scoring, and cryptographic audit trails.

**Key innovation:** No fine-tuning required. Any LLM can be used. The Keystone Gate validates and scores output against a canonical schema; ChronoSCRIBE provides full forensic traceability.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER PROMPT                               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         LLM (Any Model)                           │
│                   Generates raw capsule JSON                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        KEYSTONE GATE                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │   Schema   │→ │  Semantic  │→ │  Leighton  │→ │ChronoSCRIBE│ │
│  │  Validator │  │ Similarity │  │   Weight   │  │   Logger   │ │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘ │
│        ↓               ↓               ↓               ↓         │
│  long_con.sc.json Capsule DB    Confidence     Hash Log          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                  ┌───────────────┼───────────────┐
                  ▼               ▼               ▼
            [APPROVED]      [FLAGGED]        [REJECTED]
                  │               │               │
                  ▼               ▼               ▼
           ┌────────────┐  ┌────────────┐  ┌────────────┐
           │  Sandbox   │  │   Human    │  │ Correction │
           │  Testing   │  │   Review   │  │   Prompt   │
           └────────────┘  └────────────┘  └────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  MUTATION ENGINE   │
         │ Novel Generation   │
         └────────────────────┘
                  │
                  ▼
        ChronoSCRIBE logs lineage,
        inspiration_map, and drift
```

---

## Core Components

### 1. SCP & `long_con.sc.json`

The **Semantic Capsule Protocol** (SCP) is the Declare stage. It produces `sc` artefacts — signed, versioned, inheritable documents that state intent, parameters, and constraints.

The master schema `long_con.sc.json` defines the canonical structure for every capsule:

- `capsule_id`: Unique identifier
- `archetype`: financial, romantic, corporate, political, hybrid
- `phases`: put_up → pay_off → takedown (minimum 3)
- `trust_mechanics`: small_wins, authority_fabrication, emotional_hook
- `exit_conditions`: triggers, actions, fallbacks
- `target_profile`: demographic, psychological_triggers, vulnerabilities
- `leighton_weight`: Confidence score (0.00–2.00)
- `inspiration_map`: Source capsules and contributions
- `chronoscribe`: Audit trail

### 2. Keystone Gate (`keystone_gate.py`)

The guardrail between LLM and output.

**Process:**
1. Parse LLM JSON output
2. Validate against `long_con.sc.json`
3. Generate semantic embedding
4. Check similarity against existing capsules
5. Calculate Leighton Weight (`λ`)
6. Log to ChronoSCRIBE
7. Route: Approve / Flag / Reject

```python
gate.process(llm_output: str) -> Dict
# Returns: {status, capsule, leighton_weight, message}
```

### 3. Leighton Weight Engine

The Trust-score stage. Computes `λ` — how much an entity's word is currently worth — based on a neutral-attractor decay curve:

`λ(t) = 1.00 + (λ0 − 1.00) × e^(−kt)`

In this implementation, Leighton Weight is flipped from a decay curve to a **similarity anchor** measuring:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Schema Completeness | 30% | % of required fields populated |
| Phase Consistency | 25% | Logical flow: put_up → pay_off → takedown |
| Cross-Capsule Novelty | 25% | 1 − max similarity to existing |
| Inspiration Richness | 20% | Number and diversity of sources |

**Thresholds:**
- **≥ 0.75**: Approved for sandbox testing
- **0.50 – 0.75**: Flagged for human review
- **< 0.50**: Rejected with correction prompt

### 4. ChronoSCRIBE (`chronoscribe_full.py`)

**Signed Chronological Record of Immutable Behavioural Events.** The Audit stage. A hash-chained, append-only, signed record.

**Features:**
- Full event logging
- Hash chain for tamper-proof records
- Lineage tracking (ancestor → descendant)
- Inspiration breakdown
- Sandbox result storage
- SQLite backend

```python
chronoscribe.log_event(capsule, event_type, **kwargs) -> hash
chronoscribe.get_lineage(capsule_id) -> List[Dict]
chronoscribe.get_inspiration_breakdown(capsule_id) -> Dict
```

### 5. Mutation Engine (`mutation_engine.py`)

Generates novel concepts from existing capsules.

**Operations:**
- **Merge**: Combine phases and mechanics from multiple capsules
- **Extend**: Add new phases to an existing capsule
- **Invert**: Swap roles (mark becomes con artist)
- **Substitute**: Replace key elements (e.g., archetype)

```python
mutator.mutate(capsule_ids: List[str], operation: str = None) -> Dict
# Returns: Gate result for new capsule
```

---

## Database Schema (SQLite)

### Capsules Table
```sql
CREATE TABLE capsules (
    capsule_id TEXT PRIMARY KEY,
    name TEXT,
    archetype TEXT,
    version INTEGER,
    leighton_weight REAL,
    created_at TEXT,
    last_modified TEXT,
    current_hash TEXT,
    status TEXT,
    capsule_json TEXT
);
```

### Events Table (Full Audit)
```sql
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    capsule_id TEXT,
    timestamp TEXT,
    event_type TEXT,
    hash TEXT,
    parent_hashes TEXT,
    leighton_weight REAL,
    gate_decision TEXT,
    inspiration_map TEXT,
    similarity_results TEXT,
    details TEXT,
    FOREIGN KEY (capsule_id) REFERENCES capsules(capsule_id)
);
```

### Lineage Table (Traceability)
```sql
CREATE TABLE lineage (
    descendant_id TEXT,
    ancestor_id TEXT,
    similarity REAL,
    phase_contribution TEXT,
    mutation_operation TEXT,
    timestamp TEXT,
    PRIMARY KEY (descendant_id, ancestor_id)
);
```

---

## Quick Start

### Installation

```bash
# Clone and install dependencies
pip install jsonschema sentence-transformers scikit-learn pandas

# Initialise database
python -c "from chronoscribe_full import ChronoScribe; ChronoScribe('chronoscribe.db')"
```

### Basic Usage

```python
from keystone_gate import KeystoneGate
from chronoscribe_full import ChronoScribe
from mutation_engine import MutationEngine

# Initialise
gate = KeystoneGate('long_con.sc.json', 'capsule_db.json')
chronoscribe = ChronoScribe('chronoscribe.db')
mutator = MutationEngine(gate, chronoscribe)

# Process LLM output
llm_output = """{...}"""  # JSON from any LLM
result = gate.process(llm_output)

if result['status'] == 'approved':
    print(f"✅ Approved: {result['capsule']['name']}")
    print(f"Leighton Weight: {result['leighton_weight']:.3f}")
elif result['status'] == 'rejected':
    print(f"❌ Rejected: {result['message']}")
    print(f"Correction prompt: {result['correction_prompt']}")

# Mutate existing concepts
new_capsule = mutator.mutate(['capsule-001', 'capsule-002'], 'merge')

# Query lineage
lineage = chronoscribe.get_lineage('new-capsule-003')

# Get inspiration breakdown
inspiration = chronoscribe.get_inspiration_breakdown('new-capsule-003')
```

### Main Pipeline Script

```bash
python main.py
```

**Options:**
1. Generate new con from prompt
2. Mutate existing concepts
3. Query lineage
4. Show inspiration breakdown
5. List approved capsules
6. Sandbox simulation (stub)

---

## Verification

```bash
# Verify the ledger chain
python ledger.py verify

# Verify a signed capsule
python sign.py --verify long_con.sc.json

# Verify a cube (once implemented)
python datacube.py verify-store
```

---

## Known Limitations

### Data Persistence
- **`capsule_db.json`** is an in-memory demonstration store. State is lost on restart and the system cannot scale beyond a small number of capsules. A persistent database solution (SQLite or document DB) is planned.

### Leighton Weight Calibration
- The weights and thresholds for Leighton Weight scoring are currently demonstration constants. Calibration against a real dataset is required before the scores are meaningful for quality assessment.

### Sandbox Simulation
- The sandbox for agent-based modelling is a non-functional stub. Testing generated concepts for functional viability is not yet possible.

### Embedding Caching
- No caching exists for sentence-transformer embeddings. Performance will degrade as the capsule database grows.

### Governance
- Outcome-to-score mapping for sandbox results is not yet defined. This blocks the feedback loop required for the system to learn which patterns are effective.

---

## File Structure

```
.
├── long_con.sc.json          # Master schema
├── keystone_gate.py          # Guardrail + validation + scoring
├── chronoscribe_full.py      # Audit trail + lineage
├── mutation_engine.py        # Novel generation
├── main.py                   # Pipeline script
├── capsule_db.json           # Stored capsules (in-memory demo)
├── chronoscribe.db           # SQLite audit database
├── CHANGELOG.md              # Append-only record of what shipped
├── ROADMAP.md                # What is not yet built
└── README.md
```

---

## Relationship to Forge Stack

This project is built on the **Forge Stack** — a sovereign AI stack for declarative, auditable, accountable system building.

The stack's five stages are:

| Stage | System | Artefact |
|-------|--------|----------|
| Declare | SCP | `sc` |
| Classify | DataCube | `cube` |
| Trust-score | Leighton Weight Engine | `λ` |
| Audit | ChronoSCRIBE | `ledger` |
| Act | HAL | `seal` |

For details, see the Forge Stack capsules:
- `forge-stack/docs/tools-reference-v1`
- `forge-stack/docs/documentation-style-v1`
- `forge-stack/docs/roadmap-process-v1`
- `forge-stack/docs/changelog-v1`

---

## Ethics

This system is designed for:

- **Cybersecurity red-team exercises**
- **Academic psychology research**
- **Defensive counter-narrative generation**

All concepts are intended for simulation and analysis only, not for real-world deployment.

---

## License

MIT — for research and defensive purposes only.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

*Built on the Forge Stack.*