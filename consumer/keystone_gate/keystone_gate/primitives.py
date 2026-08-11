"""
primitives.py - Manages the living vocabulary of capsule fields.

This module contains the PrimitiveManager, which is central to Keystone Gate's
adaptive validation and auto-discovery capabilities. It maintains a persistent
JSON file (`capsule_primitives.json`) that acts as a schema and a historical
record of all fields ever encountered in processed capsules.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Set, Tuple, Optional, Union


def _utc_now() -> str:
    """Returns the current time in ISO 8601 UTC format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class PrimitiveManager:
    """
    Manages the living vocabulary of capsule fields (primitives).

    This class handles loading, saving, and auto-discovering fields from
    capsules, maintaining a persistent vocabulary in a JSON file. It tracks
    metadata for each field, such as its type, discovery date, and usage count.
    """ 

    def __init__(self, primitive_file: Union[str, Path]):
        """
        Initializes the PrimitiveManager.

        Args:
            primitive_file: Path to the JSON file for storing primitives.
        """
        self.primitive_file = Path(primitive_file)
        self.primitives: Dict[str, Dict[str, Any]] = self._load_primitives()

    def _load_primitives(self) -> Dict[str, Dict[str, Any]]:
        """Loads the primitive vocabulary from the JSON file."""
        if not self.primitive_file.exists():
            return {}
        try:
            with self.primitive_file.open('r', encoding='utf-8') as f:
                data = f.read()
                if not data.strip():
                    return {}
                return json.loads(data)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or empty, start fresh.
            return {}

    def save(self):
        """Saves the current primitive vocabulary to the JSON file."""
        self.primitive_file.parent.mkdir(parents=True, exist_ok=True)
        with self.primitive_file.open('w', encoding='utf-8') as f:
            json.dump(self.primitives, f, indent=2, sort_keys=True)

    def get_known_fields(self) -> List[str]:
        """Returns a list of all known field paths."""
        return list(self.primitives.keys())

    def is_known(self, field_path: str) -> bool:
        """Checks if a field path is already in the vocabulary."""
        return field_path in self.primitives

    def register_field(self, field_path: str, value: Any):
        """
        Registers a new field in the vocabulary or updates an existing one.

        If the field is new, it's added with metadata. If it exists, its
        occurrence count is incremented.

        Args:
            field_path: The dot-notation path of the field (e.g., "declaration.intent").
            value: The value of the field, used to infer its type.
        """
        if self.is_known(field_path):
            self.primitives[field_path]["count"] += 1
        else:
            self.primitives[field_path] = {
                "type": type(value).__name__,
                "first_seen": _utc_now(),
                "count": 1,
            }

    def discover_from_capsule(self, capsule: Dict[str, Any]) -> Set[str]:
        """
        Recursively discovers and registers all fields from a capsule dictionary.

        This is the core of the "auto-discovery" feature. It traverses the
        capsule and registers any fields not already in the vocabulary.

        Args:
            capsule: The capsule dictionary to process.

        Returns:
            A set of newly discovered field paths.
        """
        newly_discovered: Set[str] = set()

        def _traverse(obj: Any, path: str):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if not self.is_known(new_path):
                        newly_discovered.add(new_path)
                    self.register_field(new_path, value)
                    _traverse(value, new_path)

        _traverse(capsule, "")
        return newly_discovered
