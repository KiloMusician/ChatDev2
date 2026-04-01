"""Copilot Agent Capability Registry
==================================

Purpose: Unified catalog of what Copilot can safely invoke, invoke, and delegate in NuSyQ-Hub.

Structure:
- Terminal Map: Which terminal handles which domain
- Safe Commands: Read-only queries with no side effects
- Modifying Commands: Safe state-changing operations
- Unsafe Commands: Things that require human approval
- Delegatable Tasks: Work to route to other agents
- Integration Points: APIs, webhooks, event subscriptions

Auto-refreshes when tooling changes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class CommandSafety(Enum):
    """Safety level of a command."""

    READ_ONLY = "read_only"  # No side effects
    SAFE_WRITE = "safe_write"  # Creates new, doesn't modify existing
    STANDARD_WRITE = "standard_write"  # Modifies existing, but reversible
    RISKY = "risky"  # Destructive, requires care
    UNSAFE = "unsafe"  # Requires human approval


class TerminalDomain(Enum):
    """Primary domain for a terminal."""

    STATE = "state"  # System state queries
    ERRORS = "errors"  # Error handling and reporting
    SUGGESTIONS = "suggestions"  # Work suggestions and routing
    TESTING = "testing"  # Test execution
    METRICS = "metrics"  # Observability and metrics
    TASKS = "tasks"  # VS Code task execution
    AI = "ai"  # Multi-agent coordination
    CODE = "code"  # Code generation and analysis
    ORCHESTRATION = "orchestration"  # System orchestration


@dataclass
class TerminalInfo:
    """Info about a specialized terminal."""

    name: str
    emoji: str
    domain: TerminalDomain
    purpose: str
    safe_to_use: bool = True
    refresh_interval: int = 60  # seconds


@dataclass
class CommandInfo:
    """Info about a Command."""

    name: str
    category: str  # state, analysis, healing, development, etc.
    safety: CommandSafety
    description: str
    python_cmd: str | None = None  # e.g. "python scripts/start_nusyq.py health"
    terminal: str | None = None  # Which terminal to use
    example: str | None = None
    expected_effects: str | None = None  # What it changes
    blockers: list[str] | None = None  # Conditions that prevent use
    dependencies: list[str] | None = None  # Must run before this


@dataclass
class CapabilityRegistry:
    """Unified view of Copilot's capabilities."""

    timestamp: str
    terminals: dict[str, TerminalInfo]
    commands: dict[str, CommandInfo]
    task_routes: dict[str, str]  # task → terminal
    api_endpoints: dict[str, str]  # endpoint → description
    unsafe_patterns: list[str]  # Things Copilot should avoid


class RegistryBuilder:
    """Build the capability registry."""

    def __init__(self):
        self.terminals: dict[str, TerminalInfo] = {}
        self.commands: dict[str, CommandInfo] = {}
        self.task_routes: dict[str, str] = {}
        self.api_endpoints: dict[str, str] = {}
        self.unsafe_patterns: list[str] = []

    def add_terminal(self, info: TerminalInfo) -> RegistryBuilder:
        """Register a terminal Copilot can use."""
        self.terminals[info.name] = info
        return self

    def add_command(self, info: CommandInfo) -> RegistryBuilder:
        """Register a command Copilot can invoke."""
        self.commands[info.name] = info
        return self

    def add_task_route(self, task_name: str, terminal: str) -> RegistryBuilder:
        """Map a VS Code task to a terminal."""
        self.task_routes[task_name] = terminal
        return self

    def add_api_endpoint(self, path: str, description: str) -> RegistryBuilder:
        """Register an API endpoint Copilot can call."""
        self.api_endpoints[path] = description
        return self

    def add_unsafe_pattern(self, pattern: str) -> RegistryBuilder:
        """Register a pattern Copilot should avoid."""
        self.unsafe_patterns.append(pattern)
        return self

    def build(self) -> CapabilityRegistry:
        """Build the final registry."""
        return CapabilityRegistry(
            timestamp=datetime.now().isoformat(),
            terminals=self.terminals,
            commands=self.commands,
            task_routes=self.task_routes,
            api_endpoints=self.api_endpoints,
            unsafe_patterns=self.unsafe_patterns,
        )


