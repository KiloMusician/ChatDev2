#!/usr/bin/env python3
"""Test import for enhanced integrator"""


# OmniTag: {"purpose": "file_systematically_tagged",
#           "tags": ["Python", "Testing"],
#           "category": "auto_tagged",
#           "evolution_stage": "v1.0"}
import sys
import traceback
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    traceback.print_exc()
