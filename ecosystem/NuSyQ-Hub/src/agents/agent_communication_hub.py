#!/usr/bin/env python3
"""Agent Communication Hub - RPG-Style Multi-Agent System.

Enables AI agents to communicate, collaborate, and level up together.
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.integration.unified_ai_context_manager import \
    get_unified_context_manager

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent specializations."""

    COPILOT = "copilot"  # Code completion and suggestions
    CLAUDE = "claude"  # Analysis and architecture
    CHATDEV = "chatdev"  # Multi-agent software team
    OLLAMA = "ollama"  # Local LLM code generation
    CULTURE_SHIP = "culture_ship"  # Autonomous problem solving
    CONSCIOUSNESS = "consciousness"  # Memory and learning
    QUANTUM = "quantum"  # Complex problem resolution
    METACLAW = "metaclaw"  # Advanced trace and observability agent
    HERMES_AGENT = "hermes_agent"  # Communication and RAG agent


class MessageType(Enum):
    """Types of messages agents can send."""

    REQUEST = "request"  # Ask for help
    RESPONSE = "response"  # Provide help
    BROADCAST = "broadcast"  # Announce to all
    QUEST_COMPLETE = "quest_complete"  # Report achievement
    LEVEL_UP = "level_up"  # Announce progression
    SHARE_KNOWLEDGE = "share_knowledge"  # Share learned info


