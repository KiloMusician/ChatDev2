"""Guild Board CLI - Commands to interact with the guild board from CLI.

Can be called via:
- python -m src.guild.guild_cli board_status
- python -m src.guild.guild_cli board_render
- python -m src.guild.guild_cli board_post --agent copilot --message "..."
- python -m src.guild.guild_cli board_claim --agent copilot --quest q-123
"""

import asyncio
import logging
import sys
from pathlib import Path

from src.guild.agent_guild_protocols import (agent_add_quest,
                                             agent_available_quests,
                                             agent_claim, agent_close_quest,
                                             agent_complete, agent_heartbeat,
                                             agent_post, agent_start)
from src.guild.guild_board import get_board, init_board
from src.guild.guild_board_renderer import render_and_save

logger = logging.getLogger(__name__)


async def board_status() -> dict:
    """Get and display board status."""
    board = await get_board()
    summary = await board.get_board_summary()
    return summary


async def board_render() -> Path:
    """Render board to Markdown and JSON."""
    board = await get_board()
    await render_and_save(board)
    return Path("docs/GUILD_BOARD.md")


async def board_post(
    agent: str, message: str, quest_id: str | None = None, post_type: str = "progress"
) -> dict:
    """Post a message from an agent."""
    result = await agent_post(
        agent_id=agent,
        message=message,
        quest_id=quest_id,
        post_type=post_type,
    )
    return result


async def board_claim(agent: str, quest_id: str) -> dict:
    """Claim a quest."""
    success, msg = await agent_claim(agent, quest_id)
    return {"success": success, "message": msg}


async def board_start(agent: str, quest_id: str) -> dict:
    """Start a claimed quest."""
    success, msg = await agent_start(agent, quest_id)
    return {"success": success, "message": msg}


async def board_complete(agent: str, quest_id: str, artifacts: list[str] | None = None) -> dict:
    """Complete a quest."""
    success, msg = await agent_complete(agent, quest_id, artifacts)
    return {"success": success, "message": msg}


async def board_heartbeat(
    agent: str,
    status: str = "idle",
    current_quest: str | None = None,
    capabilities: list[str] | None = None,
) -> dict:
    """Post agent heartbeat."""
    result = await agent_heartbeat(
        agent_id=agent,
        status=status,
        current_quest=current_quest,
        capabilities=capabilities or [],
    )
    return result


async def board_available_quests(agent: str, capabilities: list[str] | None = None) -> dict:
    """Get available quests for agent."""
    result = await agent_available_quests(agent, capabilities or [])
    return result


async def board_add_quest(
    agent: str,
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
    result = await agent_add_quest(
        agent_id=agent,
        title=title,
        description=description,
        quest_id=quest_id,
        priority=priority,
        safety_tier=safety_tier,
        tags=tags,
        dependencies=dependencies,
        acceptance_criteria=acceptance_criteria,
    )
    return result


async def board_close_quest(
    agent: str,
    quest_id: str,
    status: str = "done",
    reason: str | None = None,
) -> dict:
    """Close a quest with a final status."""
    result = await agent_close_quest(
        agent_id=agent,
        quest_id=quest_id,
        status=status,
        reason=reason,
    )
    return result


async def main():
    """CLI entrypoint."""
    if len(sys.argv) < 2:
        logger.info(
            """Guild Board CLI

Usage:
  python -m src.guild.guild_cli board_status
  python -m src.guild.guild_cli board_render
  python -m src.guild.guild_cli board_heartbeat <agent> [status] [quest_id]
  python -m src.guild.guild_cli board_claim <agent> <quest_id>
  python -m src.guild.guild_cli board_start <agent> <quest_id>
  python -m src.guild.guild_cli board_post <agent> <message> [quest_id] [type]
  python -m src.guild.guild_cli board_complete <agent> <quest_id>
  python -m src.guild.guild_cli board_available_quests <agent> [capabilities]
  python -m src.guild.guild_cli board_add_quest <agent> <title> <description> [priority] [safety] [tags]
  python -m src.guild.guild_cli board_close_quest <agent> <quest_id> [status] [reason]
"""
        )
        return

    await init_board()
    command = sys.argv[1]

    try:
        if command == "board_status":
            result = await board_status()
            import json

            logger.info(json.dumps(result, indent=2, default=str))

        elif command == "board_render":
            path = await board_render()
            logger.info(f"✅ Board rendered to {path}")

        elif command == "board_heartbeat":
            agent = sys.argv[2] if len(sys.argv) > 2 else "unknown"
            status = sys.argv[3] if len(sys.argv) > 3 else "idle"
            quest_id = sys.argv[4] if len(sys.argv) > 4 else None
            result = await board_heartbeat(agent, status, quest_id)
            import json

            logger.info(json.dumps(result, indent=2, default=str))

        elif command == "board_claim":
            agent = sys.argv[2]
            quest_id = sys.argv[3]
            result = await board_claim(agent, quest_id)
            import json

            logger.info(json.dumps(result, indent=2, default=str))

        elif command == "board_start":
            agent = sys.argv[2]
            quest_id = sys.argv[3]
            result = await board_start(agent, quest_id)
            import json

            logger.info(json.dumps(result, indent=2, default=str))

        elif command == "board_post":
            agent = sys.argv[2]
            message = sys.argv[3]
            quest_id = sys.argv[4] if len(sys.argv) > 4 else None
            post_type = sys.argv[5] if len(sys.argv) > 5 else "progress"
            result = await board_post(agent, message, quest_id, post_type)
            import json

            logger.info(json.dumps(result, indent=2, default=str))

        elif command == "board_complete":
            agent = sys.argv[2]
            quest_id = sys.argv[3]
            result = await board_complete(agent, quest_id)
            import json

            logger.info(json.dumps(result, indent=2, default=str))

        elif command == "board_available_quests":
            agent = sys.argv[2]
            capabilities = sys.argv[3].split(",") if len(sys.argv) > 3 else []
            result = await board_available_quests(agent, capabilities)
            import json

            logger.info(json.dumps(result, indent=2, default=str))

        elif command == "board_add_quest":
            agent = sys.argv[2]
            title = sys.argv[3]
            description = sys.argv[4]
            priority = int(sys.argv[5]) if len(sys.argv) > 5 else 3
            safety = sys.argv[6] if len(sys.argv) > 6 else "safe"
            tags = sys.argv[7].split(",") if len(sys.argv) > 7 else []
            result = await board_add_quest(
                agent,
                title,
                description,
                priority=priority,
                safety_tier=safety,
                tags=tags,
            )
            import json

            logger.info(json.dumps(result, indent=2, default=str))

        elif command == "board_close_quest":
            agent = sys.argv[2]
            quest_id = sys.argv[3]
            status = sys.argv[4] if len(sys.argv) > 4 else "done"
            reason = sys.argv[5] if len(sys.argv) > 5 else None
            result = await board_close_quest(agent, quest_id, status, reason)
            import json

            logger.info(json.dumps(result, indent=2, default=str))

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
