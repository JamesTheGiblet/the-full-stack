# Nova-bot Consumer Roadmap

This document outlines the planned firmware and software work for the `nova-bot` physical robotics consumer. The initial project scaffolding, capsule creation, and ledger initialization are now complete (see `CHANGELOG.md` v0.4).

---

## 1. Firmware Implementation (ESP32)

### 1.1. Basic Motor Control
  - [x] Create initial `src/motor_control.cpp` sketch with basic mobility functions.
  - [ ] Test motor functions (forward, backward, turn, stop) on the physical hardware.
  - [ ] Implement runtime loading of pin configurations from the semantic capsule.

### 1.2. Sensor Integration
  - [ ] Write firmware to read distance from the front-facing ultrasonic sensor.
  - [ ] Write firmware to read ambient light levels from the two photocell sensors.
  - [ ] Write firmware to read rotational data from the TT motor encoders for odometry.

### 1.3. Power Management
  - [ ] Write firmware to read voltage from the battery level indicator.
  - [ ] Implement a safe low-power state (e.g., stop motors, disable sensors) when the battery level drops below a critical threshold.

---

## 2. Forge Stack Integration

### 2.1. Ledger Communication
  - [ ] Decide on a communication protocol (Serial, Wi-Fi, etc.) for the ESP32 to offload data.
  - [ ] Implement the chosen protocol to send formatted event data to a host machine.

### 2.2. Onboard Decision Loop
  - [ ] Design and implement the main `loop()` function to follow a `Sense -> Decide -> Act` cycle.
  - [ ] Integrate sensor readings into the decision logic (e.g., stop if an obstacle is detected).

### 2.3. Capsule Loading
  - [ ] Decide on a method for storing configuration on the ESP32 (e.g., SPIFFS, LittleFS).
  - [x] Externalize pin configuration into `pin-configuration-v1.sc.json`.
  - [ ] Write firmware to read and parse the capsule from the chosen storage.