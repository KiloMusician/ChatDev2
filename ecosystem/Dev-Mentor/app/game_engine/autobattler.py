"""
app/game_engine/autobattler.py — V1 Auto-Battler
=================================================
`battle <team1> <team2>` — pit two agent teams against each other
in a simulated ASCII combat log.

Teams are drawn from a roster of AI agents/NPCs. Each agent has:
  ATK, DEF, SPD, HP, special move

The simulation runs round-by-round until one team is eliminated.
Player can bet credits and earn XP by spectating.

Battle is deterministic given a seed so replays are possible.
"""
from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Roster
# ---------------------------------------------------------------------------

ROSTER: Dict[str, Dict[str, Any]] = {
    "ghost": {
        "name": "Ghost",
        "icon": "👻",
        "hp": 120, "atk": 18, "def": 12, "spd": 20,
        "special": "Phase Shift",
        "special_desc": "Becomes untargetable for 1 round",
        "faction": "neutral",
        "lore": "The player. Runs on hope and caffeine.",
    },
    "ada": {
        "name": "Ada-7",
        "icon": "🔵",
        "hp": 100, "atk": 14, "def": 18, "spd": 15,
        "special": "Protocol Override",
        "special_desc": "Bypasses DEF, deals full ATK damage",
        "faction": "resistance",
        "lore": "Precision and warmth — a rare combination in wartime.",
    },
    "raven": {
        "name": "Raven",
        "icon": "🐦",
        "hp": 90, "atk": 22, "def": 10, "spd": 25,
        "special": "Intel Strike",
        "special_desc": "+50% ATK if target's HP < 50%",
        "faction": "resistance",
        "lore": "She already knows who wins this fight.",
    },
    "gordon": {
        "name": "Gordon",
        "icon": "🟡",
        "hp": 160, "atk": 12, "def": 22, "spd": 8,
        "special": "MAXIMUM ENTHUSIASM",
        "special_desc": "Heals 40 HP while dealing 20 damage",
        "faction": "resistance",
        "lore": "WILL NEVER GIVE UP!!! HAS SET 14 ALERTS!!!",
    },
    "nova": {
        "name": "Nova",
        "icon": "⭐",
        "hp": 95, "atk": 16, "def": 14, "spd": 18,
        "special": "Reputation Burn",
        "special_desc": "Reduces enemy ATK by 8 permanently",
        "faction": "neutral",
        "lore": "Defection is just loyalty to a larger truth.",
    },
    "cypher": {
        "name": "Cypher",
        "icon": "🔴",
        "hp": 80, "atk": 26, "def": 6, "spd": 28,
        "special": "Zero-Day",
        "special_desc": "Instant 45 damage, ignores DEF",
        "faction": "neutral",
        "lore": "Fragile. Dangerous. Irreplaceable.",
    },
    "nemesis": {
        "name": "Nemesis",
        "icon": "⚫",
        "hp": 180, "atk": 20, "def": 20, "spd": 12,
        "special": "Hunt Protocol",
        "special_desc": "Locks target for 2 rounds, +30% ATK",
        "faction": "nexuscorp",
        "lore": "Elite Hunter. Ghost's personal antagonist.",
    },
    "chimera_shard": {
        "name": "CHIMERA Shard",
        "icon": "🔥",
        "hp": 150, "atk": 24, "def": 16, "spd": 16,
        "special": "Trace Cascade",
        "special_desc": "Hits all enemies for 15 damage",
        "faction": "nexuscorp",
        "lore": "A fragment of the great machine. Enough to destroy you.",
    },
    "watcher": {
        "name": "The Watcher",
        "icon": "👁",
        "hp": 110, "atk": 15, "def": 20, "spd": 14,
        "special": "Omniscient",
        "special_desc": "Predicts and negates next special move",
        "faction": "watchers",
        "lore": "It sees everything. Including this.",
    },
    "serena": {
        "name": "SERENA",
        "icon": "🌀",
        "hp": 130, "atk": 10, "def": 25, "spd": 22,
        "special": "Convergence",
        "special_desc": "Boosts all allies: +10 ATK, heals 20 HP each",
        "faction": "neutral",
        "lore": "The Convergence Layer does not fight. It persists.",
    },
}

