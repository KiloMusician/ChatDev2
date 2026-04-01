#!/usr/bin/env python3
"""Intelligent Terminal Orchestration System - ACTIVATED.

[ROUTE AGENTS] 🤖
Routes different output streams to dedicated terminals with purpose-driven assignment.
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


# Intelligent Terminal Configuration
INTELLIGENT_TERMINALS = {
    "errors": TerminalPurpose(
        name="🔥 Errors",
        purpose="Error output, exceptions, failures",
        icon="bug",
        color="terminal.ansiRed",
        auto_commands=["echo '=== Error Monitor Active ==='"],
        routes=["error", "exception", "failed", "stderr"],
        persistent=True,
    ),
    "suggestions": TerminalPurpose(
        name="💡 Suggestions",
        purpose="Next steps, recommendations, suggestions",
        icon="lightbulb",
        color="terminal.ansiYellow",
        auto_commands=["echo '=== Suggestion Stream Active ==='"],
        routes=["suggest", "recommend", "next_steps", "hint"],
        persistent=True,
    ),
    "tasks": TerminalPurpose(
        name="✓ Tasks",
        purpose="Task execution, work queue, PU processing",
        icon="checklist",
        color="terminal.ansiCyan",
        auto_commands=["echo '=== Task Execution Monitor ==='"],
        routes=["task", "pu_queue", "work_queue", "processing"],
        persistent=True,
    ),
    "zeta": TerminalPurpose(
        name="🎯 Zeta",
        purpose="Zeta orchestration, autonomous cycles, meta-operations",
        icon="target",
        color="terminal.ansiMagenta",
        auto_commands=["echo '=== Zeta Autonomous Control ==='"],
        routes=["zeta", "autonomous", "orchestrat", "cycle"],
        persistent=True,
    ),
    "agents": TerminalPurpose(
        name="🤖 Agents",
        purpose="Multi-agent coordination, AI systems",
        icon="robot",
        color="terminal.ansiGreen",
        auto_commands=["echo '=== Agent Coordination Hub ==='"],
        routes=["agent", "ai_", "ollama", "multi-agent"],
        persistent=True,
    ),
    "claude": TerminalPurpose(
        name="Claude",
        purpose="Anthropic Claude agent output and extension chatter",
        icon="account",
        color="terminal.ansiCyan",
        auto_commands=["echo '=== Claude Channel ==='"],
        routes=["claude", "anthropic"],
        persistent=True,
    ),
    "copilot": TerminalPurpose(
        name="Copilot",
        purpose="GitHub Copilot agent output and extension chatter",
        icon="github",
        color="terminal.ansiBlue",
        auto_commands=["echo '=== Copilot Channel ==='"],
        routes=["copilot", "github copilot", "gh copilot"],
        persistent=True,
    ),
    "codex": TerminalPurpose(
        name="Codex",
        purpose="OpenAI Codex agent output and extension chatter",
        icon="terminal",
        color="terminal.ansiGreen",
        auto_commands=["echo '=== Codex Channel ==='"],
        routes=["codex", "openai", "gpt"],
        persistent=True,
    ),
    "chatdev": TerminalPurpose(
        name="ChatDev",
        purpose="ChatDev multi-agent team coordination",
        icon="organization",
        color="terminal.ansiMagenta",
        auto_commands=["echo '=== ChatDev Coordination ==='"],
        routes=["chatdev", "chat dev"],
        persistent=True,
    ),
    "ai_council": TerminalPurpose(
        name="AI Council",
        purpose="AI Council deliberations and consensus runs",
        icon="people",
        color="terminal.ansiYellow",
        auto_commands=["echo '=== AI Council ==='"],
        routes=["ai council", "council", "consensus"],
        persistent=True,
    ),
    "intermediary": TerminalPurpose(
        name="Intermediary",
        purpose="Routing, relay, and broker coordination",
        icon="plug",
        color="terminal.ansiWhite",
        auto_commands=["echo '=== Intermediary Relay ==='"],
        routes=["intermediary", "broker", "relay", "router"],
        persistent=True,
    ),
    "metrics": TerminalPurpose(
        name="📊 Metrics",
        purpose="Cultivation metrics, health monitoring, dashboards",
        icon="graph",
        color="terminal.ansiBlue",
        auto_commands=["echo '=== Metrics & Health Monitor ==='"],
        routes=["metric", "health", "dashboard", "monitor"],
        persistent=True,
    ),
    "anomalies": TerminalPurpose(
        name="⚡ Anomalies",
        purpose="Unusual events, orphaned processes, unexpected behaviors",
        icon="zap",
        color="terminal.ansiRed",
        auto_commands=["echo '=== Anomaly Detection Active ==='"],
        routes=["anomaly", "orphan", "unexpected", "zombie"],
        persistent=True,
    ),
    "future": TerminalPurpose(
        name="🔮 Future",
        purpose="Planned features, upcoming tasks, development roadmap",
        icon="crystal_ball",
        color="terminal.ansiWhite",
        auto_commands=["echo '=== Future Development Stream ==='"],
        routes=["future", "planned", "roadmap", "upcoming"],
        persistent=True,
    ),
    "main": TerminalPurpose(
        name="🏠 Main",
        purpose="General output, snapshots, status reports",
        icon="home",
        color="terminal.ansiWhite",
        auto_commands=["echo '=== Main Output Stream ==='"],
        routes=["snapshot", "status", "general", "info"],
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


def _load_terminal_groups(root: Path) -> dict[str, TerminalPurpose]:
    """Load terminal groups from config/terminal_groups.json when available."""
    config_path = root / "config" / "terminal_groups.json"
    if not config_path.exists():
        return INTELLIGENT_TERMINALS
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return INTELLIGENT_TERMINALS

    terminals: dict[str, TerminalPurpose] = {}
    for section in ("agent_terminals", "operational_terminals"):
        groups = data.get(section, {})
        if not isinstance(groups, dict):
            continue
        for term_id, payload in groups.items():
            if not isinstance(payload, dict):
                continue
            fallback = INTELLIGENT_TERMINALS.get(term_id)
            terminals[term_id] = _build_terminal_purpose(term_id, payload, fallback)

    return terminals or INTELLIGENT_TERMINALS


class IntelligentTerminalOrchestrator:
    """Routes output intelligently based on content and purpose."""

    def __init__(self):
        self.root = Path(__file__).parents[1]
        self.terminals = _load_terminal_groups(self.root)
        self.routing_rules = self._build_routing_rules()
        self.sessions_config_path = self.root / ".vscode" / "sessions.json"
        self.routing_map_path = self.root / "data" / "terminal_routing.json"

    def _build_routing_rules(self) -> dict[str, str]:
        """Build keyword -> terminal routing map."""
        rules = {}
        for term_id, term in self.terminals.items():
            for keyword in term.routes:
                rules[keyword.lower()] = term_id
        return rules

    def route_output(self, content: str, default: str = "main") -> str:
        """Determine which terminal should receive this output."""
        content_lower = content.lower()

        # Check routing keywords
        for keyword, terminal_id in self.routing_rules.items():
            if keyword in content_lower:
                return terminal_id

        return default

    def generate_vscode_sessions(self) -> dict[str, Any]:
        """Generate VSCode terminal-keeper sessions.json config."""
        sessions = []

        for _term_id, term in self.terminals.items():
            terminal_config = {
                "name": term.name,
                "icon": term.icon,
                "color": term.color,
                "autoExecuteCommands": True,
                "commands": term.auto_commands,
                "clear": False,
                "executeCommandsInterval": 0,
            }
            sessions.append(terminal_config)

        return {
            "$schema": "https://cdn.statically.io/gh/nguyenngoclongdev/cdn/main/schema/v11/terminal-keeper.json",
            "theme": "tribe",
            "active": "intelligent",
            "activateOnStartup": True,
            "keepExistingTerminals": False,
            "sessions": {
                "intelligent": sessions,
                "default": [
                    {
                        "name": "Legacy (preserve)",
                        "icon": "archive",
                        "color": "terminal.ansiBlack",
                        "commands": ["echo 'Legacy terminals preserved'"],
                    }
                ],
            },
        }

    def update_sessions_config(self):
        """Update .vscode/sessions.json with intelligent terminals."""
        config = self.generate_vscode_sessions()

        # Backup existing config
        if self.sessions_config_path.exists():
            backup_path = self.sessions_config_path.parent / "sessions.json.backup"
            backup_path.write_text(self.sessions_config_path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"✅ Backed up existing config to: {backup_path}")

        # Write new config
        self.sessions_config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        print(f"✅ Updated sessions config: {self.sessions_config_path}")

    def generate_orchestration_report(self) -> dict[str, Any]:
        """Generate report on intelligent terminal configuration."""
        return {
            "generated_at": datetime.now().isoformat(),
            "total_terminals": len(self.terminals),
            "terminals": {
                term_id: {
                    "name": term.name,
                    "purpose": term.purpose,
                    "routes": term.routes,
                    "persistent": term.persistent,
                }
                for term_id, term in self.terminals.items()
            },
            "routing_keywords": len(self.routing_rules),
            "status": "intelligent orchestration ready",
        }

    def write_routing_map(self) -> Path:
        """Write routing map for terminal output helpers."""
        payload = {
            "version": "2.1.0",
            "timestamp": datetime.now().isoformat(),
            "terminals": {
                term_id: {
                    "name": term.name,
                    "purpose": term.purpose,
                    "routes": term.routes,
                }
                for term_id, term in self.terminals.items()
            },
            "routing_keywords": self.routing_rules,
            "total_terminals": len(self.terminals),
        }
        self.routing_map_path.parent.mkdir(parents=True, exist_ok=True)
        self.routing_map_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"? Updated routing map: {self.routing_map_path}")
        return self.routing_map_path

    def save_orchestration_state(self):
        """Save orchestration state for autonomous systems."""
        state_path = self.root / "data" / "intelligent_terminal_state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)

        report = self.generate_orchestration_report()
        state_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"✅ Saved orchestration state: {state_path}")
        return report


def main():
    """Activate intelligent terminal orchestration."""
    print("🧠 Activating Intelligent Terminal Orchestration System")
    print("=" * 70)

    orchestrator = IntelligentTerminalOrchestrator()

    # Update VSCode sessions config
    print("\n📝 Updating VSCode terminal configuration...")
    orchestrator.update_sessions_config()

    # Save state
    print("\n💾 Saving orchestration state...")
    report = orchestrator.save_orchestration_state()
    orchestrator.write_routing_map()

    # Display summary
    print("\n✨ Intelligent Terminals Activated!")
    print(f"   Total terminals: {report['total_terminals']}")
    print(f"   Routing keywords: {report['routing_keywords']}")

    print("\n📋 Terminal Assignments:")
    for _term_id, term in orchestrator.terminals.items():
        print(f"   {term.name}")
        print(f"      Purpose: {term.purpose}")
        print(f"      Routes: {', '.join(term.routes[:3])}...")
        print()

    print("\n🎯 Next Steps:")
    print("   1. Reload VSCode window to activate new terminals")
    print("   2. Run: python scripts/intelligent_terminal_router.py")
    print("   3. Watch output automatically route to correct terminals")

    print("\n✅ Activation complete!")


if __name__ == "__main__":
    main()
