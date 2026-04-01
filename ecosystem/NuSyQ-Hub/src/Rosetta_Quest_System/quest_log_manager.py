"""QuestLogManager shim for compatibility with older imports.

This module provides a tiny facade named QuestLogManager which wraps the
existing QuestManager implementation found in `quest_manager.py`.
"""

from typing import Any

from src.Rosetta_Quest_System.quest_manager import QuestManager


class QuestLogManager:
    """Compatibility facade exposing a minimal API expected by other modules."""

    def __init__(self) -> None:
        """Initialize QuestLogManager."""
        self._mgr = QuestManager()

    def list_questlines(self) -> list[Any]:
        return self._mgr.list_questlines()

    def list_quests(self) -> list[Any]:
        return self._mgr.list_quests()

    def add_quest(self, *args, **kwargs):
        return self._mgr.add_quest(*args, **kwargs)

    def update_quest_status(self, quest_id, status):
        return self._mgr.update_quest_status(quest_id, status)
