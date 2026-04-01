"""Tests for small infrastructure modules - batch 8.

Coverage targets:
- src/utilities/performance_analyzer.py: PerformanceMetric, PerformanceAnalyzer
- src/system/knowledge.py: ingest_artifacts, load_patterns, three_before_new
- src/tagging/tag_processors.py: process_omni_tags, process_mega_tags, etc.
"""

from __future__ import annotations


# ==============================================================================
# src/utilities/performance_analyzer.py tests
# ==============================================================================
class TestPerformanceMetricDataclass:
    """Test PerformanceMetric dataclass."""

    def test_metric_creation(self):
        """PerformanceMetric stores values correctly."""
        from src.utilities.performance_analyzer import PerformanceMetric

        metric = PerformanceMetric(
            name="response_time",
            value=123.5,
            unit="ms",
            timestamp="2024-01-01T00:00:00Z",
        )
        assert metric.name == "response_time"
        assert metric.value == 123.5
        assert metric.unit == "ms"


class TestPerformanceAnalyzerInit:
    """Test PerformanceAnalyzer initialization."""

    def test_init_empty_metrics(self):
        """Analyzer starts with empty metrics list."""
        from src.utilities.performance_analyzer import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer()
        assert analyzer.metrics == []


class TestPerformanceAnalyzerAddMetric:
    """Test PerformanceAnalyzer.add_metric."""

    def test_add_metric(self):
        """add_metric creates and stores a metric."""
        from src.utilities.performance_analyzer import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer()
        analyzer.add_metric("test_metric", 100.0)
        assert len(analyzer.metrics) == 1
        assert analyzer.metrics[0].name == "test_metric"
        assert analyzer.metrics[0].value == 100.0

    def test_add_metric_with_unit(self):
        """add_metric uses custom unit."""
        from src.utilities.performance_analyzer import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer()
        analyzer.add_metric("memory", 512.0, unit="MB")
        assert analyzer.metrics[0].unit == "MB"


class TestPerformanceAnalyzerGetAverage:
    """Test PerformanceAnalyzer.get_average."""

    def test_get_average_no_metrics(self):
        """get_average returns None when no matching metrics."""
        from src.utilities.performance_analyzer import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer()
        assert analyzer.get_average("missing") is None

    def test_get_average_single_metric(self):
        """get_average with single metric returns value."""
        from src.utilities.performance_analyzer import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer()
        analyzer.add_metric("time", 100.0)
        assert analyzer.get_average("time") == 100.0

    def test_get_average_multiple_metrics(self):
        """get_average calculates correct average."""
        from src.utilities.performance_analyzer import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer()
        analyzer.add_metric("time", 100.0)
        analyzer.add_metric("time", 200.0)
        analyzer.add_metric("time", 300.0)
        assert analyzer.get_average("time") == 200.0


class TestPerformanceAnalyzerGetStats:
    """Test PerformanceAnalyzer.get_stats."""

    def test_get_stats_empty(self):
        """get_stats returns empty dict when no metrics."""
        from src.utilities.performance_analyzer import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer()
        assert analyzer.get_stats() == {}

    def test_get_stats_single_metric(self):
        """get_stats with single metric."""
        from src.utilities.performance_analyzer import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer()
        analyzer.add_metric("test", 50.0)
        stats = analyzer.get_stats()
        assert "test" in stats
        assert stats["test"]["count"] == 1
        assert stats["test"]["min"] == 50.0
        assert stats["test"]["max"] == 50.0

    def test_get_stats_multiple_metrics(self):
        """get_stats with multiple metric types."""
        from src.utilities.performance_analyzer import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer()
        analyzer.add_metric("time", 10.0)
        analyzer.add_metric("time", 20.0)
        analyzer.add_metric("memory", 100.0)

        stats = analyzer.get_stats()
        assert "time" in stats
        assert "memory" in stats
        assert stats["time"]["count"] == 2
        assert stats["time"]["avg"] == 15.0
        assert stats["memory"]["count"] == 1


# ==============================================================================
# src/system/knowledge.py tests
# ==============================================================================
class TestIngestArtifacts:
    """Test ingest_artifacts function."""

    def test_returns_zero_when_disabled(self, monkeypatch):
        """Returns 0 when feature disabled."""
        monkeypatch.setattr("src.system.knowledge.is_feature_enabled", lambda x: False)
        from src.system.knowledge import ingest_artifacts

        result = ingest_artifacts()
        assert result == 0

    def test_returns_zero_no_artifacts(self, tmp_path, monkeypatch):
        """Returns 0 when no artifacts exist."""
        monkeypatch.setattr("src.system.knowledge.is_feature_enabled", lambda x: True)
        monkeypatch.setattr("src.system.knowledge.ARTIFACT_ROOT", tmp_path / "artifacts")
        from src.system.knowledge import ingest_artifacts

        (tmp_path / "artifacts").mkdir()
        result = ingest_artifacts()
        assert result == 0


class TestLoadPatterns:
    """Test load_patterns function."""

    def test_load_nonexistent_file(self, tmp_path, monkeypatch):
        """Returns empty list when file doesn't exist."""
        monkeypatch.setattr(
            "src.system.knowledge.PATTERN_CATALOG",
            tmp_path / "nonexistent.jsonl",
        )
        from src.system.knowledge import load_patterns

        result = load_patterns()
        assert result == []

    def test_load_patterns_from_file(self, tmp_path, monkeypatch):
        """Loads patterns from JSONL file."""
        pattern_file = tmp_path / "patterns.jsonl"
        pattern_file.write_text(
            '{"id": "p1", "description": "Pattern 1"}\n{"id": "p2", "description": "Pattern 2"}\n'
        )
        monkeypatch.setattr("src.system.knowledge.PATTERN_CATALOG", pattern_file)
        from src.system.knowledge import load_patterns

        result = load_patterns()
        assert len(result) == 2
        assert result[0]["id"] == "p1"


