"""Tests for interpreter.spec - parsing step-spec READMEs."""

from pathlib import Path

import pytest

from interpreter.spec import StepSpecError, parse_spec

EXAMPLES = Path(__file__).parent.parent / "examples"


def write_readme(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "README.md"
    path.write_text(body, encoding="utf-8")
    return path


def test_parses_hello_npm_example_in_order():
    steps = parse_spec(EXAMPLES / "01-hello-npm" / "README.md")
    assert [s.id for s in steps] == [
        "scaffold-dir",
        "write-gitignore",
        "write-package-json",
        "npm-install",
    ]
    assert steps[0].action == "run_command"
    assert steps[1].template == "text/gitignore_node"
    assert steps[2].template == "npm/package_json"
    assert steps[3].on_fail == "escalate"


def test_parses_python_hello_test_example_unverified_steps():
    steps = parse_spec(EXAMPLES / "02-python-hello-test" / "README.md")
    assert steps[0].acceptance is None
    assert steps[1].acceptance is None
    assert steps[2].action == "run_test"
    assert steps[2].command is None
    assert steps[2].acceptance.command == "pytest test_hello.py -q"


def test_parses_edge_cases_example_including_prose_only_heading():
    steps = parse_spec(EXAMPLES / "03-edge-cases" / "README.md")
    # The "Background" heading has no ```step block and must not appear.
    assert [s.id for s in steps] == [
        "create-config",
        "add-debug-flag",
        "verify-external-constraint",
    ]
    assert steps[1].patch == {"type": "set_json_field", "path": "debug", "value": True}
    assert steps[2].on_fail == "escalate"


def test_heading_with_no_step_block_is_skipped(tmp_path):
    readme = write_readme(
        tmp_path,
        """# Spec

## Just prose, no block here

Nothing to see.

## Step 1: real step

```step
id: only-step
action: run_command
command: "true"
on_fail: retry_local
```
""",
    )
    steps = parse_spec(readme)
    assert [s.id for s in steps] == ["only-step"]


def test_no_step_blocks_returns_empty_list(tmp_path):
    readme = write_readme(tmp_path, "# Just a README\n\nNo steps here at all.\n")
    assert parse_spec(readme) == []


def test_duplicate_id_is_rejected(tmp_path):
    readme = write_readme(
        tmp_path,
        """```step
id: dup
action: run_command
command: "true"
on_fail: retry_local
```

```step
id: dup
action: run_command
command: "true"
on_fail: retry_local
```
""",
    )
    with pytest.raises(StepSpecError, match="duplicate step id"):
        parse_spec(readme)


def test_unknown_action_is_rejected(tmp_path):
    readme = write_readme(
        tmp_path,
        """```step
id: bad
action: teleport_file
on_fail: retry_local
```
""",
    )
    with pytest.raises(StepSpecError, match="unknown action"):
        parse_spec(readme)


def test_run_command_without_command_is_rejected(tmp_path):
    readme = write_readme(
        tmp_path,
        """```step
id: bad
action: run_command
on_fail: retry_local
```
""",
    )
    with pytest.raises(StepSpecError, match="requires a 'command'"):
        parse_spec(readme)


def test_run_test_without_command_or_acceptance_is_rejected(tmp_path):
    readme = write_readme(
        tmp_path,
        """```step
id: bad
action: run_test
on_fail: retry_local
```
""",
    )
    with pytest.raises(StepSpecError, match="run_test needs either"):
        parse_spec(readme)


def test_create_file_with_neither_content_nor_template_is_valid(tmp_path):
    # Deferred to the generative tier (roadmap step 4) - not a parse error.
    readme = write_readme(
        tmp_path,
        """```step
id: needs-generation
action: create_file
target: x.txt
description: something a template can't cover yet
on_fail: retry_local
```
""",
    )
    steps = parse_spec(readme)
    assert steps[0].content is None
    assert steps[0].template is None


def test_create_file_rejects_both_content_and_template(tmp_path):
    both = write_readme(
        tmp_path,
        """```step
id: bad
action: create_file
target: x.txt
content: hi
template: text/gitignore_node
on_fail: retry_local
```
""",
    )
    with pytest.raises(StepSpecError, match="cannot set both 'content' and 'template'"):
        parse_spec(both)


def test_create_file_with_template_parses(tmp_path):
    readme = write_readme(
        tmp_path,
        """```step
id: ok
action: create_file
target: app/package.json
template: npm/package_json
template_params:
  name: hello-app
on_fail: retry_local
```
""",
    )
    steps = parse_spec(readme)
    assert steps[0].template == "npm/package_json"
    assert steps[0].template_params == {"name": "hello-app"}
    assert steps[0].content is None


def test_edit_file_with_neither_content_nor_patch_is_valid(tmp_path):
    # Deferred to the generative tier (roadmap step 4) - not a parse error.
    readme = write_readme(
        tmp_path,
        """```step
id: needs-generation
action: edit_file
target: x.txt
description: an edit no known patch type covers yet
on_fail: retry_local
```
""",
    )
    steps = parse_spec(readme)
    assert steps[0].content is None
    assert steps[0].patch is None


def test_edit_file_rejects_both_content_and_patch(tmp_path):
    both = write_readme(
        tmp_path,
        """```step
id: bad
action: edit_file
target: x.txt
content: do something
patch:
  type: set_json_field
  path: debug
  value: true
on_fail: retry_local
```
""",
    )
    with pytest.raises(StepSpecError, match="cannot set both 'content' and 'patch'"):
        parse_spec(both)


def test_edit_file_patch_requires_type(tmp_path):
    readme = write_readme(
        tmp_path,
        """```step
id: bad
action: edit_file
target: x.txt
patch:
  path: debug
  value: true
on_fail: retry_local
```
""",
    )
    with pytest.raises(StepSpecError, match="'patch' block requires a 'type'"):
        parse_spec(readme)


def test_edit_file_with_patch_parses(tmp_path):
    readme = write_readme(
        tmp_path,
        """```step
id: ok
action: edit_file
target: config.json
patch:
  type: set_json_field
  path: debug
  value: true
on_fail: retry_local
```
""",
    )
    steps = parse_spec(readme)
    assert steps[0].patch == {"type": "set_json_field", "path": "debug", "value": True}
    assert steps[0].content is None


def test_missing_required_field_is_rejected(tmp_path):
    readme = write_readme(
        tmp_path,
        """```step
id: bad
action: run_command
command: "true"
```
""",
    )
    with pytest.raises(StepSpecError, match="missing required field 'on_fail'"):
        parse_spec(readme)
