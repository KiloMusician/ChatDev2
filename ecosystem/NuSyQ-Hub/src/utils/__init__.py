"""Utility functions and helpers for the NuSyQ-Hub ecosystem.

Core utilities (lazy __getattr__ for heavy modules, direct for lightweight):
- RepositoryPathResolver: cross-repo path resolution (see also repo_path_resolver)
- IntelligentTimeoutManager: adaptive timeout scaling
- AIModel, TaskStatus: shared enums (constants.py)
- EventBus helpers: emit_event, emit_agent_message (event_bus.py)
- GracefulShutdownMixin: service shutdown lifecycle
- SafeSubprocessExecutor: sandboxed subprocess execution

OmniTag: {
    "purpose": "utils_subsystem",
    "tags": ["Utilities", "Helpers", "PathResolver", "Timeout", "Events"],
    "category": "infrastructure",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

from .settings import load_settings

__all__ = [
    # Shared enums (lazy)
    "AIModel",
    # Async task execution (lazy) — anti-softlock
    "AsyncTaskExecutor",
    # Config factory (lazy)
    "ConfigProxy",
    # Shutdown (lazy)
    "GracefulShutdownMixin",
    # Timeout management (lazy)
    "IntelligentTimeoutManager",
    # Path resolution (lazy)
    "RepositoryPathResolver",
    # Resource cleanup (lazy)
    "ResourceCleanup",
    # Safe subprocess (lazy)
    "SafeSubprocessExecutor",
    "ServiceTimeoutManager",
    # Session management (lazy)
    "SessionCheckpoint",
    "ShutdownConfig",
    "TaskResult",
    "TaskState",
    "TaskStatus",
    # Contextual output (lazy)
    "contextual_save",
    "emit_agent_message",
    # Event bus (lazy)
    "emit_event",
    "get_repo_path",
    "get_repo_path_str",
    # Path helpers (lazy)
    "join_path",
    # Settings (direct — lightweight)
    "load_settings",
    # Error handling (lazy)
    "with_error_handling",
]


def __getattr__(name: str) -> object:
    if name in ("RepositoryPathResolver", "get_repo_path", "get_repo_path_str"):
        from src.utils.repo_path_resolver import (RepositoryPathResolver,
                                                  get_repo_path,
                                                  get_repo_path_str)

        return locals()[name]
    if name in ("IntelligentTimeoutManager", "ServiceTimeoutManager"):
        from src.utils.intelligent_timeout_manager import (
            IntelligentTimeoutManager, ServiceTimeoutManager)

        return locals()[name]
    if name in ("AIModel", "TaskStatus"):
        from src.utils.constants import AIModel, TaskStatus

        return locals()[name]
    if name in ("emit_event", "emit_agent_message", "emit_council_vote"):
        from src.utils.event_bus import (emit_agent_message, emit_council_vote,
                                         emit_event)

        return locals()[name]
    if name in ("GracefulShutdownMixin", "ShutdownConfig", "ShutdownPhase"):
        from src.utils.graceful_shutdown import (GracefulShutdownMixin,
                                                 ShutdownConfig, ShutdownPhase)

        return locals()[name]
    if name in ("SafeSubprocessExecutor", "SecurityError"):
        from src.utils.safe_subprocess import (SafeSubprocessExecutor,
                                               SecurityError)

        return locals()[name]
    if name == "join_path":
        from src.utils.helpers import join_path

        return join_path
    # Async task execution (anti-softlock)
    if name in ("AsyncTaskExecutor", "TaskResult", "TaskState"):
        from src.utils.async_task_wrapper import (AsyncTaskExecutor,
                                                  TaskResult, TaskState)

        return locals()[name]
    # Error handling decorator
    if name == "with_error_handling":
        from src.utils.error_handling import with_error_handling

        return with_error_handling
    # Session management
    if name == "SessionCheckpoint":
        from src.utils.session_checkpoint import SessionCheckpoint

        return SessionCheckpoint
    # Contextual output
    if name == "contextual_save":
        from src.utils.contextual_output import contextual_save

        return contextual_save
    # Config factory
    if name == "ConfigProxy":
        from src.utils.config_factory import ConfigProxy

        return ConfigProxy
    # Resource cleanup
    if name == "ResourceCleanup":
        from src.utils.resource_cleanup import ResourceCleanup

        return ResourceCleanup
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
