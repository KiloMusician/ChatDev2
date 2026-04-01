"""Planning & execution discipline helpers (Phase 4).

Provides dual-plan scaffolding, early-test checklist, and cost/time telemetry container.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

from src.config.feature_flag_manager import is_feature_enabled


@dataclass
class PlanStep:
    description: str
    status: str = "pending"  # pending, in_progress, done
    notes: str = ""


@dataclass
class PlanBundle:
    high_level: list[PlanStep] = field(default_factory=list)
    microplan: list[PlanStep] = field(default_factory=list)
    early_tests: list[str] = field(default_factory=list)
    telemetry: dict[str, Any] = field(default_factory=dict)


def build_dual_plan(task: str) -> PlanBundle:
    if not is_feature_enabled("planning_discipline_enabled"):
        return PlanBundle()

    # Simple heuristics; can be replaced by LLM-generated plans later
    high_level = [
        PlanStep("Clarify requirements / acceptances"),
        PlanStep("Draft solution approach"),
        PlanStep("Implement core changes"),
        PlanStep("Run tests / lint"),
        PlanStep("Summarize & handoff"),
    ]
    microplan = [
        PlanStep("Identify affected modules/files"),
        PlanStep("Add/adjust tests (early)"),
        PlanStep("Code changes"),
        PlanStep("Run fast tests"),
        PlanStep("Assess blast radius / costs"),
    ]
    early_tests = [
        "Add/verify unit covering new path",
        "Run fast pytest subset",
        "Optional: lint/ruff if cheap",
    ]
    telemetry = {
        "plan_started": time.time(),
        "cost_estimate": {"tokens": 0, "usd": 0},
    }
    return PlanBundle(high_level, microplan, early_tests, telemetry)


def planbundle_to_dict(bundle: PlanBundle) -> dict[str, Any]:
    return {
        "high_level": [asdict(s) for s in bundle.high_level],
        "microplan": [asdict(s) for s in bundle.microplan],
        "early_tests": bundle.early_tests,
        "telemetry": bundle.telemetry,
    }
