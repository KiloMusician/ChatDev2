"""wizard_navigator.py (compatibility shim).

This module keeps legacy imports working while delegating to the
consolidated implementation in src/tools/wizard_navigator_consolidated.py.
"""

from __future__ import annotations

from src.tools.wizard_navigator_consolidated import (RepositoryWizard,
                                                     WizardNavigator)
from src.tools.wizard_navigator_consolidated import main as wizard_main

_COLOR_CODES = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "purple": 35,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "gray": 90,
    "bright_red": 91,
    "bright_green": 92,
    "bright_yellow": 93,
    "bright_blue": 94,
    "bright_magenta": 95,
    "bright_cyan": 96,
    "bright_white": 97,
}


def colorize(text: str, color: str | None = None, bold: bool = False) -> str:
    """Return ANSI-colored text for terminal output."""
    if not color:
        return text
    code = _COLOR_CODES.get(color.lower())
    if code is None:
        return text
    if bold:
        return f"\033[1;{code}m{text}\033[0m"
    return f"\033[{code}m{text}\033[0m"


def main() -> None:
    """Entry point preserved for backwards compatibility."""
    wizard_main()


__all__ = [
    "RepositoryWizard",
    "WizardNavigator",
    "colorize",
    "main",
    "wizard_main",
]


if __name__ == "__main__":
    main()
