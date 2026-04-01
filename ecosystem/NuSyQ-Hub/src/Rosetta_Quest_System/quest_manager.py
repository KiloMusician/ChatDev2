"""Minimal QuestManager facade to satisfy activation import.

Provides a small API surface used by `ACTIVATE_SYSTEM.py`.
"""

from typing import Any

from src.Rosetta_Quest_System.quest_engine import QuestEngine


class QuestManager:
    def __init__(self) -> None:
        """Initialize QuestManager."""
        self.engine = QuestEngine()

    def list_questlines(self) -> list[Any]:
        # Return names of questlines for quick activation reporting
        return list(self.engine.questlines.keys())

    def list_quests(self) -> list[Any]:
        return [q.to_dict() for q in self.engine.quests.values()]

    # small convenience wrappers
    def add_quest(self, *args, **kwargs):
        return self.engine.add_quest(*args, **kwargs)

    def update_quest_status(self, quest_id, status):
        return self.engine.update_quest_status(quest_id, status)


# Backward-compat alias used by src/games/CyberTerminal/integrated_terminal.py
QuestSystem = QuestManager
