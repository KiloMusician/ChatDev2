"""Budgeting subsystem — intelligent token budget management.

Manages token usage across agents and tasks with budget constraints and
optimization. Tracks patterns, predicts usage, and provides cost-aware
fallback strategies across the NuSyQ agent ecosystem.

OmniTag: {
    "purpose": "budgeting_subsystem",
    "tags": ["Budgeting", "Tokens", "CostOptimization", "Constraints"],
    "category": "resource_management",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.budgeting.token_budget_manager import (TokenBudget,
                                                    TokenBudgetManager,
                                                    TokenTracker, TokenUsage)

__all__ = [
    "TokenBudget",
    "TokenBudgetManager",
    "TokenTracker",
    "TokenUsage",
]


def __getattr__(name: str):
    if name in ("TokenBudget", "TokenUsage", "TokenTracker", "TokenBudgetManager"):
        from src.budgeting.token_budget_manager import (TokenBudget,
                                                        TokenBudgetManager,
                                                        TokenTracker,
                                                        TokenUsage)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