def create_default_registry() -> CapabilityRegistry:
    """Create the default Copilot capability registry."""
    builder = RegistryBuilder()

    # ===== TERMINALS =====
    builder.add_terminal(
        TerminalInfo(
            name="🤖 Claude",
            emoji="🤖",
            domain=TerminalDomain.AI,
            purpose="General AI reasoning and analysis",
        )
    )

    builder.add_terminal(
        TerminalInfo(
            name="🧩 Copilot",
            emoji="🧩",
            domain=TerminalDomain.CODE,
            purpose="Your primary terminal (GitHub Copilot agent)",
        )
    )

    builder.add_terminal(
        TerminalInfo(
            name="🔥 Errors",
            emoji="🔥",
            domain=TerminalDomain.ERRORS,
            purpose="Error report generation and ground truth",
        )
    )

    builder.add_terminal(
        TerminalInfo(
            name="💡 Suggestions",
            emoji="💡",
            domain=TerminalDomain.SUGGESTIONS,
            purpose="Quest suggestions and next-action recommendations",
        )
    )

    builder.add_terminal(
        TerminalInfo(
            name="✅ Tasks",
            emoji="✅",
            domain=TerminalDomain.TASKS,
            purpose="VS Code task execution and monitoring",
        )
    )

    builder.add_terminal(
        TerminalInfo(
            name="🧪 Tests",
            emoji="🧪",
            domain=TerminalDomain.TESTING,
            purpose="Test runner and validation",
        )
    )

    builder.add_terminal(
        TerminalInfo(
            name="📊 Metrics",
            emoji="📊",
            domain=TerminalDomain.METRICS,
            purpose="Performance metrics and health checks",
        )
    )

    builder.add_terminal(
        TerminalInfo(
            name="🎯 Zeta",
            emoji="🎯",
            domain=TerminalDomain.STATE,
            purpose="Progress tracking and quest state updates",
        )
    )

    builder.add_terminal(
        TerminalInfo(
            name="🤖 Agents",
            emoji="🤖",
            domain=TerminalDomain.ORCHESTRATION,
            purpose="Multi-agent coordination and routing",
        )
    )

    # ===== SAFE COMMANDS (READ-ONLY) =====
    builder.add_command(
        CommandInfo(
            name="system_snapshot",
            category="state",
            safety=CommandSafety.READ_ONLY,
            description="Get complete system state snapshot",
            python_cmd="python scripts/start_nusyq.py",
            terminal="✅ Tasks",
            example="python scripts/start_nusyq.py",
            expected_effects="Writes state/reports/current_state.md",
        )
    )

    builder.add_command(
        CommandInfo(
            name="health_check",
            category="state",
            safety=CommandSafety.READ_ONLY,
            description="Run comprehensive health diagnostics",
            python_cmd="python scripts/start_nusyq.py health",
            terminal="📊 Metrics",
            example="python scripts/start_nusyq.py health",
        )
    )

    builder.add_command(
        CommandInfo(
            name="error_report",
            category="errors",
            safety=CommandSafety.READ_ONLY,
            description="Generate canonial error ground truth report",
            python_cmd="python scripts/error_ground_truth_scanner.py",
            terminal="🔥 Errors",
            expected_effects="Writes state/ground_truth_errors.json",
        )
    )

    builder.add_command(
        CommandInfo(
            name="list_capabilities",
            category="state",
            safety=CommandSafety.READ_ONLY,
            description="List all 700+ system capabilities",
            python_cmd="python scripts/start_nusyq.py capabilities",
            terminal="✅ Tasks",
        )
    )

    builder.add_command(
        CommandInfo(
            name="show_action_menu",
            category="state",
            safety=CommandSafety.READ_ONLY,
            description="Display action menu with categories",
            python_cmd="python scripts/start_nusyq.py menu",
            terminal="💡 Suggestions",
        )
    )

    builder.add_command(
        CommandInfo(
            name="quest_suggestions",
            category="suggestions",
            safety=CommandSafety.READ_ONLY,
            description="Get AI suggestions for next tasks",
            python_cmd="python scripts/start_nusyq.py suggest",
            terminal="💡 Suggestions",
        )
    )

    builder.add_command(
        CommandInfo(
            name="smart_search",
            category="analysis",
            safety=CommandSafety.READ_ONLY,
            description="Zero-token semantic code search",
            python_cmd="python -m src.search.smart_search keyword '<term>'",
            terminal="🧩 Copilot",
            example="python -m src.search.smart_search keyword 'error_handler'",
        )
    )

    builder.add_command(
        CommandInfo(
            name="find_existing_tool",
            category="analysis",
            safety=CommandSafety.READ_ONLY,
            description="Find existing tool for capability (avoids re-invention)",
            python_cmd="python scripts/find_existing_tool.py --capability",
            terminal="🧩 Copilot",
            example="python scripts/find_existing_tool.py --capability 'error parsing'",
        )
    )

    builder.add_command(
        CommandInfo(
            name="verify_workspace",
            category="state",
            safety=CommandSafety.READ_ONLY,
            description="Verify tripartite workspace integrity",
            python_cmd="python scripts/verify_tripartite_workspace.py",
            terminal="📊 Metrics",
        )
    )

    # ===== SAFE WRITE COMMANDS =====
    builder.add_command(
        CommandInfo(
            name="claim_quest",
            category="work",
            safety=CommandSafety.SAFE_WRITE,
            description="Claim a quest from the guild board",
            python_cmd="python scripts/start_nusyq.py guild.claim <quest_id>",
            terminal="🎯 Zeta",
            dependencies=["guild_board_ready"],
        )
    )

    builder.add_command(
        CommandInfo(
            name="post_progress",
            category="work",
            safety=CommandSafety.SAFE_WRITE,
            description="Post progress message to guild board",
            python_cmd="python scripts/start_nusyq.py guild.post '<message>'",
            terminal="🎯 Zeta",
        )
    )

    builder.add_command(
        CommandInfo(
            name="complete_quest",
            category="work",
            safety=CommandSafety.SAFE_WRITE,
            description="Mark a quest complete",
            python_cmd="python scripts/start_nusyq.py guild.complete <quest_id>",
            terminal="🎯 Zeta",
        )
    )

    # ===== UNSAFE PATTERNS =====
    builder.add_unsafe_pattern("git push")  # Requires explicit approval
    builder.add_unsafe_pattern("git commit --amend")  # Risky history rewrite
    builder.add_unsafe_pattern("rm -rf")  # Destructive
    builder.add_unsafe_pattern("git reset --hard")  # Destructive
    builder.add_unsafe_pattern("docker rm")  # Destructive
    builder.add_unsafe_pattern("DROP TABLE")  # Database destruction

    # ===== TASK ROUTES =====
    builder.add_task_route("🧠 NuSyQ: System State Snapshot", "✅ Tasks")
    builder.add_task_route("🔥 Error Scan: Full Ecosystem", "🔥 Errors")
    builder.add_task_route("🧪 NuSyQ: Intelligent Tests Terminal", "🧪 Tests")
    builder.add_task_route("🏗️ ChatDev: Start", "🤖 Agents")

    # ===== API ENDPOINTS =====
    builder.add_api_endpoint("/health", "Service health check")
    builder.add_api_endpoint("/quests", "List all quests")
    builder.add_api_endpoint("/quests/{id}", "Get quest details")
    builder.add_api_endpoint("/quests/complete", "Mark quest complete")
    builder.add_api_endpoint("/guild/status", "Get guild board state")
    builder.add_api_endpoint("/guild/signals", "List current signals")
    builder.add_api_endpoint("/capabilities", "List all capabilities")
    builder.add_api_endpoint("/error-report", "Get latest error report")

    return builder.build()


