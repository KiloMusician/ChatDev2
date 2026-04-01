"""Resilience stubs (Phase 8 prep)."""

from __future__ import annotations

from typing import Any


def checkpoint(state: dict[str, Any], store: list[dict[str, Any]]) -> None:
    store.append(state.copy())


def retry_if_failed(result: dict[str, Any], attempts: int = 1) -> bool:
    return bool(result.get("error")) and attempts > 0


def degraded_mode(enabled: bool) -> dict[str, Any]:
    return {"degraded": enabled, "note": "use local model + basic tests"}
