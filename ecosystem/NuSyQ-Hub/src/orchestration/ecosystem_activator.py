"""Ecosystem Activator - Comprehensive system integration and activation.

This module discovers, wires, and activates all dormant infrastructure in the
NuSyQ ecosystem. It serves as the central activation point for:

- Consciousness Bridge (OmniTag, MegaTag, Symbolic Cognition)
- Quantum Systems (QuantumProblemResolver, Neural Healing)
- Integration Bridges (SimulatedVerse, Quest Temple, ChatDev-Copilot)
- AI Context Managers (Unified AI Context)
- Legacy Transformers (Code modernization)
- Game Systems (Boss Rush, Quest bridges)

This is the "master switch" for ecosystem activation.

OmniTag: ecosystem_activation, infrastructure_wiring, capability_discovery
MegaTag: MEGA_ACTIVATION, DORMANT_AWAKENING, SYSTEM_ORCHESTRATION
"""

from __future__ import annotations

import importlib
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

try:  # Python 3.11+
    from typing import NotRequired
except ImportError:  # Python <=3.10
    from typing import NotRequired

logger = logging.getLogger(__name__)


@dataclass
class ActivatedSystem:
    """Represents an activated system or bridge."""

    system_id: str
    name: str
    module_path: str
    system_type: str  # consciousness, quantum, integration, ai, legacy, game
    status: str = "inactive"  # inactive, initializing, active, error
    instance: Any | None = None
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    activated_at: str | None = None
    error: str | None = None


class SystemDef(TypedDict):
    system_id: str
    name: str
    module_path: str
    system_type: str
    capabilities: list[str]
    class_name: NotRequired[str]


