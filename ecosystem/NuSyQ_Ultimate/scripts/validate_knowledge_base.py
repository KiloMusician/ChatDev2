#!/usr/bin/env python3
import sys
import traceback
from pathlib import Path

import yaml

repo_root = Path(__file__).resolve().parents[1]
knowledge_base = repo_root / "knowledge-base.yaml"

try:
    with knowledge_base.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    print("ok")
    print("path:", knowledge_base)
    if isinstance(data, dict):
        keys = list(data.keys())[:10]
        print("top-level keys:", keys)
    sys.exit(0)
except (yaml.YAMLError, OSError, UnicodeDecodeError, ValueError, TypeError) as e:
    print("error:", type(e).__name__, e)
    traceback.print_exc()
    sys.exit(2)
