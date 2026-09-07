# Example: edge-cases

Not a build anyone would actually run — a deliberately small spec that
exercises the corners of the format so they're visible on paper before
the interpreter has to handle them at runtime.

## Background

This heading has no `step` block, so the interpreter skips it entirely
(spec doc edge case 6, extended: not every heading is a step, only ones
followed by a fenced `step` block are). It exists purely so this example
also proves prose-only sections don't confuse the step walker.

## Step 1: create the config file

```step
id: create-config
action: create_file
target: config.json
content: |
  {"mode": "dev"}
description: Base config, will be edited in step 2.
acceptance:
  command: test -f config.json
  expected_exit_code: 0
on_fail: retry_local
```

Re-running this spec after step 1 has already succeeded once is safe:
`create_file` fails fast on a target that already exists (edge case 3),
so a partial re-run stops here instead of silently overwriting
`config.json` with the templated content again.

## Step 2: edit the config file to add a field

`edit_file` targets the same file `create-config` just wrote. This used
to be a free-text instruction (`content: 'Add a "debug": true field...'`)
that always failed with "needs the generative tier" — there was no
templated tier yet to catch it. Now that `patch` exists (roadmap step 3),
"set a JSON field" is a known pattern
([`set_json_field`](../../interpreter/patches.py)), so this step runs
deterministically instead of hitting that wall.

```step
id: add-debug-flag
action: edit_file
target: config.json
patch:
  type: set_json_field
  path: debug
  value: true
description: Turn on debug mode for local runs.
acceptance:
  command: node -p "require('./config.json').debug"
  expected_exit_code: 0
  expected_output_pattern: "true"
on_fail: retry_local
```

## Step 3: a check that documents the escalate path

`set_json_field` only touches `debug`, so `mode` survives untouched and
this step passes — the point isn't to fail, it's to show `on_fail:
escalate` in a real step. Escalate is for acceptance tests that encode a
constraint no amount of local retrying can discover on its own — e.g. a
build flag that has to match a value from outside this spec — so it
skips local retries entirely rather than burning the retry cap on
something a smaller model has no way to converge on. (To see it actually
fire, break `set_json_field`'s output, e.g. by pointing `path` at
`mode` with a value that isn't `"dev"`.)

```step
id: verify-external-constraint
action: run_command
command: node -p "require('./config.json').mode"
description: Confirm mode wasn't clobbered by the edit in step 2.
acceptance:
  command: node -p "require('./config.json').mode"
  expected_exit_code: 0
  expected_output_pattern: "dev"
on_fail: escalate
```

## A note on `id` stability

If step 2's `id` were renamed from `add-debug-flag` to something else
after a failed run, roadmap step 7's capsule-cache would treat the retry
as a brand-new step with no history, rather than a known failure with an
existing fix. Renaming an `id` is a deliberate cache invalidation, not a
free-form edit — see spec doc edge case 5.
