"""Test suite for Quest Log Validator.

OmniTag: {'purpose': 'testing', 'type': 'unit_tests', 'evolution_stage': 'v1.0'}
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from src.tools.quest_log_validator import QuestLogValidator


@pytest.fixture
def temp_quest_log():
    """Create temporary quest log for testing."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        quest_log = tmppath / "quest_log.jsonl"

        # Valid quest
        valid_quest = {
            "timestamp": "2025-12-16T00:00:00",
            "event": "add_quest",
            "details": {
                "id": "12345678-1234-1234-1234-123456789012",
                "title": "Zeta01: Test Quest",
                "description": "Test description",
                "questline": "Test Questline",
                "status": "pending",
                "created_at": "2025-12-16T00:00:00",
                "updated_at": "2025-12-16T00:00:00",
                "dependencies": [],
                "tags": ["Zeta01", "test"],
                "history": [],
            },
        }

        # Invalid status quest
        invalid_status = valid_quest.copy()
        invalid_status["details"] = valid_quest["details"].copy()
        invalid_status["details"]["status"] = "invalid_status"

        # Missing field quest
        missing_field = valid_quest.copy()
        missing_field["details"] = valid_quest["details"].copy()
        del missing_field["details"]["title"]

        # Valid questline
        valid_questline = {
            "timestamp": "2025-12-16T00:00:00",
            "event": "add_questline",
            "details": {
                "name": "Test Questline",
                "description": "Test description",
                "tags": ["test"],
                "quests": [],
                "created_at": "2025-12-16T00:00:00",
                "updated_at": "2025-12-16T00:00:00",
            },
        }

        with open(quest_log, "w", encoding="utf-8") as f:
            f.write(json.dumps(valid_quest) + "\n")
            f.write(json.dumps(invalid_status) + "\n")
            f.write(json.dumps(missing_field) + "\n")
            f.write(json.dumps(valid_questline) + "\n")
            f.write("INVALID JSON LINE\n")

        yield quest_log


def test_load_quest_log(temp_quest_log):
    """Test loading quest log from file."""
    validator = QuestLogValidator(quest_log_path=temp_quest_log)
    validator.load_quest_log()

    # Should load 4 valid JSON entries + 1 error for invalid JSON
    assert len(validator.entries) == 4
    assert len(validator.errors) == 1
    assert validator.errors[0]["type"] == "invalid_json"


def test_validate_valid_quest(temp_quest_log):
    """Test validation of a valid quest."""
    validator = QuestLogValidator(quest_log_path=temp_quest_log)
    validator.load_quest_log()
    validator.validate_all()

    # Valid quest should have no errors (first entry)
    valid_entry_errors = [
        e for e in validator.errors if e.get("line") == 1 and e["type"] != "invalid_json"
    ]
    assert len(valid_entry_errors) == 0


def test_validate_invalid_status(temp_quest_log):
    """Test detection of invalid status."""
    validator = QuestLogValidator(quest_log_path=temp_quest_log)
    validator.load_quest_log()
    validator.validate_all()

    # Should detect invalid status in second entry
    status_errors = [e for e in validator.errors if e["type"] == "invalid_status"]
    assert len(status_errors) == 1
    assert "invalid_status" in status_errors[0]["value"]


def test_validate_missing_required_field(temp_quest_log):
    """Test detection of missing required fields."""
    validator = QuestLogValidator(quest_log_path=temp_quest_log)
    validator.load_quest_log()
    validator.validate_all()

    # Should detect missing title in third entry
    missing_field_errors = [e for e in validator.errors if e["type"] == "missing_required_field"]
    assert len(missing_field_errors) >= 1
    assert any(e["field"] == "title" for e in missing_field_errors)


def test_validate_questline(temp_quest_log):
    """Test validation of questline entries."""
    validator = QuestLogValidator(quest_log_path=temp_quest_log)
    validator.load_quest_log()
    validator.validate_all()

    # Questline should be valid (fourth entry)
    questline_errors = [
        e for e in validator.errors if e.get("line") == 4 and e["type"] != "invalid_json"
    ]
    assert len(questline_errors) == 0


