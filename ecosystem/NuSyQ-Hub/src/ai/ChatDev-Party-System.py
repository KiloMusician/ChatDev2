"""🎭 KILO-FOOLISH ChatDev Party System - Working Version."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

# --- Logging and Bridge Integration ---
try:
    from src.LOGGING.modular_logging_system import log_tagged_event

    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False

if TYPE_CHECKING:
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

try:
    from src.copilot.copilot_enhancement_bridge import get_enhanced_bridge

    BRIDGE_AVAILABLE = True
    bridge: EnhancedCopilotBridge | None = get_enhanced_bridge()
except (ImportError, AttributeError):  # BridgeNotAvailableError -> ImportError
    BRIDGE_AVAILABLE = False
    bridge = None

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    import subprocess

    subprocess.run(["pip", "install", "rich"], check=False)
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

console = Console()


class AgentRole(Enum):
    BUILDER = "🏗️"
    MAINTAINER = "🔧"
    CORRECTOR = "🔍"
    GUIDE = "🧭"
    OPTIMIZER = "⚡"
    CONNECTOR = "🔗"
    INTEGRATOR = "🔄"
    AUGMENTER = "✨"


class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TaskStatus(Enum):
    PENDING = "⏳"
    IN_PROGRESS = "🔄"
    COMPLETED = "✅"
    BLOCKED = "🚫"


@dataclass
class Task:
    task_id: str
    title: str
    description: str
    agent_role: AgentRole
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Agent:
    name: str
    role: AgentRole
    specialty: str
    active: bool = True
    completed_tasks: int = 0
    total_hours: float = 0.0


class ChatDevPartyOrchestrator:
    def __init__(self, repository_root: str = ".") -> None:
        """Initialize ChatDevPartyOrchestrator with repository_root."""
        self.repository_root = Path(repository_root)
        self.agents: dict[str, Agent] = {}
        self.task_queue: deque[Task] = deque()
        self.completed_tasks: list[Task] = []
        self.task_counter = 0
        self.session_start = datetime.now()

        self._initialize_party()

        console.print("[bold magenta]🎭 ChatDev Party Orchestrator Initialized![/bold magenta]")
        console.print(f"[cyan]Repository:[/cyan] {self.repository_root}")
        console.print(f"[green]Active Agents:[/green] {len(self.agents)}")

        # Log orchestrator initialization
        if LOGGING_AVAILABLE:
            log_tagged_event(
                "ChatDevPartyOrchestrator",
                "Orchestrator initialized",
                omnitag={"purpose": "init", "agents": list(self.agents.keys())},
                megatag={"type": "PARTY_SYSTEM", "context": "startup"},
            )
        if BRIDGE_AVAILABLE and bridge:
            bridge.log_event("Orchestrator initialized", tags=["init", "party_system"])

    def _initialize_party(self) -> None:
        party_config = [
            ("Atlas", AgentRole.BUILDER, "System Architecture & New Features"),
            ("Steady", AgentRole.MAINTAINER, "Code Maintenance & Updates"),
            ("Sherlock", AgentRole.CORRECTOR, "Bug Detection & Quality Assurance"),
            ("Compass", AgentRole.GUIDE, "Strategic Direction & Best Practices"),
            ("Turbo", AgentRole.OPTIMIZER, "Performance & Efficiency"),
            ("Bridge", AgentRole.CONNECTOR, "System Integration & APIs"),
            ("Fusion", AgentRole.INTEGRATOR, "Component Integration"),
            ("Nova", AgentRole.AUGMENTER, "Feature Enhancement & Innovation"),
        ]

        for name, role, specialty in party_config:
            agent = Agent(name=name, role=role, specialty=specialty)
            self.agents[name] = agent
            # Log agent creation
            if LOGGING_AVAILABLE:
                log_tagged_event(
                    "ChatDevPartyOrchestrator",
                    f"Agent created: {name}",
                    omnitag={
                        "purpose": "agent_creation",
                        "agent": name,
                        "role": role.name,
                    },
                    megatag={"type": "AGENT", "context": "party_init"},
                )
            if BRIDGE_AVAILABLE and bridge:
                bridge.log_event(f"Agent created: {name}", tags=["agent_creation", role.name])

    def create_task(
        self,
        title: str,
        description: str,
        agent_role: AgentRole,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Task:
        self.task_counter += 1
        task = Task(
            task_id=f"TASK_{self.task_counter:04d}",
            title=title,
            description=description,
            agent_role=agent_role,
            priority=priority,
        )
        self.task_queue.append(task)
        console.print(f"[green]📋 Created task:[/green] {task.task_id} - {task.title}")

        # Log task creation
        if LOGGING_AVAILABLE:
            log_tagged_event(
                "ChatDevPartyOrchestrator",
                f"Task created: {task.task_id}",
                omnitag={
                    "purpose": "task_creation",
                    "task_id": task.task_id,
                    "agent_role": agent_role.name,
                    "priority": priority.name,
                },
                megatag={"type": "TASK", "context": "creation"},
            )
        if BRIDGE_AVAILABLE and bridge:
            bridge.log_event(
                f"Task created: {task.task_id}",
                tags=["task_creation", agent_role.name, priority.name],
            )

        return task

    def log_agent_action(self, agent: Agent, action: str, extra: dict | None = None) -> None:
        """Log any agent action with tags and bridge."""
        tags = ["agent_action", agent.role.name]
        if LOGGING_AVAILABLE:
            log_tagged_event(
                "ChatDevPartyOrchestrator",
                f"Agent action: {agent.name} - {action}",
                omnitag={
                    "purpose": "agent_action",
                    "agent": agent.name,
                    "role": agent.role.name,
                    "action": action,
                    **(extra or {}),
                },
                megatag={"type": "AGENT_ACTION", "context": "runtime"},
            )
        if BRIDGE_AVAILABLE and bridge:
            bridge.log_event(f"Agent action: {agent.name} - {action}", tags=tags)

    def update_task_status(self, task: Task, status: TaskStatus) -> None:
        """Update task status and log the change."""
        old_status = task.status
        task.status = status
        # Log status update
        if LOGGING_AVAILABLE:
            log_tagged_event(
                "ChatDevPartyOrchestrator",
                f"Task status updated: {task.task_id} {old_status.value}→{status.value}",
                omnitag={
                    "purpose": "task_status_update",
                    "task_id": task.task_id,
                    "old_status": old_status.value,
                    "new_status": status.value,
                },
                megatag={"type": "TASK_STATUS", "context": "update"},
            )
        if BRIDGE_AVAILABLE and bridge:
            bridge.log_event(
                f"Task status updated: {task.task_id} {old_status.value}→{status.value}",
                tags=["task_status_update", old_status.value, status.value],
            )

    def display_party_status(self) -> None:
        table = Table(title="🎭 ChatDev Party Status")
        table.add_column("Agent", style="cyan")
        table.add_column("Role", style="magenta")
        table.add_column("Specialty", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Completed", style="blue")
        # ...existing code...

        for agent in self.agents.values():
            status = "💤 Available"
            if not agent.active:
                status = "🚫 Offline"

            table.add_row(
                f"{agent.role.value} {agent.name}",
                agent.role.name,
                agent.specialty,
                status,
                str(agent.completed_tasks),
            )

        console.print(table)

    def create_systematic_build_tasks(self) -> None:
        build_tasks = [
            (
                "Enhanced Error Handling System",
                "Implement comprehensive error handling",
                AgentRole.BUILDER,
                TaskPriority.HIGH,
            ),
            (
                "API Documentation Generator",
                "Build automated API documentation",
                AgentRole.BUILDER,
                TaskPriority.MEDIUM,
            ),
            (
                "Configuration Management Module",
                "Create centralized configuration",
                AgentRole.BUILDER,
                TaskPriority.MEDIUM,
            ),
        ]

        for title, desc, role, priority in build_tasks:
            self.create_task(title, desc, role, priority)

    def create_maintenance_tasks(self) -> None:
        maintenance_tasks = [
            (
                "Dependency Security Audit",
                "Audit dependencies for vulnerabilities",
                AgentRole.MAINTAINER,
                TaskPriority.CRITICAL,
            ),
            (
                "Code Quality Analysis",
                "Run comprehensive code quality analysis",
                AgentRole.MAINTAINER,
                TaskPriority.HIGH,
            ),
        ]

        for title, desc, role, priority in maintenance_tasks:
            self.create_task(title, desc, role, priority)

    def create_optimization_tasks(self) -> None:
        optimization_tasks = [
            (
                "Performance Optimization",
                "Optimize system performance",
                AgentRole.OPTIMIZER,
                TaskPriority.HIGH,
            ),
            (
                "Memory Usage Analysis",
                "Analyze and optimize memory usage",
                AgentRole.OPTIMIZER,
                TaskPriority.MEDIUM,
            ),
        ]

        for title, desc, role, priority in optimization_tasks:
            self.create_task(title, desc, role, priority)

    def create_integration_tasks(self) -> None:
        integration_tasks = [
            (
                "Ollama-ChatDev Bridge",
                "Create Ollama integration",
                AgentRole.INTEGRATOR,
                TaskPriority.HIGH,
            ),
            (
                "VSCode Extension Integration",
                "Integrate with VSCode",
                AgentRole.CONNECTOR,
                TaskPriority.MEDIUM,
            ),
        ]

        for title, desc, role, priority in integration_tasks:
            self.create_task(title, desc, role, priority)

    def create_augmentation_tasks(self) -> None:
        augmentation_tasks = [
            (
                "AI-Powered Code Suggestions",
                "Add AI code completion",
                AgentRole.AUGMENTER,
                TaskPriority.HIGH,
            ),
            (
                "Natural Language Interface",
                "Create natural language interface",
                AgentRole.AUGMENTER,
                TaskPriority.MEDIUM,
            ),
        ]

        for title, desc, role, priority in augmentation_tasks:
            self.create_task(title, desc, role, priority)

    async def run_development_cycle(self) -> None:
        console.print("[bold yellow]🔄 Starting ChatDev Party Development Cycle[/bold yellow]")

        # Simulate task processing
        tasks_to_process = list(self.task_queue)
        self.task_queue.clear()

        for task in tasks_to_process:
            # Find agent for this task
            agent = None
            for a in self.agents.values():
                if a.role == task.agent_role and a.active:
                    agent = a
                    break

            if agent:
                console.print(f"[blue]🔄 {agent.name} working on: {task.title}[/blue]")
                await asyncio.sleep(0.5)  # Simulate work
                task.status = TaskStatus.COMPLETED
                agent.completed_tasks += 1
                self.completed_tasks.append(task)
                console.print(f"[green]✅ {agent.name} completed: {task.title}[/green]")

        console.print("[bold green]✅ Development cycle completed![/bold green]")
        self.display_cycle_summary()

    def display_cycle_summary(self) -> None:
        total_tasks = len(self.completed_tasks)

        console.print(
            Panel.fit(
                f"""
