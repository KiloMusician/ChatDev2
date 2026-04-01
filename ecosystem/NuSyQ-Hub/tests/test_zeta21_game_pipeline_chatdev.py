"""Unit tests for ChatDev-backed creation mode in ZETA21 game pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from src.game_development.zeta21_game_pipeline import GameDevPipeline


class _FakeChatDevRouter:
    def __init__(self, result: dict[str, object]) -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    def route_task(
        self,
        task_description: str,
        codebase_issues: list[dict[str, object]] | None = None,
        priority: str | int | None = None,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "task_description": task_description,
                "codebase_issues": codebase_issues,
                "priority": priority,
            }
        )
        return self.result


def test_create_new_game_project_chatdev_mode_routes_and_persists_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pipeline = GameDevPipeline(workspace_path=tmp_path)
    fake_router = _FakeChatDevRouter(
        {"success": True, "status": "success", "task_id": "chatdev_task_123"}
    )
    monkeypatch.setattr(pipeline, "_get_chatdev_router", lambda: fake_router)

    result = pipeline.create_new_game_project(
        project_name="chatdev_game",
        framework="pygame",
        creation_mode="chatdev",
        game_brief="A puzzle game with adaptive difficulty",
    )

    assert result["creation_mode"] == "chatdev"
    assert result["chatdev_task_id"] == "chatdev_task_123"
    assert len(fake_router.calls) == 1
    assert "chatdev_game" in str(fake_router.calls[0]["task_description"])

    project_path = tmp_path / "src" / "games" / "chatdev_game"
    metadata = json.loads((project_path / "project.json").read_text(encoding="utf-8"))
    assert metadata["creation_mode"] == "chatdev"
    assert metadata["chatdev_task_id"] == "chatdev_task_123"
    assert (project_path / "CHATDEV_REQUEST.md").exists()


def test_create_new_game_project_chatdev_mode_raises_and_cleans_on_route_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pipeline = GameDevPipeline(workspace_path=tmp_path)
    fake_router = _FakeChatDevRouter({"success": False, "status": "failed", "error": "boom"})
    monkeypatch.setattr(pipeline, "_get_chatdev_router", lambda: fake_router)

    with pytest.raises(RuntimeError):
        pipeline.create_new_game_project(
            project_name="failed_chatdev_game",
            framework="pygame",
            creation_mode="chatdev",
        )

    assert not (tmp_path / "src" / "games" / "failed_chatdev_game").exists()


def test_create_new_game_project_rejects_unknown_creation_mode(tmp_path: Path) -> None:
    pipeline = GameDevPipeline(workspace_path=tmp_path)

    with pytest.raises(ValueError, match="creation_mode"):
        pipeline.create_new_game_project(
            project_name="invalid_mode_game",
            framework="pygame",
            creation_mode="unknown",
        )
