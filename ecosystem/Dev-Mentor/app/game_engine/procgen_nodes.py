"""
app/game_engine/procgen_nodes.py — RL1 Procedural Network Topology
===================================================================
Each run gets a randomly seeded network topology. Nodes are generated
deterministically from a seed so replaying the same seed reproduces the
same network (useful for daily/weekly challenges).

Node archetypes define security levels, XP rewards, and loot tables.
The network is stored in gs.flags["proc_network"] so it persists across
commands within a session.

Wire format compatible: all public methods return List[dict] with t/s keys.
"""
from __future__ import annotations

import random
import time
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Archetype definitions
# ---------------------------------------------------------------------------

NODE_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "relay": {
        "label": "RELAY",
        "icon": "◈",
        "color_hint": "dim",
        "security_level": (1, 2),
        "xp_on_discover": 10,
        "loot_table": [
            ("data", 1, 5),
            ("credits", 5, 20),
        ],
        "flavor": [
            "A public routing node. Unguarded — almost too easy.",
            "Packet traffic hums through ancient copper. No one watches the watchers.",
            "Relay node: high throughput, low intelligence. Easy pickings.",
        ],
    },
    "corporate": {
        "label": "CORPORATE",
        "icon": "◉",
        "color_hint": "warn",
        "security_level": (3, 5),
        "xp_on_discover": 25,
        "loot_table": [
            ("credits", 30, 150),
            ("data", 5, 15),
            ("keycard", 0, 1),
        ],
        "flavor": [
            "NexusCorp subnet. Automated threat detection. Proceed carefully.",
            "Corporate firewall hums with algorithmic suspicion. Watch your trace.",
            "A cathedral of data — proprietary, profitable, and paranoid.",
        ],
    },
    "research": {
        "label": "RESEARCH",
        "icon": "◎",
        "color_hint": "info",
        "security_level": (4, 7),
        "xp_on_discover": 40,
        "loot_table": [
            ("data", 20, 60),
            ("schematics", 1, 3),
            ("credits", 10, 40),
        ],
        "flavor": [
            "Academic cluster. High encryption, higher knowledge density.",
            "Forgotten research node. CHIMERA test logs still live here.",
            "PhD-level security. The experiments never stopped — they just moved underground.",
        ],
    },
    "black_market": {
        "label": "BLACK MKT",
        "icon": "◆",
        "color_hint": "success",
        "security_level": (2, 4),
        "xp_on_discover": 20,
        "loot_table": [
            ("components", 1, 4),
            ("credits", 20, 80),
            ("exploit_kit", 0, 1),
        ],
        "flavor": [
            "No logs. No records. No names. Welcome to the bazaar.",
            "Encrypted darknet hub. Transactions in ghost-coin only.",
            "What happens here stays here — including your trace signature.",
        ],
    },
    "watcher_outpost": {
        "label": "WATCHER",
        "icon": "◬",
        "color_hint": "error",
        "security_level": (6, 9),
        "xp_on_discover": 60,
        "loot_table": [
            ("lore_fragment", 1, 2),
            ("data", 10, 30),
        ],
        "flavor": [
            "WATCHER observation post. It already knows you are here.",
            "Hardened bastion — ice thick as corporate theology. Lore within.",
            "The Watcher sees 4,892 loops. You are loop 4,893.",
        ],
    },
    "resistance_cache": {
        "label": "RESISTANCE",
        "icon": "◇",
        "color_hint": "success",
        "security_level": (1, 3),
        "xp_on_discover": 30,
        "loot_table": [
            ("quest_item", 0, 1),
            ("data", 5, 20),
            ("credits", 10, 50),
        ],
        "flavor": [
            "Resistance safe-house node. Ada's handwriting in the config comments.",
            "Friendly node — Raven's encryption, Gordon's chaos, Ada's warmth.",
            "Cache left by ghosts who refused to stop fighting. For you.",
        ],
    },
}

# Node name prefixes and suffixes for procedural naming
_NAME_PREFIXES = [
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "sigma", "omega", "nexus", "node", "relay", "hub", "cluster", "sector",
    "axis", "pulse", "echo", "void", "arc", "cipher", "ghost", "null",
]
_NAME_SUFFIXES = [
    "prime", "zero", "one", "two", "core", "net", "link", "7", "9",
    "deep", "sub", "x", "y", "z", "mk2", "ex", "nexus", "point",
]


