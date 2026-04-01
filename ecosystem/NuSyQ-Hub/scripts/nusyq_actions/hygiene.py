"""Action module: hygiene checks and automation."""

from __future__ import annotations

import os
from collections.abc import Callable

from scripts.nusyq_actions.shared import emit_action_receipt


def handle_hygiene(
    paths,
    check_spine_hygiene: Callable,
    run_aux_script: Callable,
    _run_cmd: Callable,
    fast: bool = False,
) -> int:
    """Run spine hygiene checks with optional automation."""
    if os.getenv("NUSYQ_FAST_TEST_MODE") == "1":
        print("✅ Spine hygiene: CLEAN (fast test mode)")
        print("✅ AI systems: Available (mocked)")
        emit_action_receipt(
            "hygiene",
            exit_code=0,
            metadata={"mode": "fast", "reason": "NUSYQ_FAST_TEST_MODE"},
        )
        return 0

    warnings = check_spine_hygiene(paths.nusyq_hub, fast=fast)
    for warning in warnings:
        print(warning)

    # Check spine registry health
    try:
        from src.spine import get_spine

        spine = get_spine()
        health = spine.health_check()

        print("\n🧬 Spine Registry Health:")
        print(f"   Total modules: {health['total_modules']}")
        print(f"   Spine-wired: {health['wired_modules']}")
        print(f"   Loaded services: {health['loaded_services']}")

        if health["missing_dependencies"]:
            print("   ⚠️  Missing dependencies detected:")
            for module, deps in health["missing_dependencies"].items():
                print(f"      {module}: {', '.join(deps)}")
        else:
            print("   ✅ All dependencies valid")

        if not health["healthy"]:
            print("   ⚠️  Spine health check failed")
    except Exception as e:
        print(f"\n⚠️  Spine registry check failed: {e}")

    # Skip AI health check - not critical for hygiene, can hang
    print("\n✅ AI health check skipped (use 'doctor' for AI diagnostics)")

    if fast:
        print("\n⚡ Fast hygiene mode: automation skipped")
        print("   Run 'python scripts/start_nusyq.py hygiene' for full cleanup")
        emit_action_receipt(
            "hygiene",
            exit_code=0,
            metadata={"mode": "fast", "automation": "skipped"},
        )
        return 0

    print("\n🔄 Automation & Normalization (Full Mode)")
    run_aux_script(
        paths,
        "scripts/normalize_broken_paths.py",
        "Path normalization",
        timeout_s=120,
    )
    run_aux_script(
        paths,
        "scripts/todo_to_issue.py",
        "TODO→Issue automation",
        args=["--limit", "10"],
        timeout_s=120,
    )
    run_aux_script(
        paths,
        "scripts/execute_remaining_pus.py",
        "PU automation",
        timeout_s=90,
    )
    emit_action_receipt(
        "hygiene",
        exit_code=0,
        metadata={"mode": "full", "automation": "completed"},
    )
    return 0
