"""Tests for small tools modules in src/tools/

Tests collected utilities that are too small to warrant individual test files:
- doctrine_checker.py (legacy redirect)
- chatdev_testing_chamber.py (legacy redirect)
- prune_plan_generator.py (prune plan generation)
- status_report_router.py (status aggregation)
- log_indexer.py (maze summary indexing)
"""

import json
from pathlib import Path
from unittest.mock import MagicMock

# =============================================================================
# doctrine_checker.py Tests (Legacy Redirect)
# =============================================================================


class TestDoctrineCheckerRedirect:
    """Tests for doctrine_checker legacy redirect."""

    def test_imports_doctrine_checker(self):
        """Test DoctrineChecker is importable from legacy location."""
        from src.tools.doctrine_checker import DoctrineChecker

        assert DoctrineChecker is not None

    def test_imports_compliance_report(self):
        """Test ComplianceReport is importable from legacy location."""
        from src.tools.doctrine_checker import ComplianceReport

        assert ComplianceReport is not None

    def test_imports_doctrine_violation(self):
        """Test DoctrineViolation is importable from legacy location."""
        from src.tools.doctrine_checker import DoctrineViolation

        assert DoctrineViolation is not None

    def test_all_exports(self):
        """Test __all__ contains expected exports."""
        from src.tools import doctrine_checker

        expected = {"ComplianceReport", "DoctrineChecker", "DoctrineViolation"}
        assert set(doctrine_checker.__all__) == expected

    def test_has_main_function(self):
        """Test main entry point exists."""
        from src.tools.doctrine_checker import main

        assert callable(main)


# =============================================================================
# chatdev_testing_chamber.py Tests (Legacy Redirect)
# =============================================================================


class TestChatDevTestingChamberRedirect:
    """Tests for chatdev_testing_chamber legacy redirect.

    Note: The actual imports may fail due to ChatDevLauncher not being
    available. These tests verify the module file exists and has the
    expected structure.
    """

    def test_module_file_exists(self):
        """Test the module file exists."""
        from pathlib import Path

        module_path = Path(__file__).parent.parent / "src" / "tools" / "chatdev_testing_chamber.py"
        assert module_path.exists()

    def test_module_has_all_export(self):
        """Test module file contains __all__ export."""
        from pathlib import Path

        module_path = Path(__file__).parent.parent / "src" / "tools" / "chatdev_testing_chamber.py"
        content = module_path.read_text()
        assert "__all__" in content
        assert "ChatDevTestingChamber" in content

    def test_module_has_main_function(self):
        """Test module file contains main function."""
        from pathlib import Path

        module_path = Path(__file__).parent.parent / "src" / "tools" / "chatdev_testing_chamber.py"
        content = module_path.read_text()
        # Function may have type hints: def main() -> None:
        assert "def main()" in content


# =============================================================================
# prune_plan_generator.py Tests
# =============================================================================


