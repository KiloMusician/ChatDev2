#!/usr/bin/env python3
"""Agent-Specific Terminal Orchestration System.

[ROUTE AGENTS] 🤖

Creates dedicated terminals for each AI agent so they can work independently and observe each other.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class TerminalPurpose:
    """Define a terminal's specialized role."""

    name: str
    purpose: str
    icon: str
    color: str
    auto_commands: list[str]
    routes: list[str]  # What kinds of output go here
    persistent: bool = True


# AGENT-SPECIFIC TERMINALS - Each agent gets their own workspace
AGENT_TERMINALS = {
    "claude": TerminalPurpose(
        name="🧠 Claude",
        purpose="Claude Code agent execution, analysis, code generation",
        icon="robot",
        color="terminal.ansiCyan",
        auto_commands=[
            "echo '=== Claude Code Agent Terminal ==='",
            "echo 'Claude Sonnet 4.5 - Autonomous Code Agent'",
            "echo 'Monitoring: Code changes, file operations, analysis output'",
        ],
        routes=["claude", "sonnet", "anthropic", "claude_code"],
        persistent=True,
    ),
    "copilot": TerminalPurpose(
        name="🛸 Copilot",
        purpose="GitHub Copilot agent execution, suggestions, completions",
        icon="github-action",
        color="terminal.ansiGreen",
        auto_commands=[
            "echo '=== GitHub Copilot Agent Terminal ==='",
            "echo 'Copilot - AI Pair Programmer'",
            "echo 'Monitoring: Suggestions, completions, refactorings'",
        ],
        routes=["copilot", "github_copilot", "gh_copilot"],
        persistent=True,
    ),
    "codex": TerminalPurpose(
        name="⚡ Codex",
        purpose="OpenAI Codex agent execution, transformations",
        icon="code",
        color="terminal.ansiMagenta",
        auto_commands=[
            "echo '=== Codex Agent Terminal ==='",
            "echo 'OpenAI Codex - Code Understanding & Generation'",
            "echo 'Monitoring: Code transformations, migrations, refactorings'",
        ],
        routes=["codex", "openai_codex", "gpt_code"],
        persistent=True,
    ),
    "chatdev": TerminalPurpose(
        name="👥 ChatDev",
        purpose="ChatDev multi-agent software development team",
        icon="organization",
        color="terminal.ansiYellow",
        auto_commands=[
            "echo '=== ChatDev Multi-Agent Terminal ==='",
            "echo 'ChatDev - Multi-Agent Software Company Simulation'",
            "echo 'Monitoring: CEO, CTO, Designer, Coder, Tester communications'",
        ],
        routes=["chatdev", "chat_dev", "multi_agent", "software_company"],
        persistent=True,
    ),
    "ai_council": TerminalPurpose(
        name="🏛️ AI Council",
        purpose="AI Council deliberations, consensus building, decision making",
        icon="law",
        color="terminal.ansiBlue",
        auto_commands=[
            "echo '=== AI Council Deliberation Terminal ==='",
            "echo 'AI Council - Multi-Model Consensus System'",
            "echo 'Monitoring: Votes, debates, consensus decisions'",
        ],
        routes=["council", "ai_council", "consensus", "deliberation", "vote"],
        persistent=True,
    ),
    "intermediary": TerminalPurpose(
        name="🔄 Intermediary",
        purpose="Cross-agent communication, message routing, coordination",
        icon="git-pull-request",
        color="terminal.ansiWhite",
        auto_commands=[
            "echo '=== Intermediary Communication Hub ==='",
            "echo 'Message Router - Agent-to-Agent Communication'",
            "echo 'Monitoring: Inter-agent messages, coordination events'",
        ],
        routes=["intermediary", "router", "bridge", "coordinator", "handoff"],
        persistent=True,
    ),
}


