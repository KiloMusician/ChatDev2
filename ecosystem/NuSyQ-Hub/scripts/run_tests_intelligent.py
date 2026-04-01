#!/usr/bin/env python3
"""Intelligent Test Runner - Quick access to Test Intelligence Terminal

Examples:
    python scripts/run_tests_intelligent.py                     # Run all tests
    python scripts/run_tests_intelligent.py tests/test_*.py     # Specific pattern
    python scripts/run_tests_intelligent.py --stats             # Show statistics
    python scripts/run_tests_intelligent.py --force             # Skip cache
    python scripts/run_tests_intelligent.py --agent claude --quest quest_123
"""

import sys
from pathlib import Path

# Add parent to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.testing.test_intelligence_terminal import main

if __name__ == "__main__":
    sys.exit(main())
