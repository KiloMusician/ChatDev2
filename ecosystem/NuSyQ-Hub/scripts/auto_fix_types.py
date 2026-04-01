#!/usr/bin/env python3
"""DEPRECATED: Use scripts/unified_type_fixer.py instead.

This script is now a shim that delegates to the unified type fixer.

Auto-Fix Type Issues - Fix common mypy errors

Automatically fixes:
1. Missing Optional type hints (foo: Path -> foo: Optional[Path])
2. Add -> None to functions without return type
3. Fix no-any-return by adding proper type casts
4. Add explicit Exception types to bare excepts (already done)

Run with --dry-run to preview changes.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Delegate to unified_type_fixer.py with fix-mypy mode."""
    print(
        "⚠️  DEPRECATED: auto_fix_types.py is deprecated.\n"
        "   Please use: python scripts/unified_type_fixer.py --mode fix-mypy\n"
    )

    # Parse arguments to pass to unified fixer
    args = sys.argv[1:]

    # Map old --path and --limit args to unified interface
    unified_args = ["python", str(PROJECT_ROOT / "scripts" / "unified_type_fixer.py")]
    unified_args.append("--mode")
    unified_args.append("fix-mypy")

    # Pass through --dry-run if present
    if "--dry-run" in args:
        unified_args.append("--dry-run")

    # Extract --path argument
    path = "src"
    if "--path" in args:
        idx = args.index("--path")
        if idx + 1 < len(args):
            path = args[idx + 1]

    unified_args.append("--path")
    unified_args.append(path)

    # Execute unified fixer
    result = subprocess.run(unified_args, cwd=PROJECT_ROOT)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
