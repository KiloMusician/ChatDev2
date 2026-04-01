#!/usr/bin/env python3
"""Analyze all errors in the NuSyQ-Hub system."""

import json
from collections import defaultdict
from pathlib import Path

# Read the VSCode diagnostics
vscode_file = Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/state/vscode_diagnostics.json")
data = json.loads(vscode_file.read_text())

# Analyze error patterns
error_patterns = defaultdict(int)
by_file = data.get("by_file", {})

print("=" * 80)
print("NUSYQ-HUB ERROR ANALYSIS REPORT")
print("=" * 80)
print()

# Summary from vscode_diagnostics.json (current VSCode state)
print("CURRENT VSCODE STATE (from Problems Panel):")
print(f"  Errors:   {data['errors']}")
print(f"  Warnings: {data['warnings']}")
print(f"  Infos:    {data['infos']}")
print(f"  Total:    {data['total']}")
print()

# Read unified errors for linter data
unified_file = Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/state/unified_errors.json")
unified_data = json.loads(unified_file.read_text())

print("LINTER SCAN RESULTS (from unified_errors.json):")
print(f"  Date: {unified_data['timestamp']}")
print(f"  Total Errors:   {unified_data['totals']['errors']}")
print(f"  Total Warnings: {unified_data['totals']['warnings']}")
print()
print("  By Tool:")
for source in unified_data["sources"]:
    name = source["source"]
    errs = source["errors"]
    warns = source["warnings"]
    total = source["total"]
    print(f"    {name:30} {errs:4} errors, {warns:4} warnings, {total:5} total")
print()

# Top error files
error_files = [(f, info["errors"]) for f, info in by_file.items() if info["errors"] > 0]
error_files.sort(key=lambda x: x[1], reverse=True)

print("TOP 15 FILES WITH MOST ERRORS (from Pylance):")
print("-" * 80)
for i, (filepath, count) in enumerate(error_files[:15], 1):
    filename = Path(filepath).name
    # Get relative path
    rel_path = filepath.replace(r"c:\Users\keath\Desktop\Legacy\NuSyQ-Hub\\", "")
    print(f"{i:2}. {count:3} errors - {rel_path}")

print()
print("=" * 80)
print("ERROR CATEGORIES:")
print("-" * 80)

# Categorize errors by type
categories = {"import": 0, "type": 0, "syntax": 0, "undefined": 0, "unused": 0, "other": 0}

# Read error report for detailed analysis
error_report = Path(
    "C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/state/receipts/error_report_2025-12-25_132711.json"
)
error_data = json.loads(error_report.read_text())

for detail in error_data.get("diagnostic_details", [])[:100]:  # Sample first 100
    msg = detail.get("message", "").lower()
    if "import" in msg or "module" in msg:
        categories["import"] += 1
    elif "type" in msg or "incompatible" in msg or "assignment" in msg:
        categories["type"] += 1
    elif "syntax" in msg:
        categories["syntax"] += 1
    elif "undefined" in msg or "not defined" in msg:
        categories["undefined"] += 1
    elif "unused" in msg:
        categories["unused"] += 1
    else:
        categories["other"] += 1

for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    print(f"{cat:12} {count:3} errors (from sample)")

print()
print("=" * 80)
print("CRITICAL ERRORS TO FIX FIRST:")
print("-" * 80)

# Find critical errors
critical = []
for detail in error_data.get("diagnostic_details", [])[:50]:
    msg = detail["message"]
    file_path = detail.get("file_path", "")
    line = detail.get("line_num", 0)

    # Critical: import errors, syntax errors, undefined names
    if any(x in msg.lower() for x in ["not defined", "import", "syntax", "module"]):
        critical.append({"file": Path(file_path).name, "line": line, "message": msg[:80]})

for i, err in enumerate(critical[:10], 1):
    print(f"{i}. {err['file']}:{err['line']}")
    print(f"   {err['message']}")
    print()

print("=" * 80)
