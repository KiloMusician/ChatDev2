"""Agent Guild Protocols - Simple handshake patterns for agents to use the board.

Agents interact with the guild board via simple async methods:
- heartbeat(status, current_quest, blockers) - Show I'm alive + what I'm doing
- claim(quest_id) - Atomically claim a quest
- start(quest_id) - Mark quest as active
- post(message, type, artifacts) - Progress note or alert
- complete(quest_id, artifacts) - Mark quest done
- yield(quest_id, reason) - Give up (unblock others)
- swarm(quest_id, tags) - Invite other agents to help

This is the **handshake protocol** for guild coordination.
"""

import logging

from src.guild.guild_board import AgentStatus, QuestState, get_board

logger = logging.getLogger(__name__)


class AgentGuildProtocols:
    """Protocol methods for agent-board interaction."""

    @staticmethod
    async def heartbeat(
        agent_id: str,
        status: AgentStatus,
        current_quest: str | None = None,
        capabilities: list[str] | None = None,
        blockers: list[str] | None = None,
    ) -> dict[str, str]:
        """Heartbeat: Show presence + current work.

        Agents should call this periodically (e.g., every 30 seconds).
        """
        board = await get_board()
        await board.agent_heartbeat(
            agent_id=agent_id,
            status=status,
            current_quest=current_quest,
            capabilities=capabilities,
            blockers=blockers,
        )
        return {"status": "ok", "message": f"Heartbeat sent by {agent_id}"}

    @staticmethod
    async def claim(agent_id: str, quest_id: str) -> tuple[bool, str]:
        """Claim: Atomically reserve a quest so no other agent takes it.

        Returns: (success, message)
        """
        board = await get_board()
        success, message = await board.claim_quest(quest_id, agent_id)
        return success, message or "Unknown error"

    @staticmethod
    async def start(agent_id: str, quest_id: str) -> tuple[bool, str]:
        """Start: Mark claimed quest as now actively being worked on."""
        board = await get_board()
        success, message = await board.start_quest(quest_id, agent_id)
        return success, message or "Unknown error"

    @staticmethod
    async def post(
        agent_id: str,
        message: str,
        post_type: str = "progress",
        quest_id: str | None = None,
        artifacts: list[str] | None = None,
    ) -> str:
        """Post: Share a progress note, discovery, blockage, or help request.

        post_type: "progress" | "blockage" | "discovery" | "help_wanted"
        """
        board = await get_board()
        post = await board.post_on_board(
            agent_id=agent_id,
            message=message,
            quest_id=quest_id,
            post_type=post_type,
            artifacts=artifacts,
        )
        return f"Posted: {post.post_id}"

    @staticmethod
    async def complete(
        agent_id: str,
        quest_id: str,
        artifacts: list[str] | None = None,
    ) -> tuple[bool, str]:
        """Complete: Mark quest done, provide artifacts/receipts."""
        board = await get_board()
        success, message = await board.complete_quest(quest_id, agent_id, artifacts)
        return success, message or "Unknown error"

    @staticmethod
    async def add_quest(
        agent_id: str,
        title: str,
        description: str,
        quest_id: str | None = None,
        priority: int = 3,
        safety_tier: str = "safe",
        tags: list[str] | None = None,
        dependencies: list[str] | None = None,
        acceptance_criteria: list[str] | None = None,
    ) -> tuple[bool, str]:
        """Add a quest to the board."""
        board = await get_board()
        success, message = await board.add_quest(
            quest_id=quest_id,
            title=title,
            description=description,
            priority=priority,
            safety_tier=safety_tier,
            tags=tags,
            dependencies=dependencies,
            acceptance_criteria=acceptance_criteria,
        )
        if success:
            await board.post_on_board(
                agent_id=agent_id,
                message=f"Added quest: {message}",
                quest_id=message,
                post_type="discovery",
            )
        return success, message

    @staticmethod
    async def close_quest(
        agent_id: str,
        quest_id: str,
        status: str = "done",
        artifacts: list[str] | None = None,
        reason: str | None = None,
    ) -> tuple[bool, str]:
        """Close a quest with a final status."""
        board = await get_board()
        status_lower = status.lower()
        if status_lower in ("done", "completed", "complete"):
            quest_status = QuestState.DONE
        elif status_lower in ("abandoned", "cancelled", "canceled"):
            quest_status = QuestState.ABANDONED
        elif status_lower in ("blocked",):
            quest_status = QuestState.BLOCKED
        else:
            quest_status = QuestState.DONE

        success, message = await board.close_quest(
            quest_id=quest_id,
            agent_id=agent_id,
            status=quest_status,
            artifacts=artifacts,
            reason=reason,
        )
        return success, message or "Unknown error"

    @staticmethod
    async def yield_quest(
        agent_id: str,
        quest_id: str,
        reason: str = "",
    ) -> tuple[bool, str]:
        """Yield: Abandon a quest so others can claim it.

        Post blockage message first, then yield.
        """
        board = await get_board()

        # Post blockage notice
        if reason:
            await board.post_on_board(
                agent_id=agent_id,
                message=f"Yielding quest: {reason}",
                quest_id=quest_id,
                post_type="blockage",
            )

        # Reset quest state to open so others can claim
        if quest_id in board.board.quests:
            quest = board.board.quests[quest_id]
            quest.claimed_by = None
            quest.state = QuestState.OPEN
            quest.claimed_at = None
            quest.started_at = None
            if quest_id in board.board.active_work:
                del board.board.active_work[quest_id]
            await board._save_board()

        return True, f"Quest {quest_id} yielded"

    @staticmethod
    async def swarm(
        agent_id: str,
        quest_id: str,
        required_capabilities: list[str],
    ) -> str:
        """Swarm: Post help request and invite agents with specific skills.

        This becomes a "work item" that other agents can see.
        """
        board = await get_board()
        message = f"Swarming quest {quest_id} - need help with: {', '.join(required_capabilities)}"
        post = await board.post_on_board(
            agent_id=agent_id,
            message=message,
            quest_id=quest_id,
            post_type="help_wanted",
        )
        return f"Swarm request: {post.post_id}"

    @staticmethod
    async def get_available_quests(agent_id: str, capabilities: list[str]) -> list[dict]:
        """Get quests that match agent's capabilities."""
        board = await get_board()
        quests = await board.get_available_quests(capabilities)
        return [
            {
                "quest_id": q.quest_id,
                "title": q.title,
                "priority": q.priority,
                "safety_tier": q.safety_tier,
                "tags": q.tags,
            }
            for q in quests
        ]


