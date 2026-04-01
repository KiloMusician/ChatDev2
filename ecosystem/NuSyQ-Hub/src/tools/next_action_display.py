"""Next Action Queue Display & Executor.

Shows the current action queue and provides shortcuts to invoke them.
Designed to be called continuously or on-demand during perpetual chug.

Interface:
  python next_action_display.py [--json] [--auto-pick N]

  --json       output JSON instead of human-readable
  --auto-pick N   automatically select and execute top N actions
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_action_queue(repo_root: Path) -> dict:
    """Load the latest action queue."""
    queue_file = repo_root / "state" / "next_action_queue.json"
    if not queue_file.exists():
        return {"error": "No action queue generated yet"}

    result: dict[Any, Any] = json.loads(queue_file.read_text())
    return result


def display_human_readable(queue: dict):
    """Display action queue in human-friendly format."""
    if "error" in queue:
        print(f"⚠️  No action queue: {queue['error']}")
        return

    print("\n🎯 NEXT ACTIONS (Perpetual Chug Queue)")
    print("=" * 70)
    print(f"Generated: {queue.get('generated_at', 'unknown')}")
    print(f"Refresh every: {queue.get('refresh_interval_minutes', 30)} minutes\n")

    actions = queue.get("actions", [])
    if not actions:
        print("✅ No pending actions! System is in good state.")
        return

    for i, action in enumerate(actions, 1):
        priority = action.get("priority", "UNKNOWN")
        priority_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "DEFERRED": "⚪",
        }.get(priority, "❓")

        print(f"{priority_emoji} [{i}] {action.get('title', 'Untitled')}")
        print(f"    Priority: {priority} | Effort: {action.get('effort', '?')}")
        print(f"    Type: {action.get('type', 'unknown')}")
        print(f"    Source: {action.get('source', 'unknown')}")

        context = action.get("context", {})
        if context and isinstance(context, dict):
            for key, value in list(context.items())[:2]:
                value_str = f"[{len(value)} items]" if isinstance(value, list) else str(value)[:50]
                print(f"    • {key}: {value_str}")
        print()

    # Summary
    logger.info("=" * 70)
    by_priority = queue.get("by_priority", {})
    priority_counts = [
        f"{priority} ({count})"
        for priority, count in sorted(
            by_priority.items(),
            key=lambda x: ["CRITICAL", "HIGH", "MEDIUM", "LOW", "DEFERRED"].index(x[0]),
        )
        if count > 0
    ]
    print(f"Summary: {' | '.join(priority_counts)}")
    print(
        f"\n💡 Tip: Run 'python scripts/start_nusyq.py next_action_exec {actions[0]['type']}' to tackle top action"
    )
    top_context = actions[0].get("context", {})
    if isinstance(top_context, dict):
        recommended = top_context.get("recommended_command")
        if isinstance(recommended, str) and recommended.strip():
            print(f"💡 Direct command: {recommended}")


def display_json(queue: dict):
    """Display action queue as JSON."""
    print(json.dumps(queue, indent=2))


def execute_action(repo_root: Path, action_type: str) -> int:
    """Execute an action by type (routes to appropriate handler)."""
    logger.info(f"\n🚀 Executing action type: {action_type}")
    logger.info("=" * 70)

    # Map action types to invocations
    action_handlers = {
        "fix_error": lambda: _handle_fix_error(repo_root),
        "validate_module": lambda: _handle_validate_module(repo_root),
        "expand_coverage": lambda: _handle_expand_coverage(repo_root),
        "resolve_quest": lambda: _handle_resolve_quest(repo_root),
        "heal_repository": lambda: _handle_heal_repository(repo_root),
        "scale_orchestration": lambda: _handle_scale_orchestration(repo_root),
        "integrate_cross_repo": lambda: _handle_integrate_cross_repo(repo_root),
        "improve_architecture": lambda: _handle_improve_architecture(repo_root),
    }

    handler = action_handlers.get(action_type)
    if not handler:
        logger.error(f"❌ Unknown action type: {action_type}")
        return 1

    try:
        return handler()
    except Exception as e:
        logger.error(f"❌ Action execution failed: {e}")
        return 1


def _handle_fix_error(repo_root: Path) -> int:
    """Handle high-priority blocker/error triage."""
    logger.info("🚨 Running blocker triage...")
    cmd = [
        sys.executable,
        "scripts/start_nusyq.py",
        "system_complete",
        "--async",
        "--budget-s=1200",
    ]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    logger.info(result.stdout[-800:] if len(result.stdout) > 800 else result.stdout)
    return result.returncode


def _handle_validate_module(repo_root: Path) -> int:
    """Validate and fix module imports."""
    logger.info("🔍 Validating module availability...")
    cmd = [sys.executable, "-m", "src.tools.perpetual_action_generator"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("✅ Module validation complete")
    logger.info(result.stdout)
    return result.returncode


def _handle_expand_coverage(repo_root: Path) -> int:
    """Expand test coverage."""
    logger.info("📈 Expanding test coverage...")
    cmd = [sys.executable, "-m", "pytest", "tests", "-q", "--cov=src"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    logger.info(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    return result.returncode


def _handle_resolve_quest(repo_root: Path) -> int:
    """Work on active quest."""
    logger.info("📜 Loading active quests...")
    cmd = [sys.executable, "scripts/start_nusyq.py", "guild_available", "claude"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    logger.info(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    return result.returncode


def _handle_heal_repository(repo_root: Path) -> int:
    """Run repository healing."""
    logger.info("🏥 Running repository health check...")
    cmd = [sys.executable, "scripts/start_nusyq.py", "doctor"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, timeout=60)
    logger.info(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    return result.returncode


def _handle_scale_orchestration(repo_root: Path) -> int:
    """Debug and scale orchestration tests."""
    logger.info("🎯 Scaling orchestration tests...")
    # First show current status
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_orchestration_comprehensive.py",
        "-v",
        "--tb=short",
    ]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, timeout=60)
    logger.info(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
    return result.returncode


def _handle_integrate_cross_repo(repo_root: Path) -> int:
    """Plan cross-repository integration."""
    del repo_root
    logger.info("🔗 Cross-repository integration planning...")
    logger.info("\nRepositories to integrate:")
    logger.info("  • NuSyQ-Hub (orchestration + healing)")
    logger.info("  • SimulatedVerse (consciousness simulation)")
    logger.info("  • NuSyQ (multi-agent environment)")
    logger.info("\nIntegration points:")
    logger.info("  • MCP Server coordination")
    logger.info("  • Consciousness bridge routing")
    logger.info("  • Quest system synchronization")
    logger.info("  • AI model orchestration")
    logger.info("\n✅ Integration roadmap available in docs/INTEGRATION_ROADMAP.md")
    return 0


def _handle_improve_architecture(repo_root: Path) -> int:
    """Analyze and improve architecture."""
    logger.info("🏗️  Improving architecture...")
    cmd = [sys.executable, "scripts/start_nusyq.py", "lifecycle_catalog"]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, timeout=60)
    logger.info(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    return result.returncode


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent.parent

    # Parse args
    json_output = "--json" in sys.argv
    execute = None

    for arg in sys.argv[1:]:
        if arg.startswith("--execute="):
            execute = arg.split("=", 1)[1]

    # Load queue
    queue = load_action_queue(repo_root)

    # Display or execute
    if execute:
        return execute_action(repo_root, execute)
    elif json_output:
        display_json(queue)
    else:
        display_human_readable(queue)

    return 0


if __name__ == "__main__":
    sys.exit(main())
