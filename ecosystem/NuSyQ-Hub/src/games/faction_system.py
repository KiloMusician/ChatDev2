"""Faction System — Grey Hack inspired multiplayer collaboration framework.

Defines factions, reputation, shared missions, and competitive/cooperative dynamics.

OmniTag: {
    "purpose": "faction_and_reputation",
    "tags": ["Factions", "Reputation", "Multiplayer", "RPG"],
    "category": "gameplay",
    "evolution_stage": "prototype"
}
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypedDict
from uuid import uuid4

logger = logging.getLogger(__name__)


class FactionAlignment(Enum):
    """Faction philosophical alignment."""

    SYSADMIN = "sysadmin"  # Security-focused, infrastructure
    DATA_SCIENTIST = "data_scientist"  # Analysis-focused, knowledge
    EXPLORER = "explorer"  # Discovery-focused, curiosity
    ARCHITECT = "architect"  # Design-focused, systems
    SENTINEL = "sentinel"  # Defense-focused, protection


class FactionDefinition(TypedDict):
    """Typed structure for built-in faction seed data."""

    name: str
    alignment: FactionAlignment
    description: str


class MissionType(Enum):
    """Types of missions available."""

    RECONNAISSANCE = "reconnaissance"  # Scan and gather info
    INFILTRATION = "infiltration"  # Break into component
    PATCH = "patch"  # Security hardening
    EXTRACTION = "extraction"  # Data/knowledge retrieval
    SABOTAGE = "sabotage"  # Disable or compromise component
    DEFENSE = "defense"  # Protect against attacks
    RESEARCH = "research"  # Investigate and document


@dataclass
class FactionMission:
    """A mission offered by a faction."""

    id: str
    faction_id: str
    title: str
    description: str
    mission_type: MissionType
    target_component: str
    difficulty: int = 1  # 1-5
    reputation_reward: int = 100
    xp_reward: int = 50
    time_limit_minutes: int | None = None
    completed_by: str | None = None
    shared_reward: bool = False  # If True, reward shared across faction


@dataclass
class Faction:
    """A faction with unique missions and rewards."""

    id: str
    name: str
    alignment: FactionAlignment
    description: str
    created_at: str = field(default_factory=lambda: str(__import__("datetime").datetime.now()))
    active_missions: list[str] = field(default_factory=list)
    completed_missions: list[str] = field(default_factory=list)
    global_reputation: int = 0  # Communal reputation
    member_count: int = 0


@dataclass
class AgentFactionMembership:
    """An agent's membership in a faction."""

    agent_id: str
    faction_id: str
    reputation: int = 0
    rank: str = "associate"  # associate, operative, leader, founder
    missions_completed: int = 0
    missions_failed: int = 0
    total_contribution: int = 0  # XP or resource contribution


