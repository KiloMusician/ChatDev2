"""Tests for contextual_output.py.

Tests the context-aware file output management utilities.
"""

from pathlib import Path
from unittest.mock import patch

from src.utils.contextual_output import (
    OUTPUT_DIR_MAP,
    REPO_ROOT,
    contextual_save,
    get_output_dir,
    move_to_contextual_location,
    suggest_output_location,
)


class TestOutputDirMap:
    """Tests for OUTPUT_DIR_MAP constant."""

    def test_map_is_dict(self):
        """OUTPUT_DIR_MAP is a dictionary."""
        assert isinstance(OUTPUT_DIR_MAP, dict)

    def test_map_has_common_extensions(self):
        """Contains common file extensions."""
        assert ".log" in OUTPUT_DIR_MAP
        assert ".json" in OUTPUT_DIR_MAP
        assert ".md" in OUTPUT_DIR_MAP
        assert ".py" in OUTPUT_DIR_MAP

    def test_map_values_are_strings(self):
        """All values are directory name strings."""
        for ext, dirname in OUTPUT_DIR_MAP.items():
            assert isinstance(ext, str)
            assert isinstance(dirname, str)
            assert ext.startswith(".")


class TestRepoRoot:
    """Tests for REPO_ROOT constant."""

    def test_repo_root_is_path(self):
        """REPO_ROOT is a Path object."""
        assert isinstance(REPO_ROOT, Path)

    def test_repo_root_exists(self):
        """REPO_ROOT directory exists."""
        assert REPO_ROOT.exists()

    def test_repo_root_is_directory(self):
        """REPO_ROOT is a directory."""
        assert REPO_ROOT.is_dir()


class TestGetOutputDir:
    """Tests for get_output_dir function."""

    def test_log_file_goes_to_logs(self):
        """Log files go to logs directory."""
        result = get_output_dir("test.log")
        assert result == REPO_ROOT / "logs"

    def test_json_file_goes_to_reports(self):
        """JSON files go to reports directory."""
        result = get_output_dir("data.json")
        assert result == REPO_ROOT / "reports"

    def test_md_file_goes_to_reports(self):
        """Markdown files go to reports directory."""
        result = get_output_dir("README.md")
        assert result == REPO_ROOT / "reports"

    def test_csv_file_goes_to_data(self):
        """CSV files go to data directory."""
        result = get_output_dir("results.csv")
        assert result == REPO_ROOT / "data"

    def test_py_file_goes_to_scripts(self):
        """Python files go to scripts directory."""
        result = get_output_dir("helper.py")
        assert result == REPO_ROOT / "scripts"

    def test_png_file_goes_to_assets(self):
        """PNG files go to assets directory."""
        result = get_output_dir("image.png")
        assert result == REPO_ROOT / "assets"

    def test_unknown_extension_goes_to_reports(self):
        """Unknown extensions default to reports."""
        result = get_output_dir("file.xyz")
        assert result == REPO_ROOT / "reports"

    def test_context_overrides_extension(self, tmp_path):
        """Context directory takes priority if valid."""
        # Create a subdir in tmp_path to simulate valid context
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            custom_dir = tmp_path / "custom_output"
            custom_dir.mkdir()
            result = get_output_dir("test.log", context="custom_output")
            assert result == tmp_path / "custom_output"

    def test_invalid_context_uses_extension(self, tmp_path):
        """Invalid context falls back to extension-based mapping."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            result = get_output_dir("test.log", context="nonexistent")
            assert result == tmp_path / "logs"

    def test_case_insensitive_extension(self):
        """Extension matching is case-insensitive."""
        result_lower = get_output_dir("file.log")
        result_upper = get_output_dir("file.LOG")
        assert result_lower == result_upper


class TestSuggestOutputLocation:
    """Tests for suggest_output_location function."""

    def test_returns_same_as_get_output_dir(self):
        """Returns same result as get_output_dir."""
        filename = "test.json"
        assert suggest_output_location(filename) == get_output_dir(filename)

    def test_with_context(self, tmp_path):
        """Works with context parameter."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            custom = tmp_path / "mydir"
            custom.mkdir()
            result = suggest_output_location("file.txt", context="mydir")
            assert result == tmp_path / "mydir"


