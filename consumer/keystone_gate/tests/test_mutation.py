"""
test_mutation.py - Tests for the MutationEngine's semantic operators.
"""

import pytest
from pathlib import Path

from keystone_gate.core import KeystoneGate
from keystone_gate.primitives import PrimitiveManager
from keystone_gate.mutation import MutationEngine


def get_capsule_1():
    """Returns the first sample source capsule."""
    return {
        "scp_id": "keystone/source-1",
        "scp_version": "1.0.0",
        "created": "2026-08-10T11:00:00Z",
        "declaration": {
            "intent": "First source capsule.",
            "parameters": {"difficulty": "easy", "value": 100},
        },
    }


def get_capsule_2():
    """Returns the second sample source capsule."""
    return {
        "scp_id": "keystone/source-2",
        "scp_version": "1.0.0",
        "created": "2026-08-10T12:00:00Z",
        "declaration": {
            "intent": "Second source capsule.",
            "parameters": {"phases": ["a", "b"]},
        },
    }


@pytest.fixture
def mutation_test_setup(gate: KeystoneGate) -> MutationEngine:
    """
    A pytest fixture to initialize the MutationEngine and pre-populate the
    capsule cache with two source capsules for mutation tests.
    """
    # Manually add capsules to the gate's cache for the test
    cap1 = get_capsule_1()
    cap2 = get_capsule_2()
    gate.capsule_cache[cap1['scp_id']] = {"capsule": cap1, "metadata": {}}
    gate.capsule_cache[cap2['scp_id']] = {"capsule": cap2, "metadata": {}}
    gate._save_cache()

    mutator = MutationEngine(gate, gate.primitive_manager)
    return mutator


def test_mutate_merge(mutation_test_setup):
    """Tests the placeholder 'merge' operation."""
    mutator = mutation_test_setup
    new_capsule = mutator.mutate(
        source_ids=["keystone/source-1", "keystone/source-2"],
        operation="merge"
    )

    assert new_capsule["scp_id"].startswith("keystone/mutated/merge-")
    assert new_capsule["inherits"] == ["keystone/source-1", "keystone/source-2"]
    # Placeholder logic copies the first capsule's declaration
    assert new_capsule["declaration"]["parameters"]["difficulty"] == "easy"
    assert "phases" not in new_capsule["declaration"]["parameters"]


def test_mutate_evolve(mutation_test_setup):
    """Tests the placeholder 'evolve' operation."""
    mutator = mutation_test_setup
    new_capsule = mutator.mutate(
        source_ids=["keystone/source-1"],
        operation="evolve"
    )

    assert new_capsule["scp_id"].startswith("keystone/mutated/evolve-")
    assert new_capsule["inherits"] == ["keystone/source-1"]
    # Placeholder logic adds a specific new field
    assert new_capsule["declaration"]["newly_evolved_field"] == "placeholder_value"


def test_mutate_optimise(mutation_test_setup):
    """Tests the placeholder 'optimise' operation."""
    mutator = mutation_test_setup
    new_capsule = mutator.mutate(
        source_ids=["keystone/source-2"],
        operation="optimise"
    )

    assert new_capsule["scp_id"].startswith("keystone/mutated/optimise-")
    assert new_capsule["inherits"] == ["keystone/source-2"]
    # Placeholder logic removes the 'parameters' field
    assert "parameters" not in new_capsule["declaration"]


def test_mutate_unknown_source(mutation_test_setup):
    """Tests that mutation fails if a source capsule ID is not found."""
    mutator = mutation_test_setup
    with pytest.raises(ValueError, match="Source capsule\\(s\\) not found in cache"):
        mutator.mutate(source_ids=["unknown-id"], operation="merge")