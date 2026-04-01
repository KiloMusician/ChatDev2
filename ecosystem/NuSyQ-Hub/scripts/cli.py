#!/usr/bin/env python3
"""CLI launcher for NuSyQ-Hub scripts using argparse."""

# OmniTag: {
#     "purpose": "file_systematically_tagged",
#     "tags": ["Python"],
#     "category": "auto_tagged",
#     "evolution_stage": "v1.0"
# }
import argparse
import subprocess
import sys
from pathlib import Path


def main():
    """NuSyQ-Hub CLI entry point."""
    parser = argparse.ArgumentParser(description="NuSyQ-Hub CLI Launcher")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Performance monitoring
    perf_parser = subparsers.add_parser("monitor", help="Monitor system performance")
    perf_parser.add_argument("--duration", type=int, default=30, help="Monitor duration in seconds")
    perf_parser.add_argument("--interval", type=int, default=2, help="Sample interval in seconds")

    # Project navigation
    nav_parser = subparsers.add_parser("nav", help="Navigate project structure")
    nav_parser.add_argument("--depth", type=int, default=2, help="Directory depth")
    nav_parser.add_argument("--list", action="store_true", help="List directories")

    # Lint, test, check
    subparsers.add_parser("check", help="Run lint, tests, and type checks")

    # Task history query
    tasks_parser = subparsers.add_parser("tasks", help="Query task history")
    tasks_parser.add_argument("--search", help="Filter tasks by keyword")

    # TODO → Quest sync
    todo_parser = subparsers.add_parser("todo-sync", help="Convert TODO/FIXME comments from src/ into quests")
    todo_parser.add_argument("--limit", type=int, help="Limit how many TODOs are converted")
    todo_parser.add_argument(
        "--priority",
        choices=["high", "medium", "low"],
        help="Filter TODOs by priority (FIXME=high, TODO=medium)",
    )
    todo_parser.add_argument("--dry-run", action="store_true", help="Show what would be added without writing")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    scripts_dir = Path(__file__).parent

    if args.command == "monitor":
        subprocess.run(
            [
                sys.executable,
                scripts_dir / "performance_monitor.py",
                "--duration",
                str(args.duration),
                "--interval",
                str(args.interval),
            ]
        )
    elif args.command == "nav":
        cmd = [sys.executable, scripts_dir / "project_navigator.py"]
        if args.list:
            cmd.append("--list")
        cmd.extend(["--depth", str(args.depth)])
        subprocess.run(cmd)
    elif args.command == "check":
        subprocess.run([sys.executable, scripts_dir / "lint_test_check.py"])
    elif args.command == "tasks":
        history_file = scripts_dir.parent / "docs" / "tasks_history.md"
        if not history_file.exists():
            print("No task history found.")
            return
        text = history_file.read_text()
        if args.search:
            for line in text.splitlines():
                if args.search.lower() in line.lower():
                    print(line)
        else:
            print(text)
    elif args.command == "todo-sync":
        cmd = [sys.executable, scripts_dir / "todos_to_quests.py"]
        if args.limit:
            cmd.extend(["--limit", str(args.limit)])
        if args.priority:
            cmd.extend(["--priority", args.priority])
        if args.dry_run:
            cmd.append("--dry-run")
        subprocess.run(cmd)


if __name__ == "__main__":
    main()
