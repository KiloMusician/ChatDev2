"""
app/game_engine/turret_engine.py — CS5 Defense Turrets
========================================================
Deploy defensive scripts to claimed nodes. Turrets intercept
CHIMERA/NexusCorp sweeps and generate alert events.

3 turret types:
  FIREWALL   — blocks automated scans, +20 trace resistance
  HONEYPOT   — attracts attackers and fingerprints them, generates intel
  IDS_DAEMON — Intrusion Detection System, alerts on active attacks

Turrets degrade over time (each CHIMERA sweep reduces HP by ~10%).
Can be repaired with `defend repair <node>`.

Wire format compatible throughout.
"""
from __future__ import annotations

import random
import time
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Turret definitions
# ---------------------------------------------------------------------------

TURRET_TYPES = {
    "firewall": {
        "name": "Firewall Script",
        "description": "Blocks automated CHIMERA scans. +20 trace resistance on the node.",
        "hp": 100,
        "power_draw": 5,   # compute units per hour
        "cost": {"compute": 30, "data": 10},
        "defense_bonus": 20,
        "lore": "Every packet analyzed. Every anomaly rejected.",
        "icon": "🔥",
    },
    "honeypot": {
        "name": "Honeypot Daemon",
        "description": "Mimics a vulnerable service. Fingerprints attackers and generates intel data.",
        "hp": 80,
        "power_draw": 8,
        "cost": {"compute": 20, "data": 20, "credits": 50},
        "intel_per_hour": 5,  # data units
        "lore": "A trap that looks like an opportunity. Classic.",
        "icon": "🍯",
    },
    "ids_daemon": {
        "name": "IDS Daemon",
        "description": "Real-time intrusion detection. Alerts when node is under active attack.",
        "hp": 120,
        "power_draw": 10,
        "cost": {"compute": 40, "data": 15, "credits": 100},
        "alert_threshold": 3,  # attacks before alert fires
        "lore": "Silence means safety. Sound the alarm on the first byte.",
        "icon": "🚨",
    },
}

# ---------------------------------------------------------------------------
# Turret engine
# ---------------------------------------------------------------------------

