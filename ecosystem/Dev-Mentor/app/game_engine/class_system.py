"""
app/game_engine/class_system.py — R1 Class System for Terminal Depths
======================================================================
At Level 10, Ghost can choose a specialization class that grants a
passive XP multiplier and a unique active ability.

Classes reflect different paths through the CHIMERA network:
  hacker, sysadmin, social_engineer, cryptanalyst, architect
"""
from __future__ import annotations

from typing import List

# ---------------------------------------------------------------------------
# Class definitions
# ---------------------------------------------------------------------------

CLASS_DEFINITIONS: dict = {
    "hacker": {
        "name": "Ghost Hacker",
        "description": (
            "The network is your weapon. You exploit systems before "
            "they know you are there. Specializes in vulnerability "
            "scanning and zero-day exploitation."
        ),
        "bonus_skills": ["security", "hacking"],
        "passive": "+15% XP from exploit/scan commands",
        "ability": "zero_day — bypass one UID check per session",
        "unlock_level": 10,
        "icon": "🕶",
    },
    "sysadmin": {
        "name": "SysAdmin",
        "description": (
            "You speak the language of the machine. Filesystems, "
            "daemons, and services bend to your will. Root shell "
            "is not a goal — it is a starting point."
        ),
        "bonus_skills": ["terminal", "networking"],
        "passive": "+20% XP from filesystem commands",
        "ability": "root_persist — root_shell lasts entire session without re-escalation",
        "unlock_level": 10,
        "icon": "🖥",
    },
    "social_engineer": {
        "name": "Social Engineer",
        "description": (
            "Every agent has a price, a fear, a blind spot. You "
            "find it. Trust is not earned — it is engineered. "
            "The most powerful exploit is a conversation."
        ),
        "bonus_skills": ["social_engineering", "forensics"],
        "passive": "+25% XP from talk/osint/trust commands",
        "ability": "deep_cover — agents never reduce trust on failed interactions",
        "unlock_level": 10,
        "icon": "🎭",
    },
    "cryptanalyst": {
        "name": "Cryptanalyst",
        "description": (
            "CHIMERA's core is math. So is yours. You break ciphers "
            "the way others break locks — methodically, inevitably. "
            "Every encoded secret is just a puzzle waiting."
        ),
        "bonus_skills": ["cryptography", "programming"],
        "passive": "+20% XP from puzzle commands",
        "ability": "cipher_master — hints in number-theory/graph-theory are free",
        "unlock_level": 10,
        "icon": "🔐",
    },
    "architect": {
        "name": "Architect",
        "description": (
            "You do not attack systems. You redesign them. Every "
            "node you claim becomes part of your infrastructure. "
            "The network expands to match your vision."
        ),
        "bonus_skills": ["networking", "programming"],
        "passive": "+10% XP from all commands",
        "ability": "system_architect — claimed nodes produce 2x resources",
        "unlock_level": 10,
        "icon": "🏗",
    },
}

# Skills that map to passive XP bonuses per class
# Format: class_name → {skill_keyword → multiplier}
_PASSIVE_SKILL_MAP: dict = {
    "hacker": {
        "exploit": 1.15,
        "scan": 1.15,
        "hack": 1.15,
        "security": 1.15,
        "hacking": 1.15,
    },
    "sysadmin": {
        "terminal": 1.20,
        "networking": 1.20,
        "filesystem": 1.20,
        "ls": 1.20,
        "find": 1.20,
        "cat": 1.20,
    },
    "social_engineer": {
        "social_engineering": 1.25,
        "forensics": 1.25,
        "talk": 1.25,
        "osint": 1.25,
        "trust": 1.25,
    },
    "cryptanalyst": {
        "cryptography": 1.20,
        "programming": 1.20,
        "puzzle": 1.20,
        "number-theory": 1.20,
        "graph-theory": 1.20,
    },
    "architect": {
        # Applies to ALL skills — handled as a fallback
        "_all": 1.10,
    },
}