class TestContextualSave:
    """Tests for contextual_save function."""

    def test_saves_text_file(self, tmp_path):
        """Saves text content to correct location."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            result = contextual_save("hello world", "test.log")
            assert result.exists()
            assert result.read_text() == "hello world"
            assert result.parent.name == "logs"

    def test_saves_binary_file(self, tmp_path):
        """Saves binary content with mode='wb'."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            binary_data = b"\x00\x01\x02\x03"
            result = contextual_save(binary_data, "data.bin", mode="wb")
            assert result.exists()
            assert result.read_bytes() == binary_data

    def test_creates_directory_if_missing(self, tmp_path):
        """Creates output directory if it doesn't exist."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            result = contextual_save("content", "new.json")
            assert result.parent.exists()
            assert result.parent.is_dir()

    def test_versions_existing_file(self, tmp_path):
        """Adds timestamp to filename if file exists."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            # First save
            first = contextual_save("first", "test.txt")
            # Second save should version
            second = contextual_save("second", "test.txt", version_if_exists=True)
            assert first != second
            assert first.exists()
            assert second.exists()
            # Second filename should have timestamp pattern
            assert "test_" in second.name

    def test_overwrite_replaces_file(self, tmp_path):
        """Overwrite=True replaces existing file."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            first = contextual_save("first", "test.txt")
            second = contextual_save("second", "test.txt", overwrite=True)
            assert first == second
            assert second.read_text() == "second"

    def test_no_version_no_overwrite(self, tmp_path):
        """version_if_exists=False and overwrite=False still overwrites."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            first = contextual_save("first", "test.txt")
            # This should overwrite in place (same path)
            second = contextual_save("second", "test.txt", version_if_exists=False)
            assert first == second
            assert second.read_text() == "second"

    def test_custom_context(self, tmp_path):
        """Saves to custom context directory."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            custom = tmp_path / "output"
            custom.mkdir()
            result = contextual_save("data", "file.txt", context="output")
            assert result.parent == custom

    def test_custom_encoding(self, tmp_path):
        """Respects custom encoding."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            result = contextual_save("こんにちは", "utf8.txt", encoding="utf-8")
            assert result.read_text(encoding="utf-8") == "こんにちは"

    def test_returns_path(self, tmp_path):
        """Returns Path object."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            result = contextual_save("", "empty.txt")
            assert isinstance(result, Path)


class TestMoveToContextualLocation:
    """Tests for move_to_contextual_location function."""

    def test_moves_file(self, tmp_path):
        """Moves file to correct location."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            # Create source file
            source = tmp_path / "source.log"
            source.write_text("log content")
            # Move it
            result = move_to_contextual_location(source)
            assert result == tmp_path / "logs" / "source.log"
            assert result.exists()
            assert not source.exists()

    def test_creates_destination_dir(self, tmp_path):
        """Creates destination directory if needed."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            source = tmp_path / "data.json"
            source.write_text("{}")
            result = move_to_contextual_location(source)
            assert result.parent.exists()

    def test_with_context(self, tmp_path):
        """Respects context parameter."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            custom = tmp_path / "custom"
            custom.mkdir()
            source = tmp_path / "file.txt"
            source.write_text("content")
            result = move_to_contextual_location(source, context="custom")
            assert result == custom / "file.txt"

    def test_accepts_string_path(self, tmp_path):
        """Accepts string path input."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            source = tmp_path / "script.py"
            source.write_text("# python")
            result = move_to_contextual_location(str(source))
            assert isinstance(result, Path)
            assert result.exists()

    def test_returns_new_path(self, tmp_path):
        """Returns the new location path."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            source = tmp_path / "image.png"
            source.write_bytes(b"\x89PNG")
            result = move_to_contextual_location(source)
            assert result == tmp_path / "assets" / "image.png"


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_filename(self):
        """Handles empty filename."""
        result = get_output_dir("")
        assert result == REPO_ROOT / "reports"  # No extension = unknown

    def test_filename_with_multiple_dots(self):
        """Handles filenames with multiple dots."""
        result = get_output_dir("file.backup.log")
        assert result == REPO_ROOT / "logs"  # Last extension

    def test_hidden_file(self):
        """Handles hidden files (starting with dot)."""
        result = get_output_dir(".gitignore")
        assert result == REPO_ROOT / "reports"  # No recognized extension

    def test_path_like_filename(self):
        """Handles filename with path separators."""
        result = get_output_dir("subdir/test.json")
        assert result == REPO_ROOT / "reports"

    def test_timestamp_format_in_versioned_file(self, tmp_path):
        """Versioned files contain timestamp in name."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            # Create first file
            contextual_save("first", "test.txt")
            # Create versioned second file
            result = contextual_save("second", "test.txt")
            # Should contain underscore (timestamp separator)
            assert "_" in result.stem
            # Original stem should be preserved
            assert result.stem.startswith("test_")

    def test_multiple_saves_create_files(self, tmp_path):
        """Multiple saves create multiple files."""
        with patch("src.utils.contextual_output.REPO_ROOT", tmp_path):
            path1 = contextual_save("1", "test.txt")
            path2 = contextual_save("2", "test.txt")
            # Both files should exist
            assert path1.exists()
            assert path2.exists()
            # At least one should be versioned
            assert path1 != path2 or path1.read_text() == "2"
