"""Action module: doctor diagnostics suite."""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.nusyq_actions.shared import emit_action_receipt
from scripts.nusyq_actions.work_task_actions import collect_quest_signal


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _resolve_report_dir(hub_path: Any) -> Path:
    base = Path(hub_path) if hub_path else Path(".")
    report_dir = base / "state" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def _write_json_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for raw in handle:
                line = raw.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
    except OSError:
        return []
    if limit <= 0:
        return rows
    return rows[-limit:]


def _retention_count(env_name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(env_name, str(default)) or default))
    except ValueError:
        return max(1, default)


def _prune_report_history(
    report_dir: Path,
    pattern: str,
    keep_count: int,
    protected_names: set[str] | None = None,
) -> None:
    if keep_count <= 0:
        return
    protected = set(protected_names or set())
    files = sorted(
        report_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
        reverse=True,
    )
    for stale in files[keep_count:]:
        if stale.name in protected:
            continue
        try:
            stale.unlink()
        except OSError:
            continue


def _build_doctor_dashboard(history: list[dict[str, Any]], latest: dict[str, Any]) -> dict[str, Any]:
    by_step: dict[str, dict[str, Any]] = {}
    for run_entry in history:
        steps = run_entry.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            name = str(step.get("name") or "").strip()
            if not name:
                continue
            passed = bool(step.get("passed"))
            stats = by_step.setdefault(
                name,
                {"name": name, "runs": 0, "passed": 0, "failed": 0, "recent": []},
            )
            stats["runs"] += 1
            if passed:
                stats["passed"] += 1
            else:
                stats["failed"] += 1
            stats["recent"].append("PASS" if passed else "FAIL")

    trends: list[dict[str, Any]] = []
    for name, stats in sorted(by_step.items()):
        runs = int(stats["runs"])
        passed = int(stats["passed"])
        recent = stats["recent"][-10:]
        trends.append(
            {
                "name": name,
                "runs": runs,
                "passed": passed,
                "failed": int(stats["failed"]),
                "pass_rate": round(passed / runs, 4) if runs else 0.0,
                "recent": recent,
                "last_status": recent[-1] if recent else "UNKNOWN",
            }
        )

    return {
        "action": "doctor_dashboard",
        "generated_at": datetime.now().isoformat(),
        "history_runs": len(history),
        "latest": {
            "generated_at": latest.get("generated_at"),
            "status": latest.get("status"),
            "passed_steps": latest.get("passed_steps"),
            "total_steps": latest.get("total_steps"),
            "healing_validation": latest.get("healing_validation"),
        },
        "per_step_trends": trends,
    }


@dataclass(frozen=True)
class DoctorOptions:
    quick: bool = False
    include_system_health: bool = True
    include_lint: bool = True
    include_analyzer: bool = True
    budget_s: int = 0
    auto_heal: bool = False


def _parse_doctor_args(action_args: list[str] | None) -> DoctorOptions:
    tokens = [token.strip() for token in (action_args or []) if isinstance(token, str)]
    if tokens and tokens[0] == "doctor":
        tokens = tokens[1:]

    quick = "--quick" in tokens or "--fast" in tokens
    include_system_health = not quick
    include_lint = not quick
    include_analyzer = not quick

    if "--with-system-health" in tokens:
        include_system_health = True
    if "--with-lint" in tokens:
        include_lint = True
    if "--with-analyzer" in tokens:
        include_analyzer = True
    if "--skip-system-health" in tokens:
        include_system_health = False
    if "--skip-lint" in tokens:
        include_lint = False
    if "--skip-analyzer" in tokens:
        include_analyzer = False

    budget_s = int(os.getenv("NUSYQ_DOCTOR_BUDGET_S", "0") or 0)
    for index, token in enumerate(tokens):
        if token.startswith("--budget-s="):
            try:
                budget_s = max(0, int(token.split("=", 1)[1]))
            except ValueError:
                pass
            continue
        if token == "--budget-s" and index + 1 < len(tokens):
            try:
                budget_s = max(0, int(tokens[index + 1]))
            except ValueError:
                pass

    auto_heal = "--auto-heal" in tokens or "--heal" in tokens

    return DoctorOptions(
        quick=quick,
        include_system_health=include_system_health,
        include_lint=include_lint,
        include_analyzer=include_analyzer,
        budget_s=budget_s,
        auto_heal=auto_heal,
    )


