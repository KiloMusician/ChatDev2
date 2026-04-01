#!/usr/bin/env python3
"""Quick Start Script for NuSyQ Development
Sets up environment and runs most common tasks.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

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
    MetasynthesisOutputSystem = None  # type: ignore
    OutputTier = None  # type: ignore
    ExecutionContext = None  # type: ignore
    Signal = None  # type: ignore
    SignalSeverity = None  # type: ignore
    OperationReceipt = None  # type: ignore

# Terminal routing
try:
    from src.output.terminal_router import Channel, emit_route
except ImportError:

    def emit_route(*_args, **_kwargs):  # type: ignore
        return None

    class Channel:  # type: ignore
        TASKS = "TASKS"


console = Console()

START_NUSYQ = "scripts/start_nusyq.py"

TASKS = {
    "1": ("System Snapshot", START_NUSYQ, ["snapshot"]),
    "2": ("Guild Board Status", START_NUSYQ, ["guild_status"]),
    "3": ("Run Tests", "pytest", ["tests/", "-v"]),
    "4": ("System Health Check", START_NUSYQ, ["selfcheck"]),
    "5": ("Start Dev Watcher", "scripts/dev_watcher.py", []),
    "6": ("Error Report", START_NUSYQ, ["error_report"]),
    "7": ("Install Packages", "scripts/install_dev_packages.py", []),
    "8": ("Format Code (Black)", "black", ["src/", "--line-length=100"]),
    "9": ("Lint Code (Ruff)", "ruff", ["check", "src/", "--fix"]),
    "10": ("Type Check (Mypy)", "mypy", ["src/guild/", "src/config/"]),
    "11": ("Boss Rush Summary", "scripts/show_boss_rush_summary.py", []),
}


def run_task(name: str, script: str, args: list[str]) -> bool:
    """Run a development task and emit a receipt."""
    console.print(f"\n[bold cyan]🚀 Running: {name}[/bold cyan]\n")

    root = Path(__file__).parent.parent
    cmd = [sys.executable, script, *args] if script.endswith(".py") else [script, *args]

    try:
        result = subprocess.run(cmd, cwd=root, check=False)
        ok = result.returncode == 0

        # Human message
        if ok:
            console.print(f"\n[bold green]✅ {name} completed successfully![/bold green]\n")
        else:
            console.print(f"\n[bold yellow]⚠️  {name} completed with warnings[/bold yellow]\n")

        # Emit metasynthesis receipt (if available)
        if MetasynthesisOutputSystem and ExecutionContext and OperationReceipt:
            run_id = f"quickstart_{name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            system = MetasynthesisOutputSystem(tier=OutputTier.BASIC)  # type: ignore
            context = ExecutionContext(
                run_id=run_id,
                agent_id="quickstart",
                branch="unknown",
                python_version=sys.version.split(" ")[0],
                venv_active=(sys.prefix != sys.base_prefix),
                timestamp=datetime.now().isoformat(),
                cwd=str(root),
            )

            signals = [
                Signal(
                    severity=SignalSeverity.SUCCESS if ok else SignalSeverity.WARN,
                    category="[TASK]",
                    message=f"Task '{name}' executed",
                    confidence=0.95,
                    suggestion=None,
                )
            ]

            receipt = OperationReceipt(
                context=context,
                title=f"Quickstart: {name}",
                signals=signals,
                artifacts=[],
                outcome=("✅ Success" if ok else "⚠️ Degraded"),
                next_actions=["Run another task from menu", "Review outputs"],
                guild_implications={"operator_flow": "active"},
            )

            # Prioritize signals
            for sig in receipt.signals:
                system.add_signal(sig)

            # Persist machine footer receipt
            state_dir = root / "state" / "receipts"
            state_dir.mkdir(parents=True, exist_ok=True)
            out_path = state_dir / f"{run_id}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(system.render_machine_footer(receipt), f, indent=2)

        return ok
    except (RuntimeError, OSError) as e:
        console.print(f"\n[bold red]❌ {name} failed: {e}[/bold red]\n")
        return False


def main():
    """Interactive quick start menu."""
    # Route output to Tasks terminal
    emit_route(Channel.TASKS, "NuSyQ Development Quick Start")
    console.print(
        Panel.fit(
            "[bold cyan]🧠 NuSyQ Development Quick Start[/bold cyan]\n\nSelect a task to run:",
            border_style="cyan",
        )
    )

    console.print("\n[bold]Available Tasks:[/bold]\n")
    for key, (name, _, _) in TASKS.items():
        console.print(f"  [{key}] {name}")

    console.print("\n  [0] Exit")

    while True:
        choice = Prompt.ask("\n[bold cyan]Choose task[/bold cyan]", choices=[*list(TASKS.keys()), "0"], default="1")

        if choice == "0":
            console.print("\n[bold green]👋 Goodbye![/bold green]\n")
            break

        name, script, args = TASKS[choice]
        run_task(name, script, args)

        if Prompt.ask("\n[bold]Run another task?[/bold]", choices=["y", "n"], default="y") != "y":
            console.print("\n[bold green]✅ All done![/bold green]\n")
            break


if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("❌ Rich not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)
        print("✅ Rich installed. Please run this script again.")
