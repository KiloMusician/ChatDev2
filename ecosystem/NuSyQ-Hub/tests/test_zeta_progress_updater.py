"""Test suite for ZETA Progress Auto-Updater.

OmniTag: {'purpose': 'testing', 'type': 'unit_tests', 'evolution_stage': 'v1.0'}
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from src.tools.zeta_progress_updater import ZETAProgressUpdater


@pytest.fixture
def temp_files():
    """Create temporary quest log and tracker files for testing."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Sample quest log
        quest_log = tmppath / "quest_log.jsonl"
        with open(quest_log, "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": "2025-12-16T00:00:00",
                        "event": "add_quest",
                        "details": {
                            "id": "test-1",
                            "title": "Zeta01: Foundation Test",
                            "status": "completed",
                            "tags": ["Zeta01", "foundation"],
                        },
                    }
                )
                + "\n"
            )
            f.write(
                json.dumps(
                    {
                        "timestamp": "2025-12-16T00:00:01",
                        "event": "add_quest",
                        "details": {
                            "id": "test-2",
                            "title": "Regular Quest Without ZETA",
                            "status": "pending",
                            "tags": ["regular"],
                        },
                    }
                )
                + "\n"
            )

        # Sample tracker
        tracker = tmppath / "tracker.json"
        with open(tracker, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "phases": {
                        "phase_1": {
                            "name": "Foundation",
                            "tasks": [
                                {
                                    "id": "Zeta01",
                                    "name": "Foundation Test",
                                    "status": "○",
                                    "state": "PENDING",
                                }
                            ],
                        }
                    }
                },
                f,
            )

        yield quest_log, tracker


def test_load_quest_log(temp_files):
    """Test loading quests from JSONL file."""
    quest_log, tracker = temp_files
    updater = ZETAProgressUpdater(quest_log_path=quest_log, tracker_path=tracker)

    updater.load_quest_log()

    assert len(updater.quests) == 2
    assert updater.quests[0]["title"] == "Zeta01: Foundation Test"


def test_load_tracker(temp_files):
    """Test loading ZETA progress tracker."""
    quest_log, tracker = temp_files
    updater = ZETAProgressUpdater(quest_log_path=quest_log, tracker_path=tracker)

    updater.load_tracker()

    assert "phases" in updater.tracker
    assert "phase_1" in updater.tracker["phases"]


def test_map_quest_to_zeta(temp_files):
    """Test mapping quest to ZETA task ID."""
    quest_log, tracker = temp_files
    updater = ZETAProgressUpdater(quest_log_path=quest_log, tracker_path=tracker)

    # Quest with explicit tag
    quest_with_tag = {"title": "Test Quest", "tags": ["Zeta42"]}
    assert updater.map_quest_to_zeta(quest_with_tag) == "Zeta42"

    # Quest with ZETA in title
    quest_with_title = {"title": "Zeta05: Foundation Quest", "tags": []}
    assert updater.map_quest_to_zeta(quest_with_title) == "Zeta05"

    # Quest without ZETA reference
    regular_quest = {"title": "Regular Quest", "tags": ["regular"]}
    assert updater.map_quest_to_zeta(regular_quest) is None


def test_get_status_symbol(temp_files):
    """Test status symbol mapping."""
    quest_log, tracker = temp_files
    updater = ZETAProgressUpdater(quest_log_path=quest_log, tracker_path=tracker)

    assert updater.get_status_symbol("completed") == "✓"
    assert updater.get_status_symbol("in-progress") == "◐"
    assert updater.get_status_symbol("pending") == "○"
    assert updater.get_status_symbol("blocked") == "⊗"
    assert updater.get_status_symbol("mastered") == "●"
    assert updater.get_status_symbol("unknown") == "○"  # Default


def test_full_sync_workflow(temp_files):
    """Test complete synchronization workflow."""
    quest_log, tracker = temp_files
    updater = ZETAProgressUpdater(quest_log_path=quest_log, tracker_path=tracker)

    # Run full sync
    updater.load_quest_log()
    updater.load_tracker()
    updater.sync_quests_to_tracker()
    updater.save_tracker()

    # Verify backup created
    backup_path = tracker.with_suffix(".json.bak")
    assert backup_path.exists()

    # Verify tracker updated
    with open(tracker, encoding="utf-8") as f:
        updated_tracker = json.load(f)

    # Check that Zeta01 was updated
    zeta01_task = updated_tracker["phases"]["phase_1"]["tasks"][0]
    assert zeta01_task["status"] == "✓"  # Completed
    assert zeta01_task["state"] == "COMPLETED"


def test_generate_summary(temp_files):
    """Test summary generation."""
    quest_log, tracker = temp_files
    updater = ZETAProgressUpdater(quest_log_path=quest_log, tracker_path=tracker)

    updater.load_quest_log()
    updater.load_tracker()

    summary = updater.generate_summary()

    assert "total_quests" in summary
    assert summary["total_quests"] == 2
    assert "completion_by_phase" in summary
    assert "Foundation" in str(summary["completion_by_phase"]["phase_1"]["name"])


def test_invalid_json_handling(temp_files):
    """Test handling of invalid JSON lines in quest log."""
    quest_log, tracker = temp_files

    # Add invalid line
    with open(quest_log, "a", encoding="utf-8") as f:
        f.write("INVALID JSON LINE\n")

    updater = ZETAProgressUpdater(quest_log_path=quest_log, tracker_path=tracker)
    updater.load_quest_log()

    # Should load only valid quests
    assert len(updater.quests) == 2


def test_missing_files():
    """Test handling of missing quest log or tracker files."""
    updater = ZETAProgressUpdater(
        quest_log_path=Path("nonexistent_quest.jsonl"),
        tracker_path=Path("nonexistent_tracker.json"),
    )

    # Should not crash
    updater.load_quest_log()
    updater.load_tracker()

    assert len(updater.quests) == 0
    assert updater.tracker == {}
