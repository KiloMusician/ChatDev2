#!/usr/bin/env python3
"""Quick task management - add, list, complete work items instantly.

Minimal implementation: store in state/tasks.jsonl, no database, no bloat.
Usage:
    task add "Fix login bug"
    task list
    task do 1
    task rm 1

OmniTag: [task_management, quick_access, minimal_implementation]
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def get_tasks_file() -> Path:
    """Get tasks file path."""
    path = Path("state/tasks.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_tasks() -> list[dict]:
    """Load all tasks."""
    tasks_file = get_tasks_file()
    tasks = []
    if tasks_file.exists():
        with tasks_file.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    tasks.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return tasks


def save_tasks(tasks: list[dict]) -> None:
    """Save tasks (append-only JSONL)."""
    tasks_file = get_tasks_file()
    with tasks_file.open("w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task) + "\n")


def task_add(title: str) -> None:
    """Add a task."""
    tasks = load_tasks()
    task_id = len([t for t in tasks if t.get("status") != "deleted"]) + 1

    task = {
        "id": task_id,
        "title": title,
        "status": "open",
        "created": datetime.now(UTC).isoformat(),
    }
    tasks.append(task)
    save_tasks(tasks)

    print(f"✅ Added: #{task_id} {title}")


def task_list() -> None:
    """List open tasks."""
    tasks = load_tasks()
    open_tasks = [t for t in tasks if t.get("status") == "open"]

    if not open_tasks:
        print("✨ No open tasks!")
        return

    print(f"\n📋 Open Tasks ({len(open_tasks)}):\n")
    for task in open_tasks:
        print(f"  #{task['id']} {task['title']}")
    print()


def task_do(task_id: int) -> None:
    """Mark task as done."""
    tasks = load_tasks()
    found = False

    for task in tasks:
        if task.get("id") == task_id and task.get("status") == "open":
            task["status"] = "done"
            task["completed"] = datetime.now(UTC).isoformat()
            found = True
            break

    if found:
        save_tasks(tasks)
        print(f"✅ Done: #{task_id}")
    else:
        print(f"❌ Task #{task_id} not found or already done")


def task_rm(task_id: int) -> None:
    """Delete a task."""
    tasks = load_tasks()
    found = False

    for task in tasks:
        if task.get("id") == task_id:
            task["status"] = "deleted"
            found = True
            break

    if found:
        save_tasks(tasks)
        print(f"🗑️  Deleted: #{task_id}")
    else:
        print(f"❌ Task #{task_id} not found")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: task <add|list|do|rm> [args]")
        print("  add TEXT - Add a task")
        print("  list    - Show open tasks")
        print("  do ID   - Mark task done")
        print("  rm ID   - Delete task")
        return

    action = sys.argv[1]

    if action == "add":
        title = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Unnamed task"
        task_add(title)
    elif action == "list":
        task_list()
    elif action == "do":
        if len(sys.argv) > 2:
            try:
                task_id = int(sys.argv[2])
                task_do(task_id)
            except ValueError:
                print("Task ID must be a number")
        else:
            print("Need task ID")
    elif action == "rm":
        if len(sys.argv) > 2:
            try:
                task_id = int(sys.argv[2])
                task_rm(task_id)
            except ValueError:
                print("Task ID must be a number")
        else:
            print("Need task ID")
    else:
        print(f"Unknown action: {action}")


if __name__ == "__main__":
    main()