class TestThreeBeforeNew:
    """Test three_before_new function."""

    def test_disabled_returns_empty(self, monkeypatch):
        """Returns empty when feature disabled."""
        monkeypatch.setattr("src.system.knowledge.is_feature_enabled", lambda x: False)
        from src.system.knowledge import three_before_new

        result = three_before_new("test")
        assert result == []

    def test_matches_capability(self, tmp_path, monkeypatch):
        """Returns matching patterns."""
        monkeypatch.setattr("src.system.knowledge.is_feature_enabled", lambda x: True)
        pattern_file = tmp_path / "patterns.jsonl"
        pattern_file.write_text(
            '{"id": "p1", "description": "TestCapability handler"}\n'
            '{"id": "p2", "description": "Other thing"}\n'
        )
        monkeypatch.setattr("src.system.knowledge.PATTERN_CATALOG", pattern_file)
        from src.system.knowledge import three_before_new

        result = three_before_new("TestCapability")
        assert len(result) == 1
        assert "p1" in result[0]


class TestAppendLesson:
    """Test append_lesson function."""

    def test_disabled_no_op(self, tmp_path, monkeypatch):
        """Does nothing when feature disabled."""
        monkeypatch.setattr("src.system.knowledge.is_feature_enabled", lambda x: False)
        monkeypatch.setattr("src.system.knowledge.LESSONS_LOG", tmp_path / "lessons.jsonl")
        from src.system.knowledge import append_lesson

        append_lesson({"lesson": "test"})
        assert not (tmp_path / "lessons.jsonl").exists()

    def test_appends_when_enabled(self, tmp_path, monkeypatch):
        """Appends lesson to file when enabled."""
        monkeypatch.setattr("src.system.knowledge.is_feature_enabled", lambda x: True)
        lessons_file = tmp_path / "reports" / "lessons.jsonl"
        monkeypatch.setattr("src.system.knowledge.LESSONS_LOG", lessons_file)
        from src.system.knowledge import append_lesson

        append_lesson({"lesson": "test lesson"})
        assert lessons_file.exists()
        content = lessons_file.read_text()
        assert "test lesson" in content


# ==============================================================================
# src/tagging/tag_processors.py tests
# ==============================================================================
class TestProcessOmniTags:
    """Test process_omni_tags function."""

    def test_empty_tags(self):
        """Processes empty tag list."""
        from src.tagging.tag_processors import process_omni_tags

        result = process_omni_tags([])
        assert result == {}

    def test_single_tag(self):
        """Processes single tag."""
        from src.tagging.tag_processors import process_omni_tags

        result = process_omni_tags(["test_tag"])
        assert "test_tag" in result
        assert result["test_tag"]["type"] == "OmniTag"

    def test_multiple_tags(self):
        """Processes multiple tags."""
        from src.tagging.tag_processors import process_omni_tags

        result = process_omni_tags(["tag1", "tag2", "tag3"])
        assert len(result) == 3


class TestProcessMegaTags:
    """Test process_mega_tags function."""

    def test_empty_tags(self):
        """Processes empty tag list."""
        from src.tagging.tag_processors import process_mega_tags

        result = process_mega_tags([])
        assert result == {}

    def test_single_tag(self):
        """Processes single tag."""
        from src.tagging.tag_processors import process_mega_tags

        result = process_mega_tags(["mega_tag"])
        assert "mega_tag" in result
        assert result["mega_tag"]["type"] == "MegaTag"


class TestEnhanceContextWithTags:
    """Test enhance_context_with_tags function."""

    def test_empty_context(self):
        """Enhances empty context."""
        from src.tagging.tag_processors import enhance_context_with_tags

        context: dict = {}
        result = enhance_context_with_tags(context, ["tag1"])
        assert "tags" in result
        assert "omni_tags" in result["tags"]
        assert "mega_tags" in result["tags"]

    def test_existing_tags(self):
        """Preserves existing tags."""
        from src.tagging.tag_processors import enhance_context_with_tags

        context = {"tags": {"existing": "value"}}
        result = enhance_context_with_tags(context, ["new_tag"])
        assert "omni_tags" in result["tags"]
        assert "existing" in result["tags"]


class TestValidateTags:
    """Test validate_tags function."""

    def test_valid_tags(self):
        """Valid tags return True."""
        from src.tagging.tag_processors import validate_tags

        assert validate_tags(["tag1", "tag2"]) is True

    def test_empty_list_is_valid(self):
        """Empty list is valid."""
        from src.tagging.tag_processors import validate_tags

        assert validate_tags([]) is True

    def test_empty_string_invalid(self):
        """Empty string tag is invalid."""
        from src.tagging.tag_processors import validate_tags

        assert validate_tags([""]) is False


class TestExtractTagsFromContext:
    """Test extract_tags_from_context function."""

    def test_no_tags_section(self):
        """Returns empty when no tags section."""
        from src.tagging.tag_processors import extract_tags_from_context

        result = extract_tags_from_context({})
        assert result == []

    def test_extracts_both_tag_types(self):
        """Extracts both omni and mega tags."""
        from src.tagging.tag_processors import extract_tags_from_context

        context = {
            "tags": {
                "omni_tags": {"omni1": {}, "omni2": {}},
                "mega_tags": {"mega1": {}},
            }
        }
        result = extract_tags_from_context(context)
        assert len(result) == 3
        assert "omni1" in result
        assert "mega1" in result
