"""State management for DevMentor.

Handles loading/saving of portable state from .devmentor/state.json.
This is the single source of truth for user progress.
"""

import json
from datetime import datetime
from pathlib import Path

from .paths import DEVMENTOR_DIR, STATE_JSON

DEFAULT_STATE = {
    "schema_version": "1.0",
    "first_open_completed": False,
    "active_track": "vscode",
    "active_tutorial": "tutorials/00-vscode-basics/01-command-palette.md",
    "active_challenge": None,
    "skill_xp": {"vscode": 0, "git": 0, "ai": 0, "debugging": 0, "godot": 0},
    "achievements": [],
    "last_updated": None,
}


def load_state() -> dict:
    """Load the current state from state.json."""
    DEVMENTOR_DIR.mkdir(exist_ok=True)

    if STATE_JSON.exists():
        try:
            with open(STATE_JSON) as f:
                state = json.load(f)
            for key, value in DEFAULT_STATE.items():
                if key not in state:
                    state[key] = value
            return state
        except (OSError, json.JSONDecodeError):
            pass

    state = DEFAULT_STATE.copy()
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    return state


def save_state(state: dict) -> None:
    """Save the state to state.json."""
    DEVMENTOR_DIR.mkdir(exist_ok=True)
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    with open(STATE_JSON, "w") as f:
        json.dump(state, f, indent=2)


def update_skill_xp(skill: str, xp_delta: int) -> int:
    """Update the XP for a skill and return new total."""
    state = load_state()
    if "skill_xp" not in state:
        state["skill_xp"] = {}
    current = state["skill_xp"].get(skill, 0)
    state["skill_xp"][skill] = current + xp_delta
    save_state(state)
    return state["skill_xp"][skill]


def get_active_tutorial() -> str:
    """Get the currently active tutorial path."""
    state = load_state()
    return state.get("active_tutorial", DEFAULT_STATE["active_tutorial"])


def set_active_tutorial(tutorial_path: str) -> None:
    """Set the active tutorial path."""
    state = load_state()
    state["active_tutorial"] = tutorial_path
    save_state(state)