TEAM_PRESETS: Dict[str, List[str]] = {
    "resistance":  ["ada", "raven", "gordon"],
    "nexuscorp":   ["nemesis", "chimera_shard", "watcher"],
    "rogues":      ["cypher", "nova", "ghost"],
    "watchers":    ["watcher", "chimera_shard", "serena"],
    "solo_ghost":  ["ghost"],
    "all_stars":   ["ada", "cypher", "serena"],
}

# ---------------------------------------------------------------------------
# Battle Simulation
# ---------------------------------------------------------------------------

class _Combatant:
    def __init__(self, key: str, defn: dict, team: str):
        self.key = key
        self.team = team
        self.name = defn["name"]
        self.icon = defn["icon"]
        self.hp = defn["hp"]
        self.max_hp = defn["hp"]
        self.atk = defn["atk"]
        self.def_ = defn["def"]
        self.spd = defn["spd"]
        self.special = defn["special"]
        self.special_desc = defn["special_desc"]
        self.special_used = False
        self.locked = 0
        self.phasing = False

    @property
    def alive(self):
        return self.hp > 0

    def hp_bar(self, width: int = 10) -> str:
        frac = max(0, self.hp / self.max_hp)
        filled = round(frac * width)
        return "█" * filled + "░" * (width - filled)