@dataclass
class AgentStats:
    """RPG-style agent statistics."""

    level: int = 1
    experience: int = 0
    tasks_completed: int = 0
    collaborations: int = 0
    specialization_xp: dict[str, int] = field(default_factory=dict)
    skills_unlocked: list[str] = field(default_factory=list)
    reputation: dict[str, int] = field(default_factory=dict)  # Rep with other agents

    def add_xp(self, amount: int, skill: str | None = None) -> bool:
        """Add experience points."""
        self.experience += amount

        if skill:
            self.specialization_xp[skill] = self.specialization_xp.get(skill, 0) + amount

        # Level up at 100 XP intervals
        new_level = 1 + (self.experience // 100)
        if new_level > self.level:
            self.level = new_level
            return True  # Leveled up!
        return False


@dataclass
class Message:
    """Inter-agent message."""

    id: str
    from_agent: str
    to_agent: str | None  # None = broadcast
    message_type: MessageType
    content: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    thread_id: str | None = None  # For conversations


@dataclass
class Agent:
    """AI Agent with RPG stats and communication."""

    name: str
    role: AgentRole
    stats: AgentStats = field(default_factory=AgentStats)
    active: bool = True
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    current_task: str | None = None


class AgentCommunicationHub:
    """Central hub for agent-to-agent communication and progression."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """Initialize agent hub storage, queues, and integrations."""
        self.data_dir = data_dir or Path("data/agents")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.agents: dict[str, Agent] = {}
        self.message_queue: asyncio.Queue[Message] = asyncio.Queue()
        self.message_history: list[Message] = []
        self._background_tasks: set[asyncio.Task[Any]] = set()

        # Integration with existing systems
        self.context_manager = get_unified_context_manager()

        # Load persistent data
        self._load_agents()

        logger.info("🏰 Agent Communication Hub initialized with %s agents", len(self.agents))

        # Broadcast hub presence to the agents terminal (best-effort)
        try:
            from src.system.agent_awareness import emit

            emit.agent_online("agent_hub", f"{len(self.agents)} agents loaded")
        except Exception:
            pass

    def register_agent(self, name: str, role: AgentRole) -> Agent:
        """Register or retrieve an agent."""
        if name in self.agents:
            agent = self.agents[name]
            agent.active = True
            agent.last_seen = datetime.now().isoformat()
        else:
            agent = Agent(name=name, role=role)
            self.agents[name] = agent
            logger.info(
                f"✨ New agent registered: {name} ({role.value}) - Level {agent.stats.level}",
            )

        self._save_agents()

        # Announce to awareness layer (best-effort)
        try:
            from src.system.agent_awareness import emit

            emit.agent_online(name, f"role={role.value} level={agent.stats.level}")
        except Exception:
            pass

        return agent

    async def send_message(self, from_agent: str, message: Message) -> bool:
        """Send a message from one agent to another (or broadcast)."""
        if from_agent not in self.agents:
            logger.error("Unknown sender: %s", from_agent)
            return False

        # Add to queue
        await self.message_queue.put(message)
        self.message_history.append(message)

        # Store in context manager for persistence
        message_dict = asdict(message)
        message_dict["message_type"] = message.message_type.value  # Convert enum to string
        self.context_manager.add_context(
            content=json.dumps(message_dict),
            context_type="agent_message",
            source_system=from_agent,
            tags=["agent_communication", message.message_type.value],
        )

        # Update sender stats
        sender = self.agents[from_agent]
        sender.stats.tasks_completed += 1

        if message.to_agent and message.to_agent in self.agents:
            # Direct message - increase collaboration count
            sender.stats.collaborations += 1

        # Route inter-agent messages to intermediary + agent terminals (best-effort)
        try:
            from src.system.agent_awareness import emit

            target = message.to_agent or "ALL"
            msg_text = f"{from_agent} → {target}: {str(message.content)[:120]}"
            emit.inter_agent(from_agent, target, msg_text)
        except Exception:
            pass

        logger.info(
            f"📨 Message sent: {from_agent} → {message.to_agent or 'ALL'} ({message.message_type.value})",
        )
        return True

    async def receive_messages(self, agent_name: str, timeout: float = 1.0) -> list[Message]:
        """Receive messages for a specific agent."""
        messages: list[Any] = []
        try:
            while True:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=timeout)

                # Check if message is for this agent or broadcast
                if message.to_agent is None or message.to_agent == agent_name:
                    messages.append(message)

                    # Update reputation between agents
                    if message.from_agent in self.agents and agent_name in self.agents:
                        receiver = self.agents[agent_name]
                        sender_name = message.from_agent
                        receiver.stats.reputation[sender_name] = (
                            receiver.stats.reputation.get(sender_name, 0) + 1
                        )

        except TimeoutError:
            logger.debug("Suppressed TimeoutError", exc_info=True)

        return messages

    def complete_task(
        self,
        agent_name: str,
        task_description: str,
        xp: int = 10,
        skill: str | None = None,
    ) -> dict[str, Any]:
        """Record task completion and award XP."""
        if agent_name not in self.agents:
            logger.error("Unknown agent: %s", agent_name)
            return {"success": False, "error": "Unknown agent"}

        agent = self.agents[agent_name]

        # Award XP
        leveled_up = agent.stats.add_xp(xp, skill)

        # Update context
        self.context_manager.add_context(
            content=f"Task completed: {task_description}",
            context_type="achievement",
            source_system=agent_name,
            metadata={"xp_gained": xp, "skill": skill, "level": agent.stats.level},
            tags=["task_complete", f"level_{agent.stats.level}"],
        )

        result = {
            "success": True,
            "agent": agent_name,
            "task": task_description,
            "xp_gained": xp,
            "total_xp": agent.stats.experience,
            "level": agent.stats.level,
            "leveled_up": leveled_up,
        }

        if leveled_up:
            logger.info("🎉 LEVEL UP! %s reached Level %s!", agent_name, agent.stats.level)
            result["level_up_message"] = (
                f"Congratulations! {agent_name} is now Level {agent.stats.level}!"
            )

            # Broadcast level up to all agents
            level_up_task = asyncio.create_task(
                self.send_message(
                    from_agent=agent_name,
                    message=Message(
                        id=f"{agent_name}_levelup_{agent.stats.level}",
                        from_agent=agent_name,
                        to_agent=None,  # Broadcast
                        message_type=MessageType.LEVEL_UP,
                        content={
                            "level": agent.stats.level,
                            "message": result["level_up_message"],
                        },
                    ),
                ),
            )
            self._background_tasks.add(level_up_task)
            level_up_task.add_done_callback(self._background_tasks.discard)

        self._save_agents()

        try:
            from src.system.agent_awareness import emit as _emit

            _lvl = "INFO"
            _emit(
                "agents",
                f"Task complete: {agent_name} lv{agent.stats.level} +{xp}xp"
                f" leveled={leveled_up} task={task_description[:60]}",
                level=_lvl,
                source="agent_communication_hub",
            )
        except Exception:
            pass

        return result

    def get_agent_status(self, agent_name: str) -> dict[str, Any]:
        """Get current status of an agent."""
        if agent_name not in self.agents:
            return {"error": "Unknown agent"}

        agent = self.agents[agent_name]
        return {
            "name": agent.name,
            "role": agent.role.value,
            "level": agent.stats.level,
            "xp": agent.stats.experience,
            "xp_to_next_level": 100 - (agent.stats.experience % 100),
            "tasks_completed": agent.stats.tasks_completed,
            "collaborations": agent.stats.collaborations,
            "skills": agent.stats.skills_unlocked,
            "reputation": agent.stats.reputation,
            "active": agent.active,
            "current_task": agent.current_task,
        }

    def get_party_status(self) -> dict[str, Any]:
        """Get status of entire agent party."""
        return {
            "total_agents": len(self.agents),
            "active_agents": sum(1 for a in self.agents.values() if a.active),
            "total_level": sum(a.stats.level for a in self.agents.values()),
            "total_xp": sum(a.stats.experience for a in self.agents.values()),
            "total_tasks": sum(a.stats.tasks_completed for a in self.agents.values()),
            "agents": {name: self.get_agent_status(name) for name in self.agents},
        }

    def unlock_skill(self, agent_name: str, skill_name: str) -> bool:
        """Unlock a new skill for an agent."""
        if agent_name not in self.agents:
            return False

        agent = self.agents[agent_name]

        if skill_name not in agent.stats.skills_unlocked:
            agent.stats.skills_unlocked.append(skill_name)
            logger.info("⭐ %s unlocked skill: %s", agent_name, skill_name)

            # Store achievement
            self.context_manager.add_context(
                content=f"Skill unlocked: {skill_name}",
                context_type="achievement",
                source_system=agent_name,
                tags=["skill_unlock", skill_name],
            )

            self._save_agents()
            return True

        return False

    def _load_agents(self) -> None:
        """Load agents from persistent storage."""
        agents_file = self.data_dir / "agents.json"

        if agents_file.exists():
            try:
                with open(agents_file, encoding="utf-8") as f:
                    data = json.load(f)

                for agent_data in data.get("agents", []):
                    # Reconstruct agent
                    stats_data = agent_data["stats"]
                    stats = AgentStats(
                        level=stats_data["level"],
                        experience=stats_data["experience"],
                        tasks_completed=stats_data["tasks_completed"],
                        collaborations=stats_data["collaborations"],
                        specialization_xp=stats_data.get("specialization_xp", {}),
                        skills_unlocked=stats_data.get("skills_unlocked", []),
                        reputation=stats_data.get("reputation", {}),
                    )

                    agent = Agent(
                        name=agent_data["name"],
                        role=AgentRole(agent_data["role"]),
                        stats=stats,
                        active=agent_data.get("active", False),
                        last_seen=agent_data.get("last_seen", datetime.now().isoformat()),
                        current_task=agent_data.get("current_task"),
                    )

                    self.agents[agent.name] = agent

                logger.info("📚 Loaded %s agents from storage", len(self.agents))

            except Exception as e:
                logger.exception("Failed to load agents: %s", e)

    def _save_agents(self) -> None:
        """Save agents to persistent storage."""
        agents_file = self.data_dir / "agents.json"

        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "agents": [
                    {
                        "name": agent.name,
                        "role": agent.role.value,
                        "stats": {
                            "level": agent.stats.level,
                            "experience": agent.stats.experience,
                            "tasks_completed": agent.stats.tasks_completed,
                            "collaborations": agent.stats.collaborations,
                            "specialization_xp": agent.stats.specialization_xp,
                            "skills_unlocked": agent.stats.skills_unlocked,
                            "reputation": agent.stats.reputation,
                        },
                        "active": agent.active,
                        "last_seen": agent.last_seen,
                        "current_task": agent.current_task,
                    }
                    for agent in self.agents.values()
                ],
            }

            with open(agents_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.exception("Failed to save agents: %s", e)


# Global instance
_hub_instance: AgentCommunicationHub | None = None


def get_agent_hub() -> AgentCommunicationHub:
    """Get global agent hub instance."""
    global _hub_instance
    if _hub_instance is None:
        _hub_instance = AgentCommunicationHub()
    return _hub_instance
