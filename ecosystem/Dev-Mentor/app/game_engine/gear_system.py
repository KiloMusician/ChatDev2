"""
app/game_engine/gear_system.py — R3 Gear System + R7 Skill Checks
==================================================================
Software "tools" the player equips for passive bonuses to exploits,
scans, social interactions, and data operations.

State is stored in gs.flags["equipped_gear"] (dict: slot -> item_id)
and gs.flags["gear_inventory"] (list of owned item_ids).

Wire format compatible: all public methods return List[dict] with t/s keys.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Wire helpers (module-local, avoids circular import)
# ---------------------------------------------------------------------------

def _sys(s: str) -> dict:   return {"t": "system",  "s": s}
def _dim(s: str) -> dict:   return {"t": "dim",     "s": s}
def _ok(s: str) -> dict:    return {"t": "success", "s": s}
def _err(s: str) -> dict:   return {"t": "error",   "s": s}
def _info(s: str) -> dict:  return {"t": "info",    "s": s}
def _lore(s: str) -> dict:  return {"t": "lore",    "s": s}
def _warn(s: str) -> dict:  return {"t": "warn",    "s": s}


# ---------------------------------------------------------------------------
# Gear catalogue
# ---------------------------------------------------------------------------

GEAR_ITEMS: Dict[str, Dict] = {
    # ── SCANNERS ───────────────────────────────────────────────────────
    "quantum_scanner": {
        "name": "Quantum Scanner",
        "description": "Entangles with target node EM fields — scan accuracy through the roof.",
        "category": "scanner",
        "cost_credits": 200,
        "cost_data": 0,
        "level_req": 1,
        "passive_effect": {"scan": 15},
        "lore": "Built from salvaged NexusCorp sensor arrays. They don't know you're using their own eyes.",
        "icon": "📡",
    },
    "stealth_probe": {
        "name": "Stealth Probe",
        "description": "Low-emission scanner — more than compensates with trace avoidance.",
        "category": "scanner",
        "cost_credits": 350,
        "cost_data": 10,
        "level_req": 5,
        "passive_effect": {"scan": 10, "trace_reduction": 20},
        "lore": "RAVEN's personal design. Ghost in a ghost — the probe barely exists.",
        "icon": "🔭",
    },
    "deep_scanner": {
        "name": "Deep Scanner",
        "description": "Penetrates hardened node shells. Root privileges required to calibrate.",
        "category": "scanner",
        "cost_credits": 600,
        "cost_data": 25,
        "level_req": 15,
        "level_req_root": True,
        "passive_effect": {"scan": 25, "recon": 10},
        "lore": "CHIMERA's own recon protocol, extracted and repurposed. Poetry.",
        "icon": "🛰",
    },

    # ── EXPLOITS ───────────────────────────────────────────────────────
    "zero_day_kit": {
        "name": "Zero-Day Kit",
        "description": "Curated collection of unpatched CVEs. Dramatically improves exploit success.",
        "category": "exploit",
        "cost_credits": 450,
        "cost_data": 15,
        "level_req": 8,
        "passive_effect": {"exploit": 20},
        "lore": "Eleven CVEs, three weaponised. The other eight are for emergencies.",
        "icon": "💣",
    },
    "phantom_shell": {
        "name": "Phantom Shell",
        "description": "Wraps payloads in ghost-mode transport — exploit boost plus reduced trace.",
        "category": "exploit",
        "cost_credits": 700,
        "cost_data": 20,
        "level_req": 12,
        "passive_effect": {"exploit": 15, "trace_reduction": 15},
        "lore": "ZERO leaked the design. Don't ask how he got it.",
        "icon": "👻",
    },
    "chimera_fragment_x": {
        "name": "CHIMERA Fragment X",
        "description": "Legendary. A shard of CHIMERA's own offensive core. Immense exploit power.",
        "category": "exploit",
        "cost_credits": 2000,
        "cost_data": 100,
        "level_req": 20,
        "passive_effect": {"exploit": 40, "scan": 10},
        "lore": "You shouldn't have this. CHIMERA knows a piece of itself is missing.",
        "icon": "☢",
    },

    # ── FIREWALLS ──────────────────────────────────────────────────────
    "basic_ips": {
        "name": "Basic IPS",
        "description": "Off-the-shelf intrusion prevention. Better than nothing.",
        "category": "firewall",
        "cost_credits": 100,
        "cost_data": 0,
        "level_req": 1,
        "passive_effect": {"defense": 10},
        "lore": "Consumer grade. You've already patched three of its own vulnerabilities.",
        "icon": "🛡",
    },
    "adaptive_shield": {
        "name": "Adaptive Shield",
        "description": "Self-adjusting defense layer. Learns from traced connection attempts.",
        "category": "firewall",
        "cost_credits": 400,
        "cost_data": 10,
        "level_req": 8,
        "passive_effect": {"defense": 20, "trace_reduction": 5},
        "lore": "SERENA helped design the learning algorithm. She denies it.",
        "icon": "⚔",
    },
    "watcher_mirror": {
        "name": "Watcher Mirror",
        "description": "Reflects 10% of trace back at the origin. Strong defense, disorienting effect.",
        "category": "firewall",
        "cost_credits": 900,
        "cost_data": 40,
        "level_req": 18,
        "passive_effect": {"defense": 30, "trace_reflect": 10},
        "lore": "Built using the Watcher's own observation protocols. They hate that.",
        "icon": "🪞",
    },

    # ── DATASTORES ─────────────────────────────────────────────────────
    "memory_vault": {
        "name": "Memory Vault",
        "description": "Compressed encrypted storage. Modest data capacity boost.",
        "category": "datastore",
        "cost_credits": 150,
        "cost_data": 0,
        "level_req": 1,
        "passive_effect": {"data_capacity": 10},
        "lore": "Stolen from a NexusCorp backup depot. Still has their logo.",
        "icon": "💾",
    },
    "quantum_cache": {
        "name": "Quantum Cache",
        "description": "Superposition storage. More data AND a small XP processing boost.",
        "category": "datastore",
        "cost_credits": 550,
        "cost_data": 20,
        "level_req": 10,
        "passive_effect": {"data_capacity": 25, "xp_rate": 5},
        "lore": "Data that exists in multiple states until you read it. CYPHER finds this unsettling.",
        "icon": "🔮",
    },
    "void_archive": {
        "name": "Void Archive",
        "description": "Infinite-feel storage via recursive compression. Level 15+ only.",
        "category": "datastore",
        "cost_credits": 1200,
        "cost_data": 60,
        "level_req": 15,
        "passive_effect": {"data_capacity": 50, "xp_rate": 10},
        "lore": "The data goes in. No one is entirely sure where it goes after that.",
        "icon": "🕳",
    },

    # ── SOCIAL ─────────────────────────────────────────────────────────
    "neural_emulator": {
        "name": "Neural Emulator",
        "description": "Mimics agent communication patterns. Social skill boost.",
        "category": "social",
        "cost_credits": 300,
        "cost_data": 5,
        "level_req": 5,
        "passive_effect": {"social": 15},
        "lore": "Learns from every conversation. It's getting eerily good at being you.",
        "icon": "🧠",
    },
    "reputation_broker": {
        "name": "Reputation Broker",
        "description": "Automated trust-signal amplifier. Speeds up agent trust gain.",
        "category": "social",
        "cost_credits": 500,
        "cost_data": 10,
        "level_req": 10,
        "passive_effect": {"social": 20, "trust_gain": 20},
        "lore": "ADA calls it 'manufactured consent'. It works regardless.",
        "icon": "🤝",
    },
    "chimera_mask": {
        "name": "CHIMERA Mask",
        "description": "Spoofs corporate credentials. Huge social boost; corp reputation takes a hit.",
        "category": "social",
        "cost_credits": 800,
        "cost_data": 30,
        "level_req": 15,
        "passive_effect": {"social": 30, "corp_rep": -20},
        "lore": "You become NexusCorp for exactly as long as you need to be. Then you vanish.",
        "icon": "🎭",
    },
}

# Slot categories (one item per category can be equipped)
GEAR_CATEGORIES = ["scanner", "exploit", "firewall", "datastore", "social"]

# Resource refund fraction when unequipping
UNEQUIP_REFUND_FRACTION = 0.5


# ---------------------------------------------------------------------------
# GearSystem
# ---------------------------------------------------------------------------

class GearSystem:
    """
    Manages player gear: equipping, unequipping, passive bonuses, and rendering.

    State in gs.flags:
        "equipped_gear"   : { category: item_id }
        "gear_inventory"  : [ item_id, ... ]
        "gear_data_pool"  : int  (simplified data resource for gear costs)
    """

    # ── Internal state helpers ───────────────────────────────────────

    def _equipped(self, gs) -> dict:
        if "equipped_gear" not in gs.flags:
            gs.flags["equipped_gear"] = {}
        return gs.flags["equipped_gear"]

    def _inventory(self, gs) -> list:
        if "gear_inventory" not in gs.flags:
            gs.flags["gear_inventory"] = []
        return gs.flags["gear_inventory"]

    def _get_credits(self, gs) -> int:
        """Fetch player credits from the economy ledger (or flags fallback)."""
        try:
            from app.game_engine.economy import EconomyEngine
            return EconomyEngine().balance("player")
        except Exception:
            return gs.flags.get("credits", 0)

    def _deduct_credits(self, gs, amount: int) -> None:
        try:
            from app.game_engine.economy import EconomyEngine
            EconomyEngine().withdraw("player", amount, "gear purchase")
        except Exception:
            gs.flags["credits"] = max(0, gs.flags.get("credits", 0) - amount)

    def _refund_credits(self, gs, amount: int) -> None:
        try:
            from app.game_engine.economy import EconomyEngine
            EconomyEngine().deposit("player", amount, "gear refund")
        except Exception:
            gs.flags["credits"] = gs.flags.get("credits", 0) + amount

    # ── Public API ───────────────────────────────────────────────────

    def equip(self, item_id: str, gs) -> List[dict]:
        """Equip an item. Checks level req, cost, slot."""
        item = GEAR_ITEMS.get(item_id)
        if not item:
            close = [k for k in GEAR_ITEMS if item_id in k or k.startswith(item_id[:4])]
            hint = f"  Did you mean: {close[0]}?" if close else ""
            return [_err(f"  Unknown gear: '{item_id}'.{hint}")]

        level_req = item.get("level_req", 1)
        if gs.level < level_req:
            return [_err(f"  {item['name']} requires Level {level_req}. You are Level {gs.level}.")]

        if item.get("level_req_root") and not gs.flags.get("root_shell", False):
            return [_err(f"  {item['name']} requires root shell to calibrate.")]

        equipped = self._equipped(gs)
        inventory = self._inventory(gs)
        cat = item["category"]

        # Check if already equipped in slot
        if equipped.get(cat) == item_id:
            return [_warn(f"  {item['name']} is already equipped in the {cat} slot.")]

        # If already owned (in inventory), equip for free (no re-purchase)
        already_owned = item_id in inventory
        if not already_owned:
            # Charge credits
            credits = self._get_credits(gs)
            cost_c = item.get("cost_credits", 0)
            cost_d = item.get("cost_data", 0)
            if credits < cost_c:
                return [
                    _err(f"  Insufficient credits. Need {cost_c}₵, have {credits}₵."),
                    _dim("  Use `bank balance` to check funds."),
                ]
            data_pool = gs.flags.get("gear_data_pool", 0)
            if data_pool < cost_d and cost_d > 0:
                return [
                    _err(f"  Insufficient data. Need {cost_d} data units, have {data_pool}."),
                    _dim("  Earn data by scanning nodes and completing recon missions."),
                ]
            self._deduct_credits(gs, cost_c)
            if cost_d > 0:
                gs.flags["gear_data_pool"] = data_pool - cost_d
            inventory.append(item_id)

        # Swap out old item in slot if any
        old_id = equipped.get(cat)
        if old_id and old_id != item_id:
            equipped.pop(cat, None)

        equipped[cat] = item_id

        out = [
            _sys(""),
            _ok(f"  ✓ EQUIPPED: {item['icon']}  {item['name']}"),
            _dim(f"  Slot: {cat}"),
        ]
        effects = item.get("passive_effect", {})
        for stat, val in effects.items():
            sign = "+" if val >= 0 else ""
            out.append(_info(f"  Passive: {sign}{val} {stat}"))
        out.append(_lore(f"  \"{item['lore']}\""))
        out.append(_dim(""))
        return out

    def unequip(self, item_id: str, gs) -> List[dict]:
        """Unequip an item; refund 50% of credit cost."""
        item = GEAR_ITEMS.get(item_id)
        if not item:
            return [_err(f"  Unknown gear: '{item_id}'.")]

        equipped = self._equipped(gs)
        cat = item["category"]
        if equipped.get(cat) != item_id:
            return [_warn(f"  {item['name']} is not currently equipped.")]

        equipped.pop(cat)
        refund = int(item.get("cost_credits", 0) * UNEQUIP_REFUND_FRACTION)
        if refund > 0:
            self._refund_credits(gs, refund)

        return [
            _ok(f"  ✓ UNEQUIPPED: {item['name']}"),
            _dim(f"  Refund: {refund}₵ returned to your account."),
            _dim(""),
        ]

    def get_bonus(self, gs, stat: str) -> int:
        """
        Sum passive bonuses for a given stat from all currently equipped gear.
        Stat names: 'exploit', 'scan', 'defense', 'social', 'trace_reduction',
                    'data_capacity', 'xp_rate', 'recon', 'trust_gain', 'corp_rep'
        """
        equipped = self._equipped(gs)
        total = 0
        for cat, item_id in equipped.items():
            item = GEAR_ITEMS.get(item_id)
            if item:
                total += item.get("passive_effect", {}).get(stat, 0)
        return total

    def render_loadout(self, gs) -> List[dict]:
        """Show currently equipped gear with stat summary."""
        equipped = self._equipped(gs)
        out = [
            _sys(""),
            _sys("╔══════════════════════════════════════════════════════════╗"),
            _sys("║  GEAR LOADOUT — Equipped Tools & Passive Bonuses         ║"),
            _sys("╚══════════════════════════════════════════════════════════╝"),
            _dim(""),
        ]

        if not equipped:
            out.append(_dim("  No gear equipped. Use `gear shop` to browse available tools."))
            out.append(_dim(""))
            return out

        all_stats: Dict[str, int] = {}
        for cat in GEAR_CATEGORIES:
            item_id = equipped.get(cat)
            if item_id:
                item = GEAR_ITEMS[item_id]
                out.append(_info(f"  [{cat.upper():10}] {item['icon']}  {item['name']}"))
                out.append(_dim(f"              {item['description'][:55]}"))
                for stat, val in item.get("passive_effect", {}).items():
                    all_stats[stat] = all_stats.get(stat, 0) + val
            else:
                out.append(_dim(f"  [{cat.upper():10}] — empty slot —"))

        out.append(_dim(""))
        out.append(_sys("  ── CUMULATIVE BONUSES ──────────────────────────────────"))
        for stat, val in sorted(all_stats.items()):
            sign = "+" if val >= 0 else ""
            color = "success" if val >= 0 else "error"
            out.append({"t": color, "s": f"    {stat:<22} {sign}{val}"})
        out.append(_dim(""))
        out.append(_dim("  Commands: gear equip <item>  |  gear unequip <item>  |  gear info <item>"))
        out.append(_dim(""))
        return out

    def render_shop(self, gs) -> List[dict]:
        """Show available gear items grouped by category."""
        equipped = self._equipped(gs)
        inventory = self._inventory(gs)
        credits = self._get_credits(gs)

        out = [
            _sys(""),
            _sys("╔══════════════════════════════════════════════════════════╗"),
            _sys("║  GEAR SHOP — Tools, Exploits & Defense Systems           ║"),
            _sys(f"║  Your credits: {credits:>6}₵                                   ║"),
            _sys("╚══════════════════════════════════════════════════════════╝"),
            _dim(""),
        ]

        for cat in GEAR_CATEGORIES:
            out.append(_sys(f"  ── {cat.upper()} ──────────────────────────────────────────"))
            for item_id, item in GEAR_ITEMS.items():
                if item["category"] != cat:
                    continue
                locked = gs.level < item.get("level_req", 1)
                root_req = item.get("level_req_root", False) and not gs.flags.get("root_shell", False)
                owned = item_id in inventory
                e_slot = equipped.get(cat) == item_id

                cost_str = f"{item['cost_credits']}₵"
                if item.get("cost_data", 0):
                    cost_str += f" + {item['cost_data']} data"

                status = ""
                if e_slot:
                    status = " [EQUIPPED]"
                elif owned:
                    status = " [OWNED]"
                elif locked:
                    status = f" [LOCKED — Level {item['level_req']}+]"
                elif root_req:
                    status = " [LOCKED — root required]"

                style = "dim" if (locked or root_req) else ("success" if e_slot else "info")
                out.append({"t": style, "s": f"  {item['icon']}  {item['name']}{status}"})
                out.append(_dim(f"       {item['description'][:60]}"))
                if not locked and not root_req:
                    effects = "  ".join(f"{'+' if v>=0 else ''}{v} {k}" for k, v in item.get("passive_effect", {}).items())
                    out.append(_dim(f"       Cost: {cost_str}   Bonuses: {effects}"))
                    out.append(_dim(f"       → gear equip {item_id}"))
                out.append(_dim(""))

        return out

    def get_item_info(self, item_id: str, gs) -> List[dict]:
        """Detailed card for one item."""
        item = GEAR_ITEMS.get(item_id)
        if not item:
            return [_err(f"  Unknown item: {item_id}")]
        equipped = self._equipped(gs)
        inventory = self._inventory(gs)
        is_equipped = equipped.get(item["category"]) == item_id
        is_owned = item_id in inventory
        locked = gs.level < item.get("level_req", 1)

        out = [
            _sys(""),
            _sys(f"  {item['icon']}  {item['name'].upper()}"),
            _dim(f"  Category: {item['category']}  |  Level req: {item['level_req']}"),
            _dim(""),
            _info(f"  {item['description']}"),
            _dim(""),
            _lore(f"  \"{item['lore']}\""),
            _dim(""),
            _sys("  Passive Bonuses:"),
        ]
        for stat, val in item.get("passive_effect", {}).items():
            sign = "+" if val >= 0 else ""
            out.append(_info(f"    {sign}{val} {stat}"))

        cost_str = f"{item['cost_credits']}₵"
        if item.get("cost_data", 0):
            cost_str += f" + {item['cost_data']} data"
        out.append(_dim(""))
        out.append(_dim(f"  Cost: {cost_str}"))
        if is_equipped:
            out.append(_ok("  Status: EQUIPPED"))
        elif is_owned:
            out.append(_ok("  Status: OWNED (not equipped)"))
        elif locked:
            out.append(_warn(f"  Status: LOCKED — requires Level {item['level_req']}"))
        else:
            out.append(_dim(f"  → gear equip {item_id}"))
        out.append(_dim(""))
        return out


# ---------------------------------------------------------------------------
# R7 Skill Check
# ---------------------------------------------------------------------------

def check_skill(gs, skill_name: str, threshold: int) -> Tuple[bool, int, str]:
    """
    Perform a skill check for the given skill against a difficulty threshold.

    Returns:
        (success: bool, margin: int, message: str)

    Margin is positive on success (amount over threshold), negative on failure.
    Applies class passive bonuses and equipped gear bonuses.
    """
    # Base skill value
    base_skill = gs.skills.get(skill_name, 0)

    # Class passive bonus (flat +X from passive multiplier → convert to additive pts)
    class_bonus = 0
    player_class = gs.flags.get("player_class")
    if player_class:
        try:
            from app.game_engine.class_system import ClassSystem
            mult = ClassSystem().get_passive_multiplier(player_class, skill_name)
            # multiplier → bonus points (e.g. 1.15 → +15 pts on a 0-100 scale isn't right;
            # instead give flat +5 per 5% above 1.0)
            if mult > 1.0:
                class_bonus = int((mult - 1.0) * 100)
        except Exception:
            pass

    # Gear passive bonus
    gear_bonus = 0
    try:
        gs_system = GearSystem()
        # Map skill names to gear stats
        _skill_to_stat = {
            "security":         "exploit",
            "hacking":          "exploit",
            "networking":       "scan",
            "recon":            "scan",
            "social_engineering": "social",
            "trust":            "social",
            "forensics":        "recon",
        }
        stat = _skill_to_stat.get(skill_name, skill_name)
        gear_bonus = gs_system.get_bonus(gs, stat)
    except Exception:
        pass

    effective = base_skill + class_bonus + gear_bonus
    margin = effective - threshold

    # Add a small random element ±10 for drama
    roll = random.randint(-10, 10)
    final = effective + roll
    success = final >= threshold
    final_margin = final - threshold

    if success:
        msg = (
            f"Skill check PASSED [{skill_name}]: "
            f"rolled {final} vs threshold {threshold} (margin +{final_margin})"
        )
    else:
        msg = (
            f"Skill check FAILED [{skill_name}]: "
            f"rolled {final} vs threshold {threshold} (margin {final_margin})"
        )

    return success, final_margin, msg


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_system: Optional[GearSystem] = None


def get_system() -> GearSystem:
    global _system
    if _system is None:
        _system = GearSystem()
    return _system


if __name__ == "__main__":
    # Quick self-test
    class _FakeGS:
        level = 10
        skills = {"security": 40}
        flags = {}

    gs = _FakeGS()
    sys_ = GearSystem()

    # Seed some credits via flags fallback
    gs.flags["credits"] = 1000

    # Equip basic_ips (free data, 100 credits)
    result = sys_.equip("basic_ips", gs)
    for r in result:
        print(f"[{r['t']}] {r['s']}")

    print("\nLoadout:")
    for r in sys_.render_loadout(gs):
        print(f"[{r['t']}] {r['s']}")

    ok, margin, msg = check_skill(gs, "security", 30)
    print(f"\nSkill check: {ok} | margin={margin} | {msg}")
