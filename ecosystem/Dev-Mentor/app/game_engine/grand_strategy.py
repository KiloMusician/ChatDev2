"""
grand_strategy.py — V8 Grand Strategy Layer for Terminal Depths
================================================================
5 factions competing for control of 10 network nodes.

Each "tick" simulates one turn of faction expansion/diplomacy.
Player interacts via:
  grand map              — ASCII faction control map
  grand balance          — influence bar chart
  grand tick             — simulate one turn
  grand claim <n> <f>    — capture node-N for faction F
  grand diplomacy <f1> <f2> treaty|war  — declare a treaty or war

Lore hook: The NexusCorp / Resistance war for the Lattice.
The Shadow Council moves in the dark. The Watcher's Circle watches.
The Specialist Guild sells to the highest bidder.
"""
from __future__ import annotations

import random
from copy import deepcopy
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Output helpers (mirrors commands.py style — single-dict returns)
# ---------------------------------------------------------------------------

def _sys(s: str)  -> Dict: return {"t": "system",  "s": s}
def _dim(s: str)  -> Dict: return {"t": "dim",     "s": s}
def _ok(s: str)   -> Dict: return {"t": "success", "s": s}
def _err(s: str)  -> Dict: return {"t": "error",   "s": s}
def _warn(s: str) -> Dict: return {"t": "warn",    "s": s}
def _info(s: str) -> Dict: return {"t": "info",    "s": s}
def _lore(s: str) -> Dict: return {"t": "lore",    "s": s}
def _line(s: str, t: str = "output") -> Dict: return {"t": t, "s": s}


# ---------------------------------------------------------------------------
# Static data
# ---------------------------------------------------------------------------

FACTION_META: Dict[str, Dict] = {
    "resistance": {
        "display": "Resistance",
        "symbol": "R",
        "color": "cyan",
        "aggression": 0.3,
        "base_influence": 40,
        "lore": "Freedom fighters holding the old net against corporate encroachment.",
    },
    "nexuscorp": {
        "display": "NexusCorp",
        "symbol": "N",
        "color": "red",
        "aggression": 0.6,
        "base_influence": 60,
        "lore": "The dominant megacorp. Money buys nodes.",
    },
    "shadow_council": {
        "display": "Shadow Council",
        "symbol": "S",
        "color": "purple",
        "aggression": 0.5,
        "base_influence": 30,
        "lore": "Moves in silence. Prefers leverage over war.",
    },
    "watchers_circle": {
        "display": "Watcher's Circle",
        "symbol": "W",
        "color": "green",
        "aggression": 0.4,
        "base_influence": 25,
        "lore": "Ancient observers. They record, then act.",
    },
    "specialist_guild": {
        "display": "Specialist Guild",
        "symbol": "G",
        "color": "yellow",
        "aggression": 0.2,
        "base_influence": 20,
        "lore": "Mercenaries. Neutral until paid. Sometimes.",
    },
}

ALL_FACTIONS = list(FACTION_META.keys())
FACTION_ALIASES = {
    "r": "resistance", "res": "resistance",
    "n": "nexuscorp",  "nex": "nexuscorp", "corp": "nexuscorp",
    "s": "shadow_council", "shadow": "shadow_council", "sc": "shadow_council",
    "w": "watchers_circle", "watcher": "watchers_circle", "wc": "watchers_circle",
    "g": "specialist_guild", "guild": "specialist_guild", "sg": "specialist_guild",
}

# 10 network nodes in a loose 2-row grid topology (5×2)
# Adjacency: node-N is adjacent to N-1, N+1, and the node directly above/below
# Row 0: nodes 1-5  |  Row 1: nodes 6-10
NODE_COUNT = 10
_NODE_ADJACENCY: Dict[int, List[int]] = {
    1: [2, 6],
    2: [1, 3, 7],
    3: [2, 4, 8],
    4: [3, 5, 9],
    5: [4, 10],
    6: [1, 7],
    7: [2, 6, 8],
    8: [3, 7, 9],
    9: [4, 8, 10],
    10: [5, 9],
}

_INITIAL_NODE_OWNERSHIP: Dict[int, Optional[str]] = {
    1: "resistance",
    2: "resistance",
    3: None,          # contested
    4: "nexuscorp",
    5: "nexuscorp",
    6: "watchers_circle",
    7: None,          # contested
    8: "shadow_council",
    9: "specialist_guild",
    10: "nexuscorp",
}


