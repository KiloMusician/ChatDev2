# DEPRECATED: Use src/integration/consciousness_bridge.py (Phase 1 canonical).
# This file is a legacy compatibility wrapper delegating to AgentOrchestrationHub.
# Kept for backward-compat imports; do not add new logic here.
"""Consciousness Bridge (Hub) - Semantic analysis wrapper."""

from pathlib import Path
from typing import Any

from src.agents.agent_orchestration_hub import get_agent_orchestration_hub
from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


class ConsciousnessBridge:
    """Compatibility wrapper for consciousness-aware analysis."""

    def __init__(self, root_path: Path | None = None, hub: Any | None = None) -> None:
        """Initialize bridge with optional root path and orchestration hub."""
        self.root_path = root_path or Path.cwd()
        self._hub = hub or get_agent_orchestration_hub(root_path=self.root_path)

    async def analyze_task(
        self,
        task_type: str,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Analyze task semantics via the hub."""
        context = context or {}
        return await self._hub.analyze_task_semantics(task_type, description, context)

    async def enrich_context(
        self,
        task_type: str,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return the context augmented with semantic analysis."""
        context = context or {}
        analysis = await self._hub.analyze_task_semantics(task_type, description, context)
        return {**context, "semantic_analysis": analysis}


__all__ = ["ConsciousnessBridge"]
