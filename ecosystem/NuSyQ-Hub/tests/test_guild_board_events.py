"""Tests for the GuildBoard event listener system.

Covers:
  - register_event_listener / unregister_event_listener
  - _emit_event dispatching to sync and async listeners
  - Exception suppression inside listeners
  - get_board() singleton auto-attaches the OpenClaw notifier
  - get_board() is idempotent (no double-attach)

Isolation note: every test that creates a GuildBoard passes
``state_dir=tmp_path / "guild"`` and ``data_dir=tmp_path / "data"``
so no runtime files (state/guild/, data/) are touched.

For get_board() tests the module-level globals ``_board`` and
``_openclaw_attached`` are reset via monkeypatch so singletons
from other tests cannot bleed through.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

import src.guild.guild_board as _gb_module
from src.guild.guild_board import GuildBoard, _listener_tasks

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_board(tmp_path) -> GuildBoard:
    """Return an isolated GuildBoard writing into *tmp_path*."""
    return GuildBoard(
        state_dir=tmp_path / "guild",
        data_dir=tmp_path / "data",
    )


# ---------------------------------------------------------------------------
# 1. Sync listener registration and dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_and_emit_sync_listener(tmp_path):
    """A sync callable registered with register_event_listener is called by
    _emit_event with the correct (event_type, data) arguments.
    """
    board = _make_board(tmp_path)

    calls: list[tuple[str, dict[str, Any]]] = []

    def sync_listener(event_type: str, data: dict[str, Any]) -> None:
        calls.append((event_type, data))

    board.register_event_listener(sync_listener)

    await board._emit_event("test_event", {"key": "value"})

    assert len(calls) == 1
    event_type, data = calls[0]
    assert event_type == "test_event"
    assert data == {"key": "value"}


# ---------------------------------------------------------------------------
# 2. Async listener registration and dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_and_emit_async_listener(tmp_path):
    """An async coroutine function registered as a listener is scheduled via
    asyncio.ensure_future; its future appears in _listener_tasks and the
    coroutine completes within the current event loop turn.
    """
    board = _make_board(tmp_path)

    results: list[str] = []

    async def async_listener(event_type: str, data: dict[str, Any]) -> None:
        results.append(event_type)

    board.register_event_listener(async_listener)

    # Clear any pre-existing futures so the assertion is unambiguous.
    _listener_tasks.clear()

    await board._emit_event("async_event", {})

    # Give the event loop a chance to run the scheduled coroutine.
    await asyncio.sleep(0)

    assert results == ["async_event"], "Async listener should have been scheduled and run."


# ---------------------------------------------------------------------------
# 3. Unregister removes listener from dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unregister_listener(tmp_path):
    """After unregister_event_listener, the callback is no longer invoked by
    _emit_event.
    """
    board = _make_board(tmp_path)

    calls: list[str] = []

    def listener(event_type: str, data: dict[str, Any]) -> None:
        calls.append(event_type)

    board.register_event_listener(listener)
    board.unregister_event_listener(listener)

    await board._emit_event("should_not_arrive", {})

    assert calls == [], "Listener should not be called after it was unregistered."


# ---------------------------------------------------------------------------
# 4. Unregistering a non-existent listener is a no-op
# ---------------------------------------------------------------------------


def test_unregister_nonexistent_is_noop(tmp_path):
    """Calling unregister_event_listener with a callable that was never
    registered must not raise any exception.
    """
    board = _make_board(tmp_path)

    def never_registered(event_type: str, data: dict[str, Any]) -> None:
        pass

    # Should complete without raising ValueError or any other exception.
    board.unregister_event_listener(never_registered)


# ---------------------------------------------------------------------------
# 5. Listener exceptions are suppressed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_emit_suppresses_listener_exception(tmp_path):
    """If a listener raises an exception, _emit_event must not propagate it.
    Other listeners registered after the faulty one must still be called.
    """
    board = _make_board(tmp_path)

    after_calls: list[str] = []

    def bad_listener(event_type: str, data: dict[str, Any]) -> None:
        raise RuntimeError("intentional test failure")

    def good_listener(event_type: str, data: dict[str, Any]) -> None:
        after_calls.append(event_type)

    board.register_event_listener(bad_listener)
    board.register_event_listener(good_listener)

    # Must not raise.
    await board._emit_event("some_event", {})

    # The good listener after the bad one must still have been called.
    assert after_calls == [
        "some_event"
    ], "Listener registered after a failing listener should still be invoked."


# ---------------------------------------------------------------------------
# 6. get_board() auto-attaches the OpenClaw notifier
# ---------------------------------------------------------------------------


@pytest.fixture
def reset_board_singleton(monkeypatch):
    """Reset module-level board singleton globals before (and after) each test
    that exercises get_board() so test isolation is guaranteed.
    """
    monkeypatch.setattr(_gb_module, "_board", None)
    monkeypatch.setattr(_gb_module, "_openclaw_attached", False)
    yield
    # monkeypatch restores originals automatically on teardown.


@pytest.mark.asyncio
async def test_get_board_attaches_openclaw_notifier(reset_board_singleton):
    """On first call, get_board() should auto-attach the GuildOpenClawNotifier,
    leaving at least one listener registered on the returned board.
    """
    board = await _gb_module.get_board()

    # The notifier's on_guild_event method must be in the listener list.
    assert (
        len(board._event_listeners) >= 1
    ), "get_board() should register at least the OpenClaw notifier as a listener."


# ---------------------------------------------------------------------------
# 7. get_board() is idempotent — same instance, no double-attach
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_board_is_idempotent(reset_board_singleton):
    """Calling get_board() multiple times must return the exact same GuildBoard
    instance and must not register the OpenClaw notifier more than once.
    """
    board_a = await _gb_module.get_board()
    board_b = await _gb_module.get_board()

    assert board_a is board_b, "get_board() must return the same singleton instance."

    # Count how many times on_guild_event appears in the listener list.
    # attach_to_board() itself is idempotent (checks list membership), but
    # _openclaw_attached guard ensures attach_to_board is only called once.
    notifier_listeners = [
        fn for fn in board_a._event_listeners if getattr(fn, "__name__", "") == "on_guild_event"
    ]
    assert len(notifier_listeners) == 1, (
        "OpenClaw notifier's on_guild_event should be registered exactly once, "
        f"but found {len(notifier_listeners)} registration(s)."
    )


# ---------------------------------------------------------------------------
# 8. register_event_listener is itself idempotent (same callable not added twice)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_same_listener_twice_is_idempotent(tmp_path):
    """Registering the same callable twice must not result in it being called
    twice per _emit_event (the list de-duplicates on insertion).
    """
    board = _make_board(tmp_path)

    calls: list[str] = []

    def listener(event_type: str, data: dict[str, Any]) -> None:
        calls.append(event_type)

    board.register_event_listener(listener)
    board.register_event_listener(listener)  # second registration — should be ignored

    await board._emit_event("dedup_event", {})

    assert calls == [
        "dedup_event"
    ], "Registering the same listener twice should not cause it to fire twice."
