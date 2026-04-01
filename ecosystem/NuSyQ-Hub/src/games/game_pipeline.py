"""Game Development Pipeline Integration.

Integrates all game subsystems into a unified pipeline:
- Central game registry
- Module discovery and validation
- Cross-module event bus
- Unified initialization
- Health monitoring
"""

import importlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """Status of a game module."""

    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class GameModule:
    """A registered game module."""

    name: str
    module_path: str
    status: ModuleStatus = ModuleStatus.NOT_LOADED
    instance: Any | None = None
    dependencies: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    load_time_ms: float = 0.0
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "module_path": self.module_path,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "provides": self.provides,
            "load_time_ms": self.load_time_ms,
            "error": self.error_message,
        }


@dataclass
class PipelineEvent:
    """An event in the game pipeline."""

    event_type: str
    source: str
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class GameEventBus:
    """Central event bus for cross-module communication."""

    def __init__(self):
        """Initialize GameEventBus."""
        self._subscribers: dict[str, list[Callable]] = {}
        self._event_log: list[PipelineEvent] = []
        self._max_log_size = 1000

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]

    def publish(self, event: PipelineEvent) -> int:
        """Publish an event, return number of subscribers notified."""
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size :]

        count = 0
        for event_type in ["*", event.event_type]:
            for callback in self._subscribers.get(event_type, []):
                try:
                    callback(event)
                    count += 1
                except Exception as e:
                    logger.warning(f"Event callback error: {e}")

        return count

    def get_recent_events(self, limit: int = 20) -> list[dict]:
        """Get recent events."""
        return [
            {
                "type": e.event_type,
                "source": e.source,
                "data": e.data,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in self._event_log[-limit:]
        ]


class GamePipeline:
    """Unified game development pipeline.

    Orchestrates all game modules and provides central management.
    """

    # Registered modules with their configurations
    MODULE_REGISTRY: ClassVar[dict] = {
        "hacking_quests": {
            "path": "src.games.hacking_quests",
            "class": "HackingQuestManager",
            "provides": ["quests", "hacking"],
            "dependencies": [],
        },
        "achievements": {
            "path": "src.games.achievements",
            "class": "AchievementManager",
            "provides": ["achievements", "leaderboard"],
            "dependencies": [],
        },
        "game_state": {
            "path": "src.games.game_state",
            "class": "GameStateManager",
            "provides": ["save", "load", "persistence"],
            "dependencies": [],
        },
        "mini_games": {
            "path": "src.games.mini_games",
            "class": "MiniGameManager",
            "provides": ["minigames", "arcade"],
            "dependencies": [],
        },
        "procedural_quests": {
            "path": "src.games.procedural_quests",
            "class": "ProceduralQuestGenerator",
            "provides": ["procedural", "quest_generation"],
            "dependencies": [],
        },
        "narrative_engine": {
            "path": "src.games.narrative_engine",
            "class": "NarrativeEngine",
            "provides": ["narrative", "storytelling"],
            "dependencies": [],
        },
        "analytics": {
            "path": "src.games.analytics",
            "class": "GameAnalytics",
            "provides": ["analytics", "telemetry"],
            "dependencies": [],
        },
        "terminal_ui": {
            "path": "src.games.terminal_ui",
            "class": "TerminalUI",
            "provides": ["ui", "display"],
            "dependencies": [],
        },
        "ai_opponents": {
            "path": "src.games.ai_opponents",
            "class": "AIGameMaster",
            "provides": ["ai", "opponents", "npc"],
            "dependencies": [],
        },
        "dynamic_game_master": {
            "path": "src.games.dynamic_game_master",
            "class": "DynamicGameMaster",
            "provides": ["game_master", "events", "story"],
            "dependencies": ["narrative_engine"],
        },
        "multiplayer_factions": {
            "path": "src.games.multiplayer_factions",
            "class": "FactionManager",
            "provides": ["factions", "multiplayer", "territory"],
            "dependencies": [],
        },
        "consciousness_integration": {
            "path": "src.games.consciousness_integration",
            "class": "ConsciousnessGameBridge",
            "provides": ["consciousness", "simverse", "cp"],
            "dependencies": [],
        },
        "cyber_terminal": {
            "path": "src.games.cyber_terminal",
            "class": "CyberTerminal",
            "provides": ["terminal", "interface", "commands"],
            "dependencies": ["hacking_quests", "achievements", "mini_games"],
        },
    }

    def __init__(self, auto_load: bool = False):
        """Initialize GamePipeline with auto_load."""
        self.modules: dict[str, GameModule] = {}
        self.event_bus = GameEventBus()
        self._initialized = False

        # Register all modules
        for name, config in self.MODULE_REGISTRY.items():
            self.modules[name] = GameModule(
                name=name,
                module_path=config["path"],
                dependencies=config.get("dependencies", []),
                provides=config.get("provides", []),
            )

        if auto_load:
            self.initialize()

    def initialize(self) -> dict:
        """Initialize all game modules."""
        results = {"loaded": [], "errors": []}

        # Load in dependency order
        load_order = self._resolve_load_order()

        for module_name in load_order:
            success = self.load_module(module_name)
            if success:
                results["loaded"].append(module_name)
            else:
                results["errors"].append(module_name)

        self._initialized = True

        # Publish initialization event
        self.event_bus.publish(
            PipelineEvent(event_type="pipeline.initialized", source="pipeline", data=results)
        )

        return results

    def _resolve_load_order(self) -> list[str]:
        """Resolve module load order based on dependencies."""
        resolved = []
        unresolved = list(self.modules.keys())

        while unresolved:
            made_progress = False
            for name in unresolved[:]:
                module = self.modules[name]
                deps_met = all(d in resolved for d in module.dependencies)
                if deps_met:
                    resolved.append(name)
                    unresolved.remove(name)
                    made_progress = True

            if not made_progress:
                # Circular dependency or missing - load remaining anyway
                resolved.extend(unresolved)
                break

        return resolved

    def load_module(self, module_name: str) -> bool:
        """Load a specific module."""
        if module_name not in self.modules:
            logger.error(f"Unknown module: {module_name}")
            return False

        module = self.modules[module_name]
        module.status = ModuleStatus.LOADING

        start_time = datetime.now()

        try:
            config = self.MODULE_REGISTRY[module_name]

            # Import module
            mod = importlib.import_module(config["path"])

            # Get class
            cls = getattr(mod, config["class"], None)
            if cls:
                module.instance = cls()
            else:
                # Just use module itself
                module.instance = mod

            module.status = ModuleStatus.READY
            module.load_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(f"Loaded {module_name} in {module.load_time_ms:.1f}ms")
            return True

        except Exception as e:
            module.status = ModuleStatus.ERROR
            module.error_message = str(e)
            module.load_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.warning(f"Failed to load {module_name}: {e}")
            return False

    def get_module(self, module_name: str) -> Any | None:
        """Get a loaded module instance."""
        module = self.modules.get(module_name)
        if module and module.status == ModuleStatus.READY:
            return module.instance
        return None

    def get_capability(self, capability: str) -> Any | None:
        """Get a module by capability it provides."""
        for module in self.modules.values():
            if capability in module.provides and module.status == ModuleStatus.READY:
                return module.instance
        return None

    def get_status(self) -> dict:
        """Get pipeline status."""
        modules_by_status = {status: [] for status in ModuleStatus}
        for module in self.modules.values():
            modules_by_status[module.status].append(module.name)

        return {
            "initialized": self._initialized,
            "total_modules": len(self.modules),
            "ready": len(modules_by_status[ModuleStatus.READY]),
            "errors": len(modules_by_status[ModuleStatus.ERROR]),
            "not_loaded": len(modules_by_status[ModuleStatus.NOT_LOADED]),
            "modules": {name: module.to_dict() for name, module in self.modules.items()},
            "capabilities": list(
                {
                    cap
                    for m in self.modules.values()
                    if m.status == ModuleStatus.READY
                    for cap in m.provides
                }
            ),
            "recent_events": self.event_bus.get_recent_events(5),
        }

    def health_check(self) -> dict:
        """Run health check on all modules."""
        results = {"healthy": [], "degraded": [], "failed": [], "overall": "healthy"}

        for name, module in self.modules.items():
            if module.status == ModuleStatus.READY:
                results["healthy"].append(name)
            elif module.status == ModuleStatus.ERROR:
                results["failed"].append(name)
            else:
                results["degraded"].append(name)

        if results["failed"]:
            results["overall"] = "degraded"
        if len(results["failed"]) > len(self.modules) // 2:
            results["overall"] = "critical"

        return results

    def emit_game_event(self, event_type: str, data: dict, source: str = "game") -> int:
        """Emit a game event to all subscribers."""
        event = PipelineEvent(event_type=event_type, source=source, data=data)
        return self.event_bus.publish(event)

    def shutdown(self) -> None:
        """Shutdown all modules."""
        self.event_bus.publish(
            PipelineEvent(
                event_type="pipeline.shutdown",
                source="pipeline",
                data={"timestamp": datetime.now().isoformat()},
            )
        )

        for module in self.modules.values():
            if module.instance and hasattr(module.instance, "shutdown"):
                try:
                    module.instance.shutdown()
                except Exception as e:
                    logger.warning(f"Error shutting down {module.name}: {e}")
            module.status = ModuleStatus.NOT_LOADED
            module.instance = None

        self._initialized = False


# === Module-level convenience ===

_pipeline: GamePipeline | None = None


def get_pipeline(auto_load: bool = True) -> GamePipeline:
    """Get or create the game pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = GamePipeline(auto_load=auto_load)
    return _pipeline


def get_game_module(name: str) -> Any | None:
    """Get a game module by name."""
    return get_pipeline().get_module(name)


def get_capability(capability: str) -> Any | None:
    """Get a module by capability."""
    return get_pipeline().get_capability(capability)


def emit_event(event_type: str, data: dict) -> int:
    """Emit a game event."""
    return get_pipeline().emit_game_event(event_type, data)


def pipeline_status() -> dict:
    """Get pipeline status."""
    return get_pipeline(auto_load=False).get_status()


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    print("Game Pipeline Integration Demo")
    print("=" * 40)

    pipeline = GamePipeline(auto_load=False)

    # Initialize
    print("\n--- Initializing Pipeline ---")
    results = pipeline.initialize()
    print(f"Loaded: {len(results['loaded'])} modules")
    print(f"Errors: {len(results['errors'])} modules")

    # Show status
    status = pipeline.get_status()
    print("\n--- Pipeline Status ---")
    print(f"Total: {status['total_modules']}")
    print(f"Ready: {status['ready']}")
    print(f"Errors: {status['errors']}")

    # Show capabilities
    print("\n--- Available Capabilities ---")
    caps = status["capabilities"]
    for i in range(0, len(caps), 4):
        print(f"  {', '.join(caps[i : i + 4])}")

    # Health check
    health = pipeline.health_check()
    print("\n--- Health Check ---")
    print(f"Overall: {health['overall'].upper()}")
    print(f"Healthy: {len(health['healthy'])}")
    if health["failed"]:
        print(
            f"Failed: {', '.join(health['failed'][:5])}{'...' if len(health['failed']) > 5 else ''}"
        )

    # Show loaded modules
    print("\n--- Loaded Modules ---")
    for name, info in status["modules"].items():
        if info["status"] == "ready":
            print(f"  ✓ {name} ({info['load_time_ms']:.0f}ms)")

    # Test event emission
    print("\n--- Event Test ---")
    count = pipeline.emit_game_event("test.demo", {"message": "Hello from pipeline"})
    print(f"Event emitted to {count} subscribers")

    print("\n✅ Game pipeline integration complete!")
