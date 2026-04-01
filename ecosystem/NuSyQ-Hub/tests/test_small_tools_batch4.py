"""Tests for src/tools batch 4: safe_consolidator, vibe_indexer, consolidation_planner.

Coverage targets:
- safe_consolidator.py: 174 lines - SafeConsolidator class
- vibe_indexer.py: 175 lines - markdown parsing and lattice building
- consolidation_planner.py: 188 lines - KILOConsolidationPlanner class
"""

from __future__ import annotations

import json
from pathlib import Path


# ==============================================================================
# safe_consolidator.py tests
# ==============================================================================
class TestSafeConsolidatorInit:
    """Test SafeConsolidator initialization."""

    def test_init_defaults(self, tmp_path: Path):
        """Verify default initialization."""
        from src.tools.safe_consolidator import SafeConsolidator

        consolidator = SafeConsolidator(repo_root=str(tmp_path))
        assert consolidator.repo_root == tmp_path
        assert consolidator.src_root == tmp_path / "src"
        assert consolidator.empty_files_found == []
        assert consolidator.functional_files_preserved == []
        assert consolidator.consolidation_actions == []


class TestIdentifySafeConsolidations:
    """Test identify_safe_consolidations method."""

    def test_no_duplicates(self, tmp_path: Path):
        """No duplicates returns empty actions."""
        from src.tools.safe_consolidator import SafeConsolidator

        src = tmp_path / "src"
        src.mkdir()
        (src / "unique.py").write_text("# unique file")

        consolidator = SafeConsolidator(repo_root=str(tmp_path))
        actions = consolidator.identify_safe_consolidations()
        assert actions == []

    def test_identifies_safe_removal(self, tmp_path: Path):
        """Identifies safe removal when one functional and one empty duplicate exist."""
        from src.tools.safe_consolidator import SafeConsolidator

        src = tmp_path / "src"
        subdir1 = src / "mod1"
        subdir2 = src / "mod2"
        subdir1.mkdir(parents=True)
        subdir2.mkdir(parents=True)

        # One functional, one empty with same name
        (subdir1 / "config.py").write_text("# functional config\nVERSION = '1.0'")
        (subdir2 / "config.py").write_text("")  # empty

        consolidator = SafeConsolidator(repo_root=str(tmp_path))
        actions = consolidator.identify_safe_consolidations()

        assert len(actions) == 1
        assert actions[0]["filename"] == "config.py"
        assert actions[0]["action"] == "safe_removal"
        assert actions[0]["risk"] == "none"
        assert len(actions[0]["remove"]) == 1
        assert actions[0]["preserve"] == subdir1 / "config.py"

    def test_identifies_manual_review_needed(self, tmp_path: Path):
        """Multiple functional files need manual review."""
        from src.tools.safe_consolidator import SafeConsolidator

        src = tmp_path / "src"
        subdir1 = src / "mod1"
        subdir2 = src / "mod2"
        subdir1.mkdir(parents=True)
        subdir2.mkdir(parents=True)

        # Two functional files with same name
        (subdir1 / "utils.py").write_text("def helper1(): pass")
        (subdir2 / "utils.py").write_text("def helper2(): pass")

        consolidator = SafeConsolidator(repo_root=str(tmp_path))
        actions = consolidator.identify_safe_consolidations()

        assert len(actions) == 1
        assert actions[0]["filename"] == "utils.py"
        assert actions[0]["action"] == "manual_review_needed"
        assert actions[0]["risk"] == "medium"


