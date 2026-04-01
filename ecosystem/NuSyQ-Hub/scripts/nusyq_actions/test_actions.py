"""Action module: test execution and history tracking."""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

from scripts.nusyq_actions.shared import emit_action_receipt


def handle_test(paths, run, run_fast_test_suite: Callable) -> int:
    """Run pytest with intelligent timeout management and duplicate detection.

    Default behavior: run a fast subset to avoid heavy optional deps unless
    explicitly overridden with NUSYQ_FAST_TEST_MODE=0.
    """
    print("🧪 Running pytest (quick mode)...")
    fast_env = os.getenv("NUSYQ_FAST_TEST_MODE")
    # Default to fast mode unless explicitly disabled
    fast_mode = True if fast_env is None else fast_env == "1"
    timeout_s = 120
    timeout_override = os.getenv("START_NUSYQ_TEST_TIMEOUT")
    if timeout_override:
        try:
            timeout_s = int(timeout_override)
        except ValueError:
            pass
    timeout_manager = None
    record_completion = None

    try:
        from src.utils.intelligent_timeout_manager import (
            get_intelligent_timeout_manager,
            record_service_completion,
        )

        timeout_manager = get_intelligent_timeout_manager()
        timeout_s = timeout_manager.get_timeout("pytest", complexity=1.2, priority="high", update_load=True)
        record_completion = record_service_completion
    except Exception:
        timeout_manager = None
        record_completion = None

    start_time = time.time()
    cmd = None  # populated for logging below
    if fast_mode:
        # Mirror the fast suite execution signature and provide a readable command placeholder
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--fast-suite",
        ]
        rc, out, err = run_fast_test_suite(paths, timeout_s=min(timeout_s, 60))
    else:
        cmd = [sys.executable, "-m", "pytest", "tests", "-q", "--capture=no"]
        rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=timeout_s)
    duration = time.time() - start_time
    if not fast_mode and "TimeoutExpired" in err and timeout_manager is not None:
        weights = timeout_manager.service_weights.get("pytest")
        max_timeout = weights.max_timeout if weights else max(int(timeout_s * 2), timeout_s)
        bumped_timeout = min(int(timeout_s * 1.5), max_timeout)
        timeout_manager.adjust_service_weight("pytest", base_timeout=bumped_timeout)
        print(f"⏱️ Pytest timed out at {timeout_s}s; retrying with {bumped_timeout}s...")
        start_time = time.time()
        rc, out, err = run(cmd, cwd=paths.nusyq_hub, timeout_s=bumped_timeout)
        duration = time.time() - start_time
        timeout_s = bumped_timeout

    if record_completion is not None and duration > 0 and rc == 0:
        try:
            record_completion("pytest", duration)
        except Exception:
            pass
    if out:
        print(out)
    if err:
        print(f"[STDERR]\n{err}", file=sys.stderr)
    try:
        from src.utils.terminal_output import to_tests
        from src.utils.test_run_registry import record_test_run

        summary = record_test_run(
            command=cmd or ["<fast-suite>"],
            cwd=str(paths.nusyq_hub) if paths.nusyq_hub else str(Path.cwd()),
            status="pass" if rc == 0 else "fail",
            exit_code=rc,
            duration_seconds=duration,
            source="start_nusyq:test",
        )
        duplicate_note = ""
        if summary.run_count_window > 1:
            duplicate_note = f" (run {summary.run_count_window}x in window)"
        to_tests(
            f"Test run {summary.run_id} status={summary.status} duration={summary.duration_seconds}s{duplicate_note}"
        )
        _maybe_create_test_failure_quest_impl(paths, summary, out, err)
    except Exception:
        pass
    emit_action_receipt(
        "test",
        exit_code=rc,
        metadata={
            "fast_mode": fast_mode,
            "timeout_s": timeout_s,
            "duration_s": round(duration, 2),
        },
    )
    return rc


def handle_test_history(args: list[str], paths) -> int:
    """Show recent test run history."""
    limit = 10
    if len(args) > 1 and args[1].isdigit():
        limit = max(1, int(args[1]))

    if paths.nusyq_hub:
        registry_path = paths.nusyq_hub / "state" / "reports" / "test_runs.json"
    else:
        registry_path = Path("state") / "reports" / "test_runs.json"

    if not registry_path.exists():
        print(f"[INFO] No test run registry found at {registry_path}")
        emit_action_receipt(
            "test_history",
            exit_code=0,
            metadata={"status": "missing_registry", "path": str(registry_path)},
        )
        return 0

    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[ERROR] Failed to read registry: {exc}")
        emit_action_receipt(
            "test_history",
            exit_code=1,
            metadata={"error": str(exc), "path": str(registry_path)},
        )
        return 1

    runs = data.get("runs", [])
    runs = sorted(runs, key=lambda r: r.get("timestamp", ""), reverse=True)
    recent = runs[:limit]

    print("🧪 Test Run History")
    print("=" * 60)
    print(f"Registry: {registry_path}")
    print(f"Total runs tracked: {len(runs)}")
    print(f"Showing last {len(recent)}")

    for run in recent:
        status = run.get("status", "unknown")
        cmd = " ".join(run.get("command", []))
        run_count = run.get("run_count_window", 1)
        duplicate_of = run.get("duplicate_of")
        dupe_note = f" (dup of {duplicate_of})" if duplicate_of else ""
        print(
            f"- {run.get('timestamp')} | {status.upper()} | "
            f"{run.get('duration_seconds')}s | "
            f"window x{run_count}{dupe_note}\n"
            f"  {cmd}"
        )

    emit_action_receipt(
        "test_history",
        exit_code=0,
        metadata={"shown": len(recent), "total_runs": len(runs)},
    )
    return 0


def _maybe_create_test_failure_quest_impl(paths, summary, out: str, err: str) -> None:
    """Create a guild quest for recurring test failures."""
    if summary.status == "pass":
        return
    if summary.run_count_window < 3:
        return
    if not paths.nusyq_hub:
        return

    title = "Investigate recurring test failures"
    detail = err or out
    detail_line = detail.splitlines()[0] if detail else "No output captured"
    description = (
        f"Test command repeated {summary.run_count_window}x recently. "
        f"Last exit code: {summary.exit_code}. "
        f"First line: {detail_line[:160]}. "
        "See state/reports/test_runs.json for run history."
    )
    tags = ["tests", "stability", "triage"]

    try:
        from src.guild.guild_board import QuestState, get_board

        board = _run_guild_impl(get_board())
        for quest in board.board.quests.values():
            if (
                quest.state
                in {
                    QuestState.OPEN,
                    QuestState.CLAIMED,
                    QuestState.ACTIVE,
                    QuestState.BLOCKED,
                }
                and title.lower() in quest.title.lower()
            ):
                return
    except Exception:
        pass

    try:
        from src.guild.guild_cli import board_add_quest

        _run_guild_impl(
            board_add_quest(
                "system",
                title,
                description,
                priority=4,
                safety_tier="standard",
                tags=tags,
            )
        )
    except Exception:
        pass


def _run_guild_impl(fn: Callable):
    """Stub for guild board operations - minimal signature."""
    return fn() if callable(fn) else fn