# SPECIALIZED OPERATIONAL TERMINALS
OPERATIONAL_TERMINALS = {
    "errors": TerminalPurpose(
        name="🔥 Errors",
        purpose="Error output, exceptions, failures across all agents",
        icon="bug",
        color="terminal.ansiRed",
        auto_commands=["echo '=== Error Monitor Active ==='"],
        routes=["error", "exception", "failed", "stderr", "traceback"],
        persistent=True,
    ),
    "suggestions": TerminalPurpose(
        name="💡 Suggestions",
        purpose="Next steps, recommendations from all agents",
        icon="lightbulb",
        color="terminal.ansiYellow",
        auto_commands=["echo '=== Suggestion Stream Active ==='"],
        routes=["suggest", "recommend", "next_steps", "hint", "todo"],
        persistent=True,
    ),
    "tasks": TerminalPurpose(
        name="✓ Tasks",
        purpose="Task execution, work queue, PU processing",
        icon="checklist",
        color="terminal.ansiCyan",
        auto_commands=["echo '=== Task Execution Monitor ==='"],
        routes=["task", "pu_queue", "work_queue", "processing", "job"],
        persistent=True,
    ),
    "zeta": TerminalPurpose(
        name="🎯 Zeta",
        purpose="Zeta orchestration, autonomous cycles, meta-operations",
        icon="target",
        color="terminal.ansiMagenta",
        auto_commands=["echo '=== Zeta Autonomous Control ==='"],
        routes=["zeta", "autonomous", "orchestrat", "cycle", "meta"],
        persistent=True,
    ),
    "metrics": TerminalPurpose(
        name="📊 Metrics",
        purpose="Cultivation metrics, health monitoring, dashboards",
        icon="graph",
        color="terminal.ansiBlue",
        auto_commands=["echo '=== Metrics & Health Monitor ==='"],
        routes=["metric", "health", "dashboard", "monitor", "stats"],
        persistent=True,
    ),
    "anomalies": TerminalPurpose(
        name="⚡ Anomalies",
        purpose="Unusual events, orphaned processes, unexpected behaviors",
        icon="zap",
        color="terminal.ansiRed",
        auto_commands=["echo '=== Anomaly Detection Active ==='"],
        routes=["anomaly", "orphan", "unexpected", "zombie", "leak"],
        persistent=True,
    ),
    "future": TerminalPurpose(
        name="🔮 Future",
        purpose="Planned features, upcoming tasks, development roadmap",
        icon="crystal_ball",
        color="terminal.ansiWhite",
        auto_commands=["echo '=== Future Development Stream ==='"],
        routes=["future", "planned", "roadmap", "upcoming", "vision"],
        persistent=True,
    ),
    "main": TerminalPurpose(
        name="🏠 Main",
        purpose="Default terminal for general operations",
        icon="home",
        color="terminal.ansiWhite",
        auto_commands=["echo '=== Main Terminal ==='"],
        routes=["main", "default", "general"],
        persistent=True,
    ),
}


def _build_terminal_purpose(
    term_id: str,
    payload: dict[str, Any],
    fallback: TerminalPurpose | None = None,
) -> TerminalPurpose:
    """Build a TerminalPurpose from config payload with optional fallback."""
    return TerminalPurpose(
        name=str(payload.get("name") or (fallback.name if fallback else term_id)),
        purpose=str(payload.get("purpose") or (fallback.purpose if fallback else "")),
        icon=str(payload.get("icon") or (fallback.icon if fallback else "terminal")),
        color=str(payload.get("color") or (fallback.color if fallback else "terminal.ansiWhite")),
        auto_commands=list(payload.get("auto_commands") or (fallback.auto_commands if fallback else [])),
        routes=list(payload.get("routes") or (fallback.routes if fallback else [])),
        persistent=bool(payload.get("persistent", fallback.persistent if fallback else True)),
    )


def _load_terminal_groups(
    root: Path,
) -> tuple[dict[str, TerminalPurpose], dict[str, TerminalPurpose]]:
    """Load terminal groups from config/terminal_groups.json when available."""
    config_path = root / "config" / "terminal_groups.json"
    if not config_path.exists():
        return AGENT_TERMINALS, OPERATIONAL_TERMINALS
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AGENT_TERMINALS, OPERATIONAL_TERMINALS

    agent_terminals: dict[str, TerminalPurpose] = {}
    operational_terminals: dict[str, TerminalPurpose] = {}

    agent_groups = data.get("agent_terminals", {})
    if isinstance(agent_groups, dict):
        for term_id, payload in agent_groups.items():
            if not isinstance(payload, dict):
                continue
            fallback = AGENT_TERMINALS.get(term_id)
            agent_terminals[term_id] = _build_terminal_purpose(term_id, payload, fallback)

    operational_groups = data.get("operational_terminals", {})
    if isinstance(operational_groups, dict):
        for term_id, payload in operational_groups.items():
            if not isinstance(payload, dict):
                continue
            fallback = OPERATIONAL_TERMINALS.get(term_id)
            operational_terminals[term_id] = _build_terminal_purpose(term_id, payload, fallback)

    if not agent_terminals:
        agent_terminals = AGENT_TERMINALS
    if not operational_terminals:
        operational_terminals = OPERATIONAL_TERMINALS

    return agent_terminals, operational_terminals


