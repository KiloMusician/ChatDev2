#!/usr/bin/env python3
"""Daily Development Automation - Morning Standup (Enhanced with Metasynthesis Output)
Runs comprehensive health checks and prepares workspace for development.

Uses dual-stream consciousness: human-readable narrative + machine-readable JSON footer.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import enhanced output system
try:
    from src.output.metasynthesis_output_system import (
        ExecutionContext,
        MetasynthesisOutputSystem,
        OperationReceipt,
        OutputTier,
        Signal,
        SignalSeverity,
    )
except ImportError:
    # Fallback if import not available
    MetasynthesisOutputSystem = None

console = Console()
OUTPUT_CONTRACT_VERSION = "v1.1"


class CheckFailure(TypedDict):
    check: str
    exit_code: int
    duration_seconds: float
    details: str
    command: list[str]


class CheckResult(CheckFailure):
    status: str


def run_check(
    name: str,
    cmd: list[str],
    timeout_seconds: int = 30,
) -> tuple[bool, str, float, int]:
    """Run a health check command."""
    start_time = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        duration = time.monotonic() - start_time
        output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
        return result.returncode == 0, output, duration, result.returncode
    except Exception as e:
        duration = time.monotonic() - start_time
        return False, str(e), duration, 1


def summarize_output(output: str, limit: int = 160) -> str:
    cleaned = " | ".join(line.strip() for line in output.splitlines() if line.strip())
    if len(cleaned) > limit:
        return cleaned[: limit - 3] + "..."
    return cleaned


def suggest_next_steps(failures: list[CheckFailure]) -> list[str]:
    suggestions: list[str] = []
    for failure in failures:
        name = str(failure.get("check", ""))
        if "Quick Tests" in name:
            suggestions.append("Run: python scripts/start_nusyq.py test")
            suggestions.append("Or isolate failures: pytest tests/ -q -x --maxfail=1")
        elif "Code Format" in name:
            suggestions.append("Format code: python scripts/improve_code_quality.py")
            suggestions.append("Or run: black src/ --line-length=100")
        elif "Lint Check" in name:
            suggestions.append("Auto-fix lint: ruff check src/ --fix")
            suggestions.append("Re-run lint: ruff check src/ --select=E,F")
    # Deduplicate while preserving order
    seen = set()
    ordered = []
    for item in suggestions:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def build_checks(fast: bool) -> list[tuple[str, list[str], int]]:
    if fast:
        fast_timeout = 20
        return [
            (
                "?? System Health",
                [sys.executable, "scripts/start_nusyq.py", "selfcheck"],
                fast_timeout,
            ),
            (
                "?? Guild Status",
                [sys.executable, "scripts/start_nusyq.py", "guild_status"],
                fast_timeout,
            ),
            (
                "?? Lint Check",
                [sys.executable, "-m", "ruff", "check", "src/", "--select=E,F"],
                fast_timeout,
            ),
        ]
    return [
        ("?? System Health", [sys.executable, "scripts/start_nusyq.py", "selfcheck"], 45),
        ("?? Capabilities", [sys.executable, "scripts/start_nusyq.py", "capabilities"], 45),
        ("?? Guild Status", [sys.executable, "scripts/start_nusyq.py", "guild_status"], 45),
        ("?? Quick Tests", [sys.executable, "-m", "pytest", "tests/test_minimal.py", "-q"], 45),
        (
            "?? Code Format",
            [
                sys.executable,
                "-m",
                "black",
                "src/",
                "--check",
                "--extend-exclude",
                "\\.ipynb$",
            ],
            30,
        ),
        ("?? Lint Check", [sys.executable, "-m", "ruff", "check", "src/", "--select=E,F"], 30),
    ]


def main() -> int:
    """Run morning standup checks."""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    header = (
        f"[bold cyan]??  NuSyQ Morning Standup - {datetime.now().strftime('%Y-%m-%d %H:%M')}[/bold cyan]\n"
        f"[dim]Run ID:[/dim] {run_id}  "
        f"[dim]Python:[/dim] {sys.executable}  "
        f"[dim]CWD:[/dim] {Path.cwd()}"
    )
    console.print(Panel.fit(header, border_style="cyan"))

    parser = argparse.ArgumentParser(description="Morning standup health checks")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run a reduced check set with shorter timeouts.",
    )
    args = parser.parse_args()

    checks = build_checks(args.fast)

    table = Table(title="Health Check Results", show_header=True, header_style="bold magenta")
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    passed = 0
    failed = 0
    failures: list[CheckFailure] = []
    results: list[CheckResult] = []

    for name, cmd, timeout_seconds in checks:
        console.print(f"\n[cyan]Running {name}...[/cyan]")
        success, output, duration, exit_code = run_check(name, cmd, timeout_seconds)
        output_summary = summarize_output(output)

        if success:
            table.add_row(name, "? PASS", "")
            passed += 1
        else:
            table.add_row(name, "? FAIL", output_summary)
            failed += 1
            failures.append(
                {
                    "check": name,
                    "exit_code": exit_code,
                    "duration_seconds": round(duration, 2),
                    "details": output_summary,
                    "command": cmd,
                }
            )

        results.append(
            {
                "check": name,
                "status": "pass" if success else "fail",
                "exit_code": exit_code,
                "duration_seconds": round(duration, 2),
                "details": output_summary,
                "command": cmd,
            }
        )

        if "Quick Tests" in name:
            try:
                from src.utils.terminal_output import to_tests
                from src.utils.test_run_registry import record_test_run

                summary = record_test_run(
                    command=cmd,
                    cwd=str(Path.cwd()),
                    status="pass" if success else "fail",
                    exit_code=exit_code,
                    duration_seconds=duration,
                    source="morning_standup",
                )
                duplicate_note = ""
                if summary.run_count_window > 1:
                    duplicate_note = f" (run {summary.run_count_window}x in window)"
                to_tests(
                    f"Standup tests {summary.run_id} status={summary.status} "
                    f"duration={summary.duration_seconds}s{duplicate_note}"
                )
            except Exception:
                pass

    console.print("\n")
    console.print(table)

    suggestions = suggest_next_steps(failures)
    summary = Panel.fit(
        f"[bold]Total Checks: {len(checks)}[/bold]\n"
        f"[green]? Passed: {passed}[/green]\n"
        f"[red]? Failed: {failed}[/red]\n\n"
        f"{'[green]?? System ready for development![/green]' if failed == 0 else '[yellow]??  Some checks failed - review above[/yellow]'}",
        title="Summary",
        border_style="green" if failed == 0 else "yellow",
    )
    console.print("\n")
    console.print(summary)

    if failures:
        console.print("\n[bold]Top Signals:[/bold]")
        for failure in failures[:3]:
            console.print(f"- {failure.get('check')}: {failure.get('details')}")

    if suggestions:
        console.print("\n[bold]Next Steps:[/bold]")
        for item in suggestions[:5]:
            console.print(f"- {item}")

    report = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "status": "pass" if failed == 0 else "fail",
        "total_checks": len(checks),
        "passed": passed,
        "failed": failed,
        "failures": failures,
        "results": results,
        "suggestions": suggestions,
        "output_contract_version": OUTPUT_CONTRACT_VERSION,
    }

    report_dir = Path(__file__).parent.parent / "state" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    latest_path = report_dir / "morning_standup_latest.json"
    run_path = report_dir / f"morning_standup_{run_id}.json"

    latest_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    run_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    console.print("\n[bold]Machine Report:[/bold]")
    print(
        json.dumps(
            {
                "run_id": run_id,
                "status": report["status"],
                "failures": failures,
                "report_path": str(run_path),
                "latest_report": str(latest_path),
                "output_contract_version": OUTPUT_CONTRACT_VERSION,
                "suggestions": suggestions,
            },
            separators=(",", ":"),
        )
    )

    # Enhanced output using Metasynthesis system if available
    if MetasynthesisOutputSystem:
        try:
            output_system = MetasynthesisOutputSystem(tier=OutputTier.EVOLVED)

            # Add signals for each failure
            for failure in failures:
                output_system.add_signal(
                    Signal(
                        severity=SignalSeverity.FAIL,
                        category="[HEALTH]",
                        message=f"{failure['check']} failed (exit={failure['exit_code']})",
                        file=None,
                        line=None,
                        confidence=0.95,
                        suggestion=f"Review output: {failure['details'][:50]}...",
                    )
                )

            # Create receipt with guild context
            context = ExecutionContext(
                run_id=run_id,
                timestamp=datetime.now().isoformat(),
                agent_id="morning_standup",
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
                branch="master",
                cwd=str(Path.cwd()),
            )

            outcome = "✅ All checks passed" if failed == 0 else f"⚠️ {failed}/{len(checks)} checks failed"

            receipt = OperationReceipt(
                context=context,
                outcome=outcome,
                signals=output_system.signals,
                artifacts=[str(run_path), str(latest_path)],
                next_actions=(
                    [
                        "Review failed checks" if failed > 0 else "Ready for development",
                        "See detailed report at: " + str(run_path),
                    ]
                    if failed > 0
                    else ["System healthy - proceed with development"]
                ),
                guild_implications={
                    "health_status": "green" if failed == 0 else "yellow",
                    "ready_for_development": failed == 0,
                    "failures_count": failed,
                },
            )

            # Render enhanced output
            console.print("\n" + "=" * 80)
            console.print(output_system.render_complete_report(receipt))
        except Exception as e:
            console.print(f"\n[yellow]⚠️  Metasynthesis output unavailable: {e}[/yellow]")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
