"""
Tests for HintEngine: AI-powered quest suggestion system

Comprehensive test suite covering:
- Quest loading and categorization
- Dependency analysis
- Scoring algorithms
- Suggestion ranking
- Integration scenarios
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.tools.hint_engine import HintEngine, HintResult, QuestScore


class TestQuestScore:
    """Test QuestScore data class."""

    def test_score_initialization(self):
        """Test QuestScore initialization."""
        score = QuestScore(quest_id="Q1", quest_title="Test Quest")
        assert score.quest_id == "Q1"
        assert score.quest_title == "Test Quest"
        assert score.base_priority == 1
        assert score.final_score == 0.0

    def test_score_calculation(self):
        """Test score calculation."""
        score = QuestScore(
            quest_id="Q1",
            quest_title="Test",
            base_priority=10,
            zeta_stage_boost=1.5,
            blocked_penalty=1.0,
            effort_factor=1.0,
            dependency_factor=1.0,
        )
        final = score.calculate()
        assert final == 15.0  # 10 * 1.5 / 1.0 * 1.0 * 1.0


class TestHintEngineInit:
    """Test HintEngine initialization."""

    def test_default_initialization(self):
        """Test default engine initialization."""
        engine = HintEngine()
        assert engine.quests == {}
        assert engine.zeta_data == {}
        assert engine.actionable_quests == []
        assert engine.blocked_quests == []

    def test_custom_initialization(self):
        """Test with custom paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quests.jsonl"
            zeta_path = tmpdir_path / "zeta.json"

            engine = HintEngine(quest_log_path=quest_path, zeta_tracker_path=zeta_path)
            assert engine.quest_log_path == quest_path
            assert engine.zeta_tracker_path == zeta_path


class TestQuestLoading:
    """Test quest loading functionality."""

    def test_load_quests_success(self):
        """Test successful quest loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            quest_data = [
                {"id": "Q1", "title": "First Quest"},
                {"id": "Q2", "title": "Second Quest"},
            ]

            with open(quest_path, "w", encoding="utf-8") as f:
                for quest in quest_data:
                    f.write(json.dumps(quest) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            assert engine.load_quests()
            assert len(engine.quests) == 2
            assert "Q1" in engine.quests

    def test_load_quests_missing_file(self):
        """Test loading from missing file."""
        engine = HintEngine(quest_log_path=Path("/nonexistent/path"))
        assert not engine.load_quests()

    def test_load_quests_empty_file(self):
        """Test loading from empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"
            quest_path.write_text("", encoding="utf-8")

            engine = HintEngine(quest_log_path=quest_path)
            assert engine.load_quests()
            assert len(engine.quests) == 0

    def test_load_quests_malformed_json(self):
        """Test loading with some malformed JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            content = '{"id": "Q1"}\n{invalid json\n{"id": "Q2"}\n'
            quest_path.write_text(content, encoding="utf-8")

            engine = HintEngine(quest_log_path=quest_path)
            assert engine.load_quests()
            assert len(engine.quests) == 2  # Valid entries only


class TestZetaTrackerLoading:
    """Test ZETA tracker loading."""

    def test_load_zeta_tracker_success(self):
        """Test successful ZETA tracker loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            zeta_path = tmpdir_path / "zeta.json"

            zeta_data = {
                "phase": 1,
                "tasks": {
                    "ZETA_1_001": {"status": "completed"},
                    "ZETA_1_002": {"status": "in_progress"},
                },
            }

            with open(zeta_path, "w", encoding="utf-8") as f:
                json.dump(zeta_data, f)

            engine = HintEngine(zeta_tracker_path=zeta_path)
            assert engine.load_zeta_tracker()
            assert "tasks" in engine.zeta_data

    def test_load_zeta_tracker_missing_file(self):
        """Test loading from missing ZETA file."""
        engine = HintEngine(zeta_tracker_path=Path("/nonexistent/path"))
        assert not engine.load_zeta_tracker()


