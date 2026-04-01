"""Action Menu System - Unified interface for NuSyQ capabilities

Provides categorized access to all system actions:
- 🏥 Heal: Repository health, quantum resolver, import fixes
- 📊 Analyze: Code analysis, system diagnostics, error reports
- 🏗️ Develop: ChatDev, code generation, feature development
- ✨ Create: New projects, prototypes, testing chamber
- 🔍 Review: Code quality, security, documentation
- 🐛 Debug: Error resolution, quantum problem resolver
- 🤖 AI: Multi-AI orchestration, model routing
- 🎯 Autonomous: Auto-cycle, self-improvement, evolution

OmniTag: {
    "purpose": "Unified action menu dispatcher",
    "dependencies": ["agent_task_router", "quest_log", "start_nusyq"],
    "context": "System orchestration, developer experience",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from scripts.nusyq_actions.shared import emit_action_receipt

# Action categories with descriptions
ACTION_CATEGORIES = {
    "heal": {
        "emoji": "🏥",
        "title": "Heal - Repository Health & Recovery",
        "description": "Fix broken paths, imports, dependencies, and system errors",
        "actions": [
            ("heal", "Run full repository health restoration"),
            ("hygiene", "Check spine hygiene and AI system availability"),
            ("prune_reports", "Prune/archive stale report artifacts with retention caps"),
            ("orchestrator_hygiene", "Prune stale background task history and reconcile queue"),
            ("doctor", "Comprehensive system health diagnostic"),
            ("doctor_status", "Poll/control doctor async jobs (--cancel/--retry)"),
            ("selfcheck", "Quick system integrity check"),
            ("trace_doctor", "Diagnose observability/tracing issues"),
        ],
    },
    "analyze": {
        "emoji": "📊",
        "title": "Analyze - System & Code Analysis",
        "description": "Deep analysis of code, errors, and system state",
        "actions": [
            ("analyze", "Analyze file or entire system with AI"),
            ("error_report", "Generate unified error diagnostic report"),
            ("error_report_status", "Poll/control error-report async jobs (--cancel/--retry)"),
            ("error_report_split", "Split error report by repository"),
            ("error_signal_bridge", "Bridge scanner findings into guild board signals"),
            ("signal_quest_bridge", "Convert guild signals into actionable quest log entries"),
            ("error_quest_bridge", "Generate quests directly from critical error diagnostics"),
            ("system_complete", "Run full completion gate checks"),
            ("system_complete_status", "Poll/control system-complete async jobs"),
            ("openclaw_smoke", "Validate OpenClaw gateway integration and CLI responsiveness"),
            ("openclaw_smoke_status", "Poll/control OpenClaw smoke async jobs"),
            ("openclaw_status", "Check OpenClaw operational readiness (gateway/channels)"),
            ("openclaw_gateway_start", "Start OpenClaw gateway runtime"),
            ("openclaw_gateway_status", "Check OpenClaw gateway runtime"),
            ("openclaw_gateway_stop", "Stop managed OpenClaw gateway runtime"),
            ("openclaw_bridge_start", "Start NuSyQ OpenClaw bridge process"),
            ("openclaw_bridge_status", "Check NuSyQ OpenClaw bridge status"),
            ("openclaw_bridge_stop", "Stop managed NuSyQ OpenClaw bridge"),
            (
                "openclaw_internal_send",
                "Send local-only OpenClaw message (no Slack/Discord credential required)",
            ),
            ("open_antigravity_start", "Start modular-window-server runtime"),
            ("open_antigravity_runtime_status", "Check antigravity runtime + health"),
            ("open_antigravity_stop", "Stop managed antigravity runtime"),
            ("antigravity_status", "Check Open Antigravity runtime health"),
            (
                "ignition",
                "Run full system ignition sequence (API + terminals + intermediary + routing)",
            ),
            ("integration_health", "Run consolidated stack health checks (fast/full/startup)"),
            ("culture_ship", "Run strategic learning/healing cycle"),
            ("culture_ship_status", "Poll/control Culture Ship async jobs"),
            (
                "causal_analysis",
                "Extract causal links from text and detect feedback loops from variable chains",
            ),
            (
                "graph_learning",
                "Generate dependency-graph learning report for impact prediction and healing",
            ),
            (
                "advanced_ai_quests",
                "Generate or deduplicate quests for remaining advanced-AI readiness gaps",
            ),
            (
                "specialization_status",
                "Inspect cross-agent specialization learning and task coverage",
            ),
            ("problem_signal_snapshot", "Capture current problem signals"),
            ("brief", "Quick system status brief"),
            ("ai_status", "Check AI agent availability"),
            ("capabilities", "List all system capabilities"),
            ("search", "Intelligent code discovery and search"),
            ("search_keyword", "Search codebase by keyword"),
            ("search_class", "Find class definitions"),
            ("search_function", "Find function definitions"),
            ("search_patterns", "Search for code patterns (consciousness, tagging, bridges)"),
            ("search_index_health", "Check SmartSearch index status and statistics"),
            ("search_hacking_quests", "Discover hacking game quests in codebase"),
        ],
    },
    "develop": {
        "emoji": "🏗️",
        "title": "Develop - Software Development",
        "description": "Build features, generate code, orchestrate development",
        "actions": [
            ("develop_system", "Develop system using ChatDev multi-agent"),
            ("generate", "Generate code using AI systems"),
            ("work", "Interactive work session with AI assistance"),
            ("task", "Execute specific development task"),
            ("auto_cycle", "Autonomous development cycle"),
        ],
    },
    "enhance": {
        "emoji": "⚡",
        "title": "Enhance - Code Quality & Modernization",
        "description": "Patch, fix, improve, update, and modernize codebase",
        "actions": [
            ("patch", "Quick patch for specific file/module"),
            ("fix", "Fix specific error or problem"),
            ("improve", "Improve code quality and performance"),
            ("update", "Update dependencies and code to latest versions"),
            ("modernize", "Modernize code to current Python patterns"),
            ("enhance", "Interactive enhancement mode (guided workflow)"),
        ],
    },
    "create": {
        "emoji": "✨",
        "title": "Create - New Projects & Prototypes",
        "description": "Create new projects, prototypes, testing chamber experiments",
        "actions": [
            ("generate", "Generate new code/project with AI"),
            ("develop_system", "Create project with ChatDev workflow"),
            ("work", "Interactive creation session"),
        ],
    },
    "review": {
        "emoji": "🔍",
        "title": "Review - Code Quality & Documentation",
        "description": "Review code quality, security, documentation completeness",
        "actions": [
            ("review", "AI code review of specific file"),
            ("analyze", "Comprehensive code analysis"),
            ("doctrine_check", "Check adherence to system doctrine"),
            ("test", "Run test suite with coverage"),
            ("test_history", "View test execution history"),
        ],
    },
    "debug": {
        "emoji": "🐛",
        "title": "Debug - Error Resolution",
        "description": "Debug errors using Quantum Resolver and AI systems",
        "actions": [
            ("debug", "Debug error with Quantum Error Bridge"),
            ("trace_doctor", "Diagnose tracing/observability errors"),
            ("error_report", "Analyze all system errors"),
            ("problem_signal_snapshot", "Capture problem signals for debugging"),
        ],
    },
    "ai": {
        "emoji": "🤖",
        "title": "AI - Multi-AI Orchestration",
        "description": "Coordinate across Ollama, ChatDev, LM Studio, OpenAI",
        "actions": [
            ("ai_status", "Check AI systems availability"),
            ("analyze", "Route analysis to AI systems"),
            ("review", "Route code review to AI"),
            ("debug", "Route debugging to AI/Quantum"),
            ("generate", "Route generation to AI"),
            ("causal_analysis", "Run local causal reasoning over text/system variables"),
            ("graph_learning", "Generate dependency graph-learning and impact report"),
            ("advanced_ai_quests", "Create quests for remaining advanced-AI readiness gaps"),
            ("specialization_status", "Inspect learned agent-task specialization profiles"),
            ("delegation_matrix", "Generate router delegation/schema/health matrix"),
            ("claude_doctor", "Diagnose Claude preflight/CLI/router/terminal readiness"),
            ("codex_doctor", "Diagnose Codex CLI/router/terminal readiness"),
            ("copilot_doctor", "Diagnose Copilot Chat/CLI/router/terminal readiness"),
            ("multi_agent_doctor", "Diagnose shared Claude/Codex/Copilot triad readiness"),
            ("agent_fleet_doctor", "Diagnose routed, passive, observed, and doctrine fleet surfaces"),
            ("copilot_probe", "Probe Copilot bridge initialization"),
            ("claude_preflight", "Run Claude Desktop/CLI preflight diagnostics"),
            ("openclaw_internal_send", "Route an internal OpenClaw message to target system"),
            ("vscode_extensions_plan", "Generate Codex-first VS Code extension isolation plan"),
            (
                "vscode_extensions_quickwins",
                "Generate immediate extension optimization actions from audits",
            ),
            ("orchestrator_status", "Check background task orchestrator"),
            ("orchestrator_hygiene", "Prune stale background task queue/history"),
            ("dispatch_task", "Dispatch task to background AI worker"),
        ],
    },
    "autonomous": {
        "emoji": "🎯",
        "title": "Autonomous - Self-Improvement",
        "description": "Autonomous cycles, evolution, perpetual operation",
        "actions": [
            ("auto_cycle", "Autonomous development cycle"),
            ("next_action_generate", "Generate next action queue"),
            ("next_action_exec", "Execute next action from queue"),
            ("pu_execute", "Execute Processing Unit queue"),
            ("suggest", "Get AI suggestions for next steps"),
        ],
    },
    "quest": {
        "emoji": "📜",
        "title": "Quest - Task Management",
        "description": "Manage quests, track work, coordinate multi-agent tasks",
        "actions": [
            ("log_quest", "Log work to quest system"),
            ("guild_status", "Check Guild board status"),
            ("guild_available", "View available Guild quests"),
            ("guild_claim", "Claim a Guild quest"),
            ("guild_start", "Start working on quest"),
            ("guild_complete", "Mark quest complete"),
            ("auto_quest", "Alias for error_quest_bridge (critical errors -> quests)"),
            ("quest_compact", "Compact duplicate open signal-linked quests"),
            ("guild_render", "Render Guild board visualization"),
        ],
    },
    "observability": {
        "emoji": "👁️",
        "title": "Observability - Tracing & Metrics",
        "description": "Distributed tracing, metrics, correlation tracking",
        "actions": [
            ("terminal_snapshot", "Generate terminal/output awareness registry for agents"),
            ("trace_service_status", "Check observability stack status"),
            ("trace_service_start", "Start observability services"),
            ("trace_service_stop", "Stop observability services"),
            ("trace_doctor", "Diagnose tracing issues"),
            ("trace_correlation_on", "Enable correlation tracking"),
            ("trace_correlation_off", "Disable correlation tracking"),
            ("trace_config_show", "Show tracing configuration"),
        ],
    },
    "learn": {
        "emoji": "🎓",
        "title": "Learn - Tutorials & Examples",
        "description": "Interactive examples, tutorials, system demonstrations",
        "actions": [
            ("examples", "Interactive example runner (12 orphaned examples rehabilitated)"),
            ("examples_list", "List all available examples"),
            ("tutorial", "Guided tutorial mode for learning NuSyQ"),
            ("demo", "Run system demo (Phase 5: SNS orchestrator quick_demo, full suite)"),
            # Phase 2 & 4 - Additional learning resources
            (
                "factory",
                "Factory function gateway (integrator, orchestrator, quantum, context_server)",
            ),
            ("dashboard", "Open Agent Dashboard WebView (VS Code extension)"),
        ],
    },
}


@dataclass
class ActionMenuItem:
    """Single action menu item."""

    command: str
    description: str
    category: str


def print_category_menu(category: str, show_all: bool = False) -> None:
    """Print actions for a specific category."""
    if category not in ACTION_CATEGORIES:
        print(f"❌ Unknown category: {category}")
        return

    cat = ACTION_CATEGORIES[category]
    print(f"\n{cat['emoji']} {cat['title']}")
    print(cat["description"])
    print("-" * 60)

    for i, (action, desc) in enumerate(cat["actions"], 1):
        if show_all or i <= 5:
            print(f"  [{i}] {action:30} - {desc}")

    if not show_all and len(cat["actions"]) > 5:
        print(f"\n  ... {len(cat['actions']) - 5} more actions (use --show-all)")


def print_main_menu() -> None:
    """Print the main action menu."""
    print("\n" + "=" * 70)
    print("🎯 NuSyQ Action Menu - Unified System Interface")
    print("=" * 70)

    print("\n📋 CATEGORIES:\n")

    categories = [
        ("heal", "Fix & restore system health"),
        ("analyze", "Analyze code & system state"),
        ("develop", "Build features & generate code"),
        ("enhance", "Patch, improve, update & modernize"),
        ("create", "Create new projects & prototypes"),
        ("review", "Review code quality & docs"),
        ("debug", "Debug & resolve errors"),
        ("ai", "Multi-AI orchestration"),
        ("autonomous", "Autonomous operation modes"),
        ("quest", "Quest & task management"),
        ("observability", "Tracing & metrics"),
        ("learn", "Tutorials & examples"),
    ]

    for key, desc in categories:
        cat = ACTION_CATEGORIES[key]
        print(f"  {cat['emoji']} {key:15} - {desc}")

    print("\n" + "=" * 70)
    print("\n💡 USAGE:")
    print("  View category:    python start_nusyq.py menu <category>")
    print("  Run action:       python start_nusyq.py <action> [args...]")
    print("  Quick examples:   python start_nusyq.py menu examples")
    print("\n" + "=" * 70)


def print_examples() -> None:
    """Print common usage examples."""
    print("\n" + "=" * 70)
    print("💡 Common Usage Examples")
    print("=" * 70)

    examples = [
        ("Heal", "python start_nusyq.py heal", "Fix all repository health issues"),
        ("Analyze", "python start_nusyq.py analyze", "Full system analysis"),
        (
            "Async Doctor",
            "python start_nusyq.py doctor --quick --async --json",
            "Submit doctor in background job mode",
        ),
        (
            "Doctor Status",
            "python start_nusyq.py doctor_status --wait=30 --json",
            "Poll latest doctor job; supports --cancel/--retry",
        ),
        ("Patch File", "python start_nusyq.py patch src/main.py 'Fix import'", "Quick patch"),
        ("Fix Error", 'python start_nusyq.py fix "ImportError: foo"', "Fix specific error"),
        (
            "Improve Code",
            "python start_nusyq.py improve src/orchestration/",
            "Quality improvements",
        ),
        ("Review File", "python start_nusyq.py review src/main.py", "AI code review"),
        ("Debug Error", 'python start_nusyq.py debug "Error message"', "Debug with AI"),
        ("Generate Code", "python start_nusyq.py generate auth system", "Generate with AI"),
        ("Modernize", "python start_nusyq.py modernize src/legacy.py", "Modern patterns"),
        ("System Status", "python start_nusyq.py brief", "Quick health check"),
        ("AI Status", "python start_nusyq.py ai_status", "Check AI availability"),
        ("Dev Cycle", "python start_nusyq.py auto_cycle", "Autonomous development"),
        ("Quest Status", "python start_nusyq.py guild_status", "View Guild board"),
        ("Test Suite", "python start_nusyq.py test", "Run tests with coverage"),
    ]

    for title, command, description in examples:
        print(f"\n  {title}:")
        print(f"    {command}")
        print(f"    → {description}")

    print("\n" + "=" * 70)


def handle_menu(args: list[str]) -> int:
    """Handle menu command invocation."""
    if len(args) < 2:
        # No arguments - show main menu
        print_main_menu()
        emit_action_receipt("menu", exit_code=0, metadata={"view": "main_menu"})
        return 0

    subcmd = args[1].lower()

    if subcmd == "examples":
        print_examples()
        emit_action_receipt("menu", exit_code=0, metadata={"view": "examples"})
        return 0

    if subcmd in ACTION_CATEGORIES:
        show_all = "--show-all" in args
        print_category_menu(subcmd, show_all=show_all)
        emit_action_receipt("menu", exit_code=0, metadata={"view": subcmd, "show_all": show_all})
        return 0

    print(f"❌ Unknown menu command: {subcmd}")
    print("\nAvailable commands:")
    print("  menu              - Show main menu")
    print("  menu <category>   - Show category actions")
    print("  menu examples     - Show usage examples")
    emit_action_receipt("menu", exit_code=1, metadata={"error": f"unknown_command: {subcmd}"})
    return 1


def get_action_category(action: str) -> str | None:
    """Get the category for an action."""
    for category, data in ACTION_CATEGORIES.items():
        if any(cmd == action for cmd, _ in data["actions"]):
            return category
    return None


def get_all_actions() -> list[ActionMenuItem]:
    """Get all actions as menu items."""
    items: list[ActionMenuItem] = []
    for category, data in ACTION_CATEGORIES.items():
        for command, description in data["actions"]:
            items.append(ActionMenuItem(command=command, description=description, category=category))
    return items


def format_action_hint(action: str) -> str:
    """Format a helpful hint for an action."""
    category = get_action_category(action)
    if not category:
        return f"Action: {action}"

    cat = ACTION_CATEGORIES[category]
    return f"{cat['emoji']} {action} ({category})"


# Testing / standalone execution
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        print_main_menu()
        print("\n\n")
        print_examples()
        print("\n\n")
        for cat in ["heal", "analyze", "ai"]:
            print_category_menu(cat, show_all=True)
            print("\n")
    else:
        sys.exit(handle_menu(["menu", *sys.argv[1:]]))
