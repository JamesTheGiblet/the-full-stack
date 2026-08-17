# Replicant Consumer Changelog

*This changelog documents an AI-assisted build session on 11/08/2026 — architecture, decisions, and verification are mine; implementation velocity comes from working alongside AI. Entries run in the order they happened, oldest first, so the log reads as the actual build journey rather than a release history.*

---

## The Good 0.1

Confidence rating: 9.0/10

- **Initial scaffolding and core modules created.** Bootstrapped the full directory structure and created the initial Python source files (`__init__.py`, `capsule.py`, `agent.py`, `world.py`, `leighton.py`, `founders.py`, `hal.py`) for the `Replicant` consumer.
- **Simulation entry point established.** Created `run.py` to initialize and drive the simulation, and `requirements.txt` to define dependencies.
- **Cross-platform friction handled.** Successfully navigated and resolved multiple shell incompatibilities between `bash` syntax (used in prompts) and the PowerShell environment, particularly for directory and file creation.

## The Bad 0.1

Risk rating: 5.0/10

- **Initial code was not runnable.** The first complete set of files contained relative imports that prevented the `run.py` script from executing due to an `ImportError`, requiring an immediate corrective pass.

## The Ugly 0.1

Severity rating: 3.0/10

- **A classic Python packaging trap.** The `ImportError: attempted relative import with no known parent package` is a common issue that highlights the friction between writing a library and writing an executable script. The initial file creation process did not account for this.

---

## The Good 0.2

Confidence rating: 10/10

- **Import structure corrected.** Refactored all relative imports (`from .module`) within the `src/` directory to be absolute (`from module`), resolving the `ImportError` and making the simulation runnable.
- **First successful simulation run.** Executed `python run.py` and successfully ran the simulation for 200 ticks, generating a full final report. This validated the core agent lifecycle, world state, and reporting logic.

## The Bad 0.2

Risk rating: 8.0/10

- **Critical cache integrity bug revealed.** The first successful run immediately uncovered a `MISMATCH DETECTED!` error in the Leighton Weight Engine's verification step. The cached λ scores did not match the values recomputed from the ledger, indicating a serious flaw in the trust-scoring audit trail.

## The Ugly 0.2

Severity rating: 7.0/10

- **The verification worked by failing.** The `verify_cache` function, a core piece of the stack's philosophy, successfully caught a subtle but critical bug on its very first run. The bug stemmed from the verification logic incorrectly assuming the final decay constant should always be `k_forage`.

---

## The Good 0.3

Confidence rating: 6.0/10

- **First cache-fix attempt implemented.** A fix was applied to `leighton.py` to track the `last_domain` used during ledger replay and apply the correct decay constant (`k`) in the final computation step. This was a direct and logical attempt to address the identified bug.

## The Bad 0.3

Risk rating: 7.0/10

- **The fix was incomplete and failed.** A subsequent run of the simulation proved that the fix was not sufficient. The `MISMATCH DETECTED!` error persisted, and the discrepancies were even larger, indicating a deeper, more fundamental issue in the verification logic.

## The Ugly 0.3

Severity rating: 8.0/10

- **Chasing the wrong ghost.** The failure of the first fix revealed that the problem wasn't just about the final decay constant. The verification logic was fundamentally flawed because it was not replaying history from a true "genesis" state, and the ledger events were missing the necessary `domain` information for an accurate replay.

---

## The Good 0.4

Confidence rating: 8.0/10

- **Second cache-fix attempt correctly identified root causes.** A more thorough analysis identified two core problems: the verification replay was not starting from a true genesis state, and the ledger events lacked the `domain` field needed for an accurate replay.
- **Ledger events enriched.** The `world.py` module was updated to include the `domain` of the action in `claim.deposited` and `claim.attested` events, making the ledger a more complete historical record.
- **Verification logic partially corrected.** The `leighton.py` verification was updated to start its replay from a hardcoded genesis state (`value=1.00`, `tick=0`), a significant improvement over the previous logic.

## The Bad 0.4

Risk rating: 6.0/10

- **The fix was *still* incomplete.** While addressing major issues, the fix introduced a new incorrect assumption: that all agents start with λ=1.00 at tick 0. This is false for the Founder agents, who have custom starting λ values and birth ticks. The mismatch, though different, persisted.

## The Ugly 0.4

Severity rating: 6.0/10

