"""
conftest.py - Shared fixtures for the Keystone Gate test suite.
"""

import pytest
from pathlib import Path

from keystone_gate.core import KeystoneGate


@pytest.fixture
def gate(tmp_path: Path) -> KeystoneGate:
    """
    Provides a KeystoneGate instance initialized with temporary files.
    """
    primitives_file = tmp_path / "primitives.json"
    cache_file = tmp_path / "cache.json"

    gate_instance = KeystoneGate(primitive_file=primitives_file, cache_file=cache_file)
    return gate_instance