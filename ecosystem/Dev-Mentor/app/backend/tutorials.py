from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from .paths import CORE_DIR

TUTORIALS_DIR = CORE_DIR / "tutorials"


def list_tutorials() -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    if not TUTORIALS_DIR.exists():
        return items
    for track in sorted([p for p in TUTORIALS_DIR.iterdir() if p.is_dir()]):
        for md in sorted(track.rglob("*.md")):
            items.append(
                {
                    "track": track.name,
                    "name": md.stem,
                    "path": str(md.relative_to(CORE_DIR)).replace("\\", "/"),
                }
            )
    return items


def read_tutorial(rel_path: str) -> str:
    p = (CORE_DIR / rel_path).resolve()
    # guard against traversal
    if CORE_DIR not in p.parents and p != CORE_DIR:
        raise FileNotFoundError(rel_path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(rel_path)
    return p.read_text(encoding="utf-8")
