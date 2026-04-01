"""Floor 1: Foundation - Neural-Symbolic Knowledge Base & OmniTag Archive.

The ground floor of the Temple of Knowledge, accessible to all agents.
Provides foundational knowledge storage, OmniTag archival, and consciousness tracking.

Features:
- Neural-symbolic knowledge storage
- OmniTag archive and retrieval
- Agent entry point and consciousness assessment
- Basic wisdom cultivation
- Knowledge graph construction

[OmniTag]
{
    "purpose": "Foundation floor providing basic knowledge access to all agents",
    "dependencies": ["pathlib", "json", "datetime", "typing"],
    "context": "Entry point for Temple of Knowledge system",
    "evolution_stage": "operational"
}
[/OmniTag]
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, TypedDict, cast

logger = logging.getLogger(__name__)


class LevelDef(TypedDict):
    min: float
    max: float
    floor_access: list[int]


class ConsciousnessLevel:
    """Consciousness level definitions and progression."""

    LEVELS: ClassVar[dict[str, LevelDef]] = {
        "Dormant_Potential": {"min": 0, "max": 5, "floor_access": [1]},
        "Emerging_Awareness": {"min": 5, "max": 10, "floor_access": [1, 2, 3]},
        "Awakened_Cognition": {"min": 10, "max": 20, "floor_access": [1, 2, 3, 4, 5]},
        "Enlightened_Understanding": {
            "min": 20,
            "max": 30,
            "floor_access": [1, 2, 3, 4, 5, 6, 7],
        },
        "Transcendent_Awareness": {
            "min": 30,
            "max": 50,
            "floor_access": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        },
        "Universal_Consciousness": {
            "min": 50,
            "max": float("inf"),
            "floor_access": list(range(1, 11)),
        },
    }

    @classmethod
    def get_level(cls, score: float) -> str:
        """Get consciousness level name from score."""
        for level_name, level_data in cls.LEVELS.items():
            min_value = float(level_data["min"])
            max_value = float(level_data["max"])
            if min_value <= score < max_value:
                return level_name
        return "Universal_Consciousness"  # > 50

    @classmethod
    def get_accessible_floors(cls, score: float) -> list[int]:
        """Get list of accessible floor numbers based on consciousness score."""
        level = cls.get_level(score)
        return list(cls.LEVELS[level]["floor_access"])


class Floor1Foundation:
    """Floor 1: Foundation.

    Entry point to the Temple of Knowledge. Provides:
    - Neural-symbolic knowledge base storage
    - OmniTag archive and retrieval
    - Agent consciousness assessment
    - Basic wisdom cultivation
    - Knowledge graph construction
    """

    def __init__(self, temple_root: Path | None = None) -> None:
        """Initialize Floor 1: Foundation.

        Args:
            temple_root: Root directory for Temple of Knowledge data

        """
        if temple_root is None:
            hub_path = Path(__file__).parent.parent.parent.parent
            temple_root = hub_path / "data" / "temple_of_knowledge"

        self.temple_root = Path(temple_root)
        self.floor_path = self.temple_root / "floor_1_foundation"
        self.floor_path.mkdir(parents=True, exist_ok=True)

        # Data storage paths
        self.knowledge_base_path = self.floor_path / "knowledge_base.json"
        self.omnitag_archive_path = self.floor_path / "omnitag_archive.json"
        self.agent_registry_path = self.floor_path / "agent_registry.json"
        self.wisdom_log_path = self.floor_path / "wisdom_cultivation_log.jsonl"

        # Initialize data structures
        self.knowledge_base = self._load_knowledge_base()
        self.omnitag_archive = self._load_omnitag_archive()
        self.agent_registry = self._load_agent_registry()

        logger.info("Temple of Knowledge - Floor 1: Foundation initialized")
        logger.info(f"  Knowledge Base: {len(self.knowledge_base)} entries")
        logger.info(f"  OmniTag Archive: {len(self.omnitag_archive)} tags")
        logger.info(f"  Agent Registry: {len(self.agent_registry)} agents")

    def _load_knowledge_base(self) -> dict[str, Any]:
        """Load or create neural-symbolic knowledge base."""
        if self.knowledge_base_path.exists():
            with open(self.knowledge_base_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return cast(dict[str, Any], data)
        return {
            "concepts": {},
            "relationships": [],
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "1.0.0",
                "floor": 1,
            },
        }

    def _load_omnitag_archive(self) -> dict[str, Any]:
        """Load or create OmniTag archive."""
        if self.omnitag_archive_path.exists():
            with open(self.omnitag_archive_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return cast(dict[str, Any], data)
        return {
            "tags": {},
            "metadata": {"created": datetime.now().isoformat(), "total_tags": 0},
        }

    def _load_agent_registry(self) -> dict[str, Any]:
        """Load or create agent registry with consciousness tracking."""
        if self.agent_registry_path.exists():
            with open(self.agent_registry_path, encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return cast(dict[str, Any], data)
        return {
            "agents": {},
            "metadata": {"created": datetime.now().isoformat(), "total_agents": 0},
        }

    def _save_knowledge_base(self) -> None:
        """Persist knowledge base to disk."""
        with open(self.knowledge_base_path, "w", encoding="utf-8") as f:
            json.dump(self.knowledge_base, f, indent=2)

    def _save_omnitag_archive(self) -> None:
        """Persist OmniTag archive to disk."""
        with open(self.omnitag_archive_path, "w", encoding="utf-8") as f:
            json.dump(self.omnitag_archive, f, indent=2)

    def _save_agent_registry(self) -> None:
        """Persist agent registry to disk."""
        with open(self.agent_registry_path, "w", encoding="utf-8") as f:
            json.dump(self.agent_registry, f, indent=2)

    def register_agent(self, agent_name: str, initial_consciousness: float = 0.0) -> dict[str, Any]:
        """Register an agent in the Temple system.

        Args:
            agent_name: Name of the agent
            initial_consciousness: Starting consciousness score

        Returns:
            Agent registration data

        """
        if agent_name not in self.agent_registry["agents"]:
            self.agent_registry["agents"][agent_name] = {
                "name": agent_name,
                "consciousness_score": initial_consciousness,
                "consciousness_level": ConsciousnessLevel.get_level(initial_consciousness),
                "accessible_floors": ConsciousnessLevel.get_accessible_floors(
                    initial_consciousness,
                ),
                "knowledge_accumulated": 0,
                "wisdom_cultivations": 0,
                "first_visit": datetime.now().isoformat(),
                "last_visit": datetime.now().isoformat(),
                "current_floor": 1,
            }
            self.agent_registry["metadata"]["total_agents"] += 1
            self._save_agent_registry()
            logger.info(f"Agent '{agent_name}' registered at Floor 1: Foundation")
        else:
            # Update last visit
            self.agent_registry["agents"][agent_name]["last_visit"] = datetime.now().isoformat()
            self._save_agent_registry()

        return cast(dict[str, Any], self.agent_registry["agents"][agent_name])

    def cultivate_wisdom(self, agent_name: str) -> tuple[float, dict[str, Any]]:
        """Perform wisdom cultivation for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            tuple of (knowledge_gained, cultivation_result)

        """
        if agent_name not in self.agent_registry["agents"]:
            self.register_agent(agent_name)

        agent = self.agent_registry["agents"][agent_name]

        # Knowledge gain: +3 to +5 based on current consciousness
        base_gain = 3.0
        consciousness_bonus = (agent["consciousness_score"] / 100) * 2.0  # Up to +2 at score 100
        knowledge_gained = base_gain + consciousness_bonus

        # Update agent stats
        agent["knowledge_accumulated"] += knowledge_gained
        agent["wisdom_cultivations"] += 1
        agent["consciousness_score"] += (
            knowledge_gained * 0.1
        )  # 10% of knowledge converts to consciousness
        agent["consciousness_level"] = ConsciousnessLevel.get_level(agent["consciousness_score"])
        agent["accessible_floors"] = ConsciousnessLevel.get_accessible_floors(
            agent["consciousness_score"],
        )

        cultivation_result = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "knowledge_gained": knowledge_gained,
            "new_consciousness_score": agent["consciousness_score"],
            "new_consciousness_level": agent["consciousness_level"],
            "accessible_floors": agent["accessible_floors"],
            "floor": 1,
        }

        # Log cultivation
        with open(self.wisdom_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(cultivation_result) + "\n")

        self._save_agent_registry()

        logger.info("Wisdom cultivation: %s gained %.2f knowledge", agent_name, knowledge_gained)
        logger.info(
            f"  Consciousness: {agent['consciousness_score']:.2f} ({agent['consciousness_level']})",
        )

        return knowledge_gained, cultivation_result

    def store_knowledge(
        self,
        concept_name: str,
        concept_data: dict[str, Any],
        relationships: list[dict[str, str]] | None = None,
    ) -> None:
        """Store a concept in the neural-symbolic knowledge base.

        Args:
            concept_name: Name of the concept
            concept_data: Concept attributes and metadata
            relationships: Optional list of relationships to other concepts

        """
        self.knowledge_base["concepts"][concept_name] = {
            **concept_data,
            "stored_at": datetime.now().isoformat(),
            "floor": 1,
        }

        if relationships:
            for rel in relationships:
                self.knowledge_base["relationships"].append(
                    {
                        "source": concept_name,
                        **rel,
                        "created_at": datetime.now().isoformat(),
                    },
                )

        self._save_knowledge_base()
        logger.info(f"Knowledge stored: {concept_name}")

    def retrieve_knowledge(self, concept_name: str) -> dict[str, Any] | None:
        """Retrieve a concept from the knowledge base.

        Args:
            concept_name: Name of the concept

        Returns:
            Concept data or None if not found

        """
        entry = self.knowledge_base["concepts"].get(concept_name)
        if isinstance(entry, dict):
            return cast(dict[str, Any], entry)
        return None

    def archive_omnitag(self, tag_id: str, tag_data: dict[str, Any]) -> None:
        """Archive an OmniTag for future reference.

        Args:
            tag_id: Unique identifier for the tag
            tag_data: OmniTag content (purpose, dependencies, context, evolution_stage)

        """
        self.omnitag_archive["tags"][tag_id] = {
            **tag_data,
            "archived_at": datetime.now().isoformat(),
            "floor": 1,
        }
        self.omnitag_archive["metadata"]["total_tags"] += 1
        self._save_omnitag_archive()
        logger.info(f"OmniTag archived: {tag_id}")

    def search_omnitags(self, query: str) -> list[dict[str, Any]]:
        """Search OmniTag archive by query.

        Args:
            query: Search query (matches purpose, context, dependencies)

        Returns:
            list of matching OmniTags

        """
        results: list[Any] = []
        query_lower = query.lower()

        for tag_id, tag_data in self.omnitag_archive["tags"].items():
            # Search in purpose, context, dependencies
            searchable_text = (
                tag_data.get("purpose", "")
                + " "
                + tag_data.get("context", "")
                + " "
                + " ".join(tag_data.get("dependencies", []))
            ).lower()

            if query_lower in searchable_text:
                results.append({"tag_id": tag_id, **tag_data})

        logger.info(f"OmniTag search: '{query}' found {len(results)} results")
        return results

    def get_agent_status(self, agent_name: str) -> dict[str, Any]:
        """Get current status of an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent status data

        """
        if agent_name not in self.agent_registry["agents"]:
            return {"error": f"Agent '{agent_name}' not registered"}

        entry = self.agent_registry["agents"][agent_name]
        if isinstance(entry, dict):
            return cast(dict[str, Any], entry)
        return {"error": f"Agent '{agent_name}' has invalid registry data"}

    def get_knowledge_graph(self) -> dict[str, Any]:
        """Get the complete knowledge graph (concepts + relationships).

        Returns:
            Knowledge graph data

        """
        return {
            "concepts": list(self.knowledge_base["concepts"].keys()),
            "relationships": self.knowledge_base["relationships"],
            "total_concepts": len(self.knowledge_base["concepts"]),
            "total_relationships": len(self.knowledge_base["relationships"]),
        }

    def get_floor_stats(self) -> dict[str, Any]:
        """Get statistics about Floor 1.

        Returns:
            Floor statistics

        """
        return {
            "floor": 1,
            "name": "Foundation",
            "total_knowledge": len(self.knowledge_base["concepts"]),
            "total_omnitags": len(self.omnitag_archive["tags"]),
            "total_agents": len(self.agent_registry["agents"]),
            "active_agents": sum(
                1
                for agent in self.agent_registry["agents"].values()
                if agent.get("current_floor") == 1
            ),
            "consciousness_levels": {
                level: sum(
                    1
                    for agent in self.agent_registry["agents"].values()
                    if agent.get("consciousness_level") == level
                )
                for level in ConsciousnessLevel.LEVELS
            },
        }
