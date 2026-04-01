"""🗺️ Rosetta Quest System — quest-based task management and tracking.

Provides quest-based orchestration for development and system tasks.
UUID-based quest model with JSONL audit trail.

Data model fields:
  Quest: id(UUID), title, questline, status, dependencies, tags, history
  Questline: collection of related quests
  Statuses: pending → active → complete / blocked / archived

OmniTag: {
    "purpose": "quest_subsystem",
    "tags": ["Quest", "QuestEngine", "TaskOrchestration", "JSONL", "UUID"],
    "category": "orchestration",
    "evolution_stage": "v2.0"
}
MegaTag: [QUEST_ENGINE, PACKAGE_INIT]
"""

from __future__ import annotations

__all__ = [
    # Core data model
    "Quest",
    # Engine + utilities
    "QuestEngine",
    # Manager layers
    "QuestLogManager",
    "QuestManager",
    "Questline",
    "load_questlines",
    "load_quests",
    "log_event",
    "save_questlines",
    "save_quests",
]


def __getattr__(name: str) -> object:
    if name in (
        "Quest",
        "Questline",
        "QuestEngine",
        "load_quests",
        "save_quests",
        "load_questlines",
        "save_questlines",
        "log_event",
        "log_three_before_new",
    ):
        from src.Rosetta_Quest_System.quest_engine import (
            Quest, QuestEngine, Questline, load_questlines, load_quests,
            log_event, log_three_before_new, save_questlines, save_quests)

        return locals()[name]
    if name == "QuestLogManager":
        from src.Rosetta_Quest_System.quest_log_manager import QuestLogManager

        return QuestLogManager
    if name == "QuestManager":
        from src.Rosetta_Quest_System.quest_manager import QuestManager

        return QuestManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
