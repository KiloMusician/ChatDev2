"""Unified Orchestration Bridge - Inter-agent communication and task routing.

This module provides a unified interface for orchestrating tasks across multiple
AI agents and tools in the NuSyQ ecosystem. It enables:

- Task decomposition and routing
- Agent collaboration workflows
- Cross-platform communication (Claude ↔ Ollama ↔ ChatDev ↔ Continue ↔ Jupyter)
- Resource management and load balancing
- Failure recovery and fallback strategies

Architecture Layers:
1. Task Layer: High-level task definition and decomposition
2. Routing Layer: Intelligent agent selection and task distribution
3. Execution Layer: Agent lifecycle management and monitoring
4. Communication Layer: Inter-agent message passing and state synchronization
5. Persistence Layer: Execution history and learning

OmniTag: orchestration_bridge, multi_agent, task_routing
MegaTag: UNIFIED_ORCHESTRATION, AGENT_MESH, CROSS_PLATFORM_COORDINATION
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.orchestration.agent_registry import (RegisteredAgent,
                                              get_agent_registry)

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(Enum):
    """Supported agent types."""

    CLAUDE = "claude"
    OLLAMA = "ollama"
    CHATDEV = "chatdev"
    CONTINUE = "continue"
    JUPYTER = "jupyter"
    DOCKER = "docker"
    CUSTOM = "custom"


@dataclass
class Task:
    """Represents a task to be executed by one or more agents."""

    task_id: str
    description: str
    required_capabilities: list[str]
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    assigned_agents: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    subtasks: list[str] = field(default_factory=list)  # IDs of subtasks
    parent_task: str | None = None
    priority: int = 5  # 1-10, higher = more urgent


@dataclass
class ExecutionResult:
    """Result of task execution."""

    task_id: str
    success: bool
    output: Any
    error: str | None = None
    duration_seconds: float = 0.0
    agent_used: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class UnifiedOrchestrationBridge:
    """Unified bridge for orchestrating tasks across multiple AI agents."""

    def __init__(self, execution_log_path: Path | None = None) -> None:
        """Initialize UnifiedOrchestrationBridge with execution_log_path."""
        self.registry = get_agent_registry()
        self.tasks: dict[str, Task] = {}
        self.execution_history: list[ExecutionResult] = []
        self.execution_log_path = execution_log_path or Path(
            "data/orchestration/execution_log.jsonl"
        )

        # Agent-specific executors
        self.executors: dict[str, Callable] = {
            AgentType.OLLAMA.value: self._execute_ollama_task,
            AgentType.CHATDEV.value: self._execute_chatdev_task,
            AgentType.CONTINUE.value: self._execute_continue_task,
            AgentType.JUPYTER.value: self._execute_jupyter_task,
            AgentType.DOCKER.value: self._execute_docker_task,
            AgentType.CLAUDE.value: self._execute_claude_task,
        }

        # Collaboration patterns
        self.collaboration_patterns = {
            "sequential": self._execute_sequential,
            "parallel": self._execute_parallel,
            "hierarchical": self._execute_hierarchical,
            "consensus": self._execute_consensus,
        }

        logger.info("🌉 Unified Orchestration Bridge initialized")

    @staticmethod
    def _status_implies_success(status: str | None) -> bool:
        """Map mixed status values to a stable success signal."""
        if not status:
            return False
        return str(status).strip().lower() in {
            "success",
            "ok",
            "completed",
            "acknowledged",
            "delegated",
            "delegated_to_continue",
            "submitted",
            "operational",
            "partial_success",
        }

    @classmethod
    def _normalize_response_contract(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """Ensure orchestration boundaries always include status and success."""
        normalized = dict(payload)
        status = normalized.get("status")
        if not isinstance(status, str) or not status.strip():
            if "success" in normalized:
                status = "success" if bool(normalized["success"]) else "failed"
            elif normalized.get("error"):
                status = "failed"
            else:
                status = "success"
            normalized["status"] = status

        if "success" not in normalized:
            normalized["success"] = cls._status_implies_success(str(normalized["status"]))

        return normalized

    @classmethod
    def _response_succeeded(cls, payload: dict[str, Any]) -> bool:
        """Treat explicit success or success-like status as successful."""
        if "success" in payload:
            return bool(payload["success"])
        return cls._status_implies_success(payload.get("status"))

    def create_task(
        self,
        description: str,
        required_capabilities: list[str],
        input_data: dict[str, Any] | None = None,
        priority: int = 5,
        metadata: dict[str, Any] | None = None,
    ) -> Task:
        """Create a new task."""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        task = Task(
            task_id=task_id,
            description=description,
            required_capabilities=required_capabilities,
            input_data=input_data or {},
            priority=priority,
            metadata=metadata or {},
        )

        self.tasks[task_id] = task
        logger.info(f"📝 Created task {task_id}: {description}")

        return task

    def execute_task(
        self, task: Task, prefer_local: bool = True, timeout_seconds: int | None = None
    ) -> ExecutionResult:
        """Execute a task using the best available agent."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()

        start_time = time.time()

        try:
            # Find best agent for task
            agent = self.registry.find_best_agent_for_task(
                required_capabilities=task.required_capabilities,
                task_complexity=task.metadata.get("complexity", "medium"),
                prefer_local=prefer_local,
            )

            if not agent:
                raise RuntimeError(
                    f"No available agent found for capabilities: {task.required_capabilities}"
                )

            task.assigned_agents.append(agent.agent_id)
            logger.info(f"🎯 Assigned task {task.task_id} to agent {agent.name}")

            # Update agent status
            self.registry.update_agent_status(agent.agent_id, "busy")

            # Execute task using agent-specific executor
            executor = self.executors.get(agent.agent_type, self._execute_generic_task)
            output = executor(task, agent, timeout_seconds)
            if isinstance(output, dict):
                output = self._normalize_response_contract(output)

            execution_success = (
                self._response_succeeded(output) if isinstance(output, dict) else True
            )

            if not execution_success:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now().isoformat()
                task.output_data = output if isinstance(output, dict) else {}
                task.error = (
                    output.get("error", f"Agent returned status={output.get('status')}")
                    if isinstance(output, dict)
                    else "Agent execution returned failure-like output"
                )

                duration = time.time() - start_time
                result = ExecutionResult(
                    task_id=task.task_id,
                    success=False,
                    output=output,
                    error=task.error,
                    duration_seconds=duration,
                    agent_used=agent.agent_id,
                    metadata={
                        "agent_name": agent.name,
                        "agent_type": agent.agent_type,
                        "capabilities_used": task.required_capabilities,
                    },
                )

                self.registry.record_execution(agent.agent_id, False, duration)
                self.registry.update_agent_status(agent.agent_id, "idle")
                self._log_execution(result)
                logger.warning(
                    "⚠️ Task %s completed with failure contract from %s",
                    task.task_id,
                    agent.name,
                )
                return result

            # Mark success
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()
            task.output_data = output if isinstance(output, dict) else {"result": output}

            duration = time.time() - start_time

            result = ExecutionResult(
                task_id=task.task_id,
                success=True,
                output=output,
                duration_seconds=duration,
                agent_used=agent.agent_id,
                metadata={
                    "agent_name": agent.name,
                    "agent_type": agent.agent_type,
                    "capabilities_used": task.required_capabilities,
                },
            )

            # Record metrics
            self.registry.record_execution(agent.agent_id, True, duration)
            self.registry.update_agent_status(agent.agent_id, "idle")

            self._log_execution(result)

            logger.info(f"✅ Task {task.task_id} completed in {duration:.2f}s using {agent.name}")

            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now().isoformat()
            task.error = str(e)

            duration = time.time() - start_time

            result = ExecutionResult(
                task_id=task.task_id,
                success=False,
                output=None,
                error=str(e),
                duration_seconds=duration,
                agent_used=task.assigned_agents[-1] if task.assigned_agents else None,
            )

            if task.assigned_agents:
                self.registry.record_execution(task.assigned_agents[-1], False, duration)
                self.registry.update_agent_status(task.assigned_agents[-1], "idle")

            self._log_execution(result)

            logger.error(f"❌ Task {task.task_id} failed: {e}")

            return result

    def execute_collaborative_task(
        self, task: Task, pattern: str = "parallel", agents: list[str] | None = None
    ) -> ExecutionResult:
        """Execute a task using multiple agents in collaboration."""
        if pattern not in self.collaboration_patterns:
            raise ValueError(f"Unknown collaboration pattern: {pattern}")

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()

        start_time = time.time()

        try:
            # Execute using pattern
            executor = self.collaboration_patterns[pattern]
            output = executor(task, agents)
            if isinstance(output, dict):
                output = self._normalize_response_contract(output)

            execution_success = (
                self._response_succeeded(output) if isinstance(output, dict) else True
            )

            task.status = TaskStatus.COMPLETED if execution_success else TaskStatus.FAILED
            task.completed_at = datetime.now().isoformat()
            task.output_data = output if isinstance(output, dict) else {"result": output}
            task.error = None
            if not execution_success:
                task.error = (
                    output.get("error", f"Collaborative pattern returned {output.get('status')}")
                    if isinstance(output, dict)
                    else "Collaborative execution returned failure-like output"
                )

            duration = time.time() - start_time

            result = ExecutionResult(
                task_id=task.task_id,
                success=execution_success,
                output=output,
                error=task.error,
                duration_seconds=duration,
                agent_used=",".join(task.assigned_agents),
                metadata={
                    "pattern": pattern,
                    "agents_count": len(task.assigned_agents),
                },
            )

            self._log_execution(result)

            if execution_success:
                logger.info(
                    f"✅ Collaborative task {task.task_id} completed using {pattern} pattern"
                )
            else:
                logger.warning(
                    "⚠️ Collaborative task %s returned failure contract using %s pattern",
                    task.task_id,
                    pattern,
                )

            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            duration = time.time() - start_time

            result = ExecutionResult(
                task_id=task.task_id,
                success=False,
                output=None,
                error=str(e),
                duration_seconds=duration,
            )

            self._log_execution(result)

            return result

    # Agent-specific executors

    def _execute_ollama_task(
        self, task: Task, agent: RegisteredAgent, timeout_seconds: int | None
    ) -> dict[str, Any]:
        """Execute task using Ollama."""
        del agent, timeout_seconds
        try:
            # Import Ollama integration
            from src.integration.Ollama_Integration_Hub import KILOOllamaHub

            hub = KILOOllamaHub()

            # Determine which capability to use
            prompt = task.input_data.get("prompt", task.description)
            model = task.input_data.get("model")

            response = hub.chat(
                message=prompt,
                model=model,
                context_length=task.input_data.get("context_length", 5),
            )

            response_success = response.success if hasattr(response, "success") else True
            return self._normalize_response_contract(
                {
                    "status": "success" if response_success else "failed",
                    "response": (
                        response.message if hasattr(response, "message") else str(response)
                    ),
                    "model_used": response.model if hasattr(response, "model") else model,
                    "success": bool(response_success),
                }
            )

        except Exception as e:
            logger.error(f"Ollama execution failed: {e}")
            raise

    def _execute_chatdev_task(
        self, task: Task, agent: RegisteredAgent, timeout_seconds: int | None
    ) -> dict[str, Any]:
        """Execute task using ChatDev."""
        del agent, timeout_seconds
        try:
            from src.integration.chatdev_integration import \
                ChatDevIntegrationManager

            manager = ChatDevIntegrationManager()

            # Determine task type
            if "code_review" in task.required_capabilities:
                result = manager.collaborative_code_review(
                    files=task.input_data.get("files", []),
                    focus_areas=task.input_data.get("focus_areas", []),
                )
            elif "architecture_design" in task.required_capabilities:
                result = manager.design_system_architecture(
                    requirements=task.input_data.get("requirements", task.description)
                )
            else:
                # Generic multi-agent execution
                result = manager.execute_multi_agent_task(
                    description=task.description,
                    agents=task.input_data.get("agents", ["CEO", "CTO", "Programmer"]),
                )

            if isinstance(result, dict):
                return self._normalize_response_contract(result)
            return self._normalize_response_contract(
                {"status": "success", "success": True, "result": result}
            )

        except Exception as e:
            logger.error(f"ChatDev execution failed: {e}")
            raise

    def _execute_continue_task(
        self, task: Task, agent: RegisteredAgent, timeout_seconds: int | None
    ) -> dict[str, Any]:
        """Execute task using Continue extension."""
        del agent, timeout_seconds
        # Note: Continue is a VS Code extension, so we simulate interaction
        # In practice, this would interact with Continue's API or file-based interface

        return self._normalize_response_contract(
            {
                "status": "delegated_to_continue",
                "message": "Task delegated to Continue VS Code extension",
                "task_description": task.description,
                "note": "User should execute this in VS Code using Continue extension",
            }
        )

    def _execute_jupyter_task(
        self, task: Task, agent: RegisteredAgent, timeout_seconds: int | None
    ) -> dict[str, Any]:
        """Execute task using Jupyter."""
        del agent
        try:
            # Execute Jupyter notebook
            notebook_path = task.input_data.get("notebook_path")

            if not notebook_path:
                raise ValueError("notebook_path required for Jupyter tasks")

            import subprocess
            import sys

            # Execute notebook and capture output
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "jupyter",
                    "nbconvert",
                    "--to",
                    "notebook",
                    "--execute",
                    "--inplace",
                    notebook_path,
                ],
                capture_output=True,
                text=True,
                timeout=timeout_seconds or 300,
                check=False,
            )

            run_success = result.returncode == 0
            return self._normalize_response_contract(
                {
                    "status": "success" if run_success else "failed",
                    "success": run_success,
                    "notebook_path": notebook_path,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )

        except Exception as e:
            logger.error(f"Jupyter execution failed: {e}")
            raise

    def _execute_docker_task(
        self, task: Task, agent: RegisteredAgent, timeout_seconds: int | None
    ) -> dict[str, Any]:
        """Execute task using Docker."""
        del agent
        try:
            import subprocess

            action = task.input_data.get("action", "status")

            if action == "status":
                result = subprocess.run(
                    ["docker", "ps", "-a"],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds or 30,
                    check=True,
                )
                return self._normalize_response_contract(
                    {"status": "success", "success": True, "output": result.stdout}
                )

            elif action == "compose_up":
                compose_file = task.input_data.get("compose_file", "deploy/docker-compose.yml")
                result = subprocess.run(
                    ["docker-compose", "-f", compose_file, "up", "-d"],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds or 120,
                    check=True,
                )
                return self._normalize_response_contract(
                    {"status": "success", "success": True, "output": result.stdout}
                )

            else:
                raise ValueError(f"Unknown Docker action: {action}")

        except Exception as e:
            logger.error(f"Docker execution failed: {e}")
            raise

    def _execute_claude_task(
        self, task: Task, agent: RegisteredAgent, timeout_seconds: int | None
    ) -> dict[str, Any]:
        """Execute task using Claude (self-referential for delegation)."""
        del agent, timeout_seconds
        # This allows tasks to be explicitly delegated to Claude for reasoning

        return self._normalize_response_contract(
            {
                "status": "acknowledged",
                "message": "Task acknowledged by Claude orchestrator",
                "task_description": task.description,
                "note": "This is a meta-task handled by Claude's reasoning capabilities",
            }
        )

    def _execute_generic_task(
        self, task: Task, agent: RegisteredAgent, timeout_seconds: int | None
    ) -> dict[str, Any]:
        """Fallback executor for unknown agent types."""
        del task, timeout_seconds
        logger.warning(f"Using generic executor for agent type: {agent.agent_type}")

        return self._normalize_response_contract(
            {
                "status": "delegated",
                "agent": agent.name,
                "message": f"Task delegated to {agent.name}",
                "requires_manual_execution": True,
            }
        )

    # Collaboration patterns

    def _execute_sequential(self, task: Task, agents: list[str] | None) -> dict[str, Any]:
        """Execute task sequentially across multiple agents."""
        results = []
        current_input = task.input_data

        agent_ids = agents or [
            self.registry.find_best_agent_for_task([cap], prefer_local=True).agent_id
            for cap in task.required_capabilities
        ]

        for agent_id in agent_ids:
            agent = self.registry.get_agent(agent_id)
            if not agent:
                continue

            subtask = Task(
                task_id=f"{task.task_id}_step_{len(results)}",
                description=f"Sequential step {len(results)} of {task.description}",
                required_capabilities=task.required_capabilities,
                input_data=current_input,
                parent_task=task.task_id,
            )

            executor = self.executors.get(agent.agent_type, self._execute_generic_task)
            output = executor(subtask, agent, None)

            results.append(output)
            current_input = output  # Chain output to next input

            task.assigned_agents.append(agent_id)

        return self._normalize_response_contract(
            {
                "status": "success",
                "pattern": "sequential",
                "steps": results,
                "final_output": results[-1] if results else None,
            }
        )

    def _execute_parallel(self, task: Task, agents: list[str] | None) -> dict[str, Any]:
        """Execute task in parallel across multiple agents."""
        # Note: This would use asyncio for true parallelism
        # For now, simulating parallel execution

        results = []

        agent_ids = agents or [
            self.registry.find_best_agent_for_task([cap], prefer_local=True).agent_id
            for cap in task.required_capabilities
        ]

        for i, agent_id in enumerate(agent_ids):
            agent = self.registry.get_agent(agent_id)
            if not agent:
                continue

            subtask = Task(
                task_id=f"{task.task_id}_parallel_{i}",
                description=f"Parallel instance {i} of {task.description}",
                required_capabilities=task.required_capabilities,
                input_data=task.input_data,
                parent_task=task.task_id,
            )

            executor = self.executors.get(agent.agent_type, self._execute_generic_task)
            output = executor(subtask, agent, None)

            results.append({"agent": agent.name, "output": output})

            task.assigned_agents.append(agent_id)

        return self._normalize_response_contract(
            {
                "status": "success",
                "pattern": "parallel",
                "results": results,
                "aggregated": self._aggregate_parallel_results(results),
            }
        )

    def _execute_hierarchical(self, task: Task, agents: list[str] | None) -> dict[str, Any]:
        """Execute task with hierarchical coordination."""
        del agents
        # Main agent coordinates, others assist

        return self._normalize_response_contract(
            {
                "status": "acknowledged",
                "pattern": "hierarchical",
                "note": "Hierarchical pattern not yet fully implemented",
                "task_id": task.task_id,
            }
        )

    def _execute_consensus(self, task: Task, agents: list[str] | None) -> dict[str, Any]:
        """Execute task and reach consensus among multiple agents."""
        del agents
        # Get multiple perspectives and synthesize

        return self._normalize_response_contract(
            {
                "status": "acknowledged",
                "pattern": "consensus",
                "note": "Consensus pattern not yet fully implemented",
                "task_id": task.task_id,
            }
        )

    def _aggregate_parallel_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate results from parallel execution."""
        # Simple aggregation - can be enhanced with voting, averaging, etc.

        return {
            "total_agents": len(results),
            "all_results": results,
            "strategy": "collect_all",
        }

    def _log_execution(self, result: ExecutionResult) -> None:
        """Log execution result to persistent storage."""
        try:
            self.execution_log_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.execution_log_path, "a", encoding="utf-8") as f:
                log_entry = {
                    **asdict(result),
                    "output": str(result.output)[:1000],  # Truncate large outputs
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

            self.execution_history.append(result)

            # Keep only recent history in memory
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-500:]

        except Exception as e:
            logger.error(f"Failed to log execution: {e}")

    def get_task_status(self, task_id: str) -> Task | None:
        """Get current status of a task."""
        return self.tasks.get(task_id)

    def get_execution_stats(self) -> dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_history:
            return {"total_executions": 0}

        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)

        return {
            "total_executions": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "average_duration": sum(r.duration_seconds for r in self.execution_history) / total,
            "agents_used": len({r.agent_used for r in self.execution_history if r.agent_used}),
        }


# Global bridge instance
_bridge: UnifiedOrchestrationBridge | None = None


def get_orchestration_bridge() -> UnifiedOrchestrationBridge:
    """Get or create the global orchestration bridge."""
    global _bridge
    if _bridge is None:
        _bridge = UnifiedOrchestrationBridge()
    return _bridge
