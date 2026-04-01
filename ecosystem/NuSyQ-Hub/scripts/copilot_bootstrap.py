"""Copilot Agent Bootstrap System
==============================

Purpose: Self-aware initialization for Copilot working in NuSyQ-Hub.

When Copilot starts a session, this script provides:
1. System state snapshot (what's happening right now?)
2. My operational context (which terminals can I use?)
3. My assigned work (what quests are waiting for me?)
4. Highest-value commands (what should I run first?)
5. Safety guidelines (what should I avoid?)

Usage:
    python scripts/copilot_bootstrap.py [--full|--quick|--state|--work|--actions]

Outputs: JSON to stdout + readable summary to console.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class BootstrapContext:
    """Copilot agent operational context snapshot."""

    timestamp: str
    workspace_root: str
    repo_status: dict[str, Any]
    active_quests: list[dict[str, Any]]
    error_ground_truth: dict[str, Any]
    terminal_map: dict[str, str]
    safe_commands: list[str]
    next_actions: list[str]
    system_health: dict[str, bool]


def get_workspace_root() -> Path:
    """Get NuSyQ-Hub root."""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def get_repo_status() -> dict[str, Any]:
    """Quick git status for this repo."""
    try:
        root = get_workspace_root()
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no", "--ignore-submodules=all"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=20,
        )
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        modified = len([line for line in lines if line.startswith("M")])
        untracked = len([line for line in lines if line.startswith("??")])
        deleted = len([line for line in lines if line.startswith("D")])

        return {
            "branch": _get_branch(),
            "modified_files": modified,
            "untracked_files": untracked,
            "deleted_files": deleted,
            "dirty": bool(lines),
        }
    except Exception as e:
        return {"error": str(e), "dirty": None}


def _get_branch() -> str:
    """Get current git branch."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=get_workspace_root(),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def get_active_quests() -> list[dict[str, Any]]:
    """Parse active quests from quest_log.jsonl."""
    try:
        quest_log = get_workspace_root() / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
        if not quest_log.exists():
            return []

        active = []
        with open(quest_log) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("status") in {"active", "pending", "open"}:
                        active.append(
                            {
                                "id": entry.get("id"),
                                "title": entry.get("title") or entry.get("quest"),
                                "status": entry.get("status"),
                                "priority": entry.get("priority", 0),
                            }
                        )
                except json.JSONDecodeError:
                    pass

        return sorted(active, key=lambda x: -x.get("priority", 0))[:5]
    except Exception as e:
        return [{"error": str(e)}]


