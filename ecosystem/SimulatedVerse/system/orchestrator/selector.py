from __future__ import annotations
import yaml
from typing import List
from .task_types import Plan, Task, Decision
from .history import History
from .scorer import score_task

def load_plan(path: str) -> Plan:
    with open(path,"r",encoding="utf-8") as f:
        data = yaml.safe_load(f)
    tasks = [Task(**t) for t in data["tasks"]]
    return Plan(meta=data["meta"], weights=data["weights"], paths=data["paths"], tasks=tasks)

def select_next(plan: Plan, history: History, limit: int=5) -> List[Decision]:
    scored: List[Decision] = []
    for t in plan.tasks:
        s, reasons, action = score_task(t, plan.weights, plan.paths)
        # slight reinforcement if historically good
        past = history.recent_scores(t.id)
        if past:
            boost = sum(past)/max(1,len(past)) * 0.05
            s += boost; reasons.append(f"history_boost({boost:.2f})")
        scored.append(Decision(task_id=t.id, score=s, reasons=reasons, chosen_action=action))
    # sort best first
    scored.sort(key=lambda d: d.score, reverse=True)
    return scored[:limit]