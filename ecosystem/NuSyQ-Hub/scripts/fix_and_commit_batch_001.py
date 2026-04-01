#!/usr/bin/env python3
"""Format and lint the specific files in batch 001, then re-run the batch commit script.

This targets only the files listed in `scripts/batches/commit_batch_001.py` to avoid
reformatting the entire repo.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COMMIT_SCRIPT = REPO / "scripts" / "batches" / "commit_batch_001.py"


def load_files_from_commit_script(path: Path):
    text = path.read_text(encoding="utf-8")
    start = text.find("files = [")
    if start == -1:
        raise SystemExit("cannot find files list in commit script")
    start = text.find("[", start)
    end = text.find("]", start)
    arr_text = text[start : end + 1]
    # Use ast.literal_eval for safety
    import ast

    files = ast.literal_eval(arr_text)
    return files


def run(cmd, check=True):
    print("RUN:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(REPO), check=False)
    if check and res.returncode != 0:
        raise SystemExit(res.returncode)
    return res.returncode


def main():
    files = load_files_from_commit_script(COMMIT_SCRIPT)
    if not files:
        print("No files to format")
        return

    # Only target Python files to avoid formatting non-Python assets (PowerShell, venvs, etc.)
    py_files = [f for f in files if f.endswith(".py")]
    if not py_files:
        print("No Python files to format in this batch; running commit script directly")
        run([sys.executable, str(COMMIT_SCRIPT)])
        return

    # Ensure pip tools are available
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run([sys.executable, "-m", "pip", "install", "black[jupyter]", "ruff"])

    # Run black and ruff on the specific Python paths only
    run([sys.executable, "-m", "black", *py_files])
    run(["ruff", "check", "--fix", *py_files])

    # Re-run commit script
    run([sys.executable, str(COMMIT_SCRIPT)])


if __name__ == "__main__":
    main()
