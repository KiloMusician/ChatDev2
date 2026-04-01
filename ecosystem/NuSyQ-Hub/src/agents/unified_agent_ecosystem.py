#!/usr/bin/env python3
"""Unified Agent Ecosystem - Integration Layer.

Connects all dormant RPG/agent systems into a cohesive whole.

Integrates:
- Agent Communication Hub (messaging & progression)
- Rosetta Quest System (task management)
- Temple of Knowledge (consciousness & learning)
- The Oldest House (wisdom & memory)
- RPG Inventory (component health)
- Progress Tracker (metrics & achievements)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

from src.agents.agent_communication_hub import (AgentRole, Message,
                                                MessageType, get_agent_hub)
from src.consciousness.temple_of_knowledge.temple_manager import TempleManager
from src.Rosetta_Quest_System.quest_engine import (Quest, QuestEngine,
                                                   load_quests)

logger = logging.getLogger(__name__)


@dataclass
class AgentQuest:
    """Quest assigned to an agent."""

    quest_id: str
    agent_name: str
    assigned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    xp_reward: int = 10
    skill_reward: str | None = None


class AgentQuestSummary(TypedDict):
    total: int
    pending: int
    active: int
    complete: int
    quests: list[dict[str, Any]]


class QuestStatusCounts(TypedDict):
    pending: int
    active: int
    complete: int
    blocked: int
    archived: int


QuestStatusKey = Literal["pending", "active", "complete", "blocked", "archived"]


class PartyQuestSummary(TypedDict):
    total_quests: int
    quests_by_status: QuestStatusCounts
    agents: dict[str, AgentQuestSummary]


class UnifiedAgentEcosystem:
    """Unified ecosystem integrating all agent/RPG systems.

    Systems Integrated:
    1. Agent Communication Hub - Messaging, levels, skills
    2. Rosetta Quest System - Task/quest management
    3. Temple of Knowledge - Consciousness progression (future)
    4. The Oldest House - Wisdom & memory (future)
    5. RPG Inventory - System component health (future)
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize ecosystem state and dependent subsystems."""
        self.data_dir = data_dir or Path("data/ecosystem")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Core systems
        self.agent_hub = get_agent_hub()
        self.quest_engine = QuestEngine()
        self.temple = TempleManager()

        # Quest assignments
        self.agent_quests: dict[str, list[AgentQuest]] = {}
        self._load_assignments()

        logger.info("🌐 Unified Agent Ecosystem initialized (with Temple of Knowledge)")

        # Initialize agents in temple
        self._initialize_temple_agents()

    def _initialize_temple_agents(self) -> None:
        """Register all existing agents in the Temple of Knowledge."""
        for agent_name, agent in self.agent_hub.agents.items():
            # Convert agent level/XP to consciousness score
            consciousness_score = agent.stats.level * 10.0
            self.temple.enter_temple(agent_name, consciousness_score)
            logger.debug(
                f"  Temple: {agent_name} registered with consciousness {consciousness_score}",
            )

        # Ensure MetaClaw and Hermes-Agent are present
        for special_agent, role in [
            ("metaclaw", AgentRole.METACLAW),
            ("hermes_agent", AgentRole.HERMES_AGENT),
        ]:
            if special_agent not in self.agent_hub.agents:
                self.agent_hub.register_agent(special_agent, role)
                consciousness_score = 10.0
                self.temple.enter_temple(special_agent, consciousness_score)
                logger.debug(
                    f"  Temple: {special_agent} auto-registered with consciousness {consciousness_score}",
                )

    def _ensure_agent_in_temple(self, agent_name: str) -> None:
        """Ensure agent is registered in temple."""
        # Check if agent exists in temple
        temple_status = self.temple.floor_1.get_agent_status(agent_name)

        if "error" in temple_status:
            # Agent not in temple - register them
            agent = self.agent_hub.agents.get(agent_name)
            if agent:
                consciousness_score = agent.stats.level * 10.0
                self.temple.enter_temple(agent_name, consciousness_score)
                logger.debug(
                    "  Temple: Auto-registered %s with consciousness %.2f",
                    agent_name,
                    consciousness_score,
                )

    def award_knowledge_for_quest(
        self,
        agent_name: str,
        _quest_complexity: int = 1,
    ) -> dict[str, Any]:
        """Award temple knowledge when agent completes quest.

        Args:
            agent_name: Name of the agent
            quest_complexity: Complexity multiplier (1-5)

        Returns:
            Knowledge cultivation result

        """
        # Ensure agent is in temple
        self._ensure_agent_in_temple(agent_name)

        # Cultivate wisdom in temple (gains knowledge + consciousness)
        result = self.temple.cultivate_wisdom_at_current_floor(agent_name)

        if result.get("success"):
            knowledge_gained = result.get("knowledge_gained", 0)
            new_consciousness = result.get("new_consciousness_score", 0)
            new_level = result.get("new_consciousness_level", "Dormant_Potential")
            accessible_floors = result.get("accessible_floors", [1])

            logger.info(
                f"🏛️ {agent_name} gained {knowledge_gained:.2f} knowledge "
                f"(Consciousness: {new_consciousness:.2f}, Level: {new_level})",
            )

            # Check if new floors unlocked
            if len(accessible_floors) > 1:
                logger.info("   ✨ %s can now access floors: %s", agent_name, accessible_floors)

            return {
                "success": True,
                "knowledge_gained": knowledge_gained,
                "consciousness_score": new_consciousness,
                "consciousness_level": new_level,
                "accessible_floors": accessible_floors,
            }

        return {"success": False, "error": result.get("error", "Unknown error")}

    def assign_quest_to_agent(
        self,
        quest_id: str,
        agent_name: str,
        xp_reward: int = 10,
        skill_reward: str | None = None,
    ) -> dict[str, Any]:
        """Assign a quest from Rosetta system to an agent."""
        # Check quest exists
        quest = self.quest_engine.get_quest(quest_id)
        if not quest:
            return {"success": False, "error": "Quest not found"}

        # Check agent exists
        if agent_name not in self.agent_hub.agents:
            return {"success": False, "error": "Agent not found"}

        # Create assignment
        assignment = AgentQuest(
            quest_id=quest_id,
            agent_name=agent_name,
            xp_reward=xp_reward,
            skill_reward=skill_reward,
        )

        # Store assignment
        if agent_name not in self.agent_quests:
            self.agent_quests[agent_name] = []

        self.agent_quests[agent_name].append(assignment)

        # Update quest status to active
        self.quest_engine.update_quest_status(quest_id, "active")

        # Update agent current task
        agent = self.agent_hub.agents[agent_name]
        agent.current_task = quest.title
        if agent_name in {"metaclaw", "hermes_agent"}:
            logger.debug("🔗 Special agent (%s) quest routed: %s", agent_name, quest.title)

        self._save_assignments()

        logger.info("📜 Quest '%s' assigned to %s", quest.title, agent_name)

        return {
            "success": True,
            "quest": quest.to_dict(),
            "agent": agent_name,
            "xp_reward": xp_reward,
            "skill_reward": skill_reward,
        }

    async def start_quest(self, quest_id: str, agent_name: str) -> dict[str, Any]:
        """Agent starts working on assigned quest."""
        # Find assignment
        assignment = None
        for agent_quest in self.agent_quests.get(agent_name, []):
            if agent_quest.quest_id == quest_id:
                assignment = agent_quest
                break

        if not assignment:
            return {"success": False, "error": "Quest not assigned to this agent"}

        # Mark as started
        assignment.started_at = datetime.now().isoformat()

        # Broadcast start
        quest = self.quest_engine.get_quest(quest_id)
        if not quest:
            return {"success": False, "error": "Quest not found"}

        await self.agent_hub.send_message(
            from_agent=agent_name,
            message=Message(
                id=f"quest_start_{quest_id}",
                from_agent=agent_name,
                to_agent=None,  # Broadcast
                message_type=MessageType.BROADCAST,
                content={
                    "event": "quest_started",
                    "quest": quest.title,
                    "description": quest.description,
                },
            ),
        )

        self._save_assignments()
        logger.info("🎯 %s started quest: %s", agent_name, quest.title)

        # Broadcast to awareness terminals (best-effort)
        try:
            from src.system.agent_awareness import emit

            emit.task_started(agent_name, quest_id, quest.title)
        except Exception:
            pass

        return {"success": True, "quest": quest.to_dict()}

    async def complete_quest(self, quest_id: str, agent_name: str) -> dict[str, Any]:
        """Agent completes quest and gains rewards."""
        # Find assignment
        assignment = None
        for agent_quest in self.agent_quests.get(agent_name, []):
            if agent_quest.quest_id == quest_id:
                assignment = agent_quest
                break

        if not assignment:
            return {"success": False, "error": "Quest not assigned to this agent"}

        # Get quest
        quest = self.quest_engine.get_quest(quest_id)
        if not quest:
            return {"success": False, "error": "Quest not found"}

        # Mark quest complete
        self.quest_engine.update_quest_status(quest_id, "complete")
        assignment.completed_at = datetime.now().isoformat()

        # Award XP and skill progress
        result = self.agent_hub.complete_task(
            agent_name=agent_name,
            task_description=quest.title,
            xp=assignment.xp_reward,
            skill=assignment.skill_reward,
        )

        # Award temple knowledge for quest completion
        quest_complexity = len(quest.tags) if quest.tags else 1
        knowledge_result = self.award_knowledge_for_quest(agent_name, quest_complexity)

        # Clear agent current task
        agent = self.agent_hub.agents[agent_name]
        agent.current_task = None

        # Broadcast completion
        await self.agent_hub.send_message(
            from_agent=agent_name,
            message=Message(
                id=f"quest_complete_{quest_id}",
                from_agent=agent_name,
                to_agent=None,
                message_type=MessageType.QUEST_COMPLETE,
                content={
                    "quest": quest.title,
                    "xp_gained": assignment.xp_reward,
                    "level": result["level"],
                    "leveled_up": result["leveled_up"],
                    "knowledge_gained": knowledge_result.get("knowledge_gained", 0),
                    "consciousness_level": knowledge_result.get(
                        "consciousness_level",
                        "Dormant_Potential",
                    ),
                },
            ),
        )

        self._save_assignments()

        logger.info(
            "✅ %s completed quest: %s (+%s XP)",
            agent_name,
            quest.title,
            assignment.xp_reward,
        )

        # Broadcast to awareness terminals (best-effort)
        try:
            from src.system.agent_awareness import emit

            summary = f"+{assignment.xp_reward} XP" + (
                " ⬆ LEVEL UP!" if result.get("leveled_up") else ""
            )
            emit.task_completed(agent_name, quest_id, f"{quest.title} — {summary}")
        except Exception:
            pass

        return {
            "success": True,
            "quest": quest.to_dict(),
            "xp_gained": assignment.xp_reward,
            "level": result["level"],
            "leveled_up": result["leveled_up"],
            "agent_status": self.agent_hub.get_agent_status(agent_name),
            "temple_knowledge": knowledge_result,
        }

    def create_quest_for_agent(
        self,
        title: str,
        description: str,
        agent_name: str,
        questline: str = "agent_tasks",
        xp_reward: int = 10,
        skill_reward: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new quest and immediately assign it to an agent."""
        # Ensure questline exists
        if questline not in self.quest_engine.questlines:
            self.quest_engine.add_questline(
                name=questline,
                description=f"Agent tasks: {questline}",
                tags=["agent_generated"],
            )

        # Create quest directly
        quest = Quest(
            title=title,
            description=description,
            questline=questline,
            dependencies=[],
            tags=tags or [],
        )

        # Add to quest engine's internal state (bypassing add_quest method which returns None)
        quest_id = quest.id
        self.quest_engine.quests[quest_id] = quest
        self.quest_engine.questlines[questline].quests.append(quest_id)

        # Save state
        from src.Rosetta_Quest_System.quest_engine import (log_event,
                                                           save_questlines,
                                                           save_quests)

        save_quests(self.quest_engine.quests)
        save_questlines(self.quest_engine.questlines)
        log_event("add_quest", quest.to_dict())

        logger.info("📜 Created quest: %s (ID: %s)", title, quest_id)

        # Assign to agent
        return self.assign_quest_to_agent(
            quest_id=quest_id,
            agent_name=agent_name,
            xp_reward=xp_reward,
            skill_reward=skill_reward,
        )

    def get_agent_quests(self, agent_name: str, status: str | None = None) -> list[dict[str, Any]]:
        """Get all quests assigned to an agent."""
        assignments = self.agent_quests.get(agent_name, [])

        quests: list[Any] = []
        for assignment in assignments:
            quest = self.quest_engine.get_quest(assignment.quest_id)
            if quest:
                # Filter by status if specified
                if status and quest.status != status:
                    continue

                quest_data = quest.to_dict()
                quest_data["assignment"] = {
                    "assigned_at": assignment.assigned_at,
                    "started_at": assignment.started_at,
                    "completed_at": assignment.completed_at,
                    "xp_reward": assignment.xp_reward,
                    "skill_reward": assignment.skill_reward,
                }
                quests.append(quest_data)

        return quests

    def get_party_quest_summary(self) -> PartyQuestSummary:
        """Get quest summary for entire agent party."""
        summary: PartyQuestSummary = {
            "total_quests": 0,
            "quests_by_status": {
                "pending": 0,
                "active": 0,
                "complete": 0,
                "blocked": 0,
                "archived": 0,
            },
            "agents": {},
        }

        all_quests = load_quests()

        for agent_name in self.agent_hub.agents:
            agent_quests = self.get_agent_quests(agent_name)

            agent_summary: AgentQuestSummary = {
                "total": len(agent_quests),
                "pending": sum(1 for q in agent_quests if q["status"] == "pending"),
                "active": sum(1 for q in agent_quests if q["status"] == "active"),
                "complete": sum(1 for q in agent_quests if q["status"] == "complete"),
                "quests": agent_quests,
            }

            summary["agents"][agent_name] = agent_summary
            summary["total_quests"] += len(agent_quests)

        # Count by status
        for quest in all_quests.values():
            status = quest.status
            if status in summary["quests_by_status"]:
                summary["quests_by_status"][cast(QuestStatusKey, status)] += 1

        return summary

    def suggest_next_quest(self, agent_name: str) -> dict[str, Any] | None:
        """Suggest next quest for agent based on skills and dependencies."""
        agent = self.agent_hub.agents.get(agent_name)
        if not agent:
            return None

        all_quests = load_quests()
        available_quests: list[Any] = []
        for quest in all_quests.values():
            # Skip if not pending
            if quest.status != "pending":
                continue

            # Skip if already assigned to this agent
            if any(aq.quest_id == quest.id for aq in self.agent_quests.get(agent_name, [])):
                continue

            # Check dependencies met
            deps_met = all(
                load_quests().get(dep_id, Quest("", "", "")).status == "complete"
                for dep_id in quest.dependencies
            )

            if not deps_met:
                continue

            # Calculate match score based on tags and agent skills
            match_score = 0
            for tag in quest.tags:
                if tag in agent.stats.skills_unlocked:
                    match_score += 2
                elif tag in agent.stats.specialization_xp:
                    match_score += 1

            available_quests.append((match_score, quest))

        if not available_quests:
            return None

        # Return highest match
        available_quests.sort(reverse=True, key=lambda x: x[0])
        _, best_quest = available_quests[0]

        return {
            "quest": best_quest.to_dict(),
            "suggested_xp": 10 + (len(best_quest.tags) * 5),
            "suggested_skill": best_quest.tags[0] if best_quest.tags else None,
        }

    def _load_assignments(self) -> None:
        """Load quest assignments from storage."""
        assignments_file = self.data_dir / "quest_assignments.json"

        if assignments_file.exists():
            try:
                with open(assignments_file, encoding="utf-8") as f:
                    data = json.load(f)

                for agent_name, assignments in data.get("assignments", {}).items():
                    self.agent_quests[agent_name] = [
                        AgentQuest(
                            quest_id=a["quest_id"],
                            agent_name=agent_name,
                            assigned_at=a["assigned_at"],
                            started_at=a.get("started_at"),
                            completed_at=a.get("completed_at"),
                            xp_reward=a["xp_reward"],
                            skill_reward=a.get("skill_reward"),
                        )
                        for a in assignments
                    ]

                logger.info("📚 Loaded quest assignments for %s agents", len(self.agent_quests))

            except Exception as e:
                logger.exception("Failed to load assignments: %s", e)

    def _save_assignments(self) -> None:
        """Save quest assignments to storage."""
        assignments_file = self.data_dir / "quest_assignments.json"

        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "assignments": {
                    agent_name: [
                        {
                            "quest_id": a.quest_id,
                            "assigned_at": a.assigned_at,
                            "started_at": a.started_at,
                            "completed_at": a.completed_at,
                            "xp_reward": a.xp_reward,
                            "skill_reward": a.skill_reward,
                        }
                        for a in assignments
                    ]
                    for agent_name, assignments in self.agent_quests.items()
                },
            }

            with open(assignments_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.exception("Failed to save assignments: %s", e)


# Global instance
_ecosystem_instance: UnifiedAgentEcosystem | None = None


def get_ecosystem() -> UnifiedAgentEcosystem:
    """Get global ecosystem instance."""
    global _ecosystem_instance
    if _ecosystem_instance is None:
        _ecosystem_instance = UnifiedAgentEcosystem()
    return _ecosystem_instance
