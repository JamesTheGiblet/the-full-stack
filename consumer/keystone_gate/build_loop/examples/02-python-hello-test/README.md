# Example: python-hello-test

Demonstrates unverified steps (spec doc edge case 1) and the `run_test`
action's collapsed action+check form (edge case 2).

## Step 1: write the greet function

No `acceptance` key — this step is intentionally unverified. Writing a
source file has nothing meaningful to check on its own; the check that
matters is step 3, which actually exercises the function.

```step
id: write-hello
action: create_file
target: hello.py
content: |
  def greet(name: str) -> str:
      return f"Hello, {name}!"
description: The function under test.
on_fail: retry_local
```

`on_fail` is still present even though nothing can fail here — the
schema requires it on every step for uniformity (see step-spec.schema.json).
It's dead code in this step and that's expected, not a mistake.

## Step 2: write the test

Also unverified, for the same reason as step 1.

```step
id: write-test
action: create_file
target: test_hello.py
content: |
  from hello import greet

  def test_greet():
      assert greet("World") == "Hello, World!"
description: pytest case for greet().
on_fail: retry_local
```

## Step 3: run the test

This is the one step that actually gates the build. Note there's no
`command` key — for `run_test`, `acceptance.command` doubles as the
action itself, per edge case 2.

```step
id: run-hello-test
action: run_test
acceptance:
  command: pytest test_hello.py -q
  expected_exit_code: 0
description: Verify greet() behaves as specified.
on_fail: retry_local
```

If this fails, `retry_local` means the interpreter hands `hello.py` (or
`test_hello.py`) plus the pytest failure output back to the local model
for up to 2-3 attempts before escalating — not that it re-runs the same
files hoping for a different result.
