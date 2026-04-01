#!/usr/bin/env python3
"""Wrapper to run commands and ensure clean exit for VSCode tasks.
Prevents the "terminal waiting for input" issue.
"""

import subprocess
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_and_exit_clean.py <command> [args...]")
        sys.exit(1)

    # Run the command
    cmd = sys.argv[1:]
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent, check=False, text=True)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n^C Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
