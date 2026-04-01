#!/usr/bin/env python3
"""Enhanced Output Framework - Dual-Channel Human+Machine Intelligence Display.

Implements 50+ UX improvements for NuSyQ ecosystem outputs.
"""

import json
import sys
from datetime import datetime
from typing import Any, Literal

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree


class EnhancedOutput:
    """Dual-channel output system with machine-readable footer and human narrative."""

    def __init__(
        self,
        action_id: str,
        run_id: str | None = None,
        console: Console | None = None,
    ) -> None:
        """Initialize EnhancedOutput with action_id, run_id, console."""
        self.action_id = action_id
        self.run_id = run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.console = console or Console()
        self.start_time = datetime.now()

        # Context data
        self.context = {
            "run_id": self.run_id,
            "action_id": action_id,
            "start_time": self.start_time.isoformat(),
            "repo": "NuSyQ-Hub",
            "status": "running",
        }

        # Results tracking
        self.sections: list[dict[str, Any]] = []
        self.failures: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []
        self.artifacts: list[str] = []
        self.next_actions: list[dict[str, str]] = []
        self.insights: list[dict[str, str]] = []

    def add_section(
        self,
        name: str,
        status: Literal["pass", "fail", "warn", "info"],
        details: str = "",
        confidence: float = 1.0,
        artifacts: list[str] | None = None,
    ) -> None:
        """Add a result section with status and details."""
        section = {
            "name": name,
            "status": status,
            "details": details,
            "confidence": confidence,
            "artifacts": artifacts or [],
            "timestamp": datetime.now().isoformat(),
        }
        self.sections.append(section)

        if status == "fail":
            self.failures.append(section)
        elif status == "warn":
            self.warnings.append(section)

        if artifacts:
            self.artifacts.extend(artifacts)

    def add_failure(
        self,
        tool: str,
        kind: str,
        file: str,
        line: int | None,
        message: str,
        hint: str = "",
        confidence: float = 0.8,
    ) -> None:
        """Add a structured failure with context."""
        failure = {
            "tool": tool,
            "kind": kind,
            "file": file,
            "line": line,
            "message": message,
            "hint": hint,
            "confidence": confidence,
            "fingerprint": f"{tool}.{kind}@{file}:{line or 0}",
        }
        self.failures.append(failure)

    def add_insight(self, insight: str, category: str = "general") -> None:
        """Add a contextual insight or learning."""
        self.insights.append({"category": category, "text": insight})

    def add_next_action(
        self, action: str, priority: Literal["high", "medium", "low"] = "medium"
    ) -> None:
        """Suggest a next action."""
        self.next_actions.append({"action": action, "priority": priority})

    def print_header(self) -> None:
        """Print operation header with context."""
        git_info = self._get_git_info()

        header_text = f"""[bold cyan]{self.action_id.upper()}[/bold cyan]
[dim]Run ID:[/dim] {self.run_id}
[dim]Time:[/dim] {self.start_time.strftime("%Y-%m-%d %H:%M:%S")}
[dim]Branch:[/dim] {git_info["branch"]} [dim]({git_info["ahead"]} ahead)[/dim]
[dim]Dirty Files:[/dim] {git_info["dirty"]}
[dim]Python:[/dim] {sys.version.split()[0]} [dim]({sys.executable})[/dim]"""

        self.console.print(
            Panel.fit(header_text, title="🎯 Operation Context", border_style="cyan")
        )

    def print_outcome_banner(self) -> None:
        """Print high-level outcome in bold."""
        status = self._determine_status()

        if status == "pass":
            banner = "[bold green]✅ ALL SYSTEMS OPERATIONAL[/bold green]"
            color = "green"
        elif status == "warn":
            banner = f"[bold yellow]⚠️ DEGRADED: {len(self.warnings)} warnings[/bold yellow]"
            color = "yellow"
        elif status == "fail":
            banner = f"[bold red]❌ FAILED: {len(self.failures)} failures[/bold red]"
            color = "red"
        else:
            banner = "[bold]⏳ RUNNING[/bold]"
            color = "blue"

        self.console.print(Panel.fit(banner, border_style=color), style=f"bold {color}")

    def print_sections_table(self) -> None:
        """Print sections as a rich table."""
        if not self.sections:
            return

        table = Table(
            title="📊 Operation Sections",
            show_header=True,
            header_style="bold magenta",
            show_lines=False,
        )
        table.add_column("Section", style="cyan")
        table.add_column("Status", justify="center", width=12)
        table.add_column("Details", overflow="fold")
        table.add_column("Confidence", justify="right", width=10)

        for section in self.sections:
            status_map = {
                "pass": "[green]✅ PASS[/green]",
                "fail": "[red]❌ FAIL[/red]",
                "warn": "[yellow]⚠️ WARN[/yellow]",
                "info": "[blue]INFO[/blue]",
            }

            status_display = status_map.get(section["status"], section["status"])
            confidence = f"{section['confidence']:.0%}" if section["confidence"] < 1.0 else ""
            details = (
                section["details"][:80] + "..."
                if len(section["details"]) > 80
                else section["details"]
            )

            table.add_row(section["name"], status_display, details, confidence)

        self.console.print("\n", table)

    def print_failures_detailed(self) -> None:
        """Print detailed failure analysis."""
        if not self.failures:
            return

        self.console.print("\n[bold red]🔥 FAILURE ANALYSIS[/bold red]")

        for i, failure in enumerate(self.failures, 1):
            tree = Tree(f"[red]Failure {i}: {failure.get('tool', 'unknown').upper()}[/red]")

            tree.add(f"[dim]Kind:[/dim] {failure.get('kind', 'unknown')}")
            tree.add(f"[dim]Location:[/dim] {failure.get('file', '')}:{failure.get('line', 'N/A')}")
            tree.add(f"[dim]Message:[/dim] {failure.get('message', '')}")

            if failure.get("hint"):
                tree.add(
                    f"[yellow]💡 Hint (conf={failure.get('confidence', 0):.0%}):[/yellow] {failure['hint']}"
                )

            tree.add(f"[dim]Fingerprint:[/dim] {failure.get('fingerprint', 'N/A')}")

            self.console.print(tree)

    def print_insights(self) -> None:
        """Print contextual insights and learnings."""
        if not self.insights:
            return

        self.console.print("\n[bold cyan]💡 INSIGHTS & LEARNINGS[/bold cyan]")
        for insight in self.insights:
            category_icon = {"general": "🔍", "pattern": "🧩", "opportunity": "🌟"}.get(
                insight["category"], "📝"
            )
            self.console.print(f"  {category_icon} {insight['text']}")

    def print_next_actions(self) -> None:
        """Print suggested next actions."""
        if not self.next_actions:
            return

        self.console.print("\n[bold green]🎯 SUGGESTED NEXT ACTIONS[/bold green]")

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_actions = sorted(
            self.next_actions, key=lambda x: priority_order.get(x["priority"], 99)
        )

        for action in sorted_actions:
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[action["priority"]]
            self.console.print(f"  {priority_icon} {action['action']}")

    def print_machine_footer(self) -> None:
        """Print machine-readable JSON footer."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        footer_data = {
            "run_id": self.run_id,
            "action_id": self.action_id,
            "status": self._determine_status(),
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "failures": len(self.failures),
            "warnings": len(self.warnings),
            "sections_passed": sum(1 for s in self.sections if s["status"] == "pass"),
            "artifacts": self.artifacts,
            "next_actions": [a["action"] for a in self.next_actions],
            "receipt_path": f"docs/tracing/RECEIPTS/{self.action_id}_{self.run_id}.txt",
        }

        self.console.print("\n[dim]" + "=" * 80 + "[/dim]")
        self.console.print("[bold]MACHINE-READABLE FOOTER[/bold]")
        self.console.print("[dim]" + json.dumps(footer_data, indent=2) + "[/dim]")

    def finalize(self) -> None:
        """Print complete report."""
        self.context["end_time"] = datetime.now().isoformat()
        self.context["status"] = self._determine_status()

        # Print all sections
        self.print_outcome_banner()
        self.print_sections_table()
        self.print_failures_detailed()
        self.print_insights()
        self.print_next_actions()
        self.print_machine_footer()

    def _determine_status(self) -> str:
        """Determine overall status."""
        if any(s["status"] == "fail" for s in self.sections):
            return "fail"
        elif any(s["status"] == "warn" for s in self.sections):
            return "warn"
        elif all(s["status"] == "pass" for s in self.sections):
            return "pass"
        return "running"

    def _get_git_info(self) -> dict:
        """Get git repository information."""
        import subprocess

        try:
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

            ahead = (
                subprocess.run(
                    ["git", "rev-list", "--count", "@{u}..HEAD"],
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                or "0"
            )

            dirty = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True,
                text=True,
            ).stdout.count("\n")

            return {"branch": branch, "ahead": ahead, "dirty": dirty}
        except Exception:
            return {"branch": "unknown", "ahead": "0", "dirty": 0}


def create_enhanced_output(action_id: str, **kwargs) -> EnhancedOutput:
    """Factory function to create enhanced output."""
    output = EnhancedOutput(action_id, **kwargs)
    output.print_header()
    return output
