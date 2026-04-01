"""UI subsystem — VS Code metrics dashboard components.

OmniTag: {
    "purpose": "ui_subsystem",
    "tags": ["UI", "VSCode", "Metrics", "Dashboard"],
    "category": "tooling",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

__all__ = ["VSCodeMetricsUI", "create_vscode_metrics_ui"]


def __getattr__(name: str) -> object:
    if name in ("VSCodeMetricsUI", "create_vscode_metrics_ui"):
        from src.ui.vscode_metrics_ui import (VSCodeMetricsUI,
                                              create_vscode_metrics_ui)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
