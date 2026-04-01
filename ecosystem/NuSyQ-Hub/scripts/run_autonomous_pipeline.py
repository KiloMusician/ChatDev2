#!/usr/bin/env python3
"""Autonomous Pipeline Runner - Quick access to enhancement pipeline

Examples:
    python scripts/run_autonomous_pipeline.py                # Run indefinitely
    python scripts/run_autonomous_pipeline.py --cycles 5     # Run 5 cycles
    python scripts/run_autonomous_pipeline.py --no-breathing # Skip breathing
"""

import sys
from pathlib import Path

# Add parent to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.orchestration.autonomous_enhancement_pipeline import main

if __name__ == "__main__":
    sys.exit(main())
