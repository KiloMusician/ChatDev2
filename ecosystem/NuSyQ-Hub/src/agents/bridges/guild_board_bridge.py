"""Guild Board Bridge - Simplified access to the guild board."""

from pathlib import Path
from typing import Any

from src.guild.guild_board import GuildBoard
from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


class GuildBoardBridge:
    """Compatibility wrapper around GuildBoard."""

    def __init__(
        self,
        state_dir: Path | None = None,
        data_dir: Path | None = None,
    ) -> None:
        """Initialize guild board compatibility wrapper."""
        self.board = GuildBoard(
            state_dir=state_dir or Path("state/guild"),
            data_dir=data_dir or Path("data"),
        )

    async def post_update(
        self,
        agent_id: str,
        message: str,
        quest_id: str | None = None,
        post_type: str = "progress",
        artifacts: list[str] | None = None,
    ) -> dict[str, Any]:
        """Post an update to the guild board."""
        post = await self.board.post_on_board(
            agent_id=agent_id,
            message=message,
            quest_id=quest_id,
            post_type=post_type,
            artifacts=artifacts,
        )
        if isinstance(post, dict):
            return dict(post)
        if hasattr(post, "__dict__"):
            return dict(vars(post))
        return {"result": str(post)}

    async def add_quest(
        self,
        title: str,
        description: str,
        priority: int = 3,
        safety_tier: str = "safe",
        tags: list[str] | None = None,
    ) -> tuple[bool, str]:
        """Add a quest to the board."""
        raw_result = await self.board.add_quest(
            quest_id=None,
            title=title,
            description=description,
            priority=priority,
            safety_tier=safety_tier,
            tags=tags,
        )
        if isinstance(raw_result, tuple) and len(raw_result) == 2:
            success, message = raw_result
            return bool(success), str(message)
        return False, f"Unexpected add_quest return type: {type(raw_result).__name__}"

    async def get_summary(self) -> dict[str, Any]:
        """Return a condensed board summary."""
        raw_summary = await self.board.get_board_summary()
        if isinstance(raw_summary, dict):
            return dict(raw_summary)
        return {"summary": raw_summary}


__all__ = ["GuildBoardBridge"]
