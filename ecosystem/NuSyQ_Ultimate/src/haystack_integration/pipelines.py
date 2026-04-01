"""Haystack pipeline definitions for NuSyQ agent routing.

Modular Haystack components:
  - Document store initialization
  - BM25 retrieval over agent metadata
  - Feedback storage

Integration pattern:
  from src.haystack_integration.pipelines import build_routing_pipeline
  pipeline = build_routing_pipeline()
  results = pipeline.run({"query": "debugging Python concurrency bugs"})

cSpell:ignore Haystack Retrieval
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.haystack_integration import AgentRetriever


class FallbackRoutingPipeline:
    """Small stand-in pipeline with the Haystack-like `.run()` contract."""

    def __init__(self, retriever: Optional[AgentRetriever] = None) -> None:
        self.retriever = retriever or AgentRetriever()

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        query = str(inputs.get("query", "")).strip()
        top_k_raw = inputs.get("top_k", 3)
        top_k = int(top_k_raw) if isinstance(top_k_raw, (int, str)) else 3
        results = self.retriever.retrieve_similar_agents(query, top_k=max(1, top_k))
        documents = [
            {
                "content": item["description"],
                "meta": {
                    "agent_name": item["agent_name"],
                    "capabilities": item["capabilities"],
                },
                "score": item["similarity_score"],
            }
            for item in results
        ]
        return {"documents": documents, "results": results}


def build_routing_pipeline() -> Optional[Any]:
    """Build a Haystack Pipeline for agent semantic search.

    Returns:
        Haystack Pipeline instance (or None if Haystack not available)

    Note:
        Falls back to an internal lexical retriever when Haystack is absent.
    """
    return FallbackRoutingPipeline()


def index_agents_from_registry(
    registry_path: str,
) -> FallbackRoutingPipeline:
    """Load agent registry and build Haystack document index.

    Args:
        registry_path: Path to config/agent_registry.yaml

    Returns:
        Initialized fallback pipeline with indexed agent capabilities.
    """
    retriever = AgentRetriever()
    registry = Path(registry_path)
    if not registry.exists():
        return FallbackRoutingPipeline(retriever=retriever)

    profiles: List[Dict[str, Any]] = []
    try:
        from config.agent_registry import AgentRegistry

        agent_registry = AgentRegistry(registry_path=registry)
        for agent in agent_registry.get_all_agents():
            profiles.append(
                {
                    "agent_name": agent.name,
                    "description": "; ".join(agent.strengths + agent.use_cases),
                    "capabilities": agent.capabilities,
                }
            )
    except (ImportError, OSError, RuntimeError, ValueError, TypeError, AttributeError):
        profiles = []

    retriever.index_agent_capabilities(profiles)
    return FallbackRoutingPipeline(retriever=retriever)


def query_agent_similarity(
    query: str,
    pipeline: Any,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Query the Haystack pipeline for similar agents.

    Args:
        query: Task description or agent requirement
        pipeline: Haystack Pipeline instance
        top_k: Number of results to return

    Returns:
        List of dicts with agent name, description, score
    """
    if pipeline is None:
        return []

    try:
        response = pipeline.run({"query": query, "top_k": top_k})
    except (AttributeError, RuntimeError, ValueError, TypeError):
        return []

    if not isinstance(response, dict):
        return []
    if isinstance(response.get("results"), list):
        return response["results"]

    documents = response.get("documents", [])
    if not isinstance(documents, list):
        return []
    flattened: List[Dict[str, Any]] = []
    for item in documents:
        if not isinstance(item, dict):
            continue
        meta = item.get("meta", {}) if isinstance(item.get("meta"), dict) else {}
        flattened.append(
            {
                "agent_name": meta.get("agent_name", "unknown"),
                "description": item.get("content", ""),
                "capabilities": meta.get("capabilities", []),
                "similarity_score": item.get("score", 0.0),
            }
        )
    return flattened[:top_k]
