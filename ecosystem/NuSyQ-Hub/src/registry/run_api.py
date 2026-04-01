from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import uvicorn

from src.registry.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8700)
