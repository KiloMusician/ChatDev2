#!/usr/bin/env python3
"""Simple background task queue for Copilot integration.

Allows asynchronous execution of shell commands (linting, tests, doc
builds) while tracking their status and output.  Status information can
be queried via the :func:`status` function or the ``status`` CLI
sub-command.
"""

from __future__ import annotations

import os
import subprocess
import threading
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any

try:
    from src.utils.auto_recovery_watchdog import AutoRecoveryWatchdog
except Exception:  # pragma: no cover - optional in minimal environments
    AutoRecoveryWatchdog = None  # type: ignore[assignment]

OmniTag = {
    "purpose": "background_task_management",
    "tags": ["Python", "Async", "TaskQueue"],
    "evolution_stage": "v1.0",
}


class TaskQueue:
    """Manage background shell command execution using threads."""

    def __init__(self) -> None:
        """Initialize in-memory task state and synchronization lock."""
        self._tasks: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def _run_command(
        self,
        name: str,
        command: list[str],
        timeout_seconds: int | None,
        max_retries: int,
        retry_backoff_seconds: int,
    ) -> None:
        """Execute ``command`` and capture output while updating status."""
        with self._lock:
            self._tasks[name]["status"] = "running"
            self._tasks[name]["started_at"] = time.time()
            self._tasks[name]["attempts"] = 0

        final_status = "failed (unknown)"
        final_code: int | None = None

        for attempt in range(1, max_retries + 2):
            with self._lock:
                self._tasks[name]["attempts"] = attempt

            watchdog_ctx = nullcontext()
            if AutoRecoveryWatchdog is not None and timeout_seconds is not None:
                watchdog = AutoRecoveryWatchdog(
                    timeout=float(timeout_seconds),
                    auto_recover=True,
                    checkpoint_on_recovery=True,
                )
                watchdog_ctx = watchdog.monitor(f"task_queue:{name}:attempt_{attempt}")

            with watchdog_ctx:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

                try:
                    stdout, _ = process.communicate(timeout=timeout_seconds)
                    lines = stdout.splitlines() if stdout else []
                    with self._lock:
                        self._tasks[name]["output"].extend(lines)
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, _ = process.communicate()
                    lines = stdout.splitlines() if stdout else []
                    with self._lock:
                        self._tasks[name]["output"].extend(lines)
                    final_status = "timeout"
                    final_code = process.returncode
                    if attempt <= max_retries:
                        with self._lock:
                            self._tasks[name]["status"] = f"retrying ({attempt}/{max_retries})"
                        time.sleep(max(0, retry_backoff_seconds) * (2 ** (attempt - 1)))
                        continue
                    break

            final_code = process.returncode
            if process.returncode == 0:
                final_status = "success"
                break

            final_status = f"failed ({process.returncode})"
            if attempt <= max_retries:
                with self._lock:
                    self._tasks[name]["status"] = f"retrying ({attempt}/{max_retries})"
                time.sleep(max(0, retry_backoff_seconds) * (2 ** (attempt - 1)))
                continue
            break

        with self._lock:
            self._tasks[name]["status"] = final_status
            self._tasks[name]["return_code"] = final_code
            self._tasks[name]["ended_at"] = time.time()

    # ------------------------------------------------------------------
    def queue_command(
        self,
        name: str,
        command: list[str],
        timeout_seconds: int | None = None,
        is_background: bool = True,
        max_retries: int | None = None,
        retry_backoff_seconds: int = 2,
    ) -> None:
        """Queue a shell ``command`` to run in a background thread."""
        if timeout_seconds is None:
            env_timeout = os.getenv("TASK_QUEUE_TIMEOUT_SECONDS", "").strip()
            if env_timeout:
                try:
                    timeout_seconds = int(env_timeout)
                except ValueError:
                    timeout_seconds = None
        if max_retries is None:
            env_retries = os.getenv("TASK_QUEUE_MAX_RETRIES", "").strip()
            if env_retries:
                try:
                    max_retries = max(0, int(env_retries))
                except ValueError:
                    max_retries = 0
            else:
                max_retries = 0
        with self._lock:
            if name in self._tasks and self._tasks[name]["status"] in {
                "queued",
                "running",
            }:
                msg = f"Task '{name}' already in progress"
                raise ValueError(msg)
            self._tasks[name] = {
                "status": "queued",
                "output": [],
                "is_background": is_background,
                "timeout_seconds": timeout_seconds,
                "max_retries": max_retries,
                "retry_backoff_seconds": retry_backoff_seconds,
                "return_code": None,
                "attempts": 0,
                "started_at": None,
                "ended_at": None,
            }

        thread = threading.Thread(
            target=self._run_command,
            args=(name, command, timeout_seconds, max_retries, retry_backoff_seconds),
            daemon=is_background,
        )
        thread.start()

    # Convenience wrappers ------------------------------------------------
    def queue_lint(self) -> None:
        """Queue repository linting via flake8."""
        self.queue_command("lint", ["python", "-m", "flake8", "src"])

    def queue_tests(self) -> None:
        """Queue running the pytest suite."""
        self.queue_command("tests", ["pytest"])

    def queue_docs(self) -> None:
        """Queue Sphinx documentation build."""
        build_dir = Path("docs/_build")
        build_dir.mkdir(parents=True, exist_ok=True)
        self.queue_command("docs", ["sphinx-build", "docs", str(build_dir)])

    # Status inspection ---------------------------------------------------
    def status(self) -> dict[str, dict[str, Any]]:
        """Return a snapshot of task statuses and accumulated output."""
        with self._lock:
            return {
                name: {
                    "status": info["status"],
                    "output": list(info["output"]),
                    "is_background": info.get("is_background", True),
                    "timeout_seconds": info.get("timeout_seconds"),
                    "max_retries": info.get("max_retries", 0),
                    "retry_backoff_seconds": info.get("retry_backoff_seconds", 2),
                    "attempts": info.get("attempts", 0),
                    "return_code": info.get("return_code"),
                    "started_at": info.get("started_at"),
                    "ended_at": info.get("ended_at"),
                }
                for name, info in self._tasks.items()
            }

    def print_status(self) -> None:
        """Print status information for all tasks."""
        snapshot = self.status()
        for info in snapshot.values():
            for _line in info["output"][-5:]:
                pass


# Global queue instance for convenience -----------------------------------
task_queue = TaskQueue()


def queue_lint() -> None:  # pragma: no cover - thin wrappers
    task_queue.queue_lint()


def queue_tests() -> None:  # pragma: no cover
    task_queue.queue_tests()


def queue_docs() -> None:  # pragma: no cover
    task_queue.queue_docs()


def status() -> dict[str, dict[str, Any]]:  # pragma: no cover
    return task_queue.status()


def main() -> None:  # pragma: no cover - simple CLI helper
    import argparse

    parser = argparse.ArgumentParser(description="Background task queue")
    parser.add_argument(
        "command",
        choices=["lint", "tests", "docs", "status"],
        help="Task to queue or 'status' to view running tasks",
    )
    args = parser.parse_args()

    if args.command == "lint":
        queue_lint()
    elif args.command == "tests":
        queue_tests()
    elif args.command == "docs":
        queue_docs()
    else:
        task_queue.print_status()
        return

    # Keep printing status until all tasks complete
    while True:
        task_queue.print_status()
        with task_queue._lock:
            if all(
                info["status"] not in {"queued", "running"} for info in task_queue._tasks.values()
            ):
                break
        time.sleep(1)


if __name__ == "__main__":
    main()
