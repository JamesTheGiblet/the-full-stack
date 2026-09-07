"""Tests for interpreter.patches - the templated tier's known-pattern edits."""

import json

import pytest

from interpreter import patches


def test_set_json_field_top_level():
    out = patches.apply("set_json_field", '{"mode": "dev"}', {"path": "debug", "value": True})
    assert json.loads(out) == {"mode": "dev", "debug": True}


def test_set_json_field_nested_dot_path_creates_intermediate_objects():
    out = patches.apply("set_json_field", "{}", {"path": "a.b.c", "value": 1})
    assert json.loads(out) == {"a": {"b": {"c": 1}}}


def test_set_json_field_overwrites_existing_value():
    out = patches.apply("set_json_field", '{"mode": "dev"}', {"path": "mode", "value": "prod"})
    assert json.loads(out) == {"mode": "prod"}


def test_set_json_field_requires_path_and_value():
    with pytest.raises(ValueError, match="requires 'path' and 'value'"):
        patches.apply("set_json_field", "{}", {"path": "debug"})


def test_set_json_field_rejects_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        patches.apply("set_json_field", "not json", {"path": "debug", "value": True})


def test_unknown_patch_type_raises_key_error():
    with pytest.raises(KeyError):
        patches.apply("does-not-exist", "{}", {})


def test_available_lists_registered_patches():
    assert patches.available() == ["set_json_field"]
