"""Analytics subsystem — model selection and resolution tracking.

Provides performance metrics collection and analytics for AI model selection,
tracking resolution rates, latency, and quality across the agent ecosystem.

OmniTag: {
    "purpose": "analytics_subsystem",
    "tags": ["Analytics", "Metrics", "ModelSelection", "Tracking"],
    "category": "observability",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.analytics.model_selection_analytics import (
        ModelSelectionAnalytics, initialize_model_analytics)

__all__ = ["ModelSelectionAnalytics", "initialize_model_analytics"]


def __getattr__(name: str):
    if name in ("ModelSelectionAnalytics", "initialize_model_analytics"):
        from src.analytics.model_selection_analytics import (
            ModelSelectionAnalytics, initialize_model_analytics)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
