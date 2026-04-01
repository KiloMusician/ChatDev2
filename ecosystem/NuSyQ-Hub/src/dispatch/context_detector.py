"""Context mode detection for MJOLNIR Protocol.

Auto-detects whether the current working context is:
- ECOSYSTEM: Working on NuSyQ-Hub infrastructure itself
- GAME: Working on SimulatedVerse game/cultivation system
- PROJECT: Working on a new or external project

Detection uses CWD relative to known repo roots (env vars + fallback scanning).
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ContextMode(str, Enum):
    """Working context modes for agent dispatch."""

    ECOSYSTEM = "ecosystem"  # NuSyQ-Hub infrastructure work
    PROJECT = "project"  # New or external project
    GAME = "game"  # SimulatedVerse game/cultivation
    AUTO = "auto"  # Let detector decide

    def __str__(self) -> str:
        """Return string representation."""
        return self.value


# Marker files that identify a repo root
_NUSYQ_HUB_MARKERS = {"CLAUDE.md", "scripts/start_nusyq.py", "src/tools/agent_task_router.py"}
_SIMVERSE_MARKERS = {"ship-console", "GameDev", "SystemDev"}


class ContextDetector:
    """Detects working context mode from CWD and environment.

    Priority:
    1. Explicit env var override (NUSYQ_CONTEXT_MODE)
    2. CWD under NUSYQ_HUB_ROOT → ECOSYSTEM
    3. CWD under SIMULATEDVERSE_ROOT → GAME
    4. Fallback: scan parent directories for marker files
    5. Default: PROJECT
    """

    def __init__(self) -> None:
        """Initialize ContextDetector."""
        self._hub_root = self._resolve_root("NUSYQ_HUB_ROOT", _NUSYQ_HUB_MARKERS)
        self._simverse_root = self._resolve_root("SIMULATEDVERSE_ROOT", _SIMVERSE_MARKERS)

    @staticmethod
    def _resolve_root(env_var: str, markers: set[str]) -> Path | None:
        """Resolve a repo root from env var, falling back to parent dir scanning."""
        # 1. Try env var
        env_val = os.environ.get(env_var)
        if env_val:
            candidate = Path(env_val)
            if candidate.is_dir():
                return candidate.resolve()

        # 2. Try repo_path_resolver (if available)
        try:
            from src.utils.repo_path_resolver import get_repo_path

            if get_repo_path is not None:
                resolved = get_repo_path(env_var)
                if resolved and resolved.is_dir():
                    return resolved.resolve()
        except (ImportError, ValueError, RuntimeError, TypeError):
            logger.debug("Suppressed ImportError/RuntimeError/TypeError/ValueError", exc_info=True)

        # 3. Scan upward from CWD for marker files
        current = Path.cwd().resolve()
        for _ in range(8):  # Max 8 levels up
            if any((current / marker).exists() for marker in markers):
                return current
            parent = current.parent
            if parent == current:
                break
            current = parent

        return None

    def detect(self, cwd: Path | None = None) -> ContextMode:
        """Detect context mode from working directory.

        Args:
            cwd: Working directory to check (defaults to os.getcwd())

        Returns:
            Detected ContextMode
        """
        mode = self._detect_mode(cwd)
        try:
            from src.system.agent_awareness import emit as _emit

            _emit(
                "system",
                f"ContextDetector: mode={mode.value}",
                level="DEBUG",
                source="context_detector",
            )
        except Exception:
            pass
        return mode

    def _detect_mode(self, cwd: Path | None = None) -> ContextMode:
        """Internal mode detection without emit side-effect."""
        # Explicit override
        override = os.environ.get("NUSYQ_CONTEXT_MODE", "").strip().lower()
        if override in ("ecosystem", "project", "game"):
            return ContextMode(override)

        resolved_cwd = (cwd or Path.cwd()).resolve()

        # Check if CWD is under a known repo root
        if self._hub_root:
            try:
                resolved_cwd.relative_to(self._hub_root)
                return ContextMode.ECOSYSTEM
            except ValueError:
                logger.debug("Suppressed ValueError", exc_info=True)

        if self._simverse_root:
            try:
                resolved_cwd.relative_to(self._simverse_root)
                return ContextMode.GAME
            except ValueError:
                logger.debug("Suppressed ValueError", exc_info=True)

        return ContextMode.PROJECT

    def enrich_context(
        self, mode: ContextMode, base_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Enrich a context dict with mode-specific keys.

        Adds repo roots, mode identifier, and mode-specific hints that
        downstream agents can use for smarter routing.

        Args:
            mode: Detected or explicit context mode
            base_context: Existing context to augment (will not be mutated)

        Returns:
            New dict with enriched context
        """
        ctx: dict[str, Any] = dict(base_context or {})
        ctx["context_mode"] = str(mode)

        if mode == ContextMode.ECOSYSTEM:
            if self._hub_root:
                ctx["hub_root"] = str(self._hub_root)
            ctx["scope_hint"] = "nusyq-hub infrastructure and orchestration"
            ctx["relevant_configs"] = [
                "config/feature_flags.json",
                "config/model_capabilities.json",
                "config/action_catalog.json",
            ]

        elif mode == ContextMode.GAME:
            if self._simverse_root:
                ctx["simverse_root"] = str(self._simverse_root)
            ctx["scope_hint"] = "SimulatedVerse game and cultivation system"
            ctx["relevant_configs"] = ["ship-console/mind-state.json"]

        elif mode == ContextMode.PROJECT:
            ctx["scope_hint"] = "external or new project"
            # Include CWD so agents know where they're working
            ctx["project_root"] = str(Path.cwd())

        return ctx