# ---------------------------------------------------------------------------
# ClassSystem
# ---------------------------------------------------------------------------

def _sys(s: str) -> dict:
    return {"t": "system", "s": s}

def _dim(s: str) -> dict:
    return {"t": "dim", "s": s}

def _ok(s: str) -> dict:
    return {"t": "success", "s": s}

def _info(s: str) -> dict:
    return {"t": "info", "s": s}

def _err(s: str) -> dict:
    return {"t": "error", "s": s}

def _lore(s: str) -> dict:
    return {"t": "lore", "s": s}


class ClassSystem:
    """
    Manages player specialization classes unlocked at Level 10.

    Usage:
        cs = ClassSystem()
        if cs.available(gs.level):
            output = cs.render_classes(gs.level)
        output = cs.choose("hacker", gs)
    """

    def available(self, level: int) -> List[str]:
        """Return list of class names available at the given level."""
        return [
            name for name, defn in CLASS_DEFINITIONS.items()
            if level >= defn.get("unlock_level", 10)
        ]

    def choose(self, class_name: str, game_state) -> List[dict]:
        """
        Set gs.flags['player_class'] to class_name.
        Returns wire-format output lines.
        """
        class_name = class_name.lower().replace(" ", "_").replace("-", "_")
        if class_name not in CLASS_DEFINITIONS:
            # Try partial match
            matches = [k for k in CLASS_DEFINITIONS if k.startswith(class_name)]
            if len(matches) == 1:
                class_name = matches[0]
            else:
                valid = ", ".join(CLASS_DEFINITIONS.keys())
                return [_err(f"Unknown class '{class_name}'. Valid: {valid}")]

        defn = CLASS_DEFINITIONS[class_name]

        if game_state.level < defn.get("unlock_level", 10):
            needed = defn["unlock_level"]
            return [_err(f"Class '{class_name}' requires Level {needed}. You are Level {game_state.level}.")]

        current = game_state.flags.get("player_class")
        if current:
            return [
                _err(f"Class already chosen: {current}"),
                _dim("  Once chosen, your class cannot be changed."),
                _dim("  To start fresh, prestige — but that resets everything."),
            ]

        game_state.flags["player_class"] = class_name

        icon = defn.get("icon", "★")
        return [
            _sys(""),
            _sys("╔══════════════════════════════════════════════════════════╗"),
            _sys(f"║  CLASS SELECTED: {icon}  {defn['name']:<42}║"),
            _sys("╚══════════════════════════════════════════════════════════╝"),
            _dim(""),
            _info(f"  Passive: {defn['passive']}"),
            _info(f"  Ability: {defn['ability']}"),
            _dim(""),
            _lore(f"  \"{defn['description']}\""),
            _dim(""),
            _ok("  ★ Specialization locked in. The network bends to your will."),
            _dim("  Your class passive applies immediately to all XP gains."),
            _dim(""),
        ]

    def get_passive_multiplier(self, class_name: str, skill: str) -> float:
        """
        Return the XP multiplier for the given class and skill.
        Returns 1.0 if no bonus applies.
        """
        if not class_name:
            return 1.0
        skill_map = _PASSIVE_SKILL_MAP.get(class_name, {})
        # Exact or keyword match
        if skill in skill_map:
            return skill_map[skill]
        # Substring match (e.g. skill="hacking" matches key="hack")
        for key, mult in skill_map.items():
            if key == "_all":
                continue
            if key in skill or skill in key:
                return mult
        # Architect all-bonus
        if "_all" in skill_map:
            return skill_map["_all"]
        return 1.0

    def render_classes(self, level: int) -> List[dict]:
        """
        Return wire-format lines listing all available classes.
        Locked classes are shown dimmed.
        """
        unlocked = set(self.available(level))
        out: List[dict] = [
            _sys(""),
            _sys("╔══════════════════════════════════════════════════════════╗"),
            _sys("║  SPECIALIZATION CLASSES — Choose your path               ║"),
            _sys("║  At Level 10 you may lock in one class permanently.      ║"),
            _sys("╚══════════════════════════════════════════════════════════╝"),
            _dim(""),
        ]

        if not unlocked:
            out.append(_dim(f"  Classes unlock at Level 10. You are Level {level}."))
            out.append(_dim("  Keep hacking. The choice is coming."))
            out.append(_dim(""))
            return out

        out.append(_info("  Usage: class choose <name>    — lock in your class"))
        out.append(_info("         class info <name>      — view full class details"))
        out.append(_dim(""))

        for name, defn in CLASS_DEFINITIONS.items():
            icon = defn.get("icon", "★")
            req = defn.get("unlock_level", 10)
            if name in unlocked:
                out.append(_sys(f"  {icon}  {defn['name']} [{name}]"))
                out.append(_info(f"       Passive: {defn['passive']}"))
                out.append(_info(f"       Ability: {defn['ability']}"))
            else:
                out.append(_dim(f"  ○  {defn['name']} [{name}]  — requires Level {req}"))
            out.append(_dim(""))

        return out

    # ── R8: Prestige / Secondary Class ─────────────────────────────────

    PRESTIGE_UNLOCK_LEVEL = 25
    PRESTIGE_BONUS_FRACTION = 0.5  # 50% of primary class bonus

    # Hybrid ability unlocked when specific class combos are reached
    _HYBRID_ABILITIES: dict = {
        frozenset({"hacker", "cryptanalyst"}):     "ghost_cipher — exploits bypass both UID and cipher checks",
        frozenset({"hacker", "sysadmin"}):         "rootkit_persist — root + exploit persist across sessions",
        frozenset({"hacker", "social_engineer"}):  "social_exploit — talk commands trigger free vulnerability scan",
        frozenset({"hacker", "architect"}):        "dark_architect — claimed nodes run passive exploits",
        frozenset({"sysadmin", "cryptanalyst"}):   "cipher_root — cryptography puzzles grant root access",
        frozenset({"sysadmin", "social_engineer"}): "sys_whisperer — filesystem commands boost agent trust",
        frozenset({"sysadmin", "architect"}):      "infrastructure_god — nodes owned regenerate resources 3x",
        frozenset({"social_engineer", "cryptanalyst"}): "psych_cipher — social XP fuels puzzle hint pool",
        frozenset({"social_engineer", "architect"}): "empire_builder — trust gains expand colony supply cap",
        frozenset({"cryptanalyst", "architect"}):  "merkle_vision — pattern analysis reveals hidden routes",
    }

    def choose_prestige(self, class_name: str, game_state) -> List[dict]:
        """
        Set gs.flags['prestige_class'] at Level 25.
        Must differ from primary class. Returns wire-format lines.
        """
        PRESTIGE_UNLOCK = self.PRESTIGE_UNLOCK_LEVEL
        if game_state.level < PRESTIGE_UNLOCK:
            return [_err(f"  Prestige class unlocks at Level {PRESTIGE_UNLOCK}. You are Level {game_state.level}.")]

        primary = game_state.flags.get("player_class")
        if not primary:
            return [
                _err("  No primary class chosen yet."),
                _dim("  Run 'class choose <name>' first (unlocks at Level 10)."),
            ]

        class_name = class_name.lower().replace(" ", "_").replace("-", "_")
        if class_name not in CLASS_DEFINITIONS:
            matches = [k for k in CLASS_DEFINITIONS if k.startswith(class_name)]
            if len(matches) == 1:
                class_name = matches[0]
            else:
                valid = ", ".join(k for k in CLASS_DEFINITIONS if k != primary)
                return [_err(f"  Unknown class '{class_name}'. Valid: {valid}")]

        if class_name == primary:
            return [
                _err(f"  '{class_name}' is already your primary class."),
                _dim("  Choose a different class to prestige into."),
            ]

        existing = game_state.flags.get("prestige_class")
        if existing:
            return [
                _err(f"  Prestige class already set: {existing}"),
                _dim("  The dual-path is locked. Only rebirth can reset it."),
            ]

        game_state.flags["prestige_class"] = class_name

        defn = CLASS_DEFINITIONS[class_name]
        prim_defn = CLASS_DEFINITIONS[primary]
        icon = defn.get("icon", "★")
        prim_icon = prim_defn.get("icon", "★")
        combo = frozenset({primary, class_name})
        hybrid_ability = self._HYBRID_ABILITIES.get(combo, f"dual_path — combined passive from {primary} + {class_name}")

        game_state.add_story_beat("prestige_class_chosen")

        return [
            _sys(""),
            _sys("╔══════════════════════════════════════════════════════════╗"),
            _sys(f"║  PRESTIGE UNLOCKED: {prim_icon} {primary.upper()} ✦ {icon} {class_name.upper():<30}║"),
            _sys("╚══════════════════════════════════════════════════════════╝"),
            _dim(""),
            _info(f"  Primary:  {prim_icon}  {prim_defn['name']} — {prim_defn['passive']}"),
            _info(f"  Prestige: {icon}  {defn['name']} — {defn['passive']} (×{self.PRESTIGE_BONUS_FRACTION})"),
            _dim(""),
            _lore(f"  ⟁ Hybrid Ability: {hybrid_ability}"),
            _dim(""),
            _ok("  ★ Dual-path locked. You walk two roads at once."),
            _dim("  'In CHIMERA's lattice, the strongest threads are braided.' — SERENA"),
            _dim(""),
        ]

    def get_prestige_multiplier(self, prestige_class: str, skill: str) -> float:
        """Return the prestige XP multiplier (50% of primary class bonus)."""
        if not prestige_class:
            return 1.0
        base = self.get_passive_multiplier(prestige_class, skill)
        if base == 1.0:
            return 1.0
        # Interpolate: 1.0 base + (bonus * fraction)
        bonus = base - 1.0
        return 1.0 + bonus * self.PRESTIGE_BONUS_FRACTION

    def render_prestige_classes(self, level: int, primary_class: str) -> List[dict]:
        """List available prestige classes (all except primary)."""
        out: List[dict] = [
            _sys(""),
            _sys("╔══════════════════════════════════════════════════════════╗"),
            _sys("║  PRESTIGE CLASSES — Level 25 Dual Specialization         ║"),
            _sys("╚══════════════════════════════════════════════════════════╝"),
            _dim(""),
        ]

        if level < self.PRESTIGE_UNLOCK_LEVEL:
            out.append(_dim(f"  Prestige unlocks at Level {self.PRESTIGE_UNLOCK_LEVEL}. You are Level {level}."))
            out.append(_dim("  Keep grinding. The dual-path is ahead."))
            out.append(_dim(""))
            return out

        if not primary_class:
            out.append(_err("  Choose a primary class first: class choose <name>"))
            out.append(_dim(""))
            return out

        out.append(_info(f"  Primary: {primary_class.upper()} (locked)"))
        out.append(_info("  Usage: class prestige <name>"))
        out.append(_dim(""))

        for name, defn in CLASS_DEFINITIONS.items():
            if name == primary_class:
                continue
            icon = defn.get("icon", "★")
            combo = frozenset({primary_class, name})
            hybrid = self._HYBRID_ABILITIES.get(combo, "dual_path")
            out.append(_sys(f"  {icon}  {defn['name']} [{name}]"))
            out.append(_info(f"       Prestige passive: {defn['passive']} (×{self.PRESTIGE_BONUS_FRACTION})"))
            out.append(_lore(f"       Hybrid ability:  {hybrid}"))
            out.append(_dim(""))

        return out