# ---------------------------------------------------------------------------
# State helpers — stored in gs.flags["grand_strategy"]
# ---------------------------------------------------------------------------

def _default_state() -> Dict:
    return {
        "nodes": dict(_INITIAL_NODE_OWNERSHIP),          # {node_id: faction|None}
        "influence": {k: v["base_influence"] for k, v in FACTION_META.items()},
        "treaties": [],     # list of (f1, f2) tuples serialised as lists
        "wars": [],         # list of (f1, f2) tuples serialised as lists
        "turn": 0,
    }


def _get_state(flags: Dict) -> Dict:
    if "grand_strategy" not in flags:
        flags["grand_strategy"] = _default_state()
    return flags["grand_strategy"]


def _resolve_faction(name: str) -> Optional[str]:
    n = name.lower().strip()
    if n in FACTION_META:
        return n
    return FACTION_ALIASES.get(n)


def _faction_nodes(state: Dict) -> Dict[str, List[int]]:
    result: Dict[str, List[int]] = {f: [] for f in ALL_FACTIONS}
    result["neutral"] = []
    for node_id, owner in state["nodes"].items():
        if owner and owner in result:
            result[owner].append(int(node_id))
        else:
            result["neutral"].append(int(node_id))
    return result


def _in_treaty(state: Dict, f1: str, f2: str) -> bool:
    pair = sorted([f1, f2])
    return pair in [sorted(t) for t in state["treaties"]]


def _in_war(state: Dict, f1: str, f2: str) -> bool:
    pair = sorted([f1, f2])
    return pair in [sorted(w) for w in state["wars"]]


# ---------------------------------------------------------------------------
# GrandStrategy class
# ---------------------------------------------------------------------------

