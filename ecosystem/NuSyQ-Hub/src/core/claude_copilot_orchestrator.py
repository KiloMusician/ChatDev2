"""Minimal stub for ClaudeCopilotOrchestrator.

Provides a stable import target for legacy callers. This implementation is
intentionally lightweight and returns no-op responses rather than raising.
Delegates to MJOLNIR when available; degrades gracefully if import fails.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _run_async(coro: Any) -> Any:
    """Run an async coroutine safely regardless of existing event-loop state.

    - If no loop is running (normal CLI/script context): use asyncio.run().
    - If a loop is already running (Jupyter, pytest-asyncio, nested async):
      create a new loop in a thread to avoid RuntimeError.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        return asyncio.run(coro)

    # A loop is already running — run in a fresh thread-scoped event loop.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        return future.result()


class ClaudeCopilotOrchestrator:
    def __init__(self) -> None:
        """Initialize ClaudeCopilotOrchestrator."""
        self.status = "idle"

    def _get_protocol(self) -> Any:
        """Lazily import and instantiate MjolnirProtocol.

        Returns the protocol instance or None if MJOLNIR is unavailable.
        """
        try:
            from src.dispatch.mjolnir import MjolnirProtocol

            return MjolnirProtocol()
        except Exception as exc:  # ImportError or any init failure
            logger.debug("MJOLNIR unavailable, falling back to stub: %s", exc)
            return None

    def route(self, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Route a task to the best available agent via MJOLNIR."""
        ctx = context or {}

        protocol = self._get_protocol()
        if protocol is None:
            return {
                "status": "not_implemented",
                "task": task,
                "context": {**ctx},
            }

        for agent in ("ollama", "claude_cli"):
            try:
                envelope = _run_async(
                    protocol.ask(agent, task, no_guild=True, extra_context=ctx or None)
                )
                return {
                    "status": envelope.status,
                    "task": task,
                    "agent": envelope.agent,
                    "output": envelope.output,
                    "context": {**ctx},
                }
            except Exception as exc:
                logger.debug("MJOLNIR ask via %s failed: %s", agent, exc)

        return {
            "status": "error",
            "task": task,
            "context": {**ctx},
        }

    def analyze(self, text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Analyze text via MJOLNIR; falls back to stub if unavailable."""
        ctx = context or {}
        prompt = f"Analyze: {text[:500]}"

        protocol = self._get_protocol()
        if protocol is None:
            return {
                "status": "not_implemented",
                "summary": text[:200],
                "context": {**ctx},
            }

        for agent in ("ollama", "claude_cli"):
            try:
                envelope = _run_async(
                    protocol.ask(
                        agent, prompt, task_type="analyze", no_guild=True, extra_context=ctx or None
                    )
                )
                return {
                    "status": envelope.status,
                    "summary": text[:200],
                    "agent": envelope.agent,
                    "output": envelope.output,
                    "context": {**ctx},
                }
            except Exception as exc:
                logger.debug("MJOLNIR analyze via %s failed: %s", agent, exc)

        return {
            "status": "error",
            "summary": text[:200],
            "context": {**ctx},
        }


__all__ = ["ClaudeCopilotOrchestrator"]