class EcosystemActivator:
    """Central activator for all dormant NuSyQ infrastructure."""

    def __init__(self) -> None:
        """Initialize EcosystemActivator."""
        self.systems: dict[str, ActivatedSystem] = {}
        self.activation_log: list[dict[str, Any]] = []
        self.project_root = Path(__file__).resolve().parents[2]

        # Add src/ to path if not already there
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))

        # Load persisted state if available
        self._load_persisted_state()

        logger.info("🔌 Ecosystem Activator initialized")

    def _load_persisted_state(self) -> None:
        """Load previously activated systems from state/ecosystem_registry.json."""
        registry_path = self.project_root / "state" / "ecosystem_registry.json"

        if not registry_path.exists():
            logger.debug("No persisted ecosystem state found")
            return

        try:
            import json

            with open(registry_path, encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct ActivatedSystem objects from saved state
            for system_id, system_data in data.get("systems", {}).items():
                self.systems[system_id] = ActivatedSystem(
                    system_id=system_id,
                    name=system_data.get("name", "Unknown"),
                    module_path=system_data.get("module_path", ""),
                    system_type=system_data.get("system_type", "unknown"),
                    status="active",  # Assume active from registry
                    instance=None,  # Instances not persisted, will need re-activation
                    capabilities=system_data.get("capabilities", []),
                    metadata=system_data.get("metadata", {}),
                    activated_at=system_data.get("activated_at"),
                )

            logger.info(f"✅ Loaded {len(self.systems)} systems from persisted state")

        except Exception as e:
            logger.warning(f"⚠️ Could not load persisted ecosystem state: {e}")

    def discover_systems(self) -> list[ActivatedSystem]:
        """Discover all activatable systems in the codebase."""
        discoveries = []

        # Consciousness systems
        consciousness_systems: list[SystemDef] = [
            {
                "system_id": "consciousness_bridge",
                "name": "Consciousness Bridge",
                "module_path": "src.integration.consciousness_bridge",
                "class_name": "ConsciousnessBridge",
                "system_type": "consciousness",
                "capabilities": [
                    "omnitag_processing",
                    "megatag_analysis",
                    "symbolic_cognition",
                    "contextual_memory",
                ],
            },
        ]

        # Quantum systems
        quantum_systems: list[SystemDef] = [
            {
                "system_id": "quantum_resolver",
                "name": "Quantum Problem Resolver",
                "module_path": "src.quantum.quantum_problem_resolver",
                "class_name": "QuantumProblemResolver",
                "system_type": "quantum",
                "capabilities": [
                    "quantum_problem_solving",
                    "superposition_analysis",
                    "entanglement_resolution",
                ],
            },
        ]

        # Strategic oversight systems
        strategic_systems: list[SystemDef] = [
            {
                "system_id": "culture_ship_advisor",
                "name": "Culture Ship Strategic Advisor",
                "module_path": "src.orchestration.culture_ship_strategic_advisor",
                "class_name": "CultureShipStrategicAdvisor",
                "system_type": "strategic",
                "capabilities": [
                    "identify_strategic_issues",
                    "make_strategic_decisions",
                    "implement_decisions",
                    "run_full_strategic_cycle",
                ],
            },
        ]

        # Integration bridges
        integration_bridges: list[SystemDef] = [
            {
                "system_id": "simverse_bridge",
                "name": "SimulatedVerse Unified Bridge",
                "module_path": "src.integration.simulatedverse_unified_bridge",
                "class_name": "SimulatedVerseUnifiedBridge",
                "system_type": "integration",
                "capabilities": [
                    "cross_repo_sync",
                    "simverse_cultivation",
                    "reality_bridging",
                ],
            },
            {
                "system_id": "quest_temple_bridge",
                "name": "Quest Temple Progression Bridge",
                "module_path": "src.integration.quest_temple_bridge",
                "class_name": "QuestTempleProgressionBridge",
                "system_type": "integration",
                "capabilities": [
                    "quest_temple_sync",
                    "knowledge_floor_access",
                    "agent_registry_bridge",
                    "progression_calculation",
                ],
            },
            {
                "system_id": "chatdev_copilot_bridge",
                "name": "Advanced ChatDev-Ollama Orchestrator",
                "module_path": "src.integration.advanced_chatdev_copilot_integration",
                "class_name": "AdvancedChatDevOllamaOrchestrator",
                "system_type": "integration",
                "capabilities": [
                    "chatdev_ollama_coordination",
                    "multi_agent_dev",
                    "ollama_enhancement",
                ],
            },
            {
                "system_id": "quantum_error_bridge",
                "name": "Quantum Error Bridge",
                "module_path": "src.integration.quantum_error_bridge",
                "class_name": "QuantumErrorBridge",
                "system_type": "integration",
                "capabilities": [
                    "handle_error",
                    "scan_and_heal",
                ],
            },
        ]

        # AI Context Managers
        ai_systems: list[SystemDef] = [
            {
                "system_id": "unified_ai_context",
                "name": "Unified AI Context Manager",
                "module_path": "src.integration.unified_ai_context_manager",
                "class_name": "UnifiedAIContextManager",
                "system_type": "ai",
                "capabilities": [
                    "add_context",
                    "get_context",
                    "get_contexts_by_type",
                    "get_contexts_by_system",
                    "update_system_status",
                    "get_system_status",
                    "get_all_system_statuses",
                    "create_context_link",
                    "get_related_contexts",
                    "export_context_for_system",
                ],
            },
        ]

        # Legacy transformers
        legacy_systems: list[SystemDef] = [
            {
                "system_id": "kardashev_civilization",
                "name": "Kardashev Civilization System",
                "module_path": "src.integration.legacy_transformer",
                "class_name": "KardashevCivilization",
                "system_type": "legacy",
                "capabilities": [
                    "civilization_advancement",
                    "resource_management",
                    "ai_decision_making",
                ],
            },
        ]

        # Game systems
        game_systems: list[SystemDef] = [
            {
                "system_id": "boss_rush_bridge",
                "name": "Boss Rush Game Bridge",
                "module_path": "src.integration.boss_rush_bridge",
                "class_name": "BossRushBridge",
                "system_type": "game",
                "capabilities": [
                    "get_active_tasks",
                    "submit_proof_gate",
                    "sync_to_quest_system",
                    "archive_to_temple",
                    "get_boss_rush_progress",
                    "get_completed_tasks",
                    "get_task_by_id",
                    "get_tool_arsenal_status",
                    "load_knowledge_base",
                ],
            },
            {
                "system_id": "game_quest_integration",
                "name": "Game Quest Integration Bridge",
                "module_path": "src.integration.game_quest_bridge",
                "class_name": "GameQuestIntegrationBridge",
                "system_type": "game",
                "capabilities": [
                    "emit_event",
                    "get_game_statistics",
                    "register_event_handler",
                ],
            },
        ]

        # Zen Engine systems
        zen_systems: list[SystemDef] = [
            {
                "system_id": "zen_codex_bridge",
                "name": "Zen Codex Bridge",
                "module_path": "src.integration.zen_codex_bridge",
                "class_name": "ZenCodexBridge",
                "system_type": "zen",
                "capabilities": [
                    "get_wisdom_for_error",
                    "learn_from_error",
                    "learn_from_success",
                    "orchestrate_multi_agent_task",
                    "query_rules_by_tag",
                    "search_rules",
                    "zen_agent_query_ecosystem",
                ],
            },
        ]

        # Performance optimization systems
        performance_systems: list[SystemDef] = [
            {
                "system_id": "breathing_integration",
                "name": "Breathing Pacing Integration",
                "module_path": "src.integration.breathing_integration",
                "class_name": "BreathingIntegration",
                "system_type": "performance",
                "capabilities": [
                    "apply_to_timeout",
                    "calculate_breathing_factor",
                    "get_breathing_state",
                    "update_metrics",
                ],
            },
        ]

        # Phase 3 Ecosystem Generators - Code Generation & Scaffolding
        generator_systems: list[SystemDef] = [
            {
                "system_id": "graphql_generator",
                "name": "GraphQL API Generator",
                "module_path": "src.generators.graphql_generator",
                "class_name": "GraphQLSchemaGenerator",
                "system_type": "generator",
                "capabilities": [
                    "generate_schema",
                    "generate_resolvers",
                    "generate_types",
                    "generate_full_api",
                ],
            },
            {
                "system_id": "openapi_generator",
                "name": "OpenAPI/REST API Generator",
                "module_path": "src.generators.openapi_generator",
                "class_name": "OpenAPIGenerator",
                "system_type": "generator",
                "capabilities": [
                    "generate_spec",
                    "generate_paths",
                    "generate_schemas",
                    "generate_full_api",
                ],
            },
            {
                "system_id": "react_component_generator",
                "name": "React Component Scaffolder",
                "module_path": "src.generators.component_scaffolding",
                "class_name": "ReactComponentGenerator",
                "system_type": "generator",
                "capabilities": [
                    "generate_component",
                    "generate_styles",
                    "generate_tests",
                    "generate_storybook",
                ],
            },
            {
                "system_id": "database_schema_generator",
                "name": "Database Schema & Migration Generator",
                "module_path": "src.generators.database_helpers",
                "class_name": "SQLSchemaGenerator",
                "system_type": "generator",
                "capabilities": [
                    "generate_schema",
                    "generate_migrations",
                    "generate_models",
                    "generate_seeders",
                ],
            },
            {
                "system_id": "universal_project_generator",
                "name": "Universal Project Generator",
                "module_path": "src.factories.generators.specialized.universal_project_generator",
                "class_name": "UniversalProjectGenerator",
                "system_type": "generator",
                "capabilities": [
                    "generate_project",
                    "generate_structure",
                    "generate_config",
                    "generate_documentation",
                ],
            },
        ]

        all_system_defs: list[SystemDef] = (
            consciousness_systems
            + quantum_systems
            + strategic_systems
            + integration_bridges
            + ai_systems
            + legacy_systems
            + game_systems
            + zen_systems
            + performance_systems
            + generator_systems
        )

        for sys_def in all_system_defs:
            system = ActivatedSystem(
                system_id=sys_def["system_id"],
                name=sys_def["name"],
                module_path=sys_def["module_path"],
                system_type=sys_def["system_type"],
                capabilities=sys_def["capabilities"],
                metadata={"class_name": sys_def.get("class_name", "")},
            )
            discoveries.append(system)

        logger.info(f"🔍 Discovered {len(discoveries)} activatable systems")

        return discoveries

    def activate_system(self, system: ActivatedSystem) -> bool:
        """Activate a discovered system."""
        system.status = "initializing"

        try:
            # Import module
            module = importlib.import_module(system.module_path)

            # Get class
            class_name = system.metadata.get("class_name")
            if not class_name:
                raise ValueError(f"No class_name specified for {system.system_id}")

            cls = getattr(module, class_name)

            # Instantiate
            try:
                instance = cls()
            except TypeError:
                # Some classes may not have __init__ or may need specific args
                # Try with common patterns
                instance = cls.__new__(cls)

            # Initialize if method exists
            if hasattr(instance, "initialize"):
                instance.initialize()

            system.instance = instance
            system.status = "active"
            system.activated_at = datetime.now().isoformat()

            self.systems[system.system_id] = system
            self._log_activation(system, success=True)

            logger.info(f"✅ Activated: {system.name} ({system.system_type})")

            return True

        except Exception as e:
            system.status = "error"
            system.error = str(e)
            self.systems[system.system_id] = system
            self._log_activation(system, success=False, error=str(e))

            logger.error(f"❌ Failed to activate {system.name}: {e}")

            return False

    def activate_all(
        self, system_types: list[str] | None = None, skip_on_error: bool = True
    ) -> dict[str, Any]:
        """Activate all discovered systems, optionally filtered by type."""
        discoveries = self.discover_systems()

        if system_types:
            discoveries = [s for s in discoveries if s.system_type in system_types]

        results: dict[str, Any] = {
            "total": len(discoveries),
            "activated": 0,
            "failed": 0,
            "skipped": 0,
            "systems": [],
        }

        for system in discoveries:
            success = self.activate_system(system)

            if success:
                results["activated"] += 1
                results["systems"].append(
                    {
                        "id": system.system_id,
                        "name": system.name,
                        "status": "active",
                        "capabilities": len(system.capabilities),
                    }
                )
            else:
                results["failed"] += 1
                results["systems"].append(
                    {
                        "id": system.system_id,
                        "name": system.name,
                        "status": "error",
                        "error": system.error,
                    }
                )

                if not skip_on_error:
                    break

        logger.info(
            f"🎯 Activation complete: {results['activated']}/{results['total']} systems active"
        )

        return results

    def get_active_systems(self, system_type: str | None = None) -> list[ActivatedSystem]:
        """Get all active systems, optionally filtered by type."""
        active = [s for s in self.systems.values() if s.status == "active"]

        if system_type:
            active = [s for s in active if s.system_type == system_type]

        return active

    def get_system(self, system_id: str) -> ActivatedSystem | None:
        """Get a specific system by ID."""
        return self.systems.get(system_id)

    def invoke_capability(self, capability_name: str, *args: Any, **kwargs: Any) -> Any | None:
        """Invoke a capability across all systems that provide it."""
        results = []

        for system in self.systems.values():
            if system.status != "active":
                continue

            if capability_name not in system.capabilities:
                continue

            # Try to find and invoke the capability method
            instance = system.instance
            if not instance:
                continue

            # Common capability method naming patterns
            method_names = [
                capability_name,
                capability_name.replace("_", ""),
                f"execute_{capability_name}",
                f"run_{capability_name}",
            ]

            for method_name in method_names:
                if hasattr(instance, method_name):
                    try:
                        method = getattr(instance, method_name)
                        result = method(*args, **kwargs)
                        results.append(
                            {
                                "system": system.name,
                                "system_id": system.system_id,
                                "result": result,
                            }
                        )
                        break
                    except Exception as e:
                        logger.error(f"Error invoking {capability_name} on {system.name}: {e}")

        return results if results else None

    def get_activation_stats(self) -> dict[str, Any]:
        """Get comprehensive activation statistics."""
        total = len(self.systems)
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        total_capabilities = 0

        for system in self.systems.values():
            # Count by status
            by_status[system.status] = by_status.get(system.status, 0) + 1

            # Count by type
            by_type[system.system_type] = by_type.get(system.system_type, 0) + 1

            # Count capabilities
            total_capabilities += len(system.capabilities)

        return {
            "total_systems": total,
            "by_status": by_status,
            "by_type": by_type,
            "total_capabilities": total_capabilities,
            "activation_rate": by_status.get("active", 0) / total if total > 0 else 0,
            "last_activation": self.activation_log[-1] if self.activation_log else None,
        }

    def _log_activation(
        self, system: ActivatedSystem, success: bool, error: str | None = None
    ) -> None:
        """Log activation attempt."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "system_id": system.system_id,
            "system_name": system.name,
            "system_type": system.system_type,
            "success": success,
            "error": error,
        }

        self.activation_log.append(entry)

        # Keep only recent 100 entries in memory
        if len(self.activation_log) > 100:
            self.activation_log = self.activation_log[-50:]

    def deactivate_system(self, system_id: str) -> bool:
        """Deactivate a system."""
        system = self.systems.get(system_id)
        if not system:
            return False

        try:
            # Call shutdown if available
            if system.instance and hasattr(system.instance, "shutdown"):
                system.instance.shutdown()

            system.status = "inactive"
            system.instance = None

            logger.info(f"⏸️  Deactivated: {system.name}")

            return True

        except Exception as e:
            logger.error(f"Error deactivating {system.name}: {e}")
            return False

    def deactivate_all(self) -> dict[str, int]:
        """Deactivate all active systems."""
        results = {"deactivated": 0, "failed": 0}

        for system_id in list(self.systems.keys()):
            if self.deactivate_system(system_id):
                results["deactivated"] += 1
            else:
                results["failed"] += 1

        return results


# Global activator instance
_activator: EcosystemActivator | None = None


def get_ecosystem_activator() -> EcosystemActivator:
    """Get or create the global ecosystem activator."""
    global _activator
    if _activator is None:
        _activator = EcosystemActivator()
    return _activator