class TestExecuteSafeConsolidations:
    """Test execute_safe_consolidations method."""

    def test_dry_run_no_changes(self, tmp_path: Path):
        """Dry run does not delete files."""
        from src.tools.safe_consolidator import SafeConsolidator

        src = tmp_path / "src"
        subdir = src / "mod"
        subdir.mkdir(parents=True)
        empty_file = subdir / "empty.py"
        empty_file.write_text("")

        consolidator = SafeConsolidator(repo_root=str(tmp_path))
        consolidator.consolidation_actions = [
            {
                "filename": "empty.py",
                "action": "safe_removal",
                "preserve": subdir / "functional.py",
                "remove": [empty_file],
            }
        ]

        consolidator.execute_safe_consolidations(dry_run=True)
        assert empty_file.exists()  # Not deleted in dry run

    def test_live_execution_removes_files(self, tmp_path: Path):
        """Live execution removes empty files."""
        from src.tools.safe_consolidator import SafeConsolidator

        src = tmp_path / "src"
        subdir = src / "mod"
        subdir.mkdir(parents=True)
        empty_file = subdir / "empty.py"
        empty_file.write_text("")

        consolidator = SafeConsolidator(repo_root=str(tmp_path))
        consolidator.consolidation_actions = [
            {
                "filename": "empty.py",
                "action": "safe_removal",
                "preserve": subdir / "functional.py",
                "remove": [empty_file],
            }
        ]

        consolidator.execute_safe_consolidations(dry_run=False)
        assert not empty_file.exists()  # Deleted in live mode

    def test_skips_non_safe_removal_actions(self, tmp_path: Path):
        """Only processes safe_removal actions."""
        from src.tools.safe_consolidator import SafeConsolidator

        consolidator = SafeConsolidator(repo_root=str(tmp_path))
        consolidator.consolidation_actions = [
            {
                "filename": "conflict.py",
                "action": "manual_review_needed",
                "preserve": [],
                "remove": [],
            }
        ]

        # Should not raise and should complete without action
        consolidator.execute_safe_consolidations(dry_run=False)


class TestGenerateConsolidationReport:
    """Test generate_consolidation_report method."""

    def test_generates_json_report(self, tmp_path: Path):
        """Generates JSON report file."""
        from src.tools.safe_consolidator import SafeConsolidator

        consolidator = SafeConsolidator(repo_root=str(tmp_path))
        # Use strings to avoid JSON serialization issues with Path objects
        consolidator.consolidation_actions = [
            {
                "filename": "test.py",
                "action": "safe_removal",
                "preserve": str(tmp_path / "functional.py"),
                "remove": [str(tmp_path / "empty.py")],
            },
            {
                "filename": "conflict.py",
                "action": "manual_review_needed",
                "preserve": [str(tmp_path / "a.py"), str(tmp_path / "b.py")],
                "remove": [],
            },
        ]

        report = consolidator.generate_consolidation_report()

        # Check report structure
        assert report["timestamp"] == "2025-08-03"
        assert report["summary"]["total_duplicate_sets"] == 2
        assert report["summary"]["safe_removals"] == 1
        assert report["summary"]["manual_reviews"] == 1

        # Check file was created
        report_file = tmp_path / "SAFE_CONSOLIDATION_REPORT.json"
        assert report_file.exists()

        # Verify JSON content
        saved = json.loads(report_file.read_text())
        assert saved["summary"]["safe_removals"] == 1


# ==============================================================================
# vibe_indexer.py tests
# ==============================================================================
class TestFindMdFiles:
    """Test find_md_files function."""

    def test_finds_markdown_files(self, tmp_path: Path):
        """Finds .md files recursively."""
        from src.tools.vibe_indexer import find_md_files

        (tmp_path / "README.md").write_text("# Root readme")
        subdir = tmp_path / "docs"
        subdir.mkdir()
        (subdir / "GUIDE.md").write_text("# Guide")
        (tmp_path / "script.py").write_text("# not markdown")

        result = find_md_files(tmp_path)
        names = [p.name for p in result]
        assert "README.md" in names
        assert "GUIDE.md" in names
        assert "script.py" not in names

    def test_skips_git_directory(self, tmp_path: Path):
        """Skips files in .git directory."""
        from src.tools.vibe_indexer import find_md_files

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config.md").write_text("# git internal")
        (tmp_path / "README.md").write_text("# readme")

        result = find_md_files(tmp_path)
        names = [p.name for p in result]
        assert "README.md" in names
        assert "config.md" not in names


