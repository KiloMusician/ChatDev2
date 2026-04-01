"""Colonist-style agent/task scheduler (lightweight).

Provides:
- Agent: simple profile with skills, preferences, capabilities, state
- Task: minimal task metadata
- Scheduler: in-memory queue and assignment logic using skill+preference scoring

This module is intentionally small and dependency-light so it can be
integrated into larger orchestrators (see existing KILO orchestrators).
"""

from __future__ import annotations

import heapq
import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Agent:
    id: str
    skills: dict[str, int] = field(default_factory=dict)
    preferences: dict[str, int] = field(default_factory=dict)  # positive => likes
    capabilities: list[str] = field(default_factory=list)
    current_task: str | None = None
    state: str = "available"  # available, busy, resting
    metrics: dict[str, Any] = field(default_factory=lambda: {"completed": 0, "avg_time": None})

    def score_for(self, task: Task, skill_weight: float = 1.0, pref_weight: float = 0.5) -> float:
        skill_val = self.skills.get(task.skill_req, 0)
        pref_val = self.preferences.get(task.skill_req, 0)
        # If agent lacks capability required by the task, return -inf
        if task.capability and task.capability not in self.capabilities:
            return float("-inf")
        return skill_weight * skill_val + pref_weight * pref_val


@dataclass(order=True)
class Task:
    priority: int
    id: str = field(compare=False)
    skill_req: str = field(compare=False)
    min_skill: int = field(compare=False)
    context: dict[str, Any] = field(default_factory=dict, compare=False)
    capability: str | None = field(default=None, compare=False)
    created_at: float = field(default_factory=time.time, compare=False)
    status: str = field(default="queued", compare=False)  # queued, in_progress, done, failed


class Scheduler:
    """Very small scheduler: queue tasks (heap by priority) and assign to agents."""

    def __init__(self) -> None:
        """Initialize Scheduler."""
        self.agents: dict[str, Agent] = {}
        self._task_heap: list[tuple[int, float, Task]] = []  # (priority, timestamp, Task)
        self.assigned: dict[str, str] = {}  # task_id -> agent_id

    def register_agent(self, agent: Agent) -> None:
        self.agents[agent.id] = agent

    def enqueue_task(self, task: Task) -> None:
        # Python heapq is min-heap; use negative priority for high-first
        heapq.heappush(self._task_heap, (-task.priority, task.created_at, task))

    def pop_task(self) -> Task | None:
        if not self._task_heap:
            return None
        _, _, task = heapq.heappop(self._task_heap)
        return task

    def assign_once(self) -> list[tuple[Task, Agent | None]]:
        """Try to assign all queued tasks once. Returns list of (task, agent_or_None)."""
        results: list[tuple[Task, Agent | None]] = []
        remaining: list[tuple[int, float, Task]] = []

        while self._task_heap:
            pri, ts, task = heapq.heappop(self._task_heap)
            # Find best available agent
            best_agent: Agent | None = None
            best_score = float("-inf")
            for agent in self.agents.values():
                if agent.state != "available":
                    continue
                skill_val = agent.skills.get(task.skill_req, 0)
                if skill_val < task.min_skill:
                    continue
                score = agent.score_for(task)
                if score > best_score:
                    best_score = score
                    best_agent = agent

            if best_agent and best_score > float("-inf"):
                # assign
                best_agent.current_task = task.id
                best_agent.state = "busy"
                task.status = "in_progress"
                self.assigned[task.id] = best_agent.id
                results.append((task, best_agent))
            else:
                # no suitable agent now; requeue
                remaining.append((pri, ts, task))
                results.append((task, None))

        # restore remaining tasks
        for item in remaining:
            heapq.heappush(self._task_heap, item)

        return results

    def complete_task(
        self,
        task_id: str,
        agent_id: str,
        success: bool = True,
        duration: float | None = None,
    ) -> None:
        agent = self.agents.get(agent_id)
        if not agent:
            return
        if agent.current_task != task_id:
            return
        agent.current_task = None
        agent.state = "available"
        # update metrics
        metrics = agent.metrics
        metrics["completed"] = metrics.get("completed", 0) + (1 if success else 0)
        if duration is not None:
            prev = metrics.get("avg_time")
            if prev is None:
                metrics["avg_time"] = duration
            else:
                metrics["avg_time"] = (prev + duration) / 2.0


def demo_run() -> dict[str, Any]:
    """Small demo returning assignment summary for testing or manual runs."""
    s = Scheduler()
    s.register_agent(
        Agent(
            id="alice",
            skills={"coding": 8, "doc": 5},
            preferences={"coding": 1},
            capabilities=["pytest"],
        )
    )
    s.register_agent(
        Agent(
            id="bob",
            skills={"coding": 5, "doc": 8},
            preferences={"doc": 2},
            capabilities=["mkdocs"],
        )
    )

    s.enqueue_task(Task(id="T1", priority=10, skill_req="coding", min_skill=6, capability=None))
    s.enqueue_task(Task(id="T2", priority=5, skill_req="doc", min_skill=5, capability=None))
    assigned = s.assign_once()
    return {
        "assigned": [(t.id, a.id if a else None) for t, a in assigned],
        "agents": {k: v.__dict__ for k, v in s.agents.items()},
    }


if __name__ == "__main__":
    logger.info(demo_run())
