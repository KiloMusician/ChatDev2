"""Wizard Navigator module namespace wrapper.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.1"
}
"""

from src.tools.wizard_navigator import (RepositoryWizard, WizardNavigator,
                                        colorize)
from src.tools.wizard_navigator import main as wizard_main

__all__ = ["RepositoryWizard", "WizardNavigator", "colorize", "wizard_main"]


def main() -> None:
    """Entry point for the wizard navigator."""
    wizard_main()


if __name__ == "__main__":
    main()
