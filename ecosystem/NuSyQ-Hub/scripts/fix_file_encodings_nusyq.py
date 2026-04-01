#!/usr/bin/env python3
"""Fix missing encoding parameters in open() calls across the NuSyQ repository.
This is a conservative version tuned for the NuSyQ structure.
"""

import os
import re
import sys
from pathlib import Path

# Bootstrap: Add NuSyQ-Hub to sys.path for path resolver
HUB_BOOTSTRAP = Path(__file__).resolve().parent.parent  # NuSyQ-Hub root
sys.path.insert(0, str(HUB_BOOTSTRAP / "src"))


def find_py_files(root: Path):
    return list(root.glob("**/*.py"))


def fix_file(file_path: Path):
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"⚠️ Skipping {file_path}: {e}")
        return 0

    orig = text
    # Add encoding to open() if missing
    text = re.sub(r"open\(([^,\)]+)\)", r"open(\1, encoding='utf-8')", text)
    # Add encoding for open(file, 'r') etc.
    text = re.sub(
        r"open\(([^,\)]+),\s*(['\"][rwa]b?['\"])\)",
        r"open(\1,\2, encoding='utf-8')",
        text,
    )

    if text != orig:
        file_path.write_text(text, encoding="utf-8")
        return 1
    return 0


def main():
    # Use centralized path resolver with fallback
    try:
        from utils.repo_path_resolver import get_repo_path

        root = get_repo_path("NUSYQ_ROOT")
    except ImportError:
        root = Path(os.environ.get("NUSYQ_ROOT_PATH", str(Path.home() / "NuSyQ")))
        print("⚠️  Using fallback path for NuSyQ root")
    files = find_py_files(root)
    total = 0
    for f in files:
        total += fix_file(f)
    print(f"✅ Done. Files modified: {total} / {len(files)}")


if __name__ == "__main__":
    main()
