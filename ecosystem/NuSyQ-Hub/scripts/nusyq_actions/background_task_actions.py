"""Background Task Actions - CLI handlers for background task orchestration.

These handlers enable Claude Code CLI (and other agents) to dispatch
high-token operations to local LLMs (Ollama, LM Studio), ChatDev, or Copilot.
"""

import asyncio
import json
import logging
from pathlib import Path

from scripts.nusyq_actions.shared import (
    collect_audit_intelligence,
    emit_action_receipt,
    format_audit_intelligence_lines,
)

logger = logging.getLogger(__name__)

VALID_BACKGROUND_TARGETS = {"ollama", "lm_studio", "chatdev", "copilot", "auto"}


def _audit_intelligence() -> dict:
    hub_root = Path(__file__).resolve().parents[2]
    return collect_audit_intelligence(hub_root, include_sessions=False)


def _parse_dispatch_task_args(args: list[str]) -> tuple[str, str, str | None, str, str]:
    """Parse dispatch_task arguments into structured components.

    Returns:
        (prompt, target, model, priority, task_type)
    """
    prompt_parts = []
    target = "auto"
    model = None
    priority = "normal"
    task_type = "general"

    for arg in args:
        if arg.startswith("--target="):
            target = arg.split("=", 1)[1].strip().lower()
        elif arg.startswith("--model="):
            model = arg.split("=", 1)[1]
        elif arg.startswith("--priority="):
            priority = arg.split("=", 1)[1]
        elif arg.startswith("--type="):
            task_type = arg.split("=", 1)[1]
        else:
            prompt_parts.append(arg)

    prompt = " ".join(prompt_parts)
    return prompt, target, model, priority, task_type


