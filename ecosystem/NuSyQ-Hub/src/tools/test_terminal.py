"""
Intelligent Test Terminal Runner
--------------------------------

Purpose:
- Provide a dedicated, intelligent test runner with spam suppression, receipts, and routing hints.
- Integrates with metasynthesis output system and terminal router.

Features:
- Deduplicates repeated test runs within a configurable time window when inputs haven't changed.
- Counts runs per day and per branch for observability.
- Emits dual-stream receipts (human+machine) and route hints for terminals.

Usage:
    python -m src.tools.test_terminal [path] [--quiet] [--coverage] [--window-minutes N]

Environment Variables:
- TEST_TERMINAL_SPAM_WINDOW_MINUTES: default suppression window in minutes (int, default 3)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
# (unused) from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TypedDict, cast

from src.output.metasynthesis_output_system import (ExecutionContext,
                                                    MetasynthesisOutputSystem,
                                                    OperationReceipt,
                                                    OutputTier, Signal,
                                                    SignalSeverity)
from src.output.terminal_router import Channel, emit_route

STATE_DIR = Path("state")
RECEIPTS_DIR = STATE_DIR / "receipts"
METRICS_DIR = STATE_DIR / "metrics"
REGISTRY_PATH = METRICS_DIR / "test_terminal_registry.json"
COUNTS_PATH = METRICS_DIR / "test_terminal_counts.json"
DOCS_RECEIPTS_DIR = Path("docs") / "Receipts"


class TestRunRecord(TypedDict):
    time: str
    signature: str
    branch: str
    src_mtime: float
    tests_mtime: float
    last_exit_code: int


class TestTerminalRegistry(TypedDict, total=False):
    last_run: TestRunRecord
    counts: dict[str, dict[str, int]]


def _ensure_dirs() -> None:
    for p in [RECEIPTS_DIR, METRICS_DIR, DOCS_RECEIPTS_DIR]:
        p.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _get_branch() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        branch = out.stdout.strip() or "unknown"
        return branch
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _dir_last_mtime(path: Path) -> float:
    latest = 0.0
    if not path.exists():
        return latest
    for root, _, files in os.walk(path):
        for f in files:
            try:
                mtime = os.path.getmtime(os.path.join(root, f))
                if mtime > latest:
                    latest = mtime
            except OSError:
                continue
    return latest


def _load_json(path: Path) -> TestTerminalRegistry:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return cast(TestTerminalRegistry, json.load(f))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_json(path: Path, data: TestTerminalRegistry | dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _compute_signature(target: str, quiet: bool, coverage: bool) -> str:
    return json.dumps({"target": target, "quiet": quiet, "coverage": coverage}, sort_keys=True)


def _should_skip(
    registry: TestTerminalRegistry,
    signature: str,
    window_minutes: int,
    src_mtime: float,
    tests_mtime: float,
) -> tuple[bool, str]:
    """Return (skip, reason). Skip if recent identical run and no file changes."""
    last = registry.get("last_run", {})
    if not last:
        return False, "no previous run"

    try:
        last_time = datetime.fromisoformat(last.get("time", ""))
    except ValueError:
        return False, "invalid last time"

    last_signature = last.get("signature", "")
    last_src_mtime = float(last.get("src_mtime", 0.0))
    last_tests_mtime = float(last.get("tests_mtime", 0.0))

    within_window = datetime.now(UTC) - last_time <= timedelta(minutes=window_minutes)
    unchanged = src_mtime <= last_src_mtime and tests_mtime <= last_tests_mtime

    if within_window and unchanged and last_signature == signature:
        return True, (
            f"Suppressed duplicate test run within {window_minutes} min window; no changes detected"
        )
    return False, "proceed"


def _update_registry(
    registry: TestTerminalRegistry,
    signature: str,
    branch: str,
    src_mtime: float,
    tests_mtime: float,
    exit_code: int,
) -> TestTerminalRegistry:
    today = datetime.now(UTC).date().isoformat()
    counts = registry.get("counts", {})
    counts.setdefault(branch, {})
    counts[branch][today] = int(counts[branch].get(today, 0)) + 1
    registry["counts"] = counts
    registry["last_run"] = {
        "time": _now_iso(),
        "signature": signature,
        "branch": branch,
        "src_mtime": src_mtime,
        "tests_mtime": tests_mtime,
        "last_exit_code": exit_code,
    }
    return registry


def run_pytest(target: str, quiet: bool, coverage: bool) -> subprocess.CompletedProcess:
    args: list[str] = [sys.executable, "-m", "pytest", target]
    if quiet:
        args.append("-q")
    if coverage:
        args.extend(["--cov=src", "--cov-report=term-missing"])
    return subprocess.run(args, capture_output=True, text=True, check=False)


def parse_pytest_summary(stdout: str, stderr: str) -> dict[str, int]:
    summary = {"passed": 0, "failed": 0, "skipped": 0, "xfailed": 0, "xpassed": 0}
    text = f"{stdout}\n{stderr}"
    # Look for counters like "12 passed" using regex across lines
    for match in re.finditer(r"(\d+)\s+(passed|failed|skipped|xfailed|xpassed)", text):
        num = int(match.group(1))
        key = match.group(2)
        summary[key] = num
    return summary


def main(argv: list[str] | None = None) -> int:
    _ensure_dirs()

    parser = argparse.ArgumentParser(description="Intelligent Test Terminal Runner")
    parser.add_argument("path", nargs="?", default="tests", help="Path to test target")
    parser.add_argument("--quiet", action="store_true", help="Run pytest with -q")
    parser.add_argument("--coverage", action="store_true", help="Include coverage report")
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=int(os.getenv("TEST_TERMINAL_SPAM_WINDOW_MINUTES", "3")),
        help="Spam suppression window in minutes",
    )
    args = parser.parse_args(argv)

    repo_root = Path.cwd()
    target = args.path
    quiet = args.quiet
    coverage = args.coverage
    window_minutes = max(0, args.window_minutes)

    signature = _compute_signature(target, quiet, coverage)
    registry = _load_json(REGISTRY_PATH)
    branch = _get_branch()

    src_mtime = _dir_last_mtime(repo_root / "src")
    tests_mtime = _dir_last_mtime(repo_root / target)

    skip, reason = _should_skip(registry, signature, window_minutes, src_mtime, tests_mtime)

    start_ts = _now_iso()
    emit_route(Channel.METRICS, "🧪 Tests Terminal: starting")

    if skip:
        # Prepare a receipt indicating skip
        ctx = ExecutionContext(
            run_id=f"tests_terminal_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
            agent_id="tests_terminal",
            branch=branch,
            python_version=sys.version.split()[0],
            venv_active=bool(os.getenv("VIRTUAL_ENV") or os.getenv("CONDA_PREFIX")),
            timestamp=start_ts,
            cwd=str(repo_root),
        )
        signals = [
            Signal(
                severity=SignalSeverity.INFO,
                category="[TESTS]",
                message=f"Suppressed duplicate run: {reason}",
            ),
        ]
        artifacts = [str(REGISTRY_PATH), str(COUNTS_PATH)]
        receipt = OperationReceipt(
            context=ctx,
            title="Tests Terminal - Suppressed",
            signals=signals,
            artifacts=artifacts,
            outcome="✅ Success (suppressed duplicate)",
            next_actions=["Re-run after code changes or window expiry"],
            guild_implications={"noise_reduction": True, "window_minutes": window_minutes},
        )

        system = MetasynthesisOutputSystem(tier=OutputTier.EVOLVED)
        for sig in signals:
            system.add_signal(sig)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        json_path = RECEIPTS_DIR / f"tests_terminal_suppressed_{ts}.json"
        md_path = DOCS_RECEIPTS_DIR / f"RECEIPT_tests_terminal_suppressed_{ts}.md"
        machine_footer = system.render_machine_footer(receipt)
        with json_path.open("w", encoding="utf-8") as jf:
            json.dump(machine_footer, jf, indent=2, ensure_ascii=False)
        report_md = system.render_complete_report(receipt)
        with md_path.open("w", encoding="utf-8") as mf:
            mf.write(report_md)
        emit_route(Channel.METRICS, f"✅ Suppressed duplicate test run: {reason}")
        return 0

    # Execute pytest
    proc = run_pytest(target=target, quiet=quiet, coverage=coverage)
    summary = parse_pytest_summary(proc.stdout, proc.stderr)
    # status is derived inside machine footer; keep outcome string only

    run_signals: list[Signal] = []
    if proc.returncode == 0:
        run_signals.append(
            Signal(
                severity=SignalSeverity.SUCCESS,
                category="[TESTS]",
                message=f"Pytest passed: {summary}",
            )
        )
    else:
        run_signals.append(
            Signal(
                severity=SignalSeverity.FAIL,
                category="[TESTS]",
                message=f"Pytest failed: {summary}",
            )
        )

    # Build receipt
    ctx = ExecutionContext(
        run_id=f"tests_terminal_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
        agent_id="tests_terminal",
        branch=branch,
        python_version=sys.version.split()[0],
        venv_active=bool(os.getenv("VIRTUAL_ENV") or os.getenv("CONDA_PREFIX")),
        timestamp=start_ts,
        cwd=str(repo_root),
    )
    artifacts = [str(RECEIPTS_DIR), str(METRICS_DIR)]
    outcome = "✅ Success" if proc.returncode == 0 else "❌ Failed"
    receipt = OperationReceipt(
        context=ctx,
        title="Tests Terminal - Run",
        signals=run_signals,
        artifacts=artifacts,
        outcome=outcome,
        next_actions=["Review failures", "Rerun selectively (pytest -k <pattern>)"],
        guild_implications={"quality_gate": "tests", "branch": branch},
    )

    # Persist receipts via metasynthesis machine footer and complete report
    system = MetasynthesisOutputSystem(tier=OutputTier.EVOLVED)
    for sig in run_signals:
        system.add_signal(sig)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    json_path = RECEIPTS_DIR / f"tests_terminal_{ts}.json"
    md_path = DOCS_RECEIPTS_DIR / f"RECEIPT_tests_terminal_{ts}.md"
    machine_footer = system.render_machine_footer(receipt)
    with json_path.open("w", encoding="utf-8") as jf:
        json.dump(machine_footer, jf, indent=2, ensure_ascii=False)
    report_md = system.render_complete_report(receipt)
    with md_path.open("w", encoding="utf-8") as mf:
        mf.write(report_md)

    # Update registry and counts
    registry = _update_registry(
        registry,
        signature=signature,
        branch=branch,
        src_mtime=src_mtime,
        tests_mtime=tests_mtime,
        exit_code=proc.returncode,
    )
    _save_json(REGISTRY_PATH, registry)

    # Separate counts store for quick reads (optional duplication for clarity)
    counts = {"branch": branch, "counts": registry.get("counts", {})}
    _save_json(COUNTS_PATH, counts)

    # Route hint
    if proc.returncode == 0:
        emit_route(Channel.METRICS, f"✅ Tests passed: {summary}")
    else:
        emit_route(Channel.METRICS, f"❌ Tests failed: {summary}")

    # Echo minimal stdout/stderr (trim to reduce spam)
    trimmed_stdout = "\n".join(proc.stdout.splitlines()[-50:])
    trimmed_stderr = "\n".join(proc.stderr.splitlines()[-50:])
    print(trimmed_stdout)
    if trimmed_stderr:
        print(trimmed_stderr, file=sys.stderr)

    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