class TurretEngine:
    """
    Manages defensive turrets on claimed nodes.
    State in gs.flags["turrets"]: {
        node_id: {
            turret_type: {hp, deployed_at, attacks_intercepted}
        }
    }
    """

    def _get_turrets(self, flags: dict) -> dict:
        if "turrets" not in flags:
            flags["turrets"] = {}
        return flags["turrets"]

    def deploy(self, node: str, turret_type: str, flags: dict,
               claimed_nodes: list, story_beats: list) -> List[dict]:
        if node not in claimed_nodes and node != "home":
            return [{"t": "error", "s": f"  {node}: not a claimed node — claim it first with `nodes claim {node}`"}]

        defn = TURRET_TYPES.get(turret_type)
        if not defn:
            available = " | ".join(TURRET_TYPES.keys())
            return [{"t": "error", "s": f"  Unknown turret type: {turret_type}. Available: {available}"}]

        turrets = self._get_turrets(flags)
        node_turrets = turrets.setdefault(node, {})

        if turret_type in node_turrets:
            existing = node_turrets[turret_type]
            return [{"t": "warn", "s": f"  {defn['name']} already deployed on {node} (HP: {existing['hp']}/100)"}]

        # Check resource cost
        supply = flags.get("supply_bank", {})
        cost = defn.get("cost", {})
        for resource, amount in cost.items():
            if supply.get(resource, 0) < amount:
                return [{"t": "error", "s": f"  Need {amount} {resource} (have {supply.get(resource, 0)}) — use `supply` to check resources"}]

        for resource, amount in cost.items():
            supply[resource] = supply.get(resource, 0) - amount

        node_turrets[turret_type] = {
            "hp": defn["hp"],
            "max_hp": defn["hp"],
            "deployed_at": time.time(),
            "attacks_intercepted": 0,
            "alerts_fired": 0,
        }

        return [
            {"t": "success", "s": f"  {defn['icon']} {defn['name']} deployed on {node}"},
            {"t": "dim",     "s": f"  HP: {defn['hp']}/{defn['hp']}  Power draw: {defn['power_draw']} compute/h"},
            {"t": "dim",     "s": f"  '{defn['lore']}'"},
        ]

    def recall(self, node: str, turret_type: str, flags: dict) -> List[dict]:
        turrets = self._get_turrets(flags)
        node_turrets = turrets.get(node, {})
        if turret_type not in node_turrets:
            return [{"t": "error", "s": f"  No {turret_type} on {node}"}]
        node_turrets.pop(turret_type)
        return [{"t": "success", "s": f"  {turret_type} recalled from {node}"}]

    def repair(self, node: str, flags: dict) -> List[dict]:
        """Repair all turrets on a node (costs compute)."""
        turrets = self._get_turrets(flags)
        node_turrets = turrets.get(node, {})
        if not node_turrets:
            return [{"t": "warn", "s": f"  No turrets on {node}"}]
        supply = flags.get("supply_bank", {})
        repair_cost = sum(
            max(0, defn["max_hp"] - t.get("hp", 0)) // 10
            for turret_type, t in node_turrets.items()
            for defn in [TURRET_TYPES[turret_type]]
        )
        compute_cost = max(5, repair_cost)
        if supply.get("compute", 0) < compute_cost:
            return [{"t": "error", "s": f"  Need {compute_cost} compute to repair (have {supply.get('compute', 0)})"}]
        supply["compute"] = supply.get("compute", 0) - compute_cost
        out = [{"t": "success", "s": f"  Repairing turrets on {node}..."}]
        for turret_type, t in node_turrets.items():
            defn = TURRET_TYPES[turret_type]
            old_hp = t["hp"]
            t["hp"] = defn["hp"]
            out.append({"t": "success", "s": f"  {defn['icon']} {defn['name']}: {old_hp} → {t['hp']} HP"})
        return out

    def simulate_sweep(self, flags: dict, claimed_nodes: list) -> List[dict]:
        """
        Simulate a CHIMERA/NexusCorp sweep event.
        Turrets intercept attacks; unprotected nodes take trace increase.
        """
        turrets = self._get_turrets(flags)
        out = [
            {"t": "warn", "s": "  [CHIMERA]: SWEEP INITIATED — scanning claimed nodes..."},
            {"t": "dim",  "s": ""},
        ]
        for node in claimed_nodes:
            node_turrets = turrets.get(node, {})
            if not node_turrets:
                out.append({"t": "warn", "s": f"  {node}: UNPROTECTED — trace level +5"})
                flags["trace_level"] = min(100, flags.get("trace_level", 0) + 5)
            else:
                for turret_type, t in node_turrets.items():
                    defn = TURRET_TYPES[turret_type]
                    dmg = random.randint(5, 15)
                    t["hp"] = max(0, t["hp"] - dmg)
                    t["attacks_intercepted"] = t.get("attacks_intercepted", 0) + 1
                    icon = defn["icon"]
                    if t["hp"] <= 0:
                        out.append({"t": "error", "s": f"  {node}: {icon} {defn['name']} DESTROYED by sweep"})
                        turrets[node].pop(turret_type)
                    else:
                        out.append({"t": "success", "s": f"  {node}: {icon} intercepted sweep — {dmg} damage ({t['hp']} HP)"})
        return out

    def render_defense_map(self, flags: dict, claimed_nodes: list) -> List[dict]:
        turrets = self._get_turrets(flags)
        out = [
            {"t": "system", "s": "  ═══ DEFENSE MAP ═══"},
            {"t": "dim",    "s": ""},
        ]
        for node in ["home"] + (claimed_nodes or []):
            node_turrets = turrets.get(node, {})
            if node_turrets:
                out.append({"t": "info", "s": f"  {node}:"})
                for turret_type, t in node_turrets.items():
                    defn = TURRET_TYPES[turret_type]
                    hp_pct = t["hp"] / defn["hp"]
                    hp_bar = "█" * int(hp_pct * 10) + "░" * (10 - int(hp_pct * 10))
                    age_h = (time.time() - t.get("deployed_at", time.time())) / 3600
                    out.append({"t": "dim" if hp_pct < 0.3 else "success",
                                "s": f"    {defn['icon']} {defn['name']:<20} HP [{hp_bar}] {t['hp']}/{defn['hp']}  {age_h:.0f}h  intercepted={t.get('attacks_intercepted',0)}"})
            else:
                out.append({"t": "dim", "s": f"  {node}: [UNDEFENDED]"})

        out.append({"t": "dim",    "s": ""})
        out.append({"t": "dim",    "s": "  defend deploy <turret> <node>  |  defend repair <node>  |  defend sweep (simulate)"})
        out.append({"t": "dim",    "s": "  Turret types: firewall | honeypot | ids_daemon"})
        return out


_engine: Optional[TurretEngine] = None


def get_engine() -> TurretEngine:
    global _engine
    if _engine is None:
        _engine = TurretEngine()
    return _engine


if __name__ == "__main__":
    eng = TurretEngine()
    flags: dict = {"supply_bank": {"compute": 200, "data": 100, "credits": 500}}
    claimed = ["node-1", "nexus-gateway"]

    for r in eng.deploy("node-1", "firewall", flags, claimed, []):
        print(f"[{r['t']}] {r['s']}")
    for r in eng.deploy("node-1", "honeypot", flags, claimed, []):
        print(f"[{r['t']}] {r['s']}")
    for r in eng.deploy("nexus-gateway", "ids_daemon", flags, claimed, []):
        print(f"[{r['t']}] {r['s']}")

    print("\n--- Defense Map ---")
    for r in eng.render_defense_map(flags, claimed):
        print(f"[{r['t']}] {r['s']}")

    print("\n--- Simulating Sweep ---")
    for r in eng.simulate_sweep(flags, claimed):
        print(f"[{r['t']}] {r['s']}")