def test_zeta_mapping_suggestion():
    """Test ZETA mapping suggestions for quests without ZETA tags."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        quest_log = tmppath / "quest_log.jsonl"

        # Quest without ZETA mapping
        quest_no_zeta = {
            "event": "add_quest",
            "details": {
                "id": "12345678-1234-1234-1234-123456789012",
                "title": "Regular Quest",
                "description": "No ZETA mapping",
                "questline": "Test",
                "status": "pending",
                "created_at": "2025-12-16T00:00:00",
                "updated_at": "2025-12-16T00:00:00",
                "dependencies": [],
                "tags": ["regular"],
                "history": [],
            },
        }

        with open(quest_log, "w", encoding="utf-8") as f:
            f.write(json.dumps(quest_no_zeta) + "\n")

        validator = QuestLogValidator(quest_log_path=quest_log)
        validator.load_quest_log()
        validator.validate_all()

        # Should suggest adding ZETA mapping
        zeta_suggestions = [s for s in validator.suggestions if s["type"] == "missing_zeta_mapping"]
        assert len(zeta_suggestions) == 1


def test_generate_report(temp_quest_log):
    """Test validation report generation."""
    validator = QuestLogValidator(quest_log_path=temp_quest_log)
    validator.load_quest_log()
    validator.validate_all()

    report = validator.generate_report()

    assert "QUEST LOG VALIDATION REPORT" in report
    assert "SUMMARY" in report
    assert "HEALTH STATUS" in report
    assert str(len(validator.errors)) in report


def test_auto_fix_suggestions(temp_quest_log):
    """Test auto-fix suggestion generation."""
    validator = QuestLogValidator(quest_log_path=temp_quest_log)
    validator.load_quest_log()
    validator.validate_all()

    fixes = validator.get_auto_fix_suggestions()

    # Should have suggestions for invalid status and missing fields
    assert len(fixes) >= 1
    fix_types = [f["type"] for f in fixes]
    assert "normalize_status" in fix_types or "add_default_fields" in fix_types


def test_missing_file_handling():
    """Test graceful handling of missing quest log file."""
    validator = QuestLogValidator(quest_log_path=Path("nonexistent.jsonl"))
    validator.load_quest_log()

    assert len(validator.errors) == 1
    assert validator.errors[0]["type"] == "file_not_found"
    assert validator.errors[0]["severity"] == "critical"


def test_valid_statuses():
    """Test all valid status values are accepted."""
    valid_statuses = [
        "pending",
        "in-progress",
        "in_progress",
        "completed",
        "blocked",
        "mastered",
        "cancelled",
    ]

    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        for status in valid_statuses:
            quest_log = tmppath / f"quest_{status}.jsonl"

            quest = {
                "event": "add_quest",
                "details": {
                    "id": "12345678-1234-1234-1234-123456789012",
                    "title": "Test",
                    "description": "Test",
                    "questline": "Test",
                    "status": status,
                    "created_at": "2025-12-16T00:00:00",
                    "updated_at": "2025-12-16T00:00:00",
                    "dependencies": [],
                    "tags": [],
                    "history": [],
                },
            }

            with open(quest_log, "w", encoding="utf-8") as f:
                f.write(json.dumps(quest) + "\n")

            validator = QuestLogValidator(quest_log_path=quest_log)
            validator.load_quest_log()
            validator.validate_all()

            # No status errors for valid statuses
            status_errors = [e for e in validator.errors if e["type"] == "invalid_status"]
            assert len(status_errors) == 0, f"Valid status '{status}' flagged as invalid"


def test_timestamp_validation():
    """Test timestamp format validation."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        quest_log = tmppath / "quest_log.jsonl"

        quest_invalid_timestamp = {
            "event": "add_quest",
            "details": {
                "id": "12345678-1234-1234-1234-123456789012",
                "title": "Test",
                "description": "Test",
                "questline": "Test",
                "status": "pending",
                "created_at": "invalid_timestamp",
                "updated_at": "2025-12-16T00:00:00",
                "dependencies": [],
                "tags": [],
                "history": [],
            },
        }

        with open(quest_log, "w", encoding="utf-8") as f:
            f.write(json.dumps(quest_invalid_timestamp) + "\n")

        validator = QuestLogValidator(quest_log_path=quest_log)
        validator.load_quest_log()
        validator.validate_all()

        timestamp_errors = [e for e in validator.errors if e["type"] == "invalid_timestamp"]
        assert len(timestamp_errors) >= 1


def test_invalid_field_types():
    """Test detection of invalid field types."""
    with TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        quest_log = tmppath / "quest_log.jsonl"

        quest_wrong_types = {
            "event": "add_quest",
            "details": {
                "id": "12345678-1234-1234-1234-123456789012",
                "title": "Test",
                "description": "Test",
                "questline": "Test",
                "status": "pending",
                "created_at": "2025-12-16T00:00:00",
                "updated_at": "2025-12-16T00:00:00",
                "dependencies": "not_a_list",  # Should be list
                "tags": "not_a_list",  # Should be list
                "history": [],
            },
        }

        with open(quest_log, "w", encoding="utf-8") as f:
            f.write(json.dumps(quest_wrong_types) + "\n")

        validator = QuestLogValidator(quest_log_path=quest_log)
        validator.load_quest_log()
        validator.validate_all()

        type_errors = [e for e in validator.errors if e["type"] == "invalid_field_type"]
        assert len(type_errors) >= 2  # Dependencies and tags
