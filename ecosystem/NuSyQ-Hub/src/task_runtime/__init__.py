"""NuSyQ Task Runtime — lightweight task runtime and SQLite persistence.

Provides:
- Database: SQLite connection wrapper
- TaskManager: task CRUD and lifecycle operations
- Task, Run, TaskModel: core data model classes
- task_context: context manager for agent task wrapping
- AgentPreconditionError: raised when task preconditions fail

OmniTag: {
    "purpose": "task_runtime_subsystem",
    "tags": ["TaskRuntime", "SQLite", "Persistence", "Agent"],
    "category": "orchestration",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

from .db import Database
from .manager import TaskManager

__all__ = [
    # Agent wrapper (lazy)
    "AgentPreconditionError",
    # Core persistence (direct)
    "Database",
    "Run",
    # Data models (lazy)
    "Task",
    "TaskManager",
    "TaskModel",
    "task_context",
]


def __getattr__(name: str) -> object:
    if name in ("Task", "Run", "TaskModel"):
        from src.task_runtime.models import Run, Task, TaskModel

        return locals()[name]
    if name in ("AgentPreconditionError", "task_context"):
        from src.task_runtime.agent_wrapper import (AgentPreconditionError,
                                                    task_context)

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