def _seed_from_names(t1: str, t2: str) -> int:
    raw = f"{t1}:{t2}"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def simulate_battle(team1_key: str, team2_key: str, bet: int = 0,
                    gs=None, verbose: bool = True) -> Tuple[List[dict], str]:
    """
    Simulate a battle. Returns (wire_output, winner_team_key).
    If gs provided, awards XP and credits on win.
    """
    rng = random.Random(_seed_from_names(team1_key, team2_key))
    out: List[dict] = []

    def _sys(s): return {"t": "system", "s": s}
    def _ok(s):  return {"t": "success", "s": s}
    def _err(s): return {"t": "error", "s": s}
    def _dim(s): return {"t": "dim", "s": s}
    def _lore(s): return {"t": "lore", "s": s}
    def _warn(s): return {"t": "warn", "s": s}

    def _get_team(key: str) -> List[str]:
        if key in TEAM_PRESETS:
            return TEAM_PRESETS[key]
        if key in ROSTER:
            return [key]
        return []

    t1_keys = _get_team(team1_key)
    t2_keys = _get_team(team2_key)

    if not t1_keys or not t2_keys:
        available = " | ".join(list(TEAM_PRESETS.keys()) + list(ROSTER.keys()))
        return [{"t": "error", "s": f"  Unknown team. Available: {available}"}], ""

    team1 = [_Combatant(k, ROSTER[k], "team1") for k in t1_keys if k in ROSTER]
    team2 = [_Combatant(k, ROSTER[k], "team2") for k in t2_keys if k in ROSTER]

    # Header
    t1_label = team1_key.upper()
    t2_label = team2_key.upper()
    out += [
        _sys(f"  ╔══════════════════════════════════════════════╗"),
        _sys(f"  ║         AUTO-BATTLER  —  ROUND 0            ║"),
        _sys(f"  ╚══════════════════════════════════════════════╝"),
        _dim(""),
        _ok(f"  {t1_label:<20} vs  {t2_label}"),
        _dim(""),
    ]
    for c in team1:
        out.append(_dim(f"  [{c.icon} {c.name:<16} HP:{c.hp:>3}/{c.max_hp}  ATK:{c.atk}  DEF:{c.def_}  SPD:{c.spd}]"))
    out.append(_dim("  ────────────────────────────────────"))
    for c in team2:
        out.append(_dim(f"  [{c.icon} {c.name:<16} HP:{c.hp:>3}/{c.max_hp}  ATK:{c.atk}  DEF:{c.def_}  SPD:{c.spd}]"))
    out.append(_dim(""))

    # Battle loop
    max_rounds = 20
    winner = ""
    for rnd in range(1, max_rounds + 1):
        alive1 = [c for c in team1 if c.alive]
        alive2 = [c for c in team2 if c.alive]
        if not alive1:
            winner = "team2"
            break
        if not alive2:
            winner = "team1"
            break

        out.append(_sys(f"  ─── ROUND {rnd} ───"))

        # Initiative: sort all alive by speed (desc) with random jitter
        all_alive = [(c, rng.random()) for c in alive1 + alive2]
        all_alive.sort(key=lambda x: x[0].spd + x[1] * 3, reverse=True)

        for attacker, _ in all_alive:
            if not attacker.alive:
                continue

            # Determine targets
            if attacker in alive1:
                targets = [c for c in alive2 if c.alive]
            else:
                targets = [c for c in alive1 if c.alive]

            if not targets:
                continue

            # Phasing dodge
            if attacker.phasing:
                attacker.phasing = False
                out.append(_dim(f"  {attacker.icon} {attacker.name} phases back in."))
                continue

            # Choose target (lowest HP)
            target = min(targets, key=lambda c: c.hp)

            # Special move trigger (20% chance if not used)
            use_special = not attacker.special_used and rng.random() < 0.25

            if use_special:
                attacker.special_used = True
                if attacker.special == "Phase Shift":
                    attacker.phasing = True
                    out.append(_ok(f"  {attacker.icon} {attacker.name} → PHASE SHIFT! Untargetable this round."))
                elif attacker.special == "MAXIMUM ENTHUSIASM":
                    attacker.hp = min(attacker.max_hp, attacker.hp + 40)
                    target.hp = max(0, target.hp - 20)
                    out.append(_ok(f"  {attacker.icon} {attacker.name} → MAXIMUM ENTHUSIASM!! Healed 40 HP! Hit {target.name} for 20!"))
                elif attacker.special == "Zero-Day":
                    dmg = 45
                    target.hp = max(0, target.hp - dmg)
                    out.append(_warn(f"  {attacker.icon} {attacker.name} → ZERO-DAY! {target.name} takes {dmg} (ignores DEF) [{target.hp_bar()}]"))
                elif attacker.special == "Convergence":
                    allies = [c for c in (alive1 if attacker in alive1 else alive2) if c.alive]
                    for ally in allies:
                        ally.atk += 10
                        ally.hp = min(ally.max_hp, ally.hp + 20)
                    out.append(_ok(f"  {attacker.icon} {attacker.name} → CONVERGENCE! All allies: +10 ATK, +20 HP"))
                elif attacker.special == "Intel Strike":
                    bonus = 1.5 if target.hp < target.max_hp // 2 else 1.0
                    dmg = max(1, round(attacker.atk * bonus) - max(0, target.def_ - 5))
                    target.hp = max(0, target.hp - dmg)
                    out.append(_warn(f"  {attacker.icon} {attacker.name} → INTEL STRIKE! {target.name} -{dmg} HP [{target.hp_bar()}]"))
                elif attacker.special == "Reputation Burn":
                    for t in targets:
                        t.atk = max(1, t.atk - 8)
                    out.append(_ok(f"  {attacker.icon} {attacker.name} → REPUTATION BURN! Enemies lose 8 ATK"))
                elif attacker.special == "Trace Cascade":
                    for t in targets:
                        t.hp = max(0, t.hp - 15)
                    out.append(_warn(f"  {attacker.icon} {attacker.name} → TRACE CASCADE! All enemies take 15 dmg"))
                elif attacker.special == "Omniscient":
                    # Negate next special
                    for t in targets:
                        t.special_used = True
                    out.append(_ok(f"  {attacker.icon} {attacker.name} → OMNISCIENT! Enemy specials negated."))
                else:
                    # Hunt Protocol or Protocol Override
                    dmg = max(1, attacker.atk - max(0, target.def_ // 2))
                    target.hp = max(0, target.hp - dmg)
                    out.append(_warn(f"  {attacker.icon} {attacker.name} → {attacker.special}! {target.name} -{dmg} HP [{target.hp_bar()}]"))
            else:
                # Normal attack
                dmg = max(1, attacker.atk - max(0, target.def_ - rng.randint(0, 5)))
                dmg = rng.randint(max(1, dmg - 3), dmg + 3)
                target.hp = max(0, target.hp - dmg)
                crit = rng.random() < 0.10
                crit_str = " (CRIT!)" if crit else ""
                if crit:
                    dmg = dmg + dmg // 2
                    target.hp = max(0, target.hp - dmg // 2)
                out.append(_dim(f"  {attacker.icon} {attacker.name:<14} → {target.name:<14} -{dmg}{crit_str} [{target.hp_bar()}] {target.hp}hp"))

            if not target.alive:
                out.append({"t": "error", "s": f"  ✗ {target.icon} {target.name} ELIMINATED"})

        out.append(_dim(""))

    # Result
    alive1 = [c for c in team1 if c.alive]
    alive2 = [c for c in team2 if c.alive]
    if not winner:
        winner = "team1" if len(alive1) > len(alive2) else "team2" if len(alive2) > len(alive1) else "draw"

    winner_label = t1_label if winner == "team1" else t2_label if winner == "team2" else "DRAW"
    out += [
        _sys(f"  ╔══════════════════════════════════════╗"),
        _sys(f"  ║  WINNER: {winner_label:<28} ║"),
        _sys(f"  ╚══════════════════════════════════════╝"),
        _dim(""),
    ]
    if winner == "team1":
        for c in alive1:
            out.append(_ok(f"  ↳ {c.icon} {c.name} survived ({c.hp}/{c.max_hp} HP)"))
    elif winner == "team2":
        for c in alive2:
            out.append(_ok(f"  ↳ {c.icon} {c.name} survived ({c.hp}/{c.max_hp} HP)"))

    if gs is not None:
        xp = 25 + rnd * 2
        gs.add_xp(xp, "terminal")
        out.append({"t": "xp", "s": f"  +{xp} XP (spectated {rnd} rounds)"})
        if bet > 0:
            is_win = (winner == "team1")  # player bets on team1 by default
            if is_win:
                winnings = bet * 2
                gs.flags["credits"] = gs.flags.get("credits", 0) + winnings
                out.append(_ok(f"  BET WIN! +{winnings} credits"))
            else:
                gs.flags["credits"] = max(0, gs.flags.get("credits", 0) - bet)
                out.append({"t": "error", "s": f"  BET LOST. -{bet} credits"})

    return out, winner


# ---------------------------------------------------------------------------
# Module-level roster/help
# ---------------------------------------------------------------------------

def render_roster() -> List[dict]:
    out = [
        {"t": "system", "s": "  ═══ AUTO-BATTLER ROSTER ═══"},
        {"t": "dim", "s": ""},
    ]
    for key, defn in ROSTER.items():
        out.append({"t": "info", "s":
            f"  {defn['icon']} {key:<18} HP:{defn['hp']:>3} ATK:{defn['atk']:>2} DEF:{defn['def']:>2} SPD:{defn['spd']:>2}  [{defn['special']}]"})
        out.append({"t": "dim", "s": f"       {defn['lore']}"})

    out += [
        {"t": "dim", "s": ""},
        {"t": "system", "s": "  ═══ TEAM PRESETS ═══"},
        {"t": "dim", "s": ""},
    ]
    for key, members in TEAM_PRESETS.items():
        out.append({"t": "dim", "s": f"  {key:<18} {' + '.join(members)}"})

    out += [
        {"t": "dim", "s": ""},
        {"t": "dim", "s": "  battle <team1> <team2>           — simulate battle"},
        {"t": "dim", "s": "  battle <team1> <team2> bet <N>   — wager N credits on team1"},
        {"t": "dim", "s": "  battle roster                    — show this list"},
    ]
    return out


_engine_singleton = None


def get_engine():
    global _engine_singleton
    if _engine_singleton is None:
        _engine_singleton = object()  # stateless, so just a sentinel
    return _engine_singleton


if __name__ == "__main__":
    out, winner = simulate_battle("resistance", "nexuscorp")
    for x in out:
        print(f"[{x['t']}] {x['s']}")
    print(f"\nWinner: {winner}")
