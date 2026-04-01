"""
Terminal Depths — Augmentations Shop
Permanent passive bonuses that persist across prestige resets.
Purchased with prestige currency.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


AUGMENTATION_CATALOGUE = [
    {
        "id": "aug_xp_boost",
        "name": "XP Accelerator",
        "description": "+15% XP gain from all sources.",
        "cost": 3,
        "effect": {"xp_multiplier": 0.15},
        "tier": 1,
        "icon": "⚡",
    },
    {
        "id": "aug_challenge_hint",
        "name": "Challenge Oracle",
        "description": "Unlock free hints for any challenge (unlimited).",
        "cost": 2,
        "effect": {"free_hints": True},
        "tier": 1,
        "icon": "🔮",
    },
    {
        "id": "aug_stock_info",
        "name": "Market Insider",
        "description": "Reveal the next world event before it fires.",
        "cost": 4,
        "effect": {"market_preview": True},
        "tier": 2,
        "icon": "📈",
    },
    {
        "id": "aug_skill_boost",
        "name": "Neural Interface",
        "description": "All skill gains increased by +25%.",
        "cost": 5,
        "effect": {"skill_multiplier": 0.25},
        "tier": 2,
        "icon": "🧠",
    },
    {
        "id": "aug_hidden_commands",
        "name": "Ghost Protocol Alpha",
        "description": "Unlock hidden terminal commands: ghost_exec, shadow_mode.",
        "cost": 6,
        "effect": {"hidden_commands": ["ghost_exec", "shadow_mode"]},
        "tier": 2,
        "icon": "👻",
    },
    {
        "id": "aug_stock_start",
        "name": "Seed Capital",
        "description": "Start each run with +$5,000 in the stock market.",
        "cost": 3,
        "effect": {"stock_bonus_cash": 5000},
        "tier": 1,
        "icon": "💰",
    },
    {
        "id": "aug_prestige_boost",
        "name": "Prestige Echo",
        "description": "+20% prestige currency awarded on each ascension.",
        "cost": 8,
        "effect": {"prestige_multiplier": 0.20},
        "tier": 3,
        "icon": "🌀",
    },
    {
        "id": "aug_challenge_xp",
        "name": "CTF Specialist",
        "description": "+30% XP from completed CTF challenges.",
        "cost": 4,
        "effect": {"challenge_xp_multiplier": 0.30},
        "tier": 2,
        "icon": "🏴",
    },
    {
        "id": "aug_faction_trust",
        "name": "Social Engineer",
        "description": "Trust gains with all factions increased by +20%.",
        "cost": 5,
        "effect": {"faction_trust_multiplier": 0.20},
        "tier": 2,
        "icon": "🤝",
    },
    {
        "id": "aug_infinite_logs",
        "name": "Persistent Memory",
        "description": "Command history is unlimited; never truncated on reset.",
        "cost": 2,
        "effect": {"infinite_history": True},
        "tier": 1,
        "icon": "📜",
    },
    {
        "id": "aug_omega_unlock",
        "name": "Omega Clearance",
        "description": "Tier-3 augmentation. Unlock restricted CHIMERA commands from the start.",
        "cost": 15,
        "effect": {"omega_clearance": True},
        "tier": 3,
        "icon": "☢️",
    },
    # ── Social Engineering ─────────────────────────────────────────────────
    {
        "id": "aug_social_mimic",
        "name": "Voice Mimic",
        "description": "Unlock `impersonate <agent>` — spoof agent identity in faction comms for 60s.",
        "cost": 6,
        "effect": {"social_mimic": True},
        "tier": 2,
        "icon": "🎭",
    },
    {
        "id": "aug_social_blackmail",
        "name": "Kompromat Cache",
        "description": "Store up to 3 faction secrets; trade them for trust bypasses.",
        "cost": 7,
        "effect": {"blackmail_slots": 3},
        "tier": 2,
        "icon": "🗃️",
    },
    {
        "id": "aug_social_doublecross",
        "name": "Burned Bridges Protocol",
        "description": "When faction trust drops to 0, gain a one-time betrayal XP burst (+500 XP).",
        "cost": 5,
        "effect": {"betrayal_xp_burst": 500},
        "tier": 2,
        "icon": "🔥",
    },
    {
        "id": "aug_social_recruiter",
        "name": "Headhunter",
        "description": "Faction recruitment yields +2 contacts per interaction.",
        "cost": 4,
        "effect": {"recruit_bonus": 2},
        "tier": 1,
        "icon": "🪝",
    },
    {
        "id": "aug_social_honeypot",
        "name": "Honeypot Architect",
        "description": "Deploy a passive honeypot that auto-captures one rogue agent per run.",
        "cost": 9,
        "effect": {"honeypot_charges": 1},
        "tier": 3,
        "icon": "🍯",
    },
    # ── Cognitive / Neural ─────────────────────────────────────────────────
    {
        "id": "aug_cog_overclock",
        "name": "Cortex Overclock",
        "description": "Command cooldowns reduced by 20% across all subsystems.",
        "cost": 7,
        "effect": {"cooldown_reduction": 0.20},
        "tier": 2,
        "icon": "⏩",
    },
    {
        "id": "aug_cog_parallel",
        "name": "Parallel Process",
        "description": "Run two terminal commands simultaneously (second runs free, no XP cost).",
        "cost": 10,
        "effect": {"parallel_commands": True},
        "tier": 3,
        "icon": "🔀",
    },
    {
        "id": "aug_cog_memchip",
        "name": "Memory Chip Mk-II",
        "description": "Recall any past command with `recall <n>` even after a prestige reset.",
        "cost": 4,
        "effect": {"cross_prestige_recall": True},
        "tier": 1,
        "icon": "💾",
    },
    {
        "id": "aug_cog_instinct",
        "name": "Combat Instinct",
        "description": "Dungeon fight critical-hit chance increased by +10%.",
        "cost": 5,
        "effect": {"crit_bonus": 0.10},
        "tier": 2,
        "icon": "⚔️",
    },
    {
        "id": "aug_cog_savant",
        "name": "Data Savant",
        "description": "Each unique command run contributes +1 research permanently.",
        "cost": 6,
        "effect": {"research_per_unique_cmd": 1},
        "tier": 2,
        "icon": "📊",
    },
    # ── Stealth / Evasion ──────────────────────────────────────────────────
    {
        "id": "aug_stealth_ghost",
        "name": "Ghost Image",
        "description": "Trace level decays 2× faster while in stealth mode.",
        "cost": 5,
        "effect": {"trace_decay_multiplier": 2.0},
        "tier": 2,
        "icon": "🫥",
    },
    {
        "id": "aug_stealth_proxy",
        "name": "Onion Proxy Chain",
        "description": "Gain 3 proxy charges per run; each absorbs one full trace spike.",
        "cost": 6,
        "effect": {"proxy_charges_per_run": 3},
        "tier": 2,
        "icon": "🧅",
    },
    {
        "id": "aug_stealth_null",
        "name": "Null Signature",
        "description": "First 5 commands of each run generate zero trace.",
        "cost": 4,
        "effect": {"trace_free_start_cmds": 5},
        "tier": 1,
        "icon": "🚫",
    },
    {
        "id": "aug_stealth_decoy",
        "name": "Decoy Node",
        "description": "Deploy one decoy that absorbs the next WATCHER scan per run.",
        "cost": 7,
        "effect": {"decoy_charges_per_run": 1},
        "tier": 2,
        "icon": "🪤",
    },
    {
        "id": "aug_stealth_exfil",
        "name": "Clean Exit Protocol",
        "description": "On death/capture, auto-exfiltrate 50% of current credits to next run.",
        "cost": 8,
        "effect": {"death_credit_carry": 0.50},
        "tier": 3,
        "icon": "🪂",
    },
    # ── Hardware / Physical ────────────────────────────────────────────────
    {
        "id": "aug_hw_battery",
        "name": "High-Cap Battery",
        "description": "Idle engine scripts accumulate resources 50% faster.",
        "cost": 4,
        "effect": {"idle_rate_multiplier": 1.50},
        "tier": 1,
        "icon": "🔋",
    },
    {
        "id": "aug_hw_rig",
        "name": "Black Market Rig",
        "description": "Start each run with a random tier-1 hardware item pre-equipped.",
        "cost": 5,
        "effect": {"start_hardware_tier": 1},
        "tier": 2,
        "icon": "🖥️",
    },
    {
        "id": "aug_hw_antenna",
        "name": "Wide-Band Antenna",
        "description": "OSINT range extended: reveals 2 additional intel fields per target.",
        "cost": 3,
        "effect": {"osint_extra_fields": 2},
        "tier": 1,
        "icon": "📡",
    },
    {
        "id": "aug_hw_emp",
        "name": "EMP Grenade",
        "description": "One-use EMP per run: resets all active WATCHER drones to idle.",
        "cost": 9,
        "effect": {"emp_charges_per_run": 1},
        "tier": 3,
        "icon": "💥",
    },
]

AUG_MAP = {a["id"]: a for a in AUGMENTATION_CATALOGUE}


class AugmentationSystem:
    """Manages purchased augmentations for a player."""

    def __init__(self):
        self._purchased: set[str] = set()

    def get_owned(self) -> List[Dict]:
        return [AUG_MAP[aid] for aid in self._purchased if aid in AUG_MAP]

    def has(self, aug_id: str) -> bool:
        return aug_id in self._purchased

    def get_effect(self, key: str) -> Any:
        """Aggregate an effect value across all owned augmentations."""
        total = 0
        for aid in self._purchased:
            aug = AUG_MAP.get(aid)
            if aug:
                val = aug["effect"].get(key)
                if isinstance(val, (int, float)):
                    total += val
                elif val is True:
                    return True
                elif isinstance(val, list):
                    return val
        return total if total else None

    def xp_multiplier(self) -> float:
        base = self.get_effect("xp_multiplier") or 0
        return 1.0 + base

    def skill_multiplier(self) -> float:
        base = self.get_effect("skill_multiplier") or 0
        return 1.0 + base

    def challenge_xp_multiplier(self) -> float:
        base = self.get_effect("challenge_xp_multiplier") or 0
        return 1.0 + base

    def prestige_multiplier(self) -> float:
        base = self.get_effect("prestige_multiplier") or 0
        return 1.0 + base

    def has_free_hints(self) -> bool:
        return bool(self.get_effect("free_hints"))

    def has_market_preview(self) -> bool:
        return bool(self.get_effect("market_preview"))

    def stock_bonus_cash(self) -> float:
        return self.get_effect("stock_bonus_cash") or 0

    def hidden_commands(self) -> List[str]:
        return self.get_effect("hidden_commands") or []

    def has_omega_clearance(self) -> bool:
        return bool(self.get_effect("omega_clearance"))

    # ── Social ────────────────────────────────────────────────────────────
    def has_social_mimic(self) -> bool:
        return bool(self.get_effect("social_mimic"))

    def blackmail_slots(self) -> int:
        return int(self.get_effect("blackmail_slots") or 0)

    def betrayal_xp_burst(self) -> int:
        return int(self.get_effect("betrayal_xp_burst") or 0)

    def recruit_bonus(self) -> int:
        return int(self.get_effect("recruit_bonus") or 0)

    def honeypot_charges(self) -> int:
        return int(self.get_effect("honeypot_charges") or 0)

    # ── Cognitive ─────────────────────────────────────────────────────────
    def cooldown_reduction(self) -> float:
        return float(self.get_effect("cooldown_reduction") or 0.0)

    def has_parallel_commands(self) -> bool:
        return bool(self.get_effect("parallel_commands"))

    def has_cross_prestige_recall(self) -> bool:
        return bool(self.get_effect("cross_prestige_recall"))

    def crit_bonus(self) -> float:
        return float(self.get_effect("crit_bonus") or 0.0)

    def research_per_unique_cmd(self) -> int:
        return int(self.get_effect("research_per_unique_cmd") or 0)

    # ── Stealth ───────────────────────────────────────────────────────────
    def trace_decay_multiplier(self) -> float:
        base = self.get_effect("trace_decay_multiplier") or 1.0
        return float(base)

    def proxy_charges_per_run(self) -> int:
        return int(self.get_effect("proxy_charges_per_run") or 0)

    def trace_free_start_cmds(self) -> int:
        return int(self.get_effect("trace_free_start_cmds") or 0)

    def decoy_charges_per_run(self) -> int:
        return int(self.get_effect("decoy_charges_per_run") or 0)

    def death_credit_carry(self) -> float:
        return float(self.get_effect("death_credit_carry") or 0.0)

    # ── Hardware ──────────────────────────────────────────────────────────
    def idle_rate_multiplier(self) -> float:
        base = self.get_effect("idle_rate_multiplier") or 1.0
        return float(base)

    def start_hardware_tier(self) -> int:
        return int(self.get_effect("start_hardware_tier") or 0)

    def osint_extra_fields(self) -> int:
        return int(self.get_effect("osint_extra_fields") or 0)

    def emp_charges_per_run(self) -> int:
        return int(self.get_effect("emp_charges_per_run") or 0)

    def purchase(self, aug_id: str, prestige_currency: int) -> Dict[str, Any]:
        if aug_id not in AUG_MAP:
            return {"error": f"Unknown augmentation: {aug_id}"}
        if aug_id in self._purchased:
            return {"error": "Augmentation already installed."}
        aug = AUG_MAP[aug_id]
        if prestige_currency < aug["cost"]:
            return {
                "error": f"Insufficient prestige currency. Need {aug['cost']} ΨP, have {prestige_currency} ΨP."
            }
        self._purchased.add(aug_id)
        return {
            "ok": True,
            "aug": aug,
            "cost": aug["cost"],
            "remaining": prestige_currency - aug["cost"],
        }

    def to_dict(self) -> dict:
        return {"purchased": list(self._purchased)}

    @classmethod
    def from_dict(cls, d: dict) -> "AugmentationSystem":
        aug = cls()
        aug._purchased = set(d.get("purchased", []))
        return aug