class TestParseMarkdownSections:
    """Test parse_markdown_sections function."""

    def test_parses_headings(self, tmp_path: Path):
        """Parses markdown headings into sections."""
        from src.tools.vibe_indexer import parse_markdown_sections

        md_file = tmp_path / "test.md"
        md_file.write_text("# Intro\nSome text\n## Details\nMore text")

        sections = parse_markdown_sections(md_file)
        assert len(sections) == 2
        assert sections[0][0] == "Intro"
        assert "Some text" in sections[0][1]
        assert sections[1][0] == "Details"
        assert "More text" in sections[1][1]

    def test_no_headings_uses_filename(self, tmp_path: Path):
        """File with no headings uses filename as heading."""
        from src.tools.vibe_indexer import parse_markdown_sections

        md_file = tmp_path / "notes.md"
        md_file.write_text("Just some plain text without headings.")

        sections = parse_markdown_sections(md_file)
        assert len(sections) == 1
        assert sections[0][0] == "notes"  # stem of filename


class TestExtractLinks:
    """Test extract_links function."""

    def test_extracts_markdown_links(self):
        """Extracts [text](url) links from text."""
        from src.tools.vibe_indexer import extract_links

        text = "Check out [GitHub](https://github.com) and [Docs](./docs/README.md)"
        links = extract_links(text)
        assert len(links) == 2
        assert links[0] == ("GitHub", "https://github.com")
        assert links[1] == ("Docs", "./docs/README.md")

    def test_no_links_returns_empty(self):
        """Returns empty list if no links."""
        from src.tools.vibe_indexer import extract_links

        text = "Plain text with no links here."
        links = extract_links(text)
        assert links == []


class TestHeuristicsForNode:
    """Test heuristics_for_node function."""

    def test_github_url(self):
        """GitHub URLs classified as repo."""
        from src.tools.vibe_indexer import heuristics_for_node

        result = heuristics_for_node("https://github.com/user/repo")
        assert result["kind"] == "repo"
        assert result["fit"] == "ide"

    def test_archive_url(self):
        """Archive URLs classified as artifact."""
        from src.tools.vibe_indexer import heuristics_for_node

        result = heuristics_for_node("https://example.com/release.zip")
        assert result["kind"] == "artifact"
        assert result["fit"] == "browser"

    def test_extension_url(self):
        """Extension URLs classified as plugin."""
        from src.tools.vibe_indexer import heuristics_for_node

        result = heuristics_for_node("https://chrome.google.com/webstore/extension")
        assert result["kind"] == "plugin"
        assert result["fit"] == "ide"

    def test_default_is_doc(self):
        """Unknown URLs default to doc."""
        from src.tools.vibe_indexer import heuristics_for_node

        result = heuristics_for_node("https://example.com/page")
        assert result["kind"] == "doc"
        assert result["fit"] == "doc"


class TestNodeIdFromTitle:
    """Test node_id_from_title function."""

    def test_creates_slug(self):
        """Creates URL-safe slug from title."""
        from src.tools.vibe_indexer import node_id_from_title

        result = node_id_from_title("Hello World Example")
        assert result == "hello-world-example"

    def test_handles_special_chars(self):
        """Handles special characters."""
        from src.tools.vibe_indexer import node_id_from_title

        result = node_id_from_title("Test: Example (v2.0)")
        assert result == "test-example-v2-0"

    def test_empty_fallback(self):
        """Empty title returns 'node'."""
        from src.tools.vibe_indexer import node_id_from_title

        result = node_id_from_title("!!!")
        assert result == "node"


class TestBuildLattice:
    """Test build_lattice function."""

    def test_builds_lattice_structure(self, tmp_path: Path):
        """Builds complete lattice from markdown files."""
        from src.tools.vibe_indexer import build_lattice

        md_file = tmp_path / "README.md"
        md_file.write_text("# Main\nCheck [link](https://example.com)")

        lattice = build_lattice(tmp_path)
        assert lattice["lattice"] == "vibe-coding"
        assert "rev" in lattice
        assert "nodes" in lattice
        assert "edges" in lattice
        assert len(lattice["nodes"]) >= 1
        assert len(lattice["edges"]) >= 1


