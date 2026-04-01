#!/usr/bin/env python3
"""Simple Browser Launcher - No PowerShell Dependencies.

Launches the Enhanced Context Browser directly with Python.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Enhanced Context Browser directly."""
    # Get the script directory
    script_dir = Path(__file__).parent.parent
    browser_script = script_dir / "src" / "interface" / "Enhanced-Interactive-Context-Browser.py"

    if not browser_script.exists():
        return 1

    try:
        # Launch with Python directly - no PowerShell
        result = subprocess.run(
            [
                sys.executable,
                str(browser_script),
            ],
            cwd=str(script_dir),
            check=False,
        )

        return result.returncode

    except (subprocess.CalledProcessError, FileNotFoundError, OSError, ValueError):
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
