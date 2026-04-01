"""Tests for src/tools/summary_indexer.py

This module tests the Summary/Report/Analysis Documentation Indexer.

Coverage Target: 70%+
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

# =============================================================================
# Module Import Tests
# =============================================================================


class TestModuleImports:
    """Test module-level imports."""

    def test_import_summary_doc_meta(self):
        """Test SummaryDocMeta dataclass can be imported."""
        from src.tools.summary_indexer import SummaryDocMeta

        assert SummaryDocMeta is not None

    def test_import_categorize(self):
        """Test categorize function can be imported."""
        from src.tools.summary_indexer import categorize

        assert categorize is not None

    def test_import_extract_metadata(self):
        """Test extract_metadata function can be imported."""
        from src.tools.summary_indexer import extract_metadata

        assert extract_metadata is not None

    def test_import_scan_repository(self):
        """Test scan_repository function can be imported."""
        from src.tools.summary_indexer import scan_repository

        assert scan_repository is not None

    def test_import_build_summary_index(self):
        """Test build_summary_index function can be imported."""
        from src.tools.summary_indexer import build_summary_index

        assert build_summary_index is not None

    def test_import_save_summary_index(self):
        """Test save_summary_index function can be imported."""
        from src.tools.summary_indexer import save_summary_index

        assert save_summary_index is not None


# =============================================================================
# SummaryDocMeta Tests
# =============================================================================


class TestSummaryDocMeta:
    """Test SummaryDocMeta dataclass."""

    def test_create_basic_meta(self):
        """Test creating basic metadata."""
        from src.tools.summary_indexer import SummaryDocMeta

        meta = SummaryDocMeta(
            path="/test/file.md",
            repository="test-repo",
            category="summary",
            size_bytes=1024,
            modified="2025-01-01T00:00:00",
        )

        assert meta.path == "/test/file.md"
        assert meta.repository == "test-repo"
        assert meta.category == "summary"
        assert meta.size_bytes == 1024

    def test_create_with_optional_fields(self):
        """Test creating metadata with optional fields."""
        from src.tools.summary_indexer import SummaryDocMeta

        meta = SummaryDocMeta(
            path="/test/file.md",
            repository="test-repo",
            category="report",
            size_bytes=2048,
            modified="2025-01-01T00:00:00",
            title="Test Report",
            first_heading="Test Report",
            omni_tags=["OmniTag: test"],
        )

        assert meta.title == "Test Report"
        assert meta.first_heading == "Test Report"
        assert meta.omni_tags == ["OmniTag: test"]


# =============================================================================
# categorize Tests
# =============================================================================


class TestCategorize:
    """Test categorize function."""

    def test_categorize_summary(self):
        """Test categorizing summary files."""
        from src.tools.summary_indexer import categorize

        path = Path("FINAL_SUMMARY.md")
        result = categorize(path)

        assert result == "summary"

    def test_categorize_report(self):
        """Test categorizing report files."""
        from src.tools.summary_indexer import categorize

        path = Path("coverage_report.md")
        result = categorize(path)

        assert result == "report"

    def test_categorize_analysis(self):
        """Test categorizing analysis files."""
        from src.tools.summary_indexer import categorize

        path = Path("code_analysis.md")
        result = categorize(path)

        assert result == "analysis"

    def test_categorize_session(self):
        """Test categorizing session files."""
        from src.tools.summary_indexer import categorize

        path = Path("SESSION_2025_01_01.md")
        result = categorize(path)

        assert result == "session"

    def test_categorize_investigation(self):
        """Test categorizing investigation files."""
        from src.tools.summary_indexer import categorize

        path = Path("bug_investigation.md")
        result = categorize(path)

        assert result == "investigation"

    def test_categorize_other(self):
        """Test categorizing unknown files as 'other'."""
        from src.tools.summary_indexer import categorize

        path = Path("README.md")
        result = categorize(path)

        assert result == "other"

    def test_categorize_case_insensitive(self):
        """Test that categorization is case-insensitive."""
        from src.tools.summary_indexer import categorize

        path = Path("REPORT_FINAL.MD")
        result = categorize(path)

        assert result == "report"


# =============================================================================
# extract_metadata Tests
# =============================================================================


class TestExtractMetadata:
    """Test extract_metadata function."""

    def test_extract_basic_metadata(self, tmp_path):
        """Test extracting basic metadata from file."""
        from src.tools.summary_indexer import extract_metadata

        test_file = tmp_path / "test_summary.md"
        test_file.write_text("# Test Summary\n\nContent here.")

        meta = extract_metadata(test_file, "test-repo")

        assert meta.path == str(test_file)
        assert meta.repository == "test-repo"
        assert meta.category == "summary"
        assert meta.first_heading == "Test Summary"
        assert meta.title == "Test Summary"

    def test_extract_with_omni_tags(self, tmp_path):
        """Test extracting metadata with OmniTags."""
        from src.tools.summary_indexer import extract_metadata

        test_file = tmp_path / "test_report.md"
        test_file.write_text("""# Test Report
        
