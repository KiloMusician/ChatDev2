"""Compatibility ai package for lightweight test stubs."""

__all__ = [
    "claude_copilot_orchestrator",
    "ollama_chatdev_integrator",
]
import os
from pathlib import Path

# Ensure ai.* modules under src/ai are discoverable when tests import top-level ai
_repo_root = Path(__file__).resolve().parents[1]
_src_ai = str(_repo_root / "src" / "ai")
if os.path.isdir(_src_ai):
    # Prepend to package search path so imports like 'ai.ollama_hub' find src/ai/ollama_hub.py
    __path__.insert(0, _src_ai)