def get_error_ground_truth() -> dict[str, Any]:
    """Get latest error report summary."""
    try:
        # Try to read from ground truth file
        root = get_workspace_root()
        report_path = root / "state" / "ground_truth_errors.json"

        if not report_path.exists():
            return {"status": "no_report_yet", "total_errors": 0}

        with open(report_path) as f:
            data = json.load(f)

        total = data.get("summary", {}).get("total_errors", 0)
        by_repo = data.get("summary", {}).get("by_repository", {})
        by_severity = data.get("summary", {}).get("by_severity", {})

        return {
            "total_errors": total,
            "by_repository": by_repo,
            "by_severity": by_severity,
            "last_scan": data.get("metadata", {}).get("scan_timestamp", "unknown"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_terminal_map() -> dict[str, str]:
    """Map of specialized terminals available to Copilot."""
    return {
        "🤖 Claude": "General AI reasoning + code analysis",
        "🧩 Copilot": "Your primary terminal (GitHub Copilot)",
        "🔥 Errors": "Error report generation and analysis",
        "💡 Suggestions": "Quest suggestions and action recommendations",
        "✅ Tasks": "VS Code task execution and monitoring",
        "🧪 Tests": "Test running and validation",
        "📊 Metrics": "Performance metrics and observability",
        "🎯 Zeta": "Progress tracking and quest updates",
        "🤖 Agents": "Multi-agent coordination",
        "🏠 Main": "Main orchestrator commands",
        "⚡ Anomalies": "Anomaly detection and alerts",
        "🏗️ ChatDev": "ChatDev multi-agent orchestration",
        "🦙 Ollama": "Local LLM (Ollama) operations",
        # ... others as needed
    }


def get_safe_commands() -> list[str]:
    """High-value, safe commands Copilot can invoke."""
    return [
        # State inspection (read-only, no side effects)
        "python scripts/start_nusyq.py",
        "python scripts/start_nusyq.py health",
        "python scripts/start_nusyq.py error_report",
        "python scripts/start_nusyq.py capabilities",
        "python scripts/start_nusyq.py menu",
        # Quest operations (querying only)
        "python scripts/start_nusyq.py guild.status",
        "python scripts/start_nusyq.py suggest",
        # Code analysis (read-only)
        "python -m src.search.smart_search keyword '<term>' --limit 50",
        "python scripts/find_existing_tool.py --capability '<need>' --max-results 5",
        # Workspace verification
        "python scripts/verify_tripartite_workspace.py",
        # Integration testing
        "python scripts/validate_anti_hang.py",
    ]


def get_next_actions() -> list[str]:
    """Top recommendations for what to work on next."""
    return [
        "1. Build Error→Signal bridge (unblocks all downstream work)",
        "2. Wire signal→quest auto-creation (enables self-healing)",
        "3. Implement coordinator loop (orchestrates the system)",
        "4. Enhance quest→action recommendation (smart work suggestions)",
        "5. Create unified dashboard (real-time system awareness)",
    ]


def get_system_health() -> dict[str, bool]:
    """Quick health checks."""
    root = get_workspace_root()
    return {
        "quest_log_exists": (root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl").exists(),
        "guild_board_ready": (root / "src" / "guild" / "guild_board.py").exists(),
        "action_menu_available": (root / "scripts" / "nusyq_actions" / "menu.py").exists(),
        "error_scanner_ready": (root / "scripts" / "error_ground_truth_scanner.py").exists(),
        "api_running": _check_api_health(),
    }


def _check_api_health() -> bool:
    """Check if API is responding."""
    try:
        import urllib.request

        urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2)
        return True
    except Exception:
        return False


def generate_bootstrap_context() -> BootstrapContext:
    """Generate complete bootstrap snapshot for Copilot."""
    return BootstrapContext(
        timestamp=datetime.now().isoformat(),
        workspace_root=str(get_workspace_root()),
        repo_status=get_repo_status(),
        active_quests=get_active_quests(),
        error_ground_truth=get_error_ground_truth(),
        terminal_map=get_terminal_map(),
        safe_commands=get_safe_commands(),
        next_actions=get_next_actions(),
        system_health=get_system_health(),
    )


def print_bootstrap_summary(ctx: BootstrapContext) -> None:
    """Print human-readable bootstrap summary."""
    print("\n" + "=" * 80)
    print("🧠 COPILOT AGENT BOOTSTRAP")
    print("=" * 80)

    print(f"\n📍 WORKSPACE: {ctx.workspace_root}")
    print(f"⏰ TIMESTAMP: {ctx.timestamp}")

    # Repo Status
    print("\n📦 REPOSITORY STATUS")
    rs = ctx.repo_status
    if "error" not in rs:
        print(f"  Branch: {rs['branch']}")
        print(
            f"  Modified: {rs['modified_files']} | Untracked: {rs['untracked_files']} | Deleted: {rs['deleted_files']}"
        )
        print(f"  Status: {'DIRTY ⚠️' if rs['dirty'] else 'CLEAN ✅'}")
    else:
        print(f"  Error: {rs['error']}")

    # System Health
    print("\n🏥 SYSTEM HEALTH")
    for check, status in ctx.system_health.items():
        symbol = "✅" if status else "❌"
        print(f"  {symbol} {check}")

    # Active Quests
    print("\n📋 ACTIVE QUESTS (Top 5)")
    if ctx.active_quests:
        for quest in ctx.active_quests:
            if "error" not in quest:
                priority = "🔴" if quest.get("priority", 0) >= 4 else "🟡" if quest.get("priority", 0) >= 2 else "🟢"
                print(f"  {priority} {quest['title']} ({quest['status']})")
    else:
        print("  No active quests")

    # Errors
    print("\n🚨 ERROR GROUND TRUTH")
    egt = ctx.error_ground_truth
    if "error" not in egt and egt.get("total_errors"):
        print(f"  Total Errors: {egt['total_errors']}")
        if egt.get("by_severity"):
            for severity, count in egt["by_severity"].items():
                print(f"    - {severity}: {count}")
    else:
        print(f"  Status: {egt.get('status', 'unknown')}")

    # Terminals
    print("\n🖥️  AVAILABLE TERMINALS")
    for term, desc in list(ctx.terminal_map.items())[:5]:
        print(f"  {term}: {desc}")
    print(f"  ... and {len(ctx.terminal_map) - 5} more")

    # Safe Commands
    print("\n⚡ SAFE COMMANDS (Read-Only)")
    for cmd in ctx.safe_commands[:5]:
        print(f"  • {cmd}")
    print(f"  ... and {len(ctx.safe_commands) - 5} more")

    # Next Actions
    print("\n🎯 RECOMMENDED NEXT ACTIONS")
    for action in ctx.next_actions:
        print(f"  {action}")

    print("\n" + "=" * 80 + "\n")


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Copilot agent bootstrap system")
    parser.add_argument("--output", choices=["summary", "json", "both"], default="summary", help="Output format")
    parser.add_argument("--full", action="store_true", help="Generate full detailed context")

    args = parser.parse_args()

    try:
        ctx = generate_bootstrap_context()

        if args.output in ("summary", "both"):
            print_bootstrap_summary(ctx)

        if args.output in ("json", "both"):
            import dataclasses

            json_data = dataclasses.asdict(ctx)
            print(json.dumps(json_data, indent=2))

        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
