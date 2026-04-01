"""Epistemic-Operational Lattice: Planning Plane.

Converts a world state + objective into ordered action candidates by:
1. **Intent Parsing:** Extract what the user actually wants
2. **Capability Matching:** Which agents can do what's needed
3. **Action Generation:** Create candidate actions with preconditions/postconditions
4. **Ordering:** Prioritize by policy, risk, cost, dependency order

Usage:
    from src.core.plan_from_world_state import PlanGenerator
    planner = PlanGenerator()
    actions = planner.plan_from_state(world_state, user_objective="Analyze the errors")
    for action in actions:
        print(
            f"  Agent: {action['agent']}, Task: {action['task_type']}, "
            f"Risk: {action['risk_score']}"
        )
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar
from uuid import uuid4

logger = logging.getLogger(__name__)


# --- Enums & Constants ---


class TaskType(Enum):
    """High-level task categories (maps to agent capability set)."""

    ANALYSIS = "analysis"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    POLICY_EVALUATION = "policy_evaluation"


class AgentType(Enum):
    """Agent types available in NuSyQ ecosystem."""

    OLLAMA = "ollama"
    LM_STUDIO = "lmstudio"
    CHATDEV = "chatdev"
    COPILOT = "copilot"
    CLAUDE_CLI = "claude_cli"
    CONSCIOUSNESS = "consciousness"
    QUANTUM_RESOLVER = "quantum_resolver"
    FACTORY = "factory"
    OPENCLAW = "openclaw"


class RiskLevel(Enum):
    """Risk level assessment (used by policy gates)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# --- Typed Action Model ---


