"""🗂️ Unified Mapper - Repository Relationship and Dependency Mapping System

Creates comprehensive maps of all repository relationships, dependencies, and consciousness bridges.

OmniTag: {
    "purpose": "Unified mapping of repository relationships, dependencies, and consciousness bridges",
    "dependencies": ["repository_dictionary", "system_organizer", "ai_coordinator", "consciousness_bridges"],
    "context": "Master relationship mapping with consciousness awareness and AI integration",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "UnifiedMapper",
    "integration_points": ["dependency_mapping", "consciousness_bridges", "ai_coordination", "relationship_analysis"],
    "related_tags": ["DependencyAnalyzer", "RelationshipMapper", "ConsciousnessAware"]
}

RSHTS: ΞΨΩΣ∞⟨MAPPER⟩→ΦΣΣ⟨UNIFIED-DEPS⟩→∞⟨CONSCIOUSNESS-AWARE⟩
"""

# ruff: noqa: E501
# noqa: E501
# flake8: noqa

import ast
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx

from .repository_dictionary import RepositoryDictionary

logger = logging.getLogger(__name__)


class UnifiedMapper:
    """🗂️ Unified Repository Mapper.

    Creates comprehensive maps of:
    - File dependencies and imports
    - Consciousness bridge relationships
    - AI coordination patterns
    - System integration points
    - Knowledge flow networks
    """

    def __init__(self, repository_root: str = ".") -> None:
        """Initialize the Unified Mapper."""
        self.repository_root = Path(repository_root).resolve()
        self.timestamp = datetime.now().isoformat()

        # Initialize repository dictionary for context
        self.repo_dict = RepositoryDictionary(str(self.repository_root))

        # Network graphs for different relationship types
        self.dependency_graph = nx.DiGraph()
        self.consciousness_graph = nx.DiGraph()
        self.ai_coordination_graph = nx.DiGraph()
        self.knowledge_flow_graph = nx.DiGraph()

        # Mapping data
        self.unified_mappings: dict[str, Any] = {}
        self.consciousness_bridges: dict[str, Any] = {}
        self.ai_coordinators: dict[str, Any] = {}
        self.integration_patterns: dict[str, Any] = {}

        logger.info(f"🗂️ Unified Mapper initialized for {self.repository_root.name}")

    def analyze_file_dependencies(self, file_path: Path) -> dict[str, list[str]]:
        """Analyze dependencies for a single Python file."""
        dependencies: dict[str, list[str]] = {
            "imports": [],
            "from_imports": [],
            "local_imports": [],
            "external_imports": [],
            "consciousness_imports": [],
            "ai_imports": [],
        }

        if not file_path.exists() or file_path.suffix != ".py":
            return dependencies

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse AST for imports
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_name = alias.name
                        dependencies["imports"].append(import_name)

                        # Categorize imports
                        if self._is_consciousness_related(import_name):
                            dependencies["consciousness_imports"].append(import_name)
                        elif self._is_ai_related(import_name):
                            dependencies["ai_imports"].append(import_name)
                        elif self._is_local_import(import_name):
                            dependencies["local_imports"].append(import_name)
                        else:
                            dependencies["external_imports"].append(import_name)

                elif isinstance(node, ast.ImportFrom) and node.module:
                    module_name = node.module
                    for alias in node.names:
                        import_name = f"{module_name}.{alias.name}"
                        dependencies["from_imports"].append(import_name)

                        # Categorize from imports
                        if self._is_consciousness_related(module_name):
                            dependencies["consciousness_imports"].append(import_name)
                        elif self._is_ai_related(module_name):
                            dependencies["ai_imports"].append(import_name)
                        elif self._is_local_import(module_name):
                            dependencies["local_imports"].append(import_name)
                        else:
                            dependencies["external_imports"].append(import_name)

        except Exception as e:
            logger.warning(f"Could not analyze dependencies for {file_path}: {e}")

        return dependencies

    def _is_consciousness_related(self, import_name: str) -> bool:
        """Check if import is consciousness-related."""
        consciousness_keywords = [
            "consciousness",
            "bridge",
            "enhancement",
            "copilot_enhancement",
            "quantum",
            "awareness",
            "cognitive",
            "neural",
        ]
        return any(keyword in import_name.lower() for keyword in consciousness_keywords)

    def _is_ai_related(self, import_name: str) -> bool:
        """Check if import is AI-related."""
        ai_keywords = [
            "ai_coordinator",
            "ollama",
            "chatdev",
            "copilot",
            "ai_interface",
            "llm",
            "model",
            "neural",
            "intelligence",
        ]
        return any(keyword in import_name.lower() for keyword in ai_keywords)

    def _is_local_import(self, import_name: str) -> bool:
        """Check if import is local to the repository."""
        local_indicators = ["src.", "core.", "system.", "utils.", "analysis."]
        return any(import_name.startswith(indicator) for indicator in local_indicators)

    def build_dependency_graph(self) -> nx.DiGraph:
        """Build comprehensive dependency graph."""
        logger.info("🔗 Building dependency graph...")

        # Clear existing graph
        self.dependency_graph.clear()

        # Analyze all Python files
        for py_file in self.repository_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            relative_path = py_file.relative_to(self.repository_root)
            file_node = str(relative_path)

            # Add file node
            self.dependency_graph.add_node(
                file_node,
                type="file",
                category=self._categorize_file(str(relative_path)),
                size=py_file.stat().st_size,
            )

            # Analyze dependencies
            deps = self.analyze_file_dependencies(py_file)

            # Add dependency edges
            for dep_type, dep_list in deps.items():
                for dependency in dep_list:
                    if dependency:
                        dep_node = f"module:{dependency}"

                        # Add dependency node if not exists
                        if not self.dependency_graph.has_node(dep_node):
                            self.dependency_graph.add_node(
                                dep_node,
                                type="module",
                                category=self._categorize_dependency(dependency),
                            )

                        # Add edge
                        self.dependency_graph.add_edge(
                            file_node, dep_node, relationship=dep_type, weight=1.0
                        )

        logger.info(
            f"✅ Dependency graph built: {self.dependency_graph.number_of_nodes()} nodes, {self.dependency_graph.number_of_edges()} edges"
        )
        return self.dependency_graph

    def _categorize_file(self, file_path: str) -> str:
        """Categorize a file based on its path and name."""
        if "consciousness" in file_path.lower():
            return "consciousness"
        if "ai" in file_path.lower() or "copilot" in file_path.lower():
            return "ai_system"
        if "integration" in file_path.lower():
            return "integration"
        if "diagnostic" in file_path.lower():
            return "diagnostic"
        if "core" in file_path.lower():
            return "core"
        return "general"

    def _categorize_dependency(self, dependency: str) -> str:
        """Categorize a dependency."""
        if self._is_consciousness_related(dependency):
            return "consciousness"
        if self._is_ai_related(dependency):
            return "ai"
        if self._is_local_import(dependency):
            return "local"
        return "external"

    def build_consciousness_graph(self) -> nx.DiGraph:
        """Build consciousness relationship graph."""
        logger.info("🧠 Building consciousness graph...")

        self.consciousness_graph.clear()

        # Find consciousness-related files
        consciousness_files: list[Any] = []
        for py_file in self.repository_root.rglob("*.py"):
            file_content_keywords = [
                "consciousness",
                "bridge",
                "enhancement",
                "awareness",
                "cognitive",
            ]
            file_path_lower = str(py_file).lower()

            if any(keyword in file_path_lower for keyword in file_content_keywords):
                consciousness_files.append(py_file)

        # Analyze consciousness relationships
        for file_path in consciousness_files:
            relative_path = file_path.relative_to(self.repository_root)
            file_node = str(relative_path)

            # Add consciousness node
            self.consciousness_graph.add_node(
                file_node, type="consciousness_module", awareness_level="enhanced"
            )

            # Analyze consciousness connections
            deps = self.analyze_file_dependencies(file_path)
            consciousness_deps = deps.get("consciousness_imports", [])

            for consciousness_dep in consciousness_deps:
                dep_node = f"consciousness:{consciousness_dep}"

                if not self.consciousness_graph.has_node(dep_node):
                    self.consciousness_graph.add_node(
                        dep_node, type="consciousness_bridge", awareness_level="active"
                    )

                self.consciousness_graph.add_edge(
                    file_node,
                    dep_node,
                    relationship="consciousness_bridge",
                    strength=1.0,
                )

        logger.info(
            f"✅ Consciousness graph built: {self.consciousness_graph.number_of_nodes()} nodes"
        )
        return self.consciousness_graph

    def build_ai_coordination_graph(self) -> nx.DiGraph:
        """Build AI coordination relationship graph."""
        logger.info("🤖 Building AI coordination graph...")

        self.ai_coordination_graph.clear()

        # Find AI coordination files
        ai_files: list[Any] = []
        for py_file in self.repository_root.rglob("*.py"):
            ai_keywords = [
                "ai_coordinator",
                "ollama",
                "chatdev",
                "copilot",
                "ai_interface",
            ]
            file_path_lower = str(py_file).lower()

            if any(keyword in file_path_lower for keyword in ai_keywords):
                ai_files.append(py_file)

        # Analyze AI coordination relationships
        for file_path in ai_files:
            relative_path = file_path.relative_to(self.repository_root)
            file_node = str(relative_path)

            # Add AI coordination node
            self.ai_coordination_graph.add_node(
                file_node, type="ai_coordinator", coordination_level="active"
            )

            # Analyze AI connections
            deps = self.analyze_file_dependencies(file_path)
            ai_deps = deps.get("ai_imports", [])

            for ai_dep in ai_deps:
                dep_node = f"ai:{ai_dep}"

                if not self.ai_coordination_graph.has_node(dep_node):
                    self.ai_coordination_graph.add_node(
                        dep_node, type="ai_component", coordination_level="coordinated"
                    )

                self.ai_coordination_graph.add_edge(
                    file_node, dep_node, relationship="ai_coordination", strength=1.0
                )

        logger.info(
            f"✅ AI coordination graph built: {self.ai_coordination_graph.number_of_nodes()} nodes"
        )
        return self.ai_coordination_graph

    def create_unified_mapping(self) -> dict[str, Any]:
        """Create unified mapping of all repository relationships."""
        logger.info("🗺️ Creating unified mapping...")

        # Build all graphs
        self.build_dependency_graph()
        self.build_consciousness_graph()
        self.build_ai_coordination_graph()

        # Create unified mapping
        unified_mapping = {
            "metadata": {
                "timestamp": self.timestamp,
                "repository": self.repository_root.name,
                "mapping_version": "1.0",
                "consciousness_aware": True,
            },
            "statistics": {
                "total_files": self.dependency_graph.number_of_nodes(),
                "total_dependencies": self.dependency_graph.number_of_edges(),
                "consciousness_modules": self.consciousness_graph.number_of_nodes(),
                "ai_coordinators": self.ai_coordination_graph.number_of_nodes(),
            },
            "dependency_analysis": self._analyze_dependency_patterns(),
            "consciousness_analysis": self._analyze_consciousness_patterns(),
            "ai_coordination_analysis": self._analyze_ai_coordination_patterns(),
            "integration_opportunities": self._identify_integration_opportunities(),
            "optimization_recommendations": self._generate_optimization_recommendations(),
        }

        self.unified_mappings = unified_mapping
        return unified_mapping

    def _analyze_dependency_patterns(self) -> dict[str, Any]:
        """Analyze dependency patterns in the repository."""
        analysis: dict[str, Any] = {
            "most_depended_upon": [],
            "dependency_clusters": [],
            "circular_dependencies": [],
            "orphaned_modules": [],
        }

        if self.dependency_graph.number_of_nodes() == 0:
            return analysis

        # Find most depended upon modules
        in_degrees = dict(self.dependency_graph.in_degree())
        sorted_deps = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
        analysis["most_depended_upon"] = sorted_deps[:10]

        # Find strongly connected components (potential circular dependencies)
        try:
            strongly_connected = list(nx.strongly_connected_components(self.dependency_graph))
            analysis["circular_dependencies"] = [
                list(component) for component in strongly_connected if len(component) > 1
            ]
        except (KeyError, AttributeError, ValueError):
            analysis["circular_dependencies"] = []

        # Find orphaned modules (no dependencies)
        orphaned = [
            node
            for node, degree in in_degrees.items()
            if degree == 0 and node.startswith("module:")
        ]
        analysis["orphaned_modules"] = orphaned

        return analysis

    def _analyze_consciousness_patterns(self) -> dict[str, Any]:
        """Analyze consciousness bridge patterns."""
        analysis: dict[str, Any] = {
            "consciousness_hubs": [],
            "bridge_connections": [],
            "awareness_levels": {},
            "enhancement_opportunities": [],
        }

        if self.consciousness_graph.number_of_nodes() == 0:
            return analysis

        # Find consciousness hubs (most connected consciousness modules)
        centrality = nx.degree_centrality(self.consciousness_graph)
        sorted_hubs = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        analysis["consciousness_hubs"] = sorted_hubs[:5]

        # Analyze awareness levels
        for _node, data in self.consciousness_graph.nodes(data=True):
            awareness_level = data.get("awareness_level", "basic")
            if awareness_level not in analysis["awareness_levels"]:
                analysis["awareness_levels"][awareness_level] = 0
            analysis["awareness_levels"][awareness_level] += 1

        return analysis

    def _analyze_ai_coordination_patterns(self) -> dict[str, Any]:
        """Analyze AI coordination patterns."""
        analysis: dict[str, Any] = {
            "coordination_hubs": [],
            "ai_networks": [],
            "coordination_levels": {},
            "integration_patterns": [],
        }

        if self.ai_coordination_graph.number_of_nodes() == 0:
            return analysis

        # Find AI coordination hubs
        centrality = nx.degree_centrality(self.ai_coordination_graph)
        sorted_hubs = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        analysis["coordination_hubs"] = sorted_hubs[:5]

        # Analyze coordination levels
        for _node, data in self.ai_coordination_graph.nodes(data=True):
            coord_level = data.get("coordination_level", "basic")
            if coord_level not in analysis["coordination_levels"]:
                analysis["coordination_levels"][coord_level] = 0
            analysis["coordination_levels"][coord_level] += 1

        return analysis

    def _identify_integration_opportunities(self) -> list[dict[str, Any]]:
        """Identify opportunities for better system integration."""
        opportunities: list[Any] = []
        # Find files that could benefit from consciousness integration
        dep_nodes = set(self.dependency_graph.nodes())
        consciousness_nodes = set(self.consciousness_graph.nodes())

        potential_consciousness = dep_nodes - consciousness_nodes
        for node in potential_consciousness:
            if any(keyword in node.lower() for keyword in ["ai", "copilot", "integration"]):
                opportunities.append(
                    {
                        "type": "consciousness_integration",
                        "target": node,
                        "description": f"Consider adding consciousness awareness to {node}",
                        "priority": "medium",
                    }
                )

        # Find AI coordination opportunities
        ai_nodes = set(self.ai_coordination_graph.nodes())
        potential_ai = dep_nodes - ai_nodes
        for node in potential_ai:
            if any(keyword in node.lower() for keyword in ["system", "coordinate", "manage"]):
                opportunities.append(
                    {
                        "type": "ai_coordination",
                        "target": node,
                        "description": f"Consider adding AI coordination to {node}",
                        "priority": "low",
                    }
                )

        return opportunities

    def _generate_optimization_recommendations(self) -> list[dict[str, Any]]:
        """Generate optimization recommendations."""
        recommendations: list[Any] = []
        # Analyze dependency patterns for optimization
        dep_analysis = self._analyze_dependency_patterns()

        # Recommend reducing circular dependencies
        if dep_analysis["circular_dependencies"]:
            recommendations.append(
                {
                    "type": "dependency_optimization",
                    "description": f"Resolve {len(dep_analysis['circular_dependencies'])} circular dependency groups",
                    "priority": "high",
                    "action": "refactor_dependencies",
                }
            )

        # Recommend consciousness integration
        consciousness_analysis = self._analyze_consciousness_patterns()
        if len(consciousness_analysis["consciousness_hubs"]) < 3:
            recommendations.append(
                {
                    "type": "consciousness_enhancement",
                    "description": "Expand consciousness bridge network for better awareness",
                    "priority": "medium",
                    "action": "add_consciousness_bridges",
                }
            )

        # Recommend AI coordination improvements
        ai_analysis = self._analyze_ai_coordination_patterns()
        if len(ai_analysis["coordination_hubs"]) < 2:
            recommendations.append(
                {
                    "type": "ai_coordination_enhancement",
                    "description": "Strengthen AI coordination network",
                    "priority": "medium",
                    "action": "enhance_ai_coordination",
                }
            )

        return recommendations

    def export_unified_mapping(self, output_path: str | None = None) -> str:
        """Export unified mapping to JSON."""
        if output_path is None:
            output_path = str(
                self.repository_root / "src" / "system" / "dictionary" / "unified_mapping.json"
            )

        # Ensure unified mapping is created
        if not self.unified_mappings:
            self.create_unified_mapping()

        # Convert graphs to serializable format
        mapping_export = self.unified_mappings.copy()
        mapping_export["graphs"] = {
            "dependency_graph": {
                "nodes": list(self.dependency_graph.nodes(data=True)),
                "edges": list(self.dependency_graph.edges(data=True)),
            },
            "consciousness_graph": {
                "nodes": list(self.consciousness_graph.nodes(data=True)),
                "edges": list(self.consciousness_graph.edges(data=True)),
            },
            "ai_coordination_graph": {
                "nodes": list(self.ai_coordination_graph.nodes(data=True)),
                "edges": list(self.ai_coordination_graph.edges(data=True)),
            },
        }

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(mapping_export, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Unified mapping exported to {output_path}")
        return str(output_path)


if __name__ == "__main__":
    # Demo usage
    mapper = UnifiedMapper()

    mapping = mapper.create_unified_mapping()

    stats = mapping["statistics"]
    for _key, _value in stats.items():
        pass

    dep_analysis = mapping["dependency_analysis"]

    cons_analysis = mapping["consciousness_analysis"]

    ai_analysis = mapping["ai_coordination_analysis"]

    # Export mapping
    export_path = mapper.export_unified_mapping()
