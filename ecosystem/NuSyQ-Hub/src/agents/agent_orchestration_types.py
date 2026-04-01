"""Shared types for AgentOrchestrationHub.

This module isolates core enums and dataclasses so the hub stays focused
on orchestration logic while keeping type reuse consistent across bridges.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskPriority(Enum):
    """Task priority levels."""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class ExecutionMode(Enum):
    """Multi-agent execution modes."""

    CONSENSUS = "consensus"  # All agents must agree
    VOTING = "voting"  # Majority vote
    SEQUENTIAL = "sequential"  # Execute in order
    PARALLEL = "parallel"  # Execute simultaneously
    FIRST_SUCCESS = "first_success"  # Stop on first success


@dataclass
class TaskLock:
    """Represents an exclusive lock on a task."""

    task_id: str
    agent_id: str
    acquired_at: float
    expires_at: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceCapability:
    """Describes a capability that a service provides."""

    name: str
    description: str
    priority: int = 5
    requires_consciousness: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RegisteredService:
    """A registered AI service/agent."""

    service_id: str
    name: str
    capabilities: list[ServiceCapability]
    endpoint: str | None = None
    active: bool = True
    registered_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "ExecutionMode",
    "RegisteredService",
    "ServiceCapability",
    "TaskLock",
    "TaskPriority",
]
