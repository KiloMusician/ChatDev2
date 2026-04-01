#!/usr/bin/env python3
"""Full System Activation - Brings all NuSyQ subsystems online.

Activates:
- Guild Board (multi-agent coordination)
- Quest Executor (automated task execution)
- Healing Systems (error resolution)
- Culture Ship (terminal integration)
- Background Task Orchestrator (queue processing)
- Bridge Registry (service adapters)
"""

import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SystemActivation")


class FullSystemActivator:
    """Orchestrates activation of all NuSyQ subsystems."""

    def __init__(self):
        self.active_systems = {}
        self.log_path = Path(__file__).parent.parent / "data/terminal_logs"

    def log_to_terminal(self, channel: str, message: str, level: str = "INFO"):
        """Write to terminal log file."""
        log_file = self.log_path / f"{channel.lower()}.log"
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "channel": channel,
            "level": level,
            "message": message,
            "meta": {"source": "system_activator"},
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    async def activate_orchestration(self):
        """Activate core orchestration systems."""
        logger.info("Activating Orchestration Layer...")

        from src.orchestration import BackgroundTaskOrchestrator, UnifiedAIOrchestrator

        self.active_systems["background_orchestrator"] = BackgroundTaskOrchestrator()
        self.active_systems["unified_orchestrator"] = UnifiedAIOrchestrator()

        stats = self.active_systems["background_orchestrator"].get_queue_stats()
        caps = self.active_systems["unified_orchestrator"].get_capabilities()

        logger.info(f"  Queue: {stats['queued']} tasks, {stats['completed']} completed")
        logger.info(f"  AI Systems: {len(caps['systems'])} active")

        self.log_to_terminal("System", f"Orchestration active: {stats['queued']} queued tasks")
        return stats, caps

    async def activate_guild_board(self):
        """Activate Guild Board for multi-agent coordination."""
        logger.info("Activating Guild Board...")

        try:
            from src.guild.guild_board import AgentStatus, GuildBoard

            board = GuildBoard()
            self.active_systems["guild_board"] = board

            # Register Claude as an active agent
            await board.post_heartbeat(
                agent_id="claude_code",
                status=AgentStatus.WORKING,
                capabilities=["code_generation", "analysis", "orchestration", "delegation"],
                current_quest="system_activation",
            )

            logger.info("  Guild Board active, Claude registered")
            self.log_to_terminal("Agents", "Guild Board activated - Claude registered")
            return board
        except Exception as e:
            logger.warning(f"  Guild Board activation failed: {e}")
            return None

    async def activate_quest_system(self):
        """Activate Quest execution system."""
        logger.info("Activating Quest System...")

        try:
            from src.quest.quest_executor import Quest

            # Check for active quests
            quest_log = Path(__file__).parent.parent / "data/quest_log.jsonl"
            active_quests = []

            if quest_log.exists():
                with open(quest_log) as f:
                    for line in f:
                        quest = Quest.from_jsonl_line(line)
                        if quest and quest.status == "active":
                            active_quests.append(quest)

            logger.info(f"  Found {len(active_quests)} active quests")
            self.log_to_terminal("Tasks", f"Quest system active: {len(active_quests)} quests")
            return active_quests
        except Exception as e:
            logger.warning(f"  Quest system activation failed: {e}")
            return []

    async def activate_healing_systems(self):
        """Activate self-healing capabilities."""
        logger.info("Activating Healing Systems...")

        try:
            from src.healing.quantum_problem_resolver import QuantumProblemResolver

            resolver = QuantumProblemResolver()
            self.active_systems["quantum_resolver"] = resolver

            logger.info("  Quantum Problem Resolver active")
            self.log_to_terminal("System", "Healing systems online")
            return resolver
        except Exception as e:
            logger.warning(f"  Healing systems activation failed: {e}")
            return None

    async def activate_bridge_registry(self):
        """Activate service bridges."""
        logger.info("Activating Bridge Registry...")

        try:
            from src.orchestration.bridges import BridgeRegistry

            registry = BridgeRegistry(hub=None)
            self.active_systems["bridges"] = registry

            available = list(registry.BRIDGE_CLASSES.keys())
            logger.info(f"  Bridges available: {available}")
            self.log_to_terminal("System", f"Bridges active: {available}")
            return registry
        except Exception as e:
            logger.warning(f"  Bridge Registry activation failed: {e}")
            return None

    async def activate_culture_ship(self):
        """Activate Culture Ship terminal integration."""
        logger.info("Activating Culture Ship...")

        try:
            from src.culture_ship.integrated_terminal import IntegratedTerminal

            terminal = IntegratedTerminal()
            self.active_systems["culture_ship"] = terminal

            logger.info("  Culture Ship terminal active")
            self.log_to_terminal("Culture_ship", "Culture Ship systems nominal")
            return terminal
        except Exception as e:
            logger.warning(f"  Culture Ship activation failed: {e}")
            return None

    async def delegate_startup_tasks(self):
        """Create and delegate startup improvement tasks."""
        logger.info("Delegating startup tasks...")

        bg = self.active_systems.get("background_orchestrator")
        if not bg:
            return []

        from src.orchestration.background_task_orchestrator import TaskPriority, TaskTarget

        tasks_to_delegate = [
            # Code quality tasks
            (
                "Analyze src/orchestration/ for code duplication and suggest refactoring",
                TaskTarget.OLLAMA,
                TaskPriority.NORMAL,
            ),
            (
                "Review src/healing/ error handlers for edge cases",
                TaskTarget.OLLAMA,
                TaskPriority.NORMAL,
            ),
            (
                "Check src/guild/ for missing docstrings and add them",
                TaskTarget.OLLAMA,
                TaskPriority.LOW,
            ),
            # Testing tasks
            (
                "Generate pytest tests for BridgeRegistry class",
                TaskTarget.OLLAMA,
                TaskPriority.HIGH,
            ),
            (
                "Create integration test for BackgroundTaskOrchestrator",
                TaskTarget.OLLAMA,
                TaskPriority.HIGH,
            ),
            # Documentation tasks
            (
                "Generate API documentation for src/orchestration/__init__.py exports",
                TaskTarget.OLLAMA,
                TaskPriority.NORMAL,
            ),
        ]

        submitted = []
        for prompt, target, priority in tasks_to_delegate:
            task = bg.submit_task(
                prompt=prompt,
                target=target,
                priority=priority,
                requesting_agent="system_activator",
                metadata={"batch": "startup_delegation", "auto": True},
            )
            submitted.append(task.task_id)
            logger.info(f"  Delegated: {task.task_id[:25]}...")

        self.log_to_terminal("Tasks", f"Delegated {len(submitted)} startup tasks")
        return submitted

    async def run(self):
        """Execute full system activation."""
        logger.info("=" * 60)
        logger.info("  NUSYQ FULL SYSTEM ACTIVATION")
        logger.info("=" * 60)

        # Activate all subsystems
        stats, caps = await self.activate_orchestration()
        await self.activate_guild_board()
        await self.activate_quest_system()
        await self.activate_healing_systems()
        await self.activate_bridge_registry()
        await self.activate_culture_ship()

        # Delegate startup tasks
        delegated = await self.delegate_startup_tasks()

        # Summary
        logger.info("=" * 60)
        logger.info("  ACTIVATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"  Active Systems: {len(self.active_systems)}")
        logger.info(f"  Queue: {stats['queued']} tasks pending")
        logger.info(f"  AI Capacity: {caps['total_capacity']} concurrent")
        logger.info(f"  New Tasks Delegated: {len(delegated)}")
        logger.info("=" * 60)

        self.log_to_terminal(
            "System",
            f"Full activation complete: {len(self.active_systems)} systems, {len(delegated)} tasks delegated",
        )

        return {
            "systems": list(self.active_systems.keys()),
            "queue_stats": stats,
            "capabilities": caps,
            "delegated_tasks": delegated,
        }


if __name__ == "__main__":
    activator = FullSystemActivator()
    result = asyncio.run(activator.run())
    print(json.dumps(result, indent=2, default=str))
