"""
app/game_engine/prestige_engine.py — RL3 Permadeath + RL6 Rebirth/Prestige System
=====================================================================================
Optional permadeath mode and prestige rebirth mechanic.

- Permadeath: when enabled, death erases the session's game state.
  Meta-progression (prestige points, permanent upgrades) carries over.
- Rebirth: at any time (or on death in permadeath mode), player can
  "ghost out" — sacrifice current progress for Prestige Points (PP).
  PP unlock permanent upgrades that persist across all runs.

Permanent upgrades (PRESTIGE_UPGRADES):
  Each has a cost, a max_rank, and a passive effect description.
  Effects are applied at session start via `apply_prestige_effects(gs)`.

State lives in two places:
  - gs.flags["permadeath"] — bool, set at session start
  - gs.flags["prestige"] — {pp, spent_pp, upgrades: {id: rank}}
  - These survive DEATH in permadeath mode (meta-progression).

Commands (wired via _cmd_prestige, _cmd_rebirth, _cmd_permadeath):
  prestige             — show prestige menu + PP balance
  prestige upgrades    — list all permanent upgrades
  prestige buy <id>    — purchase upgrade rank
  rebirth              — sacrifice current run for PP
  permadeath on/off    — toggle permadeath mode
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Prestige Upgrades
# ---------------------------------------------------------------------------

PRESTIGE_UPGRADES: Dict[str, Dict[str, Any]] = {
    "xp_surge": {
        "name": "XP Surge",
        "description": "All XP gains increased by 10% per rank.",
        "max_rank": 5,
        "cost_per_rank": [10, 20, 35, 55, 80],
        "icon": "⚡",
        "lore": "Ghost never stops learning, even between incarnations.",
        "effect_per_rank": 0.10,  # +10% XP multiplier
    },
    "ghost_memory": {
        "name": "Ghost Memory",
        "description": "Start each run knowing 1 extra quest (per rank).",
        "max_rank": 3,
        "cost_per_rank": [15, 30, 50],
        "icon": "💭",
        "lore": "Some things persist. The muscle memory of a thousand ghosts.",
        "effect_per_rank": 1,  # +1 active quest slot
    },
    "trace_ghost": {
        "name": "Trace Ghost",
        "description": "Start each run with trace level 10 lower (per rank).",
        "max_rank": 4,
        "cost_per_rank": [12, 25, 40, 60],
        "icon": "👻",
        "lore": "Being invisible is a skill. Being forgotten is an art.",
        "effect_per_rank": -10,  # -10 trace per rank
    },
    "credit_cache": {
        "name": "Credit Cache",
        "description": "Start each run with 50 extra credits (per rank).",
        "max_rank": 5,
        "cost_per_rank": [8, 16, 28, 45, 65],
        "icon": "💰",
        "lore": "Old wallets, new ghosts.",
        "effect_per_rank": 50,
    },
    "anchor_shard": {
        "name": "Anchor Shard",
        "description": "Start with 1 extra Remnant anchor charge (per rank).",
        "max_rank": 3,
        "cost_per_rank": [20, 40, 70],
        "icon": "⚓",
        "lore": "Every death leaves a splinter of time behind.",
        "effect_per_rank": 1,
    },
    "chimera_dossier": {
        "name": "CHIMERA Dossier",
        "description": "Gain +5 to all skill checks vs CHIMERA systems (per rank).",
        "max_rank": 4,
        "cost_per_rank": [18, 36, 58, 85],
        "icon": "📁",
        "lore": "Know your enemy. Outlast your enemy. Become what hunts you.",
        "effect_per_rank": 5,
    },
    "eternal_root": {
        "name": "Eternal Root",
        "description": "Begin each run with root access already established.",
        "max_rank": 1,
        "cost_per_rank": [100],
        "icon": "🔑",
        "lore": "They cannot lock a door that doesn't remember closing.",
        "effect_per_rank": 1,
    },
    "dead_reckoning": {
        "name": "Dead Reckoning",
        "description": "On permadeath runs, keep 5% of your XP as bonus starting XP (per rank).",
        "max_rank": 5,
        "cost_per_rank": [25, 50, 80, 120, 170],
        "icon": "🧭",
        "lore": "The dead know where they've been.",
        "effect_per_rank": 0.05,
    },
}

# ---------------------------------------------------------------------------
# PP Calculation
# ---------------------------------------------------------------------------

def calculate_pp(gs_snapshot: Dict[str, Any]) -> int:
    """
    Calculate Prestige Points earned from a run based on final state.
    Formula: floor(level^1.5 + XP/200 + story_beats*2 + commands_run/50)
    Minimum: 1 PP per run.
    """
    level = gs_snapshot.get("level", 1)
    xp = gs_snapshot.get("xp", 0) + (level - 1) * 100
    beats = len(gs_snapshot.get("story_beats", []))
    commands = gs_snapshot.get("commands_run", 0)

    pp = math.floor(
        level ** 1.5
        + xp / 200
        + beats * 2
        + commands / 50
    )
    return max(1, pp)


# ---------------------------------------------------------------------------
# Prestige Engine
# ---------------------------------------------------------------------------

class PrestigeEngine:
    """Manages permadeath mode, rebirth, and permanent upgrades."""

    def _get_prestige(self, flags: dict) -> dict:
        if "prestige" not in flags:
            flags["prestige"] = {"pp": 0, "spent_pp": 0, "upgrades": {}, "total_rebirths": 0}
        return flags["prestige"]

    def get_upgrade_rank(self, flags: dict, upgrade_id: str) -> int:
        p = self._get_prestige(flags)
        return p["upgrades"].get(upgrade_id, 0)

    def buy_upgrade(self, upgrade_id: str, flags: dict) -> List[dict]:
        defn = PRESTIGE_UPGRADES.get(upgrade_id)
        if not defn:
            available = ", ".join(PRESTIGE_UPGRADES.keys())
            return [{"t": "error", "s": f"  Unknown upgrade '{upgrade_id}'. Available: {available}"}]

        p = self._get_prestige(flags)
        current_rank = p["upgrades"].get(upgrade_id, 0)
        max_rank = defn["max_rank"]

        if current_rank >= max_rank:
            return [{"t": "warn", "s": f"  {defn['icon']} {defn['name']} is already at MAX rank ({max_rank})."}]

        cost = defn["cost_per_rank"][current_rank]
        if p["pp"] < cost:
            return [{"t": "error", "s": f"  Not enough Prestige Points. Need {cost} PP, have {p['pp']} PP."}]

        p["pp"] -= cost
        p["spent_pp"] = p.get("spent_pp", 0) + cost
        p["upgrades"][upgrade_id] = current_rank + 1

        new_rank = current_rank + 1
        return [
            {"t": "success", "s": f"  {defn['icon']} {defn['name']} upgraded to Rank {new_rank}/{max_rank}"},
            {"t": "dim", "s": f"  {defn['description']}"},
            {"t": "lore", "s": f"  '{defn['lore']}'"},
            {"t": "dim", "s": f"  Remaining PP: {p['pp']}"},
        ]

    def rebirth(self, gs, force: bool = False) -> List[dict]:
        """
        Sacrifice current run for Prestige Points.
        Returns output list + modifies gs.flags["prestige"].
        Does NOT reset game state (caller must handle that).
        """
        snapshot = {
            "level": gs.level,
            "xp": gs.xp,
            "story_beats": list(gs.story_beats),
            "commands_run": getattr(gs, "commands_run", 0),
        }
        pp_earned = calculate_pp(snapshot)
        p = self._get_prestige(gs.flags)
        p["pp"] = p.get("pp", 0) + pp_earned
        p["total_rebirths"] = p.get("total_rebirths", 0) + 1

        out = [
            {"t": "system", "s": "  ═══ GHOST PROTOCOL: REBIRTH SEQUENCE ═══"},
            {"t": "dim", "s": ""},
            {"t": "lore", "s": "  Ghost fragments. The terminal goes dark. A new session begins."},
            {"t": "dim", "s": ""},
            {"t": "success", "s": f"  PRESTIGE POINTS EARNED: +{pp_earned} PP"},
            {"t": "dim", "s": f"  (Level {snapshot['level']} × {snapshot['commands_run']} commands × {len(snapshot['story_beats'])} story beats)"},
            {"t": "dim", "s": ""},
            {"t": "info", "s": f"  Total PP: {p['pp']}   Total Rebirths: {p['total_rebirths']}"},
            {"t": "dim", "s": ""},
            {"t": "dim", "s": "  Type `prestige upgrades` to spend PP on permanent bonuses."},
            {"t": "dim", "s": "  Type `prestige rebirth confirm` to start a fresh run with meta-upgrades applied."},
        ]
        return out

    def apply_prestige_effects(self, gs) -> None:
        """Apply all purchased permanent upgrades to a fresh game state."""
        p = self._get_prestige(gs.flags)
        upgrades = p.get("upgrades", {})

        # XP surge → stored as multiplier flag
        xp_rank = upgrades.get("xp_surge", 0)
        if xp_rank:
            gs.flags["prestige_xp_bonus"] = 1.0 + (xp_rank * 0.10)

        # Credit cache → add starting credits
        credit_rank = upgrades.get("credit_cache", 0)
        if credit_rank:
            bonus_credits = credit_rank * 50
            gs.flags.setdefault("credits", 0)
            gs.flags["credits"] = gs.flags.get("credits", 0) + bonus_credits

        # Trace ghost → lower starting trace
        trace_rank = upgrades.get("trace_ghost", 0)
        if trace_rank:
            reduction = trace_rank * 10
            gs.flags["trace_level"] = max(0, gs.flags.get("trace_level", 0) - reduction)

        # Anchor shard → bonus remnant charges
        anchor_rank = upgrades.get("anchor_shard", 0)
        if anchor_rank:
            gs.flags["remnant_charges"] = gs.flags.get("remnant_charges", 3) + anchor_rank

        # Eternal root → start with root
        if upgrades.get("eternal_root", 0):
            gs.flags["_root_shell"] = True

    def toggle_permadeath(self, flags: dict, enable: bool) -> List[dict]:
        flags["permadeath"] = enable
        if enable:
            return [
                {"t": "warn", "s": "  ⚠  PERMADEATH MODE ENABLED"},
                {"t": "dim", "s": "  Death will erase your run. Prestige meta-upgrades persist."},
                {"t": "lore", "s": "  'There is no respawn in CHIMERA's world. Only echoes.'"},
            ]
        else:
            return [
                {"t": "success", "s": "  PERMADEATH MODE DISABLED"},
                {"t": "dim", "s": "  Standard mode: death costs trace + XP penalty."},
            ]

    def render_prestige_menu(self, flags: dict) -> List[dict]:
        p = self._get_prestige(flags)
        upgrades = p.get("upgrades", {})
        permadeath = flags.get("permadeath", False)

        out = [
            {"t": "system", "s": "  ═══ PRESTIGE SYSTEM — GHOST META-PROGRESSION ═══"},
            {"t": "dim", "s": ""},
            {"t": "info", "s": f"  Prestige Points (PP): {p.get('pp', 0)}  |  Total Rebirths: {p.get('total_rebirths', 0)}"},
            {"t": "dim", "s": f"  Permadeath: {'ON ⚠' if permadeath else 'OFF'}"},
            {"t": "dim", "s": ""},
            {"t": "dim", "s": "  Permanent upgrades purchased:"},
        ]

        if not upgrades:
            out.append({"t": "dim", "s": "    (none yet — use `prestige buy <id>` to unlock)"})
        else:
            for uid, rank in upgrades.items():
                defn = PRESTIGE_UPGRADES.get(uid, {})
                icon = defn.get("icon", "★")
                name = defn.get("name", uid)
                max_rank = defn.get("max_rank", 1)
                out.append({"t": "success", "s": f"    {icon} {name:<22} Rank {rank}/{max_rank}"})

        out += [
            {"t": "dim", "s": ""},
            {"t": "dim", "s": "  prestige upgrades    — browse all permanent upgrades"},
            {"t": "dim", "s": "  prestige buy <id>    — spend PP on an upgrade"},
            {"t": "dim", "s": "  rebirth              — sacrifice this run for PP"},
            {"t": "dim", "s": "  permadeath on|off    — toggle permadeath mode"},
        ]
        return out

    def render_upgrades(self, flags: dict) -> List[dict]:
        p = self._get_prestige(flags)
        upgrades = p.get("upgrades", {})
        pp = p.get("pp", 0)

        out = [
            {"t": "system", "s": "  ═══ PERMANENT UPGRADES ═══"},
            {"t": "dim", "s": f"  PP Balance: {pp}"},
            {"t": "dim", "s": ""},
        ]
        for uid, defn in PRESTIGE_UPGRADES.items():
            rank = upgrades.get(uid, 0)
            max_rank = defn["max_rank"]
            icon = defn["icon"]
            name = defn["name"]
            if rank < max_rank:
                next_cost = defn["cost_per_rank"][rank]
                affordable = "✓" if pp >= next_cost else "✗"
                rank_str = f"Rank {rank}/{max_rank}"
                cost_str = f"Next rank: {next_cost} PP {affordable}"
            else:
                rank_str = "MAX"
                cost_str = ""
            color = "success" if rank > 0 else "dim"
            out.append({"t": color, "s": f"  {icon} {uid:<22} {rank_str:<12} {cost_str}"})
            out.append({"t": "dim",  "s": f"       {defn['description']}"})
        return out


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: Optional[PrestigeEngine] = None


def get_engine() -> PrestigeEngine:
    global _engine
    if _engine is None:
        _engine = PrestigeEngine()
    return _engine


if __name__ == "__main__":
    # Quick smoke test
    class _FakeGS:
        level = 8
        xp = 450
        story_beats = {"first_hack", "root_gained", "ada_trusted", "mole_suspect"}
        commands_run = 237
        flags: dict = {}

    gs = _FakeGS()
    eng = PrestigeEngine()

    print("PP for run:", calculate_pp({"level": gs.level, "xp": gs.xp,
        "story_beats": gs.story_beats, "commands_run": gs.commands_run}))

    out = eng.rebirth(gs)
    for x in out:
        print(f"[{x['t']}] {x['s']}")

    out2 = eng.buy_upgrade("xp_surge", gs.flags)
    for x in out2:
        print(f"[{x['t']}] {x['s']}")

    out3 = eng.render_prestige_menu(gs.flags)
    for x in out3:
        print(f"[{x['t']}] {x['s']}")
