"""
app/game_engine/idle_engine.py — V3 Idle/Incremental Layer
===========================================================
Background resource generation while the player is away.
Scripts run autonomously, mining XP and resources passively.

Design:
- Scripts are deployed to claimed nodes and run in the background
- Resources accumulate based on elapsed real time since last login
- Scripts have efficiency ratings and can be upgraded
- Tied to the colony supply chain (CS4 supply.py)

Wire format compatible: all output is List[dict] with t/s keys.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Script definitions
# ---------------------------------------------------------------------------

IDLE_SCRIPTS = {
    "recon_daemon": {
        "name": "Recon Daemon",
        "description": "Passive network scanner. Generates networking XP over time.",
        "xp_per_hour": 8,
        "xp_skill": "networking",
        "resource_per_hour": {"data": 2},
        "cost": {"credits": 50},
        "max_level": 5,
        "unlock_beat": None,
        "lore": "A ghost in the wire. Scans while you sleep.",
    },
    "log_harvester": {
        "name": "Log Harvester",
        "description": "Tails system logs. Generates forensics XP.",
        "xp_per_hour": 6,
        "xp_skill": "forensics",
        "resource_per_hour": {"data": 3, "compute": 1},
        "cost": {"credits": 40},
        "max_level": 5,
        "unlock_beat": "first_cat",
        "lore": "Every log entry is a confession.",
    },
    "crypto_miner": {
        "name": "Crypto Miner",
        "description": "Background cryptographic computations. Generates credits.",
        "xp_per_hour": 4,
        "xp_skill": "cryptography",
        "resource_per_hour": {"credits": 5, "compute": 2},
        "cost": {"credits": 100},
        "max_level": 10,
        "unlock_beat": None,
        "lore": "Math is money. Always has been.",
    },
    "trust_broker": {
        "name": "Trust Broker",
        "description": "Sends ambient messages to agents. Slowly builds trust.",
        "xp_per_hour": 5,
        "xp_skill": "social_engineering",
        "resource_per_hour": {"data": 1},
        "trust_per_hour": 1,  # across all agents
        "cost": {"credits": 75},
        "max_level": 3,
        "unlock_beat": "ada_first_contact",
        "lore": "Relationships cultivated in the dark.",
    },
    "exploit_compiler": {
        "name": "Exploit Compiler",
        "description": "Background zero-day research. High security XP yield.",
        "xp_per_hour": 12,
        "xp_skill": "security",
        "resource_per_hour": {"compute": 3},
        "cost": {"credits": 200},
        "max_level": 5,
        "unlock_beat": "root_achieved",
        "lore": "The best exploits are never rushed.",
    },
    "osint_spider": {
        "name": "OSINT Spider",
        "description": "Crawls the darknet for intelligence. Terminal skill focus.",
        "xp_per_hour": 7,
        "xp_skill": "terminal",
        "resource_per_hour": {"data": 4},
        "cost": {"credits": 60},
        "max_level": 5,
        "unlock_beat": None,
        "lore": "Information is the currency of power.",
    },
    "neural_trainer": {
        "name": "Neural Trainer",
        "description": "Trains background ML models. Programming + security XP.",
        "xp_per_hour": 10,
        "xp_skill": "programming",
        "resource_per_hour": {"compute": 4, "data": 2},
        "cost": {"credits": 300},
        "max_level": 5,
        "unlock_beat": "chimera_exploited",
        "lore": "The ghost teaches the machine. The machine teaches back.",
    },
}

# Cap on hours of idle accumulation (24h max)
MAX_IDLE_HOURS = 24.0
# Cap on individual resource stockpile
RESOURCE_CAP = 9999

# ---------------------------------------------------------------------------
# Idle engine
# ---------------------------------------------------------------------------

class IdleEngine:
    """
    Manages background scripts and idle resource accumulation.

    State is stored in `gs.flags` under key "idle_state":
    {
        "deployed": {
            "recon_daemon": {"level": 1, "node": "node-1", "deployed_at": 1234567890}
        },
        "last_tick": 1234567890,
        "stockpile": {"xp_networking": 45, "xp_forensics": 12, "credits": 200, "compute": 30, "data": 80}
    }
    """

    def _get_state(self, flags: dict) -> dict:
        if "idle_state" not in flags:
            flags["idle_state"] = {
                "deployed": {},
                "last_tick": time.time(),
                "stockpile": {},
            }
        return flags["idle_state"]

    def tick(self, flags: dict) -> dict:
        """
        Compute idle gains since last tick. Returns summary dict of gains.
        Call this at login / on `idle status`.
        """
        state = self._get_state(flags)
        now = time.time()
        elapsed_hours = min((now - state["last_tick"]) / 3600.0, MAX_IDLE_HOURS)
        state["last_tick"] = now

        gains: Dict[str, float] = {}
        deployed = state.get("deployed", {})

        for script_id, deployment in deployed.items():
            defn = IDLE_SCRIPTS.get(script_id)
            if not defn:
                continue
            level = deployment.get("level", 1)
            multiplier = 1.0 + (level - 1) * 0.2  # +20% per level

            # XP gain
            xp_gain = defn["xp_per_hour"] * elapsed_hours * multiplier
            skill_key = f"xp_{defn['xp_skill']}"
            gains[skill_key] = gains.get(skill_key, 0) + xp_gain

            # Resource gains
            for resource, rate in defn.get("resource_per_hour", {}).items():
                resource_gain = rate * elapsed_hours * multiplier
                gains[resource] = gains.get(resource, 0) + resource_gain

        # Commit gains to stockpile
        stockpile = state.setdefault("stockpile", {})
        for k, v in gains.items():
            stockpile[k] = min(stockpile.get(k, 0) + v, RESOURCE_CAP)

        return {k: round(v, 1) for k, v in gains.items()}

    def deploy(self, script_id: str, node: str, flags: dict, story_beats: list) -> List[dict]:
        """Deploy a script to a node."""
        defn = IDLE_SCRIPTS.get(script_id)
        if not defn:
            return [{"t": "error", "s": f"  Unknown script: {script_id}"}]

        unlock = defn.get("unlock_beat")
        if unlock and unlock not in story_beats:
            return [{"t": "error", "s": f"  {defn['name']} requires: {unlock}"}]

        state = self._get_state(flags)
        deployed = state.setdefault("deployed", {})

        if script_id in deployed:
            return [{"t": "warn", "s": f"  {defn['name']} already deployed on {deployed[script_id]['node']}"}]

        # Check cost
        stockpile = state.get("stockpile", {})
        cost = defn.get("cost", {})
        for resource, amount in cost.items():
            if stockpile.get(resource, 0) < amount:
                return [
                    {"t": "error", "s": f"  Insufficient {resource}: need {amount}, have {int(stockpile.get(resource, 0))}"},
                    {"t": "dim",   "s": f"  Use `supply` to check your resources."},
                ]

        # Deduct cost
        for resource, amount in cost.items():
            stockpile[resource] = stockpile.get(resource, 0) - amount

        deployed[script_id] = {
            "level": 1,
            "node": node,
            "deployed_at": time.time(),
        }

        return [
            {"t": "success", "s": f"  ✓ {defn['name']} deployed on {node}"},
            {"t": "dim",     "s": f"  Generating {defn['xp_per_hour']} {defn['xp_skill']} XP/hour"},
            {"t": "dim",     "s": f"  '{defn['lore']}'"},
        ]

    def recall(self, script_id: str, flags: dict) -> List[dict]:
        """Stop a deployed script."""
        state = self._get_state(flags)
        deployed = state.get("deployed", {})
        if script_id not in deployed:
            return [{"t": "error", "s": f"  {script_id} is not deployed"}]
        node = deployed.pop(script_id)["node"]
        return [{"t": "success", "s": f"  {script_id} recalled from {node}"}]

    def upgrade(self, script_id: str, flags: dict) -> List[dict]:
        """Upgrade a deployed script level."""
        defn = IDLE_SCRIPTS.get(script_id)
        if not defn:
            return [{"t": "error", "s": f"  Unknown script: {script_id}"}]
        state = self._get_state(flags)
        deployed = state.get("deployed", {})
        if script_id not in deployed:
            return [{"t": "error", "s": f"  {script_id} not deployed — deploy it first"}]

        entry = deployed[script_id]
        current_level = entry.get("level", 1)
        max_level = defn["max_level"]

        if current_level >= max_level:
            return [{"t": "warn", "s": f"  {defn['name']} is already at max level ({max_level})"}]

        upgrade_cost = {k: v * current_level * 2 for k, v in defn["cost"].items()}
        stockpile = state.get("stockpile", {})
        for resource, amount in upgrade_cost.items():
            if stockpile.get(resource, 0) < amount:
                return [{"t": "error", "s": f"  Need {amount} {resource} to upgrade (have {int(stockpile.get(resource, 0))})"}]

        for resource, amount in upgrade_cost.items():
            stockpile[resource] = stockpile.get(resource, 0) - amount

        entry["level"] = current_level + 1
        new_xph = defn["xp_per_hour"] * (1.0 + current_level * 0.2)
        return [
            {"t": "success", "s": f"  ✓ {defn['name']} upgraded to Level {current_level + 1}"},
            {"t": "dim",     "s": f"  New rate: {new_xph:.1f} {defn['xp_skill']} XP/hour"},
        ]

    def collect(self, flags: dict) -> dict:
        """Drain the stockpile and return collected amounts."""
        state = self._get_state(flags)
        stockpile = state.get("stockpile", {})
        collected = {k: round(v) for k, v in stockpile.items() if v >= 1.0}
        for k in collected:
            stockpile[k] = stockpile[k] - collected[k]
        return collected

    def render_status(self, flags: dict, story_beats: list) -> List[dict]:
        """Render the full idle dashboard."""
        state = self._get_state(flags)
        deployed = state.get("deployed", {})
        stockpile = state.get("stockpile", {})
        out = []

        out.append({"t": "system", "s": "  ═══ IDLE SCRIPTS — BACKGROUND OPS ═══"})
        out.append({"t": "dim", "s": ""})

        if deployed:
            out.append({"t": "info", "s": "  ACTIVE DEPLOYMENTS:"})
            for sid, info in deployed.items():
                defn = IDLE_SCRIPTS[sid]
                level = info.get("level", 1)
                node = info.get("node", "?")
                elapsed_h = (time.time() - info.get("deployed_at", time.time())) / 3600
                rate = defn["xp_per_hour"] * (1.0 + (level - 1) * 0.2)
                out.append({"t": "success",
                            "s": f"  [{sid}] L{level} on {node} — {rate:.1f} {defn['xp_skill']} XP/h — {elapsed_h:.1f}h running"})
            out.append({"t": "dim", "s": ""})

        # Stockpile
        if any(v >= 1.0 for v in stockpile.values()):
            out.append({"t": "info", "s": "  STOCKPILE (run `idle collect` to claim):"})
            for k, v in stockpile.items():
                if v >= 1.0:
                    out.append({"t": "dim", "s": f"    {k}: {round(v)}"})
            out.append({"t": "dim", "s": ""})

        # Available to deploy
        out.append({"t": "info", "s": "  AVAILABLE SCRIPTS:"})
        for sid, defn in IDLE_SCRIPTS.items():
            unlock = defn.get("unlock_beat")
            locked = unlock and unlock not in story_beats
            already = sid in deployed
            cost_str = ", ".join(f"{v} {k}" for k, v in defn["cost"].items())
            state_tag = "[DEPLOYED]" if already else ("[LOCKED]" if locked else "[AVAILABLE]")
            style = "dim" if (locked or already) else "info"
            out.append({"t": style, "s": f"  {state_tag} {defn['name']} — {defn['xp_per_hour']}xp/h — {cost_str}"})
            if not locked and not already:
                out.append({"t": "dim", "s": f"    → idle deploy {sid} <node>"})

        out.append({"t": "dim", "s": ""})
        out.append({"t": "dim", "s": "  Commands: idle status | idle deploy <script> <node> | idle collect | idle upgrade <script> | idle recall <script>"})
        return out


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_engine = IdleEngine()


def get_engine() -> IdleEngine:
    return _engine


if __name__ == "__main__":
    # Quick self-test
    flags: dict = {}
    beats = ["first_cat", "ada_first_contact"]
    eng = IdleEngine()

    # Deploy recon_daemon — it's free to unlock (no beat req)
    # Seed some credits first
    state = eng._get_state(flags)
    state["stockpile"]["credits"] = 500

    result = eng.deploy("recon_daemon", "node-1", flags, beats)
    for r in result:
        print(f"[{r['t']}] {r['s']}")

    # Simulate 2 hours idle
    state["last_tick"] = time.time() - 7200
    gains = eng.tick(flags)
    print(f"\nGains after 2h: {gains}")

    status = eng.render_status(flags, beats)
    for r in status:
        print(f"[{r['t']}] {r['s']}")
