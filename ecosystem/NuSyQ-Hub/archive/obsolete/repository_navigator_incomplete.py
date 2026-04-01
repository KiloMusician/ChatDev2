#!/usr/bin/env python3
"""🗺️ KILO-FOOLISH Repository Navigation & Context Map
Enhanced repository navigation with context retention and dependency visualization.

OmniTag: {
    "purpose": "Repository navigation with contextual awareness and dependency mapping",
    "dependencies": ["REPOSITORY_ARCHITECTURE_CODEX.yaml", "KILO_COMPONENT_INDEX.json", "quest_engine"],
    "context": "Navigation system integrating all KILO-FOOLISH infrastructure",
    "evolution_stage": "v4.0"
}
MegaTag: {
    "type": "NavigationFramework",
    "integration_points": ["architecture_codex", "component_index", "consciousness", "quest_system"],
    "related_tags": ["SystemNavigation", "ContextAwareness", "DependencyMapping"]
}
RSHTS: ΞΨΩ∞⟨NAVIGATION⟩→ΦΣΣ⟨CONTEXT-MAP⟩→∞
"""

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="🗺️ [%(asctime)s] NAVIGATION: %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class ComponentType(Enum):
    CORE = "core"
    AI = "ai"
    INFRASTRUCTURE = "infrastructure"
    DOCUMENTATION = "documentation"
    QUEST = "quest"
    QUANTUM = "quantum"
    CONSCIOUSNESS = "consciousness"


class OperationType(Enum):
    ACTIVE = "active"  # Requires user interaction or triggers actions
    PASSIVE = "passive"  # Informational or background operations
    HYBRID = "hybrid"  # Can be both active and passive


@dataclass
class SystemComponent:
    """Individual system component with context and dependencies."""

    id: str
    name: str
    path: Path
    component_type: ComponentType
    operation_type: OperationType
    description: str
    dependencies: list[str] = field(default_factory=list)
    provides_to: list[str] = field(default_factory=list)
    context: str | None = None
    priority: int = 3  # 1=critical, 5=optional
    status: str = "unknown"
    integration_points: list[str] = field(default_factory=list)
    evolution_stage: str = "v1.0"


@dataclass
class NavigationPath:
    """Navigation path between components."""

    from_component: str
    to_component: str
    relationship_type: str  # depends_on, provides_to, integrates_with
    description: str
    complexity: int = 1  # 1=simple, 5=complex


