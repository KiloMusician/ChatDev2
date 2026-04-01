#!/usr/bin/env python3
"""Terminal-Aware Action Wrappers

Drop-in enhancements for existing action modules that add terminal routing.
Import and use these to get automatic terminal integration.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from scripts.nusyq_actions.shared import emit_action_receipt

# Import async terminal router
try:
    from src.system.agent_terminal_router import get_router
    from src.system.multi_agent_terminal_orchestrator import (
        AgentType,
        TerminalType,
        init_orchestrator,
    )

    ASYNC_ROUTING_AVAILABLE = True
except ImportError:
    ASYNC_ROUTING_AVAILABLE = False

# Strong-reference set for fire-and-forget terminal-emit tasks (prevents GC cancellation).
_pending_emit_tasks: set[asyncio.Task[object]] = set()


# Import sync terminal router as fallback
try:
    from src.output.terminal_integration import (
        route_to_terminal,
        to_agents,
        to_errors,
        to_metrics,
        to_suggestions,
        to_tasks,
        to_zeta,
    )

    SYNC_ROUTING_AVAILABLE = True
except ImportError:
    SYNC_ROUTING_AVAILABLE = False

    # No-op fallbacks
    def to_tasks(msg):
        # Fallback no-op when sync routing is unavailable.
        pass

    def to_errors(msg):
        # Fallback no-op when sync routing is unavailable.
        pass

    def to_metrics(msg):
        # Fallback no-op when sync routing is unavailable.
        pass

    def to_suggestions(msg):
        # Fallback no-op when sync routing is unavailable.
        pass

    def to_zeta(msg):
        # Fallback no-op when sync routing is unavailable.
        pass

    def to_agents(msg):
        # Fallback no-op when sync routing is unavailable.
        pass

    def route_to_terminal(terminal, msg):
        # Fallback no-op when sync routing is unavailable.
        pass


_router_cache = None


async def _get_async_router():
    """Get async router (cached)."""
    global _router_cache
    if _router_cache is None and ASYNC_ROUTING_AVAILABLE:
        await init_orchestrator()
        _router_cache = await get_router()
    return _router_cache


def _emit_sync(terminal: str, message: str, level: str = "INFO"):
    """Emit to terminal using sync router."""
    if SYNC_ROUTING_AVAILABLE:
        route_to_terminal(terminal, f"[{level}] {message}")


def _emit_async(
    agent: AgentType,
    terminal: TerminalType,
    message: str,
    level: str = "info",
    context: dict | None = None,
):
    """Emit to terminal using async router."""
    if not ASYNC_ROUTING_AVAILABLE:
        return

    async def _do_emit():
        router = await _get_async_router()
        if router:
            await router.orchestrator.write_to_terminal(
                agent=agent,
                terminal=terminal,
                message=message,
                level=level,
                context=context or {},
            )

    try:
        asyncio.run(_do_emit())
    except RuntimeError:
        # Already in event loop
        loop = asyncio.get_event_loop()
        _t = loop.create_task(_do_emit())
        _pending_emit_tasks.add(_t)
        _t.add_done_callback(_pending_emit_tasks.discard)


# Task-specific routing functions
def emit_task_started(task_id: str, description: str):
    """Emit task started event."""
    _emit_sync("tasks", f"Task #{task_id} [STARTED]: {description}")
    if ASYNC_ROUTING_AVAILABLE:
        _emit_async(
            AgentType.COPILOT,
            TerminalType.TASKS,
            f"Task #{task_id} started: {description}",
            context={"task_id": task_id, "status": "started"},
        )


def emit_task_completed(task_id: str, description: str, duration: float | None = None):
    """Emit task completed event."""
    msg = f"Task #{task_id} [COMPLETED]: {description}"
    if duration:
        msg += f" ({duration:.2f}s)"
    _emit_sync("tasks", msg)
    if ASYNC_ROUTING_AVAILABLE:
        context = {"task_id": task_id, "status": "completed"}
        if duration:
            context["duration"] = duration
        _emit_async(AgentType.COPILOT, TerminalType.TASKS, msg, context=context)


def emit_task_failed(task_id: str, description: str, error: str):
    """Emit task failed event."""
    _emit_sync("tasks", f"Task #{task_id} [FAILED]: {description}")
    _emit_sync("errors", f"Task #{task_id} error: {error}")
    if ASYNC_ROUTING_AVAILABLE:
        _emit_async(
            AgentType.COPILOT,
            TerminalType.ERRORS,
            f"Task #{task_id} failed: {error}",
            level="error",
            context={"task_id": task_id, "error": error},
        )


def emit_queue_status(pending: int, processing: int, completed: int):
    """Emit queue status metrics."""
    msg = f"PU Queue: {pending} pending, {processing} processing, {completed} completed"
    _emit_sync("metrics", msg)
    to_metrics(msg)


def emit_test_result(test_name: str, status: str, duration: float | None = None):
    """Emit test result."""
    msg = f"Test: {test_name} - {status.upper()}"
    if duration:
        msg += f" ({duration:.2f}s)"
    route_to_terminal("tests", msg)


def emit_zeta_cycle(cycle_number: int, action: str):
    """Emit Zeta autonomous cycle event."""
    to_zeta(f"Cycle #{cycle_number}: {action}")


def emit_agent_activity(agent_name: str, activity: str):
    """Emit general agent activity."""
    to_agents(f"[{agent_name.upper()}] {activity}")


def emit_guild_event(event_type: str, details: str):
    """Emit guild board event."""
    to_agents(f"[GUILD] {event_type}: {details}")


def emit_metric(metric_name: str, value: str | int | float):
    """Emit a metric."""
    to_metrics(f"{metric_name}: {value}")


def emit_suggestion(suggestion: str):
    """Emit a suggestion."""
    to_suggestions(f"💡 {suggestion}")


def emit_error(error_message: str, context: str = ""):
    """Emit an error."""
    msg = error_message
    if context:
        msg += f" | Context: {context}"
    to_errors(msg)


# Decorators for automatic terminal routing
def with_task_routing(task_name: str):
    """Decorator that adds automatic task routing to a function."""

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            emit_task_started("auto", f"{task_name}")
            try:
                result = func(*args, **kwargs)
                emit_task_completed("auto", f"{task_name}")
                return result
            except Exception as e:
                emit_task_failed("auto", f"{task_name}", str(e))
                raise

        return wrapper

    return decorator


def with_terminal_routing(terminal: str):
    """Decorator that routes all print() calls from a function to a specific terminal."""

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            _emit_sync(terminal, f"=== {func.__name__} started ===")
            try:
                result = func(*args, **kwargs)
                _emit_sync(terminal, f"=== {func.__name__} completed ===")
                return result
            except Exception as e:
                emit_error(f"Function {func.__name__} failed: {e}")
                raise

        return wrapper

    return decorator


# Example usage
if __name__ == "__main__":
    print("🔌 Terminal-Aware Actions Demo")
    print("=" * 70)

    # Task events
    emit_task_started("1042", "System health check")
    emit_task_completed("1042", "System health check", duration=2.5)
    emit_task_started("1043", "Update dependencies")
    emit_task_failed("1043", "Update dependencies", "Dependency conflict detected")

    # Queue status
    emit_queue_status(pending=12, processing=3, completed=145)

    # Test results
    emit_test_result("test_quantum_bridge", "passed", 0.45)
    emit_test_result("test_error_handling", "failed", 0.23)

    # Zeta cycles
    emit_zeta_cycle(47, "Auto-healing initiated")
    emit_zeta_cycle(47, "Completed successfully")

    # Agent activity
    emit_agent_activity("claude", "Analyzing repository structure")
    emit_agent_activity("copilot", "Suggesting code completions")

    # Guild events
    emit_guild_event("quest_posted", "Implement authentication system")
    emit_guild_event("quest_completed", "Refactor error handling")

    # Metrics
    emit_metric("System Health", "94%")
    emit_metric("Active Agents", 6)
    emit_metric("Response Time", "1.2s")

    # Suggestions
    emit_suggestion("Consider caching configuration data")
    emit_suggestion("Add retry logic for API calls")

    # Errors
    emit_error("Database connection failed", "src/db/connection.py:42")

    print("\n✅ Demo complete! Check data/terminal_logs/ for logs")
    emit_action_receipt("terminal_aware_demo", exit_code=0)