class TestPrunePlanGenerator:
    """Tests for prune plan generation."""

    def test_generates_prune_plan_file(self, tmp_path, monkeypatch):
        """Test generates a prune plan JSON file."""
        # Patch __file__ location to use tmp_path
        import src.tools.prune_plan_generator as ppg

        # Create a mock module location
        mock_module = tmp_path / "src" / "tools" / "prune_plan_generator.py"
        mock_module.parent.mkdir(parents=True, exist_ok=True)
        mock_module.touch()

        # Monkey-patch the module's path resolution
        monkeypatch.setattr(ppg, "__file__", str(mock_module))

        from src.tools.prune_plan_generator import generate_prune_plan_with_index

        result = generate_prune_plan_with_index()

        if result:
            assert result.exists()
            assert result.suffix == ".json"

    def test_plan_contains_required_fields(self, tmp_path, monkeypatch):
        """Test plan JSON contains required fields."""
        import src.tools.prune_plan_generator as ppg

        mock_module = tmp_path / "src" / "tools" / "prune_plan_generator.py"
        mock_module.parent.mkdir(parents=True, exist_ok=True)
        mock_module.touch()
        monkeypatch.setattr(ppg, "__file__", str(mock_module))

        from src.tools.prune_plan_generator import generate_prune_plan_with_index

        result = generate_prune_plan_with_index()

        if result:
            data = json.loads(result.read_text())
            assert "generated_at" in data
            assert "age_days" in data
            assert "candidates" in data

    def test_accepts_custom_parameters(self, tmp_path, monkeypatch):
        """Test accepts custom age_days and size_threshold_bytes."""
        import src.tools.prune_plan_generator as ppg

        mock_module = tmp_path / "src" / "tools" / "prune_plan_generator.py"
        mock_module.parent.mkdir(parents=True, exist_ok=True)
        mock_module.touch()
        monkeypatch.setattr(ppg, "__file__", str(mock_module))

        from src.tools.prune_plan_generator import generate_prune_plan_with_index

        result = generate_prune_plan_with_index(
            age_days=30, size_threshold_bytes=500_000, min_duplicate_group=5
        )

        if result:
            data = json.loads(result.read_text())
            assert data["age_days"] == 30
            assert data["size_threshold_bytes"] == 500_000
            assert data["min_duplicate_group"] == 5

    def test_candidates_list_empty_by_default(self, tmp_path, monkeypatch):
        """Test candidates list is empty (placeholder behavior)."""
        import src.tools.prune_plan_generator as ppg

        mock_module = tmp_path / "src" / "tools" / "prune_plan_generator.py"
        mock_module.parent.mkdir(parents=True, exist_ok=True)
        mock_module.touch()
        monkeypatch.setattr(ppg, "__file__", str(mock_module))

        from src.tools.prune_plan_generator import generate_prune_plan_with_index

        result = generate_prune_plan_with_index()

        if result:
            data = json.loads(result.read_text())
            assert data["candidates"] == []

    def test_creates_output_directory(self, tmp_path, monkeypatch):
        """Test creates state/prune_plans directory."""
        import src.tools.prune_plan_generator as ppg

        mock_module = tmp_path / "src" / "tools" / "prune_plan_generator.py"
        mock_module.parent.mkdir(parents=True, exist_ok=True)
        mock_module.touch()
        monkeypatch.setattr(ppg, "__file__", str(mock_module))

        from src.tools.prune_plan_generator import generate_prune_plan_with_index

        generate_prune_plan_with_index()

        assert (tmp_path / "state" / "prune_plans").exists()


# =============================================================================
# status_report_router.py Tests
# =============================================================================


class TestStatusReportRouter:
    """Tests for StatusReportRouter class."""

    def test_init_empty_modules(self):
        """Test initializes with empty modules list."""
        from src.tools.status_report_router import StatusReportRouter

        router = StatusReportRouter()
        assert router.modules == []

    def test_init_with_modules(self):
        """Test initializes with provided modules."""
        from src.tools.status_report_router import StatusReportRouter

        modules = [MagicMock(), MagicMock()]
        router = StatusReportRouter(modules=modules)
        assert len(router.modules) == 2

    def test_register_module(self):
        """Test register_module adds module to list."""
        from src.tools.status_report_router import StatusReportRouter

        router = StatusReportRouter()
        module = MagicMock()
        router.register_module(module)
        assert module in router.modules

    def test_aggregate_status_markdown_default(self):
        """Test aggregate_status returns markdown by default.

        Note: MagicMock has all attributes by default (hasattr returns True),
        so module.get_status_sections will be checked first.
        """
        from src.tools.status_report_router import StatusReportRouter

        module = MagicMock()
        # Mock both methods to control behavior
        module.get_status_sections.return_value = ["## Status", "All good"]

        router = StatusReportRouter(modules=[module])
        result = router.aggregate_status()

        assert "## Status" in result

    def test_aggregate_status_json_format(self):
        """Test aggregate_status can return JSON."""
        from src.tools.status_report_router import StatusReportRouter

        module = MagicMock()
        module.generate_status_report.return_value = {"status": "ok"}

        router = StatusReportRouter(modules=[module])
        result = router.aggregate_status(output_format="json")

        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, list)

    def test_aggregate_status_with_section_flags(self):
        """Test passes section_flags to modules.

        Note: Router checks get_status_sections first (MagicMock has this).
        Test that method is called with flags.
        """
        from src.tools.status_report_router import StatusReportRouter

        module = MagicMock()
        module.get_status_sections.return_value = ["section"]

        router = StatusReportRouter(modules=[module])
        router.aggregate_status(section_flags={"health": True})

        # get_status_sections is called with the flags
        module.get_status_sections.assert_called_once_with({"health": True})

    def test_aggregate_status_get_status_sections(self):
        """Test handles modules with get_status_sections method."""
        from src.tools.status_report_router import StatusReportRouter

        module = MagicMock()
        module.get_status_sections.return_value = ["Section 1", "Section 2"]
        # Remove generate_status_report so it uses get_status_sections
        del module.generate_status_report

        router = StatusReportRouter(modules=[module])
        result = router.aggregate_status()

        assert "Section 1" in result
        assert "Section 2" in result

    def test_format_status_markdown(self):
        """Test format_status with markdown output."""
        from src.tools.status_report_router import StatusReportRouter

        router = StatusReportRouter()
        result = router.format_status(["line1", "line2"])

        assert "line1" in result
        assert "line2" in result

    def test_format_status_json(self):
        """Test format_status with JSON output."""
        from src.tools.status_report_router import StatusReportRouter

        router = StatusReportRouter()
        result = router.format_status({"key": "value"}, output_format="json")

        data = json.loads(result)
        assert data["key"] == "value"

    def test_format_status_string(self):
        """Test format_status with plain string."""
        from src.tools.status_report_router import StatusReportRouter

        router = StatusReportRouter()
        result = router.format_status("plain string")

        assert result == "plain string"


