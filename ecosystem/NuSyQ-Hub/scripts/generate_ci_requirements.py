#!/usr/bin/env python3
"""Generate a minimal requirements.ci.txt used by CI runs.

This file is intentionally small and conservative so CI jobs that
expect this script to exist do not fail when the file is missing.
Add additional packages as needed.
"""

from pathlib import Path

req_file = Path("requirements.ci.txt")
requirements = [
    "pytest>=7.0",
    "pytest-asyncio",
    "pytest-benchmark",
    "pytest-cov",
    "coverage",
    "ruff",
    "mypy",
]

req_file.write_text("\n".join(requirements), encoding="utf-8")
print(f"Wrote {req_file} with {len(requirements)} entries")
