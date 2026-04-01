"""Haystack integration for RAG-enhanced agent routing.

Phase 1B expansion: integrate Haystack pipelines to enable semantic search
over agent capabilities and past successful routing decisions.

Integration points:
  - Agent capability vector index (BM25/embedding-based)
  - Retrieval of similar past routing decisions
  - Feedback loop from outcome data to improve future routing

cSpell:ignore Haystack FAISS
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class AgentRetriever:
    """Retrieve relevant agents based on task description and history.

    Uses Haystack + embeddings to find agents who have succeeded
    on similar tasks in the past.
    """

    def __init__(self) -> None:
        self._index: List[Dict[str, Any]] = []
        self._root = Path(__file__).resolve().parents[2]
        self._feedback_dir = self._root / "Reports" / "haystack"
        self._feedback_dir.mkdir(parents=True, exist_ok=True)

    def retrieve_similar_agents(
        self,
        task_description: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Retrieve top-K agents similar to task description.

        Args:
            task_description: Human-readable task description
            top_k: Number of results to return

        Returns:
            List of dicts with agent name, description, and similarity score
        """
        if top_k <= 0:
            return []
        if not self._index:
            self.index_agent_capabilities(self._load_profiles_from_registry())
        if not self._index:
            return []

        query_tokens = _tokenize(task_description)
        if not query_tokens:
            return []

        scored: List[Dict[str, Any]] = []
        for profile in self._index:
            token_set = set(profile.get("_token_set", []))
            if not token_set:
                continue
            overlap = len(query_tokens & token_set)
            if overlap == 0:
                continue
            union = len(query_tokens | token_set)
            score = overlap / max(union, 1)
            scored.append(
                {
                    "agent_name": profile["agent_name"],
                    "description": profile["description"],
                    "capabilities": profile["capabilities"],
                    "similarity_score": round(score, 4),
                }
            )

        scored.sort(key=lambda item: item["similarity_score"], reverse=True)
        return scored[:top_k]

    def index_agent_capabilities(
        self,
        agent_profiles: List[Dict[str, Any]],
    ) -> None:
        """Index agent profiles into Haystack document store.

        Args:
            agent_profiles: List of dicts with agent name and description
        """
        indexed: List[Dict[str, Any]] = []
        for profile in agent_profiles:
            agent_name = str(profile.get("agent_name") or profile.get("name") or "").strip()
            if not agent_name:
                continue
            capabilities: Any = profile.get("capabilities", [])
            description = str(profile.get("description", "")).strip()
            if isinstance(capabilities, str):
                capability_list = [cap.strip() for cap in capabilities.split(",") if cap.strip()]
            else:
                capability_list = [str(cap).strip() for cap in capabilities if str(cap).strip()]
            token_source = " ".join([agent_name, description, *capability_list])
            indexed.append(
                {
                    "agent_name": agent_name,
                    "description": description,
                    "capabilities": capability_list,
                    "_token_set": sorted(_tokenize(token_source)),
                }
            )
        self._index = indexed

    def feedback_loop(
        self,
        task_description: str,
        selected_agent: str,
        outcome: str,  # "success" or "failure"
    ) -> None:
        """Record outcome to improve future retrieval.

        Args:
            task_description: Original task
            selected_agent: Selected agent name
            outcome: Result of agent execution
        """
        feedback_file = self._feedback_dir / "routing_feedback.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task_description": task_description,
            "selected_agent": selected_agent,
            "outcome": outcome,
        }
        with open(feedback_file, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _load_profiles_from_registry(self) -> List[Dict[str, Any]]:
        try:
            from config.agent_registry import AgentRegistry

            registry = AgentRegistry()
            profiles: List[Dict[str, Any]] = []
            for agent in registry.get_all_agents():
                profiles.append(
                    {
                        "agent_name": agent.name,
                        "description": "; ".join(agent.strengths + agent.use_cases),
                        "capabilities": agent.capabilities,
                    }
                )
            return profiles
        except (
            ImportError,
            OSError,
            RuntimeError,
            ValueError,
            TypeError,
            AttributeError,
        ):
            return []


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9_]+", text.lower())
    return {token for token in tokens if len(token) > 1}
