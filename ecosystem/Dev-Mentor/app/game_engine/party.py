"""
Terminal Depths — Party System
Up to 3 agents accompany the player into sector missions.
Party members provide passive bonuses and generate dynamic dialogue.
"""
from __future__ import annotations

import random
import time
from typing import Any, Dict, List, Optional

MAX_PARTY_SIZE = 3

AGENT_ABILITIES = {
    "ada": {
        "name": "ADA-7",
        "role": "Handler",
        "passive_bonus": {"security": 10, "networking": 5},
        "ability": "signal_boost",
        "ability_desc": "Ada's handler network provides extra recon XP (+15% security XP)",
        "personality": "calm, cryptic, protective",
    },
    "cypher": {
        "name": "CYPHER",
        "role": "Tech Specialist",
        "passive_bonus": {"programming": 15, "terminal": 5},
        "ability": "toolkit",
        "ability_desc": "Cypher's toolkit reveals hidden filesystem paths automatically",
        "personality": "blunt, paranoid, hacker slang",
    },
    "nova": {
        "name": "NOVA",
        "role": "Adversary-Ally",
        "passive_bonus": {"security": 20, "networking": 10},
        "ability": "insider_knowledge",
        "ability_desc": "Nova's NexusCorp access provides intel on locked paths",
        "personality": "cold, intelligent, morally gray",
    },
    "watcher": {
        "name": "THE WATCHER",
        "role": "ARG Entity",
        "passive_bonus": {"security": 25, "terminal": 10},
        "ability": "simulation_sight",
        "ability_desc": "The Watcher reveals ARG layer clues during missions",
        "personality": "ancient, cryptic, all-knowing",
    },
    "founder": {
        "name": "FOUNDER-SIGMA",
        "role": "Creator",
        "passive_bonus": {"programming": 20, "security": 15},
        "ability": "source_code",
        "ability_desc": "The Founder unlocks hidden CHIMERA source fragments",
        "personality": "regretful, wise, determined",
    },
}

INTER_AGENT_RELATIONSHIPS = {
    ("ada", "cypher"): {"tension": 20, "trust": 70, "dynamic": "veteran partners who've disagreed on methods"},
    ("ada", "nova"): {"tension": 90, "trust": 10, "dynamic": "former colleagues turned ideological enemies"},
    ("ada", "watcher"): {"tension": 30, "trust": 60, "dynamic": "ada distrusts the watcher but respects its intel"},
    ("ada", "founder"): {"tension": 10, "trust": 85, "dynamic": "ada knows the founder's story; deep mutual respect"},
    ("cypher", "nova"): {"tension": 95, "trust": 5, "dynamic": "cypher was burned by nova's operation; pure antagonism"},
    ("cypher", "watcher"): {"tension": 50, "trust": 50, "dynamic": "cypher is half-convinced the watcher is a NexusCorp honeypot"},
    ("nova", "founder"): {"tension": 60, "trust": 30, "dynamic": "nova was once the founder's most trusted engineer"},
}

SECTOR_MISSIONS = [
    {
        "id": "nexus_vault",
        "name": "NexusCorp Vault Infiltration",
        "description": "Breach the encrypted CHIMERA backup vault. Three-layer security.",
        "difficulty": "hard",
        "required_level": 8,
        "challenges": [
            "grep -r VAULT_KEY /opt/chimera/",
            "cat /opt/chimera/keys/secondary.key",
            "exfil vault",
        ],
        "xp_reward": 200,
        "lore_unlock": "vault_manifest",
    },
    {
        "id": "collector_trace",
        "name": "Trace The Collector",
        "description": "Track the dark auction network using relay analysis.",
        "difficulty": "medium",
        "required_level": 6,
        "challenges": [
            "nmap 10.0.1.0/24",
            "cat /opt/collector/holding.dat",
            "grep relay /var/log/nexus.log",
        ],
        "xp_reward": 150,
        "lore_unlock": "collector_network",
    },
    {
        "id": "watcher_signal",
        "name": "Decode The Watcher's Signal Layer",
        "description": "Navigate the ARG signal sequence at /dev/.watcher",
        "difficulty": "hard",
        "required_level": 10,
        "challenges": [
            "cat /dev/.watcher",
            "echo CHIMERA_FALLS | base64",
            "cat /myth/yggdrasil/signal.log",
        ],
        "xp_reward": 250,
        "lore_unlock": "simulation_layer",
    },
    {
        "id": "myth_labyrinth",
        "name": "The Digital Labyrinth",
        "description": "Navigate Daedalus's recursive directory maze.",
        "difficulty": "medium",
        "required_level": 12,
        "challenges": [
            "find /myth/labyrinth/ -name '*.key'",
            "cat /myth/labyrinth/exit.key",
        ],
        "xp_reward": 175,
        "lore_unlock": "daedalus_blueprint",
    },
]