def save_registry(registry: CapabilityRegistry, path: Path | None = None) -> Path:
    """Save registry to JSON file."""
    if path is None:
        path = Path(__file__).parent.parent / "data" / "copilot_capability_registry.json"

    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert dataclasses to dict
    registry_dict = asdict(registry)

    # Convert enums to strings
    def serialize(obj: Any) -> Any:
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [serialize(v) for v in obj]
        elif hasattr(obj, "__dict__"):
            return serialize(obj.__dict__)
        return obj

    registry_dict = serialize(registry_dict)

    with open(path, "w") as f:
        json.dump(registry_dict, f, indent=2)

    return path


def load_registry(path: Path | None = None) -> CapabilityRegistry:
    """Load registry from JSON file."""
    if path is None:
        path = Path(__file__).parent.parent / "data" / "copilot_capability_registry.json"

    if not path.exists():
        return create_default_registry()

    with open(path) as f:
        data = json.load(f)

    # Reconstruct from dict
    return CapabilityRegistry(
        timestamp=data.get("timestamp"),
        terminals={
            name: TerminalInfo(
                name=name,
                emoji=info["emoji"],
                domain=TerminalDomain(info["domain"]),
                purpose=info["purpose"],
                safe_to_use=info.get("safe_to_use", True),
                refresh_interval=info.get("refresh_interval", 60),
            )
            for name, info in data.get("terminals", {}).items()
        },
        commands={
            name: CommandInfo(
                name=name,
                category=info["category"],
                safety=CommandSafety(info["safety"]),
                description=info["description"],
                python_cmd=info.get("python_cmd"),
                terminal=info.get("terminal"),
                example=info.get("example"),
                expected_effects=info.get("expected_effects"),
                blockers=info.get("blockers"),
                dependencies=info.get("dependencies"),
            )
            for name, info in data.get("commands", {}).items()
        },
        task_routes=data.get("task_routes", {}),
        api_endpoints=data.get("api_endpoints", {}),
        unsafe_patterns=data.get("unsafe_patterns", []),
    )


