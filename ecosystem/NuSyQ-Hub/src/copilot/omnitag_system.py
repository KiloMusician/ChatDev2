"""KILO-FOOLISH OmniTag System.

Comprehensive tagging and semantic annotation system.

OmniTag: {
    "purpose": "Quantum-inspired semantic tagging system for KILO-FOOLISH",
    "dependencies": ["pathlib", "json", "datetime"],
    "context": "Tagging infrastructure for system consciousness",
    "evolution_stage": "v4.0"
}
MegaTag: {
    "type": "TaggingSystem",
    "integration_points": ["enhanced_bridge", "consciousness", "memory"],
    "related_tags": ["SemanticTagging", "QuantumAnnotation", "SystemConsciousness"]
}
RSHTS: ΞΨΩ∞⟨OMNITAG⟩→ΦΣΣ⟨SEMANTIC⟩
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class OmniTag:
    """Enhanced semantic tag with quantum-inspired properties."""

    def __init__(
        self,
        purpose: str,
        dependencies: list[str] | None = None,
        context: str = "",
        evolution_stage: str = "v1.0",
        timestamp: str | None = None,
        tag_id: str | None = None,
    ) -> None:
        """Initialize OmniTag with purpose, dependencies, context, ...."""
        self.purpose = purpose
        self.dependencies = dependencies or []
        self.context = context
        self.evolution_stage = evolution_stage
        self.timestamp = timestamp or datetime.now().isoformat()
        self.tag_id = tag_id or str(uuid.uuid4())

        # Quantum-inspired properties
        self.resonance_frequency = self._calculate_resonance()
        self.semantic_weight = self._calculate_semantic_weight()
        self.context_binding = self._generate_context_binding()

    def _calculate_resonance(self) -> float:
        """Calculate quantum resonance frequency for tag."""
        # Simple hash-based calculation for reproducible resonance
        hash_value = hash(f"{self.purpose}{self.context}")
        return (hash_value % 1000) / 1000.0

    def _calculate_semantic_weight(self) -> float:
        """Calculate semantic weight based on complexity."""
        base_weight = len(self.purpose) * 0.1
        dependency_weight = len(self.dependencies) * 0.2
        context_weight = len(self.context) * 0.05
        return min(base_weight + dependency_weight + context_weight, 10.0)

    def _generate_context_binding(self) -> str:
        """Generate context binding hash."""
        binding_data = f"{self.purpose}:{self.context}:{','.join(self.dependencies)}"
        return str(hash(binding_data))

    def to_dict(self) -> dict[str, Any]:
        """Convert OmniTag to dictionary."""
        return {
            "tag_id": self.tag_id,
            "purpose": self.purpose,
            "dependencies": self.dependencies,
            "context": self.context,
            "evolution_stage": self.evolution_stage,
            "timestamp": self.timestamp,
            "resonance_frequency": self.resonance_frequency,
            "semantic_weight": self.semantic_weight,
            "context_binding": self.context_binding,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OmniTag":
        """Create OmniTag from dictionary."""
        return cls(
            purpose=data["purpose"],
            dependencies=data.get("dependencies", []),
            context=data.get("context", ""),
            evolution_stage=data.get("evolution_stage", "v1.0"),
            timestamp=data.get("timestamp"),
            tag_id=data.get("tag_id"),
        )


class OmniTagSystem:
    """Comprehensive OmniTag management system."""

    def __init__(self, storage_dir: str = "data/tags") -> None:
        """Initialize OmniTagSystem with storage_dir."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.tags: dict[str, OmniTag] = {}
        self.tag_index: dict[str, list[str]] = {}  # purpose -> tag_ids
        self.dependency_graph: dict[str, list[str]] = {}

        self.load_existing_tags()

    def create_omni_tag(self, tag_data: dict[str, Any]) -> OmniTag:
        """Create and store new OmniTag."""
        # Extract data with defaults
        purpose = tag_data.get("purpose", "")
        dependencies = tag_data.get("dependencies", [])
        context = tag_data.get("context", "")
        evolution_stage = tag_data.get("evolution_stage", "v1.0")

        # Create tag
        tag = OmniTag(
            purpose=purpose,
            dependencies=dependencies,
            context=context,
            evolution_stage=evolution_stage,
        )

        # Store tag
        self.tags[tag.tag_id] = tag

        # Update index
        if purpose not in self.tag_index:
            self.tag_index[purpose] = []
        self.tag_index[purpose].append(tag.tag_id)

        # Update dependency graph
        self._update_dependency_graph(tag)

        # Persist to storage
        self.save_tag(tag)

        return tag

    def get_tag(self, tag_id: str) -> OmniTag | None:
        """Retrieve tag by ID."""
        return self.tags.get(tag_id)

    def find_tags_by_purpose(self, purpose: str) -> list[OmniTag]:
        """Find tags by purpose."""
        tag_ids = self.tag_index.get(purpose, [])
        return [self.tags[tag_id] for tag_id in tag_ids if tag_id in self.tags]

    def find_tags_by_dependency(self, dependency: str) -> list[OmniTag]:
        """Find tags that depend on a specific item."""
        results: list[Any] = []
        for tag in self.tags.values():
            if dependency in tag.dependencies:
                results.append(tag)
        return results

    def get_related_tags(self, tag_id: str, max_depth: int = 2) -> list[OmniTag]:
        """Get tags related through dependency graph."""
        if tag_id not in self.tags:
            return []

        related = set()
        to_explore = [tag_id]
        explored = set()
        depth = 0

        while to_explore and depth < max_depth:
            current_level = to_explore.copy()
            to_explore.clear()
            depth += 1

            for current_id in current_level:
                if current_id in explored:
                    continue
                explored.add(current_id)

                current_tag = self.tags.get(current_id)
                if not current_tag:
                    continue

                # Find tags that depend on this tag's purpose
                dependent_tags = self.find_tags_by_dependency(current_tag.purpose)
                for dep_tag in dependent_tags:
                    if dep_tag.tag_id not in explored:
                        related.add(dep_tag.tag_id)
                        to_explore.append(dep_tag.tag_id)

                # Find tags this tag depends on
                for dependency in current_tag.dependencies:
                    dependency_tags = self.find_tags_by_purpose(dependency)
                    for dep_tag in dependency_tags:
                        if dep_tag.tag_id not in explored:
                            related.add(dep_tag.tag_id)
                            to_explore.append(dep_tag.tag_id)

        return [self.tags[rid] for rid in related if rid in self.tags]

    def _update_dependency_graph(self, tag: OmniTag) -> None:
        """Update dependency graph with new tag."""
        if tag.tag_id not in self.dependency_graph:
            self.dependency_graph[tag.tag_id] = []

        # Add dependencies
        for dependency in tag.dependencies:
            if dependency not in self.dependency_graph:
                self.dependency_graph[dependency] = []
            self.dependency_graph[dependency].append(tag.tag_id)

    def save_tag(self, tag: OmniTag) -> None:
        """Save tag to persistent storage."""
        try:
            tag_file = self.storage_dir / f"{tag.tag_id}.json"
            with open(tag_file, "w", encoding="utf-8") as f:
                json.dump(tag.to_dict(), f, indent=2, ensure_ascii=False)
        except (OSError, PermissionError, TypeError):
            logger.debug("Suppressed OSError/PermissionError/TypeError", exc_info=True)

    def load_existing_tags(self) -> None:
        """Load existing tags from storage."""
        if not self.storage_dir.exists():
            return

        try:
            for tag_file in self.storage_dir.glob("*.json"):
                try:
                    with open(tag_file, encoding="utf-8") as f:
                        tag_data = json.load(f)

                    tag = OmniTag.from_dict(tag_data)
                    self.tags[tag.tag_id] = tag

                    # Update index
                    if tag.purpose not in self.tag_index:
                        self.tag_index[tag.purpose] = []
                    self.tag_index[tag.purpose].append(tag.tag_id)

                    # Update dependency graph
                    self._update_dependency_graph(tag)

                except (json.JSONDecodeError, KeyError, ValueError):
                    logger.debug("Suppressed KeyError/ValueError/json", exc_info=True)
        except (OSError, FileNotFoundError, AttributeError):
            logger.debug("Suppressed AttributeError/FileNotFoundError/OSError", exc_info=True)

    def export_tags(self, file_path: str | None = None) -> str:
        """Export all tags to a single file."""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"data/exports/omnitags_export_{timestamp}.json"

        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_tags": len(self.tags),
                "tags": [tag.to_dict() for tag in self.tags.values()],
                "tag_index": self.tag_index,
                "dependency_graph": self.dependency_graph,
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return file_path
        except Exception as e:
            return f"Export failed: {e}"

    def get_statistics(self) -> dict[str, Any]:
        """Get system statistics."""
        purpose_counts: dict[str, Any] = {}
        for purpose, tag_ids in self.tag_index.items():
            purpose_counts[purpose] = len(tag_ids)

        evolution_stages: dict[str, Any] = {}
        for tag in self.tags.values():
            stage = tag.evolution_stage
            evolution_stages[stage] = evolution_stages.get(stage, 0) + 1

        return {
            "total_tags": len(self.tags),
            "unique_purposes": len(self.tag_index),
            "purpose_distribution": purpose_counts,
            "evolution_stages": evolution_stages,
            "dependency_nodes": len(self.dependency_graph),
            "average_semantic_weight": sum(tag.semantic_weight for tag in self.tags.values())
            / max(len(self.tags), 1),
            "system_timestamp": datetime.now().isoformat(),
        }


# Example usage and testing
if __name__ == "__main__":
    # Create OmniTag system
    system = OmniTagSystem()

    # Create test tags
    test_tags = [
        {
            "purpose": "enhanced_bridge_integration",
            "dependencies": ["pathlib", "json", "omnitag_system"],
            "context": "Bridge integration for KILO-FOOLISH consciousness",
            "evolution_stage": "v2.0",
        },
        {
            "purpose": "semantic_reasoning",
            "dependencies": ["enhanced_bridge_integration", "symbolic_cognition"],
            "context": "Advanced reasoning capabilities",
            "evolution_stage": "v3.0",
        },
        {
            "purpose": "quantum_context_compression",
            "dependencies": ["semantic_reasoning", "zeta_lexeme_generation"],
            "context": "Context compression for LLM optimization",
            "evolution_stage": "v4.0",
        },
    ]

    # Create and display tags
    created_tags: list[Any] = []
    for tag_data in test_tags:
        tag = system.create_omni_tag(tag_data)
        created_tags.append(tag)

    # Display statistics
    stats = system.get_statistics()

    # Test relationships
    if created_tags:
        first_tag = created_tags[0]
        related = system.get_related_tags(first_tag.tag_id)
        for _rel_tag in related:
            pass
