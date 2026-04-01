#!/usr/bin/env python3
"""Test requests import specifically.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

print("Testing requests import...")

try:
    import requests

    print("✅ Requests import OK")
    print(f"Requests version: {requests.__version__}")

except Exception as e:
    print(f"❌ Requests import failed: {e}")
    import traceback

    traceback.print_exc()
