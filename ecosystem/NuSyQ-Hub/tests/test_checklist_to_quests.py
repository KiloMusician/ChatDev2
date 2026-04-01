import json
from pathlib import Path

from scripts.checklist_to_quests import (
    append_checklist_entries,
    build_checklist_entry,
    read_checklist_items,
)


def test_read_checklist_items(tmp_path: Path) -> None:
    checklist = tmp_path / "checklist.md"
    checklist.write_text(
        "- [ ] First task\n- [x] Already finished\n  - [ ] Nested task\n- [ ] Second task\n"
    )

    items = read_checklist_items(checklist)

    assert items == ["First task", "Nested task", "Second task"]


def test_append_checklist_entries(tmp_path: Path) -> None:
    checklist = tmp_path / "checklist.md"
    checklist.write_text("- [ ] Sync setup docs\n- [ ] Improve diagnostics\n")
    quest_log = tmp_path / "quest_log.jsonl"

    items = read_checklist_items(checklist)
    entries = [build_checklist_entry(item, checklist) for item in items]

    added, skipped = append_checklist_entries(entries, quest_log)
    assert added == 2
    assert skipped == 0
    assert quest_log.exists()

    lines = quest_log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    payload = json.loads(lines[0])
    assert payload["event"] == "add_quest"
    assert "checklist_" in payload["details"]["id"]

    # Running again should skip duplicates
    added_again, skipped_again = append_checklist_entries(entries, quest_log)
    assert added_again == 0
    assert skipped_again == 2
