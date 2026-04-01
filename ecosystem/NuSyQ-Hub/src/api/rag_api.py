"""RAG API endpoints for semantic search and indexing."""

import logging
from typing import Any

from fastapi import APIRouter, Query

try:
    from src.rag.chatdev_project_indexer import ChatDevProjectIndexer
except ImportError:
    ChatDevProjectIndexer = None

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/rag/search")
def rag_search(query: str = Query(...), top_k: int = Query(5)) -> dict[str, Any]:
    """Semantic search over indexed ChatDev projects."""
    if not ChatDevProjectIndexer:
        return {"error": "RAG not available"}
    indexer = ChatDevProjectIndexer()
    results = indexer.search_projects(query, top_k=top_k)
    return {"results": results}


@router.post("/rag/reindex")
def rag_reindex(start_fresh: bool = True) -> dict[str, Any]:
    """Reindex all ChatDev projects in workspace."""
    if not ChatDevProjectIndexer:
        return {"error": "RAG not available"}
    indexer = ChatDevProjectIndexer()
    count = indexer.index_workspace(start_fresh=start_fresh)
    return {"indexed_projects": count}
