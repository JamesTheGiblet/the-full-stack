# Build Loop — Step Spec v1

> Phase 0 documentation. No interpreter exists yet. This doc, the schema at
> [`step-spec.schema.json`](./step-spec.schema.json), and the three example
> READMEs under [`../examples/`](../examples/) are the spec the interpreter
> (roadmap step 2) will be built against.

## What this is

Build Loop applies the Keystone Gate pattern — deterministic gate first,
model only at the edges, corrections become capsules — to code generation.
A **step-spec** is an ordered list of build steps. A human authors it by
hand as a plain README.md in the format below; the interpreter walks the
steps in order, executing each deterministically and checking it against
an acceptance test before moving on.

The full step object schema (fields, types, required-ness) lives in
[`step-spec.schema.json`](./step-spec.schema.json) — read that alongside
this doc. This file covers the *authoring format* (how a step object is
written inside a README) and the edge cases the format has to survive.

## Why a README and not raw JSON

The interpreter only reads fenced code blocks tagged `step`; everything
else in the README is prose for the human author and is never parsed.
This means the same file that specifies the build is also its own
documentation — no separate spec/doc pair to keep in sync, which matters
because step-specs are meant to be hand-written and hand-read, not
generated.

## Authoring format

Each step is a level-2 heading followed by a fenced YAML block tagged
`step`:

````markdown
## Step 1: <short title, free text, not parsed>

Optional prose. Ignored by the interpreter — for the human reader only.

```step
id: some-stable-id
action: create_file
target: path/to/file
content: |
  literal file content
description: what this step is for
acceptance:
  command: some check
  expected_exit_code: 0
on_fail: retry_local
```
````

Rules:

- Steps execute in the order their `step` blocks appear in the file,
  top to bottom, regardless of heading text or numbering. Heading numbers
  are for humans; do not rely on them for ordering.
- One `step` block per heading. A heading with no `step` block is pure
  prose (a section intro, a rationale note) and is skipped entirely.
- `id` must be unique within the file and stable across edits that don't
  change the step's meaning — see edge case 5.
- The working directory for the whole spec defaults to the README's own
  directory. `target` on run_command/run_test steps is relative to that,
  not to the previous step's target.
- `step` blocks are parsed as plain YAML, so a `description` or `content`
  value containing `": "` (a colon followed by a space) needs quoting or
  it reads as a nested mapping and fails to parse — e.g.
  `content: 'Add a "debug": true field.'`, not
  `content: Add a "debug": true field.`. This bit the `03-edge-cases`
  example during Phase 0 and is exactly the kind of thing this phase
  exists to catch before the interpreter has to explain it via a stack
  trace.

## Edge cases

These are the things Phase 0 is for surfacing before the interpreter has
to handle them at runtime.

### 1. A step has no acceptance test

Omit the `acceptance` key entirely. The step still runs; the interpreter
treats it as **unverified**: no pass/fail gate, no retry, no escalation —
it logs a warning (`step '<id>' ran unverified`) and moves on. `on_fail`
is required by the schema regardless (for uniformity — every step object
has the same shape), but it is dead: with nothing to fail, it never fires.
Example: [`02-python-hello-test`](../examples/02-python-hello-test/README.md)
step 1 (writing `hello.py`) is unverified; step 2 (running pytest against
it) is what actually gates the build.

Do not use "no acceptance" as a lazy default. A step with no check is a
step the interpreter cannot tell you failed — reserve it for genuinely
unverifiable actions (writing a comment file, `cd`-only setup) not for
skipping the work of writing a real check.

### 2. `run_test` vs `run_command` — where does the command live?

`run_command` steps put their work in `command` and, optionally, a
separate `acceptance.command` to verify it afterward — two different
commands, one action then one check.

`run_test` steps may omit `command` altogether: `acceptance.command` *is*
the action. Running the test suite and checking it passed are the same
operation, so there is no separate "do the thing" step. If a `run_test`
step does set `command`, the interpreter runs `command` first (e.g. to
build fixtures) and only then runs `acceptance.command` — but that's the
exception, not the common case.

### 3. `create_file` targeting a path that already exists

Not covered by the schema — this is an interpreter-level rule, documented
here so it's decided before code exists: `create_file` fails fast if
`target` already exists (it does not silently overwrite). Use `edit_file`
for anything that touches an existing file. This makes `create_file` a
safe, idempotent-to-detect operation: a spec that's already been run
partway can be re-run and will stop at the first step it hasn't done yet,
rather than clobbering work.

### 4. There is no `create_dir` action

Only four actions exist: `create_file`, `edit_file`, `run_command`,
`run_test`. Scaffolding a folder goes through `run_command` (`mkdir -p ...`)
— see [`01-hello-npm`](../examples/01-hello-npm/README.md) step 1 — or is
implied for free when `create_file` writes into a directory that doesn't
exist yet (parent dirs are auto-created). Don't invent a fifth action for
this; it's exactly the kind of scope creep the templated tier (roadmap
step 3) is supposed to absorb as a one-line `mkdir -p` template.

