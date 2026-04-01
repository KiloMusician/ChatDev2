"""Multi-Agent Terminal Orchestration System.

Manages isolated terminal streams for Claude, Copilot, Codex, ChatDev, etc.
Prevents collision, enables cross-agent visibility, maintains audit trail.

Architecture:
- Each agent gets dedicated terminal(s) with unique I/O stream
- Central router distributes tasks to appropriate agent terminals
- Tracing & logging for all inter-agent communication
- Pub/Sub system for agents to observe each other's work
"""

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class AgentType(Enum):
    """Supported AI agents in the orchestration system."""

    CLAUDE = "claude"  # GitHub Copilot (Claude-based)
    COPILOT = "copilot"  # Direct Copilot extension
    CODEX = "codex"  # Codex extension
    CHATDEV = "chatdev"  # ChatDev multi-agent framework
    OLLAMA = "ollama"  # Local LLM via Ollama
    QUANTUM_RESOLVER = "quantum_resolver"  # Quantum problem resolver
    CONSCIOUSNESS_BRIDGE = "consciousness_bridge"  # Consciousness integration
    AI_COUNCIL = "ai_council"  # Multi-agent consensus
    INTERMEDIARY = "intermediary"  # Task delegation & routing


class TerminalType(Enum):
    """Terminal categories for organization."""

    ERRORS = "errors"  # Error monitoring & resolution
    SUGGESTIONS = "suggestions"  # AI suggestions & recommendations
    TASKS = "tasks"  # Task execution & tracking
    ZETA = "zeta"  # Autonomous control & decisions
    AGENTS = "agents"  # Agent status & coordination
    METRICS = "metrics"  # Performance metrics & telemetry
    ANOMALIES = "anomalies"  # Anomaly detection & alerting
    FUTURE = "future"  # Predictive & planning features
    MAIN = "main"  # Main system console
    # NEW AGENTS
    CLAUDE = "claude"  # Claude agent dedicated terminal
    COPILOT = "copilot"  # Copilot agent dedicated terminal
    CODEX = "codex"  # Codex agent dedicated terminal
    CHATDEV = "chatdev"  # ChatDev framework terminal
    AI_COUNCIL = "ai_council"  # AI consensus & voting
    INTERMEDIARY = "intermediary"  # Task delegation layer
    SCAFFOLDING = "scaffolding"  # Architecture & setup


@dataclass
class TerminalMessage:
    """Message in terminal stream with full provenance."""

    timestamp: str
    agent: AgentType
    terminal: TerminalType
    level: str  # "info", "warning", "error", "debug"
    message: str
    context: dict[str, Any] | None = None
    trace_id: str | None = None
    parent_trace_id: str | None = None

    def to_json(self) -> str:
        """Serialize to JSON for logging."""
        return json.dumps(asdict(self), default=str)


class TerminalStream:
    """Isolated I/O stream for a single agent/terminal pair."""

    def __init__(
        self,
        agent: AgentType,
        terminal: TerminalType,
        log_file: Path | None = None,
    ) -> None:
        """Initialize TerminalStream with agent, terminal, log_file."""
        self.agent = agent
        self.terminal = terminal
        self.log_file = log_file or Path(f"logs/agent_terminals/{agent.value}_{terminal.value}.log")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.messages: list[TerminalMessage] = []
        self._lock = asyncio.Lock()

    async def write(
        self,
        message: str,
        level: str = "info",
        context: dict[str, Any] | None = None,
        trace_id: str | None = None,
        parent_trace_id: str | None = None,
    ) -> TerminalMessage:
        """Write message to this terminal's stream."""
        msg = TerminalMessage(
            timestamp=datetime.now().isoformat(),
            agent=self.agent,
            terminal=self.terminal,
            level=level,
            message=message,
            context=context,
            trace_id=trace_id,
            parent_trace_id=parent_trace_id,
        )

        async with self._lock:
            self.messages.append(msg)
            # Write to file
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(msg.to_json() + "\n")

        return msg

    async def read_recent(self, count: int = 20) -> list[TerminalMessage]:
        """Read recent messages from this stream."""
        async with self._lock:
            return self.messages[-count:]


