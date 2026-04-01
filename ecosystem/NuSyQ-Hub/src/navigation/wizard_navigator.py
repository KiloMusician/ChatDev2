"""Navigation-focused wrapper for the Wizard Navigator module.

This module re-exports the core WizardNavigator from its tools location so
it can be developed in its own namespace.
"""

from src.tools.wizard_navigator import WizardNavigator
from src.tools.wizard_navigator import main as wizard_main

__all__ = ["WizardNavigator", "wizard_main"]
