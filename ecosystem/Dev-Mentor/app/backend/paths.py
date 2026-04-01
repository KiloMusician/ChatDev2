from __future__ import annotations
from pathlib import Path

# Repository root is two levels above this file: app/backend/paths.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]

# VS Code-native core lives at repository root (same folder) by default.
# If you embed core elsewhere later, only adjust this constant.
CORE_DIR = REPO_ROOT

# Frontend assets in app/frontend
FRONTEND_DIR = REPO_ROOT / "app" / "frontend"
