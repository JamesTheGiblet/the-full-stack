"""
test_core.py - Tests for the main KeystoneGate processing logic.
"""

import json
from pathlib import Path

from keystone_gate.core import KeystoneGate


def get_sample_capsule():
    """Returns a valid sample capsule dictionary for testing."""
    return {
        "scp_id": "keystone/test-v1",
        "scp_version": "1.0.0",
        "created": "2026-08-10T10:00:00Z",
        "declaration": {
            "intent": "A test capsule for verification.",
            "parameters": {"mode": "test", "value": 42},
        },
    }


def test_process_approved_capsule(gate: KeystoneGate):
    """
    Tests that a valid capsule is processed, approved, and cached correctly.
    """
    capsule_data = get_sample_capsule()
    result = gate.process(capsule_data)

    # 1. Check the result status and content
    assert result["status"] == "approved"
    assert "confidence_score" in result
    assert "new_fields" in result
    assert len(result["new_fields"]) > 0
    assert result["capsule"] == capsule_data

    # 2. Verify that the primitives file was created and populated
    assert gate.primitive_manager.primitive_file.exists()
    primitives = json.loads(gate.primitive_manager.primitive_file.read_text())
    assert "declaration.intent" in primitives
    assert primitives["declaration.intent"]["count"] == 1

    # 3. Verify that the cache file was created and populated
    assert gate.cache_file.exists()
    cache = json.loads(gate.cache_file.read_text())
    assert "keystone/test-v1" in cache
    assert cache["keystone/test-v1"]["capsule"]["scp_id"] == "keystone/test-v1"


def test_process_rejected_capsule(gate: KeystoneGate):
    """
    Tests that a capsule missing required fields is correctly rejected.
    """
    # Create an invalid capsule missing the 'created' field
    invalid_capsule = get_sample_capsule()
    del invalid_capsule["created"]

    result = gate.process(invalid_capsule)

    assert result["status"] == "rejected"
    assert "errors" in result
    assert "Missing required SCP field: 'created'" in result["errors"]
