"""
mutation.py - The intelligent semantic operator engine for Keystone Gate.

This module defines the MutationEngine, which provides a set of operators
to intelligently evolve, merge, and transform semantic capsules based on the
collective vocabulary managed by the PrimitiveManager.
"""

import copy
import uuid
from typing import Any, Dict, List, Literal, Optional

from .core import KeystoneGate
from .primitives import PrimitiveManager

# Define the set of valid mutation operations from the README.
Operation = Literal["merge", "extend", "invert", "substitute", "evolve", "optimise"]


class MutationEngine:
    """
    Performs intelligent semantic mutations on capsules.

    This engine uses the vocabulary and statistics from the PrimitiveManager
    and the approved capsules from the KeystoneGate's cache to perform
    operations like merging, evolving, and optimising capsules.
    """

    def __init__(self, gate: KeystoneGate, primitive_manager: PrimitiveManager):
        """
        Initializes the MutationEngine.

        Args:
            gate: An instance of the main KeystoneGate.
            primitive_manager: An instance of the PrimitiveManager.
        """
        self.gate = gate
        self.primitive_manager = primitive_manager
        # Direct access to the cache for retrieving source capsules.
        self.capsule_cache = gate.capsule_cache

    def _get_capsule_by_id(self, scp_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a deep copy of a capsule's data from the cache by its ID."""
        cached_item = self.capsule_cache.get(scp_id)
        return copy.deepcopy(cached_item.get("capsule")) if cached_item else None

    def _create_new_capsule_shell(self, source_ids: List[str], operation: str) -> Dict[str, Any]:
        """Creates a new capsule shell for the mutation result."""
        from datetime import datetime, timezone
        new_id_suffix = uuid.uuid4().hex[:12]
        new_id = f"keystone/mutated/{operation}-{new_id_suffix}-v1"
        return {
            "scp_id": new_id,
            "scp_version": "1.0.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "inherits": source_ids,
            "declaration": {
                "intent": f"Result of '{operation}' mutation on {', '.join(source_ids)}",
            },
        }

    def _merge(self, capsules: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Placeholder for merging multiple capsules."""
        print(f"Merging {len(capsules)} capsules with kwargs: {kwargs}")
        # A real implementation would intelligently combine fields.
        # For this placeholder, we'll just take the first capsule's declaration.
        new_capsule = self._create_new_capsule_shell([c['scp_id'] for c in capsules], "merge")
        if capsules:
            new_capsule["declaration"] = copy.deepcopy(capsules[0].get("declaration", {}))
            new_capsule["declaration"]["intent"] = f"Merged content from {len(capsules)} capsules."
        return new_capsule

    def _evolve(self, capsules: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Placeholder for evolving a capsule by adding new fields."""
        print(f"Evolving {len(capsules)} capsule(s) with kwargs: {kwargs}")
        # A real implementation would add missing fields from the primitive pool.
        new_capsule = self._create_new_capsule_shell([c['scp_id'] for c in capsules], "evolve")
        if capsules:
            new_capsule["declaration"] = copy.deepcopy(capsules[0].get("declaration", {}))
            new_capsule["declaration"]["newly_evolved_field"] = "placeholder_value"
        return new_capsule

    def _optimise(self, capsules: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Placeholder for optimising a capsule by removing bloated fields."""
        print(f"Optimising {len(capsules)} capsule(s) with kwargs: {kwargs}")
        # A real implementation would remove fields with low co-occurrence.
        new_capsule = self._create_new_capsule_shell([c['scp_id'] for c in capsules], "optimise")
        if capsules:
            new_capsule["declaration"] = copy.deepcopy(capsules[0].get("declaration", {}))
            # Example: remove a 'parameters' field if it exists
            new_capsule["declaration"].pop("parameters", None)
        return new_capsule

    # --- Placeholders for other operations from the README ---

    def _extend(self, capsules: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Placeholder for extending a capsule."""
        return self._evolve(capsules, **kwargs) # Similar to evolve for now

    def _invert(self, capsules: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Placeholder for inverting a capsule's intent."""
        new_capsule = self._create_new_capsule_shell([c['scp_id'] for c in capsules], "invert")
        if capsules:
            new_capsule["declaration"] = copy.deepcopy(capsules[0].get("declaration", {}))
            original_intent = new_capsule["declaration"].get("intent", "")
            new_capsule["declaration"]["intent"] = f"INVERSION of: {original_intent}"
        return new_capsule

    def _substitute(self, capsules: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Placeholder for substituting fields in a capsule."""
        new_capsule = self._create_new_capsule_shell([c['scp_id'] for c in capsules], "substitute")
        if capsules:
            new_capsule["declaration"] = copy.deepcopy(capsules[0].get("declaration", {}))
            if "parameters" in new_capsule["declaration"]:
                new_capsule["declaration"]["parameters"]["difficulty"] = "substituted_difficulty"
        return new_capsule


    def mutate(self, source_ids: List[str], operation: Operation, **kwargs) -> Dict[str, Any]:
        """
        Performs a mutation operation on one or more source capsules.

        Args:
            source_ids: A list of scp_id strings for the source capsules.
            operation: The mutation to perform (e.g., 'merge', 'evolve').
            **kwargs: Additional parameters for the specific operation.

        Returns:
            A new dictionary representing the mutated capsule.

        Raises:
            ValueError: If the operation is unknown or source capsules are not found.
        """
        source_capsules = [self._get_capsule_by_id(sid) for sid in source_ids]
        if not all(source_capsules):
            missing = [sid for sid, cap in zip(source_ids, source_capsules) if not cap]
            raise ValueError(f"Source capsule(s) not found in cache: {missing}")

        # Cast to non-optional list after the check
        valid_capsules: List[Dict[str, Any]] = [c for c in source_capsules if c is not None]

        operation_map = {
            "merge": self._merge,
            "evolve": self._evolve,
            "optimise": self._optimise,
            "extend": self._extend,
            "invert": self._invert,
            "substitute": self._substitute,
        }

        op_func = operation_map.get(operation)
        if not op_func:
            raise ValueError(f"Unknown mutation operation: '{operation}'")

        return op_func(valid_capsules, **kwargs)