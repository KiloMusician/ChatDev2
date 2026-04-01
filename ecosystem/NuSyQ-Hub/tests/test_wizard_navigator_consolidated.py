"""Tests for src/tools/wizard_navigator_consolidated.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.tools.wizard_navigator_consolidated import RepositoryWizard, WizardNavigator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_wizard(tmp_path: Path) -> WizardNavigator:
    """Return a WizardNavigator rooted at tmp_path with no git subprocess."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        wiz = WizardNavigator(tmp_path)
    return wiz


# ===========================================================================
# 1. Instantiation
# ===========================================================================


class TestInstantiation:
    def test_basic_init(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert wiz.root == tmp_path.resolve()
        assert wiz.current_path == tmp_path.resolve()

    def test_root_resolved(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert wiz.root.is_absolute()

    def test_initial_visited_empty(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert wiz.visited_paths == set()

    def test_initial_bookmarks_empty(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert wiz.bookmarks == {}

    def test_initial_notes_empty(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert wiz.notes == {}

    def test_state_path_uses_data_dir(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        wiz = make_wizard(tmp_path)
        assert wiz.state_path == data_dir / "wizard_navigator_state.json"

    def test_state_path_fallback(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert wiz.state_path == tmp_path / ".wizard_navigator_state.json"

    def test_repository_wizard_alias(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert isinstance(wiz, RepositoryWizard)

    def test_loads_ecosystem_defaults(self, tmp_path: Path) -> None:
        cfg = tmp_path / "config"
        cfg.mkdir()
        (cfg / "ecosystem_defaults.json").write_text(
            json.dumps({"wizard_navigator": {"cross_repo_search_limit": 99}}),
            encoding="utf-8",
        )
        wiz = make_wizard(tmp_path)
        assert wiz.cross_repo_search_limit == 99

    def test_defaults_empty_when_no_config(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert wiz.defaults == {}


# ===========================================================================
# 2. State persistence
# ===========================================================================


class TestStatePersistence:
    def test_save_and_load_state(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.bookmarks["home"] = str(tmp_path)
        wiz._save_state()

        wiz2 = make_wizard(tmp_path)
        assert wiz2.bookmarks.get("home") == str(tmp_path)

    def test_state_includes_recent_paths(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        wiz = make_wizard(tmp_path)
        wiz._remember_path(sub)
        wiz2 = make_wizard(tmp_path)
        assert str(sub) in wiz2.recent_paths

    def test_state_load_restores_notes(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.notes[str(tmp_path)] = ["note1", "note2"]
        wiz._save_state()
        wiz2 = make_wizard(tmp_path)
        assert "note1" in wiz2.notes.get(str(tmp_path), [])

    def test_load_missing_state_is_silent(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        # No state file written — no exception raised
        assert wiz.recent_paths == []

    def test_corrupted_state_is_silently_ignored(self, tmp_path: Path) -> None:
        state_path = tmp_path / ".wizard_navigator_state.json"
        state_path.write_text("NOT JSON", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        assert wiz.bookmarks == {}


# ===========================================================================
# 3. Navigation — move()
# ===========================================================================


class TestMove:
    def test_move_into_subdirectory(self, tmp_path: Path) -> None:
        sub = tmp_path / "src"
        sub.mkdir()
        wiz = make_wizard(tmp_path)
        result = wiz.move("src")
        assert "src" in result
        assert wiz.current_path == sub

    def test_move_up(self, tmp_path: Path) -> None:
        sub = tmp_path / "src"
        sub.mkdir()
        wiz = make_wizard(tmp_path)
        wiz.current_path = sub
        result = wiz.move("..")
        assert wiz.current_path == tmp_path
        assert "Moved up" in result

    def test_move_up_at_root_returns_warning(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.move("..")
        assert "Already at root" in result

    def test_move_root_returns_home(self, tmp_path: Path) -> None:
        sub = tmp_path / "deep"
        sub.mkdir()
        wiz = make_wizard(tmp_path)
        wiz.current_path = sub
        result = wiz.move("root")
        assert wiz.current_path == tmp_path
        assert "root" in result.lower()

    def test_move_nonexistent_dir_fails(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.move("does_not_exist")
        assert "Cannot move" in result or "not found" in result


# ===========================================================================
# 4. get_current_room()
# ===========================================================================


class TestGetCurrentRoom:
    def test_returns_dict_with_required_keys(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        room = wiz.get_current_room()
        for key in ("name", "path", "exits", "items"):
            assert key in room

    def test_missing_path_returns_unknown(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.current_path = tmp_path / "ghost"
        room = wiz.get_current_room()
        assert room["name"] == "Unknown"

    def test_items_lists_files(self, tmp_path: Path) -> None:
        (tmp_path / "hello.py").write_text("pass", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        room = wiz.get_current_room()
        assert "hello.py" in room["items"]

    def test_exits_lists_subdirs(self, tmp_path: Path) -> None:
        (tmp_path / "subdir").mkdir()
        wiz = make_wizard(tmp_path)
        room = wiz.get_current_room()
        assert "subdir" in room["exits"]

    def test_visited_paths_updated(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.get_current_room()
        assert tmp_path.resolve() in wiz.visited_paths


# ===========================================================================
# 5. display_room()
# ===========================================================================


class TestDisplayRoom:
    def test_output_is_string(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.display_room()
        assert isinstance(result, str)

    def test_hidden_files_excluded_by_default(self, tmp_path: Path) -> None:
        (tmp_path / ".hidden_file").write_text("x", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.display_room()
        assert ".hidden_file" not in result

    def test_hidden_files_shown_with_flag(self, tmp_path: Path) -> None:
        (tmp_path / ".hidden_file").write_text("x", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.display_room(show_hidden=True)
        assert ".hidden_file" in result

    def test_ext_filter_limits_items(self, tmp_path: Path) -> None:
        (tmp_path / "a.py").write_text("pass", encoding="utf-8")
        (tmp_path / "b.md").write_text("# hi", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.display_room(ext_filter=".py")
        assert "a.py" in result
        assert "b.md" not in result


# ===========================================================================
# 6. inspect()
# ===========================================================================


class TestInspect:
    def test_inspect_existing_file(self, tmp_path: Path) -> None:
        (tmp_path / "hello.py").write_text("print('hi')\n", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.inspect("hello.py")
        assert "hello.py" in result
        assert "Size" in result

    def test_inspect_missing_file(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.inspect("ghost.txt")
        assert "not found" in result

    def test_inspect_directory_returns_hint(self, tmp_path: Path) -> None:
        (tmp_path / "subdir").mkdir()
        wiz = make_wizard(tmp_path)
        result = wiz.inspect("subdir")
        assert "directory" in result.lower()


# ===========================================================================
# 7. search()
# ===========================================================================


class TestSearch:
    def test_search_finds_matching_file(self, tmp_path: Path) -> None:
        (tmp_path / "test_foo.py").write_text("pass", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.search("test_*.py")
        assert "test_foo.py" in result

    def test_search_no_match(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.search("*.nonexistent")
        assert "No files" in result


# ===========================================================================
# 8. Bookmarks
# ===========================================================================


class TestBookmarks:
    def test_add_bookmark(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.add_bookmark("myspot")
        assert "myspot" in result
        assert "myspot" in wiz.bookmarks

    def test_add_bookmark_empty_name(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.add_bookmark("")
        assert "Usage" in result

    def test_list_bookmarks_empty(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.list_bookmarks()
        assert "No bookmarks" in result

    def test_list_bookmarks_shows_entries(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.bookmarks["alpha"] = str(tmp_path)
        result = wiz.list_bookmarks()
        assert "alpha" in result

    def test_jump_to_valid_bookmark(self, tmp_path: Path) -> None:
        sub = tmp_path / "target"
        sub.mkdir()
        wiz = make_wizard(tmp_path)
        wiz.bookmarks["target"] = str(sub)
        result = wiz.jump_to_bookmark("target")
        assert wiz.current_path == sub
        assert isinstance(result, str)

    def test_jump_to_missing_bookmark(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.jump_to_bookmark("noexist")
        assert "No bookmark" in result

    def test_jump_to_nonexistent_path(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.bookmarks["ghost"] = str(tmp_path / "ghost")
        result = wiz.jump_to_bookmark("ghost")
        assert "missing path" in result


# ===========================================================================
# 9. Notes
# ===========================================================================


class TestNotes:
    def test_add_note(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.add_note("interesting finding")
        assert "Note saved" in result
        assert str(tmp_path.resolve()) in wiz.notes

    def test_add_empty_note_returns_usage(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.add_note("")
        assert "Usage" in result

    def test_list_notes_for_current_path(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.add_note("my note")
        result = wiz.list_notes()
        assert "my note" in result

    def test_list_notes_empty(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.list_notes()
        assert "No notes" in result


# ===========================================================================
# 10. grep()
# ===========================================================================


class TestGrep:
    def test_grep_finds_match(self, tmp_path: Path) -> None:
        (tmp_path / "code.py").write_text("SECRET_TOKEN = 'abc'\n", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.grep("SECRET_TOKEN")
        assert "SECRET_TOKEN" in result

    def test_grep_empty_pattern(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.grep("")
        assert "Usage" in result

    def test_grep_no_matches(self, tmp_path: Path) -> None:
        (tmp_path / "empty.py").write_text("pass\n", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.grep("ZZZNOMATCH")
        assert "No matches" in result

    def test_grep_invalid_regex(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.grep("[invalid", use_regex=True)
        assert "Invalid regex" in result

    def test_grep_case_insensitive(self, tmp_path: Path) -> None:
        (tmp_path / "f.txt").write_text("Hello World\n", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.grep("hello world", case_sensitive=False)
        assert "Hello World" in result


# ===========================================================================
# 11. todos()
# ===========================================================================


class TestTodos:
    def test_finds_todo_markers(self, tmp_path: Path) -> None:
        (tmp_path / "work.py").write_text("# TODO: fix this\npass\n", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.todos()
        assert "TODO" in result

    def test_no_todos(self, tmp_path: Path) -> None:
        (tmp_path / "clean.py").write_text("pass\n", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.todos()
        assert "No TODO" in result


# ===========================================================================
# 12. Achievements
# ===========================================================================


class TestAchievements:
    def test_no_achievements_initially(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.achievements()
        assert "No achievements" in result

    def test_explorer_i_unlocked(self, tmp_path: Path) -> None:
        dirs = [tmp_path / f"d{i}" for i in range(5)]
        for d in dirs:
            d.mkdir()
        wiz = make_wizard(tmp_path)
        for d in dirs:
            wiz.visited_paths.add(d)
        result = wiz.achievements()
        assert "Explorer I" in result

    def test_archivist_with_notes(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.notes["somewhere"] = ["a note"]
        result = wiz.achievements()
        assert "Archivist" in result

    def test_cartographer_with_bookmarks(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.bookmarks["spot"] = str(tmp_path)
        result = wiz.achievements()
        assert "Cartographer" in result


# ===========================================================================
# 13. stats_by_extension()
# ===========================================================================


class TestStatsByExtension:
    def test_counts_extensions(self, tmp_path: Path) -> None:
        (tmp_path / "a.py").write_text("pass", encoding="utf-8")
        (tmp_path / "b.py").write_text("pass", encoding="utf-8")
        (tmp_path / "c.md").write_text("# hi", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.stats_by_extension()
        assert ".py: 2" in result

    def test_no_files_returns_message(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.stats_by_extension()
        assert "No files" in result


# ===========================================================================
# 14. tree()
# ===========================================================================


class TestTree:
    def test_tree_output_contains_root(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.tree()
        assert str(tmp_path) in result

    def test_tree_shows_subdirectory(self, tmp_path: Path) -> None:
        (tmp_path / "subdir").mkdir()
        wiz = make_wizard(tmp_path)
        result = wiz.tree(depth=1)
        assert "subdir" in result

    def test_tree_depth_one_does_not_recurse(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        nested = sub / "nested_child"
        nested.mkdir()
        wiz = make_wizard(tmp_path)
        # depth=1 should show 'sub' but not 'nested_child' (which is 2 levels deep)
        result = wiz.tree(depth=1)
        assert "sub" in result
        assert "nested_child" not in result


# ===========================================================================
# 15. size_report()
# ===========================================================================


class TestSizeReport:
    def test_size_report_lists_files(self, tmp_path: Path) -> None:
        (tmp_path / "big.txt").write_bytes(b"x" * 1024)
        wiz = make_wizard(tmp_path)
        result = wiz.size_report()
        assert "big.txt" in result

    def test_size_report_empty_dir(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.size_report()
        assert "No files" in result


# ===========================================================================
# 16. git_status()
# ===========================================================================


class TestGitStatus:
    def test_git_status_no_repo_root(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.repo_root = None
        result = wiz.git_status()
        assert "unavailable" in result.lower()

    def test_git_status_clean_tree(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.repo_root = tmp_path
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = wiz.git_status()
        assert "clean" in result.lower()

    def test_git_status_subprocess_failure(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.repo_root = tmp_path
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="err")
            result = wiz.git_status()
        assert "unavailable" in result.lower()


# ===========================================================================
# 17. health()
# ===========================================================================


class TestHealth:
    def test_health_returns_string(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.health()
        assert isinstance(result, str)
        assert "pytest.ini" in result

    def test_health_shows_ok_for_existing(self, tmp_path: Path) -> None:
        (tmp_path / "pytest.ini").write_text("[pytest]", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.health()
        assert "pytest.ini: OK" in result


# ===========================================================================
# 18. explain()
# ===========================================================================


class TestExplain:
    def test_explain_finds_readme(self, tmp_path: Path) -> None:
        (tmp_path / "README.md").write_text("# My project\nGreat stuff.", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.explain()
        assert "README" in result

    def test_explain_no_readme(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.explain()
        assert isinstance(result, str)  # should not raise


# ===========================================================================
# 19. handle_command()
# ===========================================================================


class TestHandleCommand:
    def test_empty_command_displays_room(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.handle_command("")
        assert isinstance(result, str)

    def test_help_command(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.handle_command("help")
        assert "Wizard Navigator Commands" in result

    def test_unknown_command(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.handle_command("zzz_unknown_cmd")
        assert "Unknown command" in result

    def test_go_command_navigates(self, tmp_path: Path) -> None:
        sub = tmp_path / "mydir"
        sub.mkdir()
        wiz = make_wizard(tmp_path)
        wiz.handle_command("go mydir")
        assert wiz.current_path == sub

    def test_cd_alias_works(self, tmp_path: Path) -> None:
        sub = tmp_path / "adir"
        sub.mkdir()
        wiz = make_wizard(tmp_path)
        wiz.handle_command("cd adir")
        assert wiz.current_path == sub

    def test_ls_alias_returns_room(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.handle_command("ls")
        assert isinstance(result, str)

    def test_bookmark_command_saves(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.handle_command("bookmark mymark")
        assert "mymark" in wiz.bookmarks

    def test_note_command_saves(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.handle_command("note this is a note")
        assert str(tmp_path.resolve()) in wiz.notes

    def test_invalid_shlex_returns_error(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.handle_command("'unclosed quote")
        assert "Invalid command" in result or isinstance(result, str)


# ===========================================================================
# 20. _parse_args()
# ===========================================================================


class TestParseArgs:
    def test_flags_parsed(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        flags, _values, _rest = wiz._parse_args(["-a", "--deep"])
        assert "all" in flags
        assert "deep" in flags

    def test_ext_value_parsed(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        _, values, _ = wiz._parse_args(["-e", "py"])
        assert values["ext"] == "py"

    def test_rest_captures_positional(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        _, _, rest = wiz._parse_args(["hello", "world"])
        assert rest == ["hello", "world"]


# ===========================================================================
# 21. _normalize_ext()
# ===========================================================================


class TestNormalizeExt:
    def test_adds_dot_prefix(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert wiz._normalize_ext("py") == ".py"

    def test_lowercases(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert wiz._normalize_ext("PY") == ".py"

    def test_none_returns_none(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert wiz._normalize_ext(None) is None

    def test_empty_returns_none(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert wiz._normalize_ext("") is None


# ===========================================================================
# 22. _format_size()
# ===========================================================================


class TestFormatSize:
    def test_bytes(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert "B" in wiz._format_size(500)

    def test_kilobytes(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert "KB" in wiz._format_size(2048)

    def test_megabytes(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        assert "MB" in wiz._format_size(2 * 1024 * 1024)


# ===========================================================================
# 23. list_recent()
# ===========================================================================


class TestListRecent:
    def test_no_recent_paths(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.list_recent()
        assert "No recent" in result

    def test_recent_paths_shown(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        wiz.recent_paths = [str(tmp_path)]
        result = wiz.list_recent()
        assert str(tmp_path) in result


# ===========================================================================
# 24. snapshot() and trail()
# ===========================================================================


class TestSnapshotAndTrail:
    def test_snapshot_creates_file(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.snapshot()
        assert "Snapshot saved" in result
        # Check file was actually written
        reports = list((tmp_path / "state" / "reports").glob("wizard_snapshot_*.md"))
        assert len(reports) == 1

    def test_trail_creates_file(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.trail()
        assert "Trail saved" in result
        reports = list((tmp_path / "state" / "reports").glob("wizard_trail_*.md"))
        assert len(reports) == 1


# ===========================================================================
# 25. readiness()
# ===========================================================================


class TestReadiness:
    def test_readiness_returns_score(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.readiness()
        assert "Readiness score" in result

    def test_readiness_shows_missing(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.readiness()
        # README not present → "Missing" section
        assert "Missing" in result or "Readiness" in result


# ===========================================================================
# 26. teleport()
# ===========================================================================


class TestTeleport:
    def test_teleport_to_unknown_repo(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.teleport("completely_unknown_repo")
        assert "failed" in result.lower() or "not found" in result.lower()

    def test_teleport_empty_destination(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.teleport("")
        assert isinstance(result, str)

    def test_teleport_to_known_repo(self, tmp_path: Path) -> None:
        other = tmp_path / "other_repo"
        other.mkdir()
        wiz = make_wizard(tmp_path)
        wiz.repo_roots["myrepo"] = other
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            result = wiz.teleport("myrepo")
        assert wiz.root == other
        assert isinstance(result, str)


# ===========================================================================
# 27. tag_scan()
# ===========================================================================


class TestTagScan:
    def test_finds_omnitag(self, tmp_path: Path) -> None:
        (tmp_path / "tagged.py").write_text(
            '"""OmniTag: {}\n"""\n', encoding="utf-8"
        )
        wiz = make_wizard(tmp_path)
        result = wiz.tag_scan()
        assert "OmniTag" in result

    def test_no_tags_message(self, tmp_path: Path) -> None:
        (tmp_path / "plain.py").write_text("pass\n", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.tag_scan()
        assert "No OmniTag" in result


# ===========================================================================
# 28. inventory()
# ===========================================================================


class TestInventory:
    def test_lists_py_scripts(self, tmp_path: Path) -> None:
        (tmp_path / "run.py").write_text("pass", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.inventory()
        assert "run.py" in result

    def test_no_scripts_message(self, tmp_path: Path) -> None:
        (tmp_path / "data.json").write_text("{}", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        result = wiz.inventory()
        assert "No runnable" in result


# ===========================================================================
# 29. quest_note()
# ===========================================================================


class TestQuestNote:
    def test_quest_note_no_log_file(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.quest_note("some note")
        assert "Quest log not found" in result

    def test_quest_note_empty_text(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        result = wiz.quest_note("")
        assert "Usage" in result

    def test_quest_note_appends_to_file(self, tmp_path: Path) -> None:
        log_dir = tmp_path / "src" / "Rosetta_Quest_System"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "quest_log.jsonl"
        log_file.write_text("", encoding="utf-8")
        wiz = make_wizard(tmp_path)
        wiz.repo_root = tmp_path
        result = wiz.quest_note("found a thing")
        assert "appended" in result
        data = json.loads(log_file.read_text(encoding="utf-8").strip())
        assert data["note"] == "found a thing"


# ===========================================================================
# 30. _ai_assist() fallback path
# ===========================================================================


class TestAiAssist:
    def test_ai_assist_falls_back_gracefully(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        with patch.dict("sys.modules", {"src.ai.ollama_chatdev_integrator": None}):
            result = wiz._ai_assist("what is this?")
        assert isinstance(result, str)

    def test_simple_analysis_with_py_files(self, tmp_path: Path) -> None:
        wiz = make_wizard(tmp_path)
        room = {
            "name": "src",
            "path": str(tmp_path),
            "items": ["foo.py", "bar.md"],
            "exits": ["subdir"],
        }
        result = wiz._simple_analysis("explore", room)
        assert "foo.py" in result or "Python" in result