class FactionSystem:
    """Manages factions, missions, and reputation."""

    def __init__(self):
        """Initialize faction system."""
        self.factions: dict[str, Faction] = {}
        self.memberships: dict[tuple[str, str], AgentFactionMembership] = {}
        self.missions: dict[str, FactionMission] = {}
        self._initialize_default_factions()
        logger.info("FactionSystem initialized")

    def _initialize_default_factions(self) -> None:
        """Initialize built-in factions."""
        default_factions: list[FactionDefinition] = [
            {
                "name": "SysAdmins United",
                "alignment": FactionAlignment.SYSADMIN,
                "description": "Focus on system security, hardening, and infrastructure.",
            },
            {
                "name": "Data Collective",
                "alignment": FactionAlignment.DATA_SCIENTIST,
                "description": "Dedicated to knowledge extraction, analysis, and intelligence.",
            },
            {
                "name": "Explorers Guild",
                "alignment": FactionAlignment.EXPLORER,
                "description": "Driven by curiosity, discovery, and mapping the unknown.",
            },
            {
                "name": "Architects Circle",
                "alignment": FactionAlignment.ARCHITECT,
                "description": "Design and build elegant systems and solutions.",
            },
            {
                "name": "Sentinels",
                "alignment": FactionAlignment.SENTINEL,
                "description": "Guard against threats and maintain system integrity.",
            },
        ]

        for faction_def in default_factions:
            faction = Faction(
                id=str(uuid4()),
                name=faction_def["name"],
                alignment=faction_def["alignment"],
                description=faction_def["description"],
            )
            self.factions[faction.id] = faction
            logger.info(f"Created faction: {faction.name}")

    def create_faction(
        self,
        name: str,
        alignment: FactionAlignment,
        description: str,
        founder_agent_id: str,
    ) -> Faction:
        """Create a new player-defined faction."""
        faction = Faction(
            id=str(uuid4()),
            name=name,
            alignment=alignment,
            description=description,
            member_count=1,
        )
        self.factions[faction.id] = faction

        # Add founder as member
        membership = AgentFactionMembership(
            agent_id=founder_agent_id,
            faction_id=faction.id,
            rank="founder",
            reputation=1000,
        )
        self.memberships[(founder_agent_id, faction.id)] = membership

        logger.info(f"Created faction {faction.name} founded by {founder_agent_id}")
        return faction

    def join_faction(self, agent_id: str, faction_id: str) -> bool:
        """Add an agent to a faction."""
        if faction_id not in self.factions:
            logger.warning(f"Faction not found: {faction_id}")
            return False

        if (agent_id, faction_id) in self.memberships:
            logger.warning(f"Agent {agent_id} already in faction {faction_id}")
            return False

        membership = AgentFactionMembership(
            agent_id=agent_id, faction_id=faction_id, rank="associate"
        )
        self.memberships[(agent_id, faction_id)] = membership

        self.factions[faction_id].member_count += 1
        logger.info(f"Agent {agent_id} joined faction {faction_id}")
        return True

    def create_mission(
        self,
        faction_id: str,
        title: str,
        description: str,
        mission_type: MissionType,
        target_component: str,
        difficulty: int = 1,
        reputation_reward: int = 100,
        xp_reward: int = 50,
        time_limit_minutes: int | None = None,
    ) -> FactionMission:
        """Create a new mission for a faction."""
        mission = FactionMission(
            id=str(uuid4()),
            faction_id=faction_id,
            title=title,
            description=description,
            mission_type=mission_type,
            target_component=target_component,
            difficulty=difficulty,
            reputation_reward=reputation_reward,
            xp_reward=xp_reward,
            time_limit_minutes=time_limit_minutes,
        )
        self.missions[mission.id] = mission

        if faction_id in self.factions:
            self.factions[faction_id].active_missions.append(mission.id)

        logger.info(f"Created mission {mission.id}: {title}")
        return mission

    def complete_mission(self, agent_id: str, mission_id: str) -> dict[str, Any]:
        """Mark a mission as completed by an agent."""
        if mission_id not in self.missions:
            logger.warning(f"Mission not found: {mission_id}")
            return {"success": False, "error": "Mission not found"}

        mission = self.missions[mission_id]

        # Check faction membership
        if (agent_id, mission.faction_id) not in self.memberships:
            logger.warning(f"Agent {agent_id} not in faction {mission.faction_id}")
            return {"success": False, "error": "Not a faction member"}

        mission.completed_by = agent_id

        # Award reputation and XP
        membership = self.memberships[(agent_id, mission.faction_id)]
        membership.reputation += mission.reputation_reward
        membership.missions_completed += 1
        membership.total_contribution += mission.xp_reward

        # Update faction global reputation
        self.factions[mission.faction_id].global_reputation += mission.reputation_reward

        # Move mission from active to completed
        if mission_id in self.factions[mission.faction_id].active_missions:
            self.factions[mission.faction_id].active_missions.remove(mission_id)
        self.factions[mission.faction_id].completed_missions.append(mission_id)

        logger.info(f"Agent {agent_id} completed mission {mission_id}")
        return {
            "success": True,
            "reputation_gained": mission.reputation_reward,
            "xp_gained": mission.xp_reward,
            "new_reputation": membership.reputation,
        }

    def get_agent_reputation(self, agent_id: str, faction_id: str) -> int:
        """Get an agent's reputation in a faction."""
        return self.memberships.get(
            (agent_id, faction_id), AgentFactionMembership(agent_id, faction_id)
        ).reputation

    def get_agent_factions(self, agent_id: str) -> list[dict[str, Any]]:
        """Get all factions an agent belongs to."""
        factions = []
        for (a_id, f_id), membership in self.memberships.items():
            if a_id == agent_id and f_id in self.factions:
                faction = self.factions[f_id]
                factions.append(
                    {
                        "faction_id": f_id,
                        "name": faction.name,
                        "alignment": faction.alignment.value,
                        "reputation": membership.reputation,
                        "rank": membership.rank,
                        "missions_completed": membership.missions_completed,
                    }
                )
        return factions

    def get_faction_missions(
        self, faction_id: str, active_only: bool = True
    ) -> list[dict[str, Any]]:
        """Get all missions for a faction."""
        if faction_id not in self.factions:
            return []

        mission_ids = (
            self.factions[faction_id].active_missions
            if active_only
            else self.factions[faction_id].active_missions
            + self.factions[faction_id].completed_missions
        )

        missions = []
        for mission_id in mission_ids:
            if mission_id in self.missions:
                mission = self.missions[mission_id]
                missions.append(
                    {
                        "id": mission.id,
                        "title": mission.title,
                        "type": mission.mission_type.value,
                        "target": mission.target_component,
                        "difficulty": mission.difficulty,
                        "reputation_reward": mission.reputation_reward,
                        "completed_by": mission.completed_by,
                    }
                )
        return missions

    def get_leaderboard(self, faction_id: str | None = None) -> list[dict[str, Any]]:
        """Get reputation leaderboard for a faction or all factions."""
        entries = []
        for (agent_id, f_id), membership in self.memberships.items():
            if (faction_id is None or f_id == faction_id) and f_id in self.factions:
                entries.append(
                    {
                        "agent_id": agent_id,
                        "faction": self.factions[f_id].name,
                        "reputation": membership.reputation,
                        "rank": membership.rank,
                        "missions_completed": membership.missions_completed,
                    }
                )

        # Sort by reputation descending
        entries.sort(key=lambda x: x["reputation"], reverse=True)
        return entries[:20]  # Top 20


# Global instance
_faction_system: FactionSystem | None = None


def get_faction_system() -> FactionSystem:
    """Get or create global FactionSystem instance."""
    global _faction_system
    if _faction_system is None:
        _faction_system = FactionSystem()
    return _faction_system
