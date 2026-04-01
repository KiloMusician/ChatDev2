#!/usr/bin/env python3
"""Export VSCode Diagnostics to Quest System

This script attempts to capture diagnostic information from various sources
and convert them into actionable quests for the agent system.
"""

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


def run_mypy() -> list[dict[str, Any]]:
    """Run mypy and parse errors."""
    try:
        result = subprocess.run(
            ["mypy", "src", "--ignore-missing-imports", "--json"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.stdout:
            # Mypy JSON format
            issues = []
            for line in result.stdout.split("\n"):
                if line.strip():
                    try:
                        data = json.loads(line)
                        issues.append(
                            {
                                "tool": "mypy",
                                "file": data.get("file", "unknown"),
                                "line": data.get("line", 0),
                                "severity": ("error" if data.get("severity") == "error" else "warning"),
                                "message": data.get("message", ""),
                                "code": data.get("code", ""),
                            }
                        )
                    except json.JSONDecodeError:
                        pass
            return issues
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def run_ruff() -> list[dict[str, Any]]:
    """Run ruff and parse errors."""
    try:
        result = subprocess.run(
            ["ruff", "check", "src", "--output-format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.stdout:
            data = json.loads(result.stdout)
            return [
                {
                    "tool": "ruff",
                    "file": item.get("filename", "unknown"),
                    "line": item.get("location", {}).get("row", 0),
                    "severity": "warning",
                    "message": item.get("message", ""),
                    "code": item.get("code", ""),
                }
                for item in data
            ]
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def run_pylint() -> list[dict[str, Any]]:
    """Run pylint and parse errors."""
    try:
        result = subprocess.run(
            [
                "pylint",
                "src",
                "--output-format=json",
                "--disable=C,R",  # Disable convention and refactor messages
                "--max-line-length=120",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.stdout:
            data = json.loads(result.stdout)
            return [
                {
                    "tool": "pylint",
                    "file": item.get("path", "unknown"),
                    "line": item.get("line", 0),
                    "severity": item.get("type", "warning"),
                    "message": item.get("message", ""),
                    "code": item.get("message-id", ""),
                }
                for item in data
            ]
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return []


def check_syntax_errors() -> list[dict[str, Any]]:
    """Find Python files with syntax errors."""
    issues = []
    src_dir = Path("src")

    for py_file in src_dir.rglob("*.py"):
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(py_file)],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                issues.append(
                    {
                        "tool": "py_compile",
                        "file": str(py_file),
                        "line": 0,
                        "severity": "error",
                        "message": (result.stderr.split("\n")[0] if result.stderr else "Syntax error"),
                        "code": "SyntaxError",
                    }
                )
        except subprocess.TimeoutExpired:
            pass

    return issues


def categorize_issues(issues: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Categorize issues by type."""
    categories = defaultdict(list)

    for issue in issues:
        severity = issue.get("severity", "info")
        if "error" in severity.lower():
            categories["errors"].append(issue)
        elif "warning" in severity.lower():
            categories["warnings"].append(issue)
        else:
            categories["info"].append(issue)

    return dict(categories)


def create_quest_from_issues(issues: list[dict[str, Any]], category: str) -> dict[str, Any]:
    """Create a quest from a group of similar issues."""
    if not issues:
        return None

    # Group by file
    by_file = defaultdict(list)
    for issue in issues:
        by_file[issue["file"]].append(issue)

    # Find most common issue type
    issue_types = defaultdict(int)
    for issue in issues:
        code = issue.get("code", "unknown")
        issue_types[code] += 1

    most_common = max(issue_types.items(), key=lambda x: x[1]) if issue_types else ("unknown", 0)

    return {
        "title": f"Fix {category}: {most_common[0]} ({most_common[1]} occurrences)",
        "description": f"Fix {len(issues)} {category} across {len(by_file)} files",
        "type": "BugFixPU" if category == "errors" else "RefactorPU",
        "priority": ("critical" if category == "errors" else "high" if category == "warnings" else "medium"),
        "files_affected": list(by_file.keys())[:10],  # Limit to top 10
        "total_issues": len(issues),
        "issue_breakdown": dict(issue_types),
        "proof_criteria": [
            f"All {category} of type {most_common[0]} resolved",
            "Tests passing for affected files",
            f"No new {category} introduced",
        ],
    }


def main():
    """Main execution."""
    print("=" * 80)
    print("🔍 DIAGNOSTIC EXPORT - FINDING REAL ISSUES")
    print("=" * 80)
    print()

    all_issues = []

    # Run all diagnostic tools
    print("Running syntax check...")
    syntax_issues = check_syntax_errors()
    all_issues.extend(syntax_issues)
    print(f"  Found {len(syntax_issues)} syntax errors")

    print("Running ruff...")
    ruff_issues = run_ruff()
    all_issues.extend(ruff_issues)
    print(f"  Found {len(ruff_issues)} ruff issues")

    print("Running mypy...")
    mypy_issues = run_mypy()
    all_issues.extend(mypy_issues)
    print(f"  Found {len(mypy_issues)} mypy issues")

    print("Running pylint...")
    pylint_issues = run_pylint()
    all_issues.extend(pylint_issues)
    print(f"  Found {len(pylint_issues)} pylint issues")

    print()
    print("=" * 80)
    print(f"📊 TOTAL ISSUES FOUND: {len(all_issues)}")
    print("=" * 80)
    print()

    # Categorize
    categorized = categorize_issues(all_issues)

    print(f"  ❌ Errors: {len(categorized.get('errors', []))}")
    print(f"  ⚠️  Warnings: {len(categorized.get('warnings', []))}")
    print(f"  Info: {len(categorized.get('info', []))}")
    print()

    # Save raw diagnostics (durable in docs, with data/ fallback)
    output_dir = Path("data/diagnostics")
    docs_output_dir = Path("docs/Reports/diagnostics")
    output_dir.mkdir(parents=True, exist_ok=True)
    docs_output_dir.mkdir(parents=True, exist_ok=True)

    diagnostics_payload = {
        "total_issues": len(all_issues),
        "by_category": {k: len(v) for k, v in categorized.items()},
        "issues": all_issues,
    }

    diagnostics_file = output_dir / "vscode_diagnostics_export.json"
    diagnostics_docs_file = docs_output_dir / "vscode_diagnostics_export.json"
    with open(diagnostics_file, "w", encoding="utf-8") as f:
        json.dump(diagnostics_payload, f, indent=2)
    with open(diagnostics_docs_file, "w", encoding="utf-8") as f:
        json.dump(diagnostics_payload, f, indent=2)

    print(f"💾 Saved diagnostics to: {diagnostics_file}")
    print(f"💾 Saved diagnostics to: {diagnostics_docs_file}")
    print()

    # Create quests
    quests = []
    for category, issues in categorized.items():
        if issues:
            quest = create_quest_from_issues(issues, category)
            if quest:
                quests.append(quest)

    # Save quests
    quests_payload = {
        "total_quests": len(quests),
        "quests": quests,
    }
    quests_file = output_dir / "diagnostic_quests.json"
    quests_docs_file = docs_output_dir / "diagnostic_quests.json"
    with open(quests_file, "w", encoding="utf-8") as f:
        json.dump(quests_payload, f, indent=2)
    with open(quests_docs_file, "w", encoding="utf-8") as f:
        json.dump(quests_payload, f, indent=2)

    print(f"🎯 Created {len(quests)} quests from diagnostics")
    print(f"💾 Saved quests to: {quests_file}")
    print(f"💾 Saved quests to: {quests_docs_file}")
    print()

    # Show top issues
    if all_issues:
        print("=" * 80)
        print("🔝 TOP 10 ISSUES:")
        print("=" * 80)
        for i, issue in enumerate(all_issues[:10], 1):
            print(f"{i}. {issue['file']}:{issue['line']}")
            print(f"   [{issue['severity'].upper()}] {issue['message']}")
            print()

    print("=" * 80)
    print("✅ EXPORT COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Review diagnostics in: data/diagnostics/vscode_diagnostics_export.json")
    print("  2. Review quests in: data/diagnostics/diagnostic_quests.json")
    print("  3. Submit quests to autonomous_quest_generator.py")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
