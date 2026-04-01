"""Multiplayer Faction Collaboration System.

Provides:
- Faction management (join, leave, ranks)
- Territory control mechanics
- Collaborative missions
- Inter-faction relations (war/alliance/neutral)
- Resource pooling
- Leaderboards by faction
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import ClassVar

logger = logging.getLogger(__name__)


class FactionType(Enum):
    """Available factions in the game."""

    CYBER_COLLECTIVE = "Cyber Collective"
    SHADOW_SYNDICATE = "Shadow Syndicate"
    NEON_KNIGHTS = "Neon Knights"
    DATA_MONKS = "Data Monks"
    ROGUE_AGENTS = "Rogue Agents"


class FactionRank(Enum):
    """Ranks within a faction."""

    INITIATE = ("Initiate", 0)
    MEMBER = ("Member", 100)
    VETERAN = ("Veteran", 500)
    ELITE = ("Elite", 1500)
    OFFICER = ("Officer", 3000)
    COMMANDER = ("Commander", 6000)
    LEADER = ("Leader", 10000)

    def __init__(self, title: str, xp_required: int):
        """Initialize FactionRank with title, xp_required."""
        self.title = title
        self.xp_required = xp_required


class RelationType(Enum):
    """Relations between factions."""

    WAR = "war"
    HOSTILE = "hostile"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    ALLIANCE = "alliance"


@dataclass
class FactionMember:
    """A member of a faction."""

    player_id: str
    faction: FactionType
    rank: FactionRank = FactionRank.INITIATE
    contribution_xp: int = 0
    missions_completed: int = 0
    joined_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "faction": self.faction.value,
            "rank": self.rank.name,
            "contribution_xp": self.contribution_xp,
            "missions_completed": self.missions_completed,
            "joined_at": self.joined_at.isoformat(),
            "last_active": self.last_active.isoformat(),
        }


@dataclass
class Territory:
    """A territory that can be controlled by factions."""

    territory_id: str
    name: str
    owner: FactionType | None = None
    control_points: int = 0  # 0-1000
    resources_per_day: int = 10
    strategic_value: int = 1  # 1-5
    contested: bool = False

    def to_dict(self) -> dict:
        return {
            "territory_id": self.territory_id,
            "name": self.name,
            "owner": self.owner.value if self.owner else None,
            "control_points": self.control_points,
            "resources_per_day": self.resources_per_day,
            "strategic_value": self.strategic_value,
            "contested": self.contested,
        }


@dataclass
class FactionMission:
    """A collaborative faction mission."""

    mission_id: str
    name: str
    description: str
    faction: FactionType
    required_participants: int = 3
    current_participants: list[str] = field(default_factory=list)
    target_territory: str | None = None
    xp_reward: int = 500
    resource_reward: int = 100
    status: str = "open"  # open, in_progress, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    deadline_hours: int = 24

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "name": self.name,
            "description": self.description,
            "faction": self.faction.value,
            "required_participants": self.required_participants,
            "current_participants": self.current_participants,
            "target_territory": self.target_territory,
            "xp_reward": self.xp_reward,
            "resource_reward": self.resource_reward,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "deadline_hours": self.deadline_hours,
        }


@dataclass
class FactionState:
    """State of a faction."""

    faction: FactionType
    total_members: int = 0
    total_xp: int = 0
    resources: int = 1000
    territories_owned: int = 0
    missions_completed: int = 0
    relations: dict[str, str] = field(default_factory=dict)  # faction -> relation

    def to_dict(self) -> dict:
        return {
            "faction": self.faction.value,
            "total_members": self.total_members,
            "total_xp": self.total_xp,
            "resources": self.resources,
            "territories_owned": self.territories_owned,
            "missions_completed": self.missions_completed,
            "relations": self.relations,
        }


class FactionManager:
    """Manages multiplayer faction gameplay.

    Handles faction membership, territories, missions, and relations.
    """

    # Default territories
    DEFAULT_TERRITORIES: ClassVar[list] = [
        ("core_nexus", "Core Nexus", 5, 50),
        ("data_vault", "Data Vault", 4, 40),
        ("shadow_market", "Shadow Market", 3, 30),
        ("neon_district", "Neon District", 3, 25),
        ("outer_rim", "Outer Rim", 2, 15),
        ("ghost_sector", "Ghost Sector", 2, 15),
        ("archive_depths", "Archive Depths", 4, 35),
        ("quantum_fields", "Quantum Fields", 5, 45),
    ]

    # Mission templates
    MISSION_TEMPLATES: ClassVar[list] = [
        ("raid", "Territory Raid", "Assault enemy territory to gain control", 3, 500),
        ("defend", "Defense Protocol", "Defend our territory from attackers", 2, 300),
        ("heist", "Data Heist", "Steal valuable data from rival faction", 4, 700),
        ("recruit", "Recruitment Drive", "Bring new members to our cause", 2, 200),
        ("sabotage", "Sabotage Mission", "Disrupt enemy operations", 3, 450),
        ("alliance", "Diplomatic Mission", "Negotiate with another faction", 2, 250),
    ]

    def __init__(self, state_dir: Path | None = None):
        """Initialize FactionManager with state_dir."""
        self.state_dir = state_dir or Path("state/factions")
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Initialize faction states
        self.factions: dict[FactionType, FactionState] = {
            ft: FactionState(faction=ft) for ft in FactionType
        }

        # Initialize default relations (neutral)
        for faction in FactionType:
            self.factions[faction].relations = {
                other.value: RelationType.NEUTRAL.value for other in FactionType if other != faction
            }

        # Members dict
        self.members: dict[str, FactionMember] = {}

        # Territories
        self.territories: dict[str, Territory] = {
            tid: Territory(tid, name, strategic_value=sv, resources_per_day=rpd)
            for tid, name, sv, rpd in self.DEFAULT_TERRITORIES
        }

        # Active missions
        self.active_missions: dict[str, FactionMission] = {}

        # Load state
        self._load_state()

    def _load_state(self) -> None:
        """Load faction state from disk."""
        state_file = self.state_dir / "faction_state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)

                # Restore members
                for member_data in data.get("members", []):
                    member = FactionMember(
                        player_id=member_data["player_id"],
                        faction=FactionType(member_data["faction"]),
                        rank=FactionRank[member_data["rank"]],
                        contribution_xp=member_data["contribution_xp"],
                        missions_completed=member_data["missions_completed"],
                        joined_at=datetime.fromisoformat(member_data["joined_at"]),
                        last_active=datetime.fromisoformat(member_data["last_active"]),
                    )
                    self.members[member.player_id] = member
                    self.factions[member.faction].total_members += 1

                logger.info(f"Loaded faction state: {len(self.members)} members")
            except Exception as e:
                logger.warning(f"Could not load faction state: {e}")

    def _save_state(self) -> None:
        """Save faction state to disk."""
        state_file = self.state_dir / "faction_state.json"
        data = {
            "members": [m.to_dict() for m in self.members.values()],
            "factions": [f.to_dict() for f in self.factions.values()],
            "territories": [t.to_dict() for t in self.territories.values()],
            "missions": [m.to_dict() for m in self.active_missions.values()],
            "saved_at": datetime.now().isoformat(),
        }
        with open(state_file, "w") as f:
            json.dump(data, f, indent=2)

    def join_faction(self, player_id: str, faction: FactionType) -> FactionMember:
        """Join a faction."""
        # Leave current faction if any
        if player_id in self.members:
            self.leave_faction(player_id)

        member = FactionMember(player_id=player_id, faction=faction)
        self.members[player_id] = member
        self.factions[faction].total_members += 1

        self._save_state()
        logger.info(f"Player {player_id} joined {faction.value}")

        return member

    def leave_faction(self, player_id: str) -> bool:
        """Leave current faction."""
        if player_id not in self.members:
            return False

        member = self.members.pop(player_id)
        self.factions[member.faction].total_members -= 1

        self._save_state()
        logger.info(f"Player {player_id} left {member.faction.value}")

        return True

    def contribute_xp(self, player_id: str, xp: int) -> FactionRank | None:
        """Contribute XP to faction and check for rank up."""
        if player_id not in self.members:
            return None

        member = self.members[player_id]
        member.contribution_xp += xp
        member.last_active = datetime.now()

        self.factions[member.faction].total_xp += xp

        # Check for rank up
        old_rank = member.rank
        for rank in reversed(list(FactionRank)):
            if member.contribution_xp >= rank.xp_required:
                member.rank = rank
                break

        self._save_state()

        if member.rank != old_rank:
            logger.info(f"Player {player_id} ranked up to {member.rank.title}")
            return member.rank

        return None

    def get_member(self, player_id: str) -> FactionMember | None:
        """Get member info."""
        return self.members.get(player_id)

    def get_faction_info(self, faction: FactionType) -> dict:
        """Get faction information."""
        state = self.factions[faction]
        members = [m for m in self.members.values() if m.faction == faction]
        territories = [t for t in self.territories.values() if t.owner == faction]

        return {
            "faction": faction.value,
            "members": state.total_members,
            "total_xp": state.total_xp,
            "resources": state.resources,
            "territories": [t.name for t in territories],
            "relations": state.relations,
            "top_members": sorted(
                [
                    {"id": m.player_id, "rank": m.rank.title, "xp": m.contribution_xp}
                    for m in members
                ],
                key=lambda x: x["xp"],
                reverse=True,
            )[:5],
        }

    def get_faction_leaderboard(self) -> list[dict]:
        """Get faction leaderboard."""
        return sorted(
            [
                {
                    "faction": f.faction.value,
                    "members": f.total_members,
                    "xp": f.total_xp,
                    "territories": sum(
                        1 for t in self.territories.values() if t.owner == f.faction
                    ),
                    "missions": f.missions_completed,
                }
                for f in self.factions.values()
            ],
            key=lambda x: x["xp"],
            reverse=True,
        )

    def create_mission(
        self, faction: FactionType, mission_type: str, target_territory: str | None = None
    ) -> FactionMission | None:
        """Create a collaborative mission."""
        # Find template
        template = next((t for t in self.MISSION_TEMPLATES if t[0] == mission_type), None)
        if not template:
            return None

        _, name, desc, participants, xp = template

        mission_id = f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{mission_type}"
        mission = FactionMission(
            mission_id=mission_id,
            name=name,
            description=desc,
            faction=faction,
            required_participants=participants,
            target_territory=target_territory,
            xp_reward=xp,
        )

        self.active_missions[mission_id] = mission
        self._save_state()

        return mission

    def join_mission(self, player_id: str, mission_id: str) -> bool:
        """Join a mission."""
        if player_id not in self.members:
            return False

        member = self.members[player_id]
        mission = self.active_missions.get(mission_id)

        if not mission or mission.faction != member.faction:
            return False

        if player_id in mission.current_participants:
            return False

        if len(mission.current_participants) >= mission.required_participants:
            return False

        mission.current_participants.append(player_id)

        # Start mission if full
        if len(mission.current_participants) >= mission.required_participants:
            mission.status = "in_progress"

        self._save_state()
        return True

    def complete_mission(self, mission_id: str, success: bool = True) -> dict:
        """Complete a mission."""
        mission = self.active_missions.get(mission_id)
        if not mission:
            return {"error": "Mission not found"}

        result = {
            "mission": mission.name,
            "success": success,
            "participants": mission.current_participants,
            "xp_per_member": 0,
            "faction_resources": 0,
        }

        if success:
            mission.status = "completed"
            xp_each = mission.xp_reward // len(mission.current_participants)
            result["xp_per_member"] = xp_each
            result["faction_resources"] = mission.resource_reward

            # Award XP to participants
            for pid in mission.current_participants:
                self.contribute_xp(pid, xp_each)
                if pid in self.members:
                    self.members[pid].missions_completed += 1

            # Award resources to faction
            self.factions[mission.faction].resources += mission.resource_reward
            self.factions[mission.faction].missions_completed += 1

            # Handle territory capture
            if mission.target_territory and mission.target_territory in self.territories:
                territory = self.territories[mission.target_territory]
                territory.owner = mission.faction
                territory.control_points = 1000
                result["territory_captured"] = territory.name
        else:
            mission.status = "failed"

        # Remove from active
        del self.active_missions[mission_id]
        self._save_state()

        return result

    def update_relation(
        self, faction1: FactionType, faction2: FactionType, relation: RelationType
    ) -> None:
        """Update relation between factions."""
        self.factions[faction1].relations[faction2.value] = relation.value
        self.factions[faction2].relations[faction1.value] = relation.value
        self._save_state()

    def get_available_missions(self, faction: FactionType) -> list[dict]:
        """Get available missions for a faction."""
        return [
            {
                "id": m.mission_id,
                "name": m.name,
                "description": m.description,
                "participants": f"{len(m.current_participants)}/{m.required_participants}",
                "reward": f"{m.xp_reward} XP",
                "status": m.status,
            }
            for m in self.active_missions.values()
            if m.faction == faction and m.status in ("open", "in_progress")
        ]

    def get_territory_map(self) -> list[dict]:
        """Get territory ownership map."""
        return [
            {
                "id": t.territory_id,
                "name": t.name,
                "owner": t.owner.value if t.owner else "Unclaimed",
                "value": t.strategic_value,
                "contested": t.contested,
            }
            for t in sorted(
                self.territories.values(), key=lambda x: x.strategic_value, reverse=True
            )
        ]


# === Module-level convenience ===

_faction_manager: FactionManager | None = None


def get_faction_manager() -> FactionManager:
    """Get or create faction manager."""
    global _faction_manager
    if _faction_manager is None:
        _faction_manager = FactionManager()
    return _faction_manager


def join_faction(player_id: str, faction_name: str) -> dict:
    """Join a faction by name."""
    try:
        faction = FactionType(faction_name)
    except ValueError:
        return {"error": f"Unknown faction: {faction_name}"}

    fm = get_faction_manager()
    member = fm.join_faction(player_id, faction)
    return {"success": True, "faction": faction.value, "rank": member.rank.title}


def get_leaderboard() -> list[dict]:
    """Get faction leaderboard."""
    return get_faction_manager().get_faction_leaderboard()


if __name__ == "__main__":
    print("Faction System Demo")
    print("=" * 40)

    fm = FactionManager()

    # Show factions
    print("\n--- Available Factions ---")
    for ft in FactionType:
        print(f"  • {ft.value}")

    # Join faction
    member = fm.join_faction("player1", FactionType.CYBER_COLLECTIVE)
    print(f"\nJoined: {member.faction.value} as {member.rank.title}")

    # Contribute XP
    fm.contribute_xp("player1", 150)
    member = fm.get_member("player1")
    if member:
        print(f"After 150 XP: {member.rank.title} ({member.contribution_xp} XP)")

    # Create mission
    mission = fm.create_mission(FactionType.CYBER_COLLECTIVE, "raid", "core_nexus")
    if mission:
        print(f"\nMission created: {mission.name}")

    # Territory map
    print("\n--- Territories ---")
    for t in fm.get_territory_map()[:4]:
        print(f"  [{t['value']}★] {t['name']} - {t['owner']}")

    # Leaderboard
    print("\n--- Faction Leaderboard ---")
    for i, entry in enumerate(fm.get_faction_leaderboard()[:3], 1):
        print(f"  {i}. {entry['faction']}: {entry['xp']} XP, {entry['members']} members")

    print("\n✅ Faction system ready!")