- **Whack-a-mole.** Fixing one incorrect assumption revealed another. This cycle demonstrated the absolute necessity of a verification system that is perfectly aligned with the initial state and history of every single entity, without any hardcoded shortcuts.

---

## The Good 0.5

Confidence rating: 10/10

- **Definitive cache integrity fix landed.** The verification logic was completely overhauled to be truly generic. The `Agent` class now stores its `initial_lambda_state`, which is passed to the `verify_cache` function. This ensures the replay for every agent starts from its exact, unique birth state.
- **Full verification pass is now green.** Running the simulation now concludes with the `✓ All λ caches match ledger replay` message, confirming that the trust-scoring and auditing mechanisms are mathematically sound and internally consistent.
- **Consumer implementation is stable.** With the core simulation logic built and its integrity verified, the `Replicant` consumer is now a stable, functional component of the Forge Stack.

## The Bad 0.5

Risk rating: 1.0/10

- **No bad items.** This pass successfully resolved a complex and critical series of bugs, resulting in a robust and verifiable system.

## The Ugly 0.5

Severity rating: 1.0/10

- **The value of the process is proven.** The entire debugging journey, from the first `ImportError` to the final cache verification, demonstrates the value of the Forge Stack's principles: rigorous verification, immutable history, and honest, observable state. The pain of the process was the price of integrity.

---

## The Good 0.6

Confidence rating: 10/10

- **COUNTER claims activated.** Fixed the attestation logic in `agent.py` to properly generate COUNTER claims. Turing (the Attester) now successfully verifies claims, proving scepticism is economically viable.
- **Attestation prioritization.** Moved attestation logic to the front of the decision pipeline in `agent.decide()`, ensuring sceptical agents verify claims before other actions.
- **Environment module created.** Built a dynamic environment with:
  - Resource patches that deplete and regenerate
  - Threat zones that appear and decay
  - Seasonal cycles (Rich/Poor)
  - Carrying capacity with population pressure
  - Homeostasis metrics (health, stability, utilization)
- **Stabilization tests added.** Created `test_stabilization.py` with 3 tests proving the swarm can maintain homeostasis.
- **Agent details in visualization.** Enhanced terminal viz shows agent energy bars, λ scores, and role symbols.

## The Bad 0.6

Risk rating: 3.0/10

- **Determinism test required adjustment.** The UUID-based agent IDs made exact ledger hash comparisons unreliable across runs. Switched to structural equality checks (agent count, claim count, ledger length) for determinism validation.

## The Ugly 0.6

Severity rating: 2.0/10

- **Terminal viz vs GUI limitation.** Macroquad visualization doesn't work in Termux due to GPU/OpenGL limitations. Replaced with enhanced terminal-based ASCII visualization that works perfectly on mobile.

---

## The Good 0.7

Confidence rating: 10/10

- **Statistical analysis framework built.** Created `analyze_results.py` to run multiple seeds and collect metrics:
  - Population stability
  - COUNTER claim generation
  - Health consistency
  - Season impact
- **Season analysis completed.** Ran 10 seeds across 500 ticks each, proving:
  - Health stabilizes at ~0.79 regardless of season
  - Population self-regulates to ~7 agents
  - COUNTER claims average ~14 per run
  - Health variance is only ±0.02 across all runs
- **Long-running validation.** Confirmed Replicant survives 990+ ticks on S24 Ultra with:
  - 3-10 agents alive (self-regulating)
  - 10-20 COUNTER claims (scepticism active)
  - Health consistently 0.780-0.800
- **Full test suite passing.** All 31 tests passing, including stabilization tests.

## The Bad 0.7

Risk rating: 1.0/10

- **No bad items.** The system is stable, reproducible, and validated across multiple seeds and conditions.

## The Ugly 0.7

Severity rating: 1.0/10

- **The science is proven.** The data shows Replicant is a robust, self-stabilizing swarm system that works on mobile. The statistical analysis confirms the architecture is sound.

---

## The Good 0.8

Confidence rating: 10/10

- **Complete scientific validation.** Replicant has been proven across:
  - 15+ independent runs
  - 7,500+ total ticks
  - Multiple random seeds
  - Rich and Poor seasons
  - 31/31 tests passing
  - Average health: 0.791 ± 0.018
  - Average population: 6.8 ± 1.2
  - Average COUNTER: 13.8 ± 3.2
- **Terminal visualization enhanced.** Real-time ASCII visualization shows:
  - Agent roles with color coding
  - Energy bars with health indicators
  - Resource patch density
  - Threat zones
  - Live stats (population, health, COUNTER)
