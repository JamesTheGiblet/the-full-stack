# Example: hello-npm

The trivial case from the roadmap — scaffold a folder, write a
`package.json`, run `npm install` — used to prove the interpreter end to
end before anything AI-shaped exists. See
[`../../docs/step-spec.md`](../../docs/step-spec.md) for the format this
file is written in.

## Step 1: scaffold the app folder

There's no `create_dir` action (edge case 4 in the spec doc), so this
goes through `run_command`.

```step
id: scaffold-dir
action: run_command
command: mkdir -p app
description: Create the app/ directory the rest of the steps write into.
acceptance:
  command: test -d app
  expected_exit_code: 0
on_fail: retry_local
```

## Step 2: write .gitignore

Templated tier (roadmap step 3): a fixed, parameterless generator, no
model call. See
[`../../docs/step-spec.md`](../../docs/step-spec.md#templated-tier) and
[`../../interpreter/templates.py`](../../interpreter/templates.py).

```step
id: write-gitignore
action: create_file
target: app/.gitignore
template: text/gitignore_node
description: Standard Node ignores for the scaffolded app.
acceptance:
  command: test -f app/.gitignore
  expected_exit_code: 0
on_fail: retry_local
```

## Step 3: write package.json

Also templated — `npm/package_json` takes the same shape this step used
to hardcode as literal `content`, but as reusable, parameterised
substitution instead of a one-off string.

```step
id: write-package-json
action: create_file
target: app/package.json
template: npm/package_json
template_params:
  name: hello-app
  version: "1.0.0"
description: Minimal package.json identifying the app.
acceptance:
  command: node -p "require('./app/package.json').name"
  expected_exit_code: 0
  expected_output_pattern: "hello-app"
on_fail: retry_local
```

## Step 4: install dependencies

No dependencies are declared, so this mostly proves the interpreter can
shell out and check the result. It does *not* prove `node_modules/`
exists — modern npm (v11+) doesn't create one for a package with zero
declared dependencies, only `package-lock.json`. That surfaced by
actually running this example during Phase 0, which is the example
doing its job: `package-lock.json` is the acceptance check because it's
what npm install reliably produces, not because it "sounds right."

```step
id: npm-install
action: run_command
target: app
command: npm install
description: Install dependencies for the scaffolded app.
acceptance:
  command: test -f app/package-lock.json
  expected_exit_code: 0
on_fail: escalate
```

`npm-install` escalates straight away instead of retrying locally: a
failed `npm install` is almost always an environment problem (missing
npm, no network, a registry outage), not something a local model
regenerating code can fix by trying again.
