"""Tests for interpreter.templates - the templated tier's content generators."""

import json

import pytest

from interpreter import templates


def test_npm_package_json_minimal():
    out = templates.render("npm/package_json", {"name": "hello-app"})
    data = json.loads(out)
    assert data == {"name": "hello-app", "version": "1.0.0", "private": True}


def test_npm_package_json_with_overrides():
    out = templates.render(
        "npm/package_json",
        {"name": "hello-app", "version": "2.0.0", "private": False, "description": "demo"},
    )
    data = json.loads(out)
    assert data["version"] == "2.0.0"
    assert "private" not in data
    assert data["description"] == "demo"


def test_npm_package_json_requires_name():
    with pytest.raises(ValueError, match="requires a 'name'"):
        templates.render("npm/package_json", {})


def test_gitignore_node_is_parameterless_and_deterministic():
    assert templates.render("text/gitignore_node", {}) == templates.render("text/gitignore_node", {})
    assert "node_modules/" in templates.render("text/gitignore_node", {})


def test_unknown_template_raises_key_error():
    with pytest.raises(KeyError):
        templates.render("does/not-exist", {})


def test_available_lists_registered_templates():
    names = templates.available()
    assert "npm/package_json" in names
    assert "text/gitignore_node" in names
    assert names == sorted(names)
