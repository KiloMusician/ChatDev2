"""OmniTag: {.

    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Memory"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""


class SemanticClusters:
    """Class to organize memory nodes into semantic clusters for better retrieval."""

    def __init__(self) -> None:
        """Initialize SemanticClusters."""
        self.clusters: dict[str, list[str]] = {}

    def add_memory_node(self, node_id: str, tags: list[str]) -> None:
        """Add a memory node to the appropriate semantic clusters based on its tags."""
        for tag in tags:
            if tag not in self.clusters:
                self.clusters[tag] = []
            self.clusters[tag].append(node_id)

    def get_cluster(self, tag: str) -> list[str]:
        """Retrieve memory nodes associated with a specific tag."""
        return self.clusters.get(tag, [])

    def remove_memory_node(self, node_id: str, tags: list[str]) -> None:
        """Remove a memory node from its associated semantic clusters."""
        for tag in tags:
            if tag in self.clusters and node_id in self.clusters[tag]:
                self.clusters[tag].remove(node_id)

    def clear_clusters(self) -> None:
        """Clear all semantic clusters."""
        self.clusters.clear()

    def get_all_clusters(self) -> dict[str, list[str]]:
        """Retrieve all semantic clusters."""
        return self.clusters

    def __repr__(self) -> str:
        """String representation of the semantic clusters."""
        return f"SemanticClusters(clusters={self.clusters})"
