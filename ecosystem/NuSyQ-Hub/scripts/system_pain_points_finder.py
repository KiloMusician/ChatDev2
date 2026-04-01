#!/usr/bin/env python3
"""Quick Diagnostic: Find all system pain points and generate actionable report.

Usage:
    python scripts/system_pain_points_finder.py
    python scripts/system_pain_points_finder.py --json state/reports/pain_points.json
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_todos() -> list[dict[str, Any]]:
    """Find all TODO/FIXME/XXX/HACK markers in source code."""
    todos = []
    markers = ["TODO", "FIXME", "XXX", "HACK"]

    for py_file in Path("src").rglob("*.py"):
        try:
            with open(py_file, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if any(marker in line.upper() for marker in markers):
                        todos.append(
                            {
                                "file": str(py_file),
                                "line": i,
                                "text": line.strip()[:100],
                                "priority": "high" if "FIXME" in line.upper() else "medium",
                            }
                        )
        except Exception:
            pass

    return todos


def find_type_ignores() -> list[dict[str, str]]:
    """Find all type: ignore comments that suppress type errors."""
    ignores = []

    for py_file in Path("src").rglob("*.py"):
        try:
            with open(py_file, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if "type: ignore" in line or "type:ignore" in line:
                        ignores.append({"file": str(py_file), "line": i, "text": line.strip()[:100]})
        except Exception:
            pass

    return ignores


def find_redacted_configs() -> list[dict[str, str]]:
    """Find REDACTED placeholders in configuration files."""
    redacted = []
    config_files = list(Path("config").glob("*.json")) if Path("config").exists() else []

    for config_file in config_files:
        try:
            with open(config_file, encoding="utf-8") as f:
                content = f.read()
                if "REDACTED" in content or "REPLACE" in content or "your-" in content:
                    # Count occurrences
                    count = content.count("REDACTED") + content.count("REPLACE")
                    redacted.append({"file": str(config_file), "count": count, "needs_config": True})
        except Exception:
            pass

    return redacted


def check_lint_errors() -> dict[str, int]:
    """Run ruff to check current lint error count."""
    try:
        result = subprocess.run(
            ["ruff", "check", "src/", "--output-format=text"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Count errors
        errors = len([line for line in result.stdout.split("\n") if line.strip() and not line.startswith("Found")])
        return {
            "total_errors": errors,
            "status": "high" if errors > 30 else "medium" if errors > 15 else "low",
        }
    except Exception:
        return {"total_errors": -1, "status": "unknown"}


def check_mypy_warnings() -> dict[str, Any]:
    """Run mypy to check type warnings."""
    try:
        result = subprocess.run(
            ["python", "-m", "mypy", "src/", "--no-error-summary"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # Count warnings
        warnings = len([line for line in result.stderr.split("\n") if ": error:" in line])
        return {"total_warnings": warnings, "status": "high" if warnings > 30 else "low"}
    except Exception:
        return {"total_warnings": -1, "status": "unknown"}


def check_git_status() -> dict[str, Any]:
    """Check git working tree status."""
    try:
        # Uncommitted changes
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=Path.cwd())
        dirty_files = len([line for line in result.stdout.split("\n") if line.strip()])

        # Commits ahead
        result2 = subprocess.run(
            ["git", "rev-list", "--count", "@{u}..HEAD"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )
        commits_ahead = int(result2.stdout.strip()) if result2.stdout.strip().isdigit() else 0

        return {
            "dirty_files": dirty_files,
            "commits_ahead": commits_ahead,
            "status": "dirty" if dirty_files > 10 else "clean",
        }
    except Exception:
        return {"dirty_files": -1, "commits_ahead": -1, "status": "unknown"}


def check_test_status() -> dict[str, Any]:
    """Check if tests are passing."""
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-q", "--tb=no", "--co"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Count collectible tests
        test_count_match = re.search(r"(\d+) tests? collected", result.stdout)
        test_count = int(test_count_match.group(1)) if test_count_match else 0

        return {"collectible_tests": test_count, "status": "ready"}
    except Exception:
        return {"collectible_tests": -1, "status": "unknown"}


def main():
    """Generate comprehensive pain points report."""
    print("🔍 Scanning NuSyQ-Hub for pain points...")

    # Gather all diagnostics
    pain_points = {
        "timestamp": "2025-12-30",
        "todos": find_todos(),
        "type_ignores": find_type_ignores(),
        "redacted_configs": find_redacted_configs(),
        "lint_status": check_lint_errors(),
        "mypy_status": check_mypy_warnings(),
        "git_status": check_git_status(),
        "test_status": check_test_status(),
    }

    # Generate summary
    print("\n📊 PAIN POINTS SUMMARY:")
    print(f"  TODOs/FIXMEs: {len(pain_points['todos'])}")
    print(f"  Type Ignores: {len(pain_points['type_ignores'])}")
    print(f"  Redacted Configs: {len(pain_points['redacted_configs'])}")
    print(f"  Lint Errors: {pain_points['lint_status']['total_errors']}")
    print(f"  Mypy Warnings: {pain_points['mypy_status']['total_warnings']}")
    print(f"  Uncommitted Files: {pain_points['git_status']['dirty_files']}")
    print(f"  Commits Ahead: {pain_points['git_status']['commits_ahead']}")
    print(f"  Collectible Tests: {pain_points['test_status']['collectible_tests']}")

    # Priority recommendations
    print("\n🎯 TOP 3 PRIORITIES:")
    priorities = []

    if pain_points["redacted_configs"]:
        priorities.append("1. Configure API keys (see docs/CONFIGURATION_GUIDE.md)")

    if pain_points["lint_status"]["total_errors"] > 30:
        priorities.append("2. Fix lint errors: ruff check src/ --fix")

    if pain_points["git_status"]["dirty_files"] > 20:
        priorities.append("3. Commit changes: git status && git add && git commit")

    if len(priorities) < 3 and len(pain_points["todos"]) > 20:
        priorities.append("4. Convert TODOs to quests: python scripts/start_nusyq.py generate_quests")

    for priority in priorities[:3]:
        print(f"  {priority}")

    # Save JSON report if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        output_file = sys.argv[2] if len(sys.argv) > 2 else "pain_points.json"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(pain_points, f, indent=2)
        print(f"\n✅ Full report saved to {output_file}")

    print("\n📖 For detailed action plan, see: docs/SYSTEM_HEALTH_RESTORATION_PLAN.md")


if __name__ == "__main__":
    main()
