"""Navigation subsystem — wizard-style UI navigation framework.

Provides graph-based wizard navigation for multi-step workflows and
interactive prompts. Re-exports the WizardNavigator from src.tools
with its own dedicated namespace for development.

OmniTag: {
    "purpose": "navigation_subsystem",
    "tags": ["Navigation", "Wizard", "UI", "Workflow"],
    "category": "ui",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = ["WizardNavigator"]


def __getattr__(name: str):
    if name == "WizardNavigator":
        from src.navigation.wizard_navigator import WizardNavigator

        return WizardNavigator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
