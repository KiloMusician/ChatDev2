#!/usr/bin/env python3
"""DEPRECATED: Use scripts/unified_type_fixer.py instead.

This script is now a shim that delegates to the unified type fixer.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Delegate to unified_type_fixer.py with modernize mode."""
    print(
        "⚠️  DEPRECATED: modernize_typing.py is deprecated.\n"
        "   Please use: python scripts/unified_type_fixer.py --mode modernize\n"
    )

    args = sys.argv[1:]
    unified_args = ["python", str(PROJECT_ROOT / "scripts" / "unified_type_fixer.py")]
    unified_args.append("--mode")
    unified_args.append("modernize")

    if "--dry-run" in args:
        unified_args.append("--dry-run")
    if "-v" in args or "--verbose" in args:
        unified_args.append("--verbose")

    path = "src"
    if "--path" in args:
        idx = args.index("--path")
        if idx + 1 < len(args):
            path = args[idx + 1]

    unified_args.append("--path")
    unified_args.append(path)

    result = subprocess.run(unified_args, cwd=PROJECT_ROOT, check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
