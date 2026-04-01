"""Regression tests for signal_quest_mapper GuildBoard integration."""

from __future__ import annotations

import asyncio
import json
import sys
import types
from pathlib import Path

from src.orchestration import signal_quest_mapper


def test_get_guild_board_signals_uses_board_snapshot_fallback(monkeypatch) -> None:
    """Mapper should read signals from board.board.signals when get_state is unavailable."""
    fake_module = types.ModuleType("src.guild.guild_board")

    class DummyBoardState:
        signals = [{"id": "sig-1", "type": "error", "severity": "high", "message": "x"}]

    class DummyGuildBoard:
        def __init__(self) -> None:
            self.board = DummyBoardState()

    fake_module.GuildBoard = DummyGuildBoard
    monkeypatch.setitem(sys.modules, "src.guild.guild_board", fake_module)
    monkeypatch.setattr(
        signal_quest_mapper, "quest_already_exists", lambda *_args, **_kwargs: False
    )

    signals = asyncio.run(signal_quest_mapper.get_guild_board_signals())
    assert len(signals) == 1
    assert signals[0]["id"] == "sig-1"


def test_get_guild_board_signals_skips_already_processed(monkeypatch) -> None:
    """Mapper should not return signals that already have linked quests."""
    fake_module = types.ModuleType("src.guild.guild_board")

    class DummyBoardState:
        signals = [
            {"id": "sig-1", "type": "error", "severity": "high", "message": "x"},
            {"id": "sig-2", "type": "error", "severity": "high", "message": "y"},
        ]

    class DummyGuildBoard:
        def __init__(self) -> None:
            self.board = DummyBoardState()

    fake_module.GuildBoard = DummyGuildBoard
    monkeypatch.setitem(sys.modules, "src.guild.guild_board", fake_module)
    monkeypatch.setattr(
        signal_quest_mapper,
        "quest_already_exists",
        lambda signal_id, _path: signal_id == "sig-1",
    )

    signals = asyncio.run(signal_quest_mapper.get_guild_board_signals())
    assert len(signals) == 1
    assert signals[0]["id"] == "sig-2"


def test_add_quest_to_log_skips_duplicate_open_title(tmp_path: Path) -> None:
    """Mapper should avoid creating duplicate open quests with the same title."""
    quest_log = tmp_path / "quest_log.jsonl"
    existing = {
        "id": "quest_existing",
        "timestamp": "2026-02-18T00:00:00",
        "title": "Fix 50 ruff linting issues",
        "status": "open",
        "signal_id": "sig-existing",
    }
    quest_log.write_text(json.dumps(existing) + "\n", encoding="utf-8")

    quest = signal_quest_mapper.QuestToCreate(
        title="Fix 50 ruff linting issues",
        description="Duplicate quest attempt",
        priority=2,
        action_hint="python scripts/start_nusyq.py enhance fix",
        estimated_effort="quick",
        signal_id="sig-new",
        acceptance_criteria=["criterion"],
        tags=["error", "ruff"],
    )

    created = signal_quest_mapper.add_quest_to_log(quest, quest_log_path=quest_log)
    assert created is False
    lines = quest_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_add_quest_to_log_allows_same_title_when_closed(tmp_path: Path) -> None:
    """Closed quests should not block creation of a new quest with the same title."""
    quest_log = tmp_path / "quest_log.jsonl"
    existing = {
        "id": "quest_existing",
        "timestamp": "2026-02-18T00:00:00",
        "title": "Fix 50 ruff linting issues",
        "status": "closed",
        "signal_id": "sig-existing",
    }
    quest_log.write_text(json.dumps(existing) + "\n", encoding="utf-8")

    quest = signal_quest_mapper.QuestToCreate(
        title="Fix 50 ruff linting issues",
        description="Allowed because existing quest is closed",
        priority=2,
        action_hint="python scripts/start_nusyq.py enhance fix",
        estimated_effort="quick",
        signal_id="sig-new",
        acceptance_criteria=["criterion"],
        tags=["error", "ruff"],
    )

    created = signal_quest_mapper.add_quest_to_log(quest, quest_log_path=quest_log)
    assert created is True
    lines = quest_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
