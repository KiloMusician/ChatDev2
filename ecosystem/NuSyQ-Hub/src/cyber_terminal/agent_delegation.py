"""Agent delegation and orchestration for Terminal Depths.
Routes Terminal Depths commands through the NuSyQ agent system.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Literal, Optional

logger = logging.getLogger(__name__)


class TerminalDepthsCommand(Enum):
    """Available Terminal Depths commands that can be delegated."""

    PWD = "pwd"
    LS = "ls"
    CD = "cd"
    CAT = "cat"
    TASKS = "tasks"
    MISSIONS = "missions"
    MISSION_START = "mission"
    HACK = "hack"
    SCAN = "scan"
    CONNECT = "connect"
    DOWNLOAD = "download"
    EXECUTE = "execute"


class AgentRole(Enum):
    """Agent roles for Terminal Depths operations."""

    NAVIGATOR = "navigator"  # File system navigation
    HACKER = "hacker"  # Hacking operations
    ANALYST = "analyst"  # Mission analysis
    EXECUTOR = "executor"  # Command execution
    ORCHESTRATOR = "orchestrator"  # Overall coordination


@dataclass
class TerminalDepthsTask:
    """A Terminal Depths command delegated to an agent."""

    id: str
    command: TerminalDepthsCommand
    args: list[str]
    agent_role: AgentRole
    priority: Literal["low", "normal", "high"] = "normal"
    context_tags: list[str] = None
    session_id: str | None = None

    def __post_init__(self):
        if self.context_tags is None:
            self.context_tags = []
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "command": self.command.value,
            "args": self.args,
            "agent_role": self.agent_role.value,
            "priority": self.priority,
            "context_tags": self.context_tags,
            "session_id": self.session_id,
        }


@dataclass
class TerminalDepthsResult:
    """Result from a delegated Terminal Depths command."""

    task_id: str
    success: bool
    output: str
    agent_name: str
    execution_time_ms: float
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "output": self.output,
            "agent_name": self.agent_name,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }


class TerminalDepthsOrchestrator:
    """Orchestrates Terminal Depths commands across agent network.
    Routes commands to appropriate agents based on role and capability.
    """

    def __init__(self, orchestrator_endpoint: str = "http://localhost:8000"):
        self.orchestrator_endpoint = orchestrator_endpoint
        self.task_queue: list[TerminalDepthsTask] = []
        self.results: dict[str, TerminalDepthsResult] = {}
        self.agent_registry: dict[AgentRole, list[str]] = {
            AgentRole.NAVIGATOR: ["Serena", "Ada"],
            AgentRole.HACKER: ["RAV≡N", "Cypher", "Gordon"],
            AgentRole.ANALYST: ["The Librarian", "Zod"],
            AgentRole.EXECUTOR: ["Culture Ship", "System"],
            AgentRole.ORCHESTRATOR: ["AI Council"],
        }

    def route_command(
        self,
        command: str,
        args: list[str] = None,
        session_id: str | None = None,
        priority: str = "normal",
    ) -> TerminalDepthsTask:
        """Route a Terminal Depths command to the appropriate agent.

        Args:
            command: Terminal Depths command name
            args: Command arguments
            session_id: Session identifier
            priority: Task priority

        Returns:
            TerminalDepthsTask routed to agent
        """
        if args is None:
            args = []

        # Determine command and agent role
        cmd_enum = self._parse_command(command)
        role = self._determine_agent_role(cmd_enum)

        # Create task
        task = TerminalDepthsTask(
            id="",  # Will be auto-generated
            command=cmd_enum,
            args=args,
            agent_role=role,
            priority=priority,
            session_id=session_id,
        )

        # Queue task
        self.task_queue.append(task)
        logger.info(f"📋 Queued {command} for {role.value}: {task.id}")

        return task

    def _parse_command(self, command: str) -> TerminalDepthsCommand:
        """Parse string command to enum."""
        cmd_map = {
            "pwd": TerminalDepthsCommand.PWD,
            "ls": TerminalDepthsCommand.LS,
            "cd": TerminalDepthsCommand.CD,
            "cat": TerminalDepthsCommand.CAT,
            "tasks": TerminalDepthsCommand.TASKS,
            "missions": TerminalDepthsCommand.MISSIONS,
            "mission": TerminalDepthsCommand.MISSION_START,
            "hack": TerminalDepthsCommand.HACK,
            "scan": TerminalDepthsCommand.SCAN,
            "connect": TerminalDepthsCommand.CONNECT,
            "download": TerminalDepthsCommand.DOWNLOAD,
            "execute": TerminalDepthsCommand.EXECUTE,
        }
        return cmd_map.get(command.lower(), TerminalDepthsCommand.EXECUTE)

    def _determine_agent_role(self, command: TerminalDepthsCommand) -> AgentRole:
        """Determine which agent role best handles this command."""
        role_map = {
            TerminalDepthsCommand.PWD: AgentRole.NAVIGATOR,
            TerminalDepthsCommand.LS: AgentRole.NAVIGATOR,
            TerminalDepthsCommand.CD: AgentRole.NAVIGATOR,
            TerminalDepthsCommand.CAT: AgentRole.NAVIGATOR,
            TerminalDepthsCommand.TASKS: AgentRole.ANALYST,
            TerminalDepthsCommand.MISSIONS: AgentRole.ANALYST,
            TerminalDepthsCommand.MISSION_START: AgentRole.ANALYST,
            TerminalDepthsCommand.HACK: AgentRole.HACKER,
            TerminalDepthsCommand.SCAN: AgentRole.HACKER,
            TerminalDepthsCommand.CONNECT: AgentRole.HACKER,
            TerminalDepthsCommand.DOWNLOAD: AgentRole.HACKER,
            TerminalDepthsCommand.EXECUTE: AgentRole.EXECUTOR,
        }
        return role_map.get(command, AgentRole.EXECUTOR)

    async def dispatch_task(self, task: TerminalDepthsTask) -> TerminalDepthsResult:
        """Dispatch a task to an available agent.

        Args:
            task: TerminalDepthsTask to dispatch

        Returns:
            TerminalDepthsResult from agent execution
        """
        agents = self.agent_registry.get(task.agent_role, ["System"])
        agent_name = agents[0]  # TODO: load balance

        logger.info(f"🚀 Dispatching {task.command.value} to {agent_name}")

        # Simulate execution (replace with actual agent call)
        import time

        start = time.time()

        # For now, simulate execution
        output = f"[{agent_name}] {task.command.value} {' '.join(task.args)}"

        elapsed_ms = (time.time() - start) * 1000

        result = TerminalDepthsResult(
            task_id=task.id,
            success=True,
            output=output,
            agent_name=agent_name,
            execution_time_ms=elapsed_ms,
            metadata={
                "role": task.agent_role.value,
                "priority": task.priority,
            },
        )

        self.results[task.id] = result
        logger.info(f"✅ Task {task.id} completed by {agent_name}")

        return result

    async def execute_queue(self) -> list[TerminalDepthsResult]:
        """Execute all queued tasks."""
        results = []
        for task in self.task_queue:
            result = await self.dispatch_task(task)
            results.append(result)
        self.task_queue.clear()
        return results

    def get_task_status(self, task_id: str) -> dict | None:
        """Get status of a task."""
        if task_id in self.results:
            return self.results[task_id].to_dict()

        # Check queue
        for task in self.task_queue:
            if task.id == task_id:
                return {
                    "task_id": task.id,
                    "status": "queued",
                    "command": task.command.value,
                }

        return None

    def get_agent_registry(self) -> dict:
        """Get current agent registry."""
        return {role.value: agents for role, agents in self.agent_registry.items()}


# Global orchestrator instance
_orchestrator: TerminalDepthsOrchestrator | None = None


def get_orchestrator(endpoint: str = "http://localhost:8000") -> TerminalDepthsOrchestrator:
    """Get or create global orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TerminalDepthsOrchestrator(endpoint)
    return _orchestrator


