#!/usr/bin/env python
"""Extract and analyze error details from unified error report."""

import json
from collections import defaultdict
from pathlib import Path

REPORT_PATH = Path("docs/Reports/diagnostics/unified_error_report_latest.json")


def analyze_errors():
    """Analyze and categorize errors by type and impact."""
    if not REPORT_PATH.exists():
        print("Error report not found. Running full scan...")
        return

    with open(REPORT_PATH) as f:
        report = json.load(f)

    diagnostics = report.get("diagnostic_details", [])

    # Categorize errors
    by_file = defaultdict(list)
    by_type = defaultdict(int)
    by_error_msg = defaultdict(int)

    for diag in diagnostics:
        repo = diag.get("repo", "unknown")
        if repo != "nusyq-hub":
            continue

        filepath = diag.get("file_path", "unknown")
        error_type = diag.get("error_type", "unknown")
        message = diag.get("message", "unknown")
        line_num = diag.get("line_num", 0)

        by_file[filepath].append((line_num, error_type, message))
        by_type[error_type] += 1
        by_error_msg[message[:60]] += 1

    print("\n" + "=" * 80)
    print("📊 NuSyQ-HUB ERROR ANALYSIS")
    print("=" * 80)

    print("\n📈 By Error Type:")
    for etype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"   {etype}: {count}")

    print("\n🎯 Top 10 Files by Error Count:")
    top_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for filepath, errors in top_files:
        print(f"   {len(errors):2} errors  {filepath}")
        for line_num, etype, msg in errors[:2]:
            print(f"      L{line_num:4}: [{etype:10}] {msg[:60]}")

    print("\n🔄 Top 10 Error Message Patterns:")
    for msg, count in sorted(by_error_msg.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {count:2}x  {msg}...")

    print(f"\n📋 Total NuSyQ-Hub errors: {len(diagnostics)}")
    print(f"   by file: {len(by_file)}")


if __name__ == "__main__":
    analyze_errors()
