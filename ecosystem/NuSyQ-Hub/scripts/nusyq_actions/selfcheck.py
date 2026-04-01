"""Action module: selfcheck diagnostics."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from scripts.nusyq_actions.shared import emit_action_receipt


def handle_selfcheck(paths, run_cmd) -> int:
    """Run self-check, optionally skipping heavy checks."""
    if os.getenv("NUSYQ_FAST_TEST_MODE") == "1":
        print("✅ Selfcheck: OK (fast test mode)")
        emit_action_receipt(
            "selfcheck",
            exit_code=0,
            metadata={"mode": "fast", "reason": "NUSYQ_FAST_TEST_MODE"},
        )
        return 0

    if os.getenv("NUSYQ_NO_SELF_CHECK") == "1":
        print("Selfcheck disabled by NUSYQ_NO_SELF_CHECK=1")
        emit_action_receipt(
            "selfcheck",
            exit_code=0,
            metadata={"mode": "skipped", "reason": "NUSYQ_NO_SELF_CHECK"},
        )
        return 0

    # 1) VS Code diagnostics bridge
    python_exe = getattr(paths, "python", sys.executable)
    run_cmd([python_exe, "scripts/start_nusyq.py", "vscode_diagnostics_bridge"])

    # 2) Quick lint/test check (diagnostic mode)
    run_cmd([python_exe, "scripts/lint_test_check.py", "--mode", "diagnostic"])

    # 3) Print last quest state if available
    repo_root = getattr(paths, "nusyq_root", None) or getattr(paths, "nusyq_hub", None) or Path.cwd()
    quest_log = Path(repo_root) / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    if quest_log.exists():
        try:
            with quest_log.open("r", encoding="utf-8") as f:
                last = f.readlines()[-1].strip()
            data = json.loads(last)
            print("\n📜 Last quest entry:")
            print(json.dumps(data, indent=2))
        except Exception as exc:
            print(f"⚠️  Unable to read quest log: {exc}")

    print("\n✅ Selfcheck complete")
    emit_action_receipt(
        "selfcheck",
        exit_code=0,
        metadata={"mode": "full"},
    )
    return 0