def _print_dispatch_task_config(target: str, model: str | None, priority: str, task_type: str, prompt: str) -> None:
    """Print dispatch task configuration before execution."""
    print(f"Dispatching task to {target}...")
    print(f"  Model: {model or 'auto'}")
    print(f"  Priority: {priority}")
    print(f"  Task type: {task_type}")
    print(f"  Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    print()


def _handle_dispatch_task_result(result: dict) -> int:
    """Process and display dispatch task result.

    Returns:
        Exit code (0 for success/pending, 1 for failure)
    """
    print(json.dumps(result, indent=2))

    if result.get("status") == "completed":
        print("\n✅ Task completed successfully!")
        if result.get("result_preview"):
            print(f"\nResult preview:\n{result['result_preview']}")
        return 0
    elif result.get("status") == "failed":
        print(f"\n❌ Task failed: {result.get('error')}")
        return 1
    else:
        print(f"\nTask status: {result.get('status')}")
        return 0


def handle_dispatch_task(args: list[str]) -> int:
    """Dispatch a task to local LLMs for background execution.

    Usage:
        dispatch_task "Your prompt here" [--target=ollama|lm_studio|chatdev|copilot|auto] [--model=model_name]
        dispatch_task "Analyze this codebase for security issues" --target=ollama --model=deepseek-coder-v2:16b
        dispatch_task "Generate comprehensive tests" --target=chatdev
        dispatch_task "Review this module for bugs" --target=copilot --type=review
    """
    try:
        from src.orchestration.background_task_orchestrator import (
            dispatch_task_cli,
        )
    except ImportError as e:
        print(f"Error: Could not import background_task_orchestrator: {e}")
        emit_action_receipt(
            "dispatch_task",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return 1

    if not args:
        print("Usage: dispatch_task <prompt> [--target=<target>] [--model=<model>] [--priority=<priority>]")
        print("\nTargets: ollama, lm_studio, chatdev, copilot, auto (default)")
        print("Copilot target uses AgentTaskRouter bridge mode (disabled/mock/live).")
        print("Priorities: low, normal (default), high, critical")
        print("\nExample:")
        print('  dispatch_task "Analyze this code for security issues" --target=ollama --model=qwen2.5-coder:14b')
        emit_action_receipt(
            "dispatch_task",
            exit_code=1,
            metadata={"error": "missing_prompt"},
        )
        return 1

    # Parse and validate arguments
    prompt, target, model, priority, task_type = _parse_dispatch_task_args(args)
    if not prompt:
        print("Error: No prompt provided")
        emit_action_receipt(
            "dispatch_task",
            exit_code=1,
            metadata={"error": "empty_prompt"},
        )
        return 1

    if target not in VALID_BACKGROUND_TARGETS:
        print(f"Error: Unsupported background target '{target}'")
        print(f"Supported targets: {', '.join(sorted(VALID_BACKGROUND_TARGETS))}")
        emit_action_receipt(
            "dispatch_task",
            exit_code=1,
            metadata={"error": "unsupported_target", "target": target},
        )
        return 1

    # Display configuration
    _print_dispatch_task_config(target, model, priority, task_type, prompt)

    # Execute async function
    try:
        result = asyncio.run(
            dispatch_task_cli(
                prompt=prompt,
                target=target,
                model=model,
                priority=priority,
                agent="claude",
                task_type=task_type,
            )
        )
        rc = _handle_dispatch_task_result(result)
        emit_action_receipt(
            "dispatch_task",
            exit_code=rc,
            metadata={
                "target": target,
                "model": model,
                "priority": priority,
                "task_type": task_type,
                "status": result.get("status"),
            },
        )
        return rc

    except Exception as e:
        print(f"Error dispatching task: {e}")
        logger.exception("Failed to dispatch task")
        emit_action_receipt(
            "dispatch_task",
            exit_code=1,
            metadata={"error": str(e), "target": target},
        )
        return 1


def handle_task_status(args: list[str]) -> int:
    """Check status of a background task.

    Usage:
        task_status <task_id>
    """
    try:
        from src.orchestration.background_task_orchestrator import task_status_cli
    except ImportError as e:
        print(f"Error: Could not import background_task_orchestrator: {e}")
        emit_action_receipt(
            "task_status",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return 1

    if not args:
        print("Usage: task_status <task_id>")
        emit_action_receipt(
            "task_status",
            exit_code=1,
            metadata={"error": "missing_task_id"},
        )
        return 1

    task_id = args[0]
    result = task_status_cli(task_id)
    error_message = result.get("error")
    normalized_status = str(result.get("status") or ("failed" if error_message else "unknown"))
    normalized = {
        **result,
        "status": normalized_status,
        "success": bool(
            result.get("success")
            if "success" in result
            else not error_message and normalized_status in {"queued", "running", "completed"}
        ),
        "audit_intelligence": _audit_intelligence(),
    }

    print(json.dumps(normalized, indent=2))

    if error_message:
        emit_action_receipt(
            "task_status",
            exit_code=1,
            metadata={"task_id": task_id, "error": error_message},
        )
        return 1
    emit_action_receipt(
        "task_status",
        exit_code=0,
        metadata={"task_id": task_id, "status": normalized_status},
    )
    return 0


def handle_list_background_tasks(args: list[str], json_mode: bool = False) -> int:
    """List background tasks.

    Usage:
        list_background_tasks [--status=<status>] [--limit=<n>]
    """
    try:
        from src.orchestration.background_task_orchestrator import list_tasks_cli
    except ImportError as e:
        print(f"Error: Could not import background_task_orchestrator: {e}")
        emit_action_receipt(
            "list_background_tasks",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return 1

    # Parse arguments
    json_requested = json_mode or "--json" in args
    parsed_args = [arg for arg in args if arg != "--json"]
    status = None
    limit = 20

    for arg in parsed_args:
        if arg.startswith("--status="):
            status = arg.split("=", 1)[1]
        elif arg.startswith("--limit="):
            try:
                limit = int(arg.split("=", 1)[1])
            except ValueError:
                limit = 20

    tasks = list_tasks_cli(status=status, limit=limit)
    payload = {
        "action": "list_background_tasks",
        "status": "ok",
        "count": len(tasks),
        "filter": status,
        "limit": limit,
        "tasks": tasks,
        "audit_intelligence": _audit_intelligence(),
    }

    if json_requested:
        print(json.dumps(payload, indent=2, default=str))
        emit_action_receipt(
            "list_background_tasks",
            exit_code=0,
            metadata={"count": len(tasks), "limit": limit, "filter": status, "json_mode": True},
        )
        return 0

    print(f"📋 Background Tasks ({len(tasks)} shown)")
    print("=" * 60)
    if not tasks:
        print("No tasks found.")
        emit_action_receipt(
            "list_background_tasks",
            exit_code=0,
            metadata={"status": "empty", "limit": limit, "filter": status},
        )
        return 0

    for task in tasks:
        status_emoji = {
            "queued": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🚫",
        }.get(task.get("status", ""), "❓")

        print(f"\n{status_emoji} {task['task_id']}")
        print(f"   Status: {task['status']} | Target: {task['target']} | Model: {task.get('model', 'N/A')}")
        print(f"   Agent: {task['requesting_agent']} | Created: {task['created_at']}")
        if task.get("prompt"):
            print(f"   Prompt: {task['prompt'][:80]}...")

    emit_action_receipt(
        "list_background_tasks",
        exit_code=0,
        metadata={"count": len(tasks), "limit": limit, "filter": status},
    )
    return 0


def handle_orchestrator_status() -> int:
    """Show orchestrator status and available backends.

    Usage:
        orchestrator_status
    """
    try:
        from src.orchestration.background_task_orchestrator import orchestrator_status_cli
    except ImportError as e:
        print(f"Error: Could not import background_task_orchestrator: {e}")
        emit_action_receipt(
            "orchestrator_status",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return 1

    status = orchestrator_status_cli()

    print("🎭 Background Task Orchestrator Status")
    print("=" * 60)
    print(f"\nTotal Tasks: {status['total_tasks']}")
    print("\nStatus Breakdown:")
    for s, count in status.get("status_counts", {}).items():
        print(f"  {s}: {count}")

    print("\n📡 Available Targets:")

    targets = status.get("targets", {})

    # Ollama
    ollama = targets.get("ollama", {})
    print(f"\n  🦙 Ollama ({ollama.get('url', 'N/A')})")
    if ollama.get("available_models"):
        print(f"     Models: {', '.join(ollama['available_models'][:5])}")

    # LM Studio
    lm_studio = targets.get("lm_studio", {})
    print(f"\n  🖥️  LM Studio ({lm_studio.get('url', 'N/A')})")

    # ChatDev
    chatdev = targets.get("chatdev", {})
    print(f"\n  👥 ChatDev: {'Available' if chatdev.get('available') else 'Not configured'}")

    # Copilot
    copilot = targets.get("copilot", {})
    bridge_mode = copilot.get("bridge_mode", "disabled")
    endpoint = copilot.get("endpoint", "")
    endpoint_display = endpoint if endpoint else "(not configured)"
    print(f"\n  🧩 Copilot: Available (bridge_mode={bridge_mode})")
    print(f"     Endpoint: {endpoint_display}")

    print(f"\n🔄 Worker Running: {status.get('worker_running', False)}")
    print("\n📚 Audit Intelligence")
    for line in format_audit_intelligence_lines(_audit_intelligence(), max_lines=4):
        print(f"  - {line}")

    emit_action_receipt(
        "orchestrator_status",
        exit_code=0,
        metadata={"total_tasks": status.get("total_tasks")},
    )
    return 0


def _parse_int_flag(args: list[str], prefix: str, default: int) -> int:
    for arg in args:
        if arg.startswith(prefix):
            raw = arg.split("=", 1)[1]
            return int(raw)
    return default


def handle_orchestrator_hygiene(args: list[str]) -> int:
    """Prune/reconcile background task history and stale running entries.

    Usage:
        orchestrator_hygiene [--dry-run]
            [--keep-completed=<n>] [--keep-failed=<n>] [--keep-cancelled=<n>]
            [--stale-running-after-s=<seconds>]
    """
    try:
        from src.orchestration.background_task_orchestrator import orchestrator_hygiene_cli
    except ImportError as e:
        print(f"Error: Could not import background_task_orchestrator: {e}")
        emit_action_receipt(
            "orchestrator_hygiene",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return 1

    dry_run = "--dry-run" in args

    try:
        keep_completed = _parse_int_flag(args, "--keep-completed=", 250)
        keep_failed = _parse_int_flag(args, "--keep-failed=", 200)
        keep_cancelled = _parse_int_flag(args, "--keep-cancelled=", 200)
        stale_running_after_s = _parse_int_flag(args, "--stale-running-after-s=", 3600)
    except ValueError as exc:
        print(f"Error: Invalid numeric argument ({exc})")
        emit_action_receipt(
            "orchestrator_hygiene",
            exit_code=1,
            metadata={"error": str(exc)},
        )
        return 1

    result = orchestrator_hygiene_cli(
        keep_completed=keep_completed,
        keep_failed=keep_failed,
        keep_cancelled=keep_cancelled,
        stale_running_after_s=stale_running_after_s,
        dry_run=dry_run,
    )

    print("🧹 Orchestrator Hygiene")
    print("=" * 60)
    print(f"Dry run: {result.get('dry_run')}")
    print(f"Tasks: {result.get('before_total')} -> {result.get('after_total')}")
    print(f"Removed total: {result.get('removed_total')}")
    print(f"Running reconciled: {result.get('running_reconciled')}")
    removed_by_status = result.get("removed_by_status", {})
    for status_name in ("completed", "failed", "cancelled"):
        print(f"  {status_name}: {removed_by_status.get(status_name, 0)} removed")

    emit_action_receipt(
        "orchestrator_hygiene",
        exit_code=0,
        metadata={
            "dry_run": result.get("dry_run"),
            "removed_total": result.get("removed_total"),
        },
    )
    return 0
