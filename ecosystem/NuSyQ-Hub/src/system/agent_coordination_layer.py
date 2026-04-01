"""Agent Coordination Layer - Prevents task collision & orchestrates handoff.

Manages task locking, request/grant patterns, and exclusive context acquisition.
Ensures only one agent works on a task at a time while others observe.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.system.multi_agent_terminal_orchestrator import (AgentType,
                                                          TerminalType,
                                                          get_orchestrator)


class TaskLockStatus(Enum):
    """Status of a task lock request."""

    GRANTED = "granted"
    DENIED = "denied"
    QUEUED = "queued"
    RELEASED = "released"


class RequestType(Enum):
    """Types of inter-agent requests."""

    TASK_LOCK_REQUEST = "task_lock_request"
    TASK_LOCK_RELEASE = "task_lock_release"
    PERMISSION_REQUEST = "permission_request"
    CONSULTATION_REQUEST = "consultation_request"
    VETO_NOTIFICATION = "veto_notification"


@dataclass
class TaskLock:
    """Lock on a specific task held by an agent."""

    task_id: str
    locked_by: AgentType
    acquired_at: datetime
    timeout_seconds: int = 300
    exclusive: bool = True  # If True, no other agent can work on task

    def is_expired(self) -> bool:
        """Check if lock has expired."""
        elapsed = (datetime.now() - self.acquired_at).total_seconds()
        return elapsed > self.timeout_seconds

    def remaining_time(self) -> float:
        """Get remaining lock time in seconds."""
        elapsed = (datetime.now() - self.acquired_at).total_seconds()
        return max(0, self.timeout_seconds - elapsed)


@dataclass
class AgentRequest:
    """Request from one agent to another."""

    request_id: str
    source: AgentType
    target: AgentType
    request_type: RequestType
    task_id: str | None = None
    context: dict[str, Any] | None = None
    created_at: datetime = None
    status: str = "pending"  # pending, accepted, rejected, cancelled

    def __post_init__(self) -> None:
        """Implement __post_init__."""
        if self.created_at is None:
            self.created_at = datetime.now()


class AgentCoordinationLayer:
    """Manages task locks, request queues, and multi-agent coordination."""

    def __init__(self, state_dir: Path = Path("data/agent_coordination")):
        """Initialize AgentCoordinationLayer with state_dir."""
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)
        self.orchestrator = None

        # Task locks: task_id → TaskLock
        self.task_locks: dict[str, TaskLock] = {}

        # Request queues: (target_agent) → list[AgentRequest]
        self.request_queues: dict[AgentType, list[AgentRequest]] = {
            agent: [] for agent in AgentType
        }

        # Agent deadlines: task_id → deadline time
        self.task_deadlines: dict[str, datetime] = {}

        # Inter-agent waitlists: task_id → list[AgentType] waiting
        self.task_waitlists: dict[str, list[AgentType]] = {}

        self._lock = asyncio.Lock()

    def _coerce_agent(self, agent: AgentType | str) -> AgentType:
        """Normalize agent identifiers to AgentType."""
        if isinstance(agent, AgentType):
            return agent

        candidate = str(agent).strip().lower()
        for enum_agent in AgentType:
            if enum_agent.value == candidate or enum_agent.name.lower() == candidate:
                return enum_agent

        valid = ", ".join(sorted(a.value for a in AgentType))
        raise ValueError(f"Unknown agent '{agent}'. Expected one of: {valid}")

    async def init(self) -> None:
        """Initialize coordination layer with orchestrator."""
        if self.orchestrator is None:
            self.orchestrator = await get_orchestrator()

    async def request_task_lock(
        self,
        task_id: str,
        agent: AgentType | str,
        exclusive: bool = True,
        timeout_seconds: int = 300,
    ) -> tuple[TaskLockStatus, TaskLock | None]:
        """Request exclusive lock on a task."""
        await self.init()
        agent = self._coerce_agent(agent)

        async with self._lock:
            # Check if task already locked
            if task_id in self.task_locks:
                existing_lock = self.task_locks[task_id]

                # Check if lock expired
                if existing_lock.is_expired():
                    # Reclaim expired lock
                    new_lock = TaskLock(
                        task_id=task_id,
                        locked_by=agent,
                        acquired_at=datetime.now(),
                        timeout_seconds=timeout_seconds,
                        exclusive=exclusive,
                    )
                    self.task_locks[task_id] = new_lock
                    await self._emit_lock_event(
                        task_id, agent, TaskLockStatus.GRANTED, "Lock reclaimed (expired)"
                    )
                    return (TaskLockStatus.GRANTED, new_lock)

                else:
                    # Lock held by another agent
                    if agent not in self.task_waitlists.get(task_id, []):
                        if task_id not in self.task_waitlists:
                            self.task_waitlists[task_id] = []
                        self.task_waitlists[task_id].append(agent)

                    await self._emit_lock_event(
                        task_id,
                        agent,
                        TaskLockStatus.QUEUED,
                        f"Waiting for {existing_lock.locked_by.value}",
                    )
                    return (TaskLockStatus.DENIED, None)

            # Grant new lock
            new_lock = TaskLock(
                task_id=task_id,
                locked_by=agent,
                acquired_at=datetime.now(),
                timeout_seconds=timeout_seconds,
                exclusive=exclusive,
            )
            self.task_locks[task_id] = new_lock
            await self._emit_lock_event(task_id, agent, TaskLockStatus.GRANTED, "Lock acquired")
            return (TaskLockStatus.GRANTED, new_lock)

    async def release_task_lock(self, task_id: str, agent: AgentType | str) -> bool:
        """Release lock on a task."""
        await self.init()
        agent = self._coerce_agent(agent)
        next_agent: AgentType | None = None

        async with self._lock:
            if task_id not in self.task_locks:
                return False

            lock = self.task_locks[task_id]
            if lock.locked_by != agent:
                self.logger.warning(
                    f"Agent {agent.value} tried to release lock held by {lock.locked_by.value}"
                )
                return False

            del self.task_locks[task_id]

            # Capture next waiter while lock is held, but grant outside lock
            # to avoid re-entrant deadlock on self._lock.
            if self.task_waitlists.get(task_id):
                next_agent = self.task_waitlists[task_id].pop(0)
                if not self.task_waitlists[task_id]:
                    del self.task_waitlists[task_id]

        await self._emit_lock_event(task_id, agent, TaskLockStatus.RELEASED, "Lock released")

        if next_agent is not None:
            status, _ = await self.request_task_lock(task_id, next_agent)
            if status == TaskLockStatus.GRANTED:
                self.logger.info(f"Granted lock to waiting agent {next_agent.value}")

        return True

    async def send_request(
        self,
        source: AgentType,
        target: AgentType,
        request_type: RequestType,
        task_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentRequest:
        """Send a request from one agent to another."""
        await self.init()

        request = AgentRequest(
            request_id=f"{source.value}_{target.value}_{datetime.now().timestamp()}",
            source=source,
            target=target,
            request_type=request_type,
            task_id=task_id,
            context=context,
        )

        async with self._lock:
            self.request_queues[target].append(request)

        # Emit to intermediary
        await self.orchestrator.write_to_terminal(
            source,
            TerminalType.INTERMEDIARY,
            f"Request {request_type.value}: {source.value} → {target.value}",
            context={"request_id": request.request_id, "task_id": task_id},
        )

        return request

    async def get_pending_requests(self, agent: AgentType) -> list[AgentRequest]:
        """Get all pending requests for an agent."""
        async with self._lock:
            return [r for r in self.request_queues[agent] if r.status == "pending"]

    async def accept_request(
        self, agent: AgentType, request_id: str, response_context: dict | None = None
    ) -> bool:
        """Accept a request."""
        async with self._lock:
            for request in self.request_queues[agent]:
                if request.request_id == request_id:
                    request.status = "accepted"
                    await self.orchestrator.write_to_terminal(
                        agent,
                        TerminalType.INTERMEDIARY,
                        f"Accepted request {request_id}",
                        context=response_context,
                    )
                    return True
        return False

    async def reject_request(self, agent: AgentType, request_id: str, reason: str = "") -> bool:
        """Reject a request."""
        async with self._lock:
            for request in self.request_queues[agent]:
                if request.request_id == request_id:
                    request.status = "rejected"
                    await self.orchestrator.write_to_terminal(
                        agent,
                        TerminalType.INTERMEDIARY,
                        f"Rejected request {request_id}: {reason}",
                    )
                    return True
        return False

    async def get_coordination_status(self) -> dict[str, Any]:
        """Get current coordination state."""
        async with self._lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "task_locks": {
                    task_id: {
                        "locked_by": lock.locked_by.value,
                        "acquired_at": lock.acquired_at.isoformat(),
                        "remaining_time": lock.remaining_time(),
                    }
                    for task_id, lock in self.task_locks.items()
                },
                "request_queues": {
                    agent.value: [
                        {
                            "request_id": r.request_id,
                            "source": r.source.value,
                            "type": r.request_type.value,
                            "status": r.status,
                        }
                        for r in self.request_queues[agent]
                    ]
                    for agent in AgentType
                },
                "waitlists": {
                    task_id: [a.value for a in agents]
                    for task_id, agents in self.task_waitlists.items()
                },
            }

    async def save_state(self) -> None:
        """Persist coordination state to disk."""
        state = await self.get_coordination_status()
        state_file = self.state_dir / "coordination_state.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)

    async def _emit_lock_event(
        self, task_id: str, agent: AgentType, status: TaskLockStatus, message: str
    ) -> None:
        """Emit lock event to relevant terminals."""
        await self.orchestrator.write_to_terminal(
            agent,
            TerminalType.AGENTS,
            f"[{status.value}] {message} (task: {task_id})",
            context={"task_id": task_id, "lock_status": status.value},
        )


# Singleton instance
_coordination_layer: AgentCoordinationLayer | None = None


async def get_coordination_layer() -> AgentCoordinationLayer:
    """Get or create the singleton coordination layer."""
    global _coordination_layer
    if _coordination_layer is None:
        _coordination_layer = AgentCoordinationLayer()
        await _coordination_layer.init()
    return _coordination_layer


async def init_coordination_layer() -> AgentCoordinationLayer:
    """Initialize the coordination layer."""
    layer = await get_coordination_layer()
    await layer.init()
    return layer