### 5. What identifies a step for the capsule-cache (roadmap step 7)?

The cache key is `id` plus a hash of the failure signature (the acceptance
command's stderr/output, normalised), not a hash of the whole step body.
This means: renaming a step's `id` invalidates its cache entry (correct —
it's now a different step as far as history is concerned), but editing a
step's `description` or prose does not (the id and the failure shape are
what matter, not the wording). This is why `id` stability is a rule in
the authoring format above and not just a convention.

### 6. A step spec with zero steps, or a file with no `step` blocks at all

Valid but a no-op: the interpreter reports "0 steps found" and exits 0.
This is deliberate — it's the same code path as "finished successfully",
not a special error case, so an empty README is not a way to test failure
handling.

## Templated tier

Roadmap step 3. `create_file` and `edit_file` no longer require literal
`content` — a step can instead name a deterministic generator and let the
interpreter fill it in, with no model call:

- `create_file` steps take `template` (a name from
  [`../interpreter/templates.py`](../interpreter/templates.py)) +
  `template_params`, as an alternative to `content`. Setting both is a
  spec error caught at parse time (ambiguous — which one wins?). Setting
  neither is valid: it means no template matches this step, so it falls
  through to the generative tier (roadmap step 4) at execution time —
  today that's just a clear "not available yet" error, since step 4
  doesn't exist.
- `edit_file` steps take `patch` (`{type: <name>, ...params}`, matched
  against [`../interpreter/patches.py`](../interpreter/patches.py)), as
  an alternative to `content`. Same rule: both is a parse-time error,
  neither defers to the generative tier.

Both registries are plain Python dicts of pure functions —
`params -> content` for templates, `(text, params) -> new_text` for
patches. Adding a new one is adding a function, not touching the
interpreter's control flow.

### Edge case 7: unknown template/patch names fail at execution, not parse time

Whether `content`/`template` (or `content`/`patch`) is present is a
structural check spec.py can do without knowing what templates exist.
Whether the *named* template or patch type is actually registered can
only be checked once the interpreter is running, the same way a bad
`target` directory only surfaces at execution. The error names the
unknown name and lists what *is* available, so this isn't a bare
`KeyError`.

### What this tier does and doesn't absorb

`01-hello-npm`'s `write-package-json` step and `03-edge-cases`'s
`add-debug-flag` step both moved from literal `content` to
`template`/`patch` once this tier existed — see those examples. Two
things did **not** move, deliberately:

- `02-python-hello-test`'s `hello.py`/`test_hello.py` content stayed
  literal. A greet function's body is specific logic, not boilerplate —
  forcing it through a template would just be hiding a hardcoded string
  behind an extra layer.
- `03-edge-cases`'s free-text edit instructions still hit the
  `edit_file` wall (`"needs the generative tier"`) whenever they don't
  match a registered `patch` type. The templated tier only covers
  *known* patterns; that's the whole design point of measuring what
  fraction of real steps need generation before building it (roadmap
  step 4).

### What fraction of steps actually need generation?

Roadmap step 3 asked for this measurement before step 4 gets built.
Across the three examples' 6 content-bearing steps (`create_file`/
`edit_file` steps that write or change something, as opposed to
`run_command`/`run_test`):

| Source | Count | Steps |
| --- | --- | --- |
| Templated (`template`) | 2 | `write-gitignore`, `write-package-json` |
| Patched (`patch`) | 1 | `add-debug-flag` |
| Literal, hand-written `content` | 3 | `create-config`, `write-hello`, `write-test` |
| **Needs the generative tier** | **0** | — |

Read that zero as a sample-size artefact, not a result: n=6, hand-picked,
and one of the three "literal" steps (`add-debug-flag`'s predecessor)
only became patchable *because* this phase built a patch for it. The
honest takeaway isn't "the generative tier is unnecessary" — it's that
this sample is too small and too curated to say. What it does show:
free-text `edit_file` instructions still hit the generative-tier wall
whenever they don't match a registered `patch` type, and `create_file`
steps with neither `content` nor `template` do the same (see the
executor tests for both). Real measurement needs specs nobody wrote to
prove a point.

## Freezing into an sc capsule

Once a step-spec README is stable, it gets wrapped the same way any other
Forge Stack doc does: a capsule under `sc/` whose
`declaration.parameters.document` points at the README and whose
`document_sha256` is filled in by `freeze.py`. See
[`../sc/step-spec-v1.sc.json`](../sc/step-spec-v1.sc.json) for the capsule
wrapping *this* doc, and note that individual example READMEs are not
capsuled themselves yet — that happens when the interpreter (roadmap step
2) actually starts consuming them and lineage tracking becomes relevant,
not before.
