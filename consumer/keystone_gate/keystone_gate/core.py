"""
core.py - The main processing engine for the Keystone Gate.

This module defines the KeystoneGate class, which orchestrates the validation,
scoring, and routing of semantic capsules based on the rules and features
outlined in the consumer's README.md.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from .primitives import PrimitiveManager


class KeystoneGate:
    """
    Orchestrates the validation, mutation, and governance of semantic capsules.

    This class is the primary entry point for processing LLM outputs or other
    potential capsules. It uses the PrimitiveManager for vocabulary control,
    performs adaptive validation, calculates semantic similarity against a cache
    of known capsules, and produces a confidence score to determine whether a
    capsule is approved, flagged, or rejected.
    """

    def __init__(
        self,
        primitive_file: Union[str, Path],
        cache_file: Union[str, Path],
        approval_threshold: float = 0.7,
        flag_threshold: float = 0.5,
    ):
        """
        Initializes the KeystoneGate.

        Args:
            primitive_file: Path to the JSON file for the field vocabulary.
            cache_file: Path to the JSON file for caching approved capsules.
            approval_threshold: Confidence score required for automatic approval.
            flag_threshold: Confidence score below which capsules are rejected.
                            Scores between flag and approval are flagged for review.
        """
        self.primitive_manager = PrimitiveManager(primitive_file)
        self.cache_file = Path(cache_file)
        self.capsule_cache = self._load_cache()

        self.approval_threshold = approval_threshold
        self.flag_threshold = flag_threshold

        # Placeholder for a real sentence transformer model
        self._embedding_model = None

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Loads the cache of approved capsules from a JSON file."""
        if not self.cache_file.exists():
            return {}
        try:
            with self.cache_file.open('r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_cache(self):
        """Saves the capsule cache to its JSON file."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_file.open('w', encoding='utf-8') as f:
            json.dump(self.capsule_cache, f, indent=2)

    def _validate_capsule_structure(self, capsule: Dict[str, Any]) -> List[str]:
        """Performs basic structural validation for required SCP fields."""
        errors = []
        required_fields = ["scp_id", "scp_version", "created", "declaration"]
        for field in required_fields:
            if field not in capsule:
                errors.append(f"Missing required SCP field: '{field}'")
        return errors

    def _calculate_semantic_similarity(self, capsule: Dict[str, Any]) -> float:
        """
        Placeholder for field-aware semantic similarity calculation.

        In a real implementation, this would use a sentence transformer model
        to embed the new capsule's fields and compare them against embeddings
        of capsules in the cache.
        """
        if not self.capsule_cache:
            return 1.0  # First capsule is always novel and approved.
        # Fake a similarity score for this placeholder.
        return 0.85

    def _calculate_confidence_score(
        self, similarity: float, new_fields: Set[str]
    ) -> float:
        """
        Placeholder for the composite confidence score calculation.

        A real implementation would weigh similarity, field innovation (the ratio
        of new vs. known fields), and potentially other metrics.
        """
        total_fields = len(self.primitive_manager.get_known_fields())
        innovation_score = len(new_fields) / total_fields if total_fields > 0 else 0

        # Simple weighted average for this placeholder
        confidence = (similarity * 0.8) + (innovation_score * 0.2)
        return min(1.0, confidence)

    def process(self, capsule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes an incoming capsule through the gate.

        Args:
            capsule_data: A dictionary representing the potential capsule.

        Returns:
            A result dictionary with status, scores, and the processed capsule.
        """
        errors = self._validate_capsule_structure(capsule_data)
        if errors:
            return {"status": "rejected", "errors": errors}

        # 1. Discover fields and update primitives
        newly_discovered = self.primitive_manager.discover_from_capsule(capsule_data)
        self.primitive_manager.save()

        # 2. Calculate similarity and confidence
        similarity = self._calculate_semantic_similarity(capsule_data)
        confidence = self._calculate_confidence_score(similarity, newly_discovered)

        # 3. Determine status based on thresholds
        status = "flagged"
        if confidence >= self.approval_threshold:
            status = "approved"
        elif confidence < self.flag_threshold:
            status = "rejected"
            errors.append(f"Confidence score {confidence:.2f} is below reject threshold {self.flag_threshold:.2f}")

        # 4. Build the result
        result: Dict[str, Any] = {
            "status": status,
            "confidence_score": confidence,
            "similarity_score": similarity,
            "capsule": capsule_data,
        }
        if newly_discovered:
            result["new_fields"] = sorted(list(newly_discovered))
        if errors:
            result["errors"] = errors

        # 5. If approved, add to cache
        if status == "approved":
            scp_id = capsule_data.get("scp_id")
            if scp_id:
                self.capsule_cache[scp_id] = {
                    "capsule": capsule_data,
                    "metadata": {
                        "added_at": datetime.now(timezone.utc).isoformat(),
                        "confidence": confidence,
                    }
                }
                self._save_cache()

        return result