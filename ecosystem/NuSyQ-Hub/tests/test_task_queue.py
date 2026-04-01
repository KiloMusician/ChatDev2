#!/usr/bin/env python3
"""Tests for the background task queue"""

import time

from src.system.task_queue import TaskQueue

OmniTag = {
    "purpose": "testing_task_queue",
    "tags": ["Python", "Testing"],
    "evolution_stage": "v1.0",
}


def test_queue_command_echo():
    queue = TaskQueue()
    queue.queue_command("echo", ["python", "-c", "print('hello')"])

    for _ in range(50):  # wait up to ~5s
        status = queue.status()["echo"]["status"]
        if status not in {"queued", "running"}:
            break
        time.sleep(0.1)

    result = queue.status()["echo"]
    assert result["status"] == "success"
    assert "hello" in "\n".join(result["output"])


def test_queue_command_retries_and_reports_attempts():
    queue = TaskQueue()
    queue.queue_command(
        "always_fail",
        ["python", "-c", "import sys; sys.exit(2)"],
        max_retries=1,
        retry_backoff_seconds=0,
    )

    for _ in range(80):
        status = queue.status()["always_fail"]["status"]
        if status not in {"queued", "running"} and not status.startswith("retrying"):
            break
        time.sleep(0.1)

    result = queue.status()["always_fail"]
    assert result["status"].startswith("failed")
    assert result["attempts"] == 2
