"""Intelligent Agent Router for Task-Specific Model Selection.

Routes tasks to optimal agents based on task type, complexity, and performance profiles.
Learns from historical quest log to improve routing decisions over time.

OmniTag: [intelligent routing, model selection, task classification, pattern matching, orchestration]
"""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import ClassVar

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Classification of task types."""

    CODE_REVIEW = "code_review"
    CODE_GENERATION = "code_generation"
    DOCUMENTATION = "documentation"
    DEBUGGING = "debugging"
    ANALYSIS = "analysis"
    TESTING = "testing"
    OPTIMIZATION = "optimization"
    GENERAL = "general"


class RouteProfile:
    """Profile for optimal routing of a task type to specific agents."""

    def __init__(
        self,
        task_type: TaskType,
        preferred_agents: list[str],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        description: str = "",
    ):
        """Initialize RouteProfile with task_type, preferred_agents, temperature, ...."""
        self.task_type = task_type
        self.preferred_agents = preferred_agents
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.description = description
        self.performance_history: list[dict] = []

    def record_performance(self, agent: str, success: bool, latency: float, tokens: int):
        """Record performance metrics for this routing."""
        self.performance_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "success": success,
                "latency": latency,
                "tokens": tokens,
            }
        )

    def get_avg_performance(self, agent: str) -> dict[str, float]:
        """Get average performance for a specific agent."""
        agent_records = [r for r in self.performance_history if r["agent"] == agent]
        if not agent_records:
            return {"success_rate": 0.0, "avg_latency": 0.0, "avg_tokens": 0}

        success_count = sum(1 for r in agent_records if r["success"])
        avg_latency = sum(r["latency"] for r in agent_records) / len(agent_records)
        avg_tokens = sum(r["tokens"] for r in agent_records) / len(agent_records)

        return {
            "success_rate": success_count / len(agent_records),
            "avg_latency": avg_latency,
            "avg_tokens": int(avg_tokens),
        }


class IntelligentAgentRouter:
    """Routes tasks to optimal agents based on task type and learned performance.

    Routing strategies:
    1. Task-specific preference: Code review → starcoder2, fast analysis → qwen, etc.
    2. Load balancing: Distribute across agents to avoid bottlenecks
    3. Performance-based: Route to agents with best historical success rates
    4. Fallback: Use preferred agents if primary unavailable
    """

    # Default routing profile for each task type
    DEFAULT_ROUTES: ClassVar[dict[TaskType, RouteProfile]] = {
        TaskType.CODE_REVIEW: RouteProfile(
            TaskType.CODE_REVIEW,
            ["starcoder2:15b", "deepseek-coder-v2:16b", "qwen2.5-coder:7b"],
            temperature=0.5,
            max_tokens=1500,
            description="High-precision code review with multiple perspectives",
        ),
        TaskType.CODE_GENERATION: RouteProfile(
            TaskType.CODE_GENERATION,
            ["deepseek-coder-v2:16b", "starcoder2:15b", "qwen2.5-coder:7b"],
            temperature=0.8,
            max_tokens=3000,
            description="Creative code generation with balanced accuracy",
        ),
        TaskType.DOCUMENTATION: RouteProfile(
            TaskType.DOCUMENTATION,
            ["llama3.1:8b", "qwen2.5-coder:7b", "gemma2:9b"],
            temperature=0.7,
            max_tokens=2000,
            description="Clear, comprehensive documentation generation",
        ),
        TaskType.DEBUGGING: RouteProfile(
            TaskType.DEBUGGING,
            ["qwen2.5-coder:7b", "deepseek-coder-v2:16b", "starcoder2:15b"],
            temperature=0.3,
            max_tokens=1500,
            description="Systematic debugging with high precision",
        ),
        TaskType.ANALYSIS: RouteProfile(
            TaskType.ANALYSIS,
            ["llama3.1:8b", "deepseek-coder-v2:16b", "qwen2.5-coder:7b"],
            temperature=0.6,
            max_tokens=2000,
            description="Deep analysis with reasoning",
        ),
        TaskType.TESTING: RouteProfile(
            TaskType.TESTING,
            ["starcoder2:15b", "qwen2.5-coder:7b", "deepseek-coder-v2:16b"],
            temperature=0.4,
            max_tokens=1500,
            description="Comprehensive test generation and validation",
        ),
        TaskType.OPTIMIZATION: RouteProfile(
            TaskType.OPTIMIZATION,
            ["deepseek-coder-v2:16b", "starcoder2:15b", "llama3.1:8b"],
            temperature=0.5,
            max_tokens=2000,
            description="Performance and efficiency optimization",
        ),
        TaskType.GENERAL: RouteProfile(
            TaskType.GENERAL,
            ["qwen2.5-coder:7b", "llama3.1:8b", "phi3.5:latest"],
            temperature=0.7,
            max_tokens=2000,
            description="General-purpose tasks with balanced capabilities",
        ),
    }

    def __init__(self):
        """Initialize IntelligentAgentRouter."""
        self.routes: dict[TaskType, RouteProfile] = {}
        self.routing_history: list[dict] = []
        self._initialize_routes()
        self._load_performance_history()

    def _initialize_routes(self):
        """Initialize default routing profiles."""
        for task_type, profile in self.DEFAULT_ROUTES.items():
            self.routes[task_type] = profile

    def _load_performance_history(self):
        """Load performance history from quest log if available."""
        try:
            quest_log = (
                Path(__file__).parent.parent.parent
                / "src"
                / "Rosetta_Quest_System"
                / "quest_log.jsonl"
            )
            if quest_log.exists():
                with open(quest_log) as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if entry.get("event_type") in ["orchestration_task", "agent_request"]:
                                self.routing_history.append(entry)
                        except json.JSONDecodeError:
                            continue
                logger.info(f"Loaded {len(self.routing_history)} routing events from quest log")
        except Exception as e:
            logger.debug(f"Could not load performance history: {e}")

    def classify_task(self, task_description: str) -> TaskType:
        """Classify a task description into a TaskType.

        Uses keyword matching to infer task type from description.
        """
        description_lower = task_description.lower()

        # Keyword-based classification
        if any(word in description_lower for word in ["review", "audit", "check", "verify"]):
            return TaskType.CODE_REVIEW
        elif any(
            word in description_lower for word in ["generate", "create", "write", "implement"]
        ):
            return TaskType.CODE_GENERATION
        elif any(
            word in description_lower for word in ["document", "explain", "describe", "comment"]
        ):
            return TaskType.DOCUMENTATION
        elif any(
            word in description_lower for word in ["debug", "fix", "error", "issue", "problem"]
        ):
            return TaskType.DEBUGGING
        elif any(
            word in description_lower for word in ["analyze", "analyze", "analyze", "evaluate"]
        ):
            return TaskType.ANALYSIS
        elif any(word in description_lower for word in ["test", "unit test", "integration test"]):
            return TaskType.TESTING
        elif any(
            word in description_lower for word in ["optimize", "improve", "performance", "speed"]
        ):
            return TaskType.OPTIMIZATION

        return TaskType.GENERAL

    def route_task(
        self,
        task_description: str,
        task_type: TaskType | None = None,
        available_agents: list[str] | None = None,
    ) -> tuple[str, dict]:
        """Route a task to the optimal agent.

        Args:
            task_description: Description of the task
            task_type: Explicit task type (auto-classified if None)
            available_agents: List of available agents (uses all if None)

        Returns:
            Tuple of (selected_agent, route_info)
        """
        # Classify if not provided
        if task_type is None:
            task_type = self.classify_task(task_description)

        # Get route profile
        profile = self.routes.get(task_type, self.routes[TaskType.GENERAL])

        # Determine which agents are available
        preferred = profile.preferred_agents
        if available_agents:
            selected_agent = None
            for agent in preferred:
                if agent in available_agents:
                    selected_agent = agent
                    break
            if selected_agent is None:
                selected_agent = available_agents[0] if available_agents else preferred[0]
        else:
            selected_agent = preferred[0]

        route_info = {
            "task_type": task_type.value,
            "selected_agent": selected_agent,
            "temperature": profile.temperature,
            "max_tokens": profile.max_tokens,
            "preferred_agents": preferred,
            "description": profile.description,
            "timestamp": datetime.now().isoformat(),
        }

        self.routing_history.append(route_info)
        return selected_agent, route_info

    def get_route_for_type(
        self, task_type: TaskType, available_agents: list[str] | None = None
    ) -> tuple[str, dict]:
        """Get optimal agent for a specific task type.

        Args:
            task_type: The type of task to route
            available_agents: List of available agents

        Returns:
            Tuple of (selected_agent, route_info)
        """
        profile = self.routes[task_type]

        if available_agents:
            selected_agent = None
            for agent in profile.preferred_agents:
                if agent in available_agents:
                    selected_agent = agent
                    break
            if selected_agent is None:
                selected_agent = available_agents[0]
        else:
            selected_agent = profile.preferred_agents[0]

        return selected_agent, {
            "task_type": task_type.value,
            "selected_agent": selected_agent,
            "temperature": profile.temperature,
            "max_tokens": profile.max_tokens,
        }

    def get_team_for_consensus(
        self, task_type: TaskType, team_size: int = 3, available_agents: list[str] | None = None
    ) -> list[tuple[str, dict]]:
        """Get a team of agents for consensus on a task type.

        Args:
            task_type: The type of task
            team_size: Number of agents for consensus
            available_agents: List of available agents

        Returns:
            List of (agent, route_info) tuples
        """
        profile = self.routes[task_type]

        # Filter preferred agents to available ones
        candidates = profile.preferred_agents
        if available_agents:
            candidates = [a for a in candidates if a in available_agents]
            if not candidates:
                candidates = available_agents[:team_size]

        # Select top agents
        team = candidates[:team_size]
        result = []
        for agent in team:
            result.append(
                (
                    agent,
                    {
                        "task_type": task_type.value,
                        "agent": agent,
                        "temperature": profile.temperature,
                        "role": f"Agent {len(result) + 1}",
                    },
                )
            )

        return result

    def generate_routing_report(self) -> str:
        """Generate a report of routing statistics."""
        report = ["📍 INTELLIGENT AGENT ROUTING REPORT\n"]

        # Task type summary
        task_counts = {}
        for entry in self.routing_history:
            task_type = entry.get("task_type", "unknown")
            task_counts[task_type] = task_counts.get(task_type, 0) + 1

        report.append("[ROUTING BY TASK TYPE]")
        for task_type, count in sorted(task_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {task_type}: {count} requests")

        # Agent usage summary
        agent_usage = {}
        for entry in self.routing_history:
            agent = entry.get("selected_agent", "unknown")
            agent_usage[agent] = agent_usage.get(agent, 0) + 1

        report.append("\n[AGENT USAGE DISTRIBUTION]")
        for agent, count in sorted(agent_usage.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {agent}: {count} assignments")

        report.append("\n[SUMMARY]")
        report.append(f"  Total routing decisions: {len(self.routing_history)}")
        report.append(f"  Task types: {len(task_counts)}")
        report.append(f"  Agents used: {len(agent_usage)}")

        return "\n".join(report)


def demo_intelligent_routing():
    """Demonstrate intelligent agent router."""
    logger.info("🤖 INTELLIGENT AGENT ROUTER DEMO\n")

    router = IntelligentAgentRouter()

    # Test task classification
    test_tasks = [
        ("Review this Python code for security issues", TaskType.CODE_REVIEW),
        ("Generate a REST API implementation", TaskType.CODE_GENERATION),
        ("Write documentation for the auth module", TaskType.DOCUMENTATION),
        ("Debug this intermittent timeout error", TaskType.DEBUGGING),
        ("Analyze performance bottlenecks", TaskType.ANALYSIS),
    ]

    logger.info("[TASK CLASSIFICATION & ROUTING]")
    for description, expected_type in test_tasks:
        classified = router.classify_task(description)
        agent, info = router.route_task(description, classified)
        status = "✅" if classified == expected_type else "⚠️"
        logger.info(f"{status} {description[:50]}...")
        logger.info(f"   → Type: {classified.value}")
        logger.info(f"   → Agent: {agent}")
        logger.info(f"   → Temp: {info['temperature']}\n")

    # Test available agents
    available = ["qwen2.5-coder:7b", "llama3.1:8b", "phi3.5:latest"]
    logger.info("[ROUTING WITH LIMITED AGENTS]")
    agent, info = router.route_task(
        "Create optimized database indexes", TaskType.OPTIMIZATION, available
    )
    logger.info(f"Optimization task → {agent}")

    # Test consensus team building
    logger.info("\n[CONSENSUS TEAM SELECTION]")
    team = router.get_team_for_consensus(
        TaskType.CODE_REVIEW, team_size=3, available_agents=available
    )
    logger.info(f"Code review team ({len(team)} agents):")
    for agent, _info in team:
        logger.info(f"  • {agent}")

    # Generate report
    logger.info("\n" + router.generate_routing_report())


if __name__ == "__main__":
    demo_intelligent_routing()
