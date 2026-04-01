"""
app/game_engine/cyberware.py — Street-Level Cyberware System
=============================================================
Implants bought from fixers, installed for credits, slots-based.
Different from prestige Augmentations (augmentations.py) — these are
gritty, mid-game, street-market hardware with heat/glitch side-effects.

State stored in gs.flags['cyberware_installed'] (JSON list of aug IDs)
              gs.flags['cyberware_heat'] (int 0-100)
              gs.flags['cyberware_glitch_cd'] (int commands until next glitch)
"""
from __future__ import annotations
import json, random
from typing import Dict, List, Optional, Tuple

# ── Wire helpers ────────────────────────────────────────────────────────────
def _sys(s): return {"t": "system",  "s": s}
def _dim(s): return {"t": "dim",     "s": s}
def _ok(s):  return {"t": "success", "s": s}
def _err(s): return {"t": "error",   "s": s}
def _lore(s):return {"t": "lore",    "s": s}
def _warn(s):return {"t": "warn",    "s": s}
def _line(s, t="info"): return {"t": t, "s": s}

# ── Slot definitions ─────────────────────────────────────────────────────────
SLOTS: Dict[str, int] = {
    "cortex":  3,   # cognitive processing implants
    "reflex":  2,   # reaction / timing implants
    "optical": 2,   # visual enhancement
    "dermal":  2,   # surface / interface layer
    "neural":  1,   # deep neural bridge (rarest, one slot)
}

# ── Implant catalogue ────────────────────────────────────────────────────────
IMPLANTS: Dict[str, Dict] = {
    # CORTEX SLOT
    "syn_cortex": {
        "name": "SYN-Cortex Mk.II", "slot": "cortex", "tier": 1,
        "cost": 800, "heat_per_cmd": 0.3,
        "desc": "Synthetic cortex overlay. +2 to all skill rolls, +10% XP.",
        "effect": {"xp_bonus": 0.10, "skill_flat": 2},
        "lore": "NexusCorp's own implant division. They didn't intend it to be modified.",
        "icon": "🧠",
    },
    "mnemonic_lace": {
        "name": "Mnemonic Lace", "slot": "cortex", "tier": 2,
        "cost": 1500, "heat_per_cmd": 0.5,
        "desc": "Weaves memory architecture. Command history +50 entries. -5% puzzle failure.",
        "effect": {"history_bonus": 50, "puzzle_resist": 0.05},
        "lore": "Surgically threaded into the hippocampal layer. You remember everything now.",
        "icon": "🕸️",
    },
    "overclock_v3": {
        "name": "Overclock v3", "slot": "cortex", "tier": 3,
        "cost": 2500, "heat_per_cmd": 1.2,
        "desc": "Processing overclock. XP bonuses doubled for 10 commands after activation.",
        "effect": {"overclock_commands": 10, "overclock_mult": 2.0},
        "lore": "Your thoughts move at 300% normal speed. Your body can't keep up. Yet.",
        "icon": "⚡",
        "active": True, "active_cmd": "overclock",
    },
    # REFLEX SLOT
    "reflex_buffer": {
        "name": "Reflex Buffer", "slot": "reflex", "tier": 1,
        "cost": 600, "heat_per_cmd": 0.2,
        "desc": "Pre-emptive response buffer. Auto-evades first interception per session.",
        "effect": {"auto_evade": 1},
        "lore": "Your hands move before your eyes see the alert.",
        "icon": "⚔️",
    },
    "pain_editor": {
        "name": "Pain Editor", "slot": "reflex", "tier": 2,
        "cost": 1200, "heat_per_cmd": 0.4,
        "desc": "Blocks trace pain signals. 50% chance to ignore trace escalation per tick.",
        "effect": {"trace_resist": 0.50},
        "lore": "The pain was a feature. You made it a bug.",
        "icon": "💊",
    },
    # OPTICAL SLOT
    "data_eye": {
        "name": "Data-Eye Mk.I", "slot": "optical", "tier": 1,
        "cost": 900, "heat_per_cmd": 0.2,
        "desc": "Reveals hidden .hidden and .zero files in ls output.",
        "effect": {"reveal_hidden": True},
        "lore": "You see the seams now. The files that shouldn't be there.",
        "icon": "👁️",
    },
    "spectrum_scope": {
        "name": "Spectrum Scope", "slot": "optical", "tier": 2,
        "cost": 1800, "heat_per_cmd": 0.6,
        "desc": "Reveals node vulnerability tier in scan output. +15% exploit success.",
        "effect": {"scan_reveal": True, "exploit_bonus": 0.15},
        "lore": "The network is a living organism. You can see its circulation.",
        "icon": "🔭",
    },
    # DERMAL SLOT
    "ghost_chip": {
        "name": "Ghost Chip", "slot": "dermal", "tier": 2,
        "cost": 1400, "heat_per_cmd": 0.3,
        "desc": "+25% stealth. -20% trace gen. Ghost Protocol command unlocked.",
        "effect": {"stealth_bonus": 0.25, "trace_reduction": 0.20, "unlock_ghost": True},
        "lore": "Applied subcutaneously. NexusCorp scanners see a ghost. Nothing more.",
        "icon": "👻",
    },
    "ice_breaker": {
        "name": "ICE Breaker Array", "slot": "dermal", "tier": 3,
        "cost": 3000, "heat_per_cmd": 0.8,
        "desc": "+20% exploit success. Reveals ICE layer depth in scan.",
        "effect": {"exploit_bonus": 0.20, "ice_reveal": True},
        "lore": "Breaks through defensive ICE like water through paper.",
        "icon": "🧊",
    },
    # NEURAL SLOT (rare, 1 slot)
    "lattice_tap": {
        "name": "Lattice Tap", "slot": "neural", "tier": 3,
        "cost": 5000, "heat_per_cmd": 1.0,
        "desc": "+30% social XP. Hear faction background comms. jack-in command unlocked.",
        "effect": {"social_bonus": 0.30, "faction_comms": True, "unlock_jack_in": True},
        "lore": "Direct neural link to the Lattice mesh. You hear everything. Everyone.",
        "icon": "🔗",
    },
}