class AgentTerminalOrchestrator:
    """Orchestrate agent-specific and operational terminals."""

    def __init__(self, root: Path):
        self.root = root
        self.agent_terminals, self.operational_terminals = _load_terminal_groups(self.root)
        self.all_terminals = {**self.agent_terminals, **self.operational_terminals}

        # Build routing map
        self.routing_rules = {}
        for term_id, term in self.all_terminals.items():
            for keyword in term.routes:
                self.routing_rules[keyword] = term_id

    def route_output(self, content: str, agent: str | None = None, default: str = "main") -> str:
        """Determine which terminal should receive this output.

        Args:
            content: The output content to route
            agent: Specific agent name (claude, copilot, codex, etc.)
            default: Default terminal if no match found
        """
        # If agent specified and exists, route there
        if agent and agent.lower() in self.agent_terminals:
            return agent.lower()

        # Check content against routing rules
        content_lower = content.lower()
        for keyword, terminal_id in self.routing_rules.items():
            if keyword in content_lower:
                return terminal_id

        return default

    def generate_vscode_sessions(self) -> dict[str, Any]:
        """Generate VSCode terminal-keeper sessions.json config."""
        sessions = []

        # Add agent terminals first
        print("\n🤖 Agent Terminals:")
        for _term_id, term in self.agent_terminals.items():
            terminal_config = {
                "name": term.name,
                "icon": term.icon,
                "color": term.color,
                "autoExecuteCommands": True,
                "commands": term.auto_commands,
            }
            sessions.append(terminal_config)
            print(f"   {term.name} - {term.purpose}")

        # Add operational terminals
        print("\n⚙️  Operational Terminals:")
        for _term_id, term in self.operational_terminals.items():
            terminal_config = {
                "name": term.name,
                "icon": term.icon,
                "color": term.color,
                "autoExecuteCommands": True,
                "commands": term.auto_commands,
            }
            sessions.append(terminal_config)
            print(f"   {term.name} - {term.purpose}")

        return {"active": "agent_orchestrated", "sessions": {"agent_orchestrated": sessions}}

    def generate_routing_map(self) -> dict[str, Any]:
        """Generate routing configuration for system integration."""
        return {
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "terminals": {
                term_id: {
                    "name": term.name,
                    "purpose": term.purpose,
                    "routes": term.routes,
                    "type": "agent" if term_id in self.agent_terminals else "operational",
                }
                for term_id, term in self.all_terminals.items()
            },
            "routing_keywords": self.routing_rules,
            "total_terminals": len(self.all_terminals),
            "agent_count": len(self.agent_terminals),
            "operational_count": len(self.operational_terminals),
        }

    def activate(self) -> dict[str, Any]:
        """Activate the agent terminal system."""
        # Generate VSCode sessions config
        sessions_config = self.generate_vscode_sessions()
        sessions_path = self.root / ".vscode" / "sessions.json"
        sessions_path.parent.mkdir(exist_ok=True)

        with open(sessions_path, "w") as f:
            json.dump(sessions_config, f, indent=2)

        # Generate routing map
        routing_map = self.generate_routing_map()
        routing_path = self.root / "data" / "terminal_routing.json"
        routing_path.parent.mkdir(exist_ok=True)

        with open(routing_path, "w") as f:
            json.dump(routing_map, f, indent=2)

        return {
            "sessions_path": str(sessions_path),
            "routing_path": str(routing_path),
            "total_terminals": len(self.all_terminals),
            "agent_terminals": len(self.agent_terminals),
            "operational_terminals": len(self.operational_terminals),
            "routing_keywords": len(self.routing_rules),
        }


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    orchestrator = AgentTerminalOrchestrator(root)

    print("=" * 70)
    print("AGENT TERMINAL ORCHESTRATION SYSTEM")
    print("=" * 70)

    report = orchestrator.activate()

    print("\n✨ Agent Terminals Activated!")
    print(f"   Total terminals: {report['total_terminals']}")
    print(f"   Agent terminals: {report['agent_terminals']}")
    print(f"   Operational terminals: {report['operational_terminals']}")
    print(f"   Routing keywords: {report['routing_keywords']}")

    print("\n📋 Terminal Assignments:")
    for _term_id, term in orchestrator.all_terminals.items():
        print(f"   {term.name}")
        print(f"      Purpose: {term.purpose}")
        print(f"      Routes: {', '.join(term.routes[:3])}...")
        print()

    print("\n💾 Configuration saved:")
    print(f"   Sessions: {report['sessions_path']}")
    print(f"   Routing:  {report['routing_path']}")

    print("\n🔄 Next Steps:")
    print("   1. Reload VSCode window to activate terminals")
    print("   2. Wire terminal routing into logging/output systems")
    print("   3. Each agent can now write to their dedicated terminal")
    print("   4. Agents can observe each other's terminals")

    print("\n" + "=" * 70)