# Convenience shortcuts for agents
async def agent_heartbeat(
    agent_id: str,
    status: str = "idle",
    current_quest: str | None = None,
    capabilities: list[str] | None = None,
    blockers: list[str] | None = None,
) -> dict:
    """Simple heartbeat call for agents."""
    normalized = (status or "idle").strip().lower()
    aliases = {
        "active": "WORKING",
        "busy": "WORKING",
        "work": "WORKING",
        "working": "WORKING",
        "observe": "OBSERVING",
        "observing": "OBSERVING",
        "offline": "OFFLINE",
        "blocked": "BLOCKED",
        "idle": "IDLE",
    }
    status_key = aliases.get(normalized, normalized).upper()
    try:
        status_enum = AgentStatus[status_key]
    except KeyError:
        status_enum = AgentStatus.IDLE

    return await AgentGuildProtocols.heartbeat(
        agent_id=agent_id,
        status=status_enum,
        current_quest=current_quest,
        capabilities=capabilities,
        blockers=blockers,
    )


async def agent_claim(agent_id: str, quest_id: str) -> dict:
    """Claim a quest."""
    success, message = await AgentGuildProtocols.claim(agent_id, quest_id)
    return {"success": success, "message": message}


async def agent_start(agent_id: str, quest_id: str) -> dict:
    """Start working on claimed quest."""
    success, message = await AgentGuildProtocols.start(agent_id, quest_id)
    return {"success": success, "message": message}


async def agent_post(
    agent_id: str,
    message: str,
    post_type: str = "progress",
    quest_id: str | None = None,
    artifacts: list[str] | None = None,
) -> dict:
    """Post on board."""
    post_id = await AgentGuildProtocols.post(
        agent_id=agent_id,
        message=message,
        post_type=post_type,
        quest_id=quest_id,
        artifacts=artifacts,
    )
    return {"post_id": post_id}


async def agent_complete(
    agent_id: str,
    quest_id: str,
    artifacts: list[str] | None = None,
) -> dict:
    """Complete a quest."""
    success, message = await AgentGuildProtocols.complete(agent_id, quest_id, artifacts)
    return {"success": success, "message": message}


async def agent_yield(
    agent_id: str,
    quest_id: str,
    reason: str = "",
) -> dict:
    """Yield a quest."""
    success, message = await AgentGuildProtocols.yield_quest(agent_id, quest_id, reason)
    return {"success": success, "message": message}


async def agent_available_quests(agent_id: str, capabilities: list[str]) -> dict:
    """Get available quests for agent."""
    quests = await AgentGuildProtocols.get_available_quests(agent_id, capabilities)
    return {"agent": agent_id, "available_quests": quests}


async def agent_add_quest(
    agent_id: str,
    title: str,
    description: str,
    quest_id: str | None = None,
    priority: int = 3,
    safety_tier: str = "safe",
    tags: list[str] | None = None,
    dependencies: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
) -> dict:
    """Add a quest to the board."""
    success, message = await AgentGuildProtocols.add_quest(
        agent_id=agent_id,
        title=title,
        description=description,
        quest_id=quest_id,
        priority=priority,
        safety_tier=safety_tier,
        tags=tags,
        dependencies=dependencies,
        acceptance_criteria=acceptance_criteria,
    )
    return {"success": success, "quest_id": message}


async def agent_close_quest(
    agent_id: str,
    quest_id: str,
    status: str = "done",
    artifacts: list[str] | None = None,
    reason: str | None = None,
) -> dict:
    """Close a quest with final status."""
    success, message = await AgentGuildProtocols.close_quest(
        agent_id=agent_id,
        quest_id=quest_id,
        status=status,
        artifacts=artifacts,
        reason=reason,
    )
    return {"success": success, "message": message}