[bold green]🎉 Development Cycle Summary[/bold green]

[cyan]Tasks Completed:[/cyan] {total_tasks}
[cyan]Active Agents:[/cyan] {len([a for a in self.agents.values() if a.active])}
[cyan]Session Duration:[/cyan] {(datetime.now() - self.session_start).total_seconds():.0f}s
            """,
                title="ChatDev Party Results",
            )
        )


def main() -> None:
    console.print("[bold magenta]🚀 Launching ChatDev Party System![/bold magenta]")

    # Initialize orchestrator
    orchestrator = ChatDevPartyOrchestrator()

    # Show party status
    orchestrator.display_party_status()

    # Create tasks
    console.print("\n[bold cyan]📋 Creating comprehensive task set...[/bold cyan]")
    orchestrator.create_systematic_build_tasks()
    orchestrator.create_maintenance_tasks()
    orchestrator.create_optimization_tasks()
    orchestrator.create_integration_tasks()
    orchestrator.create_augmentation_tasks()

    console.print(f"\n[bold green]✅ Created {len(orchestrator.task_queue)} tasks![/bold green]")

    # Run development cycle
    console.print("\n[bold yellow]🔄 Running development cycle...[/bold yellow]")
    asyncio.run(orchestrator.run_development_cycle())

    # Final status
    orchestrator.display_party_status()

    console.print(
        "\n[bold green]🎭 ChatDev Party System ready for repository evolution![/bold green]"
    )


if __name__ == "__main__":
    main()
