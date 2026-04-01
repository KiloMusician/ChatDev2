#!/usr/bin/env python3
"""Analyze tools, utils, and system directories for issues."""

import ast
from pathlib import Path
from typing import Dict, List


def find_issues(directory: str) -> dict[str, list[str]]:
    """Find incomplete/problematic Python files."""
    issues = {
        "incomplete": [],
        "warnings": [],
        "ok": [],
    }

    path = Path(directory)
    if not path.exists():
        return issues

    # First level only - don't recurse into __pycache__
    try:
        for py_file in path.glob("*.py"):
            if py_file.name.startswith("#") or py_file.name.startswith("."):
                continue

            try:
                with open(py_file, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    try:
                        ast.parse(content)
                    except SyntaxError:
                        issues["incomplete"].append(py_file.name)
                        continue

                # Check for NotImplementedError or empty implementations
                has_not_impl = "NotImplementedError" in content
                has_todo = "TODO" in content or "FIXME" in content

                if has_not_impl:
                    issues["incomplete"].append(py_file.name)
                elif has_todo:
                    issues["warnings"].append(py_file.name)
                else:
                    issues["ok"].append(py_file.name)
            except Exception:
                pass
    except Exception:
        pass

    return issues


# Check tools, utils, system
dirs_to_check = {
    "src/tools": "Tool modules (routing, healing, etc)",
    "src/utils": "Utility modules (helpers, imports, etc)",
    "src/system": "System-level modules",
    "src/core": "Core modules",
    "src/diagnostics": "Diagnostic utilities",
    "src/healing": "Healing & recovery tools",
    "src/orchestration": "Orchestration & agent routing",
}

for directory, description in dirs_to_check.items():
    issues = find_issues(directory)

    print(f"\n{'=' * 70}")
    print(f"📂 {description}: {directory}")
    print("=" * 70)

    total = len(issues["incomplete"]) + len(issues["warnings"]) + len(issues["ok"])
    print(f"Total: {total} files")

    if issues["incomplete"]:
        print(f"\n⚠️  Incomplete/Broken ({len(issues['incomplete'])} files):")
        for f in sorted(issues["incomplete"])[:10]:
            print(f"   - {f}")
        if len(issues["incomplete"]) > 10:
            print(f"   ... and {len(issues['incomplete']) - 10} more")

    if issues["warnings"]:
        print(f"\n📌 With TODO/FIXME ({len(issues['warnings'])} files):")
        for f in sorted(issues["warnings"])[:10]:
            print(f"   - {f}")
        if len(issues["warnings"]) > 10:
            print(f"   ... and {len(issues['warnings']) - 10} more")

    print(f"\n✅ OK/Complete: {len(issues['ok'])} files")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

total_incomplete = 0
total_warnings = 0
for directory, _ in dirs_to_check.items():
    issues = find_issues(directory)
    total_incomplete += len(issues["incomplete"])
    total_warnings += len(issues["warnings"])

print(f"Total incomplete files: {total_incomplete}")
print(f"Total files with TODOs: {total_warnings}")
