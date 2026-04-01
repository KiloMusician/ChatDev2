"""
Terminal Depths — R2: Attribute System
4 core attributes derived from skill levels. Passive and active effects.
"""
from __future__ import annotations

import random
from typing import Dict, List


# ── Wire-format helpers ───────────────────────────────────────────────────────

def _line(text: str, t: str = "info") -> dict:
    return {"t": t, "s": text}


def _ok(text: str) -> dict:
    return _line(text, "success")


def _dim(text: str) -> dict:
    return _line(text, "dim")


def _sys(text: str) -> dict:
    return _line(text, "system")


def _lore(text: str) -> dict:
    return _line(text, "lore")


# ── Attribute → skill mapping ─────────────────────────────────────────────────
#   STR ← security, hacking (hacking mapped to security for compat)
#   INT ← cryptography, programming, networking
#   CHA ← social_engineering, forensics
#   LCK ← terminal, git

_ATTR_SKILLS: Dict[str, List[str]] = {
    "str": ["security"],        # hacking skill maps to security
    "int": ["cryptography", "programming", "networking"],
    "cha": ["social_engineering", "forensics"],
    "lck": ["terminal", "git"],
}

_BASE = 10  # base value for every attribute


# ── AttributeSystem ───────────────────────────────────────────────────────────

class AttributeSystem:
    """
    R2 Attribute System.

    Attributes are computed live from gs.skills; they are never stored
    separately — always derived so they stay in sync.
    """

    # ── Core computation ────────────────────────────────────────────────

    def compute(self, gs) -> Dict[str, int]:
        """
        Return {str, int, cha, lck} computed from gs.skills.

        Each relevant skill at level L contributes floor(L / 5) bonus points.
        Bonus from multiple skills in a category stacks.
        Minimum attribute value: 10 (base).
        """
        skills: Dict[str, int] = getattr(gs, "skills", {})
        attrs: Dict[str, int] = {}
        for attr, skill_keys in _ATTR_SKILLS.items():
            bonus = sum(skills.get(sk, 0) // 5 for sk in skill_keys)
            attrs[attr] = _BASE + bonus
        return attrs

    # ── Effect helpers ───────────────────────────────────────────────────

    def lck_roll(self, gs) -> bool:
        """
        1% chance per LCK point to find bonus loot/XP.
        Returns True if the luck check succeeds.
        """
        attrs = self.compute(gs)
        lck = attrs["lck"]
        chance = lck / 100.0  # e.g. LCK=12 → 12% chance
        return random.random() < chance

    def cha_trust_bonus(self, gs) -> float:
        """
        +2% trust gain per CHA point beyond 10.
        Returns a multiplier (e.g. CHA=14 → 1.08).
        """
        attrs = self.compute(gs)
        cha = attrs["cha"]
        bonus_pct = max(0, cha - _BASE) * 0.02
        return 1.0 + bonus_pct

    def str_damage_bonus(self, gs) -> int:
        """
        +1 base damage per 2 STR points.
        Returns integer bonus.
        """
        attrs = self.compute(gs)
        return attrs["str"] // 2

    def int_hint_discount(self, gs) -> int:
        """
        Reduces hint cost by 1 per 5 INT points beyond 10 (min effective cost 1).
        Returns integer reduction.
        """
        attrs = self.compute(gs)
        return (attrs["int"] - _BASE) // 5

    # ── Render ───────────────────────────────────────────────────────────

    def render(self, gs) -> List[dict]:
        """Return wire-format attribute card."""
        attrs = self.compute(gs)

        _NAMES = {
            "str": ("STR", "Strength",      "security / hacking skills"),
            "int": ("INT", "Intelligence",  "cryptography / programming / networking"),
            "cha": ("CHA", "Charisma",      "social engineering / forensics"),
            "lck": ("LCK", "Luck",          "terminal / git"),
        }
        _EFFECTS = {
            "str": f"+{self.str_damage_bonus(gs)} dungeon base damage",
            "int": f"-{self.int_hint_discount(gs)} hint cost reduction",
            "cha": f"+{(attrs['cha'] - _BASE) * 2}% trust gain bonus",
            "lck": f"{attrs['lck']}% bonus loot/XP chance",
        }

        out: List[dict] = [
            _sys("  ═══════════════════════════════════════════════════════"),
            _sys("  ║               GHOST — ATTRIBUTE MATRIX             ║"),
            _sys("  ═══════════════════════════════════════════════════════"),
            _dim(""),
        ]
        for attr_key, (abbrev, full_name, sources) in _NAMES.items():
            val = attrs[attr_key]
            bonus = val - _BASE
            bar_filled = min(val, 30)  # cap visual at 30 (3× base)
            bar = "█" * (bar_filled // 2) + "░" * (15 - bar_filled // 2)
            color = "success" if bonus > 10 else ("warn" if bonus > 4 else "info")
            out.append(_line(
                f"  {abbrev}  {full_name:<16}  [{bar}]  {val:>3}  (+{bonus})",
                color,
            ))
            out.append(_dim(f"       Sources: {sources}"))
            out.append(_dim(f"       Effect : {_EFFECTS[attr_key]}"))
            out.append(_dim(""))

        # Luck roll teaser
        lck_chance = attrs["lck"]
        out.append(_lore(
            f"  LCK roll on each command: {lck_chance}% chance to find bonus loot."
        ))
        cha_mult = self.cha_trust_bonus(gs)
        out.append(_lore(
            f"  CHA multiplier: {cha_mult:.2f}x trust gain on all social interactions."
        ))
        out.append(_dim(""))
        out.append(_dim("  Raise attributes by levelling the associated skill categories."))
        return out
