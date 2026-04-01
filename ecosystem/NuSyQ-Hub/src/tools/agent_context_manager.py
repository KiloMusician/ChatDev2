"""AgentContextManager.

Lightweight JSON-backed context registry for agents. Allows registering named
contexts (dicts), loading/saving to disk, merging contexts, and simple querying.

This is intentionally small and modular so it can be replaced or extended by
other implementations (database-backed, Redis, or IPC-based) later.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class AgentContextManager:
    """Manage named contexts for agents with JSON persistence.

    Usage:
        mgr = AgentContextManager(repo_root=Path('.'))
        mgr.register('kilo_discovery', {'files': ['src/tools/kilo_discovery_system.py']})
        mgr.save()
        ctx = mgr.load('kilo_discovery')
    """

    def __init__(
        self, repo_root: Path | None = None, filename: str = "agent_contexts.json"
    ) -> None:
        """Initialize the AgentContextManager.

        Args:
            repo_root: Repository root path where the context file will be stored.
            filename: Filename for persisted contexts (JSON).

        """
        self.repo_root = repo_root or Path.cwd()
        self._file = self.repo_root / filename
        self._contexts: dict[str, dict[str, Any]] = {}
        # Try loading existing file if present
        if self._file.exists():
            try:
                self._contexts = json.loads(self._file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError, OSError):
                # Corrupt file - start fresh
                self._contexts = {}

    def register(self, name: str, context: dict[str, Any]) -> None:
        """Register or replace a named context."""
        self._contexts[name] = context

    def load(self, name: str) -> dict[str, Any] | None:
        """Return a copy of the named context or None if missing."""
        ctx = self._contexts.get(name)
        if ctx is None:
            return None
        # Return a shallow copy to avoid accidental mutation
        return dict(ctx)

    def merge(self, name: str, other: dict[str, Any]) -> dict[str, Any]:
        """Merge 'other' into the named context and return the merged result.

        This uses a simple shallow merge: values from 'other' overwrite existing keys.
        """
        base = dict(self._contexts.get(name, {}))
        base.update(other)
        self._contexts[name] = base
        return dict(base)

    def save(self) -> None:
        """Persist contexts to disk (atomic write)."""
        tmp = self._file.with_suffix(self._file.suffix + ".tmp")
        tmp.write_text(json.dumps(self._contexts, indent=2), encoding="utf-8")
        tmp.replace(self._file)

    def list(self) -> list[str]:
        """Return a list of registered context names."""
        return list(self._contexts.keys())


__all__ = ["AgentContextManager"]
