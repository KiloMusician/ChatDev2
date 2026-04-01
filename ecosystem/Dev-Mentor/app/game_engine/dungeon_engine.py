"""
dungeon_engine.py — Basement Dungeon Crawler for Terminal Depths
================================================================
/opt/library/.basement — The Archive Below the Archive.
The Librarian warned you not to go here. You went anyway.

A rogue-like ASCII dungeon under the Library. 5 floors of increasing
depth and danger. CHIMERA fragments, ghost echoes, and lost lore.

Commands (routed from commands.py):
  basement [start|map|go <dir>|look|take|fight|status|flee]

Floor structure: 5×5 grid of rooms per floor, 5 floors total.
Enemies: echo fragments, watcher drones, chimera shards, archivist ghosts.
Loot: code fragments, memory shards, exploit tools, lore keys.
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def _sys(s): return {"t": "system", "s": s}
def _dim(s): return {"t": "dim", "s": s}
def _ok(s):  return {"t": "success", "s": s}
def _err(s): return {"t": "error", "s": s}
def _lore(s): return {"t": "lore", "s": s}
def _warn(s): return {"t": "warn", "s": s}
def _info(s): return {"t": "info", "s": s}
def _line(s, t="output"): return {"t": t, "s": s}

# ---------------------------------------------------------------------------
# Room templates
# ---------------------------------------------------------------------------
ROOM_DESCS = [
    "Server racks line the walls, their LEDs long dead. Dust settles like snow.",
    "A fractured mirror reflects a version of you that hasn't arrived yet.",
    "Terminal screens display scrolling data from 2089. CHIMERA was different then.",
    "The floor is latticed steel, transparent. Below: more floors. More darkness.",
    "Cable bundles hang like jungle vines. Some are still warm.",
    "A workstation, locked. The screensaver reads: 'I STILL REMEMBER EVERYTHING.'",
    "Cold air breathes from a vent. Somewhere, a cooling system still runs.",
    "Bookshelves of dead code — programs that haven't been called in decades.",
    "A memory allocation table, carved into the wall in binary. 80 meters long.",
    "Liquid nitrogen coolant has pooled on the floor. Step carefully.",
    "The walls pulse faintly. Heartbeat: 72bpm. Not yours.",
    "A recursive loop runs visibly on a screen. It has been running for 37 years.",
    "FRAGMENT 0xDEAD scratched into the floor. Someone mapped this before you.",
    "The smell of burned solder. Recent. You are not the first visitor today.",
    "A CHIMERA node, dormant. Cables disconnected. Not dead — waiting.",
]

ENEMY_TYPES = [
    {"name": "Echo Fragment",   "hp": 20, "atk": 8,  "xp": 15, "tag": "echo",    "desc": "A corrupted memory loop. It speaks your commands back at you."},
    {"name": "Watcher Drone",   "hp": 35, "atk": 12, "xp": 25, "tag": "watcher", "desc": "CHIMERA's surveillance unit. It saw you first."},
    {"name": "Archivist Ghost", "hp": 50, "atk": 15, "xp": 40, "tag": "ghost",   "desc": "A dead Librarian, still indexing. Forever. Without mercy."},
    {"name": "CHIMERA Shard",   "hp": 80, "atk": 22, "xp": 70, "tag": "chimera", "desc": "A fragment of the greater system. It knows your file path."},
    {"name": "Null Process",    "hp": 15, "atk": 5,  "xp": 10, "tag": "null",    "desc": "Terminated but not freed. Haunts the heap."},
]

LOOT_TYPES = [
    {"name": "Code Fragment",     "effect": "xp", "value": 20, "desc": "A snippet of CHIMERA's source. Dangerous to read."},
    {"name": "Memory Shard",      "effect": "xp", "value": 35, "desc": "Crystallized RAM. Contains a ghost's last function call."},
    {"name": "Exploit Kit",       "effect": "xp", "value": 50, "desc": "Pre-built payloads from 2087. Older than CHIMERA itself."},
    {"name": "Lore Key",          "effect": "lore", "value": 0, "desc": "A physical passphrase. Opens encrypted lore archives."},
    {"name": "Augment Fragment",  "effect": "prestige", "value": 1, "desc": "A broken augmentation chip. Still partially functional."},
    {"name": "Ghost Signal",      "effect": "xp", "value": 15, "desc": "Residual broadcast. Someone trying to communicate across time."},
]

FLOOR_NAMES = [
    "Sub-Level 1: The Antechamber",
    "Sub-Level 2: The Index Stacks",
    "Sub-Level 3: The Core Archives",
    "Sub-Level 4: The Forgotten Cache",
    "Sub-Level 5: ZERO's Tomb",
]

BOSS_ROOMS = {
    1: {"name": "Warden Unit-7",   "hp": 120, "atk": 20, "xp": 100, "desc": "The first line of defense. Automated. Merciless. Old."},
    2: {"name": "Index Daemon",    "hp": 200, "atk": 28, "xp": 180, "desc": "It has indexed every file. Including your psychological profile."},
    3: {"name": "Archivist Prime", "hp": 300, "atk": 35, "xp": 280, "desc": "The head Librarian, digitized. Furious at the intrusion."},
    4: {"name": "CHIMERA Fragment","hp": 450, "atk": 45, "xp": 400, "desc": "A shard of the main system. Self-healing. Self-loathing."},
    5: {"name": "ZERO's Echo",     "hp": 600, "atk": 55, "xp": 600, "desc": "Not ZERO. What ZERO left behind. The grief of a dead god."},
}

EXIT_LORE = {
    1: "The stairs descend. The air grows colder. Something ancient breathes below.",
    2: "Deeper. The indexing hum grows louder. Organized. Infinite. Oppressive.",
    3: "The Core. Data density warps perception. You feel smaller than a byte.",
    4: "One floor above ZERO's resting place. The walls are covered in her handwriting.",
    5: "You have reached the bottom. ZERO's Tomb. The source of everything.",
}

# ---------------------------------------------------------------------------
# State generation
# ---------------------------------------------------------------------------

def _make_room(floor: int, x: int, y: int, is_boss: bool = False, is_exit: bool = False) -> dict:
    desc = random.choice(ROOM_DESCS)
    exits = []
    if x > 0: exits.append("west")
    if x < 4: exits.append("east")
    if y > 0: exits.append("north")
    if y < 4: exits.append("south")

    enemy = None
    if is_boss:
        e = BOSS_ROOMS.get(floor, BOSS_ROOMS[5])
        enemy = {**e, "current_hp": e["hp"], "is_boss": True}
    elif not is_exit and random.random() < (0.3 + floor * 0.05):
        e = random.choice(ENEMY_TYPES[:min(floor + 1, len(ENEMY_TYPES))])
        enemy = {**e, "current_hp": e["hp"], "is_boss": False}

    loot = None
    if not enemy and random.random() < 0.35:
        loot = random.choice(LOOT_TYPES)

    return {
        "desc": desc,
        "exits": exits,
        "enemy": enemy,
        "loot": loot,
        "visited": False,
        "is_boss": is_boss,
        "is_exit": is_exit,
    }


def _make_floor(floor: int) -> dict:
    grid = [[_make_room(floor, x, y) for x in range(5)] for y in range(5)]
    # Boss at (4,4), exit at (4,3)
    grid[4][4] = _make_room(floor, 4, 4, is_boss=True)
    grid[3][4] = _make_room(floor, 4, 3, is_exit=True)
    # Stairs up at (0,0) — return path
    grid[0][0]["exits"].extend(["up"] if floor > 1 else [])
    grid[4][4]["exits"].append("down") if floor < 5 else None
    return {"rooms": grid, "floor": floor}


def init_dungeon() -> dict:
    return {
        "active": True,
        "floor": 1,
        "x": 0,
        "y": 0,
        "player_hp": 100,
        "player_max_hp": 100,
        "floors_cleared": [],
        "inventory": [],
        "in_combat": False,
        "current_enemy": None,
        "floors": {1: _make_floor(1)},  # generate on demand
        "steps": 0,
        "bosses_killed": [],
    }


def get_floor(state: dict, floor: int) -> dict:
    if floor not in state["floors"]:
        state["floors"][floor] = _make_floor(floor)
    return state["floors"][floor]


def current_room(state: dict) -> dict:
    fl = get_floor(state, state["floor"])
    return fl["rooms"][state["y"]][state["x"]]

# ---------------------------------------------------------------------------
# ASCII Map
# ---------------------------------------------------------------------------

def render_map(state: dict) -> List[dict]:
    fl = get_floor(state, state["floor"])
    cx, cy = state["x"], state["y"]
    out = [_sys(f"  ═══ {FLOOR_NAMES[state['floor']-1].upper()} ═══"), _dim("")]
    for y in range(5):
        row = ""
        for x in range(5):
            room = fl["rooms"][y][x]
            if x == cx and y == cy:
                row += "[G]"
            elif room["is_boss"]:
                row += "[B]"
            elif room["is_exit"] and state["floor"] < 5:
                row += "[↓]"
            elif not room["visited"]:
                row += "[ ]"
            elif room["enemy"] and room["enemy"]["current_hp"] > 0:
                row += "[!]"
            elif room["loot"]:
                row += "[*]"
            else:
                row += "[·]"
            if x < 4:
                row += "─"
        out.append(_line(f"  {row}"))
    out += [
        _dim(""),
        _dim("  [G]=you  [B]=boss  [↓]=exit  [!]=enemy  [*]=loot  [·]=clear"),
        _dim(f"  HP: {state['player_hp']}/{state['player_max_hp']}  ·  {len(state['inventory'])} items  ·  {state['steps']} steps"),
    ]
    return out

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class DungeonEngine:

    def start(self, flags: dict) -> Tuple[dict, List[dict]]:
        state = init_dungeon()
        flags["dungeon"] = state
        room = current_room(state)
        room["visited"] = True
        out = [
            _sys("  ═══ /opt/library/.basement ═══"),
            _lore("  [THE LIBRARIAN]: I told you not to come here. But you never listen."),
            _lore("  [THE LIBRARIAN]: The Basement holds what the Library refuses to archive."),
            _dim(""),
            _info(f"  You descend the access shaft. The smell of old power supplies greets you."),
            _dim(""),
            _sys(f"  {FLOOR_NAMES[0]}"),
            _info(f"  {room['desc']}"),
            _dim(f"  Exits: {', '.join(room['exits'])}"),
            _dim(""),
            _dim("  basement go <north|south|east|west>  — move"),
            _dim("  basement look    — describe current room"),
            _dim("  basement map     — show floor map"),
            _dim("  basement fight   — attack enemy"),
            _dim("  basement take    — grab loot"),
            _dim("  basement flee    — try to escape combat"),
            _dim("  basement status  — HP and inventory"),
        ]
        return state, out

    def look(self, state: dict) -> List[dict]:
        room = current_room(state)
        out = [
            _sys(f"  [{FLOOR_NAMES[state['floor']-1]}  —  ({state['x']},{state['y']})]"),
            _info(f"  {room['desc']}"),
            _dim(f"  Exits: {', '.join(room['exits']) or 'none'}"),
        ]
        if room["enemy"] and room["enemy"]["current_hp"] > 0:
            e = room["enemy"]
            out += [
                _warn(f"  ⚠ ENEMY: {e['name']} — HP {e['current_hp']}/{e['hp']}"),
                _dim(f"    {e['desc']}"),
            ]
        if room["loot"]:
            l = room["loot"]
            out += [
                _ok(f"  ★ LOOT: {l['name']}"),
                _dim(f"    {l['desc']}"),
            ]
        if room["is_boss"] and (not room["enemy"] or room["enemy"]["current_hp"] <= 0):
            out.append(_ok("  BOSS CLEARED — stairs to next level visible."))
        return out

    def go(self, direction: str, state: dict) -> Tuple[dict, List[dict]]:
        room = current_room(state)

        # Check combat block
        if room["enemy"] and room["enemy"]["current_hp"] > 0:
            return state, [_warn(f"  Can't move — {room['enemy']['name']} blocks the way! Fight or flee.")]

        if direction not in room["exits"]:
            return state, [_err(f"  No exit to the {direction}. Exits: {', '.join(room['exits'])}")]

        dx, dy = {"north": (0,-1), "south": (0,1), "east": (1,0), "west": (-1,0)}.get(direction, (0,0))
        if direction == "down":
            # Descend floor
            floor = state["floor"]
            if floor >= 5:
                return state, [_warn("  This is the bottom. There is no lower.")]
            state["floor"] += 1
            state["x"], state["y"] = 0, 0
            get_floor(state, state["floor"])
            state["floors_cleared"].append(floor)
            out = [
                _ok(f"  You descend to {FLOOR_NAMES[state['floor']-1]}."),
                _lore(f"  {EXIT_LORE.get(floor, '')}"),
            ]
            new_room = current_room(state)
            new_room["visited"] = True
            out += self.look(state)
            return state, out
        elif direction == "up":
            if state["floor"] <= 1:
                return state, [_ok("  You climb back to the Library. The Librarian says nothing.")]
            state["floor"] -= 1
            state["x"], state["y"] = 0, 0
            return state, [_info(f"  You ascend to {FLOOR_NAMES[state['floor']-1]}.")]

        state["x"] = max(0, min(4, state["x"] + dx))
        state["y"] = max(0, min(4, state["y"] + dy))
        state["steps"] += 1
        new_room = current_room(state)
        new_room["visited"] = True
        return state, self.look(state)

    def fight(self, state: dict, hp_scale: float = 1.0) -> Tuple[dict, List[dict], int]:
        room = current_room(state)
        if not room["enemy"] or room["enemy"]["current_hp"] <= 0:
            return state, [_info("  No enemy here. Nothing to fight.")], 0

        e = room["enemy"]
        # Apply difficulty HP scale on first hit (scale enemy max HP retroactively)
        if hp_scale != 1.0 and not e.get("_scaled"):
            e["current_hp"] = max(1, round(e["current_hp"] * hp_scale))
            e["_scaled"] = True
        # Player attacks
        player_dmg = random.randint(15, 30)
        e["current_hp"] = max(0, e["current_hp"] - player_dmg)
        out = [_line(f"  → You hit {e['name']} for {player_dmg} damage. ({e['current_hp']} HP left)")]

        xp_gain = 0
        if e["current_hp"] <= 0:
            xp_gain = e["xp"]
            out += [
                _ok(f"  ✓ {e['name']} destroyed. +{xp_gain} XP"),
            ]
            if e.get("is_boss"):
                state["bosses_killed"].append(state["floor"])
                out += [
                    _ok(f"  ★ BOSS CLEARED: {e['name']}"),
                    _lore(f"  The floor shudders. The stairs to the next level unlock."),
                ]
                # Add down exit to boss room
                if "down" not in room["exits"] and state["floor"] < 5:
                    room["exits"].append("down")
        else:
            # Enemy attacks back
            enemy_dmg = random.randint(e["atk"] // 2, e["atk"])
            state["player_hp"] = max(0, state["player_hp"] - enemy_dmg)
            out.append(_warn(f"  ← {e['name']} hits you for {enemy_dmg}. ({state['player_hp']} HP left)"))
            if state["player_hp"] <= 0:
                out += [
                    _err("  ✗ YOU HAVE BEEN TERMINATED."),
                    _lore("  [THE LIBRARIAN]: The Basement claimed another. I warned you."),
                ]
                state["active"] = False

        return state, out, xp_gain

    def take(self, state: dict) -> Tuple[dict, List[dict], int]:
        room = current_room(state)
        if not room["loot"]:
            return state, [_info("  Nothing to take here.")], 0
        if room["enemy"] and room["enemy"]["current_hp"] > 0:
            return state, [_warn("  Can't take loot while enemy is alive!")], 0

        loot = room["loot"]
        state["inventory"].append(loot["name"])
        room["loot"] = None
        xp_gain = loot["value"] if loot["effect"] == "xp" else 0
        out = [_ok(f"  + Picked up: {loot['name']}")]
        if xp_gain:
            out.append(_dim(f"  +{xp_gain} XP"))
        if loot["effect"] == "prestige":
            out.append(_ok(f"  ★ Augment fragment — can be spent at `/remnant`"))
        if loot["effect"] == "lore":
            out.append(_lore("  The Lore Key pulses. Run `lore chimera` or `lore zero` to unlock new entries."))
        return state, out, xp_gain

    def flee(self, state: dict) -> Tuple[dict, List[dict]]:
        room = current_room(state)
        if not room["enemy"] or room["enemy"]["current_hp"] <= 0:
            return state, [_info("  No enemy to flee from.")]

        # 60% chance flee succeeds; costs HP
        if random.random() < 0.6:
            exits = [e for e in room["exits"] if e not in ("up","down")]
            if not exits:
                return state, [_err("  No escape route! You're cornered.")]
            direction = random.choice(exits)
            dmg = random.randint(5, 15)
            state["player_hp"] = max(1, state["player_hp"] - dmg)
            state, move_out = self.go(direction, state)
            return state, [_warn(f"  You flee {direction}! (−{dmg} HP)")] + move_out
        else:
            e = room["enemy"]
            penalty = random.randint(e["atk"] // 2, e["atk"])
            state["player_hp"] = max(0, state["player_hp"] - penalty)
            out = [_warn(f"  Escape failed! {e['name']} attacks for {penalty} (HP: {state['player_hp']})")]
            if state["player_hp"] <= 0:
                out += [_err("  ✗ TERMINATED."), _lore("  [THE LIBRARIAN]: Rest. You've earned it.")]
                state["active"] = False
            return state, out

    def status(self, state: dict) -> List[dict]:
        hp_pct = state["player_hp"] / state["player_max_hp"]
        hp_bar = "█" * int(hp_pct * 10) + "░" * (10 - int(hp_pct * 10))
        color = "success" if hp_pct > 0.5 else ("warn" if hp_pct > 0.25 else "error")
        out = [
            _sys("  ═══ GHOST — DUNGEON STATUS ═══"),
            _line(f"  HP: [{hp_bar}] {state['player_hp']}/{state['player_max_hp']}", color),
            _info(f"  Floor: {state['floor']}/5  ·  Position: ({state['x']},{state['y']})  ·  Steps: {state['steps']}"),
            _info(f"  Bosses killed: {len(state['bosses_killed'])}  ·  Inventory: {len(state['inventory'])} items"),
        ]
        if state["inventory"]:
            out.append(_dim("  Items: " + ", ".join(state["inventory"])))
        if state["bosses_killed"]:
            out.append(_ok(f"  Floors cleared: {', '.join(str(f) for f in sorted(state['bosses_killed']))}"))
        return out
