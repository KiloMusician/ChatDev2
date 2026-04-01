"""Zen-Engine Orchestrator: Multi-Agent Coordination Hub

Coordinates all agents (Copilot, Ollama, ChatDev, custom systems),
unifies rule access, error capture, and session memory.

Part of the Recursive Zen-Engine architecture.

OmniTag: [zen-engine, orchestration, multi-agent, coordination]
MegaTag: ZEN_ENGINE⨳ORCHESTRATOR⦾AGENT_HARMONY→∞
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """Describes an agent's capabilities and preferences."""

    name: str
    type: str  # copilot, ollama, chatdev, custom
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    preferred_rules: list[str] = field(default_factory=list)
    last_active: str | None = None
    success_rate: float = 1.0


@dataclass
class SessionContext:
    """Tracks current session state across all agents."""

    session_id: str
    start_time: str
    agents_active: list[str] = field(default_factory=list)
    errors_captured: int = 0
    rules_triggered: list[str] = field(default_factory=list)
    wisdom_shared: int = 0
    agent_feedback: dict[str, Any] = field(default_factory=dict)


class ZenOrchestrator:
    """Central coordination hub for the Zen-Engine ecosystem.

    Responsibilities:
    - Register and manage agents
    - Route errors to appropriate handlers
    - Provide agent-specific rule views
    - Track learning and feedback
    - Coordinate multi-agent wisdom sharing
    """

    def __init__(
        self,
        codex_path: Path | None = None,
        agents_index_path: Path | None = None,
    ):
        """Initialize the orchestrator."""
        self.codex_path = codex_path or Path("zen_engine/codex/zen.json")
        self.agents_index = agents_index_path or Path("zen_engine/codex/indexes/agents.json")
        self.agents: dict[str, AgentCapability] = self._load_agents()
        self.session = self._init_session()
        self.codex = self._load_codex()

        logger.info(f"Orchestrator initialized with {len(self.agents)} registered agents")

    def _init_session(self) -> SessionContext:
        """Initialize a new session."""
        return SessionContext(
            session_id=f"zen_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_time=datetime.now().isoformat(),
        )

    def _load_agents(self) -> dict[str, AgentCapability]:
        """Load registered agents from index."""
        if not self.agents_index.exists():
            logger.info("No agents index found, creating default")
            return self._default_agents()

        try:
            with open(self.agents_index, encoding="utf-8") as f:
                data = json.load(f)
            return {
                name: AgentCapability(**agent_data)
                for name, agent_data in data.get("agents", {}).items()
            }
        except Exception as e:
            logger.error(f"Failed to load agents: {e}")
            return self._default_agents()

    def _default_agents(self) -> dict[str, AgentCapability]:
        """Create default agent registry."""
        return {
            "copilot": AgentCapability(
                name="copilot",
                type="copilot",
                strengths=[
                    "code_completion",
                    "refactoring",
                    "documentation",
                    "real_time_assistance",
                ],
                weaknesses=["long_running_tasks", "external_api_calls"],
            ),
            "ollama": AgentCapability(
                name="ollama",
                type="ollama",
                strengths=[
                    "local_inference",
                    "privacy",
                    "offline_operation",
                    "model_variety",
                ],
                weaknesses=["requires_local_resources", "slower_than_cloud"],
            ),
            "chatdev": AgentCapability(
                name="chatdev",
                type="chatdev",
                strengths=[
                    "multi_agent_collaboration",
                    "software_engineering",
                    "project_scaffolding",
                ],
                weaknesses=["setup_complexity", "requires_coordination"],
            ),
        }

    def _load_codex(self) -> dict[str, Any]:
        """Load the ZenCodex."""
        if not self.codex_path.exists():
            logger.warning(f"Codex not found at {self.codex_path}")
            return {"rules": []}

        try:
            with open(self.codex_path, encoding="utf-8") as f:
                codex_data: dict[str, Any] = json.load(f)
                return codex_data
        except Exception as e:
            logger.error(f"Failed to load codex: {e}")
            return {"rules": []}

    def register_agent(self, agent: AgentCapability):
        """Register a new agent or update existing one."""
        self.agents[agent.name] = agent
        active_list: list[str] = self.session.agents_active
        active_list.append(agent.name)
        logger.info(f"Agent registered: {agent.name} ({agent.type})")

    def capture_error(
        self, error_event: dict[str, Any], agent_name: str | None = None
    ) -> dict[str, Any]:
        """Capture an error event and route to appropriate handlers.

        Args:
            error_event: Structured error event
            agent_name: Name of the agent reporting the error

        Returns:
            Response with matched rules and suggestions
        """
        self.session.errors_captured += 1

        # Find matching rules
        matched_rules = self._match_error_to_rules(error_event)

        if matched_rules:
            self.session.rules_triggered.extend([r["id"] for r in matched_rules])

        # Generate response
        response = {
            "matched_rules": [r["id"] for r in matched_rules],
            "suggestions": self._aggregate_suggestions(matched_rules),
            "agent_advice": self._tailor_advice_for_agent(matched_rules, agent_name),
        }

        return response

    def _match_error_to_rules(self, error_event: dict[str, Any]) -> list[dict[str, Any]]:
        """Match error event to codex rules."""
        rules = self.codex.get("rules", [])
        matched = []

        error_lines = error_event.get("error_lines", [])
        patterns_detected = error_event.get("patterns_detected", [])

        for rule in rules:
            triggers = rule.get("triggers", {})

            # Check error text matches
            error_markers = triggers.get("errors", [])
            if any(
                any(marker.lower() in line.lower() for marker in error_markers)
                for line in error_lines
            ):
                matched.append(rule)
                continue

            # Check pattern matches
            if any(
                pattern in patterns_detected for pattern in triggers.get("command_patterns", [])
            ):
                matched.append(rule)

        return matched

    def _aggregate_suggestions(self, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Aggregate suggestions from multiple rules."""
        all_suggestions = []

        for rule in rules:
            for suggestion in rule.get("suggestions", []):
                all_suggestions.append(
                    {
                        "from_rule": rule["id"],
                        "strategy": suggestion.get("strategy"),
                        "example": suggestion.get("example"),
                        "when_to_use": suggestion.get("when_to_use"),
                    }
                )

        return all_suggestions

    def _tailor_advice_for_agent(
        self, rules: list[dict[str, Any]], agent_name: str | None
    ) -> dict[str, Any]:
        """Tailor advice based on agent capabilities."""
        if not agent_name or agent_name not in self.agents:
            return {"general": "Apply suggested fixes"}

        agent = self.agents[agent_name]

        # Filter suggestions based on agent strengths
        tailored: dict[str, Any] = {"agent": agent_name, "type": agent.type, "advice": []}

        for rule in rules:
            lesson = rule.get("lesson", {})
            tailored["advice"].append(
                {
                    "rule": rule["id"],
                    "message": lesson.get("short"),
                    "priority": (
                        "high"
                        if any(tag in agent.strengths for tag in rule.get("tags", []))
                        else "normal"
                    ),
                }
            )

        return tailored

    def get_agent_view(self, agent_name: str) -> dict[str, Any]:
        """Get a personalized codex view for an agent."""
        if agent_name not in self.agents:
            logger.warning(f"Unknown agent: {agent_name}")
            return {}

        agent = self.agents[agent_name]
        rules = self.codex.get("rules", [])

        # Filter and rank rules for this agent
        relevant_rules = []
        for rule in rules:
            tags = rule.get("tags", [])
            relevance = sum(1 for tag in tags if tag in agent.strengths)

            if relevance > 0 or agent.type in tags:
                relevant_rules.append({"rule": rule, "relevance": relevance})

        # Sort by relevance
        relevant_rules.sort(key=lambda x: x["relevance"], reverse=True)

        return {
            "agent": agent_name,
            "capabilities": agent.strengths,
            "rules_count": len(relevant_rules),
            "top_rules": [r["rule"]["id"] for r in relevant_rules[:10]],
        }

    def record_feedback(self, agent_name: str, rule_id: str, helpful: bool):
        """Record agent feedback on rule usefulness."""
        if agent_name not in self.session.agent_feedback:
            self.session.agent_feedback[agent_name] = {}

        feedback = self.session.agent_feedback[agent_name]
        if rule_id not in feedback:
            feedback[rule_id] = {"helpful": 0, "not_helpful": 0}

        if helpful:
            feedback[rule_id]["helpful"] += 1
        else:
            feedback[rule_id]["not_helpful"] += 1

        logger.info(
            f"Feedback recorded: {agent_name} found {rule_id} {'helpful' if helpful else 'not helpful'}"
        )

    def get_session_summary(self) -> dict[str, Any]:
        """Get summary of current session."""
        return {
            "session_id": self.session.session_id,
            "duration": (
                datetime.now() - datetime.fromisoformat(self.session.start_time)
            ).total_seconds(),
            "agents_active": self.session.agents_active,
            "errors_captured": self.session.errors_captured,
            "rules_triggered": len(set(self.session.rules_triggered)),
            "wisdom_shared": self.session.wisdom_shared,
            "top_rules": self._get_top_rules(),
        }

    def _get_top_rules(self) -> list[str]:
        """Get most frequently triggered rules in session."""
        from collections import Counter

        counts = Counter(self.session.rules_triggered)
        return [rule for rule, _ in counts.most_common(5)]


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    orchestrator = ZenOrchestrator()
    print(orchestrator.get_session_summary())
