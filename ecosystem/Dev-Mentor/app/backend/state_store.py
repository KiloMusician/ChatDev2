from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict

from .paths import CORE_DIR

STATE_DIR = CORE_DIR / ".devmentor"
STATE_PATH = STATE_DIR / "state.json"

DEFAULT_STATE: Dict[str, Any] = {
    "schema_version": "0.2.0",
    "environment": "replit",
    "active_tutorial": "tutorials/00-welcome/START_HERE.md",
    "progress": {"level": 1, "xp": 0, "streak_days": 0},
    "skill_xp": {},
    "achievements": [],
    "last_action": None,
}


def ensure_state() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_PATH.exists():
        save_state(DEFAULT_STATE)


def load_state() -> Dict[str, Any]:
    ensure_state()
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        bad = STATE_PATH.with_suffix(".json.bad")
        try:
            shutil.copy2(STATE_PATH, bad)
        except Exception:
            pass
        save_state(DEFAULT_STATE)
        return dict(DEFAULT_STATE)


def save_state(state: Dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    tmp.replace(STATE_PATH)