IMPLANT_IDS = list(IMPLANTS.keys())
FIXER_NAMES = ["Mako", "Vector", "Crux", "Null-3", "The Surgeon", "Ghost-V"]


class CyberwareSystem:
    """Manages cyberware state for a GameState instance."""

    def __init__(self, gs):
        self.gs = gs

    def _installed(self) -> List[str]:
        raw = self.gs.flags.get("cyberware_installed", "[]")
        try: return json.loads(raw) if isinstance(raw, str) else list(raw)
        except: return []

    def _save(self, lst: List[str]):
        self.gs.flags["cyberware_installed"] = json.dumps(lst)

    def _heat(self) -> float:
        return float(self.gs.flags.get("cyberware_heat", 0.0))

    def _add_heat(self, amt: float):
        h = min(100.0, self._heat() + amt)
        self.gs.flags["cyberware_heat"] = h
        return h

    def _cool(self, amt: float = 10.0):
        h = max(0.0, self._heat() - amt)
        self.gs.flags["cyberware_heat"] = h
        return h

    def has(self, imp_id: str) -> bool:
        return imp_id in self._installed()

    def slots_used(self, slot: str) -> int:
        return sum(1 for i in self._installed() if IMPLANTS.get(i, {}).get("slot") == slot)

    def slots_free(self, slot: str) -> int:
        return SLOTS.get(slot, 0) - self.slots_used(slot)

    def effect(self, key: str, default=None):
        """Aggregate a named effect across all installed implants."""
        for imp_id in self._installed():
            e = IMPLANTS.get(imp_id, {}).get("effect", {})
            if key in e:
                return e[key]
        return default

    def effect_sum(self, key: str) -> float:
        """Sum a numeric effect across all installed implants."""
        total = 0.0
        for imp_id in self._installed():
            e = IMPLANTS.get(imp_id, {}).get("effect", {})
            if key in e:
                total += float(e[key])
        return total

    def tick_heat(self) -> Optional[str]:
        """Call on each command. Returns glitch message if heat spikes."""
        installed = self._installed()
        if not installed:
            return None
        total_heat = sum(IMPLANTS.get(i, {}).get("heat_per_cmd", 0) for i in installed)
        heat = self._add_heat(total_heat)
        if heat >= 90:
            glitch_cd = self.gs.flags.get("cyberware_glitch_cd", 0)
            if glitch_cd <= 0:
                self.gs.flags["cyberware_glitch_cd"] = 8
                return random.choice([
                    "⚠ CYBERWARE GLITCH: Optical feed stutters. Vision fragments for 0.3 seconds.",
                    "⚠ CYBERWARE HEAT: SYN-Cortex thermal throttle. Processing at 60%.",
                    "⚠ DERMAL FEEDBACK: Ghost chip registers hostile scan. Counter-measures active.",
                    "⚠ NEURAL OVERFLOW: Lattice Tap receiving fragment storm. Filtering...",
                    "⚠ REFLEX BUFFER: Pain editor suppression cascade. You feel nothing. That's wrong.",
                ])
        elif heat >= 100:
            self.gs.flags["cyberware_heat"] = 80.0  # auto-cool at 100
        cd = self.gs.flags.get("cyberware_glitch_cd", 0)
        if cd > 0:
            self.gs.flags["cyberware_glitch_cd"] = cd - 1
        return None

    def render_catalog(self) -> List[dict]:
        installed = self._installed()
        creds = self.gs.flags.get("credits", 0)
        out = [
            _sys("╔══════════════════════════════════════════════════════════╗"),
            _sys("║  FIXER MARKET — STREET CYBERWARE CATALOG                ║"),
            _sys("╚══════════════════════════════════════════════════════════╝"),
            _dim(f"  Credits: {creds} cr   Heat: {self._heat():.0f}%   Fixer: {random.choice(FIXER_NAMES)}"),
            _dim(""),
        ]
        for slot in SLOTS:
            slot_items = [(k, v) for k, v in IMPLANTS.items() if v["slot"] == slot]
            if not slot_items:
                continue
            used = self.slots_used(slot)
            out.append(_line(f"  ── {slot.upper()} SLOT ({used}/{SLOTS[slot]}) ──────────────────────", "system"))
            for imp_id, imp in slot_items:
                is_inst = imp_id in installed
                can_afford = int(creds) >= imp["cost"] if not is_inst else True
                status = "✓ INSTALLED" if is_inst else f"{imp['cost']} cr"
                t = "success" if is_inst else ("info" if can_afford else "error")
                out.append(_line(f"  {imp['icon']} {imp['name']:<22} [{status:>12}]  T{imp['tier']}", t))
                out.append(_dim(f"      {imp['desc']}"))
            out.append(_dim(""))
        out += [_dim("  cyberware install <id>   cyberware status   cyberware uninstall <id>")]
        return out

    def render_status(self) -> List[dict]:
        installed = self._installed()
        heat = self._heat()
        out = [
            _sys("╔══════════════════════════════════════════════════════════╗"),
            _sys("║  CYBERWARE STATUS                                       ║"),
            _sys("╚══════════════════════════════════════════════════════════╝"),
            _dim(""),
        ]
        heat_bar = "█" * int(heat / 10) + "░" * (10 - int(heat / 10))
        heat_t = "error" if heat >= 80 else "warn" if heat >= 50 else "success"
        out.append(_line(f"  Heat    : [{heat_bar}] {heat:.0f}%", heat_t))
        out.append(_dim(""))
        for slot, cap in SLOTS.items():
            used_ids = [i for i in installed if IMPLANTS.get(i, {}).get("slot") == slot]
            out.append(_line(f"  {slot.upper():<10} {len(used_ids)}/{cap} slots", "system"))
            for imp_id in used_ids:
                imp = IMPLANTS.get(imp_id, {})
                out.append(_line(f"    {imp.get('icon','•')} {imp.get('name', imp_id)}", "success"))
                out.append(_dim(f"       {imp.get('desc','')}"))
            if not used_ids:
                out.append(_dim(f"    (empty)"))
        if not installed:
            out.append(_dim(""))
            out.append(_dim("  No implants installed. Run: cyberware catalog"))
        out.append(_dim(""))
        out.append(_dim("  cyberware catalog | cyberware cool — reduce heat by 15"))
        return out

    def install(self, imp_id: str) -> List[dict]:
        if imp_id not in IMPLANTS:
            return [_err(f"  cyberware: unknown implant '{imp_id}'. Run: cyberware catalog")]
        imp = IMPLANTS[imp_id]
        installed = self._installed()
        if imp_id in installed:
            return [_warn(f"  {imp['name']} already installed.")]
        slot = imp["slot"]
        if self.slots_free(slot) <= 0:
            return [_err(f"  {slot.upper()} slot full ({SLOTS[slot]}/{SLOTS[slot]}). Uninstall first.")]
        creds = int(self.gs.flags.get("credits", 0))
        if creds < imp["cost"]:
            return [_err(f"  Insufficient credits ({creds}/{imp['cost']} cr).")]
        self.gs.flags["credits"] = creds - imp["cost"]
        installed.append(imp_id)
        self._save(installed)
        self._add_heat(15)  # installation heat spike
        self.gs.add_story_beat(f"cyberware_{imp_id}_installed")
        self.gs.add_xp(50, "hacking")
        effects = []
        if imp["effect"].get("unlock_ghost"):
            effects.append("Ghost Protocol command unlocked (ghost activate)")
        if imp["effect"].get("unlock_jack_in"):
            effects.append("Jack-In command unlocked (jack-in <node>)")
        if imp["effect"].get("reveal_hidden"):
            effects.append("Hidden files now visible in ls")
        out = [
            _ok(f"  ✓ INSTALLED: {imp['icon']} {imp['name']}"),
            _lore(f"  [FIXER]: Don't fight the integration sickness. Let it wash through."),
            _dim(f"  Slot used : {slot.upper()}  |  Heat +15%  |  +50 XP"),
        ]
        for e in effects:
            out.append(_line(f"  Effect    : {e}", "success"))
        out.append(_dim(f"  Lore: {imp['lore']}"))
        return out

    def uninstall(self, imp_id: str) -> List[dict]:
        installed = self._installed()
        if imp_id not in installed:
            return [_err(f"  {imp_id} not installed.")]
        installed.remove(imp_id)
        self._save(installed)
        imp = IMPLANTS.get(imp_id, {"name": imp_id, "cost": 0})
        refund = imp.get("cost", 0) // 4  # 25% refund
        self.gs.flags["credits"] = int(self.gs.flags.get("credits", 0)) + refund
        return [
            _warn(f"  Uninstalled: {imp.get('name', imp_id)}"),
            _dim(f"  Refund: {refund} cr (25% of cost)"),
            _dim("  Integration sickness will fade."),
        ]