def print_registry_summary(registry: CapabilityRegistry) -> None:
    """Print human-readable registry summary."""
    print("\n" + "=" * 80)
    print("📋 COPILOT CAPABILITY REGISTRY")
    print("=" * 80)

    print(f"\n🖥️  TERMINALS ({len(registry.terminals)} available)")
    for name, info in list(registry.terminals.items())[:8]:
        status = "✅" if info.safe_to_use else "⚠️"
        print(f"  {status} {name}: {info.purpose}")
    if len(registry.terminals) > 8:
        print(f"  ... and {len(registry.terminals) - 8} more")

    print(
        f"\n⚡ SAFE COMMANDS ({len([c for c in registry.commands.values() if c.safety == CommandSafety.READ_ONLY])} read-only)"
    )
    for _, info in [(n, c) for n, c in registry.commands.items() if c.safety == CommandSafety.READ_ONLY][:6]:
        print(f"  • {info.name}: {info.description}")

    print(
        f"\n🛡️  WRITE COMMANDS ({len([c for c in registry.commands.values() if c.safety in (CommandSafety.SAFE_WRITE, CommandSafety.STANDARD_WRITE)])})"
    )
    for _, info in [
        (n, c)
        for n, c in registry.commands.items()
        if c.safety in (CommandSafety.SAFE_WRITE, CommandSafety.STANDARD_WRITE)
    ][:4]:
        print(f"  • {info.name}: {info.description}")

    print(
        f"\n⛔ UNSAFE PATTERNS to avoid: {', '.join(registry.unsafe_patterns[:3])}... ({len(registry.unsafe_patterns)} total)"
    )

    print(f"\n🔌 API ENDPOINTS ({len(registry.api_endpoints)})")
    for endpoint, desc in list(registry.api_endpoints.items())[:5]:
        print(f"  • {endpoint}: {desc}")
    if len(registry.api_endpoints) > 5:
        print(f"  ... and {len(registry.api_endpoints) - 5} more")

    print("\n" + "=" * 80 + "\n")


def main() -> int:
    """Main entry point."""
    registry = create_default_registry()
    path = save_registry(registry)

    print(f"✅ Saved registry to {path}")
    print_registry_summary(registry)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