class TestVibeIndexerMain:
    """Test main CLI function."""

    def test_nonexistent_path_returns_2(self, tmp_path: Path):
        """Returns 2 for nonexistent path."""
        from src.tools.vibe_indexer import main

        result = main(["nonexistent_path_xyz"])
        assert result == 2

    def test_successful_indexing(self, tmp_path: Path):
        """Successfully indexes directory and writes output."""
        from src.tools.vibe_indexer import main

        (tmp_path / "README.md").write_text("# Test")
        out_file = tmp_path / "out" / "lattice.json"

        result = main([str(tmp_path), "--out", str(out_file)])
        assert result == 0
        assert out_file.exists()

        data = json.loads(out_file.read_text())
        assert data["lattice"] == "vibe-coding"


# ==============================================================================
# consolidation_planner.py tests
# ==============================================================================
class TestKILOConsolidationPlannerInit:
    """Test KILOConsolidationPlanner initialization."""

    def test_init_defaults(self, tmp_path: Path):
        """Verify default initialization with hardcoded actions."""
        from src.tools.consolidation_planner import KILOConsolidationPlanner

        planner = KILOConsolidationPlanner(repo_root=str(tmp_path))
        assert planner.repo_root == tmp_path
        assert len(planner.consolidation_actions) == 3
        assert planner.consolidation_actions[0]["type"] == "empty_file_cleanup"
        assert planner.consolidation_actions[1]["type"] == "broken_file_repair"
        assert planner.consolidation_actions[2]["type"] == "import_dependency_healing"


class TestAnalyzeConsolidationImpact:
    """Test analyze_consolidation_impact method."""

    def test_analyzes_existing_files(self, tmp_path: Path):
        """Analyzes impact on existing files."""
        from src.tools.consolidation_planner import KILOConsolidationPlanner

        # Create the files referenced in hardcoded actions
        core_dir = tmp_path / "src" / "core"
        ai_dir = tmp_path / "src" / "ai"
        core_dir.mkdir(parents=True)
        ai_dir.mkdir(parents=True)

        (core_dir / "ai_coordinator.py").write_text("")  # empty
        (ai_dir / "ai_coordinator.py").write_text("# functional\n" * 100)

        planner = KILOConsolidationPlanner(repo_root=str(tmp_path))
        # Should not raise
        planner.analyze_consolidation_impact()

    def test_handles_missing_files(self, tmp_path: Path):
        """Handles case where referenced files don't exist."""
        from src.tools.consolidation_planner import KILOConsolidationPlanner

        planner = KILOConsolidationPlanner(repo_root=str(tmp_path))
        # Should not raise even with missing files
        planner.analyze_consolidation_impact()


class TestCreateConsolidationScript:
    """Test create_consolidation_script method."""

    def test_creates_script_file(self, tmp_path: Path):
        """Creates safe_consolidation.py script."""
        from src.tools.consolidation_planner import KILOConsolidationPlanner

        planner = KILOConsolidationPlanner(repo_root=str(tmp_path))
        planner.create_consolidation_script()

        script_path = tmp_path / "safe_consolidation.py"
        assert script_path.exists()

        content = script_path.read_text()
        assert "def safe_consolidation" in content
        assert "dry_run=True" in content
        assert "KILO-FOOLISH" in content


class TestGenerateConsolidationReportPlanner:
    """Test generate_consolidation_report method."""

    def test_runs_without_error(self, tmp_path: Path):
        """generate_consolidation_report runs without error (empty body)."""
        from src.tools.consolidation_planner import KILOConsolidationPlanner

        planner = KILOConsolidationPlanner(repo_root=str(tmp_path))
        # Method has empty body but should not raise
        planner.generate_consolidation_report()
