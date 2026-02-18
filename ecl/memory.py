"""NuSyQ ChatDev memory compatibility shim.

This module intentionally provides a lightweight placeholder implementation
while exposing the legacy API surface expected by older ChatDev/CAMEL code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def retrieve_experiences(query: str, limit: int = 1) -> list[str]:
    """Return placeholder references for the requested query."""
    return [f"nusyq-memory-{query}-{idx}" for idx in range(1, limit + 1)]


def store_experience(data: dict[str, str]) -> None:
    """No-op storage path (placeholder only)."""
    del data  # intentional no-op


def describe() -> str:
    """Explain the placeholder to auditing tools."""
    return "NuSyQ ChatDev memory compatibility shim (placeholder backend)."


class Memory:
    """Compatibility shim for ChatDev memory API.

    Legacy ChatDev paths expect:
    - ``memory.memory_data["All"]`` to exist
    - ``memory.memory_retrieval(...)`` to be callable
    - ``memory.upload()`` and ``memory.upload_from_experience(...)`` methods
    - mutable ``id_enabled`` and ``directory`` attributes
    """

    def __init__(self) -> None:
        self._store: list[dict[str, str]] = []
        self.id_enabled: bool = False
        self.directory: str | None = None
        # Legacy shape: channels keyed by role/group name.
        self.memory_data: dict[str, "Memory"] = {"All": self}

    def retrieve(self, query: str, limit: int = 1) -> list[str]:
        """Retrieve placeholder experiences."""
        return retrieve_experiences(query, limit)

    def add(self, data: dict[str, str]) -> None:
        """Store an experience payload in-memory."""
        self._store.append(data)
        store_experience(data)

    def upload(self) -> None:
        """Initialize backing directory if configured (no-op persistence)."""
        if self.directory:
            Path(self.directory).mkdir(parents=True, exist_ok=True)

    def upload_from_experience(self, experience: Any) -> None:
        """Accept legacy upload calls without failing."""
        self.add({"source": "experience", "value": str(type(experience).__name__)})

    def memory_retrieval(self, query: str, retrieval_type: str = "text") -> None:
        """Legacy retrieval hook used by CAMEL ChatAgent.

        Returning ``None`` keeps behavior safe for placeholder mode while
        satisfying callers that only check for method existence.
        """
        del query, retrieval_type
        return None
