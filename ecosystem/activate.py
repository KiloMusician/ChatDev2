"""PYTHONPATH activation — call this first to enable cross-repo imports."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ECOSYSTEM_DIR = Path(__file__).resolve().parent
REPO_ROOTS = [
    ECOSYSTEM_DIR / "NuSyQ-Hub" / "src",
    ECOSYSTEM_DIR / "NuSyQ-Hub",
    ECOSYSTEM_DIR / "NuSyQ_Ultimate",
    ECOSYSTEM_DIR / "Dev-Mentor",
    ECOSYSTEM_DIR / "Dev-Mentor" / "app",
    ECOSYSTEM_DIR / "SimulatedVerse",
    ECOSYSTEM_DIR / "CONCEPT_SAMURAI",
    ECOSYSTEM_DIR / "awesome-vibe-coding",
    ECOSYSTEM_DIR,
    ECOSYSTEM_DIR.parent,
]


def activate(verbose: bool = False) -> list[str]:
    """Add all ecosystem repos to sys.path. Returns list of paths added."""
    added = []
    for root in REPO_ROOTS:
        p = str(root)
        if root.exists() and p not in sys.path:
            sys.path.insert(0, p)
            added.append(p)

    # Set env var so subprocesses inherit
    existing = os.environ.get("PYTHONPATH", "")
    all_paths = [str(r) for r in REPO_ROOTS if r.exists()]
    new_pythonpath = ":".join(all_paths + ([existing] if existing else []))
    os.environ["PYTHONPATH"] = new_pythonpath

    if verbose:
        print(f"[activate] Added {len(added)} paths to sys.path")
    return added


if __name__ == "__main__":
    activate(verbose=True)
