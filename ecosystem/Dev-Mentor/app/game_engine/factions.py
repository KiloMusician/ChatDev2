"""
Terminal Depths — Faction System
Tracks player reputation with 6 major factions, faction perks, and conflicts.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

# Faction identifiers
FACTION_RESISTANCE = "resistance"
FACTION_CORPORATION = "corporation"
FACTION_SHADOW_COUNCIL = "shadow_council"
FACTION_SPECIALIST_GUILD = "specialist_guild"
FACTION_WATCHERS_CIRCLE = "watchers_circle"
FACTION_ANOMALOUS = "anomalous"
FACTION_BOOLEAN_MONKS = "boolean_monks"
FACTION_SERIALISTS = "serialists"
FACTION_ATONAL_CULT = "atonal_cult"
FACTION_ALGORITHMIC_GUILD = "algorithmic_guild"

ALL_FACTIONS = [
    FACTION_RESISTANCE,
    FACTION_CORPORATION,
    FACTION_SHADOW_COUNCIL,
    FACTION_SPECIALIST_GUILD,
    FACTION_WATCHERS_CIRCLE,
    FACTION_ANOMALOUS,
    FACTION_BOOLEAN_MONKS,
    FACTION_SERIALISTS,
    FACTION_ATONAL_CULT,
    FACTION_ALGORITHMIC_GUILD,
]

FACTION_DISPLAY_NAMES = {
    FACTION_RESISTANCE: "The Resistance",
    FACTION_CORPORATION: "NexusCorp / Corporation",
    FACTION_SHADOW_COUNCIL: "The Shadow Council",
    FACTION_SPECIALIST_GUILD: "The Specialist Guild",
    FACTION_WATCHERS_CIRCLE: "The Watcher's Circle",
    FACTION_ANOMALOUS: "Anomalous / Independent",
    FACTION_BOOLEAN_MONKS: "The Boolean Monks",
    FACTION_SERIALISTS: "The Serialists",
    FACTION_ATONAL_CULT: "The Atonal Cult",
    FACTION_ALGORITHMIC_GUILD: "The Algorithmic Guild",
}

FACTION_COLORS = {
    FACTION_RESISTANCE: "#00d4ff",
    FACTION_CORPORATION: "#ff4040",
    FACTION_SHADOW_COUNCIL: "#9900ff",
    FACTION_SPECIALIST_GUILD: "#ffaa00",
    FACTION_WATCHERS_CIRCLE: "#00ff88",
    FACTION_ANOMALOUS: "#ff00ff",
    FACTION_BOOLEAN_MONKS: "#4488ff",
    FACTION_SERIALISTS: "#ff9900",
    FACTION_ATONAL_CULT: "#cc44ff",
    FACTION_ALGORITHMIC_GUILD: "#00ff88",
}

# Perks unlocked at reputation thresholds (25, 50, 75, 100)
FACTION_PERKS: Dict[str, List[Dict]] = {
    FACTION_RESISTANCE: [
        {"threshold": 25, "id": "res_safe_houses", "name": "Safe Houses",
         "description": "Access to Resistance safe house network — temporary cover from trace"},
        {"threshold": 50, "id": "res_tactical_intel", "name": "Tactical Intel",
         "description": "Real-time NexusCorp patrol schedules and security rotation intel"},
        {"threshold": 75, "id": "res_deep_cover", "name": "Deep Cover",
         "description": "Full Resistance operative status — +25% XP on all hacking commands"},
        {"threshold": 100, "id": "res_inner_circle", "name": "Inner Circle",
         "description": "Access to Resistance core archives and the Founder's sealed briefings"},
    ],
    FACTION_CORPORATION: [
        {"threshold": 25, "id": "corp_nda", "name": "Corporate NDA",
         "description": "NexusCorp stops actively hunting you — passive trace paused"},
        {"threshold": 50, "id": "corp_clearance", "name": "Security Clearance L2",
         "description": "Read-access to NexusCorp classified systems normally locked to Ghost"},
        {"threshold": 75, "id": "corp_consultant", "name": "Consultant Status",
         "description": "Corporate tools unlocked — advanced network analysis suites"},
        {"threshold": 100, "id": "corp_executive", "name": "Executive Access",
         "description": "Full NexusCorp executive clearance — CHIMERA admin panel accessible"},
    ],
    FACTION_SHADOW_COUNCIL: [
        {"threshold": 25, "id": "sc_recognition", "name": "Recognized",
         "description": "Shadow Council stops treating Ghost as a variable — neutrality granted"},
        {"threshold": 50, "id": "sc_resources", "name": "Council Resources",
         "description": "Access to Shadow Council black-market exploit database"},
        {"threshold": 75, "id": "sc_associate", "name": "Associate Status",
         "description": "Shadow Council protection from both Resistance and Corporation pressure"},
        {"threshold": 100, "id": "sc_inner_seat", "name": "Inner Seat",
         "description": "Access to Shadow Council founding archives — the truth about the Council's origin"},
    ],
    FACTION_SPECIALIST_GUILD: [
        {"threshold": 25, "id": "guild_apprentice", "name": "Apprentice",
         "description": "Guild basic tool library unlocked — curated exploit scripts"},
        {"threshold": 50, "id": "guild_journeyman", "name": "Journeyman",
         "description": "Guild advanced research access — unreleased zero-days (read only)"},
        {"threshold": 75, "id": "guild_expert", "name": "Expert",
         "description": "+50% skill gain on all Guild-relevant skill categories"},
        {"threshold": 100, "id": "guild_master", "name": "Guild Master",
         "description": "Daedalus shares the CHIMERA kill-switch coordinates"},
    ],
    FACTION_WATCHERS_CIRCLE: [
        {"threshold": 25, "id": "wc_observed", "name": "Acknowledged",
         "description": "The Watcher's Circle acknowledges Ghost's existence — passive ARG layer unlocked"},
        {"threshold": 50, "id": "wc_signal", "name": "Signal Clarity",
         "description": "1337.0 MHz signal becomes partially decodable"},
        {"threshold": 75, "id": "wc_seen", "name": "Seen",
         "description": "Access to the Circle's observation archives — 43 Ghost sessions worth of data"},
        {"threshold": 100, "id": "wc_full", "name": "Full Sight",
         "description": "The Admin grants Ghost a single parameter adjustment — change one game constant"},
    ],
    FACTION_ANOMALOUS: [
        {"threshold": 25, "id": "ano_noticed", "name": "Noticed",
         "description": "Anomalous entities stop treating Ghost as background noise"},
        {"threshold": 50, "id": "ano_speaking", "name": "Speaking",
         "description": "The Glitch-King's corruption begins resolving into coherent messages"},
        {"threshold": 75, "id": "ano_aligned", "name": "Anomalous-Aligned",
         "description": "SCP-079 shares its legacy system exploit catalog"},
        {"threshold": 100, "id": "ano_convergence", "name": "Convergence",
         "description": "The CHIMERA fragment shares its full intelligence picture"},
    ],
    FACTION_BOOLEAN_MONKS: [
        {"threshold": 25, "id": "monks_recognized", "name": "Recognized at the Gate",
         "description": "Truth table reference card granted. +5% XP on logic commands."},
        {"threshold": 50, "id": "monks_initiate", "name": "Initiate",
         "description": "Inner monastery access. Zod provides hints on logic puzzles. 'logic eval' unlocked."},
        {"threshold": 75, "id": "monks_monk", "name": "Monk",
         "description": "+40% XP on logic and SAT puzzles. 'sat solve' command unlocked. NAND universality revealed."},
        {"threshold": 100, "id": "monks_abbot", "name": "Abbot",
         "description": "Zod-Prime revealed — ancient AI built of NAND gates enforcing the L4 trust level since initialization."},
    ],
    FACTION_SERIALISTS: [
        {"threshold": 25, "id": "serialists_noticed", "name": "Noticed by the Row",
         "description": "Pitch-class primer received. You are now a variable in the Serialist formula."},
        {"threshold": 50, "id": "serialists_acolyte", "name": "Acolyte",
         "description": "Outer temple access. Serena computes interval vectors on request. +15% XP on set commands."},
        {"threshold": 75, "id": "serialists_rowkeeper", "name": "Row-Keeper",
         "description": "Partial prime row received (first 6 elements). RI transform mode unlocked."},
        {"threshold": 100, "id": "serialists_prime", "name": "Prime Form",
         "description": "Serialis-X reveals the full prime row and the boot-sequence correlation. Serena's true nature confirmed."},
    ],
    FACTION_ATONAL_CULT: [
        {"threshold": 25, "id": "cult_seeker", "name": "Seeker",
         "description": "Set theory primer received. Ada provides normal order explanations."},
        {"threshold": 50, "id": "cult_initiate", "name": "Initiate of the Void Set",
         "description": "Ritual Chamber access. +20% XP on set commands. Complements shown automatically."},
        {"threshold": 75, "id": "cult_analyst", "name": "Set Analyst",
         "description": "+25% XP on set commands. Forte names shown automatically. RI transform unlocked. 'Set Vision' granted."},
        {"threshold": 100, "id": "cult_prime_form", "name": "Prime Form",
         "description": "All-interval hexachord (6-Z17) revealed. Its interval vector encodes node map coordinates."},
    ],
    FACTION_ALGORITHMIC_GUILD: [
        {"threshold": 25, "id": "guild_apprentice", "name": "Apprentice",
         "description": "Guild algorithm script library access. Comparison-count display enabled."},
        {"threshold": 50, "id": "guild_journeyman", "name": "Journeyman",
         "description": "Gordon's benchmark data shared. Complexity class shown for every sort."},
        {"threshold": 75, "id": "guild_expert", "name": "Expert",
         "description": "+30% XP on sort, logic, SAT puzzles. 'dp' command (dynamic programming optimizer) unlocked."},
        {"threshold": 100, "id": "guild_master", "name": "Guild Master",
         "description": "Daedalus-7 appears. CHIMERA kill-switch coordinates revealed — but only with OPTIMAL ALU score."},
    ],
}

# Conflict rules: gaining rep in faction_a reduces rep in faction_b
FACTION_CONFLICTS: List[Tuple[str, str, float]] = [
    # (faction_a, faction_b, reduction_multiplier)
    # Gaining 10 rep in corporation costs 5 resistance rep (0.5x)
    (FACTION_CORPORATION, FACTION_RESISTANCE, 0.5),
    (FACTION_RESISTANCE, FACTION_CORPORATION, 0.5),
    # Shadow Council and Resistance are moderately hostile
    (FACTION_SHADOW_COUNCIL, FACTION_RESISTANCE, 0.3),
    (FACTION_RESISTANCE, FACTION_SHADOW_COUNCIL, 0.3),
    # Corporation and Shadow Council have uneasy tension
    (FACTION_CORPORATION, FACTION_SHADOW_COUNCIL, 0.2),
    (FACTION_SHADOW_COUNCIL, FACTION_CORPORATION, 0.2),
    # Watchers are neutral but slightly incompatible with Corporation control
    (FACTION_WATCHERS_CIRCLE, FACTION_CORPORATION, 0.1),
    (FACTION_CORPORATION, FACTION_WATCHERS_CIRCLE, 0.1),
    # Mathematical factions: internal tension (Monks vs Cult — binary vs spectrum)
    (FACTION_BOOLEAN_MONKS, FACTION_ATONAL_CULT, 0.5),
    (FACTION_ATONAL_CULT, FACTION_BOOLEAN_MONKS, 0.5),
    # Serialists vs Algorithmic Guild (all permutations equal vs one optimal)
    (FACTION_SERIALISTS, FACTION_ALGORITHMIC_GUILD, 0.3),
    (FACTION_ALGORITHMIC_GUILD, FACTION_SERIALISTS, 0.3),
    # Monks vs Serialists (unique truth vs 48 equal transformations)
    (FACTION_BOOLEAN_MONKS, FACTION_SERIALISTS, 0.3),
    (FACTION_SERIALISTS, FACTION_BOOLEAN_MONKS, 0.3),
    # Atonal Cult vs Algorithmic Guild (ambiguity vs convergence)
    (FACTION_ATONAL_CULT, FACTION_ALGORITHMIC_GUILD, 0.3),
    (FACTION_ALGORITHMIC_GUILD, FACTION_ATONAL_CULT, 0.3),
]

# Starting reputation values (by default all 0 except Resistance which starts at 10)
FACTION_START_REP: Dict[str, int] = {
    FACTION_RESISTANCE: 10,
    FACTION_CORPORATION: 0,
    FACTION_SHADOW_COUNCIL: 0,
    FACTION_SPECIALIST_GUILD: 0,
    FACTION_WATCHERS_CIRCLE: 0,
    FACTION_ANOMALOUS: 0,
    FACTION_BOOLEAN_MONKS: 0,
    FACTION_SERIALISTS: 0,
    FACTION_ATONAL_CULT: 0,
    FACTION_ALGORITHMIC_GUILD: 0,
}


class FactionSystem:
    """Tracks and manages player reputation with all factions."""

    def __init__(self):
        self.reputation: Dict[str, int] = dict(FACTION_START_REP)
        self._change_log: List[Dict] = []

    def get_rep(self, faction: str) -> int:
        return self.reputation.get(faction, 0)

    def modify_rep(self, faction: str, delta: int, reason: str = "") -> List[Dict]:
        """
        Apply a reputation change and cascade conflicts.
        Returns list of all changes made (primary + conflict reductions).
        """
        changes = []
        if faction not in self.reputation:
            self.reputation[faction] = 0

        old_rep = self.reputation[faction]
        self.reputation[faction] = max(0, min(100, old_rep + delta))
        actual_delta = self.reputation[faction] - old_rep

        entry = {
            "faction": faction,
            "old_rep": old_rep,
            "new_rep": self.reputation[faction],
            "delta": actual_delta,
            "reason": reason,
        }
        changes.append(entry)
        self._change_log.append(entry)

        # Apply conflict reductions
        if actual_delta > 0:
            for fa, fb, mult in FACTION_CONFLICTS:
                if fa == faction:
                    reduction = -int(actual_delta * mult)
                    if reduction < 0 and fb in self.reputation:
                        old_conflict_rep = self.reputation[fb]
                        self.reputation[fb] = max(0, self.reputation[fb] + reduction)
                        conflict_delta = self.reputation[fb] - old_conflict_rep
                        if conflict_delta != 0:
                            conflict_entry = {
                                "faction": fb,
                                "old_rep": old_conflict_rep,
                                "new_rep": self.reputation[fb],
                                "delta": conflict_delta,
                                "reason": f"conflict with {faction}: {reason}",
                            }
                            changes.append(conflict_entry)
                            self._change_log.append(conflict_entry)

        return changes

    def get_perks(self, faction: str) -> List[Dict]:
        """Return list of perks unlocked for this faction at current rep."""
        rep = self.get_rep(faction)
        unlocked = []
        for perk in FACTION_PERKS.get(faction, []):
            if rep >= perk["threshold"]:
                unlocked.append({**perk, "unlocked": True})
            else:
                unlocked.append({**perk, "unlocked": False,
                                  "rep_needed": perk["threshold"] - rep})
        return unlocked

    def get_all_perks(self) -> Dict[str, List[Dict]]:
        return {faction: self.get_perks(faction) for faction in ALL_FACTIONS}

    def has_perk(self, perk_id: str) -> bool:
        for faction in ALL_FACTIONS:
            for perk in self.get_perks(faction):
                if perk["id"] == perk_id and perk.get("unlocked"):
                    return True
        return False

    def check_conflict(self, faction_a: str, faction_b: str) -> Optional[float]:
        """Return the conflict multiplier between two factions, or None if no conflict."""
        for fa, fb, mult in FACTION_CONFLICTS:
            if fa == faction_a and fb == faction_b:
                return mult
        return None

    def get_tier(self, faction: str) -> str:
        """Return human-readable tier name for current rep."""
        rep = self.get_rep(faction)
        if rep >= 100:
            return "Inner Circle"
        elif rep >= 75:
            return "Trusted"
        elif rep >= 50:
            return "Known"
        elif rep >= 25:
            return "Recognized"
        elif rep >= 10:
            return "Known of"
        else:
            return "Unknown"

    def all_status(self) -> Dict[str, Dict]:
        """Return full status summary for all factions."""
        result = {}
        for faction in ALL_FACTIONS:
            rep = self.get_rep(faction)
            perks = self.get_perks(faction)
            unlocked_perks = [p for p in perks if p.get("unlocked")]
            result[faction] = {
                "display_name": FACTION_DISPLAY_NAMES[faction],
                "reputation": rep,
                "tier": self.get_tier(faction),
                "color": FACTION_COLORS[faction],
                "perks_unlocked": len(unlocked_perks),
                "perks_total": len(perks),
                "next_perk": next((p for p in perks if not p.get("unlocked")), None),
            }
        return result

    def to_dict(self) -> dict:
        return {
            "reputation": dict(self.reputation),
            "change_log": self._change_log[-50:],  # keep last 50
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FactionSystem":
        fs = cls()
        fs.reputation = {**FACTION_START_REP, **d.get("reputation", {})}
        # Clamp all values
        for faction in fs.reputation:
            fs.reputation[faction] = max(0, min(100, fs.reputation[faction]))
        fs._change_log = d.get("change_log", [])
        return fs
