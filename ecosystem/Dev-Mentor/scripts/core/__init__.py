"""DevMentor Core Library

Shared utilities for path management, state handling, and reporting.
This module consolidates common functionality to prevent duplication.
"""

from .paths import (CHALLENGES_DIR, DEVMENTOR_DIR, DOCS_DIR, EXPORTS_DIR,
                    REPORTS_DIR, ROOT, SCRIPTS_DIR, STATE_JSON, TUTORIALS_DIR,
                    VSCODE_DIR)
from .state import (get_active_tutorial, load_state, save_state,
                    set_active_tutorial, update_skill_xp)

__all__ = [
    "CHALLENGES_DIR",
    "DEVMENTOR_DIR",
    "DOCS_DIR",
    "EXPORTS_DIR",
    "REPORTS_DIR",
    "ROOT",
    "SCRIPTS_DIR",
    "STATE_JSON",
    "TUTORIALS_DIR",
    "VSCODE_DIR",
    "get_active_tutorial",
    "load_state",
    "save_state",
    "set_active_tutorial",
    "update_skill_xp",
]
