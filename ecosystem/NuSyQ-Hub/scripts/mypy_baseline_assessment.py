"""Mypy Baseline Assessment for start_nusyq.py

Documents pre-existing type issues vs. new issues from recent changes.
Used to prevent conflating brownfield technical debt with new regressions.
"""

import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
START_NUSYQ = PROJECT_ROOT / "scripts" / "start_nusyq.py"


def run_mypy() -> tuple[int, list[str]]:
    """Run mypy on start_nusyq.py and capture errors."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                str(START_NUSYQ),
                "--show-error-codes",
                "--no-error-summary",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )

        # Parse stderr and stdout (mypy uses both)
        output = result.stderr + result.stdout
        lines = [line for line in output.split("\n") if "error:" in line]

        return len(lines), lines

    except Exception as e:
        print(f"❌ Failed to run mypy: {e}")
        return 0, []


def categorize_errors(error_lines: list[str]) -> dict[str, list[str]]:
    """Categorize errors by type code."""
    categories = defaultdict(list)

    for line in error_lines:
        # Extract error code from [code-name]
        if "[" in line and "]" in line:
            code_start = line.rfind("[")
            code_end = line.rfind("]")
            error_code = line[code_start + 1 : code_end]
            categories[error_code].append(line.strip())
        else:
            categories["unknown"].append(line.strip())

    return dict(categories)


def generate_baseline_report():
    """Generate baseline report of mypy issues in start_nusyq.py."""
    print("=" * 80)
    print("🔍 Mypy Baseline Assessment: scripts/start_nusyq.py")
    print("=" * 80)
    print()

    total_errors, error_lines = run_mypy()

    if total_errors == 0:
        print("✅ No mypy errors found - file is clean!")
        return

    print(f"📊 Total Errors: {total_errors}")
    print()

    # Categorize by error code
    categorized = categorize_errors(error_lines)

    print("📋 Error Breakdown by Type:")
    print()

    # Sort by count (descending)
    sorted_categories = sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True)

    for error_code, errors in sorted_categories:
        print(f"  [{error_code}]: {len(errors)} occurrences")

    print()
    print("=" * 80)
    print("📝 Detailed Errors by Category")
    print("=" * 80)
    print()

    for error_code, errors in sorted_categories[:5]:  # Top 5 categories
        print(f"### [{error_code}] - {len(errors)} errors")
        print()
        for error in errors[:3]:  # Show first 3 examples
            # Shorten long paths
            display_error = error.replace(str(PROJECT_ROOT), ".")
            print(f"  {display_error}")
        if len(errors) > 3:
            print(f"  ... and {len(errors) - 3} more")
        print()

    print("=" * 80)
    print("🎯 Baseline Classification")
    print("=" * 80)
    print()
    print("These errors are BROWNFIELD BASELINE - pre-existing technical debt")
    print("from before 2026-02-17. Any new patches should:")
    print()
    print("  1. Not increase this count")
    print("  2. Document if fixing any of these errors")
    print("  3. Use # type: ignore[error-code] for legitimate cases")
    print("  4. File quests for systematic remediation")
    print()
    print(f"📅 Baseline Snapshot: {total_errors} errors as of 2026-02-17 (pre-orphan modernization)")
    print()

    # Suggest remediation strategy
    print("=" * 80)
    print("🏗️ Recommended Remediation Strategy")
    print("=" * 80)
    print()

    if "arg-type" in categorized:
        print("  • [arg-type] errors → Add proper type hints to function parameters")

    if "return-value" in categorized:
        print("  • [return-value] errors → Fix return type annotations")

    if "attr-defined" in categorized:
        print("  • [attr-defined] errors → Fix attribute access or add stub types")

    if "union-attr" in categorized or "no-untyped-call" in categorized:
        print("  • [union-attr/no-untyped-call] → Add type guards or proper narrowing")

    if "no-untyped-def" in categorized:
        print("  • [no-untyped-def] → Add type hints to all function signatures")

    print()
    print("💡 Consider creating a Culture Ship quest: 'Modernize start_nusyq.py Type Safety'")
    print()


if __name__ == "__main__":
    generate_baseline_report()