class MultiAgentTerminalOrchestrator:
    """Central orchestration for all agent terminals."""

    def __init__(self, state_dir: Path = Path("data/agent_terminals")):
        """Initialize MultiAgentTerminalOrchestrator with state_dir."""
        self.root = Path(__file__).resolve().parents[2]
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Terminal streams indexed by (agent, terminal)
        self.streams: dict[tuple[AgentType, TerminalType], TerminalStream] = {}

        # Pub/Sub for cross-agent visibility
        self.subscribers: dict[TerminalType, list[Callable]] = {}

        # Current active agent (prevents collision)
        self.active_agent: AgentType | None = None
        self._agent_lock = asyncio.Lock()

        # Defaults
        self.ecosystem_defaults = self._load_defaults(
            self.root / "config" / "ecosystem_defaults.json"
        )
        self.orchestration_defaults = self._load_defaults(
            self.root / "config" / "orchestration_defaults.json"
        )
        terminal_defaults = self.ecosystem_defaults.get("terminal_orchestration", {})
        terminal_arch = self.ecosystem_defaults.get("terminal_architecture", {})
        routing_defaults = self.orchestration_defaults.get("terminal_routing", {})

        self.auto_tag_agent_ids = bool(terminal_defaults.get("auto_tag_agent_ids", False))
        self.agent_id_format = str(routing_defaults.get("agent_id_format", "[{agent_id}]"))
        self.audit_log_enabled = bool(terminal_arch.get("per_message_audit_log", False))
        audit_path = routing_defaults.get("audit_log_path", "state/terminals/audit.jsonl")
        audit_path = Path(audit_path)
        self.audit_log_path = audit_path if audit_path.is_absolute() else (self.root / audit_path)
        self._audit_lock = asyncio.Lock()

        # Tracing
        self.logger = logging.getLogger(__name__)

    def _load_defaults(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            defaults: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            return defaults
        except (OSError, json.JSONDecodeError):
            return {}

    def _tag_message(self, agent: AgentType, message: str) -> tuple[str, str | None]:
        if not self.auto_tag_agent_ids:
            return message, None
        tag = self.agent_id_format.format(agent_id=agent.value)
        if message.startswith(tag):
            return message, None
        return f"{tag} {message}", message

    async def _write_audit_log(self, message: TerminalMessage) -> None:
        if not self.audit_log_enabled:
            return
        payload = asdict(message)
        payload["event"] = "terminal_message"
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        async with self._audit_lock:
            with self.audit_log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")

    async def acquire_agent_context(self, agent: AgentType) -> "AgentContext":
        """Acquire exclusive context for an agent to execute work."""
        async with self._agent_lock:
            if self.active_agent and self.active_agent != agent:
                self.logger.warning(
                    f"Agent {agent.value} waiting for {self.active_agent.value} to finish"
                )
                # In real implementation, would queue and wait
            self.active_agent = agent
        return AgentContext(self, agent)

    async def get_or_create_stream(
        self, agent: AgentType, terminal: TerminalType
    ) -> TerminalStream:
        """Get or create a terminal stream for agent/terminal pair."""
        key = (agent, terminal)
        if key not in self.streams:
            self.streams[key] = TerminalStream(agent, terminal)
        return self.streams[key]

    async def write_to_terminal(
        self,
        agent: AgentType,
        terminal: TerminalType,
        message: str,
        level: str = "info",
        context: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> TerminalMessage:
        """Write message to specific terminal and notify subscribers."""
        tagged_message, raw_message = self._tag_message(agent, message)
        payload_context = dict(context or {})
        if raw_message:
            payload_context.setdefault("raw_message", raw_message)
            payload_context.setdefault(
                "agent_tag", self.agent_id_format.format(agent_id=agent.value)
            )

        stream = await self.get_or_create_stream(agent, terminal)
        msg = await stream.write(tagged_message, level, payload_context, trace_id)

        # Notify subscribers
        if terminal in self.subscribers:
            for callback in self.subscribers[terminal]:
                await callback(msg)

        await self._write_audit_log(msg)
        return msg

    async def subscribe_to_terminal(
        self, terminal: TerminalType, callback: Callable[[TerminalMessage], None]
    ) -> None:
        """Subscribe to messages from a terminal."""
        if terminal not in self.subscribers:
            self.subscribers[terminal] = []
        self.subscribers[terminal].append(callback)

    async def get_agent_status(self, agent: AgentType) -> dict[str, Any]:
        """Get status of an agent across all its terminals."""
        status: dict[str, Any] = {
            "agent": agent.value,
            "active": self.active_agent == agent,
            "terminals": {},
        }

        for (a, t), stream in self.streams.items():
            if a == agent:
                recent = await stream.read_recent(5)
                status["terminals"][t.value] = {
                    "terminal": t.value,
                    "message_count": len(stream.messages),
                    "recent_messages": [asdict(m) for m in recent],
                }

        return status

    async def get_system_status(self) -> dict[str, Any]:
        """Get status of entire multi-agent system."""
        agents_status = {}
        for agent in AgentType:
            agents_status[agent.value] = await self.get_agent_status(agent)

        return {
            "timestamp": datetime.now().isoformat(),
            "active_agent": self.active_agent.value if self.active_agent else None,
            "terminal_streams": len(self.streams),
            "agents": agents_status,
        }

    async def save_state(self) -> None:
        """Persist system state to disk."""
        state = await self.get_system_status()
        state_file = self.state_dir / "orchestrator_state.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)


class AgentContext:
    """Context manager for agent exclusive execution."""

    def __init__(self, orchestrator: MultiAgentTerminalOrchestrator, agent: AgentType) -> None:
        """Initialize AgentContext with orchestrator, agent."""
        self.orchestrator = orchestrator
        self.agent = agent

    async def __aenter__(self):
        """Enter exclusive agent context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release exclusive agent context."""
        async with self.orchestrator._agent_lock:
            self.orchestrator.active_agent = None

    async def write(
        self,
        terminal: TerminalType,
        message: str,
        level: str = "info",
        context: dict[str, Any] | None = None,
    ) -> TerminalMessage:
        """Write message to agent's terminal."""
        return await self.orchestrator.write_to_terminal(
            self.agent, terminal, message, level, context
        )

    async def read_visible(self, terminal: TerminalType, count: int = 20) -> list[TerminalMessage]:
        """Read recent messages from a terminal this agent can see."""
        stream = await self.orchestrator.get_or_create_stream(self.agent, terminal)
        return await stream.read_recent(count)


# Singleton instance
_orchestrator: MultiAgentTerminalOrchestrator | None = None


async def get_orchestrator() -> MultiAgentTerminalOrchestrator:
    """Get or create the singleton orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentTerminalOrchestrator()
    return _orchestrator


async def init_orchestrator() -> MultiAgentTerminalOrchestrator:
    """Initialize the multi-agent terminal orchestrator."""
    orchestrator = await get_orchestrator()

    # Pre-create all terminal streams for all agent/terminal combinations
    for agent in AgentType:
        for terminal in TerminalType:
            await orchestrator.get_or_create_stream(agent, terminal)

    # Save initial state
    await orchestrator.save_state()

    return orchestrator