class RepositoryNavigator:
    """Enhanced repository navigation system with contextual awareness."""

    def __init__(self) -> None:
        self.base_path = Path(__file__).parent.parent.parent
        self.components: dict[str, SystemComponent] = {}
        self.navigation_paths: list[NavigationPath] = []
        self.context_cache: dict[str, Any] = {}

        # Load system data
        self._load_architecture_codex()
        self._load_component_index()
        self._build_dependency_graph()

        logger.info("🗺️ Repository Navigator initialized")

    def _load_architecture_codex(self) -> None:
        """Load architecture codex for system understanding."""
        codex_path = self.base_path / "REPOSITORY_ARCHITECTURE_CODEX.yaml"

        try:
            with open(codex_path, encoding="utf-8") as f:
                codex_data = yaml.safe_load(f)

            # Extract core source architecture
            if "core_source_architecture" in codex_data:
                directories = codex_data["core_source_architecture"]["directories"]

                for dir_name, dir_info in directories.items():
                    if isinstance(dir_info, dict) and "path" in dir_info:
                        component = SystemComponent(
                            id=dir_name,
                            name=dir_info.get("purpose", dir_name),
                            path=Path(dir_info["path"]),
                            component_type=self._infer_component_type(dir_name),
                            operation_type=self._infer_operation_type(dir_info),
                            description=dir_info.get("function", "System component"),
                            context=dir_info.get("context", None),
                            evolution_stage=dir_info.get("evolution_stage", "v1.0"),
                        )

                        # Extract relationships
                        if "relationships" in dir_info:
                            relationships = dir_info["relationships"]
                            component.dependencies = relationships.get("depends_on", [])
                            component.provides_to = relationships.get("provides_to", [])
                            component.integration_points = relationships.get("integrates_with", [])

                        self.components[dir_name] = component

            logger.info(f"📚 Loaded {len(self.components)} components from architecture codex")

        except FileNotFoundError:
            logger.warning("📚 Architecture codex not found, using minimal component set")
        except Exception as e:
            logger.exception(f"❌ Error loading architecture codex: {e}")

    def _load_component_index(self) -> None:
        """Load component index for detailed system information."""
        index_path = self.base_path / "config" / "KILO_COMPONENT_INDEX.json"

        try:
            with open(index_path, encoding="utf-8") as f:
                index_data = json.load(f)

            # Update components with index information
            for component_info in index_data.values():
                if isinstance(component_info, dict) and "path" in component_info:
                    path_parts = Path(component_info["path"]).parts
                    if len(path_parts) >= 2:
                        dir_name = path_parts[1]  # src/ai -> ai

                        if dir_name in self.components:
                            # Update existing component with index info
                            self.components[dir_name].status = "indexed"

            logger.info("🔍 Enhanced components with index information")

        except FileNotFoundError:
            logger.warning("🔍 Component index not found")
        except Exception as e:
            logger.exception(f"❌ Error loading component index: {e}")

    def _infer_component_type(self, dir_name: str) -> ComponentType:
        """Infer component type from directory name."""
        type_mapping = {
            "ai": ComponentType.AI,
            "core": ComponentType.CORE,
            "consciousness": ComponentType.CONSCIOUSNESS,
            "quantum": ComponentType.QUANTUM,
            "Rosetta_Quest_System": ComponentType.QUEST,
            "orchestration": ComponentType.INFRASTRUCTURE,
            "integration": ComponentType.INFRASTRUCTURE,
            "tools": ComponentType.INFRASTRUCTURE,
            "utils": ComponentType.INFRASTRUCTURE,
            "docs": ComponentType.DOCUMENTATION,
        }
        return type_mapping.get(dir_name, ComponentType.INFRASTRUCTURE)

    def _infer_operation_type(self, dir_info: dict) -> OperationType:
        """Infer operation type from directory information."""
        description = dir_info.get("description", "").lower()
        function = dir_info.get("function", "").lower()
        context = dir_info.get("context", "").lower()

        # Active operation indicators
        active_keywords = [
            "launcher",
            "orchestrator",
            "coordinator",
            "engine",
            "testing",
            "interactive",
        ]
        # Passive operation indicators
        passive_keywords = [
            "storage",
            "documentation",
            "configuration",
            "logging",
            "memory",
        ]

        text_to_check = f"{description} {function} {context}"

        if any(keyword in text_to_check for keyword in active_keywords):
            return OperationType.ACTIVE
        if any(keyword in text_to_check for keyword in passive_keywords):
            return OperationType.PASSIVE
        return OperationType.HYBRID

    def _build_dependency_graph(self) -> None:
        """Build navigation paths based on component dependencies."""
        for component_id, component in self.components.items():
            # Create dependency paths
            for dependency in component.dependencies:
                if dependency in self.components:
                    path = NavigationPath(
                        from_component=component_id,
                        to_component=dependency,
                        relationship_type="depends_on",
                        description=f"{component.name} depends on {self.components[dependency].name}",
                        complexity=1,
                    )
                    self.navigation_paths.append(path)

            # Create provision paths
            for provided_to in component.provides_to:
                if isinstance(provided_to, str) and provided_to in self.components:
                    path = NavigationPath(
                        from_component=component_id,
                        to_component=provided_to,
                        relationship_type="provides_to",
                        description=f"{component.name} provides services to {provided_to}",
                        complexity=1,
                    )
                    self.navigation_paths.append(path)

            # Create integration paths
            for integration in component.integration_points:
                if integration in self.components:
                    path = NavigationPath(
                        from_component=component_id,
                        to_component=integration,
                        relationship_type="integrates_with",
                        description=f"{component.name} integrates with {self.components[integration].name}",
                        complexity=2,
                    )
                    self.navigation_paths.append(path)

        logger.info(f"🔗 Built {len(self.navigation_paths)} navigation paths")

    def get_component_context(self, component_id: str) -> dict[str, Any]:
        """Get comprehensive context for a component."""
        if component_id not in self.components:
            return {"error": f"Component '{component_id}' not found"}

        component = self.components[component_id]

        # Get related components
        dependencies = [
            self.components[dep] for dep in component.dependencies if dep in self.components
        ]
        integrations = [
            self.components[integ]
            for integ in component.integration_points
            if integ in self.components
        ]

        # Find components that depend on this one
        dependents: list[Any] = []
        for other_comp in self.components.values():
            if component_id in other_comp.dependencies:
                dependents.append(other_comp)

        return {
            "component": {
                "id": component.id,
                "name": component.name,
                "path": str(component.path),
                "type": component.component_type.value,
                "operation_type": component.operation_type.value,
                "description": component.description,
                "context": component.context,
                "evolution_stage": component.evolution_stage,
                "priority": component.priority,
                "status": component.status,
            },
            "relationships": {
                "dependencies": [
                    {"id": dep.id, "name": dep.name, "type": dep.component_type.value}
                    for dep in dependencies
                ],
                "integrations": [
                    {
                        "id": integ.id,
                        "name": integ.name,
                        "type": integ.component_type.value,
                    }
                    for integ in integrations
                ],
                "dependents": [
                    {"id": dep.id, "name": dep.name, "type": dep.component_type.value}
                    for dep in dependents
                ],
            },
            "navigation": {
                "upstream": [
                    path for path in self.navigation_paths if path.from_component == component_id
                ],
                "downstream": [
                    path for path in self.navigation_paths if path.to_component == component_id
                ],
            },
        }

    def find_path_between_components(
        self, start: str, end: str, max_depth: int = 3
    ) -> list[list[str]]:
        """Find navigation paths between two components."""
        if start not in self.components or end not in self.components:
            return []

        paths: list[Any] = []
        visited = set()

        def dfs(current: str, target: str, path: list[str], depth: int) -> None:
            if depth > max_depth:
                return

            if current == target:
                paths.append([*path, current])
                return

            if current in visited:
                return

            visited.add(current)

            # Follow navigation paths
            for nav_path in self.navigation_paths:
                if nav_path.from_component == current:
                    dfs(nav_path.to_component, target, [*path, current], depth + 1)

            visited.remove(current)

        dfs(start, end, [], 0)
        return paths

    def get_system_overview(self) -> dict[str, Any]:
        """Get comprehensive system overview."""
        type_counts: dict[str, Any] = {}
        operation_counts: dict[str, Any] = {}
        evolution_stages: dict[str, Any] = {}
        for component in self.components.values():
            # Count by type
            type_key = component.component_type.value
            type_counts[type_key] = type_counts.get(type_key, 0) + 1

            # Count by operation type
            op_key = component.operation_type.value
            operation_counts[op_key] = operation_counts.get(op_key, 0) + 1

            # Count by evolution stage
            stage_key = component.evolution_stage
            evolution_stages[stage_key] = evolution_stages.get(stage_key, 0) + 1

        # Calculate priority distribution
        priority_distribution: dict[int, int] = {}
        for component in self.components.values():
            priority_distribution[component.priority] = (
                priority_distribution.get(component.priority, 0) + 1
            )

        return {
            "total_components": len(self.components),
            "component_types": type_counts,
            "operation_types": operation_counts,
            "evolution_stages": evolution_stages,
            "priority_distribution": priority_distribution,
            "navigation_paths": len(self.navigation_paths),
            "critical_components": [
                comp.id for comp in self.components.values() if comp.priority <= 2
            ],
            "active_components": [
                comp.id
                for comp in self.components.values()
                if comp.operation_type == OperationType.ACTIVE
            ],
        }

    def generate_execution_order(
        self, include_types: list[ComponentType] | None = None
    ) -> list[str]:
        """Generate optimal execution order based on dependencies and priorities."""
        components_to_order = list(self.components.keys())

        if include_types:
            components_to_order = [
                comp_id
                for comp_id, comp in self.components.items()
                if comp.component_type in include_types
            ]

        # Topological sort considering dependencies and priorities
        resolved: list[Any] = []
        unresolved: list[Any] = []

        def resolve(component_id: str) -> None:
            if component_id in unresolved:
                msg = f"Circular dependency detected: {component_id}"
                raise Exception(msg)

            if component_id not in resolved:
                unresolved.append(component_id)

                # Resolve dependencies first
                component = self.components[component_id]
                dependencies = [dep for dep in component.dependencies if dep in components_to_order]

                for dependency in dependencies:
                    resolve(dependency)

                resolved.append(component_id)
                unresolved.remove(component_id)

        # Sort by priority first
        sorted_components = sorted(
            components_to_order,
            key=lambda x: (self.components[x].priority, x),
        )

        for component_id in sorted_components:
            if component_id not in resolved:
                resolve(component_id)

        return resolved

    def create_context_snapshot(self) -> dict[str, Any]:
        """Create snapshot of current system context."""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_overview": self.get_system_overview(),
            "components": {
                comp_id: self.get_component_context(comp_id) for comp_id in self.components
            },
            "execution_orders": {
                "all_components": self.generate_execution_order(),
                "active_only": self.generate_execution_order(
                    [ComponentType.CORE, ComponentType.AI, ComponentType.QUEST]
                ),
                "critical_path": self.generate_execution_order()[:5],  # Top 5 by dependency order
            },
        }

    def interactive_navigation_menu(self) -> None:
        """Interactive navigation interface."""
        while True:
            try:
                choice = input("\nEnter your choice (0-9): ").strip()

                if choice == "0":
                    break
                if choice == "1":
                    self._show_system_overview()
                elif choice == "2":
                    self._explore_component()
                elif choice == "3":
                    self._find_component_path()
                elif choice == "4":
                    self._list_components_by_type()
                elif choice == "5":
                    self._generate_execution_order()
                elif choice == "6":
                    self._create_snapshot()
                elif choice == "7":
                    self._analyze_operation_types()
                elif choice == "8":
                    self._dependency_analysis()
                elif choice == "9":
                    self._evolution_analysis()
                else:
                    pass

            except KeyboardInterrupt:
                break
            except (EOFError, RuntimeError):
                pass

    def _show_system_overview(self) -> None:
        """Display comprehensive system overview."""
        overview = self.get_system_overview()

        for _comp_type, _count in overview["component_types"].items():
            pass

        for _op_type, _count in overview["operation_types"].items():
            pass

        for _stage, _count in overview["evolution_stages"].items():
            pass

        for comp_id in overview["critical_components"]:
            self.components[comp_id]

    def _explore_component(self) -> None:
        """Explore a specific component in detail."""
        for _i, (_comp_id, _comp) in enumerate(self.components.items(), 1):
            pass

        try:
            choice = int(input("Select component number: ")) - 1
            comp_ids = list(self.components.keys())

            if 0 <= choice < len(comp_ids):
                comp_id = comp_ids[choice]
                context = self.get_component_context(comp_id)

                context["component"]

                if context["relationships"]["dependencies"]:
                    for _dep in context["relationships"]["dependencies"]:
                        pass

                if context["relationships"]["integrations"]:
                    for _integ in context["relationships"]["integrations"]:
                        pass

            else:
                pass
        except ValueError:
            pass

    def _find_component_path(self) -> None:
        """Find path between two components."""
        comp_ids = list(self.components.keys())

        for _i, _comp_id in enumerate(comp_ids, 1):
            pass

        try:
            start_idx = int(input("Select start component: ")) - 1
            end_idx = int(input("Select end component: ")) - 1

            if 0 <= start_idx < len(comp_ids) and 0 <= end_idx < len(comp_ids):
                start_comp = comp_ids[start_idx]
                end_comp = comp_ids[end_idx]

                paths = self.find_path_between_components(start_comp, end_comp)

                if paths:
                    for _i, path in enumerate(paths, 1):
                        [self.components[comp_id].name for comp_id in path]
                else:
                    pass
            else:
                pass
        except ValueError:
            pass

    def _list_components_by_type(self) -> None:
        """List components grouped by type."""
        types: dict[str, Any] = {}
        for comp_id, comp in self.components.items():
            comp_type = comp.component_type.value
            if comp_type not in types:
                types[comp_type] = []
            types[comp_type].append((comp_id, comp))

        for _comp_type, components in types.items():
            for _comp_id, _comp in components:
                pass

    def _generate_execution_order(self) -> None:
        """Generate and display execution order."""
        try:
            choice = input("Select option (1-3): ").strip()

            if choice == "1":
                order = self.generate_execution_order()
            elif choice == "2":
                order = self.generate_execution_order([ComponentType.CORE, ComponentType.AI])
            elif choice == "3":
                order = [
                    comp_id
                    for comp_id in self.generate_execution_order()
                    if self.components[comp_id].operation_type == OperationType.ACTIVE
                ]
            else:
                return

            for _i, comp_id in enumerate(order, 1):
                self.components[comp_id]

        except (KeyError, AttributeError, ValueError):
            pass

    def _create_snapshot(self) -> None:
        """Create and display system snapshot."""
        snapshot = self.create_context_snapshot()

        snapshot_file = (
            self.base_path / f"system_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2)

    def _analyze_operation_types(self) -> None:
        """Analyze active vs passive operations."""
        active_components: list[Any] = []
        passive_components: list[Any] = []
        hybrid_components: list[Any] = []
        for comp_id, comp in self.components.items():
            if comp.operation_type == OperationType.ACTIVE:
                active_components.append((comp_id, comp))
            elif comp.operation_type == OperationType.PASSIVE:
                passive_components.append((comp_id, comp))
            else:
                hybrid_components.append((comp_id, comp))

        for _comp_id, _comp in active_components:
            pass

        for _comp_id, _comp in passive_components:
            pass

        for _comp_id, _comp in hybrid_components:
            pass

    def _dependency_analysis(self) -> None:
        """Analyze component dependencies."""
        # Components with no dependencies (starting points)
        no_deps = [comp_id for comp_id, comp in self.components.items() if not comp.dependencies]
        for _comp_id in no_deps:
            pass

        # Components with most dependencies
        most_deps = sorted(
            [(comp_id, len(comp.dependencies)) for comp_id, comp in self.components.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        for _comp_id, dep_count in most_deps:
            if dep_count > 0:
                pass

        # Most depended upon
        dependents: dict[str, Any] = {}
        for _comp_id, comp in self.components.items():
            for dep in comp.dependencies:
                dependents[dep] = dependents.get(dep, 0) + 1

        most_depended = sorted(dependents.items(), key=lambda x: x[1], reverse=True)[:5]
        for comp_id, _dependent_count in most_depended:
            if comp_id in self.components:
                pass

    def _evolution_analysis(self) -> None:
        """Analyze evolution stages."""
        stages: dict[str, Any] = {}
        for comp_id, comp in self.components.items():
            stage = comp.evolution_stage
            if stage not in stages:
                stages[stage] = []
            stages[stage].append((comp_id, comp))

        for stage in sorted(stages.keys()):
            components = stages[stage]
            for _comp_id, _comp in components:
                "⭐" * (6 - comp.priority)


def main() -> None:
    """Main entry point for repository navigator."""
    navigator = RepositoryNavigator()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "overview":
            navigator.get_system_overview()
        elif command == "snapshot":
            navigator.create_context_snapshot()
        elif command == "order":
            navigator.generate_execution_order()
        else:
            pass
    else:
        navigator.interactive_navigation_menu()


if __name__ == "__main__":
    main()