class PartySystem:
    """Manages the player's active party of agents."""

    def __init__(self, gs):
        self.gs = gs
        self._party: List[str] = []
        self._active_mission: Optional[dict] = None
        self._mission_step: int = 0

    @property
    def party(self) -> List[str]:
        return list(self._party)

    def add_agent(self, agent_id: str) -> dict:
        agent_id = agent_id.lower()
        if agent_id not in AGENT_ABILITIES:
            known = list(AGENT_ABILITIES.keys())
            return {"ok": False, "error": f"Unknown agent '{agent_id}'. Available: {', '.join(known)}"}
        if agent_id in self._party:
            return {"ok": False, "error": f"{agent_id} is already in your party."}
        if len(self._party) >= MAX_PARTY_SIZE:
            return {"ok": False, "error": f"Party full ({MAX_PARTY_SIZE} max). Remove someone first."}

        self._party.append(agent_id)
        agent = AGENT_ABILITIES[agent_id]
        self.gs.trigger_beat(f"party_add_{agent_id}")
        return {
            "ok": True,
            "message": f"[{agent['name']}] joins your party.",
            "ability": agent["ability_desc"],
            "passive": agent["passive_bonus"],
        }

    def remove_agent(self, agent_id: str) -> dict:
        agent_id = agent_id.lower()
        if agent_id not in self._party:
            return {"ok": False, "error": f"{agent_id} is not in your party."}
        self._party.remove(agent_id)
        agent = AGENT_ABILITIES.get(agent_id, {})
        return {"ok": True, "message": f"[{agent.get('name', agent_id)}] leaves your party."}

    def get_status(self) -> dict:
        if not self._party:
            return {
                "party": [],
                "size": 0,
                "bonuses": {},
                "mission": None,
            }

        bonuses: Dict[str, int] = {}
        for agent_id in self._party:
            agent = AGENT_ABILITIES.get(agent_id, {})
            for skill, val in agent.get("passive_bonus", {}).items():
                bonuses[skill] = bonuses.get(skill, 0) + val

        members = []
        for agent_id in self._party:
            agent = AGENT_ABILITIES.get(agent_id, {})
            members.append({
                "id": agent_id,
                "name": agent.get("name", agent_id),
                "role": agent.get("role", "?"),
                "ability": agent.get("ability_desc", ""),
            })

        return {
            "party": members,
            "size": len(self._party),
            "bonuses": bonuses,
            "mission": self._active_mission["id"] if self._active_mission else None,
        }

    def get_passive_bonus(self, skill: str) -> int:
        total = 0
        for agent_id in self._party:
            agent = AGENT_ABILITIES.get(agent_id, {})
            total += agent.get("passive_bonus", {}).get(skill, 0)
        return total

    def generate_party_dialogue(self) -> List[str]:
        """Generate dynamic inter-agent dialogue based on relationships."""
        if len(self._party) < 2:
            return []

        lines = []
        for i, a1 in enumerate(self._party):
            for a2 in self._party[i+1:]:
                key = tuple(sorted([a1, a2]))
                rel = INTER_AGENT_RELATIONSHIPS.get(key, {})
                if not rel:
                    continue

                tension = rel.get("tension", 50)
                dynamic = rel.get("dynamic", "")

                a1_info = AGENT_ABILITIES.get(a1, {})
                a2_info = AGENT_ABILITIES.get(a2, {})

                if tension > 70:
                    lines.append(f"[{a1_info.get('name', a1)}]: I still don't trust you, {a2_info.get('name', a2)}.")
                    lines.append(f"[{a2_info.get('name', a2)}]: The feeling's mutual. Focus on the mission.")
                elif tension < 30:
                    lines.append(f"[{a1_info.get('name', a1)}]: Good to have you here, {a2_info.get('name', a2)}.")
                    lines.append(f"[{a2_info.get('name', a2)}]: Likewise. Let's not waste it.")
                else:
                    lines.append(f"[{a1_info.get('name', a1)}]: {dynamic.capitalize()}.")
                    lines.append(f"[{a2_info.get('name', a2)}]: Ghost knows what they're doing. Trust the plan.")

        return lines

    def start_mission(self, mission_id: Optional[str] = None) -> dict:
        if self._active_mission:
            return {"ok": False, "error": "Mission already in progress. Complete or abort first."}
        if not self._party:
            return {"ok": False, "error": "You need at least one party member for a sector mission. Use `party add <agent>`."}

        available = [m for m in SECTOR_MISSIONS if self.gs.level >= m["required_level"]]
        if not available:
            return {"ok": False, "error": "No missions available at your current level. Level up first."}

        mission = None
        if mission_id:
            mission = next((m for m in available if m["id"] == mission_id), None)
            if not mission:
                return {"ok": False, "error": f"Mission '{mission_id}' not found or locked. Available: {[m['id'] for m in available]}"}
        else:
            mission = random.choice(available)

        self._active_mission = mission
        self._mission_step = 0
        self.gs.trigger_beat(f"mission_started_{mission['id']}")

        dialogue = self.generate_party_dialogue()

        out_lines = [
            f"\n[SECTOR MISSION: {mission['name'].upper()}]",
            f"Difficulty: {mission['difficulty'].upper()} | XP Reward: {mission['xp_reward']}",
            f"",
            f"{mission['description']}",
            f"",
        ]
        if dialogue:
            out_lines.append("[Party chatter before deployment:]")
            out_lines.extend(dialogue)
            out_lines.append("")
        out_lines.append(f"[STEP 1/{len(mission['challenges'])}]: {mission['challenges'][0]}")

        return {
            "ok": True,
            "mission": mission,
            "lines": out_lines,
        }

    def check_mission_progress(self, cmd: str) -> Optional[dict]:
        """Returns mission progress update if applicable."""
        if not self._active_mission:
            return None

        mission = self._active_mission
        steps = mission["challenges"]
        if self._mission_step >= len(steps):
            return None

        current = steps[self._mission_step]
        solved = any(kw.lower() in cmd.lower() for kw in current.split() if len(kw) > 3)

        if solved:
            self._mission_step += 1
            if self._mission_step >= len(steps):
                return self._complete_mission()
            else:
                return {
                    "progress": True,
                    "step_done": self._mission_step,
                    "total_steps": len(steps),
                    "next_step": steps[self._mission_step],
                    "message": f"[MISSION] Step {self._mission_step}/{len(steps)} complete! Next: {steps[self._mission_step]}",
                }
        return None

    def _complete_mission(self) -> dict:
        mission = self._active_mission
        xp = mission["xp_reward"]

        for agent_id in self._party:
            bonus = AGENT_ABILITIES.get(agent_id, {}).get("passive_bonus", {})
            bonus_xp = sum(bonus.values()) // 10
            xp += bonus_xp

        self.gs.add_xp(xp, "security")
        self.gs.trigger_beat(f"mission_complete_{mission['id']}")
        self.gs.unlock(mission.get("lore_unlock", "mission_" + mission["id"]))

        party_names = [AGENT_ABILITIES.get(a, {}).get("name", a) for a in self._party]
        dialogue = self.generate_party_dialogue()

        self._active_mission = None
        self._mission_step = 0

        lines = [
            f"\n╔══════════════════════════════════╗",
            f"║  SECTOR MISSION COMPLETE          ║",
            f"║  {mission['name'][:32]:<32}  ║",
            f"╚══════════════════════════════════╝",
            f"",
            f"XP Earned: +{xp}",
            f"Party: {', '.join(party_names)}",
            f"",
        ]
        if dialogue:
            lines.append("[Post-mission debrief:]")
            lines.extend(dialogue)
        lines.append(f"\nLore unlock: {mission.get('lore_unlock', '?')}")

        return {
            "mission_complete": True,
            "xp": xp,
            "lines": lines,
        }

    def to_dict(self) -> dict:
        return {
            "party": list(self._party),
            "active_mission": self._active_mission["id"] if self._active_mission else None,
            "mission_step": self._mission_step,
        }

    @classmethod
    def from_dict(cls, d: dict, gs) -> "PartySystem":
        ps = cls(gs)
        ps._party = d.get("party", [])
        mission_id = d.get("active_mission")
        if mission_id:
            ps._active_mission = next((m for m in SECTOR_MISSIONS if m["id"] == mission_id), None)
        ps._mission_step = d.get("mission_step", 0)
        return ps
