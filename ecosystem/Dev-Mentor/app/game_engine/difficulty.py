"""
app/game_engine/difficulty.py — Adaptive Difficulty Scaler
===========================================================
Dynamically adjusts game challenge based on player performance metrics.

Design principles:
- Transparent to the player (no hidden difficulty label shown unless debug)
- Adjusts: XP multipliers, enemy HP scaling, puzzle hint costs, trust decay rates
- Based on: session velocity (commands/min), success rate, level vs time played
- Stored in gs.flags["difficulty_state"]

Usage:
    from app.game_engine.difficulty import AdaptiveDifficulty
    diff = AdaptiveDifficulty()
    scale = diff.get_scale(gs.flags)        # 0.5 (easy) to 2.0 (brutal)
    xp = diff.scale_xp(base_xp, gs.flags)  # adjusted XP
    diff.record_event(gs.flags, "success")   # track outcomes
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Difficulty scale clamped to [MIN_SCALE, MAX_SCALE]
MIN_SCALE = 0.6
MAX_SCALE = 2.0
DEFAULT_SCALE = 1.0

# Target commands per minute for "balanced" play
TARGET_VELOCITY = 3.0   # 3 commands/min = engaged but not grinding

# How much each signal shifts the difficulty (per evaluation cycle)
VELOCITY_WEIGHT = 0.15
SUCCESS_WEIGHT = 0.25
LEVEL_TIME_WEIGHT = 0.10

# Evaluation window (seconds)
EVAL_WINDOW = 300  # 5 minutes

# ---------------------------------------------------------------------------
# Adaptive difficulty engine
# ---------------------------------------------------------------------------

class AdaptiveDifficulty:
    """
    Computes a difficulty scale factor [0.6, 2.0] from player behaviour.

    Factors considered:
    1. Command velocity (commands/min) vs. target velocity
    2. Success rate: exploits won / exploits attempted
    3. Level-to-time ratio: are they levelling faster or slower than baseline?
    4. Consecutive failures (frustration signal → ease off)
    """

    def _init_state(self, flags: dict) -> dict:
        if "difficulty_state" not in flags:
            flags["difficulty_state"] = {
                "scale": DEFAULT_SCALE,
                "command_log": [],        # list of (timestamp, success: bool)
                "level_log": [],          # list of (timestamp, level)
                "consecutive_failures": 0,
                "last_eval": time.time(),
            }
        return flags["difficulty_state"]

    def record_event(self, flags: dict, event: str, level: int = None) -> None:
        """
        Record a gameplay event.
        event: "success" | "failure" | "command"
        """
        state = self._init_state(flags)
        now = time.time()
        window_cutoff = now - EVAL_WINDOW

        # Prune old entries
        state["command_log"] = [(t, s) for t, s in state["command_log"] if t > window_cutoff]

        if event == "success":
            state["command_log"].append((now, True))
            state["consecutive_failures"] = 0
        elif event == "failure":
            state["command_log"].append((now, False))
            state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        elif event == "command":
            state["command_log"].append((now, None))  # neutral command

        if level is not None:
            state["level_log"] = [(t, l) for t, l in state["level_log"] if t > window_cutoff]
            state["level_log"].append((now, level))

        # Re-evaluate every 60 seconds
        if now - state.get("last_eval", 0) > 60:
            self._evaluate(state, now)

    def _evaluate(self, state: dict, now: float) -> None:
        """Recompute difficulty scale from recent signals."""
        log = state["command_log"]
        if len(log) < 3:
            return  # not enough data

        state["last_eval"] = now
        current_scale = state["scale"]
        delta = 0.0

        # Signal 1: Command velocity
        window_seconds = min(EVAL_WINDOW, now - log[0][0]) if log else 1
        velocity = len(log) / max(window_seconds / 60.0, 0.1)  # commands/min
        velocity_ratio = velocity / TARGET_VELOCITY
        delta += (velocity_ratio - 1.0) * VELOCITY_WEIGHT

        # Signal 2: Success rate (only count true/false entries)
        outcomes = [(t, s) for t, s in log if s is not None]
        if len(outcomes) >= 3:
            success_rate = sum(1 for _, s in outcomes if s) / len(outcomes)
            # High success = player doing well → increase difficulty slightly
            delta += (success_rate - 0.6) * SUCCESS_WEIGHT

        # Signal 3: Consecutive failures — ease off
        consec = state.get("consecutive_failures", 0)
        if consec >= 5:
            delta -= 0.2  # frustration relief

        # Apply damped adjustment
        new_scale = current_scale + delta * 0.3  # damping factor
        state["scale"] = round(max(MIN_SCALE, min(MAX_SCALE, new_scale)), 3)

    def get_scale(self, flags: dict) -> float:
        """Return current difficulty scale [0.6, 2.0]."""
        state = self._init_state(flags)
        return state.get("scale", DEFAULT_SCALE)

    def scale_xp(self, base_xp: int, flags: dict) -> int:
        """Return XP adjusted by inverse difficulty (easier = more XP, harder = less)."""
        scale = self.get_scale(flags)
        # Invert: harder difficulty means player earns slightly less XP (challenge matters more)
        xp_multiplier = 2.0 - scale  # scale=0.6 → 1.4x XP; scale=2.0 → 0.0x (floor at 0.5x)
        xp_multiplier = max(xp_multiplier, 0.5)
        return max(1, round(base_xp * xp_multiplier))

    def scale_enemy_hp(self, base_hp: int, flags: dict) -> int:
        """Return enemy HP adjusted by difficulty scale."""
        scale = self.get_scale(flags)
        return max(1, round(base_hp * scale))

    def hint_cost_multiplier(self, flags: dict) -> float:
        """Puzzle hints cost more XP on higher difficulty."""
        scale = self.get_scale(flags)
        return round(scale, 1)

    def get_label(self, flags: dict) -> str:
        """Human-readable difficulty label."""
        scale = self.get_scale(flags)
        if scale < 0.75:
            return "EASY"
        if scale < 1.0:
            return "BALANCED (easing)"
        if scale < 1.3:
            return "BALANCED"
        if scale < 1.6:
            return "HARD"
        if scale < 1.9:
            return "EXPERT"
        return "BRUTAL"

    def render_debug(self, flags: dict) -> List[dict]:
        """Wire-format debug readout."""
        state = self._init_state(flags)
        scale = state["scale"]
        log = state["command_log"]
        now = time.time()
        window_cutoff = now - EVAL_WINDOW
        recent = [(t, s) for t, s in log if t > window_cutoff]
        velocity = len(recent) / (EVAL_WINDOW / 60.0)
        outcomes = [(t, s) for t, s in recent if s is not None]
        success_rate = (sum(1 for _, s in outcomes if s) / len(outcomes)) if outcomes else 0.0

        return [
            {"t": "system", "s": "  ═══ ADAPTIVE DIFFICULTY ═══"},
            {"t": "info",   "s": f"  Scale: {scale:.3f}  Label: {self.get_label(flags)}"},
            {"t": "dim",    "s": f"  Velocity: {velocity:.1f} cmd/min (target: {TARGET_VELOCITY})"},
            {"t": "dim",    "s": f"  Success rate: {success_rate:.0%}  Consecutive failures: {state.get('consecutive_failures', 0)}"},
            {"t": "dim",    "s": f"  XP multiplier: {(2.0 - scale):.2f}x  Enemy HP: {scale:.2f}x"},
        ]


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_instance: Optional[AdaptiveDifficulty] = None


def get_difficulty() -> AdaptiveDifficulty:
    global _instance
    if _instance is None:
        _instance = AdaptiveDifficulty()
    return _instance


if __name__ == "__main__":
    diff = AdaptiveDifficulty()
    flags: dict = {}

    # Simulate 10 commands, mostly successes (good player)
    for i in range(10):
        diff.record_event(flags, "success", level=3)

    print(f"Scale after 10 successes: {diff.get_scale(flags)} — {diff.get_label(flags)}")
    print(f"XP 50 → {diff.scale_xp(50, flags)}")
    print(f"Enemy HP 35 → {diff.scale_enemy_hp(35, flags)}")

    # Simulate frustration
    for _ in range(6):
        diff.record_event(flags, "failure")

    for r in diff.render_debug(flags):
        print(f"[{r['t']}] {r['s']}")
