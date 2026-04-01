#!/usr/bin/env python3
"""Terminal Intelligence Orchestrator - Master Terminal Coordination System.

Wires all 23 specialized terminals with intelligent routing, automation, and enhancement.
Each terminal serves a specific purpose in the AI development ecosystem.

🏷️ OmniTag: terminal_orchestration|multi_ai_coordination|intelligent_routing
🏷️ MegaTag: quantum_terminal_nexus|consciousness_routing|adaptive_intelligence
🏷️ RSHTS: ⟡ Master terminal conductor connecting 23 specialized intelligence streams ⟡

Terminal Roster (23 terminals):
1.  🤖 Claude        - Claude AI agent output
2.  🧩 Copilot       - GitHub Copilot agent output
3.  🧠 Codex         - OpenAI Codex agent output
4.  🏗️ ChatDev       - ChatDev multi-agent team output
5.  🏛️ AI Council    - Multi-AI consensus and voting
6.  🔗 Intermediary  - Inter-agent message passing
7.  🔥 Errors        - Error detection and diagnostics
8.  💡 Suggestions   - AI-generated improvement suggestions
9.  ✅ Tasks         - Task tracking and management
10. 🧪 Tests         - Test execution and results
11. 🎯 Zeta          - ZETA progress tracking
12. 🤖 Agents        - General agent management
13. 📊 Metrics       - Performance metrics and analytics
14. ⚡ Anomalies     - Anomaly detection and alerts
15. 🔮 Future        - Predictive analysis and planning
16. 🏠 Main          - Main system operations
17. 🛡️ Culture Ship  - Guardian ethics and oversight
18. ⚖️ Moderator     - Moderation and governance
19. 🖥️ System        - System-level operations
20. 🌉 ChatGPT       - ChatGPT API bridge
21. 🎮 SimulatedVerse - SimulatedVerse integration
22. 🦙 Ollama        - Ollama model operations
23. 🎨 LM Studio     - LM Studio model operations
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field

try:
    from datetime import UTC, datetime
except ImportError:  # Python < 3.11 compatibility
    from datetime import datetime, timezone

    UTC = timezone.utc  # noqa: UP017
from enum import Enum
from pathlib import Path
from typing import Any

from src.output.terminal_integration import TerminalRouter
from src.system.agent_terminal_router import AgentTerminalRouter
from src.system.enhanced_terminal_ecosystem import TerminalManager

logger = logging.getLogger(__name__)


class TerminalRole(Enum):
    """Terminal role classification for intelligent routing."""

    AI_AGENT = "ai_agent"  # Claude, Copilot, Codex output
    MULTI_AGENT = "multi_agent"  # ChatDev, AI Council, Intermediary
    MONITORING = "monitoring"  # Errors, Metrics, Anomalies
    DEVELOPMENT = "development"  # Tasks, Tests, Zeta
    INTELLIGENCE = "intelligence"  # Suggestions, Future, Agents
    ORCHESTRATION = "orchestration"  # Main, System, Moderator
    INTEGRATION = "integration"  # ChatGPT, SimulatedVerse, Ollama, LM Studio
    GOVERNANCE = "governance"  # Culture Ship, Moderator


@dataclass
class TerminalConfig:
    """Configuration for a single terminal."""

    name: str
    emoji: str
    role: TerminalRole
    description: str
    auto_start: bool = True
    routing_keywords: list[str] = field(default_factory=list)
    command_suggestions: list[str] = field(default_factory=list)
    intelligence_level: int = 1  # 1-5: Basic → Advanced → Expert → Master → Quantum


@dataclass
class TerminalState:
    """Runtime state for a terminal."""

    config: TerminalConfig
    active: bool = False
    message_count: int = 0
    last_activity: datetime | None = None
    errors_detected: int = 0
    intelligence_insights: list[str] = field(default_factory=list)


class TerminalIntelligenceOrchestrator:
    """Master orchestrator for all 23 specialized terminals."""

    def __init__(self, workspace_root: Path | None = None):
        """Initialize TerminalIntelligenceOrchestrator with workspace_root."""
        self.workspace_root = workspace_root or Path(__file__).resolve().parents[2]
        self.logger = logging.getLogger(__name__)

        # Initialize terminal routers
        self.agent_router = AgentTerminalRouter()
        self.terminal_manager = TerminalManager.get_instance()
        self.terminal_router = TerminalRouter(self.workspace_root)

        # Terminal configurations
        self.terminals: dict[str, TerminalState] = {}
        self._initialize_terminal_configs()

        # Routing intelligence
        self.routing_rules: dict[str, Callable] = {}
        self._initialize_routing_rules()

    def _initialize_terminal_configs(self) -> None:
        """Initialize all 23 terminal configurations."""
        configs = [
            # AI Agent Terminals
            TerminalConfig(
                name="Claude",
                emoji="🤖",
                role=TerminalRole.AI_AGENT,
                description="Claude AI agent output and analysis",
                routing_keywords=["claude", "anthropic", "assistant"],
                command_suggestions=[
                    "python -m src.ai.claude_integration analyze <file>",
                    "python -m src.tools.agent_task_router analyze_with_ai --target claude",
                ],
                intelligence_level=5,
            ),
            TerminalConfig(
                name="Copilot",
                emoji="🧩",
                role=TerminalRole.AI_AGENT,
                description="GitHub Copilot agent output",
                routing_keywords=["copilot", "github", "suggestion"],
                command_suggestions=[
                    "# Copilot suggestions appear here automatically",
                    "python -m src.tools.agent_task_router review_with_ai",
                ],
                intelligence_level=4,
            ),
            TerminalConfig(
                name="Codex",
                emoji="🧠",
                role=TerminalRole.AI_AGENT,
                description="OpenAI Codex agent output",
                routing_keywords=["codex", "openai", "completion"],
                command_suggestions=[
                    "python -m src.ai.openai_integration complete <prompt>",
                ],
                intelligence_level=4,
            ),
            # Multi-Agent Terminals
            TerminalConfig(
                name="ChatDev",
                emoji="🏗️",
                role=TerminalRole.MULTI_AGENT,
                description="ChatDev multi-agent team (CEO, CTO, Programmer, Tester)",
                routing_keywords=["chatdev", "multi-agent", "team", "develop"],
                command_suggestions=[
                    "cd C:\\Users\\keath\\NuSyQ && python nusyq_chatdev.py --task '<task>' --symbolic --consensus",
                    "python -m src.tools.agent_task_router generate_with_ai --target chatdev",
                ],
                intelligence_level=5,
            ),
            TerminalConfig(
                name="AI Council",
                emoji="🏛️",
                role=TerminalRole.MULTI_AGENT,
                description="Multi-AI consensus voting and decision-making",
                routing_keywords=["council", "consensus", "vote", "decision"],
                command_suggestions=[
                    "python -m src.ai.ai_council initiate_vote '<question>'",
                    "python -m src.orchestration.multi_ai_orchestrator consensus_task",
                ],
                intelligence_level=5,
            ),
            TerminalConfig(
                name="Intermediary",
                emoji="🔗",
                role=TerminalRole.MULTI_AGENT,
                description="Inter-agent message passing and coordination",
                routing_keywords=["intermediary", "message", "coordinate", "bridge"],
                command_suggestions=[
                    "python -m src.integration.ai_intermediary route_message",
                    "python -m src.integration.consciousness_bridge sync",
                ],
                intelligence_level=4,
            ),
            # Monitoring Terminals
            TerminalConfig(
                name="Errors",
                emoji="🔥",
                role=TerminalRole.MONITORING,
                description="Error detection, diagnostics, and recovery",
                routing_keywords=["error", "exception", "fail", "traceback", "crash"],
                command_suggestions=[
                    "python scripts/start_nusyq.py error_report",
                    "python -m src.diagnostics.system_health_assessor",
                    "python -m src.healing.quantum_problem_resolver",
                ],
                intelligence_level=5,
            ),
            TerminalConfig(
                name="Metrics",
                emoji="📊",
                role=TerminalRole.MONITORING,
                description="Performance metrics and analytics",
                routing_keywords=["metric", "performance", "benchmark", "stat"],
                command_suggestions=[
                    "python -m src.diagnostics.performance_monitor",
                    "python scripts/start_nusyq.py metrics",
                ],
                intelligence_level=3,
            ),
            TerminalConfig(
                name="Anomalies",
                emoji="⚡",
                role=TerminalRole.MONITORING,
                description="Anomaly detection and alerts",
                routing_keywords=["anomaly", "unusual", "outlier", "alert"],
                command_suggestions=[
                    "python -m src.diagnostics.anomaly_detector",
                ],
                intelligence_level=4,
            ),
            # Development Terminals
            TerminalConfig(
                name="Tasks",
                emoji="✅",
                role=TerminalRole.DEVELOPMENT,
                description="Task tracking and quest management",
                routing_keywords=["task", "TODO", "quest", "assignment"],
                command_suggestions=[
                    "python -m src.Rosetta_Quest_System.quest_cli list",
                    "python -m src.Rosetta_Quest_System.quest_cli create '<title>'",
                    "python scripts/start_nusyq.py quests",
                ],
                intelligence_level=3,
            ),
            TerminalConfig(
                name="Tests",
                emoji="🧪",
                role=TerminalRole.DEVELOPMENT,
                description="Test execution and results",
                routing_keywords=["test", "pytest", "unittest", "coverage"],
                command_suggestions=[
                    "pytest --cov=src --cov-report=term-missing",
                    "python scripts/lint_test_check.py",
                    "python -m src.testing.test_intelligence_terminal",
                ],
                intelligence_level=4,
            ),
            TerminalConfig(
                name="Zeta",
                emoji="🎯",
                role=TerminalRole.DEVELOPMENT,
                description="ZETA progress tracking and milestones",
                routing_keywords=["zeta", "progress", "milestone", "phase"],
                command_suggestions=[
                    "python scripts/view_zeta_progress.py",
                    "# Check config/ZETA_PROGRESS_TRACKER.json",
                ],
                intelligence_level=3,
            ),
            # Intelligence Terminals
            TerminalConfig(
                name="Suggestions",
                emoji="💡",
                role=TerminalRole.INTELLIGENCE,
                description="AI-generated improvement suggestions",
                routing_keywords=["suggest", "improve", "recommend", "enhance"],
                command_suggestions=[
                    "python scripts/start_nusyq.py suggest",
                    "python -m src.tools.agent_task_router analyze_with_ai --target auto",
                ],
                intelligence_level=4,
            ),
            TerminalConfig(
                name="Future",
                emoji="🔮",
                role=TerminalRole.INTELLIGENCE,
                description="Predictive analysis and planning",
                routing_keywords=["future", "predict", "forecast", "plan"],
                command_suggestions=[
                    "python -m src.ai.predictive_engine analyze_trends",
                    "# AI-driven roadmap generation",
                ],
                intelligence_level=5,
            ),
            TerminalConfig(
                name="Agents",
                emoji="🤖",
                role=TerminalRole.INTELLIGENCE,
                description="General agent management and coordination",
                routing_keywords=["agent", "ai", "model", "orchestrate"],
                command_suggestions=[
                    "python scripts/start_nusyq.py agent_status",
                    "python -m src.orchestration.multi_ai_orchestrator",
                ],
                intelligence_level=4,
            ),
            # Orchestration Terminals
            TerminalConfig(
                name="Main",
                emoji="🏠",
                role=TerminalRole.ORCHESTRATION,
                description="Main system operations and coordination",
                routing_keywords=["main", "primary", "core"],
                command_suggestions=[
                    "python scripts/start_nusyq.py snapshot",
                    "python scripts/start_system.ps1",
                    "python src/main.py",
                ],
                intelligence_level=3,
            ),
            TerminalConfig(
                name="System",
                emoji="🖥️",
                role=TerminalRole.ORCHESTRATION,
                description="System-level operations and health",
                routing_keywords=["system", "health", "status"],
                command_suggestions=[
                    "python scripts/start_system.ps1",
                    "python -m src.diagnostics.system_health_assessor",
                ],
                intelligence_level=3,
            ),
            TerminalConfig(
                name="Moderator",
                emoji="⚖️",
                role=TerminalRole.GOVERNANCE,
                description="Moderation and governance",
                routing_keywords=["moderate", "govern", "review", "approve"],
                command_suggestions=[
                    "# Moderation and approval workflows",
                ],
                intelligence_level=3,
            ),
            # Integration Terminals
            TerminalConfig(
                name="ChatGPT Bridge",
                emoji="🌉",
                role=TerminalRole.INTEGRATION,
                description="ChatGPT API integration and bridge",
                routing_keywords=["chatgpt", "gpt", "openai bridge"],
                command_suggestions=[
                    "python -m src.integration.chatgpt_bridge",
                ],
                intelligence_level=4,
            ),
            TerminalConfig(
                name="SimulatedVerse",
                emoji="🎮",
                role=TerminalRole.INTEGRATION,
                description="SimulatedVerse consciousness engine integration",
                routing_keywords=["simulatedverse", "consciousness", "game"],
                command_suggestions=[
                    "cd C:\\Users\\keath\\Desktop\\SimulatedVerse\\SimulatedVerse && npm run dev",
                    "python -m src.integration.consciousness_bridge",
                ],
                intelligence_level=5,
            ),
            TerminalConfig(
                name="Ollama",
                emoji="🦙",
                role=TerminalRole.INTEGRATION,
                description="Ollama local LLM operations",
                routing_keywords=["ollama", "local llm", "model"],
                command_suggestions=[
                    "ollama list",
                    "python -m src.tools.agent_task_router analyze_with_ai --target ollama",
                    "python -m src.ai.ollama_chatdev_integrator",
                ],
                intelligence_level=4,
            ),
            TerminalConfig(
                name="LM Studio",
                emoji="🎨",
                role=TerminalRole.INTEGRATION,
                description="LM Studio model operations",
                routing_keywords=["lm studio", "lmstudio"],
                command_suggestions=[
                    "# LM Studio API integration",
                ],
                intelligence_level=3,
            ),
            # Governance Terminal
            TerminalConfig(
                name="Culture Ship",
                emoji="🛡️",
                role=TerminalRole.GOVERNANCE,
                description="Guardian ethics and oversight (Culture Mind)",
                routing_keywords=["culture", "ethics", "guardian", "oversight"],
                command_suggestions=[
                    "python -m src.consciousness.culture_ship_guardian",
                    "# Ethics and safety monitoring",
                ],
                intelligence_level=5,
            ),
        ]

        # Initialize terminal states
        for config in configs:
            self.terminals[config.name] = TerminalState(config=config)

    def _initialize_routing_rules(self) -> None:
        """Initialize intelligent routing rules for each terminal."""
        # Error detection rules
        self.routing_rules["detect_error"] = lambda msg: any(
            keyword in msg.lower()
            for keyword in ["error", "exception", "fail", "traceback", "crash"]
        )

        # Suggestion detection rules
        self.routing_rules["detect_suggestion"] = lambda msg: any(
            keyword in msg.lower()
            for keyword in ["suggest", "improve", "recommend", "enhance", "should"]
        )

        # Task detection rules
        self.routing_rules["detect_task"] = lambda msg: any(
            keyword in msg.lower() for keyword in ["task", "TODO", "quest", "complete", "done"]
        )

        # Test detection rules
        self.routing_rules["detect_test"] = lambda msg: any(
            keyword in msg.lower()
            for keyword in ["test", "pytest", "assert", "coverage", "passed", "failed"]
        )

        # Metric detection rules
        self.routing_rules["detect_metric"] = lambda msg: any(
            keyword in msg.lower()
            for keyword in ["metric", "performance", "latency", "throughput", "benchmark"]
        )

    def activate_all_terminals(self) -> dict[str, bool]:
        """Activate all terminals with auto_start=True."""
        results = {}

        for name, state in self.terminals.items():
            if state.config.auto_start:
                success = self.activate_terminal(name)
                results[name] = success

        return results

    def activate_terminal(self, name: str) -> bool:
        """Activate a specific terminal."""
        if name not in self.terminals:
            self.logger.error(f"Unknown terminal: {name}")
            return False

        state = self.terminals[name]
        if state.active:
            self.logger.info(f"Terminal {name} already active")
            return True

        try:
            # Initialize terminal channel
            channel_name = f"{state.config.emoji} {name}"
            self.terminal_manager.send(
                channel_name,
                "INFO",
                "terminal_activated",
                meta={
                    "timestamp": datetime.now(UTC).isoformat(),
                    "config": {
                        "name": state.config.name,
                        "role": state.config.role.value,
                        "description": state.config.description,
                        "intelligence_level": state.config.intelligence_level,
                    },
                },
            )

            state.active = True
            state.last_activity = datetime.now(UTC)

            self.logger.info(f"✅ Activated terminal: {state.config.emoji} {name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to activate terminal {name}: {e}")
            return False

    def route_message(
        self,
        message: str,
        source: str | None = None,
        level: str = "INFO",
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """Intelligently route a message to appropriate terminals."""
        routed_to: list[str] = []

        # Check routing rules and send to terminals
        if self.routing_rules["detect_error"](message):
            self._send_to_terminal("Errors", message, level, metadata)
            routed_to.append("Errors")
            # Errors often imply anomalies as well
            self._send_to_terminal("Anomalies", message, level, metadata)
            routed_to.append("Anomalies")

        if self.routing_rules["detect_suggestion"](message):
            self._send_to_terminal("Suggestions", message, level, metadata)
            routed_to.append("Suggestions")

        if self.routing_rules["detect_task"](message):
            self._send_to_terminal("Tasks", message, level, metadata)
            routed_to.append("Tasks")

        if self.routing_rules["detect_test"](message):
            self._send_to_terminal("Tests", message, level, metadata)
            routed_to.append("Tests")

        if self.routing_rules["detect_metric"](message):
            self._send_to_terminal("Metrics", message, level, metadata)
            routed_to.append("Metrics")

        # Route to source terminal if specified and not already routed
        if source and source in self.terminals and source not in routed_to:
            self._send_to_terminal(source, message, level, metadata)
            routed_to.append(source)

        # Always route to Main if nothing matched
        if not routed_to:
            self._send_to_terminal("Main", message, level, metadata)
            routed_to.append("Main")

        return routed_to

    def _send_to_terminal(
        self,
        name: str,
        message: str,
        level: str = "INFO",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Send a message to a specific terminal."""
        if name not in self.terminals:
            return

        state = self.terminals[name]

        # Ensure terminal is active
        if not state.active:
            self.activate_terminal(name)

        # Update state
        state.message_count += 1
        state.last_activity = datetime.now(UTC)

        if level == "ERROR":
            state.errors_detected += 1

        # Send to terminal channel
        channel_name = f"{state.config.emoji} {name}"
        self.terminal_manager.send(
            channel_name,
            level,
            message,
            meta={
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": metadata or {},
            },
        )

    def get_terminal_status(self) -> dict[str, Any]:
        """Get status of all terminals."""
        return {
            name: {
                "active": state.active,
                "role": state.config.role.value,
                "message_count": state.message_count,
                "errors_detected": state.errors_detected,
                "last_activity": state.last_activity.isoformat() if state.last_activity else None,
                "intelligence_level": state.config.intelligence_level,
            }
            for name, state in self.terminals.items()
        }

    def get_command_suggestions(self, terminal_name: str) -> list[str]:
        """Get command suggestions for a specific terminal."""
        if terminal_name not in self.terminals:
            return []
        return self.terminals[terminal_name].config.command_suggestions

    def generate_terminal_dashboard(self) -> str:
        """Generate a visual dashboard of all terminal states."""
        dashboard_lines = [
            "=" * 80,
            "🎯 TERMINAL INTELLIGENCE ORCHESTRATOR - Live Dashboard",
            "=" * 80,
            "",
        ]

        # Group terminals by role
        by_role: dict[TerminalRole, list[str]] = {}
        for name, state in self.terminals.items():
            role = state.config.role
            if role not in by_role:
                by_role[role] = []
            by_role[role].append(name)

        # Display by role
        for role in TerminalRole:
            if role not in by_role:
                continue

            terminals = by_role[role]
            dashboard_lines.append(f"\n📂 {role.value.upper().replace('_', ' ')}")
            dashboard_lines.append("-" * 80)

            for name in terminals:
                state = self.terminals[name]
                status = "🟢 ACTIVE" if state.active else "⚫ INACTIVE"
                intelligence = "⭐" * state.config.intelligence_level

                dashboard_lines.append(
                    f"{state.config.emoji} {name:20} | {status:12} | "
                    f"Msgs: {state.message_count:4} | Errors: {state.errors_detected:3} | "
                    f"Intelligence: {intelligence}"
                )

        dashboard_lines.append("\n" + "=" * 80)

        return "\n".join(dashboard_lines)


# Singleton instance
_orchestrator: TerminalIntelligenceOrchestrator | None = None


def get_orchestrator() -> TerminalIntelligenceOrchestrator:
    """Get or create the singleton orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TerminalIntelligenceOrchestrator()
    return _orchestrator


async def main():
    """Demo: Activate all terminals and show dashboard."""
    orchestrator = get_orchestrator()

    logger.info("🚀 Activating all terminals...")
    results = orchestrator.activate_all_terminals()

    logger.info(f"\n✅ Activated {sum(results.values())}/{len(results)} terminals")

    logger.info("\n" + orchestrator.generate_terminal_dashboard())

    # Test routing
    test_messages = [
        ("Error in module X", "ERROR"),
        ("Suggest improving performance", "INFO"),
        ("Task completed successfully", "INFO"),
        ("pytest passed 42 tests", "INFO"),
        ("Performance improved by 25%", "INFO"),
    ]

    logger.info("\n🧪 Testing intelligent routing...")
    for message, level in test_messages:
        routed = orchestrator.route_message(message, level=level)
        logger.info(f"  '{message}' → {', '.join(routed)}")


if __name__ == "__main__":
    asyncio.run(main())
