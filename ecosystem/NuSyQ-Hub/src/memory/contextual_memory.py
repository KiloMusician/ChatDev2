"""OmniTag: {.

    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Memory"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""

from datetime import datetime
from typing import Any


class ContextualMemory:
    """Class to manage the storage and retrieval of contextual information."""

    def __init__(self) -> None:
        """Initialize ContextualMemory."""
        self.memory_store: dict[str, Any] = {}
        self.timestamp_store: dict[str, datetime] = {}

    def store_context(self, key: str, context: Any) -> None:
        """Store contextual information with a timestamp."""
        self.memory_store[key] = context
        self.timestamp_store[key] = datetime.now()

    def retrieve_context(self, key: str) -> Any:
        """Retrieve contextual information by key."""
        return self.memory_store.get(key)

    def get_context_timestamp(self, key: str) -> datetime:
        """Get the timestamp of when the context was stored."""
        result = self.timestamp_store.get(key)
        if result is None:
            return datetime.now()
        return result

    def clear_context(self, key: str) -> None:
        """Clear contextual information by key."""
        if key in self.memory_store:
            del self.memory_store[key]
            del self.timestamp_store[key]

    def clear_all_contexts(self) -> None:
        """Clear all stored contextual information."""
        self.memory_store.clear()
        self.timestamp_store.clear()

    def list_contexts(self) -> list[str]:
        """List all stored context keys."""
        return list(self.memory_store.keys())