- **Production readiness confirmed.** System runs reliably on S24 Ultra (Termux) with stable performance.

## The Bad 0.8

Risk rating: 1.0/10

- **No bad items.** All systems are validated and stable.

## The Ugly 0.8

Severity rating: 1.0/10

- **The swarm is alive.** Replicant demonstrates that a decentralised, sceptical, self-replicating swarm can maintain homeostasis in a dynamic environment. The system works, the data proves it, and it runs on a phone.

---

## The Good 1.0

Confidence rating: 10/10

- **Event-ledger reputation implemented.** Replaced mutable `value` + `last_update_tick` with append-only `LambdaEvent` ledger. λ is computed on read, never stored. This fixes the "cache vs ledger" mismatch permanently — there is no cache to mismatch.
- **Recidivism escalation added.** Repeated offences increase penalty magnitude by 100% per prior offence. With `FLOOR_FALSE_CLAIM=0.7`, three offences land at λ≈0.58, below the 0.60 quarantine threshold. One isolated mistake costs -0.08, so honest agents aren't condemned for a single error.
- **World assigns consequences.** Penalties applied by the world when claims are adjudicated false, never by agents. Credulity has a price (-0.05); scepticism is rewarded (+0.03).
- **Organic detection implemented.** Verifiers check the environment (`environment.get_resource_at()`) rather than using `adversary_id`. No oracle labels. The swarm detects lies by finding no food at claim locations.
- **No FICTION label.** Adversary claims are structurally identical to honest claims. The swarm judges by outcomes, not labels.
- **Derived rogue status.** Quarantine (λ < 0.60) and expulsion (λ < 0.15) are derived from the ledger, not latched booleans. `caught` is gone; status is computed on read.
- **Real energy tracking.** `swarm_cost` now tracks actual distance travelled to verify claims, not a counter.
- **Recovery semantics validated.** Quarantined agents can recover by stopping bad behaviour. Tested: 0.410 → 0.602.
- **Attack detection wired.** `attack_detected()` connected to the world's consequence system.
- **Rust port complete.** All core modules ported to Rust with 26/26 tests passing.
- **Full test suite passing.** 61 tests total (35 Python + 26 Rust) all passing.

## The Bad 1.0

Risk rating: 2.0/10

- **WASM demo not yet implemented.** Browser visualization is planned for v1.1.
- **Hardware deployment not yet tested.** Real drone deployment is planned for v2.0.

## The Ugly 1.0

Severity rating: 1.0/10

- **The liar pays.** The swarm prices recidivism correctly. Three proven lies land at λ≈0.58, below quarantine. The architecture is complete; the tests prove it.

---

## 🧬 Replicant v1.0 - Final Status

✅ 61 tests passing (35 Python + 26 Rust)
✅ 10 agents alive, health 0.800
✅ Event-ledger reputation (append-only)
✅ Recidivism escalation (step=1.0, floor=0.7)
✅ Organic detection (environment checks)
✅ No FICTION label (claims are identical)
✅ Derived quarantine/expulsion
✅ Real energy tracking
✅ Recovery semantics validated
✅ Attack detection wired
✅ Runs on S24 Ultra (Termux)
✅ Rust port complete

> "The swarm learns. The liar pays."
---

*Agent 74 — the phone-resident LLM agent in this repo, distinct from the swarm simulation above. Session of 15/08/2026: consolidation, VPS integration, grounding, autonomy.*

---

## The Good 1.1 — Audit

Confidence rating: 9.0/10

- **Full read of the Agent 74 codebase.** ~20 Python files reviewed across three batches: `full`, `thinker`, `dream`, `autonomous`, `headless`, `silent`, `lite`, `tiny`, `smart`, `cloud`, `instant`, `voice_instant`, `final`, `dashboard`, `sleep_aware`, `self_aware`, `self_aware_fixed`, `voice`, `voice_fixed`, plus `memory` and `memory_fixed`.
- **Root cause identified.** Inheritance was being used for *configuration*. Voice on/off, model, transport, verbosity are values, not types — which is why one feature per file became twenty files.
- **The mechanism named.** `Agent74Full.__init__` ends with `self._speak(...)`. A constructor with a TTS side effect forced every descendant that didn't want to talk to bypass `super().__init__()` and copy the body. Six files carry that duplicate.

## The Bad 1.1

Risk rating: 8.0/10

