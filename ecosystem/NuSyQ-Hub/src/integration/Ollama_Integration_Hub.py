"""Ollama Integration Hub — model selection, performance monitoring, conversation management."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

FALLBACK_MODEL = "qwen2.5-coder:14b"

_INTENT_PATTERNS: dict[str, list[str]] = {
    "code_analysis": [r"\bdebug\b", r"\bfunction\b", r"\bcode\b", r"\berror\b", r"\bbug\b"],
    "documentation": [r"\btutorial\b", r"\bdocument\b", r"\bguide\b", r"\bexplain\b"],
    "conversation": [r"\bhello\b", r"\bhi\b", r"\bchat\b"],
}


# ─── Data models ──────────────────────────────────────────────────────────────


@dataclass
class OllamaModel:
    name: str
    size: int
    digest: str
    modified_at: str
    family: str
    capabilities: list[str] = field(default_factory=list)
    performance_rating: float = 0.0


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


# ─── Intelligent model selection ─────────────────────────────────────────────


class IntelligentModelSelector:
    def select_optimal_model(self, available: dict[str, OllamaModel], intent: str) -> str:
        best_name, best_score = FALLBACK_MODEL, -1.0
        for name, model in available.items():
            score = model.performance_rating
            if intent in model.capabilities:
                score += 1.0
            if score > best_score:
                best_score, best_name = score, name
        return best_name

    def analyze_message_intent(self, message: str) -> str:
        lower = message.lower()
        for intent, patterns in _INTENT_PATTERNS.items():
            if any(re.search(p, lower) for p in patterns):
                return intent
        return "conversation"


# ─── Performance monitoring ───────────────────────────────────────────────────


class PerformanceMonitor:
    def __init__(self) -> None:
        self._samples: list[dict[str, Any]] = []

    def record(self, metric: str, value: float) -> None:
        self._samples.append({"metric": metric, "value": value})

    def _calculate_trends(self) -> dict[str, Any]:
        if len(self._samples) < 2:
            return {"success": False, "status": "insufficient_data"}
        values = [s["value"] for s in self._samples]
        return {"success": True, "status": "ok", "trend": values[-1] - values[0]}


# ─── Conversation management ──────────────────────────────────────────────────

_SESSION_ROOT = Path.home() / ".nusyq" / "conversations"


class ConversationManager:
    def __init__(self, session_id: str, storage_root: Path | None = None) -> None:
        self.session_id = session_id
        root = storage_root or _SESSION_ROOT
        self.persistent_storage_path = root / session_id
        self.persistent_storage_path.mkdir(parents=True, exist_ok=True)
        self.conversation_history: list[ChatMessage] = []
        self.conversation_themes: list[str] = []
        self.cross_session_memory: list[dict[str, Any]] = []
        self.conversation_summaries: dict[str, Any] = {}
        self._load_session()

    # ------------------------------------------------------------------
    def add_message(self, msg: ChatMessage) -> None:
        self.conversation_history.append(msg)
        self._detect_themes(msg.content)
        if len(self.conversation_history) % 10 == 0:
            self._summarize_chunk()

    def get_enhanced_context_messages(
        self, max_messages: int = 20, include_summary: bool = True
    ) -> list[dict[str, Any]]:
        recent = self.conversation_history[-max_messages:]
        return [{"role": m.role, "content": m.content} for m in recent]

    def get_contextual_memory(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        return self.cross_session_memory[:limit]

    def save_to_file(self) -> Path:
        self._auto_save_session()
        return self.persistent_storage_path / "session_data.json"

    def _auto_save_session(self) -> None:
        data = {
            "session_id": self.session_id,
            "themes": self.conversation_themes,
            "memories": self.cross_session_memory,
            "summaries": self.conversation_summaries,
            "history": [{"role": m.role, "content": m.content} for m in self.conversation_history],
        }
        (self.persistent_storage_path / "session_data.json").write_text(json.dumps(data, indent=2))

    # ------------------------------------------------------------------
    def _load_session(self) -> None:
        path = self.persistent_storage_path / "session_data.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text())
            self.conversation_themes = data.get("themes", [])
            self.cross_session_memory = data.get("memories", [])
            self.conversation_summaries = data.get("summaries", {})
            self.conversation_history = [
                ChatMessage(role=m["role"], content=m["content"]) for m in data.get("history", [])
            ]
        except Exception:
            pass

    def _detect_themes(self, text: str) -> None:
        for theme in ("data", "code", "pipeline", "analysis", "debug", "research"):
            if theme in text.lower() and theme not in self.conversation_themes:
                self.conversation_themes.append(theme)

    def _summarize_chunk(self) -> None:
        chunk = self.conversation_history[-10:]
        key = f"chunk_{len(self.conversation_summaries)}"
        self.conversation_summaries[key] = {
            "messages": len(chunk),
            "first": chunk[0].content[:80] if chunk else "",
        }
