"""
panel_manager.py — Unlockable Panel System
Every panel maps to both a terminal form and a graphical form.
Panels unlock based on story beats, level, and skill progression.
This is the authoritative source for panel state across both UIs.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class PanelDef:
    id: str
    label: str
    tab_key: str                    # key used in frontend tab system
    terminal_cmd: str               # equivalent terminal command(s)
    graphical_form: str             # description of graphical representation
    unlock_condition: str           # human-readable unlock condition
    # Unlock gates — all that apply must be True
    always: bool = False
    min_level: int = 0
    required_beats: List[str] = field(default_factory=list)
    required_skill: Optional[str] = None
    required_skill_min: int = 0
    faction_required: bool = False
    compression_note: str = ""


# ── Panel registry — the canonical definition of every panel ─────────────────
ALL_PANELS: List[PanelDef] = [
    PanelDef(
        id="terminal", label="Terminal", tab_key="terminal",
        terminal_cmd="(main terminal)", graphical_form="xterm.js panel",
        unlock_condition="always", always=True,
        compression_note="text-native; graphical is a styled wrapper"
    ),
    PanelDef(
        id="objective", label="Active Objective", tab_key="objective",
        terminal_cmd="tutorial | story", graphical_form="OBJ tab",
        unlock_condition="always", always=True,
        compression_note="tutorial-driven; no separate data model"
    ),
    PanelDef(
        id="stats", label="Identity & Stats", tab_key="stats",
        terminal_cmd="status | skills", graphical_form="STATS tab",
        unlock_condition="always", always=True,
        compression_note="live game state — zero storage cost"
    ),
    PanelDef(
        id="tutorial", label="Tutorial Guide", tab_key="tutorial",
        terminal_cmd="tutorial", graphical_form="TUT tab",
        unlock_condition="always", always=True,
        compression_note="42-step sequence; text-only"
    ),
    PanelDef(
        id="challenges", label="Challenges", tab_key="challenges",
        terminal_cmd="challenges", graphical_form="CHAL tab",
        unlock_condition="always", always=True,
        compression_note="35 challenges; code-defined"
    ),
    PanelDef(
        id="timeline", label="Event Timeline", tab_key="timeline",
        terminal_cmd="timeline", graphical_form="LOG tab",
        unlock_condition="always", always=True,
        compression_note="in-memory ring buffer; no persistence"
    ),
    PanelDef(
        id="skills", label="Skill Tree", tab_key="skills",
        terminal_cmd="skills | density", graphical_form="TREE tab — SVG skill graph",
        unlock_condition="reach level 5", min_level=5,
        compression_note="SVG procedurally generated from skill data"
    ),
    PanelDef(
        id="quest", label="Quest Log", tab_key="quest",
        terminal_cmd="timeline beats | story", graphical_form="QUEST tab — categorized quest list",
        unlock_condition="first story beat",
        required_beats=["boot"],
        compression_note="beats-driven; no separate quest DB"
    ),
    PanelDef(
        id="lore", label="Lore Library", tab_key="lore",
        terminal_cmd="cat /var/msg/* | lore", graphical_form="LORE tab — fragment list",
        unlock_condition="find 5 hidden files", min_level=3,
        compression_note="text fragments; no binary assets"
    ),
    PanelDef(
        id="map", label="Network Map", tab_key="map",
        terminal_cmd="graph | map", graphical_form="MAP tab — ASCII node graph",
        unlock_condition="discover 3 nodes", min_level=2,
        compression_note="same data model, two projections"
    ),
    PanelDef(
        id="agent_chat", label="Agent Chat", tab_key="agent_chat",
        terminal_cmd="talk <agent> | hive", graphical_form="CHAT panel — agent messages with avatars",
        unlock_condition="first Ada contact",
        required_beats=["ada_first_contact", "boot"],
        compression_note="text-native; graphical adds avatars"
    ),
    PanelDef(
        id="faction_status", label="Faction Status", tab_key="faction",
        terminal_cmd="faction", graphical_form="Faction status bar (persistent)",
        unlock_condition="join a faction", faction_required=True,
        compression_note="persistent bar — always visible once unlocked"
    ),
    PanelDef(
        id="compression_chamber", label="Compression Chamber", tab_key="compress",
        terminal_cmd="compress | density", graphical_form="COMPRESS panel — stellar stage meter",
        unlock_condition="reach level 10", min_level=10,
        compression_note="mechanics are the metaphor — meta-game layer"
    ),
    PanelDef(
        id="anomaly_registry", label="Anomaly Registry", tab_key="anomaly",
        terminal_cmd="anomaly", graphical_form="ANOMALY panel — SCP-style registry",
        unlock_condition="first anomaly interaction",
        required_beats=["anomaly_first_view"],
        compression_note="4 anomalies; procedural — no external data"
    ),
    PanelDef(
        id="script_editor", label="Script Editor", tab_key="scripts",
        terminal_cmd="script write | script run", graphical_form="SCRIPTS panel — syntax-highlighted editor",
        unlock_condition="write first script", min_level=8,
        compression_note="terminal form is primary; graphical adds highlighting"
    ),
    PanelDef(
        id="darknet_market", label="Darknet Market", tab_key="darknet",
        terminal_cmd="darknet market", graphical_form="DARKNET panel — market UI",
        unlock_condition="trace level > 20 or level 12",
        min_level=12,
        compression_note="8 items; all procedural — no art assets"
    ),
    PanelDef(
        id="council", label="AI Council", tab_key="council",
        terminal_cmd="council convene", graphical_form="COUNCIL panel — 7-member vote UI",
        unlock_condition="reach level 20", min_level=20,
        compression_note="probabilistic vote — no stored history"
    ),
    PanelDef(
        id="panels", label="Panel Manager", tab_key="panels",
        terminal_cmd="panels", graphical_form="PANELS overlay — unlock status",
        unlock_condition="always", always=True,
        compression_note="metadata-driven; self-referential"
    ),
]

PANEL_BY_ID: Dict[str, PanelDef] = {p.id: p for p in ALL_PANELS}


class PanelUnlockManager:
    """
    Determines which panels are unlocked for a given game state.
    Used by both the terminal (/api/ui/panels) and graphical UI (game.js).
    """

    def get_unlocked(self, gs_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return list of unlocked panel dicts given a serialized GameState."""
        level = gs_dict.get("level", 1)
        beats = set(gs_dict.get("story_beats", []))
        skills = gs_dict.get("skills", {})
        faction = gs_dict.get("faction")

        unlocked = []
        for p in ALL_PANELS:
            if self._is_unlocked(p, level, beats, skills, faction):
                unlocked.append(self._to_dict(p, unlocked=True))

        return unlocked

    def get_all_with_status(self, gs_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return all panels with unlock status."""
        level = gs_dict.get("level", 1)
        beats = set(gs_dict.get("story_beats", []))
        skills = gs_dict.get("skills", {})
        faction = gs_dict.get("faction")

        return [
            self._to_dict(p, unlocked=self._is_unlocked(p, level, beats, skills, faction))
            for p in ALL_PANELS
        ]

    def _is_unlocked(self, p: PanelDef, level: int, beats: set,
                     skills: dict, faction: Optional[str]) -> bool:
        if p.always:
            return True
        if level < p.min_level:
            return False
        if p.required_beats and not any(b in beats for b in p.required_beats):
            return False
        if p.faction_required and not faction:
            return False
        if p.required_skill and skills.get(p.required_skill, 0) < p.required_skill_min:
            return False
        return True

    def _to_dict(self, p: PanelDef, unlocked: bool) -> Dict[str, Any]:
        return {
            "id": p.id,
            "label": p.label,
            "tab_key": p.tab_key,
            "terminal_cmd": p.terminal_cmd,
            "graphical_form": p.graphical_form,
            "unlock_condition": p.unlock_condition,
            "unlocked": unlocked,
            "compression_note": p.compression_note,
        }

    def newly_unlocked(self, prev_gs: Dict[str, Any],
                       curr_gs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return panels that became unlocked between two game states."""
        prev_ids = {p["id"] for p in self.get_unlocked(prev_gs)}
        curr_ids = {p["id"] for p in self.get_unlocked(curr_gs)}
        new_ids  = curr_ids - prev_ids
        return [self._to_dict(PANEL_BY_ID[pid], unlocked=True)
                for pid in new_ids if pid in PANEL_BY_ID]


# Singleton
panel_manager = PanelUnlockManager()
