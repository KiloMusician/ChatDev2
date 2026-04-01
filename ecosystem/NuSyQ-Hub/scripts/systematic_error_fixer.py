#!/usr/bin/env python3
"""Systematic Error Fixer

Surgical fixes for common code quality issues:
1. E402 - Move imports to top (safe cases only)
2. Remove trailing whitespace
3. Fix simple formatting issues
4. Add missing blank lines

Zeta08: Error Recovery System
- Build recovery plans from ruff diagnostics
- Classify issues into safe auto-fix vs. manual review
"""

import argparse
import json
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RecoveryAction:
    """Recovery action for a specific issue or file."""

    file_path: str
    rule_code: str
    message: str
    line: int
    column: int
    severity: str
    auto_fixable: bool
    suggested_action: str


def fix_trailing_whitespace(content: str) -> tuple[str, int]:
    """Remove trailing whitespace from all lines."""
    lines = content.split("\n")
    fixed_count = 0

    fixed_lines = []
    for line in lines:
        if line != line.rstrip():
            fixed_count += 1
        fixed_lines.append(line.rstrip())

    return "\n".join(fixed_lines), fixed_count


def fix_multiple_blank_lines(content: str) -> tuple[str, int]:
    """Reduce multiple consecutive blank lines to maximum 2."""
    fixed_count = 0
    lines = content.split("\n")
    result = []
    blank_count = 0

    for line in lines:
        if not line.strip():
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
            else:
                fixed_count += 1
        else:
            blank_count = 0
            result.append(line)

    return "\n".join(result), fixed_count


def fix_import_spacing(content: str) -> tuple[str, int]:
    """Ensure proper spacing around import groups."""
    lines = content.split("\n")
    fixed_count = 0
    result: list[str] = []

    prev_import = False
    prev_blank = False

    for i, line in enumerate(lines):
        is_import = line.strip().startswith(("import ", "from "))
        is_blank = not line.strip()

        # Need blank line before import group (after non-import code)
        if is_import and not prev_import and not prev_blank and i > 0:
            # Check if previous line was docstring end or comment
            if result and not result[-1].strip().endswith('"""') and not result[-1].strip().startswith("#"):
                result.append("")
                fixed_count += 1

        result.append(line)
        prev_import = is_import
        prev_blank = is_blank

    return "\n".join(result), fixed_count


def run_ruff_json(target: Path) -> list[dict[str, Any]]:
    """Run ruff and return JSON diagnostics.

    Args:
        target: File or directory to analyze

    Returns:
        List of ruff issue dictionaries
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(target), "--output-format=json"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print("❌ Ruff check timed out")
        return []

    if not result.stdout.strip():
        return []

    try:
        data = json.loads(result.stdout)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        print("❌ Failed to parse ruff JSON output")
        return []


def classify_severity(rule_code: str) -> str:
    """Classify rule code into severity buckets."""
    if rule_code.startswith(("F", "E")):
        return "error"
    if rule_code.startswith("W"):
        return "warning"
    return "info"


def suggest_action(rule_code: str) -> str:
    """Suggest recovery actions based on ruff rule code."""
    if rule_code in {"F401", "F841", "I001", "E402"}:
        return "auto-fix via ruff --fix"
    if rule_code == "B904":
        return "manual: add 'raise ... from err' in except blocks"
    if rule_code.startswith("C90"):
        return "manual: refactor to reduce complexity"
    return "manual review"


def build_recovery_plan(issues: Iterable[dict[str, Any]]) -> list[RecoveryAction]:
    """Build a recovery plan from ruff issues."""
    actions: list[RecoveryAction] = []
    for issue in issues:
        rule = issue.get("code", "unknown")
        actions.append(
            RecoveryAction(
                file_path=issue.get("filename", "unknown"),
                rule_code=rule,
                message=issue.get("message", ""),
                line=int(issue.get("line", 0) or 0),
                column=int(issue.get("column", 0) or 0),
                severity=classify_severity(rule),
                auto_fixable=issue.get("fix") is not None,
                suggested_action=suggest_action(rule),
            )
        )
    return actions


def summarize_actions(actions: list[RecoveryAction]) -> dict[str, Any]:
    """Summarize recovery actions for reporting."""
    summary: dict[str, Any] = {
        "total": len(actions),
        "by_severity": {"error": 0, "warning": 0, "info": 0},
        "by_rule": {},
        "auto_fixable": 0,
    }
    for action in actions:
        summary["by_severity"][action.severity] += 1
        summary["by_rule"][action.rule_code] = summary["by_rule"].get(action.rule_code, 0) + 1
        if action.auto_fixable:
            summary["auto_fixable"] += 1
    return summary


def fix_file(file_path: Path, fixes_applied: dict[str, int]) -> bool:
    """Apply systematic fixes to a single file."""
    try:
        # Read file
        content = file_path.read_text(encoding="utf-8")
        original = content

        # Apply fixes
        content, count = fix_trailing_whitespace(content)
        fixes_applied["trailing_whitespace"] += count

        content, count = fix_multiple_blank_lines(content)
        fixes_applied["blank_lines"] += count

        # Only write if changed
        if content != original:
            file_path.write_text(content, encoding="utf-8")
            fixes_applied["files_modified"] += 1
            return True

        return False

    except (OSError, UnicodeDecodeError) as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False


def main() -> int:
    """Main execution."""
    parser = argparse.ArgumentParser(description="Systematic Error Fixer (Zeta08)")
    parser.add_argument(
        "--target",
        default="src",
        help="Target directory or file for scanning",
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Generate recovery plan without applying fixes",
    )
    parser.add_argument(
        "--apply-ruff-fix",
        action="store_true",
        help="Apply ruff auto-fixes for safe rules",
    )
    parser.add_argument(
        "--report",
        default="docs/reports/error_recovery_plan.json",
        help="Output path for recovery plan report",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("🔧 SYSTEMATIC ERROR FIXER")
    print("=" * 80)
    print()

    target_path = Path(args.target)
    if not target_path.exists():
        print(f"❌ Target not found: {target_path}")
        return 1

    # Find all Python files
    py_files = list(target_path.rglob("*.py"))
    print(f"📊 Found {len(py_files)} Python files in {target_path}")
    print()

    fixes_applied = {
        "files_modified": 0,
        "trailing_whitespace": 0,
        "blank_lines": 0,
        "import_spacing": 0,
    }

    if not args.plan_only:
        print("🔄 Applying fixes...")
        for i, py_file in enumerate(py_files):
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i + 1}/{len(py_files)}")

            fix_file(py_file, fixes_applied)

        print()
        print("=" * 80)
        print("✅ FIXES APPLIED")
        print("=" * 80)
        print(f"  Files modified: {fixes_applied['files_modified']}")
        print(f"  Trailing whitespace removed: {fixes_applied['trailing_whitespace']} lines")
        print(f"  Blank lines fixed: {fixes_applied['blank_lines']} locations")
        print()

    print("📊 Building error recovery plan from ruff diagnostics...")
    issues = run_ruff_json(target_path)
    actions = build_recovery_plan(issues)
    summary = summarize_actions(actions)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_payload = {
        "target": str(target_path),
        "summary": summary,
        "actions": [action.__dict__ for action in actions],
    }
    report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    print(f"💾 Recovery plan saved: {report_path}")

    if args.apply_ruff_fix:
        print("⚡ Applying ruff auto-fixes for safe rules...")
        subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(target_path), "--fix"],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        print("✅ Ruff auto-fix completed")

    print()
    print("=" * 80)
    print("✅ COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