async def delegate_command(
    command: str, args: list[str] = None, session_id: str | None = None, wait: bool = True
) -> TerminalDepthsResult:
    """Delegate a Terminal Depths command to an agent.

    Args:
        command: Command name (pwd, ls, cd, etc.)
        args: Command arguments
        session_id: Session ID
        wait: Wait for completion

    Returns:
        TerminalDepthsResult

    Example:
        result = await delegate_command("pwd")
        print(result.output)
    """
    orchestrator = get_orchestrator()
    task = orchestrator.route_command(command, args, session_id)

    if wait:
        return await orchestrator.dispatch_task(task)
    else:
        return task


def delegate_command_sync(
    command: str, args: list[str] = None, session_id: str | None = None
) -> TerminalDepthsResult:
    """Synchronous wrapper for delegation."""
    return asyncio.run(delegate_command(command, args, session_id))


if __name__ == "__main__":
    # Demo
    import asyncio

    async def demo():
        """Demo agent delegation."""
        orchestrator = get_orchestrator()

        # Queue some commands
        print("📋 Queuing Terminal Depths commands...")
        orchestrator.route_command("pwd")
        orchestrator.route_command("ls", session_id="demo")
        orchestrator.route_command("hack", session_id="demo")
        orchestrator.route_command("scan", session_id="demo")

        # Execute queue
        print("\n🚀 Executing queue...")
        results = await orchestrator.execute_queue()

        print("\n✅ Results:")
        for result in results:
            print(f"  {result.agent_name}: {result.output} ({result.execution_time_ms:.1f}ms)")

        # Show registry
        print("\n📊 Agent Registry:")
        for role, agents in orchestrator.get_agent_registry().items():
            print(f"  {role}: {', '.join(agents)}")

    asyncio.run(demo())
