"""Tests for interpreter.executor - the deterministic step-walker."""

from pathlib import Path

from interpreter.executor import run_spec
from interpreter.spec import Acceptance, Step


def make_step(**overrides) -> Step:
    defaults = dict(id="step", action="run_command", on_fail="retry_local")
    defaults.update(overrides)
    return Step(**defaults)


def test_create_file_writes_content(tmp_path: Path):
    step = make_step(action="create_file", target="hello.txt", content="hi\n")
    results = run_spec([step], tmp_path)
    assert results[0].ok
    assert (tmp_path / "hello.txt").read_text(encoding="utf-8") == "hi\n"


def test_create_file_auto_creates_parent_dirs(tmp_path: Path):
    step = make_step(action="create_file", target="nested/dir/hello.txt", content="hi\n")
    results = run_spec([step], tmp_path)
    assert results[0].ok
    assert (tmp_path / "nested" / "dir" / "hello.txt").exists()


def test_create_file_fails_fast_on_existing_target(tmp_path: Path):
    (tmp_path / "hello.txt").write_text("already here", encoding="utf-8")
    step = make_step(action="create_file", target="hello.txt", content="hi\n")
    results = run_spec([step], tmp_path)
    assert not results[0].ok
    assert "already exists" in results[0].error
    # And the original content must survive - no silent overwrite.
    assert (tmp_path / "hello.txt").read_text(encoding="utf-8") == "already here"


def test_step_with_no_acceptance_is_unverified_and_run_continues(tmp_path: Path):
    unverified = make_step(id="write", action="create_file", target="a.txt", content="x")
    verified = make_step(
        id="check",
        action="run_command",
        command="echo done",
        acceptance=Acceptance(command="echo done", expected_exit_code=0),
    )
    results = run_spec([unverified, verified], tmp_path)
    assert results[0].unverified
    assert results[0].ok
    assert results[1].ok
    assert not results[1].unverified


def test_acceptance_pass(tmp_path: Path):
    step = make_step(
        action="run_command",
        command="echo hello",
        acceptance=Acceptance(command="echo hello", expected_exit_code=0, expected_output_pattern="hel+o"),
    )
    results = run_spec([step], tmp_path)
    assert results[0].ok
    assert results[0].acceptance.passed


def test_acceptance_exit_code_mismatch_stops_the_run(tmp_path: Path):
    steps = [
        make_step(
            id="fails",
            action="run_command",
            command="echo nope",
            acceptance=Acceptance(command="exit 1"),
        ),
        make_step(id="never-runs", action="run_command", command="echo should-not-run"),
    ]
    results = run_spec(steps, tmp_path)
    assert len(results) == 1
    assert not results[0].ok
    assert "exit code" in results[0].acceptance.reason


def test_acceptance_output_pattern_mismatch_fails(tmp_path: Path):
    step = make_step(
        action="run_command",
        command="echo hello",
        acceptance=Acceptance(command="echo hello", expected_output_pattern="goodbye"),
    )
    results = run_spec([step], tmp_path)
    assert not results[0].ok
    assert "did not match pattern" in results[0].acceptance.reason


def test_run_test_with_no_command_uses_acceptance_as_the_action(tmp_path: Path):
    step = make_step(
        action="run_test",
        acceptance=Acceptance(command="echo ran-the-test", expected_output_pattern="ran-the-test"),
    )
    results = run_spec([step], tmp_path)
    assert results[0].ok


def test_run_command_action_failure_stops_before_later_steps(tmp_path: Path):
    steps = [
        make_step(id="boom", action="run_command", command="exit 3"),
        make_step(id="never-runs", action="run_command", command="echo nope"),
    ]
    results = run_spec(steps, tmp_path)
    assert len(results) == 1
    assert not results[0].ok
    assert "command failed" in results[0].error


def test_edit_file_free_text_is_rejected_until_generative_tier_exists(tmp_path: Path):
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    step = make_step(action="edit_file", target="config.json", content="add a debug flag")
    results = run_spec([step], tmp_path)
    assert not results[0].ok
    assert "generative tier" in results[0].error


def test_create_file_from_template(tmp_path: Path):
    step = make_step(
        action="create_file",
        target="app/package.json",
        template="npm/package_json",
        template_params={"name": "hello-app"},
    )
    results = run_spec([step], tmp_path)
    assert results[0].ok
    assert '"hello-app"' in (tmp_path / "app" / "package.json").read_text(encoding="utf-8")


def test_create_file_with_neither_content_nor_template_defers_to_generative_tier(tmp_path: Path):
    step = make_step(action="create_file", target="x.txt")
    results = run_spec([step], tmp_path)
    assert not results[0].ok
    assert "generative tier" in results[0].error


def test_create_file_unknown_template_fails_clearly(tmp_path: Path):
    step = make_step(action="create_file", target="x.txt", template="does/not-exist")
    results = run_spec([step], tmp_path)
    assert not results[0].ok
    assert "unknown template" in results[0].error


def test_edit_file_via_known_patch(tmp_path: Path):
    (tmp_path / "config.json").write_text('{"mode": "dev"}', encoding="utf-8")
    step = make_step(
        action="edit_file",
        target="config.json",
        patch={"type": "set_json_field", "path": "debug", "value": True},
    )
    results = run_spec([step], tmp_path)
    assert results[0].ok
    assert "true" in (tmp_path / "config.json").read_text(encoding="utf-8").lower()


def test_edit_file_with_neither_content_nor_patch_defers_to_generative_tier(tmp_path: Path):
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    step = make_step(action="edit_file", target="config.json")
    results = run_spec([step], tmp_path)
    assert not results[0].ok
    assert "generative tier" in results[0].error


def test_edit_file_unknown_patch_type_fails_clearly(tmp_path: Path):
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    step = make_step(action="edit_file", target="config.json", patch={"type": "does-not-exist"})
    results = run_spec([step], tmp_path)
    assert not results[0].ok
    assert "unknown patch type" in results[0].error


def test_run_command_target_is_working_directory(tmp_path: Path):
    (tmp_path / "app").mkdir()
    # A relative redirect proves *where* the command actually ran: it only
    # lands in tmp_path/app/marker.txt if cwd was resolved from `target`.
    step = make_step(action="run_command", target="app", command="echo hi > marker.txt")
    results = run_spec([step], tmp_path)
    assert results[0].ok
    assert (tmp_path / "app" / "marker.txt").exists()
    assert not (tmp_path / "marker.txt").exists()