class TestDependencyGraph:
    """Test dependency graph building."""

    def test_build_dependency_graph(self):
        """Test building dependency graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            quests = [
                {"id": "Q1", "title": "Base Quest", "dependencies": []},
                {"id": "Q2", "title": "Dependent Quest", "dependencies": ["Q1"]},
            ]

            with open(quest_path, "w", encoding="utf-8") as f:
                for q in quests:
                    f.write(json.dumps(q) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            engine.load_quests()
            engine.build_dependency_graph()

            if engine.dependency_graph is not None:
                assert "Q1" in engine.dependency_graph
                assert "Q2" in engine.dependency_graph

    def test_build_dependency_graph_no_networkx(self):
        """Test graph building without NetworkX."""
        with patch("src.tools.hint_engine.nx", None):
            engine = HintEngine()
            engine.build_dependency_graph()
            # Should handle gracefully
            assert engine.dependency_graph is None


class TestQuestCategorization:
    """Test quest categorization."""

    def test_categorize_actionable_quests(self):
        """Test categorization of actionable quests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            quests = [
                {"id": "Q1", "title": "Quest 1", "dependencies": []},
                {"id": "Q2", "title": "Quest 2", "dependencies": ["Q1"]},
            ]

            with open(quest_path, "w", encoding="utf-8") as f:
                for q in quests:
                    f.write(json.dumps(q) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            engine.load_quests()
            engine.categorize_quests()

            assert "Q1" in engine.actionable_quests

    def test_categorize_blocked_quests(self):
        """Test categorization of blocked quests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"
            zeta_path = tmpdir_path / "zeta.json"

            quests = [
                {
                    "id": "Q1",
                    "title": "Quest 1",
                    "dependencies": [],
                    "zeta_tags": ["ZETA_1_001"],
                },
                {
                    "id": "Q2",
                    "title": "Quest 2",
                    "dependencies": ["Q1"],
                    "zeta_tags": ["ZETA_1_002"],
                },
            ]

            with open(quest_path, "w", encoding="utf-8") as f:
                for q in quests:
                    f.write(json.dumps(q) + "\n")

            zeta_data = {
                "phase": 1,
                "tasks": {
                    "ZETA_1_001": {"status": "not_started"},
                    "ZETA_1_002": {"status": "not_started"},
                },
            }

            with open(zeta_path, "w", encoding="utf-8") as f:
                json.dump(zeta_data, f)

            engine = HintEngine(quest_log_path=quest_path, zeta_tracker_path=zeta_path)
            engine.load_quests()
            engine.load_zeta_tracker()
            engine.categorize_quests()

            # Q2 should be blocked by Q1
            assert "Q2" in engine.blocked_quests


class TestScoring:
    """Test quest scoring."""

    def test_score_with_high_priority(self):
        """Test scoring with high priority."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            quest = {
                "id": "Q1",
                "title": "Important Quest",
                "priority_tags": ["high"],
            }

            with open(quest_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(quest) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            engine.load_quests()
            engine.actionable_quests = ["Q1"]

            score = engine.score_quest("Q1")
            assert score.base_priority == 7

    def test_score_with_low_effort(self):
        """Test scoring with low effort."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            quest = {
                "id": "Q1",
                "title": "Quick Quest",
                "effort_estimate": "low",
            }

            with open(quest_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(quest) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            engine.load_quests()
            engine.actionable_quests = ["Q1"]

            score = engine.score_quest("Q1")
            assert score.effort_factor == 1.2

    def test_score_with_blocked_quest(self):
        """Test scoring with blocked quest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            quest = {"id": "Q1", "title": "Blocked Quest"}

            with open(quest_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(quest) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            engine.load_quests()
            engine.blocked_quests = ["Q1"]

            score = engine.score_quest("Q1")
            assert score.blocked_penalty == 3.0


class TestSuggestions:
    """Test suggestion generation."""

    def test_suggest_next_quests(self):
        """Test basic suggestion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            quests = [
                {
                    "id": "Q1",
                    "title": "First Quest",
                    "priority_tags": ["high"],
                    "dependencies": [],
                },
                {
                    "id": "Q2",
                    "title": "Second Quest",
                    "priority_tags": ["medium"],
                    "dependencies": [],
                },
            ]

            with open(quest_path, "w", encoding="utf-8") as f:
                for q in quests:
                    f.write(json.dumps(q) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            engine.load_quests()
            engine.categorize_quests()

            result = engine.suggest_next_quests(count=2)

            assert isinstance(result, HintResult)
            assert len(result.suggested_quests) <= 2

    def test_suggest_respects_count(self):
        """Test that suggestion respects count parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            # Create 10 quests
            with open(quest_path, "w", encoding="utf-8") as f:
                for i in range(10):
                    quest = {
                        "id": f"Q{i}",
                        "title": f"Quest {i}",
                        "dependencies": [],
                    }
                    f.write(json.dumps(quest) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            engine.load_quests()
            engine.categorize_quests()

            result = engine.suggest_next_quests(count=3)

            assert len(result.suggested_quests) <= 3

    def test_suggestion_result_has_reasoning(self):
        """Test that suggestions include reasoning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            quest = {"id": "Q1", "title": "Test Quest"}

            with open(quest_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(quest) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            engine.load_quests()
            engine.categorize_quests()

            result = engine.suggest_next_quests(count=1)

            assert result.reasoning
            assert (
                "analyzing" in result.reasoning.lower() or "suggestions" in result.reasoning.lower()
            )


class TestRunIntegration:
    """Test complete engine run."""

    def test_run_full_workflow(self):
        """Test full engine workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"
            zeta_path = tmpdir_path / "zeta.json"

            quests = [
                {
                    "id": "Q1",
                    "title": "First Quest",
                    "priority_tags": ["high"],
                    "dependencies": [],
                    "zeta_tags": ["ZETA_1_001"],
                },
                {
                    "id": "Q2",
                    "title": "Second Quest",
                    "dependencies": ["Q1"],
                    "zeta_tags": ["ZETA_1_002"],
                },
            ]

            with open(quest_path, "w", encoding="utf-8") as f:
                for q in quests:
                    f.write(json.dumps(q) + "\n")

            zeta_data = {
                "phase": 1,
                "tasks": {
                    "ZETA_1_001": {"status": "not_started"},
                    "ZETA_1_002": {"status": "not_started"},
                },
            }

            with open(zeta_path, "w", encoding="utf-8") as f:
                json.dump(zeta_data, f)

            engine = HintEngine(quest_log_path=quest_path, zeta_tracker_path=zeta_path)
            result = engine.run(count=2)

            assert isinstance(result, HintResult)
            assert result.metrics["actionable_count"] >= 0
            assert result.metrics["blocked_count"] >= 0

    def test_run_with_no_quests(self):
        """Test run with empty quest log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"
            quest_path.write_text("", encoding="utf-8")

            engine = HintEngine(quest_log_path=quest_path)
            result = engine.run(count=5)

            assert result.metrics["total_quests"] == 0


class TestEdgeCases:
    """Test edge cases."""

    def test_circular_dependencies(self):
        """Test handling of circular dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            quests = [
                {"id": "Q1", "title": "Quest 1", "dependencies": ["Q2"]},
                {"id": "Q2", "title": "Quest 2", "dependencies": ["Q1"]},
            ]

            with open(quest_path, "w", encoding="utf-8") as f:
                for q in quests:
                    f.write(json.dumps(q) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            engine.load_quests()
            engine.categorize_quests()

            # Should handle without crashing
            result = engine.suggest_next_quests(count=2)
            assert isinstance(result, HintResult)

    def test_missing_dependencies(self):
        """Test handling of missing dependency references."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            quests = [
                {
                    "id": "Q1",
                    "title": "Quest 1",
                    "dependencies": ["Q_NONEXISTENT"],
                }
            ]

            with open(quest_path, "w", encoding="utf-8") as f:
                for q in quests:
                    f.write(json.dumps(q) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            engine.load_quests()
            engine.categorize_quests()

            result = engine.suggest_next_quests(count=1)
            # Should treat as actionable since dependency doesn't exist
            assert isinstance(result, HintResult)

    def test_unicode_quest_titles(self):
        """Test handling of Unicode in quest data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            quest_path = tmpdir_path / "quest_log.jsonl"

            quest = {"id": "Q1", "title": "测试任务 🎯", "dependencies": []}

            with open(quest_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(quest, ensure_ascii=False) + "\n")

            engine = HintEngine(quest_log_path=quest_path)
            assert engine.load_quests()
            assert "Q1" in engine.quests
