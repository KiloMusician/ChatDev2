"""
Terminal Depths — Prestige & Ascension System
Players can reset progress after story completion, earning prestige currency
and permanent augmentations that persist across runs.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List


def _compute_prestige_reward(gs_snapshot: Dict, augmentations) -> int:
    """
    Calculate prestige currency (ΨP) earned on ascension.
    Based on: level reached, challenges completed, commands run,
    story beats triggered, ascension count (scaling down over time).
    """
    level = gs_snapshot.get("level", 1)
    challenges = len(gs_snapshot.get("completed_challenges", []))
    commands = gs_snapshot.get("commands_run", 0)
    beats = len(gs_snapshot.get("story_beats", []))
    ascension_count = gs_snapshot.get("ascension_count", 0)

    base = level * 2 + challenges * 3 + (commands // 50) + beats
    scaling = max(0.5, 1.0 - ascension_count * 0.1)
    reward = max(1, int(base * scaling))

    prestige_mult = augmentations.prestige_multiplier() if augmentations else 1.0
    return max(1, int(reward * prestige_mult))


ASCENSION_LAYER_NAMES = [
    "Surface Layer",
    "Shadow Layer",
    "Ghost Layer",
    "Phantom Layer",
    "Void Layer",
    "Singularity Layer",
    "Omega Layer",
    "ΞΣΛΨΩN Layer",
]

LAYER_MODIFIERS = {
    0: {},
    1: {"xp_rate": 1.10, "enemy_strength": 1.15, "challenge_xp": 1.20},
    2: {"xp_rate": 1.25, "enemy_strength": 1.35, "challenge_xp": 1.40, "hidden_content": True},
    3: {"xp_rate": 1.50, "enemy_strength": 1.60, "challenge_xp": 1.60, "hidden_content": True},
    4: {"xp_rate": 2.00, "enemy_strength": 2.00, "challenge_xp": 2.00, "chaos_mode": True},
}


class PrestigeSystem:
    """Tracks prestige state across player resets."""

    def __init__(self):
        self.prestige_currency: int = 0
        self.ascension_count: int = 0
        self.total_prestige_earned: int = 0
        self.ascension_log: List[Dict] = []
        self.current_layer: int = 0
        self.layer_name: str = ASCENSION_LAYER_NAMES[0]
        self.main_story_complete: bool = False
        self._last_ascension_at: float = 0.0

    @property
    def layer_modifiers(self) -> Dict:
        return LAYER_MODIFIERS.get(min(self.ascension_count, 4), LAYER_MODIFIERS[4])

    def can_ascend(self) -> bool:
        """Player can ascend after completing the main story arc."""
        return self.main_story_complete

    def ascend(self, gs_snapshot: Dict, augmentations) -> Dict[str, Any]:
        """
        Execute ascension: compute reward, record history.
        Returns the ascension result dict. Caller is responsible for
        resetting the GameState while preserving augmentations.
        """
        if not self.can_ascend():
            return {"error": "Ascension requires completing the main story arc first."}

        reward = _compute_prestige_reward(gs_snapshot, augmentations)
        self.prestige_currency += reward
        self.total_prestige_earned += reward
        self.ascension_count += 1
        self.current_layer = self.ascension_count
        self.layer_name = ASCENSION_LAYER_NAMES[min(self.ascension_count, len(ASCENSION_LAYER_NAMES) - 1)]
        self.main_story_complete = False  # reset for new run
        self._last_ascension_at = time.time()

        record = {
            "ascension_number": self.ascension_count,
            "level_reached": gs_snapshot.get("level", 1),
            "challenges_completed": len(gs_snapshot.get("completed_challenges", [])),
            "commands_run": gs_snapshot.get("commands_run", 0),
            "prestige_earned": reward,
            "layer": self.layer_name,
            "timestamp": self._last_ascension_at,
        }
        self.ascension_log.append(record)

        return {
            "ok": True,
            "prestige_earned": reward,
            "prestige_total": self.prestige_currency,
            "ascension_count": self.ascension_count,
            "new_layer": self.layer_name,
            "layer_modifiers": self.layer_modifiers,
            "record": record,
        }

    def to_dict(self) -> dict:
        return {
            "prestige_currency": self.prestige_currency,
            "ascension_count": self.ascension_count,
            "total_prestige_earned": self.total_prestige_earned,
            "ascension_log": list(self.ascension_log),
            "current_layer": self.current_layer,
            "layer_name": self.layer_name,
            "main_story_complete": self.main_story_complete,
            "last_ascension_at": self._last_ascension_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PrestigeSystem":
        p = cls()
        p.prestige_currency = d.get("prestige_currency", 0)
        p.ascension_count = d.get("ascension_count", 0)
        p.total_prestige_earned = d.get("total_prestige_earned", 0)
        p.ascension_log = d.get("ascension_log", [])
        p.current_layer = d.get("current_layer", 0)
        p.layer_name = d.get("layer_name", ASCENSION_LAYER_NAMES[0])
        p.main_story_complete = d.get("main_story_complete", False)
        p._last_ascension_at = d.get("last_ascension_at", 0.0)
        return p
