# 🤖 Nova-bot

**A physical robotics platform, built on an ESP32, governed by the Forge Stack.**

*From simulation to silicon. From bits to atoms.*

> **Status: pre-alpha.** This document is the design specification for a new hardware consumer. The chassis is defined, but the code is not yet written.

`Nova-bot` is a new **consumer** of the Forge Stack, representing the stack's first venture into physical hardware. It resides in `consumer/nova-bot/`, holds its own capsule namespace, maintains its own consumer ledger, and inherits its governance model from the root stack.

---

## 🎯 The Core Question

`Nova_bot` is designed to answer a fundamental question: **What happens when a physical robot's every action and observation is part of a verifiable, trust-scored, and immutable audit trail?**

Unlike a simulation where the physics are programmed, a physical robot contends with the real world's noise, uncertainty, and unpredictability. `Nova-bot` will explore how the Forge Stack's principles can be used to build a reliable, auditable agent that operates under these challenging conditions. Can we prove, cryptographically, that the robot did what it said it did, and can we score its reliability over time as it interacts with an imperfect world?

---

## Hardware Specification

The initial prototype (`v1`) is built on a standardized, reproducible hardware set:

| Component | Specification | Role |
|---|---|---|
| **Chassis** | Round chassis with TT motors | Mobility |
| **MCU** | ESP32 Development Board | Central processing |
| **Power** | 2x 3.7V 1800mAh Li-ion (in series) | 7.4V nominal supply |
| **Regulation** | Digital buck converter | Stable voltage for components |
| **Motor Driver**| H-Bridge Driver | Motor control and direction |
| **Sensors** | 2x Photocell sensors | Ambient light detection |
| **Sensors** | 1x Ultrasonic sensor (front) | Obstacle detection / distance measurement |
| **Sensors** | 2x Motor encoders | Wheel rotation tracking for odometry |
| **Feedback** | Battery level indicator | Power status monitoring |

---

## 🏛️ The Forge Stack in the Physical World

`Nova-bot` maps the five stages of the Forge Stack directly onto its physical operations.

| Stage | System → Artefact | In `Nova_bot` |
|---|---|---|
| **Declare** | SCP → `sc` | The robot's own hardware manifest and identity is a signed Semantic Capsule. Its "birth" is the moment its capsule is minted. |
| **Classify** | DataCube → `cube` | Sensor readings are classified through the six lenses. An ultrasonic distance reading is a **FACT**. A sudden drop in light from a photocell is **CONTEXT**. A series of movements without hitting an obstacle is an **OPINION** that the path is clear. |
| **Trust-score** | Leighton Weight Engine → λ | The robot's own reliability is scored. If its odometry-based movement commands consistently match real-world outcomes (verified by other sensors), its `navigation.execution` lambda score increases. A high-lambda robot is a reliable one. |
| **Audit** | ChronoSCRIBE → ledger | Every significant event—a motor command, a sensor reading, a decision to turn—is recorded as a hash-chained entry in `consumer/nova-bot/ledger.jsonl`. This creates a verifiable history of the robot's entire operational life. |
| **Act** | HAL → seal | High-consequence actions, like moving at maximum speed or entering a previously unmapped area, can be defined to require a HAL seal, authorized by the operator based on the robot's current lambda score. |

---

### Declare — The Hardware Capsule

The robot's existence begins with a signed capsule that declares its physical components. This provides a verifiable manifest of its capabilities.

```json
// sc/nova_bot/hardware-manifest-v1.sc.json
{
  "scp_id": "nova_bot/hardware-manifest-v1",
  "created": "2026-08-16T12:00:00Z",
  "declaration": {
    "intent": "To declare the physical components and capabilities of the Nova_bot v1 prototype.",
    "parameters": {
      "mcu": "ESP32",
      "sensors": ["ultrasonic-HC-SR04", "photoresistor-gl5528", "motor-encoder-tt"],
      "actuators": ["motor-tt", "h-bridge-l298n"]
    }
  },
  "signature": { ... }
}
```

### Classify — Sensor Data as Claims

A sensor reading is not ground truth; it is a claim about the world.

| Lens | Sensor Reading Example |
|---|---|
| **FACT** | Ultrasonic sensor reports an object 25cm away. |
| **COUNTER** | Left photocell reports darkness; right photocell reports brightness. This counters the opinion "the area is uniformly lit." |
| **OPINION** | After moving forward 10cm without the ultrasonic distance changing, the robot forms the opinion "the object ahead is a flat wall." |
| **FICTION** | A hypothetical scenario used for planning: "What if there were an obstacle 5cm to my left?" |
| **CONTEXT** | Both photocells report low light levels, indicating the robot is likely under an object or in a dark room. |
| **UNKNOWN** | The area behind the robot is currently unobserved. |

### Trust-score — Scoring Reliability

The Leighton Weight Engine will be used to score the robot's performance in key domains. For example, a `navigation` domain score could be influenced by:
- **`succeeded`**: A move command completed without triggering an obstacle alert.
- **`failed`**: A move command resulted in a stall or unexpected collision (detected by encoders vs. ultrasonic).
- **`confirmed`**: The robot successfully returns to a previously mapped location.

A robot with a high lambda score is one that can be trusted to execute its plans successfully.

### Audit — A Robot's Diary

The `ledger.jsonl` becomes the robot's immutable diary.

```json
// consumer/Nova_bot/ledger.jsonl entry
{
  "seq": 101,
  "event": "command.motor.move",
  "subject": "move-forward-10cm",
  "sha256": "...", // hash of the command parameters
  "prev": "...",
  "signature": { ... }
}
```
This allows for perfect, verifiable replay and analysis of the robot's behavior, answering not just *what* it did, but *when* and in what order.

### Act — Gated Actions

The HAL system provides a crucial safety layer.

| Tier | Action Class | λ Required |
|---|---|---|
| 1 | Routine sensing, slow movement | ≥ 0.60 |
| 2 | Standard speed movement in a mapped area | ≥ 0.90 |
| 3 | Exploring an unmapped area | ≥ 1.20 |
| 4 | Moving at maximum velocity | ≥ 1.50 |
| 5 | Executing a firmware update | ≥ 1.80 + seal |

---

## 📂 Consumer Structure
```
consumer/Nova_bot/
├── README.md                 # This document
├── ROADMAP.md                # Forward-looking plan
├── CHANGELOG.md              # History of changes
├── ledger.jsonl              # Consumer-specific audit ledger
├── sc/                       # Semantic capsules for hardware, etc.
└── src/                      # Source code (C++/MicroPython for ESP32)
```

---

## 📜 Governance

`Nova_bot` inherits its governance model under **MSL-1.0** via the Forge Stack. All significant design decisions and hardware changes will be ratified in signed capsules and witnessed in the ledger.