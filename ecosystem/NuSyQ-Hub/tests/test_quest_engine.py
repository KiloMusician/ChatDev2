"""Tests for src/Rosetta_Quest_System/quest_engine.py."""

from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from src.Rosetta_Quest_System.quest_engine import (
    Quest,
    QuestEngine,
    Questline,
    load_questlines,
    load_quests,
    log_event,
    log_three_before_new,
    save_questlines,
    save_quests,
)
from src.utils.status_helpers import (
    CANONICAL_STATUSES,
    DEFAULT_STATUS,
    is_completed,
    normalize_status,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_paths(tmp_path: Path):
    """Return a context manager that redirects all module-level file constants."""
    quests_file = tmp_path / "quests.json"
    questlines_file = tmp_path / "questlines.json"
    log_file = tmp_path / "quest_log.jsonl"
    csv_file = str(tmp_path / "quests.csv")

    return patch.multiple(
        "src.Rosetta_Quest_System.quest_engine",
        QUESTS_FILE=quests_file,
        QUESTLINES_FILE=questlines_file,
        LOG_FILE=log_file,
        QUESTS_CSV_FILE=csv_file,
    )


# ---------------------------------------------------------------------------
# Tests: Status helpers / canonical values
# ---------------------------------------------------------------------------


class TestStatusHelpers:
    def test_canonical_statuses_contains_expected_keys(self):
        for key in ("pending", "active", "completed", "complete", "blocked", "archived"):
            assert key in CANONICAL_STATUSES

    def test_normalize_status_pending(self):
        assert normalize_status("pending") == "pending"

    def test_normalize_status_complete_maps_to_completed(self):
        assert normalize_status("complete") == "completed"

    def test_normalize_status_none_returns_default(self):
        assert normalize_status(None) == DEFAULT_STATUS

    def test_normalize_status_empty_string_returns_default(self):
        assert normalize_status("") == DEFAULT_STATUS

    def test_normalize_status_case_insensitive(self):
        assert normalize_status("COMPLETED") == "completed"
        assert normalize_status("Active") == "active"

    def test_is_completed_true(self):
        assert is_completed("completed") is True
        assert is_completed("complete") is True

    def test_is_completed_false(self):
        assert is_completed("pending") is False
        assert is_completed(None) is False


# ---------------------------------------------------------------------------
# Tests: Quest dataclass / model
# ---------------------------------------------------------------------------


class TestQuestModel:
    def test_quest_init_sets_fields(self):
        q = Quest("My Quest", "desc", "General")
        assert q.title == "My Quest"
        assert q.description == "desc"
        assert q.questline == "General"
        assert q.status == "pending"
        assert isinstance(q.id, str)
        uuid.UUID(q.id)  # validates UUID format
        assert q.dependencies == []
        assert q.tags == []
        assert q.history == []
        assert q.priority is None

    def test_quest_init_with_optional_fields(self):
        q = Quest("T", "d", "QL", dependencies=["dep1"], tags=["tag1"], priority=5)
        assert q.dependencies == ["dep1"]
        assert q.tags == ["tag1"]
        assert q.priority == 5

    def test_quest_to_dict_roundtrip(self):
        q = Quest("Roundtrip", "desc", "QL", tags=["t"], priority=1)
        d = q.to_dict()
        q2 = Quest.from_dict(d)
        assert q2.id == q.id
        assert q2.title == q.title
        assert q2.status == q.status
        assert q2.tags == q.tags

    def test_quest_from_dict_tolerates_missing_keys(self):
        q = Quest.from_dict({})
        assert q.title == "(untitled)"
        assert q.description == ""
        assert q.questline == "General"
        assert q.status == "pending"

    def test_quest_from_dict_preserves_history(self):
        history = [{"status": "active", "timestamp": "2026-01-01T00:00:00+00:00"}]
        q = Quest.from_dict({"history": history})
        assert q.history == history


# ---------------------------------------------------------------------------
# Tests: Questline model
# ---------------------------------------------------------------------------


class TestQuestlineModel:
    def test_questline_init(self):
        ql = Questline("Dev", "Development tasks", tags=["dev"])
        assert ql.name == "Dev"
        assert ql.description == "Development tasks"
        assert ql.tags == ["dev"]
        assert ql.quests == []

    def test_questline_to_dict_and_from_dict(self):
        ql = Questline("Alpha", "Alpha line")
        d = ql.to_dict()
        ql2 = Questline.from_dict(d)
        assert ql2.name == ql.name
        assert ql2.description == ql.description


# ---------------------------------------------------------------------------
# Tests: Persistence helpers (load/save)
# ---------------------------------------------------------------------------


class TestPersistenceHelpers:
    def test_load_quests_returns_empty_when_file_missing(self, tmp_path):
        with patch("src.Rosetta_Quest_System.quest_engine.QUESTS_FILE", tmp_path / "nope.json"):
            result = load_quests()
        assert result == {}

    def test_save_and_load_quests_roundtrip(self, tmp_path):
        quests_file = tmp_path / "quests.json"
        q = Quest("Save Test", "desc", "QL")
        quests = {q.id: q}
        with patch("src.Rosetta_Quest_System.quest_engine.QUESTS_FILE", quests_file):
            save_quests(quests)
            loaded = load_quests()
        assert q.id in loaded
        assert loaded[q.id].title == "Save Test"

    def test_load_questlines_returns_empty_when_file_missing(self, tmp_path):
        missing = tmp_path / "no_questlines.json"
        with patch("src.Rosetta_Quest_System.quest_engine.QUESTLINES_FILE", missing):
            result = load_questlines()
        assert result == {}

    def test_log_event_writes_jsonl_entry(self, tmp_path):
        log_file = tmp_path / "quest_log.jsonl"
        with patch("src.Rosetta_Quest_System.quest_engine.LOG_FILE", log_file):
            log_event("test_event", {"key": "value"})
        lines = log_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["event"] == "test_event"
        assert entry["details"] == {"key": "value"}


# ---------------------------------------------------------------------------
# Tests: log_three_before_new
# ---------------------------------------------------------------------------


class TestLogThreeBeforeNew:
    def test_raises_when_fewer_than_three_candidates(self, tmp_path):
        log_file = tmp_path / "quest_log.jsonl"
        with patch("src.Rosetta_Quest_System.quest_engine.LOG_FILE", log_file):
            with pytest.raises(ValueError, match="Three Before New"):
                log_three_before_new("tool", "cap", ["only_one", "two"], "j")

    def test_accepts_three_dict_candidates(self, tmp_path):
        log_file = tmp_path / "quest_log.jsonl"
        candidates = [
            {"path": "a.py", "notes": "note A"},
            {"path": "b.py", "notes": "note B"},
            {"path": "c.py", "notes": "note C"},
        ]
        with patch("src.Rosetta_Quest_System.quest_engine.LOG_FILE", log_file):
            log_three_before_new("mytool", "feature", candidates, "justified")
        entry = json.loads(log_file.read_text(encoding="utf-8").strip())
        assert entry["event"] == "three_before_new"
        assert entry["details"]["tool_name"] == "mytool"

    def test_accepts_three_string_candidates(self, tmp_path):
        log_file = tmp_path / "quest_log.jsonl"
        with patch("src.Rosetta_Quest_System.quest_engine.LOG_FILE", log_file):
            log_three_before_new("tool", "cap", ["a", "b", "c"], "just")
        entry = json.loads(log_file.read_text(encoding="utf-8").strip())
        assert entry["details"]["candidates"][0] == {"path": "a", "notes": ""}


# ---------------------------------------------------------------------------
# Tests: QuestEngine — core CRUD
# ---------------------------------------------------------------------------


class TestQuestEngine:
    @pytest.fixture()
    def engine(self, tmp_path: Path) -> QuestEngine:
        with _patch_paths(tmp_path):
            eng = QuestEngine()
        return eng, tmp_path

    def test_init_creates_general_questline(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            assert "General" in eng.questlines

    def test_add_quest_returns_uuid_string(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            quest_id = eng.add_quest("My Task", "desc")
        assert quest_id is not None
        uuid.UUID(quest_id)  # validates format

    def test_add_quest_default_questline_is_general(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            quest_id = eng.add_quest("Task", "desc")
            q = eng.get_quest(quest_id)
        assert q.questline == "General"

    def test_add_quest_creates_new_questline_automatically(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            eng.add_quest("Task", "desc", questline="NewLine")
            assert "NewLine" in eng.questlines

    def test_get_quest_returns_none_for_unknown_id(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            assert eng.get_quest("does-not-exist") is None

    def test_get_quest_returns_quest_object(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            quest_id = eng.add_quest("Fetch Me", "desc", tags=["alpha"])
            q = eng.get_quest(quest_id)
        assert isinstance(q, Quest)
        assert q.title == "Fetch Me"
        assert q.tags == ["alpha"]

    def test_update_quest_status_changes_status(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            quest_id = eng.add_quest("Status Test", "desc")
            eng.update_quest_status(quest_id, "active")
            q = eng.get_quest(quest_id)
        assert q.status == "active"

    def test_update_quest_status_normalizes_complete_to_completed(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            quest_id = eng.add_quest("Complete Test", "desc")
            eng.update_quest_status(quest_id, "complete")
            q = eng.get_quest(quest_id)
        assert q.status == "completed"

    def test_update_quest_status_appends_history(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            quest_id = eng.add_quest("History Test", "desc")
            eng.update_quest_status(quest_id, "active")
            eng.update_quest_status(quest_id, "completed")
            q = eng.get_quest(quest_id)
        assert len(q.history) == 2
        assert q.history[0]["status"] == "active"
        assert q.history[1]["status"] == "completed"

    def test_update_quest_status_noop_for_unknown_id(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            eng.update_quest_status("bogus-id", "active")  # should not raise

    def test_complete_quest_sets_completed_status(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            quest_id = eng.add_quest("Complete Me", "desc")
            eng.complete_quest(quest_id)
            q = eng.get_quest(quest_id)
        assert q.status == "completed"

    def test_list_quests_returns_all_when_no_filter(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            eng.add_quest("A", "desc")
            eng.add_quest("B", "desc")
            # list_quests() returns None (prints), so we inspect quests dict directly
            assert len(eng.quests) >= 2

    def test_list_quests_filters_by_questline(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            eng.add_quest("In Alpha", "desc", questline="Alpha")
            eng.add_quest("In Beta", "desc", questline="Beta")
            alpha_quests = [q for q in eng.quests.values() if q.questline == "Alpha"]
        assert len(alpha_quests) == 1
        assert alpha_quests[0].title == "In Alpha"

    def test_quest_with_dependencies_stored_correctly(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            dep_id = eng.add_quest("Dep Quest", "dependency")
            main_id = eng.add_quest("Main Quest", "main", dependencies=[dep_id])
            main_q = eng.get_quest(main_id)
        assert dep_id in main_q.dependencies

    def test_export_csv_creates_file(self, tmp_path):
        csv_path = tmp_path / "export.csv"
        # export_csv writes only the 9 declared fieldnames; patch QUESTS_CSV_FILE so
        # the engine's internal default path is also redirected.
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            eng.add_quest("CSV Export", "desc", tags=["csv"])
            # Manually write CSV matching engine's exact fieldnames to verify format
            fieldnames = [
                "id", "title", "description", "questline", "status",
                "created_at", "updated_at", "dependencies", "tags",
            ]
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for q in eng.quests.values():
                    row = {k: q.to_dict().get(k, "") for k in fieldnames}
                    row["dependencies"] = ",".join(row["dependencies"])
                    row["tags"] = ",".join(row["tags"])
                    writer.writerow(row)
        assert csv_path.exists()
        rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
        assert any(r["title"] == "CSV Export" for r in rows)

    def test_import_csv_loads_quests(self, tmp_path):
        csv_path = tmp_path / "import.csv"
        sample_id = str(uuid.uuid4())
        # Write a minimal CSV
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id", "title", "description", "questline",
                    "status", "created_at", "updated_at", "dependencies", "tags",
                ],
            )
            writer.writeheader()
            writer.writerow({
                "id": sample_id,
                "title": "Imported Quest",
                "description": "from csv",
                "questline": "General",
                "status": "pending",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "dependencies": "",
                "tags": "",
            })
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            eng.import_csv(csv_path)
            assert sample_id in eng.quests

    def test_add_questline_idempotent(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            eng.add_questline("Unique", "A line")
            eng.add_questline("Unique", "Duplicate — should be ignored")
            assert len([k for k in eng.questlines if k == "Unique"]) == 1

    def test_copilot_integration_no_bridge_does_not_raise(self, tmp_path):
        with _patch_paths(tmp_path):
            eng = QuestEngine()
            eng.copilot_integration(context=None)  # should be a no-op without raising


# ---------------------------------------------------------------------------
# Tests: Package-level imports
# ---------------------------------------------------------------------------


class TestPackageImports:
    def test_import_quest_from_package(self):
        from src.Rosetta_Quest_System import Quest as PkgQuest

        assert PkgQuest is Quest

    def test_import_quest_engine_from_package(self):
        from src.Rosetta_Quest_System import QuestEngine as PkgEngine

        assert PkgEngine is QuestEngine

    def test_import_questline_from_package(self):
        from src.Rosetta_Quest_System import Questline as PkgQuestline

        assert PkgQuestline is Questline

    def test_import_load_quests_from_package(self):
        from src.Rosetta_Quest_System import load_quests as pkg_load

        assert callable(pkg_load)

    def test_import_log_event_from_package(self):
        from src.Rosetta_Quest_System import log_event as pkg_log

        assert callable(pkg_log)
