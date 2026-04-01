"""Unit coverage for src.tools.work_queue_executor."""

from __future__ import annotations

import json

import pytest

from src.tools.work_queue_executor import (
    KEY_DURATION_SECONDS,
    KEY_ERROR,
    KEY_ITEMS,
    KEY_OUTPUT,
    KEY_STATUS,
    STATUS_COMPLETED,
    STATUS_EMPTY,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
    STATUS_NO_QUEUED_ITEMS,
    STATUS_QUEUED,
    STATUS_SUCCESS,
    WorkQueueExecutor,
)


def _write_queue(executor: WorkQueueExecutor, payload: dict) -> None:
    executor.work_queue_path.parent.mkdir(parents=True, exist_ok=True)
    executor.work_queue_path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_work_queue_missing_file_returns_empty(tmp_path):
    executor = WorkQueueExecutor(repo_root=tmp_path)
    assert executor._load_work_queue() == {KEY_ITEMS: []}


def test_update_item_status_persists_to_queue(tmp_path):
    executor = WorkQueueExecutor(repo_root=tmp_path)
    _write_queue(
        executor,
        {
            KEY_ITEMS: [
                {"id": "item-1", KEY_STATUS: STATUS_QUEUED},
                {"id": "item-2", KEY_STATUS: STATUS_IN_PROGRESS},
            ]
        },
    )

    executor._update_item_status("item-1", STATUS_COMPLETED, note="done")
    updated = json.loads(executor.work_queue_path.read_text(encoding="utf-8"))

    item_1 = next(i for i in updated[KEY_ITEMS] if i["id"] == "item-1")
    assert item_1[KEY_STATUS] == STATUS_COMPLETED
    assert item_1["last_note"] == "done"
    assert "last_updated" in item_1
    assert "last_updated" in updated


@pytest.mark.asyncio
async def test_execute_next_item_returns_empty_when_no_items(tmp_path):
    executor = WorkQueueExecutor(repo_root=tmp_path)
    _write_queue(executor, {KEY_ITEMS: []})

    result = await executor.execute_next_item()
    assert result[KEY_STATUS] == STATUS_EMPTY


@pytest.mark.asyncio
async def test_execute_next_item_returns_no_queued_items(tmp_path):
    executor = WorkQueueExecutor(repo_root=tmp_path)
    _write_queue(
        executor,
        {KEY_ITEMS: [{"id": "done-1", "title": "Done", KEY_STATUS: STATUS_COMPLETED}]},
    )

    result = await executor.execute_next_item()
    assert result[KEY_STATUS] == STATUS_NO_QUEUED_ITEMS


@pytest.mark.asyncio
async def test_execute_item_capability_routed_fails_without_description(tmp_path):
    executor = WorkQueueExecutor(repo_root=tmp_path)
    result = await executor._execute_item_capability_routed({"id": "missing-description"})

    assert result[KEY_STATUS] == STATUS_FAILED
    assert "missing title/description" in result[KEY_ERROR]


@pytest.mark.asyncio
async def test_execute_item_uses_legacy_fallback_when_enabled(tmp_path, monkeypatch):
    executor = WorkQueueExecutor(repo_root=tmp_path)

    async def fail_routed(_item):
        return {KEY_STATUS: STATUS_FAILED, KEY_ERROR: "router_failed"}

    async def pass_legacy(_item):
        return {KEY_STATUS: STATUS_SUCCESS, KEY_OUTPUT: "legacy_ok"}

    monkeypatch.setattr(executor, "_execute_item_capability_routed", fail_routed)
    monkeypatch.setattr(executor, "_execute_item_legacy", pass_legacy)

    result = await executor._execute_item({"title": "Fallback path", "description": "run fallback"})
    assert result[KEY_STATUS] == STATUS_SUCCESS
    assert result[KEY_OUTPUT] == "legacy_ok"
    assert "fallback_from" in result
    assert result[KEY_DURATION_SECONDS] >= 0


@pytest.mark.asyncio
async def test_get_queue_status_counts_states(tmp_path):
    executor = WorkQueueExecutor(repo_root=tmp_path)
    _write_queue(
        executor,
        {
            KEY_ITEMS: [
                {"id": "q", KEY_STATUS: STATUS_QUEUED},
                {"id": "ip", KEY_STATUS: STATUS_IN_PROGRESS},
                {"id": "c", KEY_STATUS: STATUS_COMPLETED},
                {"id": "f", KEY_STATUS: STATUS_FAILED},
            ]
        },
    )

    result = await executor.get_queue_status()
    assert result[KEY_STATUS] == STATUS_SUCCESS
    assert result["queued"] == 1
    assert result["in_progress"] == 1
    assert result["completed"] == 1
    assert result["failed"] == 1


def test_infer_task_type_uses_keyword_heuristics(tmp_path):
    executor = WorkQueueExecutor(repo_root=tmp_path)
    assert (
        executor._infer_task_type({"title": "Generate scaffold", "description": ""}) == "generate"
    )
    assert (
        executor._infer_task_type({"title": "Review lint warnings", "description": ""}) == "review"
    )
    assert executor._infer_task_type({"title": "Fix crash", "description": ""}) == "debug"
    assert executor._infer_task_type({"title": "Smoke test suite", "description": ""}) == "test"
    assert executor._infer_task_type({"title": "Write docs", "description": ""}) == "document"
    assert executor._infer_task_type({"title": "Plan roadmap", "description": ""}) == "plan"
    assert executor._infer_task_type({"title": "Random task", "description": ""}) == "analyze"


def test_map_priority_normalizes_values(tmp_path):
    executor = WorkQueueExecutor(repo_root=tmp_path)
    assert executor._map_priority("critical") == "CRITICAL"
    assert executor._map_priority("medium") == "NORMAL"
    assert executor._map_priority("low") == "LOW"
    assert executor._map_priority(None) == "NORMAL"


def test_infer_target_system_precedence(tmp_path, monkeypatch):
    executor = WorkQueueExecutor(repo_root=tmp_path)

    assert executor._infer_target_system({"target_system": "chatdev"}, "analyze") == "chatdev"

    monkeypatch.setenv("NUSYQ_WORK_QUEUE_TARGET_SYSTEM", "ollama")
    assert executor._infer_target_system({}, "generate") == "ollama"

    monkeypatch.delenv("NUSYQ_WORK_QUEUE_TARGET_SYSTEM")
    assert executor._infer_target_system({}, "generate") == "chatdev"
    assert executor._infer_target_system({}, "debug") == "quantum_resolver"
    assert executor._infer_target_system({}, "analyze") == "auto"
