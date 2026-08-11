# **Keystone Gate — Consumer Documentation**

## *A governed semantic‑capsule validation, mutation, and lineage‑tracking system*

---

## **Overview**

Keystone Gate is a **consumer** within the Forge Stack, located at `consumer/keystone_gate/`. It uses the existing stack infrastructure (SCP, DataCube, Leighton Weight Engine, ChronoSCRIBE, HAL) to provide a governance layer for semantic capsule evolution.

**What Keystone Gate adds:**
- **Primitive Manager** — living field vocabulary with auto-discovery
- **Adaptive validation** — soft schema validation with field registration
- **Semantic similarity** — field-aware embedding and comparison
- **Mutation Engine** — intelligent semantic operators (merge, extend, invert, substitute, evolve, optimise)
- **Confidence scoring** — composite metric with field innovation weighting
- **Deliberation pool** — automatic merging of flagged capsules
- **Meta-Gate** (planned) — self-calibrating thresholds

**What Keystone Gate assumes (already in the stack):**
- SCP protocol (`freeze.py`, `sign.py`)
- ChronoSCRIBE (`genesis.py`, `ledger.py`, `ledger.jsonl`)
- DataCube (`datacube.py`, cubes, store)
- Leighton Weight Engine (`leighton_weight.py`, λ, k calibration)
- HAL (`hal.py`, seals, tiers)

---

## **Location & Structure**

Keystone Gate lives at `consumer/keystone_gate/` within the full stack:

```
the-full-stack/
├── consumer/
│   └── keystone_gate/           # ← You are here
│       ├── README.md            # This file
│       ├── CHANGELOG.md         # Consumer changelog
│       ├── ROADMAP.md           # Consumer roadmap
│       ├── capsule_primitives.json
│       ├── capsule_cache.json
│       ├── keystone_gate/
│       │   ├── __init__.py
│       │   ├── core.py
│       │   ├── primitives.py
│       │   ├── mutation.py
│       │   └── cli.py
│       └── tests/
├── sc/                          # Root stack capsules
├── ledger.jsonl                 # Root ledger
├── freeze.py                    # Stack tools
├── sign.py
├── ledger.py
├── datacube.py
├── leighton_weight.py
└── hal.py
```

---

## **Integration with Stack Tools**

Keystone Gate uses the stack tools via absolute paths or `PATH`:

```python
import subprocess
import json

# Stack tools are assumed to be in PATH or at known locations
STACK_PATH = "../.."  # Relative from consumer/keystone_gate/

def freeze_capsule(capsule_path):
    subprocess.run([f"{STACK_PATH}/freeze.py", capsule_path], check=True)

def sign_capsule(capsule_path):
    subprocess.run([
        f"{STACK_PATH}/sign.py", capsule_path,
        "--key-id", "did:key:z6MktudRY5LBZJeE13BiF4BeisAwWs7gvg6srh2GwLAMKDwJ"
    ], check=True)

def pin_to_ledger(capsule_path):
    subprocess.run([
        f"{STACK_PATH}/ledger.py", "append-pins",
        "--scope", "keystone_gate"
    ], check=True)
```

---

## **Consumer Ledger**

Keystone Gate has its own consumer ledger, anchored to the root ledger:

```bash
# Create/verify consumer ledger
python ../ledger.py append-pins --scope keystone_gate
python ../ledger.py verify --scope keystone_gate
```

The consumer ledger is at `consumer/keystone_gate/ledger.jsonl` and cryptographically anchored to the root chain.

---

## **Basic Usage**

### **1. Process LLM Output**

```python
from keystone_gate import KeystoneGate

gate = KeystoneGate(
    primitive_file='capsule_primitives.json',
    cache_file='capsule_cache.json'
)

# Process LLM output
llm_output = {
    "scp_id": "keystone/example-v1",
    "scp_version": "1.0.0",
    "created": "2026-08-10T00:00:00Z",
    "declaration": {
        "intent": "Educational simulator",
        "parameters": {
            "phases": ["intro", "practice", "assessment"],
            "difficulty": "intermediate"
        }
    }
}

result = gate.process(llm_output)
print(f"Status: {result['status']}")  # approved / flagged / rejected
print(f"Confidence: {result['confidence_score']}")
print(f"New fields discovered: {result.get('new_fields', [])}")
```

### **2. Full Pipeline with Stack Tools**

```python
import subprocess
import json
from keystone_gate import KeystoneGate

gate = KeystoneGate('capsule_primitives.json', 'capsule_cache.json')

# 1. Process through Gate
result = gate.process(llm_output)
if result['status'] != 'approved':
    print(f"Rejected: {result.get('errors', [])}")
    exit(1)

# 2. Write capsule
capsule_path = 'capsule.sc.json'
with open(capsule_path, 'w') as f:
    json.dump(result['capsule'], f, indent=2)

# 3. Freeze placeholders
subprocess.run(['../freeze.py', capsule_path], check=True)

# 4. Sign capsule
subprocess.run([
    '../sign.py', capsule_path,
    '--key-id', 'did:key:z6MktudRY5LBZJeE13BiF4BeisAwWs7gvg6srh2GwLAMKDwJ'
], check=True)

# 5. Pin to consumer ledger
subprocess.run(['../ledger.py', 'append-pins', '--scope', 'keystone_gate'], check=True)

# 6. Verify
subprocess.run(['../ledger.py', 'verify', '--scope', 'keystone_gate'], check=True)
```

