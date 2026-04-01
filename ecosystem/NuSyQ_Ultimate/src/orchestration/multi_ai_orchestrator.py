"""Lightweight in-process MultiAIOrchestrator fallback."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from queue import Empty, PriorityQueue
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    BACKGROUND = 30
    NORMAL = 20
    HIGH = 10


@dataclass(order=True)
class OrchestrationTask:
    sort_index: int = field(init=False, repr=False)
    task_id: str
    task_type: str
    content: str
    context: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: float = field(default_factory=time.time, compare=False)

    def __post_init__(self) -> None:
        self.sort_index = self.priority.value


class MultiAIOrchestrator:
    """Queue-driven fallback orchestrator used by bootstrap scripts."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs
        self.task_queue: PriorityQueue = PriorityQueue()
        self._results: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._running = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._sequence = 0

    def start_orchestration(self) -> None:
        """Start a background worker that drains queued orchestration tasks."""
        if self._running.is_set():
            return
        self._running.set()
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="nusyq-multi-ai-orchestrator",
            daemon=True,
        )
        self._worker_thread.start()
        logger.info("MultiAIOrchestrator worker started")

    def stop_orchestration(self, timeout: float = 2.0) -> None:
        """Stop worker loop gracefully."""
        self._running.clear()
        if self._worker_thread:
            self._worker_thread.join(timeout=timeout)
            self._worker_thread = None

    def submit_task(
        self,
        *,
        task_type: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        task_id: Optional[str] = None,
    ) -> str:
        """Create and enqueue a task."""
        self._sequence += 1
        created_task = OrchestrationTask(
            task_id=task_id or f"{task_type}_{uuid4().hex[:10]}",
            task_type=task_type,
            content=content,
            context=context or {},
            priority=priority,
        )
        self.task_queue.put((created_task.priority.value, self._sequence, created_task))
        return created_task.task_id

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Return a processed task result if available."""
        with self._lock:
            return self._results.get(task_id)

    def _extract_task(self, queue_item: Any) -> Optional[OrchestrationTask]:
        if isinstance(queue_item, OrchestrationTask):
            return queue_item
        if isinstance(queue_item, tuple):
            for part in reversed(queue_item):
                if isinstance(part, OrchestrationTask):
                    return part
        return None

    def _worker_loop(self) -> None:
        while self._running.is_set():
            try:
                item = self.task_queue.get(timeout=0.5)
            except Empty:
                continue
            task = self._extract_task(item)
            if task is None:
                self.task_queue.task_done()
                continue
            result = self._process_task(task)
            with self._lock:
                self._results[task.task_id] = result
            self.task_queue.task_done()

    def _process_task(self, task: OrchestrationTask) -> Dict[str, Any]:
        """Process a queued task with deterministic fallback behavior."""
        if task.task_type.lower() == "ping":
            payload: Dict[str, Any] = {"pong": True, "echo": task.content}
        else:
            payload = {"echo": task.content, "context": task.context}
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "success": True,
            "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "result": payload,
        }
