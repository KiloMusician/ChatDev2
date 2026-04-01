"""Repo registry — reads repo_registry.json; fallback to env-based defaults."""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from .env import REGISTRY_PATH


@lru_cache(maxsize=1)
def get_registry() -> Dict[str, Any]:
    try:
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def get_repo(name: str) -> Optional[Dict[str, Any]]:
    reg = get_registry()
    return reg.get(name) or reg.get(name.replace("-", "_")) or reg.get(name.replace("_", "-"))


def list_repos(online_only: bool = False) -> List[Dict[str, Any]]:
    reg = get_registry()
    repos = [
        {"id": k, **v}
        for k, v in reg.items()
        if not k.startswith("_")
    ]
    if online_only:
        repos = [r for r in repos if r.get("status") == "online"]
    return repos


def repo_root(name: str) -> Optional[str]:
    r = get_repo(name)
    return r.get("root") if r else None


def repo_api(name: str) -> Optional[str]:
    r = get_repo(name)
    return r.get("api") if r else None
