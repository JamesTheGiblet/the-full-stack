# **CHANGELOG.md**

> **Header Note:** This changelog documents an AI-assisted build — architecture, decisions, and verification are James's; implementation velocity comes from working alongside AI. Entries run oldest-first, version-ordered. Ordering is authoritative over any individual timestamp. This is an append-only file — once written, entries are never edited. Corrections are new entries.

---

## **2026-08-28 — v0.5.0 — Build Loop: Templated Tier**

## The Good (Confidence: 9)

- **`create_file`/`edit_file` can now be pure substitution.** `interpreter/templates.py` (a registry of `params -> content` functions: `npm/package_json`, `text/gitignore_node`) and `interpreter/patches.py` (a registry of `(text, params) -> new_text` functions: `set_json_field`, supporting dotted key paths) let a step name a known pattern instead of hardcoding content — still zero model calls.
- **`03-edge-cases`'s `edit_file` step went from "always errors" to actually passing.** Before this tier existed, any `edit_file` step with free-text `content` hit a hard "needs the generative tier" wall — there was nothing else it could do. Its `add-debug-flag` step now uses `patch: {type: set_json_field, ...}` and the whole three-step example runs end to end for the first time.
- **`01-hello-npm`'s `write-package-json` step moved from a hardcoded literal to `template: npm/package_json`**, plus a new `write-gitignore` step proving a second, parameterless template. Re-ran both examples for real in a scratch dir after the change — 4/4 and 3/3 steps pass.
- **Measured the fraction of steps needing generation, as the roadmap asked for**: across the three examples' 6 content-bearing steps, 0 currently hit the generative-tier wall — reported honestly in `step-spec.md` as a sample-size artefact (n=6, hand-picked), not evidence the generative tier is unnecessary.
- **47 unit tests, all passing** — 26 new ones covering the template/patch registries and the parser's content/template and content/patch exclusivity rules.

## The Bad (Risk: 2)

- **A real design bug caught mid-implementation, not after.** The first cut of the exclusivity rule required *exactly one* of `content`/`template` (and `content`/`patch`), which silently closed off the "neither is set, defer to the generative tier" case roadmap step 4 depends on — `create_file` could never have reached the generative tier at all under that rule. Caught by re-reading the validation against the roadmap before moving on, not by a test failing; fixed to "at most one; both is a parse error; neither is valid and defers." Recorded here because it's the kind of bug that would have been invisible until step 4 tried to use it.
- **Only two templates and one patch type exist.** Enough to prove the tier works and to convert the two examples that had genuine boilerplate; real coverage numbers need more real specs, not more templates written speculatively.

## The Ugly (Severity: 1)

- **None.** Clean addition on top of the v0.4.0 interpreter; no schema fields removed, only extended.

---

## **2026-08-28 — v0.4.0 — Build Loop: Deterministic Interpreter**

## The Good (Confidence: 9.1)

- **Step-walker implemented.** `build_loop/interpreter/` (`spec.py` parser, `executor.py` executor, `cli.py`/`__main__.py` entry point) reads a step-spec README and executes `create_file` / `edit_file` / `run_command` / `run_test` steps in order, checking each against its acceptance test. No model calls anywhere in this path, as planned — this is the known-good baseline the templated and generative tiers (roadmap steps 3-4) get built on top of.
- **21 unit tests, all passing**, covering the parser's validation rules and the executor's action/acceptance/unverified-step behaviour.
- **Proved end-to-end, not just unit-tested.** Ran the interpreter for real against both example READMEs in a scratch working directory — `01-hello-npm` (mkdir → write `package.json` → real `npm install`) and `02-python-hello-test` (two unverified writes → a real `pytest` gate) — both completed 3/3 steps.
- **Two real bugs caught by actually running the examples**, not by reasoning about them: an unquoted YAML colon in `03-edge-cases`'s `content` field broke the parser (fixed, and turned into a documented quoting rule in `step-spec.md` so the next author doesn't hit it blind); `01-hello-npm`'s acceptance check assumed `npm install` creates `node_modules/`, which modern npm (v11+) doesn't do for a package with zero declared dependencies (fixed to check `package-lock.json` instead). Both are exactly the class of thing the "prove it end-to-end before adding AI" step was for.

## The Bad (Risk: 2.1)

- **`edit_file` is a hard stop for anything but a unified diff.** A free-text edit instruction raises `StepExecutionError` explaining it needs the generative tier — correct for this phase, but it means no example spec can exercise `edit_file` end-to-end yet.
- **`on_fail` is recorded, not acted on.** Both `retry_local` and `escalate` currently just stop the run with a log line naming which one would fire — the retry loop and the escalation path are roadmap steps 5 and 6.

## The Ugly (Severity: 1.1)

- **PyYAML added as a dependency** (`build_loop/requirements.txt`) to parse the step blocks. A deliberate, minimal addition — not a departure from the "rule-based, no AI in the loop" intent, just a parsing library.

---

## **2026-08-28 — v0.3.0 — Build Loop: Step-Spec Schema (Phase 0)**

