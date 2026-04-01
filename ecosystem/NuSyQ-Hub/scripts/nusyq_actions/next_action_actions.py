"""Next-action related handlers extracted from the spine.

These functions operate with a minimal dependency surface and only assume
`paths` has a `.nusyq_hub` attribute pointing to the NuSyQ-Hub repo root.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from scripts.nusyq_actions.shared import emit_action_receipt


def _run(cmd: list[str], cwd: Path | None = None, timeout_s: int = 10) -> tuple[int, str, str]:
    """Run a subprocess command and return (code, stdout, stderr)."""
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"


def handle_next_action_generation(paths, json_mode: bool = False) -> int:
    """Generate next-action queue from current intelligence signals."""
    if not json_mode:
        print("🎯 Generating next-action queue...")

    hub = getattr(paths, "nusyq_hub", None)
    if not hub:
        print("[WARNING] NuSyQ-Hub path not found; skipping action generation.")
        emit_action_receipt(
            "next_action_generate",
            exit_code=0,
            metadata={"status": "skipped", "reason": "missing_hub_path"},
        )
        return 0

    try:
        sys.path.insert(0, str(hub / "src" / "tools"))
        from perpetual_action_generator import ActionGenerator  # type: ignore

        generator = ActionGenerator(hub)
        actions = generator.generate_actions()
        _ = generator.save_action_queue(actions)

        payload = {
            "action": "next_action_generate",
            "status": "ok",
            "generated_at": datetime.now().isoformat(),
            "generated_count": len(actions),
        }
        if actions:
            top = actions[0]
            payload["top"] = {
                "title": getattr(top, "title", str(top)),
                "priority": getattr(getattr(top, "priority", None), "name", "unknown"),
            }

        if json_mode:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"   ✅ Generated {len(actions)} next actions")
            if "top" in payload:
                print(f"   📌 Top priority: {payload['top']['title']} ({payload['top']['priority']})")
        emit_action_receipt(
            "next_action_generate",
            exit_code=0,
            metadata={"generated_count": len(actions)},
        )
        return 0
    except Exception as e:
        if json_mode:
            print(
                json.dumps(
                    {
                        "action": "next_action_generate",
                        "status": "error",
                        "generated_at": datetime.now().isoformat(),
                        "error": str(e),
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(f"   ⚠️  Action generation failed: {e}")
        emit_action_receipt(
            "next_action_generate",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return 1


def handle_next_action_display(paths, json_mode: bool = False) -> int:
    """Display the current next-action queue."""
    if not json_mode:
        print("🎯 Next Action Queue")
        print("=" * 70)

    hub = getattr(paths, "nusyq_hub", None)
    if not hub:
        print("[ERROR] NuSyQ-Hub path not found")
        emit_action_receipt(
            "next_action_display",
            exit_code=1,
            metadata={"error": "missing_hub_path"},
        )
        return 1

    try:
        cmd = [sys.executable, "src/tools/next_action_display.py"]
        if json_mode:
            cmd.append("--json")
        rc, out, err = _run(cmd, cwd=hub, timeout_s=10)
        if json_mode:
            queue_payload: dict | list | str | None
            try:
                queue_payload = json.loads(out) if out else None
            except json.JSONDecodeError:
                queue_payload = out or err
            print(
                json.dumps(
                    {
                        "action": "next_action",
                        "status": "ok" if rc == 0 else "error",
                        "generated_at": datetime.now().isoformat(),
                        "queue": queue_payload,
                        "stderr": err,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            emit_action_receipt(
                "next_action_display",
                exit_code=rc,
                metadata={"json_mode": True},
            )
            return rc
        if out:
            print(out)
        emit_action_receipt(
            "next_action_display",
            exit_code=rc,
            metadata={"json_mode": False},
        )
        return rc
    except TimeoutError:
        print("⚠️  Action display timed out")
        emit_action_receipt(
            "next_action_display",
            exit_code=1,
            metadata={"error": "timeout"},
        )
        return 1


def handle_next_action_generate(paths, json_mode: bool = False) -> int:
    """Generate a fresh next-action queue (alias to generation)."""
    return handle_next_action_generation(paths, json_mode=json_mode)


def handle_next_action_exec(args: list[str], paths) -> int:
    """Execute an action by type using the display tool's --execute."""
    if len(args) < 2:
        print("Usage: next_action_exec <action_type>")
        print(
            "Available types: validate_module, expand_coverage, resolve_quest, heal_repository, scale_orchestration, integrate_cross_repo"
        )
        emit_action_receipt(
            "next_action_exec",
            exit_code=1,
            metadata={"error": "missing_action_type"},
        )
        return 1

    action_type = args[1]

    hub = getattr(paths, "nusyq_hub", None)
    if not hub:
        print("[ERROR] NuSyQ-Hub path not found")
        emit_action_receipt(
            "next_action_exec",
            exit_code=1,
            metadata={"error": "missing_hub_path", "action_type": action_type},
        )
        return 1

    try:
        cmd = [sys.executable, "src/tools/next_action_display.py", f"--execute={action_type}"]
        rc, out, _ = _run(cmd, cwd=hub, timeout_s=300)
        if out:
            print(out)
        emit_action_receipt(
            "next_action_exec",
            exit_code=rc,
            metadata={"action_type": action_type},
        )
        return rc
    except TimeoutError:
        print("⚠️  Action execution timed out")
        emit_action_receipt(
            "next_action_exec",
            exit_code=1,
            metadata={"action_type": action_type, "error": "timeout"},
        )
        return 1