OmniTag: {"purpose": "test"}
MegaTag: TEST

Content here.
""")

        meta = extract_metadata(test_file, "test-repo")

        assert meta.omni_tags is not None
        assert len(meta.omni_tags) == 2
        assert any("OmniTag" in t for t in meta.omni_tags)

    def test_extract_no_heading(self, tmp_path):
        """Test extracting metadata when no heading present."""
        from src.tools.summary_indexer import extract_metadata

        test_file = tmp_path / "no_heading_summary.md"
        test_file.write_text("Just plain content without heading.")

        meta = extract_metadata(test_file, "test-repo")

        assert meta.first_heading is None
        assert meta.title is None

    def test_extract_nonexistent_file(self, tmp_path):
        """Test extracting metadata from non-existent file."""
        from src.tools.summary_indexer import extract_metadata

        fake_path = tmp_path / "nonexistent.md"

        meta = extract_metadata(fake_path, "test-repo")

        assert meta.size_bytes == 0

    def test_extract_size_and_modified(self, tmp_path):
        """Test extracting size and modified timestamp."""
        from src.tools.summary_indexer import extract_metadata

        test_file = tmp_path / "test_analysis.md"
        test_file.write_text("# Analysis\n\nSome content.")

        meta = extract_metadata(test_file, "test-repo")

        assert meta.size_bytes > 0
        assert meta.modified is not None
        # Should be ISO format
        datetime.fromisoformat(meta.modified)


# =============================================================================
# scan_repository Tests
# =============================================================================


class TestScanRepository:
    """Test scan_repository function."""

    def test_scan_empty_repository(self, tmp_path):
        """Test scanning empty repository."""
        from src.tools.summary_indexer import scan_repository

        result = scan_repository(tmp_path)

        assert result == []

    def test_scan_root_level_summary(self, tmp_path):
        """Test scanning root-level summary files."""
        from src.tools.summary_indexer import scan_repository

        summary_file = tmp_path / "PROJECT_SUMMARY.md"
        summary_file.write_text("# Project Summary\n\nContent.")

        result = scan_repository(tmp_path)

        assert len(result) == 1
        assert result[0].category == "summary"

    def test_scan_docs_directory(self, tmp_path):
        """Test scanning docs directory."""
        from src.tools.summary_indexer import scan_repository

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "API_REPORT.md").write_text("# API Report")

        result = scan_repository(tmp_path)

        assert len(result) == 1
        assert result[0].category == "report"

    def test_scan_reports_directory(self, tmp_path):
        """Test scanning Reports directory."""
        from src.tools.summary_indexer import scan_repository

        reports_dir = tmp_path / "Reports"
        reports_dir.mkdir()
        (reports_dir / "coverage_analysis.md").write_text("# Coverage")

        result = scan_repository(tmp_path)

        assert len(result) == 1
        assert result[0].category == "analysis"

    def test_scan_excludes_git_directory(self, tmp_path):
        """Test that .git directory is excluded."""
        from src.tools.summary_indexer import scan_repository

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        git_dir = docs_dir / ".git"
        git_dir.mkdir()
        (git_dir / "summary.md").write_text("# Should not find")

        result = scan_repository(tmp_path)

        assert len(result) == 0

    def test_scan_excludes_archive_directory(self, tmp_path):
        """Test that archive directory is excluded."""
        from src.tools.summary_indexer import scan_repository

        docs_dir = tmp_path / "docs"
        archive_dir = docs_dir / "archive"
        archive_dir.mkdir(parents=True)
        (archive_dir / "old_summary.md").write_text("# Old Summary")

        result = scan_repository(tmp_path)

        assert len(result) == 0

    def test_scan_deduplicates_paths(self, tmp_path):
        """Test that duplicate paths are not included."""
        from src.tools.summary_indexer import scan_repository

        # Create both at root and docs (but same file shouldn't be double-counted)
        summary_file = tmp_path / "SUMMARY.md"
        summary_file.write_text("# Summary")

        result = scan_repository(tmp_path)

        assert len(result) == 1

    def test_scan_ignores_non_summary_files(self, tmp_path):
        """Test that non-summary files are ignored."""
        from src.tools.summary_indexer import scan_repository

        (tmp_path / "README.md").write_text("# Readme")
        (tmp_path / "CHANGELOG.md").write_text("# Changelog")

        result = scan_repository(tmp_path)

        assert len(result) == 0

    def test_scan_state_reports_directory(self, tmp_path):
        """Test scanning state/reports directory."""
        from src.tools.summary_indexer import scan_repository

        state_reports = tmp_path / "state" / "reports"
        state_reports.mkdir(parents=True)
        (state_reports / "status_report.md").write_text("# Status Report")

        result = scan_repository(tmp_path)

        assert len(result) == 1


# =============================================================================
# build_summary_index Tests
# =============================================================================


class TestBuildSummaryIndex:
    """Test build_summary_index function."""

    def test_build_empty_index(self, tmp_path):
        """Test building index for empty repository."""
        from src.tools.summary_indexer import build_summary_index

        result = build_summary_index(tmp_path)

        assert result["total_files"] == 0
        assert result["files"] == []
        assert result["categories"] == {}
        assert "generated_at" in result

    def test_build_index_with_files(self, tmp_path):
        """Test building index with files."""
        from src.tools.summary_indexer import build_summary_index

        (tmp_path / "SUMMARY.md").write_text("# Summary")
        (tmp_path / "REPORT.md").write_text("# Report")

        result = build_summary_index(tmp_path)

        assert result["total_files"] == 2
        assert len(result["files"]) == 2
        assert result["categories"]["summary"] == 1
        assert result["categories"]["report"] == 1

    def test_build_index_repository_name(self, tmp_path):
        """Test that repository name is included."""
        from src.tools.summary_indexer import build_summary_index

        result = build_summary_index(tmp_path)

        assert result["repository"] == tmp_path.name

    def test_build_index_generated_at_iso(self, tmp_path):
        """Test that generated_at is ISO format."""
        from src.tools.summary_indexer import build_summary_index

        result = build_summary_index(tmp_path)

        # Should parse without error
        datetime.fromisoformat(result["generated_at"])


# =============================================================================
# save_summary_index Tests
# =============================================================================


class TestSaveSummaryIndex:
    """Test save_summary_index function."""

    def test_save_creates_output_directory(self, tmp_path):
        """Test that save creates docs/Auto directory."""
        from src.tools.summary_indexer import save_summary_index

        save_summary_index(tmp_path)

        assert (tmp_path / "docs" / "Auto").exists()

    def test_save_creates_json_file(self, tmp_path):
        """Test that save creates SUMMARY_INDEX.json."""
        from src.tools.summary_indexer import save_summary_index

        out_file = save_summary_index(tmp_path)

        assert out_file.name == "SUMMARY_INDEX.json"
        assert out_file.exists()

    def test_save_json_is_valid(self, tmp_path):
        """Test that saved JSON is valid."""
        from src.tools.summary_indexer import save_summary_index

        (tmp_path / "TEST_SUMMARY.md").write_text("# Test")

        out_file = save_summary_index(tmp_path)

        content = json.loads(out_file.read_text(encoding="utf-8"))
        assert "total_files" in content
        assert "files" in content

    def test_save_returns_correct_path(self, tmp_path):
        """Test that save returns correct output path."""
        from src.tools.summary_indexer import save_summary_index

        out_file = save_summary_index(tmp_path)

        expected = tmp_path / "docs" / "Auto" / "SUMMARY_INDEX.json"
        assert out_file == expected


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for full workflow."""

    def test_full_workflow(self, tmp_path):
        """Test complete scan → index → save workflow."""
        from src.tools.summary_indexer import save_summary_index

        # Create some files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "API_SUMMARY.md").write_text("# API Summary\n\nAPI docs.")
        (docs_dir / "TEST_REPORT.md").write_text("# Test Report\n\nTest results.")
        (tmp_path / "ANALYSIS.md").write_text("# Analysis\n\nCode analysis.")

        # Save index
        out_file = save_summary_index(tmp_path)

        # Verify
        content = json.loads(out_file.read_text())
        assert content["total_files"] == 3
        assert content["categories"]["summary"] == 1
        assert content["categories"]["report"] == 1
        assert content["categories"]["analysis"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
