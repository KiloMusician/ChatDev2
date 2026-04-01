#!/usr/bin/env python3
"""Fix VS Code tasks.json to add isBackground flags to appropriate tasks.

Identifies tasks that should run in background and adds proper configuration.
"""

import json
import re
from pathlib import Path


def should_be_background(task: dict) -> bool:
    """Determine if a task should run in background."""
    label = task.get("label", "").lower()
    command = str(task.get("command", "")).lower()
    args = " ".join(str(arg) for arg in task.get("args", [])).lower()

    # Tasks that are already marked as background
    if task.get("isBackground"):
        return False  # Already configured

    # Patterns indicating background tasks
    background_patterns = [
        # Server/daemon tasks
        "server",
        "daemon",
        "watcher",
        "watch",
        "monitor",
        # Long-running services
        "jupyter",
        "docker",
        "observability",
        # Development servers
        "dev server",
        "simulated",
        "mcp server",
        # Continuous processes
        "auto cycle",
        "architecture watcher",
        # Log viewers
        "view.*logs",
        "logs.*tail",
    ]

    task_text = f"{label} {command} {args}"

    for pattern in background_patterns:
        if re.search(pattern, task_text):
            return True

    # Check for specific indicators
    if "panel" in task.get("presentation", {}):
        if task["presentation"].get("panel") == "dedicated":
            # Dedicated panel usually means long-running
            return True

    return False


def create_background_config(task: dict) -> dict:
    """Create appropriate background configuration for a task."""
    # Default problem matcher for background tasks
    problem_matcher = task.get("problemMatcher", {})

    if not problem_matcher or problem_matcher == []:
        # Generic background problem matcher
        problem_matcher = {
            "owner": f"{task['label'].replace(' ', '-').replace(':', '').lower()}-ready",
            "pattern": [{"regexp": "^(.+)$", "message": 1}],
            "background": {
                "activeOnStart": True,
                "beginsPattern": ".*",
                "endsPattern": "(ready|started|running|listening|server)",
            },
        }

    return problem_matcher


def main() -> None:
    """Fix tasks.json file."""
    repo_root = Path(__file__).resolve().parents[1]
    tasks_file = repo_root / ".vscode" / "tasks.json"

    print("🔧 VS Code Tasks Background Flag Fixer")
    print("=" * 60)
    print(f"Processing: {tasks_file}")
    print()

    with open(tasks_file, encoding="utf-8") as f:
        data = json.load(f)

    tasks = data.get("tasks", [])
    total_tasks = len(tasks)
    background_count = sum(1 for t in tasks if t.get("isBackground"))

    print(f"Total tasks: {total_tasks}")
    print(f"Already background: {background_count}")
    print()

    # Analyze and fix tasks
    fixes = []
    for task in tasks:
        if should_be_background(task) and not task.get("isBackground"):
            fixes.append(task["label"])
            task["isBackground"] = True

            # Ensure proper problem matcher for background task
            if not task.get("problemMatcher"):
                task["problemMatcher"] = create_background_config(task)

    if fixes:
        print(f"🔨 Fixing {len(fixes)} tasks:")
        for label in fixes:
            print(f"  ✅ {label}")
        print()

        # Create backup
        backup_file = tasks_file.with_suffix(".json.backup")
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Backup saved: {backup_file}")

        # Write fixed file
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Tasks file updated: {tasks_file}")
        print()
        print("📊 Summary:")
        print(f"  - Total tasks: {total_tasks}")
        print(f"  - Background before: {background_count}")
        print(f"  - Background after: {background_count + len(fixes)}")
        print(f"  - Tasks fixed: {len(fixes)}")
    else:
        print("✅ No fixes needed - all tasks properly configured!")

    print()
    print("💡 Tip: Reload VS Code to apply changes")


if __name__ == "__main__":
    main()
