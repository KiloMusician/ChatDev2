"""Copilot Enhancement Bridge
This module provides a lightweight, robust bridge for enriching Copilot with
NuSyQ-Hub context (quests, progress, session state) without introducing new
dependencies or fragile runtime behavior.

OmniTag: {"purpose": "copilot_enhancement_bridge", "type": "integration", "evolution_stage": "v1.1"}
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, cast

COPILOT_BRIDGE_ACTIVE = True


@dataclass(frozen=True)
class BridgeConfig:
    """Configuration for context synthesis and logging.

    Paths are resolved relative to the NuSyQ-Hub repository root.
    """

    repo_root: Path
    agents_md: Path
    progress_json: Path
    quest_log_jsonl: Path
    state_snapshot_md: Path
    log_path: Path


def _default_config() -> BridgeConfig:
    root = Path(__file__).resolve().parents[1]
    return BridgeConfig(
        repo_root=root,
        agents_md=root / "AGENTS.md",
        progress_json=root / "config" / "ZETA_PROGRESS_TRACKER.json",
        quest_log_jsonl=root / "src" / "Rosetta_Quest_System" / "quest_log.jsonl",
        state_snapshot_md=root / "state" / "reports" / "current_state.md",
        log_path=root / "copilot_enhancement_bridge.log",
    )


def log_event(message: str, *, config: BridgeConfig | None = None) -> None:
    """Append a timestamped message to the bridge log.

    Safe and UTF-8 by default, ignores I/O failures silently (non-fatal).
    """
    cfg = config or _default_config()
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        cfg.log_path.parent.mkdir(parents=True, exist_ok=True)
        with cfg.log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] {message}\n")
    except OSError:
        # Logging must never become a failure mode
        pass


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                return cast(dict[str, Any], json.load(fh))
    except (OSError, json.JSONDecodeError):
        return None
    return None


def _read_last_jsonl(path: Path) -> dict[str, Any] | None:
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                lines = [ln.strip() for ln in fh if ln.strip()]
            if not lines:
                return None
            return cast(dict[str, Any], json.loads(lines[-1]))
    except (OSError, json.JSONDecodeError):
        return None
    return None


def _read_text(path: Path, max_chars: int = 5000) -> str | None:
    try:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore")
            if len(text) > max_chars:
                return text[:max_chars] + "\n… (truncated)"
            return text
    except OSError:
        return None
    return None


def synthesize_context(*, config: BridgeConfig | None = None) -> dict[str, Any]:
    """Aggregate lightweight session context for Copilot suggestions.

    Returns a dictionary with:
    - progress: ZETA progress tracker (if present)
    - last_quest: last entry from quest_log.jsonl (if present)
    - state_snapshot: excerpt from current_state.md (if present)
    - repo_root: absolute path to NuSyQ-Hub
    """
    cfg = config or _default_config()
    context: dict[str, Any] = {
        "repo_root": str(cfg.repo_root),
        "progress": _read_json(cfg.progress_json) or {},
        "last_quest": _read_last_jsonl(cfg.quest_log_jsonl) or {},
        "state_snapshot": _read_text(cfg.state_snapshot_md) or "",
    }

    log_event("synthesize_context invoked")
    return context


class EnhancedBridge:
    """Thin facade exposing bridge utilities for easy import in other modules."""

    def __init__(self, config: BridgeConfig | None = None) -> None:
        self.config = config or _default_config()

    def synthesize_context(self) -> dict[str, Any]:
        return synthesize_context(config=self.config)

    def log(self, message: str) -> None:
        log_event(message, config=self.config)


def get_enhanced_bridge() -> EnhancedBridge:
    """Factory returning a ready-to-use bridge instance."""
    return EnhancedBridge()