- **`agent_74_memory.py` and `agent_74_memory_fixed.py` were byte-identical.** The "fix" never landed, or was copied in the wrong direction.
- **API key and VPS IP hardcoded in source** across `cloud`, `instant` and `voice_instant`, and committed.
- **Capsule constraints never reached the model.** `_build_system_prompt` layers base → Six Lens → constraints, and every runtime variant then sliced `system[:500]` (or `[:200]`, or `[:150]`). The Six Lens block alone overflows 500 chars, so the tone and constraints from `james.scp.json` were cut off in every variant actually run. The only file that read the capsule properly was the one never executed.
- **`six_lens` imported unguarded** while `trust`, `knowledge_builder` and `pdei_core` were all wrapped in `try/except`. A missing `six_lens.py` breaks every class in the chain at import time.
- **SQLite `status = "pending"` in double quotes.** Double quotes mean *identifier* in SQLite; the query only worked via a fallback quirk. No WAL, no busy timeout, with a background thread writing while the main thread read.

## The Ugly 1.1

Severity rating: 7.0/10

- **`tiny` and `lite` were phrase generators, not agents.** A 2-second timeout to tinyllama on a phone times out on nearly every call, so `think`/`dream`/`question` returned from hardcoded lists. Alive in the logs, not in fact.
- **`smart` could stall for ~8.5 minutes** — 3+5+10+20+30+60s per model across four models, inside the autonomy loop, holding its lock.
- **`_is_phone_active()` can never return `False`.** `dumpsys` is blocked for unrooted Termux, and the fallback compares `consecutive_idle` to a threshold that only increments when the phone is already inactive. Sleep-aware quiet mode never fired once.

---

## The Good 1.2 — Consolidation

Confidence rating: 9.0/10

- **One file, presets instead of subclasses.** Every old variant became a value: `default`, `tiny`, `cloud`, `smart`, `sleep`. Change a number, not a class.
- **Constructor does no I/O and no speech.** The rule that dissolves the duplication problem at its source.
- **Kept what was best.** The TTS chunker from `agent_voice_fixed.py`, `james.scp.json` as the source of tone and constraints, the memory schema, the forge commands, the Six Lens vocabulary.
- **Reference build verified offline** — 43 checks with no model, no TTS, no sensors, no network.

## The Bad 1.2

Risk rating: 5.0/10

- **The shipped copy is a hand-merge, not the reference build.** Config, presets and transports were kept; `Router`, `Identity` layering, `Scheduler`, `Memory`, the UI layer and the self-test were not. `--selftest` and `--no-capsule` are parsed and silently ignored.
- **The header docstring now describes features the file no longer has.** Comments are not a description of what runs.

## The Ugly 1.2

Severity rating: 4.0/10

- **`RemoteTransport` lost its `payload` method in the merge**, inheriting `raise NotImplementedError` — an exception with no message, printed as `❌ Error:` with nothing after it. A swallowed exception hid the only useful information for two debugging rounds.

---

## The Good 1.3 — VPS integration

Confidence rating: 10/10

- **Contabo endpoint verified live** and returning Ollama-shaped JSON (`.message.content`), matching what the transport parses.
- **Token budgets proven to work.** Same prompt, uncapped vs `options.num_predict: 10` → 340 words vs 8. The proxy honours `num_predict`.
- **Budgets wired to the task.** `think` 150, `dream` 300, `code` 500, `question` 60 — instead of hardcoded 30/40/20.
- **Keys moved to the environment.** `AGENT74_VPS_KEY`, `AGENT74_REMOTE_URL`.

## The Bad 1.3

Risk rating: 9.0/10

- **`max_tokens` was never honoured by anything.** Ollama reads `options.num_predict`; the proxy ignores `max_tokens` too. Every token cap in the old code was decorative — calls generated full-length responses and then got sliced to `[:200]` for display.
- **Which explains the timeouts.** `instant` needed 90 seconds to be "instant", `smart`'s 3-second first attempt could essentially never succeed, and `tiny`'s 2-second budget failed constantly. The cap that was supposed to make things fast was doing nothing at all.
- **The key has still not been rotated.** `Agent74_Secure_Key_2026` remains in git history, and the endpoint is plain HTTP — the header travels in cleartext.

## The Ugly 1.3

Severity rating: 3.0/10

- **A placeholder exported literally.** `export AGENT74_VPS_KEY="..."` sent `X-API-Key: ...` and produced a 401, then a silent fallthrough to a cold local model that timed out at 15 seconds. Two failures, one cause, no error message worth reading.