def _emit_progress(message: str, *, json_mode: bool) -> None:
    if json_mode:
        print(f"[doctor] {message}", file=sys.stderr, flush=True)
    else:
        print(message, flush=True)


def handle_doctor(
    paths: Any,
    run_cmd: Callable[..., tuple[int, str, str]],
    health_filename: str,
    json_mode: bool = False,
    action_args: list[str] | None = None,
) -> int:
    """Run doctor diagnostics, skipping heavy checks when env opts out."""
    steps: list[dict[str, Any]] = []
    hub_path = getattr(paths, "nusyq_hub", None)
    options = _parse_doctor_args(action_args)
    run_started = time.time()
    report_dir = _resolve_report_dir(hub_path)
    checkpoint_stamp = _now_stamp()
    checkpoint_path = report_dir / f"doctor_checkpoint_{checkpoint_stamp}.json"
    checkpoint_latest_path = report_dir / "doctor_checkpoint_latest.json"
    checkpoint: dict[str, Any] = {
        "action": "doctor_checkpoint",
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "total_planned": 3,
        "completed_checks": 0,
        "current_check": None,
        "options": {
            "quick": options.quick,
            "include_system_health": options.include_system_health,
            "include_lint": options.include_lint,
            "include_analyzer": options.include_analyzer,
            "budget_s": options.budget_s,
        },
        "checks": [],
    }

    def _write_checkpoint() -> None:
        checkpoint["updated_at"] = datetime.now().isoformat()
        checks = checkpoint.get("checks", [])
        checkpoint["completed_checks"] = len(checks) if isinstance(checks, list) else 0
        _write_json_report(checkpoint_path, checkpoint)
        _write_json_report(checkpoint_latest_path, checkpoint)

    def _remaining_budget_s() -> int | None:
        if options.budget_s <= 0:
            return None
        elapsed = int(time.time() - run_started)
        return max(0, options.budget_s - elapsed)

    def _append_step(entry: dict[str, Any]) -> None:
        steps.append(entry)
        checks = checkpoint.setdefault("checks", [])
        if isinstance(checks, list):
            checks.append(entry)
        checkpoint["current_check"] = entry.get("name")
        _write_checkpoint()

    def _run(cmd: list[str], timeout_s: int) -> tuple[int, str, str]:
        """Run diagnostic command with explicit timeout and cwd when supported."""
        try:
            return run_cmd(cmd, cwd=hub_path, timeout_s=timeout_s)
        except TypeError:
            # Backward compatibility for simpler stubs.
            return run_cmd(cmd)

    def _pick_system_health_cmd() -> list[str] | None:
        """Resolve the best available system-health command in current workspace."""
        if not hub_path:
            return None
        hub = Path(hub_path)
        candidates: list[list[str]] = [
            [sys.executable, "scripts/system_health.py", "--output", health_filename],
            [sys.executable, "scripts/health_check.py"],
            [sys.executable, "src/diagnostics/system_health_assessor.py"],
        ]
        for cmd in candidates:
            script = hub / cmd[1]
            if script.exists():
                return cmd
        return None

    if os.getenv("NUSYQ_NO_DOCTOR") == "1":
        skipped_payload: dict[str, Any] = {
            "action": "doctor",
            "status": "skipped",
            "reason": "NUSYQ_NO_DOCTOR=1",
            "generated_at": datetime.now().isoformat(),
            "steps": [],
        }
        print(json.dumps(skipped_payload, indent=2) if json_mode else "Doctor disabled by NUSYQ_NO_DOCTOR=1")
        return 0

    _emit_progress(
        f"Mode={'quick' if options.quick else 'full'} | "
        f"system_health={'on' if options.include_system_health else 'off'} | "
        f"lint={'on' if options.include_lint else 'off'} | "
        f"analyzer={'on' if options.include_analyzer else 'off'} | "
        f"budget_s={options.budget_s if options.budget_s > 0 else 'none'}",
        json_mode=json_mode,
    )
    _write_checkpoint()

    # Allow skipping the slow system health.
    if options.include_system_health and os.getenv("NUSYQ_NO_SYSTEM_HEALTH") != "1":
        health_cmd = _pick_system_health_cmd()
        if health_cmd:
            remaining = _remaining_budget_s()
            if remaining is not None and remaining <= 0:
                _append_step(
                    {
                        "name": "system_health",
                        "rc": 124,
                        "passed": False,
                        "skipped": True,
                        "reason": "budget_exceeded",
                        "cmd": health_cmd,
                    }
                )
            else:
                timeout = int(os.getenv("NUSYQ_DOCTOR_SYSTEM_HEALTH_TIMEOUT_S", "45"))
                effective_timeout = timeout if remaining is None else max(1, min(timeout, remaining))
                _emit_progress(
                    f"Running system_health ({' '.join(health_cmd)}) timeout={effective_timeout}s...",
                    json_mode=json_mode,
                )
                started = time.time()
                rc, out, err = _run(health_cmd, timeout_s=effective_timeout)
                elapsed = round(time.time() - started, 2)
                _emit_progress(
                    f"system_health {'PASS' if rc == 0 else 'FAIL'} in {elapsed}s",
                    json_mode=json_mode,
                )
                step = {
                    "name": "system_health",
                    "rc": rc,
                    "passed": rc == 0,
                    "cmd": health_cmd,
                    "timeout_s": effective_timeout,
                    "elapsed_s": elapsed,
                    "stdout_tail": "\n".join(out.splitlines()[-10:]) if out else "",
                    "stderr_tail": "\n".join(err.splitlines()[-10:]) if err else "",
                }
                budget_remaining = _remaining_budget_s()
                if budget_remaining is not None:
                    step["budget_remaining_s"] = budget_remaining
                _append_step(step)
        else:
            _append_step(
                {
                    "name": "system_health",
                    "rc": 0,
                    "passed": True,
                    "skipped": True,
                    "reason": "No system health script found",
                }
            )
    elif not options.include_system_health:
        _append_step(
            {
                "name": "system_health",
                "rc": 0,
                "passed": True,
                "skipped": True,
                "reason": "quick mode (use --with-system-health to include)",
            }
        )
    else:
        _append_step(
            {
                "name": "system_health",
                "rc": 0,
                "passed": True,
                "skipped": True,
                "reason": "NUSYQ_NO_SYSTEM_HEALTH=1",
            }
        )

    # Always run the fast diagnostics below.
    quick_timeout_default = "15" if options.quick else "90"
    diagnostic_steps: list[tuple[str, list[str], int]] = []
    if options.include_analyzer:
        diagnostic_steps.append(
            (
                "quick_system_analyzer",
                [sys.executable, "src/diagnostics/quick_system_analyzer.py"],
                int(os.getenv("NUSYQ_DOCTOR_QUICK_ANALYZER_TIMEOUT_S", quick_timeout_default)),
            )
        )
    else:
        _append_step(
            {
                "name": "quick_system_analyzer",
                "rc": 0,
                "passed": True,
                "skipped": True,
                "reason": "quick mode (use --with-analyzer to include)",
            }
        )

    if options.include_lint:
        diagnostic_steps.append(
            (
                "lint_test_diagnostic",
                [sys.executable, "scripts/lint_test_check.py", "--mode", "diagnostic"],
                int(os.getenv("NUSYQ_DOCTOR_LINT_TIMEOUT_S", "180")),
            )
        )
    else:
        _append_step(
            {
                "name": "lint_test_diagnostic",
                "rc": 0,
                "passed": True,
                "skipped": True,
                "reason": "quick mode (use --with-lint to include)",
            }
        )

    for name, cmd, timeout in diagnostic_steps:
        remaining = _remaining_budget_s()
        if remaining is not None and remaining <= 0:
            _append_step(
                {
                    "name": name,
                    "rc": 124,
                    "passed": False,
                    "skipped": True,
                    "reason": "budget_exceeded",
                    "cmd": cmd,
                }
            )
            continue
        effective_timeout = timeout if remaining is None else max(1, min(timeout, remaining))
        _emit_progress(f"Running {name} timeout={effective_timeout}s...", json_mode=json_mode)
        started = time.time()
        rc, out, err = _run(cmd, timeout_s=effective_timeout)
        elapsed = round(time.time() - started, 2)
        _emit_progress(
            f"{name} {'PASS' if rc == 0 else 'FAIL'} in {elapsed}s",
            json_mode=json_mode,
        )
        step = {
            "name": name,
            "rc": rc,
            "passed": rc == 0,
            "cmd": cmd,
            "timeout_s": effective_timeout,
            "elapsed_s": elapsed,
            "stdout_tail": "\n".join(out.splitlines()[-10:]) if out else "",
            "stderr_tail": "\n".join(err.splitlines()[-10:]) if err else "",
        }
        budget_remaining = _remaining_budget_s()
        if budget_remaining is not None:
            step["budget_remaining_s"] = budget_remaining
        _append_step(step)

    passed_steps = sum(1 for step in steps if step.get("passed"))
    total_steps = len(steps)
    failed_steps = [s for s in steps if not s.get("passed") and not s.get("skipped")]
    healing_validation: dict[str, Any] | None = None

    # Generate healing suggestions for failed checks
    healing_suggestions = []
    if failed_steps:
        healing_suggestions.append(
            {
                "command": "python scripts/start_nusyq.py heal",
                "description": "Run comprehensive system healing (RepositoryHealthRestorer)",
                "issues_addressed": len(failed_steps),
                "auto_fixable": True,
            }
        )
        # Add specific suggestions based on failure types
        if any("lint" in s.get("name", "") for s in failed_steps):
            healing_suggestions.append(
                {
                    "command": "ruff check src/ scripts/ --fix",
                    "description": "Auto-fix lint issues",
                    "auto_fixable": True,
                }
            )
        if any("import" in str(s.get("stderr_tail", "")).lower() for s in failed_steps):
            healing_suggestions.append(
                {
                    "command": "python src/utils/quick_import_fix.py",
                    "description": "Fix import errors",
                    "auto_fixable": True,
                }
            )

    quest_signal = collect_quest_signal(Path(hub_path) if hub_path else None)
    payload: dict[str, Any] = {
        "action": "doctor",
        "status": "ok" if passed_steps == total_steps else "degraded",
        "generated_at": datetime.now().isoformat(),
        "mode": "quick" if options.quick else "full",
        "options": {
            "include_system_health": options.include_system_health,
            "include_lint": options.include_lint,
            "include_analyzer": options.include_analyzer,
            "budget_s": options.budget_s,
            "auto_heal": options.auto_heal,
        },
        "passed_steps": passed_steps,
        "total_steps": total_steps,
        "failed_steps": len(failed_steps),
        "healing_suggestions": healing_suggestions,
        "healing_validation": healing_validation,
        "quest_signal": quest_signal,
        "steps": steps,
    }
    report_path = report_dir / f"doctor_report_{_now_stamp()}.json"
    latest_report_path = report_dir / "doctor_report_latest.json"
    history_path = report_dir / "doctor_history.jsonl"
    dashboard_path = report_dir / f"doctor_dashboard_{_now_stamp()}.json"
    dashboard_latest_path = report_dir / "doctor_dashboard_latest.json"
    _write_json_report(report_path, payload)
    _write_json_report(latest_report_path, payload)
    _append_jsonl(history_path, payload)
    history = _read_jsonl(history_path, limit=200)
    dashboard = _build_doctor_dashboard(history, payload)
    _write_json_report(dashboard_path, dashboard)
    _write_json_report(dashboard_latest_path, dashboard)
    payload["history_file"] = str(history_path)
    payload["dashboard_file"] = str(dashboard_latest_path)
    payload["checkpoint_file"] = str(checkpoint_latest_path)
    _write_json_report(latest_report_path, payload)
    checkpoint["status"] = "completed" if passed_steps == total_steps else "degraded"
    checkpoint["finished_at"] = datetime.now().isoformat()
    checkpoint["report_file"] = str(latest_report_path)
    _write_checkpoint()

    _prune_report_history(
        report_dir,
        pattern="doctor_checkpoint_*.json",
        keep_count=_retention_count("NUSYQ_DOCTOR_CHECKPOINT_HISTORY_KEEP", 20),
        protected_names={"doctor_checkpoint_latest.json"},
    )
    _prune_report_history(
        report_dir,
        pattern="doctor_report_*.json",
        keep_count=_retention_count("NUSYQ_DOCTOR_REPORT_HISTORY_KEEP", 20),
        protected_names={"doctor_report_latest.json"},
    )
    _prune_report_history(
        report_dir,
        pattern="doctor_dashboard_*.json",
        keep_count=_retention_count("NUSYQ_DOCTOR_DASHBOARD_HISTORY_KEEP", 20),
        protected_names={"doctor_dashboard_latest.json"},
    )
    _prune_report_history(
        report_dir,
        pattern="doctor_validation_*.json",
        keep_count=_retention_count("NUSYQ_DOCTOR_VALIDATION_HISTORY_KEEP", 12),
        protected_names={"doctor_validation_latest.json"},
    )

    if json_mode:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("🩺 Doctor diagnostics")
        print("=" * 60)
        for step in steps:
            status = "PASS" if step.get("passed") else "FAIL"
            suffix = " (skipped)" if step.get("skipped") else ""
            print(f"  {status} {step.get('name')}{suffix}")
            tail = step.get("stderr_tail") or step.get("stdout_tail") or ""
            if tail and not step.get("passed"):
                last_line = str(tail).splitlines()[-1]
                print(f"    {last_line}")
        print("-" * 60)
        print(f"Summary: {passed_steps}/{total_steps} checks passed")
        print(
            "Quest signal: "
            f"recent={quest_signal.get('actionable_recent_count', 0)} "
            f"stale={quest_signal.get('stale_backlog_count', 0)} "
            f"(window={quest_signal.get('window_days', 21)}d)"
        )
        print(f"Report: {report_path}")
        print(f"Dashboard: {dashboard_latest_path}")

        # Show healing suggestions if there are failures
        if healing_suggestions:
            print("\n🔧 Healing Suggestions:")
            for idx, suggestion in enumerate(healing_suggestions, 1):
                print(f"  {idx}. {suggestion['description']}")
                print(f"     $ {suggestion['command']}")

    # Auto-heal workflow: run healing if requested and issues detected
    if options.auto_heal and failed_steps:
        if not json_mode:
            print("\n🏥 Auto-heal enabled: Running system healing...")

        # Call heal via agent_task_router
        try:
            import asyncio

            from src.tools.agent_task_router import AgentTaskRouter

            router = AgentTaskRouter(repo_root=Path(hub_path) if hub_path else Path.cwd())
            heal_result = asyncio.run(router.heal_system(auto_confirm=True))

            if heal_result["status"] == "success":
                actions_count = len(heal_result.get("actions_taken", []))
                if not json_mode:
                    print(f"✅ Healing complete: {actions_count} actions taken")
                    print(f"   Report: {heal_result.get('report_path')}")
                    print("\n♻️  Re-running diagnostics to validate fixes...")
                validation_cmd = [
                    sys.executable,
                    "scripts/start_nusyq.py",
                    "doctor",
                    "--quick",
                ]
                validation_timeout = int(os.getenv("NUSYQ_DOCTOR_VALIDATION_TIMEOUT_S", "120"))
                v_rc, v_out, v_err = _run(validation_cmd, timeout_s=validation_timeout)
                validation_payload = {
                    "action": "doctor_validation",
                    "generated_at": datetime.now().isoformat(),
                    "rc": v_rc,
                    "cmd": validation_cmd,
                    "timeout_s": validation_timeout,
                    "stdout_tail": "\n".join(v_out.splitlines()[-20:]) if v_out else "",
                    "stderr_tail": "\n".join(v_err.splitlines()[-20:]) if v_err else "",
                    "healing_report": heal_result.get("report_path"),
                }
                validation_path = report_dir / f"doctor_validation_{_now_stamp()}.json"
                validation_latest_path = report_dir / "doctor_validation_latest.json"
                _write_json_report(validation_path, validation_payload)
                _write_json_report(validation_latest_path, validation_payload)
                healing_validation = {
                    "rc": v_rc,
                    "report_file": str(validation_latest_path),
                    "healing_report": heal_result.get("report_path"),
                }
                payload["healing_validation"] = healing_validation
                _write_json_report(latest_report_path, payload)
                dashboard = _build_doctor_dashboard(history, payload)
                _write_json_report(dashboard_latest_path, dashboard)
                if not json_mode:
                    if v_rc == 0:
                        print("✅ Validation passed: system health check clean")
                    else:
                        print("⚠️  Validation reported remaining issues")
                        if validation_payload["stderr_tail"]:
                            last_line = validation_payload["stderr_tail"].splitlines()[-1]
                            print(f"    {last_line}")
                        print("   Review validation report for details:")
                        print(f"   {validation_latest_path}")
            else:
                if not json_mode:
                    print(f"❌ Healing failed: {heal_result.get('error')}")

        except Exception as exc:
            if not json_mode:
                print(f"❌ Auto-heal error: {exc}")
            import traceback

            traceback.print_exc()

    emit_action_receipt(
        "doctor",
        exit_code=0,
        metadata={
            "passed_steps": passed_steps,
            "total_steps": total_steps,
            "issues_found": len(failed_steps),
            "auto_heal": options.auto_heal,
        },
    )
    return 0