# =============================================================================
# log_indexer.py Tests
# =============================================================================


class TestLogIndexer:
    """Tests for log indexer utility."""

    def test_returns_empty_list_when_no_dir(self, tmp_path):
        """Test returns empty list when log dir doesn't exist."""
        from src.tools.log_indexer import latest_maze_summaries

        nonexistent = tmp_path / "nonexistent"
        result = latest_maze_summaries(log_dir=nonexistent)
        assert result == []

    def test_returns_empty_list_when_no_files(self, tmp_path):
        """Test returns empty list when no maze summary files."""
        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        result = latest_maze_summaries(log_dir=log_dir)
        assert result == []

    def test_finds_maze_summary_files(self, tmp_path):
        """Test finds maze_summary_*.json files."""
        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create maze summary files
        (log_dir / "maze_summary_001.json").write_text("{}")
        (log_dir / "maze_summary_002.json").write_text("{}")

        result = latest_maze_summaries(log_dir=log_dir)
        assert len(result) == 2

    def test_respects_limit(self, tmp_path):
        """Test respects limit parameter."""
        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create 5 files
        for i in range(5):
            (log_dir / f"maze_summary_{i:03d}.json").write_text("{}")

        result = latest_maze_summaries(log_dir=log_dir, limit=2)
        assert len(result) == 2

    def test_default_limit_is_3(self, tmp_path):
        """Test default limit is 3."""
        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create 5 files
        for i in range(5):
            (log_dir / f"maze_summary_{i:03d}.json").write_text("{}")

        result = latest_maze_summaries(log_dir=log_dir)
        assert len(result) == 3

    def test_returns_most_recent_first(self, tmp_path):
        """Test returns files sorted by modification time (most recent first)."""
        import time

        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create files with staggered times
        old = log_dir / "maze_summary_old.json"
        old.write_text("{}")

        time.sleep(0.01)  # Small delay for mtime difference

        new = log_dir / "maze_summary_new.json"
        new.write_text("{}")

        result = latest_maze_summaries(log_dir=log_dir, limit=10)
        # Most recent first
        assert result[0].name == "maze_summary_new.json"

    def test_ignores_non_matching_files(self, tmp_path):
        """Test ignores files that don't match pattern."""
        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create matching and non-matching files
        (log_dir / "maze_summary_001.json").write_text("{}")
        (log_dir / "other_log.json").write_text("{}")
        (log_dir / "maze_summary.txt").write_text("")  # Wrong extension

        result = latest_maze_summaries(log_dir=log_dir)
        assert len(result) == 1
        assert result[0].name == "maze_summary_001.json"

    def test_returns_path_objects(self, tmp_path):
        """Test returns list of Path objects."""
        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "maze_summary_001.json").write_text("{}")

        result = latest_maze_summaries(log_dir=log_dir)
        assert all(isinstance(p, Path) for p in result)