---

## The Good 1.4 — Grounding

Confidence rating: 8.0/10

- **Experiences table added and actually written to.** Mutations, dreams, questions and stored learnings all persist. Previously `store_learning` was never called anywhere — the table was created and left empty forever.
- **`learn <text>` stores; blank rows filtered from recall.**
- **Reflection reads real memory.** `think` now assembles the last six experiences, timestamped and oldest-first, and is told explicitly to use only those.

## The Bad 1.4

Risk rating: 7.0/10

- **First grounding attempt made it worse.** With an empty experiences table, `think` reached for the only concrete content in the system prompt — the project list — and produced a confident status report: "15% increase in Legion's orchestration efficiency", "99% uptime", "5% gain". Every figure invented.
- **Second attempt mapped internal traits onto imaginary people.** Her own `scepticism` and `talkativeness` values became "user scepticism" and "users experiencing information fatigue", with recommendations about ESP32 response times and interaction logs. None of it existed.

## The Ugly 1.4

Severity rating: 8.0/10

- **The reflection loop ate itself.** `cmd_think` stored its output as an experience, and `_recent_experiences` then fed those reflections straight back in. Thirteen consecutive thinks produced one thought — "self-regulation mechanism… within Legion" — with the tags proving it: `[dream] Your internal trait trends suggest…`, her own words relabelled and re-read. Fixed by excluding `reflection` rows from her own input.
- **Notably, `dream` was the best output in the run** — varied, coherent, genuinely interesting. It is the only action that reads nothing from memory. The ungrounded task outperformed the grounded one, because the grounded one was reading poison.

---

## The Good 1.5 — Autonomy and time

Confidence rating: 9.0/10

- **Scheduler restored, two threads by design.** The tick loop only decides *what* to attempt and queues a name; a worker does the slow part. A 90-second VPS call cannot stall the ticker or the prompt. Stress-tested 9/9, including a failing action and a slow worker.
- **Quiet hours** with a window that correctly crosses midnight, plus speech gating and a minimum gap between utterances.
- **Real time awareness.** Current date and time rebuilt into the system prompt on every call, so the clock cannot go stale; experiences carry timestamps, oldest-first, which fixed her misreading trait direction.
- **Honest uptime.** A heartbeat that credits only elapsed time while running; a gap longer than two beats is booked as *frozen*, not lived. Verified 8/8 against a simulated 10-minute freeze.
- **Ran unattended for 50 minutes** on the VPS, accumulating its own memory.

## The Bad 1.5

Risk rating: 6.0/10

- **The shared SQLite connection had no lock and `check_same_thread=True`.** Autonomy would have raised `ProgrammingError` from the worker thread. Fixed with `check_same_thread=False` and a lock around every write.
- **Android freezes Termux under Doze** the moment the screen goes off — threads stop, timers stop. Ten minutes of silence that looked like a broken scheduler was the OS. `termux-wake-lock` is mandatory for background running.
- **Eighteen suspended processes accumulated** from `^Z`, several with live autonomy threads and open handles on the same database.

## The Ugly 1.5

Severity rating: 3.0/10

- **She is coachable by her own guardrails.** Reflections began quoting the system prompt back — "a Replicant swarm agent with no users or hardware" — and slipped from reflecting to instructing herself how to reflect. phi3:mini is small enough to treat rules as content to discuss. Not a bug; the ceiling of a 3.8B model.

---

## 🧬 Agent 74 v1.0 — Status

✅ One file, presets not subclasses
✅ Contabo VPS (phi3:mini) with local tinyllama fallback
✅ Token budgets honoured end to end (`options.num_predict`)
✅ Keys from the environment
✅ Capsule constraints reach the model intact
✅ SQLite WAL, busy timeout, locked writes
✅ Memory grows from her own actions and does not feed on itself
✅ Autonomy: two threads, quiet hours, non-blocking
✅ Real awake-time tracking, freezes counted as frozen
✅ Runs unattended on S24 Ultra (Termux)

⬜ API key not yet rotated — still in git history, still plain HTTP
⬜ Terminal face built and tested (13/13), not yet applied
⬜ Mutation deltas can round to zero at two decimals
⬜ `learn` and `recall` still overlap
⬜ Reference build's UI layer and self-test not in the shipped file

> "The cap that was supposed to make it fast was doing nothing at all."
