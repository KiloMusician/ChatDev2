"""Wizard Navigator sub-package — interactive repository navigation.

Provides a room-graph traversal system for navigating the NuSyQ-Hub
codebase interactively via wizard-style prompts.

OmniTag: {
    "purpose": "wizard_navigator_subpackage",
    "tags": ["Navigation", "Wizard", "Repository", "Interactive"],
    "category": "tooling",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

from .wizard_navigator import RepositoryWizard, WizardNavigator, main

__all__ = [
    # Graph/room primitives (lazy)
    "Navigator",
    "RepositoryWizard",
    "Room",
    "WizardNavigator",
    "main",
]


def __getattr__(name: str) -> object:
    if name == "Navigator":
        from src.navigation.wizard_navigator.graph import Navigator

        return Navigator
    if name == "Room":
        from src.navigation.wizard_navigator.room import Room

        return Room
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
