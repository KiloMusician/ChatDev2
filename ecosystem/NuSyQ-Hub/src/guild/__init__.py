"""Guild module - Adventurer's Guild coordination system.

The guild board is the central coordination substrate for multi-agent work.

Core API:
- get_board() - Get the singleton board instance
- init_board() - Initialize the board
- Agent protocols via agent_guild_protocols module
"""

from src.guild.agent_guild_protocols import (agent_add_quest,
                                             agent_available_quests,
                                             agent_claim, agent_close_quest,
                                             agent_complete, agent_heartbeat,
                                             agent_post, agent_start,
                                             agent_yield)
from src.guild.guild_board import (AgentId, AgentStatus, GuildBoard, QuestId,
                                   QuestState, get_board, init_board)
from src.guild.guild_board_renderer import GuildBoardRenderer, render_and_save

__all__ = [
    "AgentId",  # String identifier for agents (claude, ollama, copilot, etc.)
    "AgentStatus",
    # Board
    "GuildBoard",
    # Renderer
    "GuildBoardRenderer",
    # Type aliases
    "QuestId",  # UUID string for quest identification
    "QuestState",
    "agent_add_quest",
    "agent_available_quests",
    "agent_claim",
    "agent_close_quest",
    "agent_complete",
    # Protocols
    "agent_heartbeat",
    "agent_post",
    "agent_start",
    "agent_yield",
    "get_board",
    "init_board",
    "render_and_save",
]
