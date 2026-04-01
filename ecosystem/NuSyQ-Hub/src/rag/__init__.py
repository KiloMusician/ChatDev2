"""RAG (Retrieval-Augmented Generation) subsystem — project indexing.

Provides document indexing and retrieval for ChatDev projects, enabling
AI agents to search and reference project artifacts during code generation
and analysis workflows.

OmniTag: {
    "purpose": "rag_subsystem",
    "tags": ["RAG", "Indexing", "Retrieval", "ChatDev"],
    "category": "ai_infrastructure",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

__all__ = [
    "ChatDevProjectIndexer",
    "ProjectDocument",
    "ProjectMetadata",
    "get_chatdev_project_indexer",
]


def __getattr__(name: str):
    if name in (
        "ProjectMetadata",
        "ProjectDocument",
        "ChatDevProjectIndexer",
        "get_chatdev_project_indexer",
    ):
        from src.rag.chatdev_project_indexer import (
            ChatDevProjectIndexer, ProjectDocument, ProjectMetadata,
            get_chatdev_project_indexer)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
