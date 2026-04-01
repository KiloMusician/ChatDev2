"""Multi-metric voting & cross-model diffing (Phase 7)."""

from __future__ import annotations

from typing import Any


def vote_responses(responses: list[dict[str, Any]]) -> dict[str, Any]:
    """Simplified vote: choose first non-error, include all."""
    winner = next((r for r in responses if not r.get("error")), responses[0] if responses else {})
    return {"winner": winner, "votes": responses}


def diff_responses(a: str, b: str) -> dict[str, Any]:
    """Very small diff indicator for cross-model checks."""
    return {"same": a.strip() == b.strip(), "len_a": len(a), "len_b": len(b)}