### **3. Perform Mutations**

```python
from keystone_gate import MutationEngine

mutator = MutationEngine(gate, primitive_manager)

# Evolve a capsule (adds missing fields from field pool)
new_capsule = mutator.mutate(
    ['keystone/example-v1'],
    operation='evolve'
)

# Merge two capsules
new_capsule = mutator.mutate(
    ['keystone/example-v1', 'keystone/example-v2'],
    operation='merge',
    innovation_weight=0.3
)

# Optimise (remove bloated fields)
new_capsule = mutator.mutate(
    ['keystone/example-v1'],
    operation='optimise'
)
```

### **4. Query Lineage**

```python
from keystone_gate import ChronoSCRIBE

# ChronoSCRIBE wrapper for consumer ledger
chrono = ChronoSCRIBE('ledger.jsonl')

lineage = chrono.get_lineage('keystone/example-v1')
print(f"Ancestors: {lineage['ancestors']}")
print(f"Descendants: {lineage['descendants']}")
print(f"Field inheritance: {lineage['field_inheritance']}")
```

---

## **Configuration**

Keystone Gate expects the stack tools to be accessible:

```bash
# Check tools are available
cd consumer/keystone_gate
ls ../freeze.py ../sign.py ../ledger.py ../datacube.py ../leighton_weight.py ../hal.py
```

If not in `PATH`, set the `FORGE_STACK_PATH` environment variable:

```bash
export FORGE_STACK_PATH=../..  # From consumer/keystone_gate/
```

---

## **CLI Interface**

Keystone Gate provides a CLI for common operations:

```bash
cd consumer/keystone_gate

# Process LLM output
keystone-gate process --input llm_output.json

# Mutate capsules
keystone-gate mutate --ids id1,id2 --operation merge

# Show lineage
keystone-gate lineage --id keystone/example-v1

# Show inspiration breakdown
keystone-gate inspiration --id keystone/example-v1

# List approved capsules
keystone-gate list --status approved

# Run sandbox simulation
keystone-gate sandbox --iterations 50
```

---

## **Known Limitations (Consumer View)**

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **Field cooccurrence is heuristic** | May suggest nonsensical field combinations | Review mutations before pinning |
| **No Meta-Gate self-calibration** | Thresholds remain fixed | Manual threshold adjustment in config |
| **HAL single-operator** | All seals `separation: none` | Accept for now; upgrade when second operator exists |
| **k not calibrated** | λ values are demonstration only | Use domain-specific k when available |
| **No field expiration** | Vocabulary may bloat | Manual primitive file cleanup |
| **Migration tooling missing** | Breaking schema changes hard | Use LLM-assisted migration manually |

---

## **Roadmap (Consumer)**

### **Implemented**
- ✅ Primitive Manager with auto-discovery
- ✅ Adaptive validation (required + optional fields)
- ✅ Field-aware semantic embedding
- ✅ Five mutation operators (merge, extend, invert, substitute, evolve)
- ✅ Optimisation operator
- ✅ Field cooccurrence tracking
- ✅ Field innovation scoring
- ✅ Deliberation pool (auto-merge flagged capsules)
- ✅ Integration with Forge Stack tools

### **Planned**
- 🔄 Meta-Gate self-calibration
- 🔄 Field expiration and pruning
- 🔄 Migration tooling (LLM-assisted)
- 🔄 Performance benchmarking
- 🔄 Visualisation dashboard
- 🔄 Full HAL integration (multi-validator flow)

---

## **Changelog**

See [`CHANGELOG.md`](./CHANGELOG.md) for the consumer's build history.

---

## **Ethical Use**

Keystone Gate is intended for:
- simulation and research
- behavioural modelling
- controlled concept evolution
- sovereign AI stack experimentation

**Single-operator disclosure:** This consumer runs within a single-operator stack. HAL seals carry `separation: none`. This is stated honestly and should not be described as providing separation-of-concerns guarantees.

---

## **Contributing**

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with:
   - New field registrations (if introducing new capsule properties)
   - Updated Primitive Manager (if adding mutation operators)
   - Integration tests against stack tools
   - Updated documentation

**Before submitting:**
```bash
# Test with stack tools
keystone-gate test --integration

# Lint and format
pylint keystone_gate/
black keystone_gate/

# Run tests
pytest tests/
```

---

## **Glossary (Consumer Context)**

| Term | Definition |
|------|------------|
| **Primitive Manager** | Keystone Gate's living field vocabulary |
| **Adaptive validation** | Soft validation with auto-discovery |
| **Field-aware embedding** | Semantic similarity by field type |
| **Mutation Engine** | Keystone Gate's intelligent operators |
| **Deliberation pool** | Auto-merge of flagged capsules |
| **Meta-Gate** | Planned self-calibrating thresholds |

*For full Forge Stack terminology, see `../../docs/glossary.md`.*

---

## **Licence**

MSL-1.0 — Forge Stack licence terms apply.

---

*Keystone Gate is a consumer within the Forge Stack, located at `consumer/keystone_gate/`. It relies on the stack's existing infrastructure for cryptographic signing, auditing, classification, trust scoring, and human accountability. This documentation describes the consumer layer only. For stack-wide documentation, see `../../README.md`.*

*Last updated: 2026-08-10*