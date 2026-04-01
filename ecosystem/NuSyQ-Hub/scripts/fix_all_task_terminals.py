#!/usr/bin/env python3
"""Comprehensive Task Terminal Fix - Chug Mode.
Fixes terminal stuck issues across all repos by applying proper presentation settings.
"""

import json
from pathlib import Path
from typing import Any

# Standard presentation settings for non-background tasks
STANDARD_PRESENTATION = {
    "echo": True,
    "reveal": "always",
    "focus": False,
    "panel": "shared",
    "showReuseMessage": False,
    "clear": False,
}

# Background task settings
BACKGROUND_PRESENTATION = {
    "echo": True,
    "reveal": "always",
    "focus": False,
    "panel": "dedicated",
    "showReuseMessage": False,
}

# Tasks that should be marked as background
BACKGROUND_TASK_PATTERNS = [
    "docker",
    "observability",
    "logs",
    "watch",
    "serve",
    "dev server",
    "continuous",
]


def should_be_background(label: str) -> bool:
    """Determine if a task should be a background task."""
    label_lower = label.lower()
    return any(pattern in label_lower for pattern in BACKGROUND_TASK_PATTERNS)


def fix_tasks_json(tasks_path: Path) -> dict[str, Any]:
    """Fix a tasks.json file by adding proper presentation settings."""
    if not tasks_path.exists():
        return {"status": "skipped", "reason": "file_not_found"}

    try:
        with open(tasks_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {"status": "error", "reason": f"json_error: {e}"}

    tasks = data.get("tasks", [])
    fixed_count = 0
    background_count = 0

    for task in tasks:
        label = task.get("label", "unknown")

        # Check if task needs fixing
        if "presentation" not in task or task["presentation"].get("showReuseMessage") is not False:
            is_background = should_be_background(label)

            if is_background:
                task["presentation"] = BACKGROUND_PRESENTATION.copy()
                task["isBackground"] = True
                background_count += 1
            else:
                if "presentation" not in task:
                    task["presentation"] = {}
                task["presentation"].update(STANDARD_PRESENTATION)

            fixed_count += 1

    # Write back
    with open(tasks_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return {
        "status": "success",
        "total_tasks": len(tasks),
        "fixed": fixed_count,
        "background": background_count,
    }


def main():
    """Fix tasks.json files across all repos."""
    root = Path(__file__).parents[1]

    # Find all tasks.json files
    tasks_files = list(root.glob("**/.vscode/tasks.json"))

    print("🔧 Task Terminal Hygiene - Chug Mode")
    print(f"Found {len(tasks_files)} tasks.json files\n")

    results = {}
    for tasks_file in tasks_files:
        rel_path = tasks_file.relative_to(root)
        print(f"Fixing: {rel_path}")
        result = fix_tasks_json(tasks_file)
        results[str(rel_path)] = result

        if result["status"] == "success":
            print(f"  ✅ Fixed {result['fixed']}/{result['total_tasks']} tasks")
            if result["background"] > 0:
                print(f"  🔄 Marked {result['background']} as background")
        else:
            print(f"  ⚠️  {result['status']}: {result.get('reason', 'unknown')}")
        print()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_fixed = sum(r.get("fixed", 0) for r in results.values() if r["status"] == "success")
    total_background = sum(r.get("background", 0) for r in results.values() if r["status"] == "success")

    print(f"Total tasks fixed: {total_fixed}")
    print(f"Total background tasks: {total_background}")
    print("\n✅ Terminal hygiene complete!")


if __name__ == "__main__":
    main()
