from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Task:
    id: str
    title: str
    kind: str                  # fix | complete | refactor | test | docs | perf | new
    targets: List[str]
    notes: str = ""
    deps: List[str] = field(default_factory=list)

@dataclass
class Decision:
    task_id: str
    score: float
    reasons: List[str]
    chosen_action: str         # "fix", "write_tests", "refactor", etc.

@dataclass
class Plan:
    meta: Dict
    weights: Dict[str, float]
    paths: Dict[str, List[str]]
    tasks: List[Task]