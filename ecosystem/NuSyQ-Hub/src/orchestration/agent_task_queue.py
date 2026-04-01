#!/usr/bin/env python3
"""Agent Task Queue - Real-time task assignment and execution coordination.

Implements the actual task queue mechanism that was missing from the system:
- Tasks pulled from error reports and work queues
- Automatic assignment based on agent capabilities
- Real-time execution tracking and status updates
- Task dependency management
- Result capture and integration

This is the critical missing link between "error detected" and "agent working".
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from src.utils.session_checkpoint import SessionCheckpoint
except ImportError:  # pragma: no cover - optional during isolated runtime use
    SessionCheckpoint = None  # type: ignore[assignment]


DEFAULT_MAX_RETRIES = int(os.getenv("NUSYQ_TASK_QUEUE_MAX_RETRIES", "2"))
RETRY_BASE_SECONDS = int(os.getenv("NUSYQ_TASK_QUEUE_RETRY_BASE_SECONDS", "30"))
MAX_RETRY_DELAY_SECONDS = int(os.getenv("NUSYQ_TASK_QUEUE_MAX_RETRY_DELAY_SECONDS", "1800"))


class TaskStatus(Enum):
    """Task execution status."""

    CREATED = "created"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""

    CRITICAL = 1  # Fix immediately
    HIGH = 2  # Fix within 1 hour
    NORMAL = 3  # Fix within 8 hours
    LOW = 4  # Fix within 24 hours
    BACKGROUND = 5  # When time permits


class TaskType(Enum):
    """Types of tasks agents can perform."""

    CODE_FIX = "code_fix"  # Fix code issues
    TEST = "test"  # Run tests
    REVIEW = "review"  # Review code
    REFACTOR = "refactor"  # Refactor code
    DOCUMENTATION = "documentation"  # Write docs
    ANALYSIS = "analysis"  # Analyze code/system
    OPTIMIZATION = "optimization"  # Optimize performance
    OTHER = "other"


@dataclass
class TaskDependency:
    """Represents a dependency on another task."""

    task_id: str
    required_status: TaskStatus = TaskStatus.COMPLETED


@dataclass
class AgentAssignment:
    """Assignment of a task to an agent."""

    agent_id: str
    agent_name: str
    assigned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    result: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTask:
    """A task to be executed by an agent."""

    task_id: str
    task_type: TaskType
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.CREATED
    source: str = "system"  # Where this task came from (error_report, work_queue, manual, etc.)
    source_ref: str = ""  # Reference to source (error ID, quest ID, etc.)
    assigned_agent: AgentAssignment | None = None
    capabilities_required: list[str] = field(default_factory=list)
    estimated_duration_minutes: int = 30
    dependencies: list[TaskDependency] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)  # Output paths
    retry_count: int = 0
    max_retries: int = DEFAULT_MAX_RETRIES
    next_retry_at: str | None = None
    last_error: str = ""
    checkpoint_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    due_at: str | None = None
    completed_at: str | None = None

    def has_dependencies_met(self, completed_tasks: dict[str, AgentTask]) -> bool:
        """Check if all dependencies are satisfied.

        Args:
            completed_tasks: Dictionary of task_id -> completed tasks

        Returns:
            True if all dependencies met, False otherwise
        """
        for dep in self.dependencies:
            if dep.task_id not in completed_tasks:
                return False
            task = completed_tasks[dep.task_id]
            if task.status != dep.required_status:
                return False
        return True

    def is_overdue(self) -> bool:
        """Check if task is past its due date."""
        if not self.due_at:
            return False
        return datetime.now() > datetime.fromisoformat(self.due_at)


class AgentTaskQueue:
    """Manages task queue and assignment for agents."""

    def __init__(self, queue_dir: Path | str = "state/task_queue"):
        """Initialize the task queue.

        Args:
            queue_dir: Directory to store queue state
        """
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)

        self.tasks_file = self.queue_dir / "tasks.jsonl"
        self.assignments_file = self.queue_dir / "assignments.jsonl"
        self.completed_file = self.queue_dir / "completed.jsonl"
        self._checkpoint_dir = self.queue_dir / "checkpoints"

        # In-memory caches
        self._tasks: dict[str, AgentTask] = {}
        self._completed_tasks: dict[str, AgentTask] = {}
        self._agent_registry: dict[str, dict[str, Any]] = {}
        self._checkpoint_manager: Any | None = None
        if SessionCheckpoint is not None:
            try:
                self._checkpoint_manager = SessionCheckpoint(
                    checkpoint_dir=self._checkpoint_dir,
                    agent_name="agent_task_queue",
                    max_checkpoints=25,
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to initialize task queue checkpoint manager: %s", exc)
                self._checkpoint_manager = None

        self._load_tasks()

    def _load_tasks(self) -> None:
        """Load tasks from persistence."""
        try:
            if self.tasks_file.exists():
                for line in self.tasks_file.read_text().strip().split("\n"):
                    if line.strip():
                        data = json.loads(line)
                        self._tasks[data["task_id"]] = self._deserialize_task(data)

            if self.completed_file.exists():
                for line in self.completed_file.read_text().strip().split("\n"):
                    if line.strip():
                        data = json.loads(line)
                        self._completed_tasks[data["task_id"]] = self._deserialize_task(data)
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.error(f"Failed to load tasks: {e}")

    def _deserialize_task(self, data: dict[str, Any]) -> AgentTask:
        """Deserialize a task from JSON."""
        task = AgentTask(
            task_id=data["task_id"],
            task_type=TaskType(data["task_type"]),
            title=data["title"],
            description=data["description"],
            priority=TaskPriority(data["priority"]),
            status=TaskStatus(data.get("status", "created")),
            source=data.get("source", "system"),
            source_ref=data.get("source_ref", ""),
            capabilities_required=data.get("capabilities_required", []),
            estimated_duration_minutes=data.get("estimated_duration_minutes", 30),
            artifacts=data.get("artifacts", []),
            retry_count=int(data.get("retry_count", 0) or 0),
            max_retries=max(0, int(data.get("max_retries", DEFAULT_MAX_RETRIES) or 0)),
            next_retry_at=data.get("next_retry_at"),
            last_error=data.get("last_error", ""),
            checkpoint_id=data.get("checkpoint_id"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            due_at=data.get("due_at"),
            completed_at=data.get("completed_at"),
        )

        # Reconstruct dependencies
        for dep_data in data.get("dependencies", []):
            dep = TaskDependency(
                task_id=dep_data["task_id"],
                required_status=TaskStatus(dep_data.get("required_status", "completed")),
            )
            task.dependencies.append(dep)

        # Reconstruct assignment
        if data.get("assigned_agent"):
            assign_data = data["assigned_agent"]
            task.assigned_agent = AgentAssignment(
                agent_id=assign_data["agent_id"],
                agent_name=assign_data["agent_name"],
                assigned_at=assign_data.get("assigned_at", datetime.now().isoformat()),
                started_at=assign_data.get("started_at"),
                completed_at=assign_data.get("completed_at"),
                result=assign_data.get("result", {}),
            )

        return task

    def create_task(
        self,
        task_id: str,
        task_type: TaskType,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        source: str = "system",
        source_ref: str = "",
        capabilities_required: list[str] | None = None,
        estimated_duration_minutes: int = 30,
        dependencies: list[TaskDependency] | None = None,
        max_retries: int | None = None,
    ) -> AgentTask:
        """Create a new task in the queue.

        Args:
            task_id: Unique task identifier
            task_type: Type of task
            title: Task title
            description: Task description
            priority: Task priority level
            source: Where this task came from
            source_ref: Reference to source
            capabilities_required: List of required agent capabilities
            estimated_duration_minutes: Estimated time to complete
            dependencies: List of task dependencies
            max_retries: Number of retry attempts before permanent failure

        Returns:
            The created task
        """
        due_at = (datetime.now() + timedelta(minutes=estimated_duration_minutes)).isoformat()

        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            title=title,
            description=description,
            priority=priority,
            source=source,
            source_ref=source_ref,
            capabilities_required=capabilities_required or [],
            estimated_duration_minutes=estimated_duration_minutes,
            dependencies=dependencies or [],
            max_retries=(DEFAULT_MAX_RETRIES if max_retries is None else max(0, int(max_retries))),
            due_at=due_at,
        )

        self._tasks[task_id] = task
        self._save_task(task)
        self._checkpoint_state(f"create_task:{task_id}")

        logger.info(f"📝 Task created: {task_id} ({task_type.value}) - {title} [{priority.name}]")
        return task

    def register_agent(
        self,
        agent_id: str,
        agent_name: str,
        capabilities: list[str],
        max_concurrent_tasks: int = 3,
    ) -> None:
        """Register an agent with the queue.

        Args:
            agent_id: Unique agent identifier
            agent_name: Agent name
            capabilities: List of capabilities (code_fix, test, review, etc.)
            max_concurrent_tasks: Max tasks to assign simultaneously
        """
        self._agent_registry[agent_id] = {
            "name": agent_name,
            "capabilities": capabilities,
            "max_concurrent_tasks": max_concurrent_tasks,
            "current_load": 0,
            "completed_tasks": 0,
            "registered_at": datetime.now().isoformat(),
        }
        logger.info(
            f"🤖 Agent registered: {agent_name} with capabilities: {', '.join(capabilities)}"
        )

    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Assign a task to an agent.

        Args:
            task_id: Task ID to assign
            agent_id: Agent to assign to

        Returns:
            True if assigned, False otherwise
        """
        task = self._tasks.get(task_id)
        agent = self._agent_registry.get(agent_id)

        if not task:
            logger.error(f"Task {task_id} not found")
            return False

        if not agent:
            logger.error(f"Agent {agent_id} not found")
            return False

        # Check if agent is at capacity
        current_load = agent["current_load"]
        max_tasks = agent["max_concurrent_tasks"]
        if current_load >= max_tasks:
            logger.warning(
                f"Agent {agent['name']} is at capacity ({current_load}/{max_tasks} tasks)"
            )
            return False

        # Check if all dependencies are met
        if task.dependencies:
            for dep in task.dependencies:
                if dep.task_id not in self._completed_tasks:
                    logger.warning(f"Task {task_id} has unmet dependency: {dep.task_id}")
                    return False

        # Check if agent has required capabilities
        if task.capabilities_required:
            agent_caps = set(agent["capabilities"])
            required_caps = set(task.capabilities_required)
            if not required_caps.issubset(agent_caps):
                missing = required_caps - agent_caps
                logger.warning(f"Agent {agent['name']} missing capabilities: {missing}")
                return False

        # Perform assignment
        task.assigned_agent = AgentAssignment(
            agent_id=agent_id,
            agent_name=agent["name"],
        )
        task.status = TaskStatus.ASSIGNED
        task.next_retry_at = None
        agent["current_load"] += 1

        self._save_task(task)
        self._checkpoint_state(f"assign_task:{task_id}")

        logger.info(
            f"✅ Task {task_id} assigned to {agent['name']} (load: {agent['current_load']}/{max_tasks})"
        )
        return True

    def start_task(self, task_id: str) -> bool:
        """Mark a task as in-progress.

        Args:
            task_id: Task to start

        Returns:
            True if started, False otherwise
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        if not task.assigned_agent:
            logger.error(f"Task {task_id} not assigned to agent")
            return False

        task.status = TaskStatus.IN_PROGRESS
        task.assigned_agent.started_at = datetime.now().isoformat()
        self._save_task(task)
        self._checkpoint_state(f"start_task:{task_id}")

        logger.info(f"🚀 Task {task_id} started by {task.assigned_agent.agent_name}")
        return True

    def complete_task(
        self, task_id: str, result: dict[str, Any], artifacts: list[str] | None = None
    ) -> bool:
        """Mark a task as completed.

        Args:
            task_id: Task to complete
            result: Result data from execution
            artifacts: List of output artifact paths

        Returns:
            True if completed, False otherwise
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        if not task.assigned_agent:
            logger.error(f"Task {task_id} not assigned")
            return False

        # Move task to completed
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now().isoformat()
        task.last_error = ""
        task.next_retry_at = None
        task.assigned_agent.completed_at = task.completed_at
        task.assigned_agent.result = result
        if artifacts:
            task.artifacts = artifacts

        # Update agent load
        agent = self._agent_registry.get(task.assigned_agent.agent_id)
        if agent:
            agent["current_load"] = max(0, agent["current_load"] - 1)
            agent["completed_tasks"] = agent.get("completed_tasks", 0) + 1

        # Move to completed file
        del self._tasks[task_id]
        self._completed_tasks[task_id] = task
        self._save_completed_task(task)
        self._checkpoint_state(f"complete_task:{task_id}")

        logger.info(
            f"✨ Task {task_id} completed by {task.assigned_agent.agent_name} with {len(task.artifacts)} artifacts"
        )
        return True

    def fail_task(self, task_id: str, error_message: str) -> bool:
        """Mark a task as failed.

        Args:
            task_id: Task that failed
            error_message: Error message

        Returns:
            True if marked failed, False otherwise
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        task.last_error = error_message
        should_retry = task.retry_count < task.max_retries
        if task.assigned_agent:
            # Reduce agent load
            agent = self._agent_registry.get(task.assigned_agent.agent_id)
            if agent:
                agent["current_load"] = max(0, agent["current_load"] - 1)
        if should_retry:
            task.retry_count += 1
            retry_delay_s = self._calculate_retry_delay(task.retry_count)
            task.next_retry_at = (datetime.now() + timedelta(seconds=retry_delay_s)).isoformat()
            task.status = TaskStatus.QUEUED
            task.assigned_agent = None
            self._save_task(task)
            self._checkpoint_state(f"retry_task:{task_id}")
            logger.warning(
                "🔁 Task %s scheduled for retry %s/%s in %ss: %s",
                task_id,
                task.retry_count,
                task.max_retries,
                retry_delay_s,
                error_message,
            )
            return True

        task.status = TaskStatus.FAILED
        task.next_retry_at = None
        if task.assigned_agent:
            task.assigned_agent.result = {"error": error_message}

        self._save_task(task)
        self._checkpoint_state(f"fail_task:{task_id}")

        logger.error(f"❌ Task {task_id} failed: {error_message}")
        return True

    def get_pending_tasks(self, agent_id: str | None = None) -> list[AgentTask]:
        """Get pending tasks, optionally filtered by agent.

        Args:
            agent_id: Filter to tasks for this agent

        Returns:
            List of pending tasks
        """
        now = datetime.now()
        tasks = [
            t
            for t in self._tasks.values()
            if t.status in (TaskStatus.CREATED, TaskStatus.QUEUED) and self._is_retry_ready(t, now)
        ]

        if agent_id and agent_id in self._agent_registry:
            agent = self._agent_registry[agent_id]
            agent_caps = set(agent["capabilities"])
            tasks = [
                t
                for t in tasks
                if not t.capabilities_required or set(t.capabilities_required).issubset(agent_caps)
            ]

        # Sort by priority and creation time
        tasks.sort(key=lambda t: (t.priority.value, t.created_at))
        return tasks

    def get_task(self, task_id: str) -> AgentTask | None:
        """Get a task by ID."""
        return self._tasks.get(task_id) or self._completed_tasks.get(task_id)

    def get_queue_status(self) -> dict[str, Any]:
        """Get overall queue status.

        Returns:
            Queue metrics and statistics
        """
        all_tasks = list(self._tasks.values()) + list(self._completed_tasks.values())

        now = datetime.now()
        retry_waiting = [
            t
            for t in self._tasks.values()
            if t.status == TaskStatus.QUEUED and not self._is_retry_ready(t, now)
        ]
        return {
            "total_tasks": len(all_tasks),
            "pending": len(
                [
                    t
                    for t in self._tasks.values()
                    if t.status in (TaskStatus.CREATED, TaskStatus.QUEUED)
                    and self._is_retry_ready(t, now)
                ]
            ),
            "retry_waiting": len(retry_waiting),
            "assigned": len([t for t in self._tasks.values() if t.status == TaskStatus.ASSIGNED]),
            "in_progress": len(
                [t for t in self._tasks.values() if t.status == TaskStatus.IN_PROGRESS]
            ),
            "completed": len(self._completed_tasks),
            "failed": len([t for t in self._tasks.values() if t.status == TaskStatus.FAILED]),
            "agents_registered": len(self._agent_registry),
            "agents_busy": sum(1 for a in self._agent_registry.values() if a["current_load"] > 0),
            "timestamp": datetime.now().isoformat(),
        }

    def _save_task(self, task: AgentTask) -> None:
        """Save task to persistence."""
        try:
            tasks = []
            if self.tasks_file.exists():
                for line in self.tasks_file.read_text().strip().split("\n"):
                    if line.strip():
                        tasks.append(json.loads(line))

            tasks = [t for t in tasks if t["task_id"] != task.task_id]

            task_dict = asdict(task)
            task_dict["task_type"] = task.task_type.value
            task_dict["priority"] = task.priority.value
            task_dict["status"] = task.status.value
            task_dict["dependencies"] = [asdict(d) for d in task.dependencies]
            task_dict["assigned_agent"] = (
                asdict(task.assigned_agent) if task.assigned_agent else None
            )
            tasks.append(task_dict)
            self._write_jsonl_atomic(self.tasks_file, tasks)
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.error(f"Failed to save task: {e}")

    def _save_completed_task(self, task: AgentTask) -> None:
        """Save completed task to persistence."""
        try:
            tasks = []
            if self.completed_file.exists():
                for line in self.completed_file.read_text().strip().split("\n"):
                    if line.strip():
                        tasks.append(json.loads(line))

            task_dict = asdict(task)
            task_dict["task_type"] = task.task_type.value
            task_dict["priority"] = task.priority.value
            task_dict["status"] = task.status.value
            task_dict["dependencies"] = [asdict(d) for d in task.dependencies]
            task_dict["assigned_agent"] = (
                asdict(task.assigned_agent) if task.assigned_agent else None
            )
            tasks.append(task_dict)
            self._write_jsonl_atomic(self.completed_file, tasks)
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.error(f"Failed to save completed task: {e}")

    @staticmethod
    def _write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
        """Write JSONL content atomically to avoid partial writes."""
        content = "\n".join(json.dumps(row) for row in rows)
        if content:
            content = f"{content}\n"
        temp_path = path.with_suffix(f"{path.suffix}.tmp")
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(path)

    @staticmethod
    def _is_retry_ready(task: AgentTask, now: datetime | None = None) -> bool:
        """Return True when task retry window is ready (or no retry delay)."""
        if not task.next_retry_at:
            return True
        current = now or datetime.now()
        try:
            return datetime.fromisoformat(task.next_retry_at) <= current
        except ValueError:
            return True

    @staticmethod
    def _calculate_retry_delay(retry_count: int) -> int:
        """Exponential backoff delay in seconds with upper cap."""
        power = max(0, retry_count - 1)
        delay = RETRY_BASE_SECONDS * (2**power)
        return min(MAX_RETRY_DELAY_SECONDS, delay)

    def _checkpoint_state(self, reason: str) -> None:
        """Capture queue state checkpoint for crash-safe recovery."""
        if self._checkpoint_manager is None:
            return
        try:
            state = {
                "reason": reason,
                "pending_task_ids": sorted(self._tasks.keys()),
                "completed_task_ids": sorted(self._completed_tasks.keys()),
                "agent_registry": self._agent_registry,
                "timestamp": datetime.now().isoformat(),
            }
            checkpoint_id = self._checkpoint_manager.save(state, description=reason)
            if self._tasks:
                for task in self._tasks.values():
                    task.checkpoint_id = checkpoint_id
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Task queue checkpoint failed (%s): %s", reason, exc)
