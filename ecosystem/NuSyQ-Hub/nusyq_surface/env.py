"""Environment resolution for the NuSyQ ecosystem — Replit-native."""
from __future__ import annotations
import os
from pathlib import Path

# ── Root paths ─────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent.parent  # ecosystem/
_WORKSPACE = _HERE.parent                        # project root

ECOSYSTEM_ROOT  = str(_HERE)
WORKSPACE_ROOT  = str(_WORKSPACE)
REGISTRY_PATH   = str(_HERE / "repo_registry.json")

# ── Service endpoints ──────────────────────────────────────────────────────
CHATDEV_API         = os.environ.get("CHATDEV_API",         "http://localhost:6400")
DEV_MENTOR_API      = os.environ.get("DEV_MENTOR_API",      "http://localhost:8008")
CONCEPT_SAMURAI_API = os.environ.get("CONCEPT_SAMURAI_API", "http://localhost:3002")
NUSYQ_HUB_API       = os.environ.get("NUSYQ_HUB_API",       "")

# ── Repo roots ─────────────────────────────────────────────────────────────
REPO_ROOTS = {
    "chatdev":           WORKSPACE_ROOT,
    "dev_mentor":        str(_HERE / "Dev-Mentor"),
    "nusyq_hub":         str(_HERE / "NuSyQ-Hub"),
    "concept_samurai":   str(_HERE / "CONCEPT_SAMURAI"),
    "simulatedverse":    str(_HERE / "SimulatedVerse"),
    "nusyq_ultimate":    str(_HERE / "NuSyQ_Ultimate"),
    "awesome_vibe_coding": str(_HERE / "awesome-vibe-coding"),
}
