#!/usr/bin/env python3
"""Shim for fix_logging_fstrings.py (delegates to unified_logging_fixer --mode fstrings)."""

import sys

from scripts.unified_logging_fixer import UnifiedLoggingFixer

if __name__ == "__main__":
    fixer = UnifiedLoggingFixer(verbose=True)
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    results = fixer.fix(path, mode="fstrings")
    sys.exit(0 if results.errors_encountered == 0 else 1)
