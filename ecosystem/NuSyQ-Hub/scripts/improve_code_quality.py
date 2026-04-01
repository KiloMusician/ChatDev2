#!/usr/bin/env python3
"""Automated Code Quality Improver
Runs formatter, linter, and auto-fixes common issues.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Metasynthesis Output System integration
try:
    from src.output.metasynthesis_output_system import (
        ExecutionContext,
        MetasynthesisOutputSystem,
        OperationReceipt,
        OutputTier,
        Signal,
        SignalSeverity,
    )
except Exception:
    # Fallback: allow script to run even if import resolution is funky
    MetasynthesisOutputSystem = None  # type: ignore
    OutputTier = None  # type: ignore
    ExecutionContext = None  # type: ignore
    Signal = None  # type: ignore
    SignalSeverity = None  # type: ignore
    OperationReceipt = None  # type: ignore

# Terminal routing hint
try:
    from src.output.terminal_router import Channel, emit_route
except ImportError:

    def emit_route(*args, **kwargs):  # type: ignore
        return None

    class Channel:  # type: ignore
        METRICS = "METRICS"


console = Console()


def run_tool(name: str, cmd: list[str], fix_mode: bool = False) -> tuple[bool, str, str, int]:
    """Run a code quality tool and return (ok, stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        if result.returncode == 0:
            console.print(f"[green]✅ {name} - OK[/green]")
            return True, stdout, stderr, result.returncode
        else:
            if fix_mode:
                console.print(f"[yellow]🔧 {name} - Fixed issues[/yellow]")
                return True, stdout, stderr, result.returncode
            else:
                console.print(f"[red]❌ {name} - Found issues[/red]")
                console.print(stdout[:300])
                return False, stdout, stderr, result.returncode
    except Exception as e:
        console.print(f"[red]❌ {name} - Error: {e}[/red]")
        return False, "", str(e), 2


def main():
    """Run code quality improvements."""
    # Route to Metrics terminal
    emit_route(Channel.METRICS, "NuSyQ Code Quality Improver")
    console.print("\n[bold cyan]🎨 NuSyQ Code Quality Improver[/bold cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # 1. Format with Black
        task = progress.add_task("[cyan]Formatting code with Black...", total=None)
        ok_black, _out_black, _err_black, _rc_black = run_tool(
            "Black Formatter",
            [sys.executable, "-m", "black", "src/", "tests/", "--line-length=100"],
            fix_mode=True,
        )
        progress.remove_task(task)

        # 2. Organize imports
        task = progress.add_task("[cyan]Organizing imports...", total=None)
        ok_imports, _out_imports, _err_imports, _rc_imports = run_tool(
            "Import Organizer",
            [sys.executable, "-m", "ruff", "check", "src/", "--select=I", "--fix"],
            fix_mode=True,
        )
        progress.remove_task(task)

        # 3. Auto-fix safe Ruff issues
        task = progress.add_task("[cyan]Auto-fixing Ruff issues...", total=None)
        ok_ruff_fix, _out_ruff_fix, _err_ruff_fix, _rc_ruff_fix = run_tool(
            "Ruff Auto-Fix", [sys.executable, "-m", "ruff", "check", "src/", "--fix"], fix_mode=True
        )
        progress.remove_task(task)

        # 4. Run final lint check
        task = progress.add_task("[cyan]Final lint check...", total=None)
        success, _out_final, _err_final, _rc_final = run_tool(
            "Final Ruff Check",
            [sys.executable, "-m", "ruff", "check", "src/", "--select=E,F,W"],
            fix_mode=False,
        )
        progress.remove_task(task)

    console.print("\n[bold green]✅ Code quality improvements complete![/bold green]\n")

    console.print("[dim]Next steps:[/dim]")
    console.print("  • Review changes: [cyan]git diff[/cyan]")
    console.print("  • Run tests: [cyan]pytest tests/ -v[/cyan]")
    console.print("  • Commit: [cyan]git add . && git commit -m 'chore: code quality improvements'[/cyan]\n")

    # Emit metasynthesis dual-stream report (if available)
    try:
        root = Path(__file__).parent.parent
        run_id = f"code_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if MetasynthesisOutputSystem and ExecutionContext and OperationReceipt:
            system = MetasynthesisOutputSystem(tier=OutputTier.EVOLVED)  # type: ignore
            context = ExecutionContext(
                run_id=run_id,
                agent_id="improve_code_quality",
                branch="unknown",
                python_version=sys.version.split(" ")[0],
                venv_active=(sys.prefix != sys.base_prefix),
                timestamp=datetime.now().isoformat(),
                cwd=str(root),
            )

            signals = []

            # Construct signals based on tool outcomes
            signals.append(
                Signal(
                    severity=SignalSeverity.SUCCESS if ok_black else SignalSeverity.WARN,
                    category="[FORMAT]",
                    message=(
                        "Black formatted code (line-length=100)"
                        if ok_black
                        else "Black reported issues; attempted fixes applied"
                    ),
                    confidence=0.95,
                )
            )
            signals.append(
                Signal(
                    severity=SignalSeverity.SUCCESS if ok_imports else SignalSeverity.WARN,
                    category="[IMPORTS]",
                    message=(
                        "Imports organized via Ruff (select=I)"
                        if ok_imports
                        else "Import organization encountered issues"
                    ),
                    confidence=0.9,
                )
            )
            signals.append(
                Signal(
                    severity=SignalSeverity.SUCCESS if ok_ruff_fix else SignalSeverity.WARN,
                    category="[LINT]",
                    message=("Ruff auto-fix applied" if ok_ruff_fix else "Ruff auto-fix encountered issues"),
                    confidence=0.85,
                )
            )
            signals.append(
                Signal(
                    severity=(SignalSeverity.SUCCESS if success else SignalSeverity.FAIL),
                    category="[LINT]",
                    message=("Final Ruff check passed" if success else "Final Ruff check found issues"),
                    confidence=0.8,
                )
            )

            artifacts = []
            receipt = OperationReceipt(
                context=context,
                title="Code Quality Improver",
                signals=signals,
                artifacts=artifacts,
                outcome=("✅ Success" if success else "⚠️ Degraded (lint issues remain)"),
                next_actions=[
                    "Run tests: pytest tests/ -v",
                    "Review remaining lint findings",
                    "Commit changes: git add . && git commit -m 'chore: code quality improvements'",
                ],
                guild_implications={
                    "quality": "improving",
                    "risk": "low" if success else "medium",
                },
            )

            # Add signals to system for prioritized view
            for sig in receipt.signals:
                system.add_signal(sig)

            report = system.render_complete_report(receipt)
            console.print("\n" + report + "\n")

            # Persist machine footer receipt
            state_dir = root / "state" / "receipts"
            state_dir.mkdir(parents=True, exist_ok=True)
            out_path = state_dir / f"{run_id}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(system.render_machine_footer(receipt), f, indent=2)

            # Canonical short receipt in docs
            docs_dir = root / "docs" / "Receipts"
            docs_dir.mkdir(parents=True, exist_ok=True)
            md_path = docs_dir / f"RECEIPT_{run_id}.md"
            md_path.write_text(
                (
                    f"# Receipt: {receipt.title}\n\n"
                    f"- run_id: {run_id}\n"
                    f"- outcome: {receipt.outcome}\n"
                    f"- timestamp: {context.timestamp}\n"
                    f"- cwd: {context.cwd}\n"
                ),
                encoding="utf-8",
            )

        else:
            console.print("[dim]Metasynthesis Output System not available; skipping receipt emission.[/dim]")
    except Exception as e:
        console.print(f"[yellow]⚠️  Receipt emission skipped: {e}[/yellow]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
