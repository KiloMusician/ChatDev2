"""Unit tests for add_zeta_tags_to_quests.py quest-ZETA synchronization."""

import json
from pathlib import Path

from src.tools.add_zeta_tags_to_quests import QUEST_TO_ZETA_MAP, load_quest_log


def test_quest_to_zeta_map_is_populated() -> None:
    """Quest-to-ZETA mapping should exist and cover core phases."""
    assert len(QUEST_TO_ZETA_MAP) > 0
    assert any("Zeta0" in v for v in QUEST_TO_ZETA_MAP.values())  # Foundation phase
    assert any("Zeta2" in v for v in QUEST_TO_ZETA_MAP.values())  # Consciousness phase
    assert any("Zeta4" in v for v in QUEST_TO_ZETA_MAP.values())  # Meta-cognitive phase


def test_load_quest_log_empty_file(tmp_path: Path) -> None:
    """Loading empty quest log should return empty list."""
    quest_file = tmp_path / "empty_quests.jsonl"
    quest_file.write_text("")

    quests = load_quest_log(quest_file)
    assert quests == []


def test_load_quest_log_single_entry(tmp_path: Path) -> None:
    """Loading quest log with one entry should parse correctly."""
    quest_file = tmp_path / "quests.jsonl"
    entry = {"quest_id": "q1", "title": "Test Quest", "status": "open"}
    quest_file.write_text(json.dumps(entry))

    quests = load_quest_log(quest_file)
    assert len(quests) == 1
    assert quests[0]["quest_id"] == "q1"


def test_load_quest_log_multiple_entries(tmp_path: Path) -> None:
    """Loading quest log with multiple entries should parse all."""
    quest_file = tmp_path / "quests.jsonl"
    entries = [
        {"quest_id": "q1", "title": "Test Quest 1"},
        {"quest_id": "q2", "title": "Test Quest 2"},
        {"quest_id": "q3", "title": "Test Quest 3"},
    ]
    quest_file.write_text("\n".join(json.dumps(e) for e in entries))

    quests = load_quest_log(quest_file)
    assert len(quests) == 3
    assert quests[0]["quest_id"] == "q1"
    assert quests[2]["quest_id"] == "q3"


def test_load_quest_log_with_blank_lines(tmp_path: Path) -> None:
    """Loading quest log with blank lines should skip them."""
    quest_file = tmp_path / "quests.jsonl"
    lines = [
        json.dumps({"quest_id": "q1", "title": "Q1"}),
        "",
        json.dumps({"quest_id": "q2", "title": "Q2"}),
        "",
        "",
        json.dumps({"quest_id": "q3", "title": "Q3"}),
    ]
    quest_file.write_text("\n".join(lines))

    quests = load_quest_log(quest_file)
    assert len(quests) == 3
    assert [q["quest_id"] for q in quests] == ["q1", "q2", "q3"]


def test_zeta_mapping_has_foundation_tasks() -> None:
    """Zeta mapping should include Foundation phase (Zeta01-05) tasks."""
    foundation_quests = [q for q in QUEST_TO_ZETA_MAP.values() if q.startswith("Zeta0")]
    assert len(foundation_quests) > 0, "Should have Foundation phase tasks"


def test_zeta_mapping_has_consciousness_tasks() -> None:
    """Zeta mapping should include Consciousness phase (Zeta2x) tasks."""
    consciousness_quests = [q for q in QUEST_TO_ZETA_MAP.values() if q.startswith("Zeta2")]
    assert len(consciousness_quests) > 0, "Should have Consciousness phase tasks"


def test_zeta_mapping_has_meta_tasks() -> None:
    """Zeta mapping should include Meta-cognitive phase (Zeta4x) tasks."""
    meta_quests = [q for q in QUEST_TO_ZETA_MAP.values() if q.startswith("Zeta4")]
    assert len(meta_quests) > 0, "Should have Meta-cognitive phase tasks"
