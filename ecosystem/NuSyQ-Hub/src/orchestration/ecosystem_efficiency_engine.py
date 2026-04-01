"""Ecosystem Efficiency Engine - optional routing hints for agent orchestration.

This module is intentionally lightweight and optional. The agent task router
will import it if available and attach any routing hints to the orchestration
context. Set NUSYQ_ECOSYSTEM_EFFICIENCY_FORCE=1 to allow the hint to override
auto routing decisions.
"""

from __future__ import annotations

from typing import Any


def suggest_routing(
    task_type: str,
    description: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a lightweight routing hint without enforcing it.

    Args:
        task_type: Requested task type (analyze, generate, review, debug, ...)
        description: Task description
        context: Optional context payload

    Returns:
        Dict with suggested target_system and metadata.
    """
    del description
    context = context or {}
    target_system = None

    if task_type in {"generate"}:
        target_system = "chatdev"
    elif task_type in {"analyze", "review"}:
        target_system = "ollama"
    elif task_type in {"debug"}:
        target_system = "quantum_resolver"

    return {
        "target_system": target_system,
        "confidence": 0.4 if target_system else 0.0,
        "reason": "baseline heuristic hint from ecosystem_efficiency_engine",
        "context_keys": sorted(context.keys())[:8],
    }
