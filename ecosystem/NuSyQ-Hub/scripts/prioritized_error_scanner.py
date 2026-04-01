#!/usr/bin/env python3
"""Scan for files with errors and prioritize by fix difficulty"""

import subprocess
from collections import defaultdict
from pathlib import Path


def get_python_errors(file_path: str) -> int:
    """Count Python errors in a file using ruff"""
    try:
        result = subprocess.run(
            ["python", "-m", "ruff", "check", file_path, "--select=E,F"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Count lines with actual errors (not just file headers)
        lines = result.stdout.strip().split("\n")
        errors = [line for line in lines if ":" in line and "error" in line.lower()]
        return len(errors)
    except Exception:
        return 0


repos = {
    "NuSyQ-Hub": "C:/Users/keath/Desktop/Legacy/NuSyQ-Hub",
    "SimulatedVerse": "C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse",
    "NuSyQ": "C:/Users/keath/NuSyQ",
}

print("SCANNING FOR FIXABLE ERRORS...\n")

files_by_errors = defaultdict(list)

for repo_name, repo_path in repos.items():
    path_obj = Path(repo_path)

    # Scan Python files
    for py_file in path_obj.glob("**/*.py"):
        errors = get_python_errors(str(py_file))
        if 0 < errors < 6:  # Focus on files with 1-5 errors (easiest wins)
            rel_path = py_file.relative_to(path_obj)
            files_by_errors[errors].append((repo_name, rel_path))

# Display results sorted by error count (easiest first)
print("FILES WITH 1-5 ERRORS (priority order):\n")
for error_count in sorted(files_by_errors.keys()):
    print(f"\n{error_count} ERROR(S):")
    for repo, file_path in sorted(files_by_errors[error_count]):
        print(f"  [{repo}] {file_path}")

total_easy_fixes = sum(len(v) for v in files_by_errors.values())
print(f"\n{'=' * 70}")
print(f"Total files with 1-5 errors: {total_easy_fixes} (quick wins!)")
print(f"{'=' * 70}")