@dataclass
class Action:
    """A proposed action the orchestrator can take."""

    action_id: str
    timestamp: str
    agent: AgentType
    task_type: TaskType
    description: str
    preconditions: list[str]  # Must be true before execution
    postconditions: list[str]  # Should be true after execution
    estimated_cost: dict[str, Any]  # {"tokens": N, "time_s": N, "cpu": N}
    risk_score: float  # 0.0-1.0
    policy_category: str  # "SECURITY", "BUGFIX", "FEATURE", etc.
    time_sensitivity: str  # "low", "normal", "high", "critical"
    quest_dependency: str | None = None  # quest_id this action contributes to
    rollback_hint: str | None = None  # How to undo if things go wrong
    optimization: dict[str, float] = field(default_factory=dict)
    selection_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize action to dict (returns copies of mutable fields)."""
        return {
            "action_id": self.action_id,
            "timestamp": self.timestamp,
            "agent": self.agent.value,
            "task_type": self.task_type.value,
            "description": self.description,
            "preconditions": list(self.preconditions),
            "postconditions": list(self.postconditions),
            "estimated_cost": dict(self.estimated_cost),
            "risk_score": self.risk_score,
            "policy_category": self.policy_category,
            "time_sensitivity": self.time_sensitivity,
            "quest_dependency": self.quest_dependency,
            "rollback_hint": self.rollback_hint,
            "optimization": dict(self.optimization),
            "selection_score": self.selection_score,
        }


# --- Capability Registry ---


class CapabilityRegistry:
    """Maps agents to their capabilities (models, latency, cost)."""

    AGENT_CAPABILITIES: ClassVar[dict] = {
        AgentType.OLLAMA: {
            "task_types": [TaskType.ANALYSIS, TaskType.DEBUGGING, TaskType.CODE_REVIEW],
            "models": ["qwen2.5-coder:14b", "deepseek-coder-v2:16b", "gemma2:9b"],
            "avg_latency_s": 3.0,
            "cost_tier": "low",
            "success_rate": 0.92,
        },
        AgentType.LM_STUDIO: {
            "task_types": [TaskType.ANALYSIS, TaskType.CODE_GENERATION],
            "models": ["lm-studio-model:13b"],
            "avg_latency_s": 2.5,
            "cost_tier": "low",
            "success_rate": 0.88,
        },
        AgentType.CHATDEV: {
            "task_types": [TaskType.CODE_GENERATION, TaskType.TESTING],
            "models": ["chatdev-team"],
            "avg_latency_s": 60.0,  # Multi-agent team is slower
            "cost_tier": "medium",
            "success_rate": 0.85,
        },
        AgentType.COPILOT: {
            "task_types": [TaskType.CODE_GENERATION, TaskType.CODE_REVIEW, TaskType.REFACTORING],
            "models": ["copilot-gpt4"],
            "avg_latency_s": 1.0,
            "cost_tier": "high",
            "success_rate": 0.94,
        },
        AgentType.CLAUDE_CLI: {
            "task_types": [TaskType.ANALYSIS, TaskType.DOCUMENTATION],
            "models": ["claude-3.5-sonnet"],
            "avg_latency_s": 2.0,
            "cost_tier": "high",
            "success_rate": 0.96,
        },
        AgentType.CONSCIOUSNESS: {
            "task_types": [TaskType.POLICY_EVALUATION],
            "models": ["simulatedverse-consciousness"],
            "avg_latency_s": 0.5,
            "cost_tier": "free",
            "success_rate": 0.99,
        },
        AgentType.QUANTUM_RESOLVER: {
            "task_types": [TaskType.DEBUGGING],
            "models": ["quantum-healing"],
            "avg_latency_s": 5.0,
            "cost_tier": "low",
            "success_rate": 0.87,
        },
        AgentType.FACTORY: {
            "task_types": [TaskType.CODE_GENERATION],
            "models": ["projectfactory-multi"],
            "avg_latency_s": 10.0,
            "cost_tier": "low",
            "success_rate": 0.80,
        },
    }

    @classmethod
    def agents_for_task(cls, task_type: TaskType) -> list[tuple[AgentType, dict[str, Any]]]:
        """Get agents that can perform a task, ranked by success rate."""
        candidates = []
        for agent_type, capabilities in cls.AGENT_CAPABILITIES.items():
            if task_type in capabilities["task_types"]:
                candidates.append((agent_type, capabilities))

        # Sort by success rate (descending)
        candidates.sort(key=lambda x: x[1]["success_rate"], reverse=True)
        return candidates

    @classmethod
    def cost_estimate(
        cls, agent: AgentType, task_type: TaskType, complexity: str = "normal"
    ) -> dict[str, int]:
        """Estimate resource cost for an action."""
        cap = cls.AGENT_CAPABILITIES.get(agent, {})
        base_tokens = {"analysis": 500, "code_generation": 1000, "testing": 800}.get(
            task_type.value, 400
        )
        complexity_mult = {"simple": 0.5, "normal": 1.0, "complex": 2.0}.get(complexity, 1.0)

        latency = cap.get("avg_latency_s", 5.0)
        complexity_time_mult = {"simple": 0.5, "normal": 1.0, "complex": 3.0}.get(complexity, 1.0)

        return {
            "tokens": int(base_tokens * complexity_mult),
            "time_s": int(latency * complexity_time_mult),
            "cpu": 20 if cap.get("cost_tier") == "high" else 10,
        }


# --- Intent Parser ---


class IntentParser:
    """Extract structured intent from user message."""

    @staticmethod
    def parse(user_message: str, world_state: dict[str, Any]) -> dict[str, Any]:
        """Parse intent to (task_type, description, required_capabilities)."""
        msg_lower = user_message.lower()

        # Simple keyword matching (v0.1; should be upgraded to semantic parsing)
        if any(kw in msg_lower for kw in ["analyze", "analysis", "review", "scan"]):
            return {
                "task_type": TaskType.ANALYSIS,
                "description": "Analyze codebase for issues",
                "required_capabilities": ["context_understanding", "static_analysis"],
                "complexity": "normal",
            }
        elif any(kw in msg_lower for kw in ["generate", "create", "write", "implement"]):
            return {
                "task_type": TaskType.CODE_GENERATION,
                "description": "Generate code for feature/fix",
                "required_capabilities": ["coding", "architecture"],
                "complexity": "complex",
            }
        elif any(kw in msg_lower for kw in ["review", "audit", "inspect"]):
            return {
                "task_type": TaskType.CODE_REVIEW,
                "description": "Review code for quality",
                "required_capabilities": ["code_review", "quality_assessment"],
                "complexity": "normal",
            }
        elif any(kw in msg_lower for kw in ["debug", "fix", "error", "broken"]):
            return {
                "task_type": TaskType.DEBUGGING,
                "description": "Debug and fix issues",
                "required_capabilities": ["debugging", "problem_solving"],
                "complexity": "complex",
            }
        elif any(kw in msg_lower for kw in ["test", "testing"]):
            return {
                "task_type": TaskType.TESTING,
                "description": "Generate and run tests",
                "required_capabilities": ["testing", "test_generation"],
                "complexity": "normal",
            }
        else:
            return {
                "task_type": TaskType.ANALYSIS,
                "description": "Analyze the situation",
                "required_capabilities": ["context_understanding"],
                "complexity": "simple",
            }


# --- Action Generator ---


class ActionGenerator:
    """Generate candidate actions from capability + intent."""

    @staticmethod
    def _compute_optimization(
        success_rate: float,
        risk_score: float,
        cost: dict[str, Any],
    ) -> tuple[dict[str, float], float]:
        """Compute risk-adjusted efficiency metrics (Hacknet/Bitburner-style ROI)."""
        tokens = max(int(cost.get("tokens", 0) or 0), 1)
        time_s = max(int(cost.get("time_s", 0) or 0), 1)
        cpu = max(int(cost.get("cpu", 0) or 0), 1)

        risk_adjusted_success = max(success_rate * (1.0 - risk_score), 0.0)
        token_efficiency = risk_adjusted_success / tokens
        time_efficiency = risk_adjusted_success / time_s

        # Penalize expensive actions across token/time/cpu dimensions.
        weighted_cost = tokens + (25 * time_s) + (10 * cpu)
        roi_score = (risk_adjusted_success * 1000.0) / max(weighted_cost, 1.0)

        optimization = {
            "success_rate": round(float(success_rate), 4),
            "risk_adjusted_success": round(float(risk_adjusted_success), 6),
            "token_efficiency": round(float(token_efficiency), 8),
            "time_efficiency": round(float(time_efficiency), 8),
            "weighted_cost": round(float(weighted_cost), 2),
            "roi_score": round(float(roi_score), 6),
        }
        return optimization, float(roi_score)

    @staticmethod
    def generate_actions(
        task_type: TaskType,
        description: str,
        world_state: dict[str, Any],
        max_candidates: int = 5,
    ) -> list[Action]:
        """Generate ordered list of action candidates."""
        actions = []

        # Get agents that can do this task
        candidates = CapabilityRegistry.agents_for_task(task_type)

        if not candidates:
            logger.warning(f"No agents available for task: {task_type}")
            return actions

        # Convert world state policy state to risk assessment
        policy_state = world_state.get("policy_state", {})
        policy_state.get("safety_gates", {}).get("max_risk_score", 0.7)

        for agent_type, capabilities in candidates[:max_candidates]:
            # Estimate cost + risk
            complexity = "normal"  # Inferred from task type
            cost = CapabilityRegistry.cost_estimate(agent_type, task_type, complexity)

            # Risk assessment: based on agent success rate + policy constraints
            success_rate = float(capabilities.get("success_rate", 0.0) or 0.0)
            base_risk = 1.0 - success_rate
            policy_risk = 0.1 if task_type == TaskType.CODE_GENERATION else 0.05
            risk_score = min(base_risk + policy_risk, 1.0)
            optimization, selection_score = ActionGenerator._compute_optimization(
                success_rate=success_rate,
                risk_score=risk_score,
                cost=cost,
            )

            # Check budget constraints
            budget = world_state.get("policy_state", {}).get("resource_budgets", {})
            token_budget = budget.get("token_budget_remaining", 5000)
            budget.get("time_budget_remaining_s", 300)

            # Skip if insufficient budget + high risk
            if cost["tokens"] > token_budget and risk_score > 0.5:
                continue

            action = Action(
                action_id=str(uuid4()),
                timestamp=datetime.now(UTC).isoformat(),
                agent=agent_type,
                task_type=task_type,
                description=f"{description} using {agent_type.value}",
                preconditions=[
                    f"Agent {agent_type.value} is online",
                    f"Available tokens >= {cost['tokens']}",
                    f"Available time >= {cost['time_s']}s",
                ],
                postconditions=[
                    "Task completed with status recorded",
                    "Receipt logged to action_receipt_ledger",
                ],
                estimated_cost=cost,
                risk_score=risk_score,
                policy_category="ANALYSIS" if task_type == TaskType.ANALYSIS else "FEATURE",
                time_sensitivity="normal",
                rollback_hint=f"Delete action_id {uuid4()} from ledger and revert quest status",
                optimization=optimization,
                selection_score=selection_score,
            )
            actions.append(action)

        return actions


# --- Plan Generator (High Level) ---


class PlanGenerator:
    """High-level planner: objective → ordered action list."""

    def __init__(self):
        """Initialize PlanGenerator."""
        self.intent_parser = IntentParser()
        self.action_gen = ActionGenerator()

    def plan_from_state(
        self,
        world_state: dict[str, Any],
        user_objective: str = "",
    ) -> list[Action]:
        """Convert world state + objective into ordered action plan.

        Returns actions ordered by:
        1. Time sensitivity
        2. Policy priority (SECURITY > BUGFIX > FEATURE)
        3. Cost (low cost first)
        4. Success probability (high success first)
        """
        # Parse user intent
        intent = self.intent_parser.parse(user_objective, world_state)

        # Generate action candidates
        actions = self.action_gen.generate_actions(
            intent["task_type"],
            intent["description"],
            world_state,
            max_candidates=5,
        )

        # Sort by priority
        priority_map = {
            "critical": 1,
            "high": 2,
            "normal": 3,
            "low": 4,
        }
        policy_priority_map = {
            "SECURITY": 1,
            "BUGFIX": 2,
            "FEATURE": 3,
            "REFACTOR": 4,
            "DOCS": 5,
        }

        actions.sort(
            key=lambda a: (
                priority_map.get(a.time_sensitivity, 99),
                policy_priority_map.get(a.policy_category, 99),
                -a.selection_score,  # Higher risk-adjusted ROI first
                a.estimated_cost["tokens"],  # Lower cost first
                a.estimated_cost.get("time_s", 999),  # Shorter time first
            )
        )

        return actions


def plan_from_world_state(
    world_state: dict[str, Any],
    user_objective: str = "",
) -> dict[str, Any]:
    """Convenience function that returns planning output as a structured dict.

    Returns:
        {
            "objective": {...},
            "actions": [Action1, Action2, ...],
            "metadata": {...}
        }
    """
    planner = PlanGenerator()
    actions = planner.plan_from_state(world_state, user_objective)

    return {
        "objective": {
            "user_intent": user_objective,
            "parsed_task_type": actions[0].task_type.value if actions else "unknown",
            "required_capabilities": [],
        },
        "actions": [a.to_dict() for a in actions],
        "metadata": {
            "total_candidates": len(actions),
            "timestamp": datetime.now(UTC).isoformat(),
            "schema_version": "0.1",
        },
    }


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)

    # Sample world state
    sample_world_state = {
        "policy_state": {
            "resource_budgets": {
                "token_budget_remaining": 5000,
                "time_budget_remaining_s": 300,
            },
            "safety_gates": {
                "max_risk_score": 0.7,
            },
        },
    }

    plan = plan_from_world_state(sample_world_state, "Analyze the codebase for errors")
    logger.info(json.dumps(plan, indent=2))
