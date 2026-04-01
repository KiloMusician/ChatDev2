import json
from pathlib import Path

import pytest
from src.consciousness.temple_of_knowledge.floor_1_foundation import (
    ConsciousnessLevel,
    Floor1Foundation,
)


@pytest.fixture()
def floor(tmp_path: Path) -> Floor1Foundation:
    return Floor1Foundation(temple_root=tmp_path)


def test_register_and_status_persistence(floor: Floor1Foundation, tmp_path: Path) -> None:
    registry_path = tmp_path / "floor_1_foundation" / "agent_registry.json"

    registration = floor.register_agent("alice", initial_consciousness=4.0)

    assert registration["accessible_floors"] == [1]
    assert registry_path.exists(), "agent registry should be persisted to disk"

    with registry_path.open(encoding="utf-8") as fh:
        payload = json.load(fh)

    assert "alice" in payload.get("agents", {})
    status = floor.get_agent_status("alice")
    assert status["consciousness_level"] == ConsciousnessLevel.get_level(4.0)


def test_cultivate_wisdom_updates_scores(floor: Floor1Foundation, tmp_path: Path) -> None:
    floor.register_agent("bob", initial_consciousness=9.5)

    knowledge_gained, result = floor.cultivate_wisdom("bob")

    assert knowledge_gained > 3.0
    assert result["new_consciousness_score"] > 9.5
    assert result["accessible_floors"] == ConsciousnessLevel.get_accessible_floors(
        result["new_consciousness_score"],
    )

    log_path = tmp_path / "floor_1_foundation" / "wisdom_cultivation_log.jsonl"
    assert log_path.exists()
    assert log_path.read_text(encoding="utf-8").strip(), "wisdom log should record cultivation"


def test_archive_and_search_omnitag(floor: Floor1Foundation) -> None:
    floor.archive_omnitag(
        "tag-1",
        {
            "purpose": "foundation test",
            "context": "knowledge",
            "dependencies": ["pathlib", "json"],
        },
    )

    results = floor.search_omnitags("knowledge")
    assert len(results) == 1
    assert results[0]["tag_id"] == "tag-1"