**The Good (Confidence: 9)**

- **Schema defined before any interpreter code existed.** `build_loop/docs/step-spec.schema.json` formalises a single step object (`id`, `action`, `target`, `acceptance`, `on_fail`, plus `content`/`command`/`description` — see "The Bad"); `build_loop/docs/step-spec.md` documents the hand-authored README format (fenced ` ```step ` YAML blocks under headings) and six edge cases surfaced by writing real examples: unverified steps, `run_test`'s collapsed action+check form, `create_file` failing fast on an existing target, no `create_dir` action, the cache key for the future fix-cache (roadmap step 7), and empty specs being a no-op rather than an error.
- **Three example READMEs hand-written in the format** before any code had to parse them: `01-hello-npm` (the trivial scaffold+package.json+install case), `02-python-hello-test` (unverified writes + a real pytest gate), `03-edge-cases` (edit_file, a deliberate `escalate`, an id-stability note, a prose-only heading with no step block).
- **Wrapped as an sc capsule** (`build_loop/sc/step-spec-v1.sc.json`), inheriting `forge-stack/governance-v6`, following the same document-pointer pattern as `gate-pattern-v1.sc.json` and `leighton-weight-v1.sc.json` rather than inventing a new capsule shape.
- **Built inside `keystone_gate/` rather than as a new consumer** — a deliberate scoping call: Build Loop reuses Keystone's capsule and cache machinery for code fixes specifically, instead of fragmenting into a 21st project.

**The Bad (Risk: 2)**

- **Schema grew beyond the original four fields.** `action`/`target`/`acceptance`/`on_fail` alone can't describe what to write or run, so `content`, `command`, and `description` were added to make the schema executable. Flagged for review at the time; not yet explicitly confirmed.
- **Capsule is unsigned and unfrozen.** `document_sha256` is still `COMPUTE-ON-FREEZE` — needs `freeze.py` then `sign.py` before it's a real, pinned capsule rather than a draft.

**The Ugly (Severity: 1)**

- **A necessary discovery pass.** The edge cases this phase surfaced (including the YAML-quoting gotcha found later, in v0.4.0) are exactly what Phase 0 documentation is for — better to hit them writing a README by hand than debugging a stack trace from the interpreter.

---

## **2026-08-10 — v0.2.1 — Test Refactoring**

**The Good (Confidence: 10)**

- **Test fixtures refactored.** The duplicated `pytest` setup from `test_core.py` and `test_mutation.py` has been moved into a shared `tests/conftest.py` file, creating a single source of truth for test setup.
- **Improved maintainability.** This resolves the "Ugly" point from the `v0.2.0` entry, making the test suite cleaner, more robust, and easier to maintain.

**The Bad (Risk: 1)**

- **No new test coverage.** This was a refactoring pass only; no new tests were added.

**The Ugly (Severity: 1)**

- **A necessary cleanup.** This pass addresses technical debt introduced during the initial implementation, which is a healthy and essential part of the development cycle.

---

## **2026-08-10 — v0.2.0 — Initial Implementation & Test Suite**

**The Good (Confidence: 9)**

- **Core classes implemented.** Drafted initial Python implementations for `KeystoneGate` (in `core.py`), `PrimitiveManager` (in `primitives.py`), and `MutationEngine` (in `mutation.py`).
- **File structure established.** Created the full directory structure, including placeholder data files and `__init__.py` files, matching the `README.md`.
- **Basic test suite added.** Created initial `pytest` files (`tests/test_core.py`, `tests/test_mutation.py`) to verify the basic functionality of the core classes and mutation placeholders.
- **Architectural consistency.** The initial code correctly reflects the architecture, responsibilities, and interactions described in the `v0.1.0` documentation.

**The Bad (Risk: 3)**

- **Placeholder logic.** Core functionality, such as semantic similarity in `core.py` and all operators in `mutation.py`, are currently placeholders and do not perform their real tasks.
- **CLI not implemented.** The `cli.py` file remains a placeholder with no command-line functionality.

**The Ugly (Severity: 2)**

- **Duplicated test setup.** The `pytest` setup logic is duplicated across `test_core.py` and `test_mutation.py`. This should be refactored into a shared `conftest.py` to improve test maintainability.

---

## **2026-08-10 — v0.1.0 — Initial Documentation**

**The Good (Confidence: 10)**

- **Initial documentation created.** Drafted and added `README.md` for the `keystone_gate` consumer, establishing its purpose, scope, and integration with the Forge Stack.
- **Strong architectural alignment.** The documentation correctly positions Keystone Gate as a consumer, details its use of core stack tools (`freeze.py`, `ledger.py`, etc.), and adheres to the established conventions for consumer-scoped ledgers.

**The Bad (Risk: 1)**

- **Implementation is pending.** The `README.md` describes a fully-featured system, but the implementation itself is not yet present. This changelog entry marks the creation of the documentation only.

**The Ugly (Severity: 1)**

- **A clean start.** This placeholder establishes a clear and accurate starting point for the consumer's development history.
