"""Path resolution utilities for cross-repo imports."""
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import List

from .env import REPO_ROOTS
from .registry import get_repo


def activate_all() -> List[str]:
    """Add all known repo roots to sys.path. Returns list added."""
    added = []
    for name, root in REPO_ROOTS.items():
        p = Path(root)
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))
            added.append(str(p))
    return added


def repo_path(name: str) -> Path:
    """Resolve a repo path by registry name, env var, or default."""
    # 1. Registry
    r = get_repo(name)
    if r and r.get("root"):
        p = Path(r["root"])
        if p.exists():
            return p
    # 2. Env var
    env_key = f"NUSYQ_{name.upper()}_ROOT"
    env_val = os.environ.get(env_key, "")
    if env_val and Path(env_val).exists():
        return Path(env_val)
    # 3. Default
    default = REPO_ROOTS.get(name, "")
    return Path(default) if default else Path(".")


def find_entrypoint(repo_name: str) -> str:
    """Find a repo's most likely executable entry point."""
    root = repo_path(repo_name)
    candidates = [
        "app/backend/main.py", "src/main.py", "main.py",
        "app/main.py", "server.py", "run.py",
    ]
    for c in candidates:
        p = root / c
        if p.exists():
            return str(p)
    return ""
