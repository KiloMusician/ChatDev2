"""Tests for GuildOpenClawNotifier and its helper functions.

Covers:
- _should_notify_quest_added() — priority gate (HIGH/CRITICAL → True, NORMAL → False)
- _should_notify_quest_added() — security tag overrides NORMAL priority
- _fmt_quest_completed() — includes quest_id and agent in output
- _fmt_quest_claimed() — includes agent_id in output
- GuildOpenClawNotifier.on_guild_event() for quest_completed → calls _send()
- GuildOpenClawNotifier.on_guild_event() for agent_heartbeat OFFLINE transition → calls _send()
- GuildOpenClawNotifier.on_guild_event() for agent_heartbeat routine → does NOT call _send()
- attach_to_board() registers the notifier's listener on the board

Isolation note: GuildOpenClawNotifier uses a ClassVar ``_agent_statuses``
dict.  Each test that exercises heartbeat logic should clear it first so
previous test state cannot bleed through.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.guild.guild_openclaw_notifier import (
    GuildOpenClawNotifier,
    _fmt_quest_claimed,
    _fmt_quest_completed,
    _should_notify_quest_added,
    attach_to_board,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_notifier() -> GuildOpenClawNotifier:
    """Return a fresh GuildOpenClawNotifier with cleared class-level state."""
    GuildOpenClawNotifier._agent_statuses.clear()
    return GuildOpenClawNotifier()


# ---------------------------------------------------------------------------
# 1. _should_notify_quest_added() — priority gate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("priority", ["HIGH", "high", "CRITICAL", "critical", "1", "2"])
def test_should_notify_high_and_critical_priorities(priority: str):
    """HIGH and CRITICAL priority quests (and numeric equivalents) should trigger
    a notification.
    """
    data: dict[str, Any] = {"priority": priority, "tags": []}
    assert _should_notify_quest_added(data) is True


@pytest.mark.parametrize("priority", ["NORMAL", "normal", "LOW", "low", "MEDIUM", "medium"])
def test_should_not_notify_normal_and_lower_priorities(priority: str):
    """NORMAL, LOW, and MEDIUM priority quests without critical tags should NOT
    trigger a notification.
    """
    data: dict[str, Any] = {"priority": priority, "tags": []}
    assert _should_notify_quest_added(data) is False


def test_should_not_notify_missing_priority():
    """When priority is absent the default is NORMAL — no notification."""
    data: dict[str, Any] = {"tags": []}
    assert _should_notify_quest_added(data) is False


# ---------------------------------------------------------------------------
# 2. _should_notify_quest_added() — security tag overrides NORMAL priority
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tag", ["security", "SECURITY", "blocker", "BLOCKER", "escalated"])
def test_should_notify_security_tag_overrides_normal_priority(tag: str):
    """A quest with a critical tag (security, blocker, escalated…) must trigger
    a notification even when priority is NORMAL.
    """
    data: dict[str, Any] = {"priority": "NORMAL", "tags": [tag]}
    assert _should_notify_quest_added(data) is True


def test_should_notify_security_tag_mixed_with_other_tags():
    """A 'security' tag among other tags still triggers a notification."""
    data: dict[str, Any] = {
        "priority": "NORMAL",
        "tags": ["feature", "security", "backend"],
    }
    assert _should_notify_quest_added(data) is True


# ---------------------------------------------------------------------------
# 3. _fmt_quest_completed() — includes quest_id and agent
# ---------------------------------------------------------------------------


def test_fmt_quest_completed_includes_quest_id():
    """_fmt_quest_completed() must contain the quest_id in the returned string."""
    data: dict[str, Any] = {
        "quest_id": "abc-123",
        "title": "Fix the login bug",
        "agent_id": "ollama",
    }
    result = _fmt_quest_completed(data)
    assert "abc-123" in result


def test_fmt_quest_completed_includes_agent():
    """_fmt_quest_completed() must reference the agent_id."""
    data: dict[str, Any] = {
        "quest_id": "xyz-789",
        "title": "Write tests",
        "agent_id": "codex-agent",
    }
    result = _fmt_quest_completed(data)
    assert "codex-agent" in result


def test_fmt_quest_completed_falls_back_to_agent_field():
    """Falls back to 'agent' key when 'agent_id' is absent."""
    data: dict[str, Any] = {
        "quest_id": "q1",
        "title": "Refactor",
        "agent": "lmstudio",
    }
    result = _fmt_quest_completed(data)
    assert "lmstudio" in result


def test_fmt_quest_completed_handles_missing_fields():
    """_fmt_quest_completed() must not raise when optional fields are absent."""
    result = _fmt_quest_completed({})
    assert isinstance(result, str)
    assert "?" in result  # sentinel for missing quest_id and agent


# ---------------------------------------------------------------------------
# 4. _fmt_quest_claimed() — includes agent_id
# ---------------------------------------------------------------------------


def test_fmt_quest_claimed_includes_agent_id():
    """_fmt_quest_claimed() must contain the agent_id."""
    data: dict[str, Any] = {
        "quest_id": "q99",
        "title": "Deploy service",
        "agent_id": "copilot",
    }
    result = _fmt_quest_claimed(data)
    assert "copilot" in result


def test_fmt_quest_claimed_includes_quest_id():
    """_fmt_quest_claimed() should also include the quest_id for traceability."""
    data: dict[str, Any] = {
        "quest_id": "q-unique-001",
        "title": "Deploy service",
        "agent_id": "copilot",
    }
    result = _fmt_quest_claimed(data)
    assert "q-unique-001" in result


def test_fmt_quest_claimed_handles_missing_agent():
    """Falls back gracefully when agent_id is absent."""
    data: dict[str, Any] = {"quest_id": "q2", "title": "Something"}
    result = _fmt_quest_claimed(data)
    assert isinstance(result, str)
    assert "?" in result  # sentinel for missing agent


# ---------------------------------------------------------------------------
# 5. on_guild_event() — quest_completed calls _send()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_guild_event_quest_completed_calls_send():
    """on_guild_event('quest_completed', ...) must invoke _send() with a non-empty
    message.
    """
    notifier = _make_notifier()
    notifier._send = AsyncMock()

    data: dict[str, Any] = {
        "quest_id": "q-complete-1",
        "title": "All tests pass",
        "agent_id": "pytest-runner",
    }

    await notifier.on_guild_event("quest_completed", data)

    notifier._send.assert_awaited_once()
    sent_msg: str = notifier._send.call_args[0][0]
    assert "q-complete-1" in sent_msg


@pytest.mark.asyncio
async def test_on_guild_event_quest_completed_uses_fmt_function():
    """The message forwarded for quest_completed contains the quest title."""
    notifier = _make_notifier()
    notifier._send = AsyncMock()

    data: dict[str, Any] = {
        "quest_id": "q-title-check",
        "title": "Unique Title For Assertion",
        "agent_id": "ollama",
    }

    await notifier.on_guild_event("quest_completed", data)

    sent_msg: str = notifier._send.call_args[0][0]
    assert "Unique Title For Assertion" in sent_msg


# ---------------------------------------------------------------------------
# 6. on_guild_event() — agent_heartbeat OFFLINE transition calls _send()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_guild_event_agent_goes_offline_calls_send():
    """When an agent transitions from a non-OFFLINE state to OFFLINE,
    on_guild_event must call _send() with a warning message.
    """
    notifier = _make_notifier()
    notifier._send = AsyncMock()

    # Pre-seed with a non-offline status so there is a real transition
    GuildOpenClawNotifier._agent_statuses["agent-007"] = "idle"

    data: dict[str, Any] = {"agent_id": "agent-007", "status": "OFFLINE"}

    await notifier.on_guild_event("agent_heartbeat", data)

    notifier._send.assert_awaited_once()
    sent_msg: str = notifier._send.call_args[0][0]
    assert "agent-007" in sent_msg


@pytest.mark.asyncio
async def test_on_guild_event_agent_offline_message_contains_status():
    """The OFFLINE notification message references the offline status."""
    notifier = _make_notifier()
    notifier._send = AsyncMock()

    GuildOpenClawNotifier._agent_statuses["agent-offline-test"] = "working"

    await notifier.on_guild_event(
        "agent_heartbeat", {"agent_id": "agent-offline-test", "status": "offline"}
    )

    sent_msg: str = notifier._send.call_args[0][0]
    assert "OFFLINE" in sent_msg.upper()


# ---------------------------------------------------------------------------
# 7. on_guild_event() — routine heartbeat does NOT call _send()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_guild_event_routine_heartbeat_does_not_call_send():
    """Routine heartbeats (non-OFFLINE status) must not call _send()."""
    notifier = _make_notifier()
    notifier._send = AsyncMock()

    data: dict[str, Any] = {"agent_id": "agent-alive", "status": "IDLE"}

    await notifier.on_guild_event("agent_heartbeat", data)

    notifier._send.assert_not_called()


@pytest.mark.asyncio
async def test_on_guild_event_already_offline_stays_silent():
    """An agent that was already OFFLINE and sends another OFFLINE heartbeat
    must NOT trigger a second notification (no state transition).
    """
    notifier = _make_notifier()
    notifier._send = AsyncMock()

    # Agent was already offline before this heartbeat
    GuildOpenClawNotifier._agent_statuses["sleeping-agent"] = "offline"

    await notifier.on_guild_event(
        "agent_heartbeat", {"agent_id": "sleeping-agent", "status": "offline"}
    )

    notifier._send.assert_not_called()


@pytest.mark.asyncio
async def test_on_guild_event_first_heartbeat_offline_does_not_notify():
    """An agent appearing for the first time with OFFLINE status (old='')
    must NOT trigger a notification (no meaningful transition yet).
    """
    notifier = _make_notifier()
    notifier._send = AsyncMock()

    # No prior entry in _agent_statuses
    await notifier.on_guild_event(
        "agent_heartbeat", {"agent_id": "brand-new-offline", "status": "offline"}
    )

    notifier._send.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("routine_status", ["idle", "IDLE", "working", "WORKING", "observing"])
async def test_on_guild_event_various_routine_statuses_do_not_call_send(routine_status: str):
    """All non-offline statuses should be silent."""
    notifier = _make_notifier()
    notifier._send = AsyncMock()

    await notifier.on_guild_event(
        "agent_heartbeat", {"agent_id": "routine-agent", "status": routine_status}
    )

    notifier._send.assert_not_called()


# ---------------------------------------------------------------------------
# 8. attach_to_board() registers the listener
# ---------------------------------------------------------------------------


def test_attach_to_board_registers_listener():
    """attach_to_board(board) must call board.register_event_listener() with the
    notifier's on_guild_event method.
    """
    board_mock = MagicMock()

    attach_to_board(board_mock)

    board_mock.register_event_listener.assert_called_once()
    # Verify the registered callable is a bound method named on_guild_event
    registered_fn = board_mock.register_event_listener.call_args[0][0]
    assert callable(registered_fn)
    assert registered_fn.__name__ == "on_guild_event"


def test_attach_to_board_uses_module_singleton():
    """attach_to_board() registers the module-level singleton notifier,
    not a new instance each time.
    """
    import src.guild.guild_openclaw_notifier as _notif_module

    board_mock = MagicMock()
    attach_to_board(board_mock)

    registered_fn = board_mock.register_event_listener.call_args[0][0]
    # The __self__ of a bound method is the notifier singleton
    assert registered_fn.__self__ is _notif_module.get_notifier()


def test_attach_to_board_can_be_called_multiple_times():
    """Calling attach_to_board() multiple times must not raise; each call
    registers (the board controls idempotency via register_event_listener).
    """
    board_mock = MagicMock()

    attach_to_board(board_mock)
    attach_to_board(board_mock)

    assert board_mock.register_event_listener.call_count == 2