def _line(text: str, t: str = "info") -> dict:
    return {"t": t, "s": text}


def _ok(text: str) -> List[dict]:
    return [_line(text, "success")]


def _err(text: str) -> List[dict]:
    return [_line(text, "error")]


def _dim(text: str) -> List[dict]:
    return [_line(text, "dim")]


def _sys(text: str) -> List[dict]:
    return [_line(text, "system")]


def _lore(text: str) -> dict:
    return _line(text, "lore")


# ---------------------------------------------------------------------------
# ProceduralNetwork
# ---------------------------------------------------------------------------

class ProceduralNetwork:
    """Generates and manages a procedural node network for a session."""

    def generate(self, seed: int, node_count: int = 8) -> List[Dict[str, Any]]:
        """Generate a list of nodes deterministically from seed."""
        rng = random.Random(seed)

        archetype_keys = list(NODE_ARCHETYPES.keys())
        # Weighted archetype selection: relays more common, watcher outposts rare
        weights = [0.25, 0.22, 0.18, 0.15, 0.08, 0.12]

        nodes = []
        used_names: set = set()

        for i in range(node_count):
            arch_key = rng.choices(archetype_keys, weights=weights, k=1)[0]
            arch = NODE_ARCHETYPES[arch_key]

            # Generate unique name
            attempts = 0
            while attempts < 20:
                prefix = rng.choice(_NAME_PREFIXES)
                suffix = rng.choice(_NAME_SUFFIXES)
                name = f"{prefix}-{suffix}"
                if name not in used_names:
                    used_names.add(name)
                    break
                attempts += 1
            else:
                name = f"node-{i}"

            sec_lo, sec_hi = arch["security_level"]
            security = rng.randint(sec_lo, sec_hi)
            flavor = rng.choice(arch["flavor"])

            node = {
                "id": f"pn-{i}",
                "name": name,
                "archetype": arch_key,
                "label": arch["label"],
                "icon": arch["icon"],
                "color_hint": arch["color_hint"],
                "security_level": security,
                "loot_table": arch["loot_table"],
                "flavor_text": flavor,
                "connected_to": [],
                "is_discovered": i == 0,  # first node always discovered
                "looted": False,
            }
            nodes.append(node)

        # Wire connections: each node connects to 1-3 others
        for i, node in enumerate(nodes):
            num_connections = rng.randint(1, min(3, node_count - 1))
            candidates = [j for j in range(node_count) if j != i]
            chosen = rng.sample(candidates, min(num_connections, len(candidates)))
            node["connected_to"] = [nodes[j]["id"] for j in chosen]

        return nodes

    def get_network(self, gs: Any) -> List[Dict[str, Any]]:
        """Return existing network or generate one for this session."""
        flags = gs.flags
        if "proc_network" not in flags or not flags["proc_network"].get("nodes"):
            seed = flags.get("proc_network_seed", int(time.time()) % 999983)
            flags["proc_network_seed"] = seed
            nodes = self.generate(seed, node_count=8)
            flags["proc_network"] = {
                "seed": seed,
                "nodes": nodes,
                "generated_at": time.time(),
            }
        return flags["proc_network"]["nodes"]

    def _get_node(self, node_id: str, gs: Any) -> Optional[Dict[str, Any]]:
        nodes = self.get_network(gs)
        for n in nodes:
            if n["id"] == node_id or n["name"] == node_id:
                return n
        return None

    def discover_node(self, node_id: str, gs: Any) -> List[dict]:
        """Mark node discovered, award XP."""
        node = self._get_node(node_id, gs)
        if node is None:
            return _err(f"  nodes: unknown node '{node_id}'")

        if node["is_discovered"]:
            return _dim(f"  [{node['icon']}] {node['name']} — already in your map.")

        node["is_discovered"] = True
        xp = NODE_ARCHETYPES[node["archetype"]]["xp_on_discover"]
        gs.add_xp(xp, "networking")

        out: List[dict] = []
        out += _sys(f"  [{node['icon']}] NODE DISCOVERED: {node['name'].upper()}")
        out += [_lore(f"  {node['flavor_text']}")]
        out.append(_line(f"  Archetype: {node['label']}  |  Security: {node['security_level']}/10", "info"))
        out += [_line(f"  +{xp} XP (networking)", "xp")]
        return out

    def render_map(self, gs: Any) -> List[dict]:
        """Render ASCII network map."""
        nodes = self.get_network(gs)
        seed = gs.flags.get("proc_network", {}).get("seed", "?")

        out: List[dict] = []
        out += _sys(f"  ╔══ PROCEDURAL NETWORK MAP  [seed:{seed}] ══╗")
        out.append(_line("  Nodes | ? = undiscovered  SEC = security level", "dim"))
        out.append(_line("  ─────────────────────────────────────────────", "dim"))

        id_to_node = {n["id"]: n for n in nodes}

        for node in nodes:
            if node["is_discovered"]:
                conn_names = []
                for cid in node["connected_to"]:
                    cn = id_to_node.get(cid)
                    if cn:
                        conn_names.append(cn["name"] if cn["is_discovered"] else "???")
                conns = ", ".join(conn_names) if conn_names else "isolated"
                looted = " [LOOTED]" if node.get("looted") else ""
                line = (
                    f"  {node['icon']} {node['name']:<20} "
                    f"{node['label']:<12} SEC:{node['security_level']}/10"
                    f"{looted}  → {conns}"
                )
                out.append(_line(line, node["color_hint"]))
            else:
                # Show that undiscovered nodes exist but obscure details
                out.append(_line(f"  ◌ ???                  UNKNOWN      SEC:?", "dim"))

        out.append(_line("  ─────────────────────────────────────────────", "dim"))
        discovered = sum(1 for n in nodes if n["is_discovered"])
        out += _dim(f"  Discovered: {discovered}/{len(nodes)}  |  nodes discover <name> to reveal")
        return out

    def get_loot(self, node_id: str, gs: Any) -> List[dict]:
        """Roll loot table for a discovered node (once per node)."""
        node = self._get_node(node_id, gs)
        if node is None:
            return _err(f"  nodes: unknown node '{node_id}'")
        if not node["is_discovered"]:
            return _err(f"  nodes: discover {node_id} before looting.")
        if node.get("looted"):
            return _dim(f"  [{node['icon']}] {node['name']} — already stripped clean.")

        node["looted"] = True
        rng = random.Random(int(time.time()))
        out: List[dict] = []
        out += _sys(f"  [{node['icon']}] LOOTING: {node['name'].upper()}")

        flags = gs.flags
        for item, lo, hi in node["loot_table"]:
            amount = rng.randint(lo, hi)
            if amount <= 0:
                continue
            if item == "credits":
                gs.credits = getattr(gs, "credits", 0) + amount
                out.append(_line(f"  +{amount} credits", "success"))
            elif item == "data":
                flags["supply_bank"] = flags.get("supply_bank", {})
                flags["supply_bank"]["data"] = flags["supply_bank"].get("data", 0) + amount
                out.append(_line(f"  +{amount} data shards", "info"))
            elif item == "lore_fragment":
                out += [_lore(f"  [LORE FRAGMENT] {node['flavor_text']}")]
                gs.add_xp(15, "forensics")
                out.append(_line("  +15 XP (forensics)", "xp"))
            elif item in ("keycard", "exploit_kit", "quest_item", "schematics", "components"):
                inv = flags.get("inventory", [])
                inv.append({"item": item, "from": node["name"], "qty": amount})
                flags["inventory"] = inv
                out.append(_line(f"  +{amount} {item}", "success"))

        out += _dim("  Node looted. Nothing more to take.")
        return out

    def force_regenerate(self, gs: Any) -> List[dict]:
        """Force a new network (costs 50 credits)."""
        credits = getattr(gs, "credits", 0)
        if credits < 50:
            return _err("  nodes: insufficient credits (need 50).")
        gs.credits = credits - 50
        seed = int(time.time()) % 999983
        nodes = self.generate(seed, node_count=8)
        gs.flags["proc_network"] = {
            "seed": seed,
            "nodes": nodes,
            "generated_at": time.time(),
        }
        out: List[dict] = []
        out += _sys(f"  NEW NETWORK GENERATED  [seed:{seed}]")
        out += _dim("  -50 credits")
        out += _ok("  Type 'nodes map' to explore your new topology.")
        return out
