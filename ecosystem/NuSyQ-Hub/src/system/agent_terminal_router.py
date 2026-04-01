"""Agent Terminal Router - Routes agent output to dedicated terminals.

Intercepts agent activity from orchestrators and task routers,
emits to appropriate terminal stream with tracing & visibility.

Also integrates with Guild Board for persistent coordination state.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from src.system.multi_agent_terminal_orchestrator import (AgentType,
                                                          TerminalType,
                                                          get_orchestrator)


class AgentTerminalRouter:
    """Routes agent output to appropriate terminals with full tracing."""

    def __init__(self) -> None:
        """Initialize AgentTerminalRouter."""
        self.logger = logging.getLogger(__name__)
        self.orchestrator = None
        self._init_lock = asyncio.Lock()

        # Agent → Terminal mapping
        self.agent_terminal_map = {
            AgentType.CLAUDE: TerminalType.CLAUDE,
            AgentType.COPILOT: TerminalType.COPILOT,
            AgentType.CODEX: TerminalType.CODEX,
            AgentType.CHATDEV: TerminalType.CHATDEV,
            AgentType.OLLAMA: TerminalType.AGENTS,  # Shared agent terminal
            AgentType.QUANTUM_RESOLVER: TerminalType.AGENTS,
            AgentType.CONSCIOUSNESS_BRIDGE: TerminalType.AGENTS,
            AgentType.AI_COUNCIL: TerminalType.AI_COUNCIL,
            AgentType.INTERMEDIARY: TerminalType.INTERMEDIARY,
        }

        # Event routing map: event type → terminals that should receive it
        self.event_terminal_routes = {
            "task_started": [TerminalType.TASKS, TerminalType.AGENTS, TerminalType.MAIN],
            "task_completed": [TerminalType.TASKS, TerminalType.AGENTS, TerminalType.METRICS],
            "task_failed": [TerminalType.ERRORS, TerminalType.TASKS, TerminalType.MAIN],
            "agent_analysis": [TerminalType.SUGGESTIONS, TerminalType.AGENTS],
            "error_detected": [TerminalType.ERRORS, TerminalType.ANOMALIES],
            "consensus_vote": [TerminalType.AI_COUNCIL, TerminalType.INTERMEDIARY],
            "inter_agent_message": [TerminalType.INTERMEDIARY],
            "performance_metric": [TerminalType.METRICS],
            "future_prediction": [TerminalType.FUTURE],
        }

    async def init(self) -> None:
        """Initialize router with orchestrator connection."""
        async with self._init_lock:
            if self.orchestrator is None:
                self.orchestrator = await get_orchestrator()

    async def route_agent_output(
        self,
        agent: AgentType,
        message: str,
        level: str = "info",
        context: dict[str, Any] | None = None,
        primary_terminal: TerminalType | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Route agent output to its primary terminal + related system terminals."""
        await self.init()

        # Use mapped terminal or provided one
        terminal = primary_terminal or self.agent_terminal_map.get(agent)
        if not terminal:
            self.logger.warning(f"No terminal mapping for agent {agent.value}")
            return

        # Write to primary agent terminal
        await self.orchestrator.write_to_terminal(
            agent=agent,
            terminal=terminal,
            message=message,
            level=level,
            context=context,
            trace_id=trace_id,
        )

    async def route_event(
        self,
        event_type: str,
        source_agent: AgentType,
        message: str,
        context: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Route event to all interested terminals based on event type."""
        await self.init()

        # Get terminals for this event type
        terminals = self.event_terminal_routes.get(event_type, [])

        # Also emit to source agent's primary terminal
        primary = self.agent_terminal_map.get(source_agent)
        if primary and primary not in terminals:
            terminals = [primary, *terminals]

        # Emit to all interested terminals
        for terminal in terminals:
            await self.orchestrator.write_to_terminal(
                agent=source_agent,
                terminal=terminal,
                message=message,
                level="info",
                context=context or {"event_type": event_type},
                trace_id=trace_id,
            )

    async def route_task_update(
        self,
        task_id: str,
        agent: AgentType,
        status: str,  # started, in_progress, completed, failed
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Route task status update with standardized format."""
        await self.init()

        event_type = f"task_{status}"
        full_context = {
            "task_id": task_id,
            "agent": agent.value,
            "status": status,
            **(context or {}),
        }

        await self.route_event(
            event_type=event_type,
            source_agent=agent,
            message=message,
            context=full_context,
        )

    async def route_error(
        self,
        agent: AgentType,
        error_message: str,
        error_type: str = "RuntimeError",
        context: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Route error to error terminal + agent's primary terminal."""
        await self.init()

        error_context = {
            "agent": agent.value,
            "error_type": error_type,
            "timestamp": datetime.now().isoformat(),
            **(context or {}),
        }

        # Write to error terminal
        await self.orchestrator.write_to_terminal(
            agent=agent,
            terminal=TerminalType.ERRORS,
            message=f"[{error_type}] {error_message}",
            level="error",
            context=error_context,
            trace_id=trace_id,
        )

        # Also write to agent's primary terminal
        primary = self.agent_terminal_map.get(agent)
        if primary:
            await self.orchestrator.write_to_terminal(
                agent=agent,
                terminal=primary,
                message=f"ERROR: {error_message}",
                level="error",
                context=error_context,
                trace_id=trace_id,
            )

    async def route_inter_agent_message(
        self,
        source_agent: AgentType,
        target_agent: AgentType,
        message: str,
        message_type: str = "request",  # request, response, notification
        context: dict[str, Any] | None = None,
    ) -> None:
        """Route inter-agent communication for visibility."""
        await self.init()

        comm_context = {
            "source": source_agent.value,
            "target": target_agent.value,
            "message_type": message_type,
            **(context or {}),
        }

        # Emit to Intermediary for all inter-agent comms
        await self.orchestrator.write_to_terminal(
            agent=source_agent,
            terminal=TerminalType.INTERMEDIARY,
            message=f"{source_agent.value} → {target_agent.value}: {message}",
            level="info",
            context=comm_context,
        )

        # Also emit to each agent's primary terminal for their awareness
        for agent in [source_agent, target_agent]:
            primary = self.agent_terminal_map.get(agent)
            if primary:
                await self.orchestrator.write_to_terminal(
                    agent=agent,
                    terminal=primary,
                    message=f"{'[From]' if agent == target_agent else '[To]'} {message}",
                    level="info",
                    context=comm_context,
                )

    async def get_agent_terminal_view(self, agent: AgentType, count: int = 20) -> list[dict]:
        """Get recent terminal output visible to a specific agent."""
        await self.init()

        primary = self.agent_terminal_map.get(agent)
        if not primary:
            return []

        stream = await self.orchestrator.get_or_create_stream(agent, primary)
        messages = await stream.read_recent(count)

        return [
            {
                "timestamp": m.timestamp,
                "level": m.level,
                "message": m.message,
                "context": m.context,
            }
            for m in messages
        ]

    async def get_global_terminal_view(self, count: int = 50) -> dict[str, list[dict]]:
        """Get recent output from all terminals."""
        await self.init()

        view = {}
        for agent in AgentType:
            view[agent.value] = await self.get_agent_terminal_view(agent, count)

        return view

    async def export_terminal_history(self, output_file: Path) -> None:
        """Export all terminal history to JSON file."""
        await self.init()

        state = await self.orchestrator.get_system_status()
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)


# Singleton instance
_router: AgentTerminalRouter | None = None


async def get_router() -> AgentTerminalRouter:
    """Get or create the singleton router."""
    global _router
    if _router is None:
        _router = AgentTerminalRouter()
        await _router.init()
    return _router


async def init_router() -> AgentTerminalRouter:
    """Initialize the router."""
    router = await get_router()
    await router.init()
    return router
