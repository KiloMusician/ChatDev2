"""Guild Board → Terminal Log Notifier.

Registers as a guild event listener and routes notable events to the
terminal log files watched by the PowerShell watcher scripts.  This
makes every agent "aware" of guild activity in real-time — each event
appears in the appropriate colored terminal without any manual wiring.

Events routed:
- quest_added        → tasks terminal (+ agent's terminal if agent_id known)
- quest_completed    → tasks + metrics terminals
- quest_claimed      → tasks terminal
- quest_failed       → errors terminal
- agent_heartbeat    → agents terminal (or agent-specific terminal)
- board_post         → main terminal
- signal             → main terminal (all signals)
- terminal_registry_updated → system terminal

Usage (auto-attached by get_board())::

    from src.guild.guild_terminal_notifier import attach_to_board
    attach_to_board(board)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_attached = False


class GuildTerminalNotifier:
    """Listens to guild events and routes them to terminal log files."""

    def __init__(self) -> None:
        # Import lazily to avoid circular imports at module load
        from src.system.agent_awareness import emit

        self._emit = emit

    async def on_guild_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Called by GuildBoard._emit_event for every board event."""
        try:
            await self._route(event_type, data)
        except Exception as exc:
            logger.debug("guild_terminal_notifier routing error: %s", exc)

    async def _route(self, event_type: str, data: dict[str, Any]) -> None:
        emit = self._emit

        if event_type == "quest_added":
            title = data.get("title", "?")
            priority = data.get("priority", "?")
            tags = ", ".join(data.get("tags") or [])
            msg = f"Quest added: [{priority}] {title}" + (f"  [{tags}]" if tags else "")
            emit("tasks", msg, level="INFO", source="guild")

        elif event_type == "quest_completed":
            title = data.get("title", "?")
            agent = data.get("agent_id", "")
            msg = f"Quest completed: {title}" + (f"  (by {agent})" if agent else "")
            emit("tasks", msg, level="INFO", source="guild")
            emit("metrics", msg, level="INFO", source="guild")
            if agent:
                emit(agent, f"Completed: {title}", level="INFO", source="guild")

        elif event_type == "quest_claimed":
            title = data.get("title") or data.get("quest_id", "?")
            agent = data.get("agent_id", "?")
            msg = f"Quest claimed by {agent}: {title}"
            emit("tasks", msg, level="INFO", source="guild")
            emit(agent, f"Claimed: {title}", level="INFO", source="guild")

        elif event_type in ("quest_failed", "quest_blocked"):
            title = data.get("title", "?")
            reason = data.get("reason", "")
            msg = f"Quest {event_type.split('_')[1]}: {title}" + (f" — {reason}" if reason else "")
            emit("errors", msg, level="ERROR", source="guild")
            emit("tasks", msg, level="WARNING", source="guild")

        elif event_type == "agent_heartbeat":
            agent_id = data.get("agent_id", "?")
            status = data.get("status", "?")
            quest = data.get("current_quest")
            msg = f"{agent_id} heartbeat: {status}" + (f"  (working on: {quest})" if quest else "")
            level = "WARNING" if status in ("OFFLINE", "BLOCKED") else "INFO"
            emit("agents", msg, level=level, source="guild")
            emit(agent_id, f"Status: {status}", level=level, source="guild")

        elif event_type == "board_post":
            content = data.get("content", "")
            author = data.get("author", "guild")
            msg = f"[board] {author}: {content}"
            emit("main", msg, level="INFO", source="guild")

        elif event_type == "signal":
            sig_type = data.get("signal_type", "?")
            msg_body = data.get("message", str(data))
            msg = f"[signal:{sig_type}] {msg_body}"
            emit("main", msg, level="WARNING", source="guild")

        elif event_type == "terminal_registry_updated":
            active = data.get("active_terminals", 0)
            roles = data.get("roles", [])
            msg = f"Terminal registry updated: {active} active ({len(roles)} roles)"
            emit("system", msg, level="INFO", source="registry")

        else:
            # Catch-all: forward unknown events to main + system
            emit("main", f"[{event_type}] {str(data)[:200]}", level="INFO", source="guild")


def attach_to_board(board: Any) -> None:
    """Register GuildTerminalNotifier as a listener on *board*.

    Idempotent — safe to call multiple times.
    """
    global _attached
    if _attached:
        return
    try:
        notifier = GuildTerminalNotifier()
        board.register_event_listener(notifier.on_guild_event)
        _attached = True
        logger.debug("GuildTerminalNotifier attached to board")
    except Exception as exc:
        logger.debug("guild_terminal_notifier attach failed: %s", exc)
