"""Copilot task routing and execution utilities."""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def run_lint() -> subprocess.CompletedProcess:
    """Run code linting using Ruff."""
    return subprocess.run(["ruff", "check"], check=False)


def run_tests() -> subprocess.CompletedProcess:
    """Run the test suite using pytest."""
    return subprocess.run(["pytest"], check=False)


def generate_docs() -> subprocess.CompletedProcess:
    """Generate project documentation using Sphinx."""
    return subprocess.run(["sphinx-build", "docs", "docs/_build"], check=False)


TASK_ROUTER: dict[str, Callable[[], subprocess.CompletedProcess]] = {
    "lint": run_lint,
    "test": run_tests,
    "doc": generate_docs,
}


class CopilotTaskManager:
    """Manage and execute development tasks triggered by LLM responses."""

    TASK_PATTERN = re.compile(r"<task:(\w+)>|run\s+(lint|test|doc)")

    def __init__(
        self,
        task_router: dict[str, Callable[[], subprocess.CompletedProcess]] | None = None,
    ) -> None:
        """Initialize CopilotTaskManager with task_router, Callable[[], subprocess.CompletedProcess]] | None."""
        self.task_router = task_router or TASK_ROUTER.copy()

    def register_task(
        self,
        name: str,
        func: Callable[[], subprocess.CompletedProcess],
    ) -> None:
        """Register a new task."""
        self.task_router[name] = func

    def execute_task(self, name: str) -> subprocess.CompletedProcess | None:
        """Execute a task by name if registered."""
        func = self.task_router.get(name)
        if not func:
            return None
        result = func()
        try:
            from src.system.agent_awareness import emit as _emit

            _rc = getattr(result, "returncode", None)
            _lvl = "WARNING" if _rc and _rc != 0 else "INFO"
            _emit(
                "copilot",
                f"Task executed: {name} returncode={_rc}",
                level=_lvl,
                source="copilot_task_manager",
            )
        except Exception:
            pass
        return result

    def handle_response(self, response: str) -> None:
        """Parse an LLM response and trigger any referenced tasks."""
        if not response:
            return
        for match in self.TASK_PATTERN.findall(response.lower()):
            task_name = match[0] or match[1]
            if task_name:
                self.execute_task(task_name)
