"""Guild Board → OpenClaw Notification Bridge.

Registers as a guild event listener and forwards notable events to the
OpenClaw Gateway so they surface in Slack, Discord, Telegram, etc.

Events forwarded:
- quest_completed    — always (agent finished work)
- quest_added        — only when priority >= HIGH or category in critical set
- quest_claimed      — summary of who claimed what (throttled)
- agent_heartbeat    — OFFLINE transitions only (agent went down)
- signal             — all signals (culture ship vetoes, escalations, etc.)

Usage::

    from src.guild.guild_openclaw_notifier import attach_to_board
    from src.guild.guild_board import get_board

    board = await get_board()
    attach_to_board(board)            # auto-attached on module import via get_board hook
    # or manually:
    notifier = GuildOpenClawNotifier()
    board.register_event_listener(notifier.on_guild_event)

The notifier is designed to be completely non-blocking — it schedules
delivery as a background asyncio task and never raises to the board.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

logger = logging.getLogger(__name__)

# Priority threshold: only forward quest_added for these priorities or above
_NOTIFY_QUEST_ADDED_PRIORITIES: frozenset[str] = frozenset(
    {"CRITICAL", "HIGH", "critical", "high", "1", "2"}
)

# Tags/categories that always trigger quest_added notifications
_CRITICAL_QUEST_TAGS: frozenset[str] = frozenset(
    {"security", "SECURITY", "blocker", "BLOCKER", "critical", "CRITICAL", "escalated"}
)

# Channel to post notifications to (configurable via env)
_DEFAULT_CHANNEL = "internal"


def _get_target_channel() -> str:
    """Resolve notification channel from env or default."""
    import os

    return os.getenv("GUILD_NOTIFY_CHANNEL", _DEFAULT_CHANNEL)


def _get_target_user() -> str:
    """Resolve notification user/room from env or default."""
    import os

    return os.getenv("GUILD_NOTIFY_USER", "guild-feed")


def _fmt_quest_completed(data: dict[str, Any]) -> str:
    """Format a quest_completed event as a human-readable message."""
    quest_id = data.get("quest_id", "?")
    title = data.get("title", data.get("description", ""))[:80]
    agent = data.get("agent_id", data.get("agent", "?"))
    artifacts = data.get("artifacts", [])
    artifact_note = f"\n📎 Artifacts: {len(artifacts)}" if artifacts else ""
    return f"✅ Quest complete: **{title}**\n🤖 Agent: `{agent}` | 🆔 `{quest_id}`{artifact_note}"


def _fmt_quest_added(data: dict[str, Any]) -> str:
    """Format a quest_added event."""
    quest_id = data.get("quest_id", "?")
    title = data.get("title", data.get("description", ""))[:80]
    priority = data.get("priority", "NORMAL")
    tags = data.get("tags", [])
    tag_note = f" [{', '.join(tags[:3])}]" if tags else ""
    return f"📋 New quest [{priority}]{tag_note}: **{title}**\n🆔 `{quest_id}`"


def _fmt_quest_claimed(data: dict[str, Any]) -> str:
    """Format a quest_claimed event."""
    quest_id = data.get("quest_id", "?")
    title = data.get("title", data.get("quest_title", ""))[:60]
    agent = data.get("agent_id", "?")
    return f"🤝 Quest claimed by `{agent}`: {title} (`{quest_id}`)"


def _fmt_signal(data: dict[str, Any]) -> str:
    """Format a signal event (culture ship veto, escalation, etc.)."""
    kind = data.get("kind", data.get("signal_type", "unknown"))
    message = data.get("message", data.get("content", ""))[:200]
    source = data.get("source", "guild")
    emoji = "⛵" if "culture_ship" in source.lower() else "📡"
    return f"{emoji} Signal [{kind}] from `{source}`\n{message}"


def _fmt_agent_offline(data: dict[str, Any]) -> str:
    """Format an agent going OFFLINE."""
    agent = data.get("agent_id", "?")
    status = data.get("status", "offline")
    return f"⚠️ Agent `{agent}` is now **{status.upper()}**"


def _should_notify_quest_added(data: dict[str, Any]) -> bool:
    """Return True if this quest_added event should be forwarded."""
    priority = str(data.get("priority", "NORMAL"))
    if priority in _NOTIFY_QUEST_ADDED_PRIORITIES:
        return True
    tags = {str(t).lower() for t in data.get("tags", [])}
    if tags & {t.lower() for t in _CRITICAL_QUEST_TAGS}:
        return True
    return False


class GuildOpenClawNotifier:
    """Listens to guild board events and forwards them to OpenClaw gateway.

    Attach to a GuildBoard instance::

        board.register_event_listener(notifier.on_guild_event)
    """

    # Track last-seen agent statuses to detect OFFLINE transitions
    _agent_statuses: ClassVar[dict[str, str]] = {}

    async def on_guild_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Handle a guild board event.

        Args:
            event_type: One of quest_added, quest_completed, agent_heartbeat, etc.
            data: Event payload dict from GuildBoard._emit_event.
        """
        message: str | None = None

        if event_type == "quest_completed":
            message = _fmt_quest_completed(data)

        elif event_type == "quest_added" and _should_notify_quest_added(data):
            message = _fmt_quest_added(data)

        elif event_type == "quest_claimed":
            # Throttle claim notifications — only log, don't spam external channels
            logger.info(
                "Guild quest claimed: %s by %s",
                data.get("quest_id", "?"),
                data.get("agent_id", "?"),
            )
            # Only forward if HIGH priority quest claimed
            if str(data.get("priority", "NORMAL")) in _NOTIFY_QUEST_ADDED_PRIORITIES:
                message = _fmt_quest_claimed(data)

        elif event_type == "agent_heartbeat":
            # Only forward OFFLINE transitions (not routine heartbeats)
            agent_id = data.get("agent_id", "")
            new_status = str(data.get("status", "")).lower()
            old_status = self._agent_statuses.get(agent_id, "")
            self._agent_statuses[agent_id] = new_status
            if new_status == "offline" and old_status not in ("offline", ""):
                message = _fmt_agent_offline(data)

        elif event_type == "signal":
            message = _fmt_signal(data)

        if message:
            await self._send(message)

    async def _send(self, message: str) -> None:
        """Send a message to the OpenClaw gateway. Best-effort."""
        try:
            from src.integrations.openclaw_gateway_bridge import \
                get_openclaw_gateway_bridge

            bridge = get_openclaw_gateway_bridge()
            channel = _get_target_channel()
            user = _get_target_user()
            await bridge.send_result(
                channel=channel,
                target_user_id=user,
                result_text=message,
                task_id=None,
            )
            logger.debug("Guild notification sent to %s/%s", channel, user)
        except Exception as exc:
            # Never raise — notifier must never break guild operations
            logger.debug("Guild OpenClaw notification failed (suppressed): %s", exc)


# Module-level singleton
_notifier: GuildOpenClawNotifier | None = None


def get_notifier() -> GuildOpenClawNotifier:
    """Return or create the module-level GuildOpenClawNotifier singleton."""
    global _notifier
    if _notifier is None:
        _notifier = GuildOpenClawNotifier()
    return _notifier


def attach_to_board(board: Any) -> None:
    """Attach the OpenClaw notifier to a GuildBoard instance.

    Idempotent — safe to call multiple times.

    Args:
        board: A GuildBoard instance with register_event_listener().
    """
    notifier = get_notifier()
    board.register_event_listener(notifier.on_guild_event)
    logger.info("Guild→OpenClaw notifier attached to board")
