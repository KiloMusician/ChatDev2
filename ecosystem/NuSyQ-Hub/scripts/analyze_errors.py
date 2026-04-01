#!/usr/bin/env python
"""Analyze mypy errors to identify Stage 5 targets."""

import subprocess
from collections import defaultdict

result = subprocess.run(
    ["python", "-m", "mypy", "src/", "--no-error-summary"],
    capture_output=True,
    text=True,
    timeout=120,
)
output = result.stdout + result.stderr

file_errors = defaultdict(int)
for line in output.split("\n"):
    if line.startswith("src/") and ":" in line:
        filepath = line.split(":")[0]
        file_errors[filepath] += 1

sorted_files = sorted(file_errors.items(), key=lambda x: x[1], reverse=True)
print("\n🎯 TOP 15 FILES BY ERROR COUNT (Stage 5 Targets):\n")
for i, (filepath, count) in enumerate(sorted_files[:15], 1):
    print(f"{i:2}. {count:3} errors  {filepath}")