class GrandStrategy:
    """Faction control and diplomacy engine."""

    # ── Tick ──────────────────────────────────────────────────────────────

    def tick(self, gs, flags: Dict) -> List[Dict]:
        """Simulate one grand-strategy turn. Factions expand/contract."""
        state = _get_state(flags)
        state["turn"] += 1
        turn = state["turn"]

        out: List[Dict] = [
            _sys(f"  [GRAND STRATEGY] Turn {turn} — Faction expansion in progress..."),
            _dim("  ─────────────────────────────────────────────────────────"),
        ]

        fn = _faction_nodes(state)
        events: List[str] = []

        # Shuffle faction order each turn for fairness
        faction_order = random.sample(ALL_FACTIONS, len(ALL_FACTIONS))

        for attacker in faction_order:
            a_meta = FACTION_META[attacker]
            aggression = a_meta["aggression"]

            # Only expand if random roll beats (1 - aggression)
            if random.random() > aggression:
                continue

            my_nodes = fn.get(attacker, [])
            if not my_nodes:
                continue

            # Find adjacent enemy or neutral nodes
            candidates: List[Tuple[int, Optional[str]]] = []
            for n in my_nodes:
                for adj in _NODE_ADJACENCY.get(n, []):
                    owner = state["nodes"].get(adj)
                    if owner != attacker:
                        # Skip if treaty exists between attacker and owner
                        if owner and _in_treaty(state, attacker, owner):
                            continue
                        candidates.append((adj, owner))

            if not candidates:
                continue

            # Pick a target node — prefer neutral, then weakest
            neutral_cands = [(n, o) for n, o in candidates if o is None]
            hostile_cands = [(n, o) for n, o in candidates if o is not None]

            target_node, target_owner = (
                random.choice(neutral_cands) if neutral_cands
                else random.choice(hostile_cands)
            )

            # Capture chance: attacker influence vs defender influence
            atk_inf = state["influence"].get(attacker, 20)
            if target_owner:
                def_inf = state["influence"].get(target_owner, 20)
                capture_prob = atk_inf / (atk_inf + def_inf)
            else:
                capture_prob = 0.75  # neutrals are easier

            if random.random() < capture_prob:
                state["nodes"][target_node] = attacker
                fn[attacker].append(target_node)
                if target_owner:
                    fn[target_owner].remove(target_node)
                    # Attacker gains influence; defender loses
                    state["influence"][attacker] = min(100, atk_inf + 3)
                    state["influence"][target_owner] = max(5, def_inf - 3)
                    events.append(
                        f"  {a_meta['symbol']}:{a_meta['display']} seizes node-{target_node} from "
                        f"{FACTION_META[target_owner]['display']}"
                    )
                    # If war exists, flag it
                    if _in_war(state, attacker, target_owner):
                        events[-1] += " [WAR ACTION]"
                else:
                    state["influence"][attacker] = min(100, atk_inf + 1)
                    events.append(
                        f"  {a_meta['symbol']}:{a_meta['display']} claims neutral node-{target_node}"
                    )

        if events:
            for e in events:
                out.append(_info(e))
        else:
            out.append(_dim("  A quiet turn — no node changes."))

        # Status summary
        fn2 = _faction_nodes(state)
        out.append(_dim("  ─────────────────────────────────────────────────────────"))
        for f in ALL_FACTIONS:
            nodes = fn2.get(f, [])
            meta = FACTION_META[f]
            out.append(_dim(
                f"  [{meta['symbol']}] {meta['display']:20s} nodes: {len(nodes):2d}  "
                f"influence: {state['influence'][f]:3d}"
            ))
        out.append(_dim(f"  [?] Neutral                 nodes: {len(fn2.get('neutral', []))}"))

        return out

    # ── Render map ────────────────────────────────────────────────────────

    def render_map(self, flags: Dict) -> List[Dict]:
        """ASCII faction control map — 2-row × 5-col grid."""
        state = _get_state(flags)

        def _cell(node_id: int) -> str:
            owner = state["nodes"].get(node_id)
            if owner:
                sym = FACTION_META[owner]["symbol"]
            else:
                sym = "·"
            return f"[{node_id:02d}:{sym}]"

        # Row layout: top row 1-5, bottom row 6-10
        row1 = "  " + "──".join(_cell(n) for n in range(1, 6))
        row2 = "  " + "──".join(_cell(n) for n in range(6, 11))
        col_links = "  " + "  |    |    |    |    |  "

        out: List[Dict] = [
            _sys("  ╔══════════════════════════════════════════════╗"),
            _sys("  ║        LATTICE NETWORK — FACTION MAP         ║"),
            _sys(f"  ║  Turn {state['turn']:3d}                                  ║"),
            _sys("  ╚══════════════════════════════════════════════╝"),
            _dim(""),
            _info(row1),
            _dim(col_links),
            _info(row2),
            _dim(""),
            _dim("  Legend:"),
        ]
        for f, meta in FACTION_META.items():
            nodes = [n for n, o in state["nodes"].items() if o == f]
            out.append(_dim(f"    [{meta['symbol']}] {meta['display']:20s} → nodes {sorted(nodes)}"))
        out.append(_dim("    [·] Neutral / Contested"))

        # Diplomacy status
        if state["treaties"] or state["wars"]:
            out.append(_dim(""))
            out.append(_dim("  Diplomacy:"))
            for t in state["treaties"]:
                f1, f2 = t
                out.append(_info(f"    TREATY  {FACTION_META[f1]['display']} ↔ {FACTION_META[f2]['display']}"))
            for w in state["wars"]:
                f1, f2 = w
                out.append(_warn(f"    WAR     {FACTION_META[f1]['display']} ✗ {FACTION_META[f2]['display']}"))

        out.append(_dim(""))
        out.append(_dim("  Commands: grand tick · grand balance · grand claim <node> <faction>"))
        out.append(_dim("            grand diplomacy <f1> <f2> treaty|war"))
        return out

    # ── Balance of power ─────────────────────────────────────────────────

    def render_balance_of_power(self, flags: Dict) -> List[Dict]:
        """Influence bar chart for all factions."""
        state = _get_state(flags)
        fn = _faction_nodes(state)
        max_inf = max(state["influence"].values()) or 1

        out: List[Dict] = [
            _sys("  ═══ BALANCE OF POWER ═══"),
            _dim(f"  Turn {state['turn']}"),
            _dim(""),
        ]

        for f in ALL_FACTIONS:
            meta = FACTION_META[f]
            inf = state["influence"].get(f, 0)
            nodes = len(fn.get(f, []))
            bar_len = int(inf / 100 * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            out.append(_info(
                f"  [{meta['symbol']}] {meta['display']:20s} [{bar}] {inf:3d}  nodes:{nodes}"
            ))

        neutral_count = len(fn.get("neutral", []))
        out.append(_dim(f"\n  Neutral nodes: {neutral_count} / {NODE_COUNT}"))

        total_inf = sum(state["influence"].values())
        out.append(_dim(""))
        out.append(_dim("  Share of influence:"))
        for f in ALL_FACTIONS:
            meta = FACTION_META[f]
            pct = state["influence"].get(f, 0) / total_inf * 100
            out.append(_dim(f"    {meta['display']:20s} {pct:5.1f}%"))

        return out

    # ── Diplomacy ─────────────────────────────────────────────────────────

    def diplomacy(self, faction1: str, faction2: str, action: str,
                  flags: Dict) -> List[Dict]:
        """Declare a treaty or war between two factions."""
        state = _get_state(flags)

        f1 = _resolve_faction(faction1)
        f2 = _resolve_faction(faction2)

        if not f1:
            return [_err(f"  Unknown faction: '{faction1}'. Try: resistance nexuscorp shadow_council watchers_circle specialist_guild")]
        if not f2:
            return [_err(f"  Unknown faction: '{faction2}'. Try: resistance nexuscorp shadow_council watchers_circle specialist_guild")]
        if f1 == f2:
            return [_err("  A faction cannot have diplomacy with itself.")]

        action = action.lower().strip()
        pair = sorted([f1, f2])
        treaties = [sorted(t) for t in state["treaties"]]
        wars = [sorted(w) for w in state["wars"]]

        m1 = FACTION_META[f1]["display"]
        m2 = FACTION_META[f2]["display"]

        if action == "treaty":
            if pair in treaties:
                return [_warn(f"  {m1} and {m2} already have a treaty.")]
            # Cancel war if exists
            if pair in wars:
                state["wars"] = [w for w in state["wars"] if sorted(w) != pair]
            state["treaties"].append([f1, f2])
            return [
                _ok(f"  TREATY SIGNED: {m1} ↔ {m2}"),
                _lore(f"  [INTELLIGENCE] Diplomatic channel opened. Neither faction will attack the other's nodes."),
            ]

        elif action == "war":
            if pair in wars:
                return [_warn(f"  {m1} and {m2} are already at war.")]
            # Cancel treaty if exists
            if pair in treaties:
                state["treaties"] = [t for t in state["treaties"] if sorted(t) != pair]
            state["wars"].append([f1, f2])
            # Boost both factions' aggression for this turn via influence penalty
            state["influence"][f1] = max(5, state["influence"][f1] - 5)
            state["influence"][f2] = max(5, state["influence"][f2] - 5)
            return [
                _warn(f"  WAR DECLARED: {m1} ✗ {m2}"),
                _lore(f"  [INTELLIGENCE] Hostilities commence. Node seizures accelerate. Influence costs mount."),
            ]

        else:
            return [_err(f"  Unknown diplomacy action '{action}'. Use: treaty | war")]

    # ── Player node claim ─────────────────────────────────────────────────

    def player_claim(self, node: str, faction: str, flags: Dict, gs) -> List[Dict]:
        """Player captures a node and assigns it to a faction."""
        state = _get_state(flags)

        # Parse node id
        try:
            node_str = node.lower().replace("node-", "").replace("node", "")
            node_id = int(node_str)
        except (ValueError, AttributeError):
            return [_err(f"  Invalid node '{node}'. Use: node-1 … node-{NODE_COUNT} or just the number.")]

        if node_id < 1 or node_id > NODE_COUNT:
            return [_err(f"  Node must be between 1 and {NODE_COUNT}.")]

        f = _resolve_faction(faction)
        if not f:
            return [_err(f"  Unknown faction: '{faction}'.")]

        current_owner = state["nodes"].get(node_id)
        meta = FACTION_META[f]

        # Cost: 10 XP to claim
        xp_cost = 10
        if gs.xp < xp_cost:
            return [_err(f"  Need {xp_cost} XP to claim a node. You have {gs.xp}.")]

        gs.xp -= xp_cost
        prev_display = FACTION_META[current_owner]["display"] if current_owner else "Neutral"
        state["nodes"][node_id] = f

        # Boost claimed faction's influence
        state["influence"][f] = min(100, state["influence"][f] + 5)
        if current_owner:
            state["influence"][current_owner] = max(5, state["influence"][current_owner] - 3)

        return [
            _ok(f"  NODE-{node_id} CLAIMED for {meta['display']} (was: {prev_display})"),
            _lore(f"  [INTELLIGENCE] You insert a ghost certificate. Node-{node_id} now routes through {meta['display']} infrastructure."),
            _dim(f"  Cost: {xp_cost} XP  |  Remaining: {gs.xp} XP"),
            _dim(f"  {meta['display']} influence: {state['influence'][f]}"),
        ]
