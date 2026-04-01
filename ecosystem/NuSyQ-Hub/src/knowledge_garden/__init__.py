"""Knowledge Garden subsystem — living knowledge state registry.

Single source of truth for all system artifacts (quests, proofs, changelogs,
logs, ideas). SQLite-backed registry with full lifecycle tracking and lineage.

OmniTag: {
    "purpose": "knowledge_garden_subsystem",
    "tags": ["KnowledgeGarden", "Registry", "Artifacts", "StateManagement"],
    "category": "persistence",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = [
    "Artifact",
    "LifecycleEvent",
    "Lineage",
    "StateRegistry",
]


def __getattr__(name: str):
    if name in ("LifecycleEvent", "Lineage", "Artifact", "StateRegistry"):
        from src.knowledge_garden.registry import (Artifact, LifecycleEvent,
                                                   Lineage, StateRegistry)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
