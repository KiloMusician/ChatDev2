"""Tests for src/orchestration/specialization_learner.py — dataclasses and learning logic."""

import json

import pytest


class TestAgentSpecialization:
    """Tests for AgentSpecialization dataclass."""

    def _make(self, **kwargs):
        from src.orchestration.specialization_learner import AgentSpecialization
        defaults = {
            "agent_name": "ollama",
            "task_type": "code_review",
            "temperature": 0.7,
        }
        defaults.update(kwargs)
        return AgentSpecialization(**defaults)

    def test_instantiation(self):
        assert self._make() is not None

    def test_default_counts_zero(self):
        spec = self._make()
        assert spec.success_count == 0
        assert spec.failure_count == 0

    def test_total_attempts_zero_initially(self):
        assert self._make().total_attempts == 0

    def test_success_rate_zero_when_no_attempts(self):
        assert self._make().success_rate == 0.0

    def test_update_success(self):
        spec = self._make()
        spec.update(success=True, quality=0.9, tokens=100, latency_ms=500.0)
        assert spec.success_count == 1
        assert spec.failure_count == 0

    def test_update_failure(self):
        spec = self._make()
        spec.update(success=False, quality=0.3, tokens=80, latency_ms=300.0)
        assert spec.failure_count == 1
        assert spec.success_count == 0

    def test_success_rate_after_mixed(self):
        spec = self._make()
        spec.update(True, 0.9, 100, 500.0)
        spec.update(False, 0.3, 80, 300.0)
        assert spec.success_rate == 0.5

    def test_success_rate_all_success(self):
        spec = self._make()
        spec.update(True, 1.0, 100, 200.0)
        spec.update(True, 0.9, 120, 220.0)
        assert spec.success_rate == 1.0

    def test_specialization_score_set_after_update(self):
        spec = self._make()
        spec.update(True, 1.0, 100, 200.0)
        assert spec.specialization_score > 0

    def test_specialization_score_range(self):
        spec = self._make()
        spec.update(True, 1.0, 100, 200.0)
        assert 0.0 <= spec.specialization_score <= 100.0

    def test_avg_quality_updates(self):
        spec = self._make()
        spec.update(True, 0.8, 100, 200.0)
        assert abs(spec.avg_quality - 0.8) < 0.001

    def test_avg_tokens_updates(self):
        spec = self._make()
        spec.update(True, 0.8, 150, 200.0)
        assert spec.avg_tokens == 150

    def test_to_dict_returns_dict(self):
        d = self._make().to_dict()
        assert isinstance(d, dict)
        assert "agent_name" in d
        assert "task_type" in d
        assert "specialization_score" in d

    def test_from_dict_roundtrip(self):
        from src.orchestration.specialization_learner import AgentSpecialization
        spec = self._make(agent_name="chatdev", task_type="generate_tests")
        d = spec.to_dict()
        spec2 = AgentSpecialization.from_dict(d)
        assert spec2.agent_name == "chatdev"
        assert spec2.task_type == "generate_tests"


class TestSpecializationRecord:
    """Tests for SpecializationRecord dataclass."""

    def _make(self, **kwargs):
        from src.orchestration.specialization_learner import SpecializationRecord
        defaults = {
            "timestamp": "2026-01-01T00:00:00",
            "agent": "ollama",
            "task_type": "code_review",
            "temperature": 0.7,
            "success": True,
            "quality_score": 0.85,
            "tokens_used": 200,
            "latency_ms": 500.0,
        }
        defaults.update(kwargs)
        return SpecializationRecord(**defaults)

    def test_instantiation(self):
        assert self._make() is not None

    def test_fields_stored(self):
        rec = self._make(agent="lmstudio", success=False)
        assert rec.agent == "lmstudio"
        assert rec.success is False

    def test_to_dict(self):
        d = self._make().to_dict()
        assert isinstance(d, dict)
        assert "agent" in d
        assert "task_type" in d

    def test_from_dict_roundtrip(self):
        from src.orchestration.specialization_learner import SpecializationRecord
        rec = self._make(agent="codex", quality_score=0.9)
        d = rec.to_dict()
        rec2 = SpecializationRecord.from_dict(d)
        assert rec2.agent == "codex"
        assert rec2.quality_score == 0.9


class TestSpecializationTracker:
    """Tests for SpecializationTracker with mocked file paths."""

    @pytest.fixture
    def tracker(self, tmp_path, monkeypatch):
        import src.orchestration.specialization_learner as sl_mod
        monkeypatch.setattr(sl_mod, "SPECIALIZATION_HISTORY_FILE", tmp_path / "history.jsonl")
        monkeypatch.setattr(sl_mod, "AGENT_PROFILES_FILE", tmp_path / "profiles.json")
        monkeypatch.setattr(sl_mod, "AGENT_PAIRINGS_FILE", tmp_path / "pairings.json")
        from src.orchestration.specialization_learner import SpecializationTracker
        return SpecializationTracker()

    def _make_record(self):
        from src.orchestration.specialization_learner import SpecializationRecord
        return SpecializationRecord(
            timestamp="2026-01-01T00:00:00",
            agent="ollama",
            task_type="code_review",
            temperature=0.7,
            success=True,
            quality_score=0.85,
            tokens_used=200,
            latency_ms=500.0,
        )

    def test_instantiation(self, tracker):
        assert tracker is not None
        assert tracker.history == []

    def test_record_attempt_appends(self, tracker):
        tracker.record_attempt(self._make_record())
        assert len(tracker.history) == 1

    def test_get_records_for_agent(self, tracker):
        rec = self._make_record()
        tracker.record_attempt(rec)
        results = tracker.get_records_for_agent("ollama")
        assert len(results) == 1

    def test_get_records_for_agent_wrong_agent_empty(self, tracker):
        tracker.record_attempt(self._make_record())
        assert tracker.get_records_for_agent("chatdev") == []

    def test_get_records_for_task(self, tracker):
        tracker.record_attempt(self._make_record())
        results = tracker.get_records_for_task("code_review")
        assert len(results) == 1

    def test_get_records_for_combo(self, tracker):
        tracker.record_attempt(self._make_record())
        results = tracker.get_records_for_combo("ollama", "code_review")
        assert len(results) == 1

    def test_get_best_agents_empty_with_insufficient_data(self, tracker):
        # Only 2 attempts — below minimum of 3
        for _ in range(2):
            tracker.record_attempt(self._make_record())
        results = tracker.get_best_agents_for_task("code_review")
        assert results == []

    def test_get_best_agents_requires_minimum_3_attempts(self, tracker):
        for _ in range(3):
            tracker.record_attempt(self._make_record())
        results = tracker.get_best_agents_for_task("code_review", top_n=1)
        assert len(results) == 1
        assert results[0][0] == "ollama"

    def test_persists_to_file(self, tracker, tmp_path, monkeypatch):
        import src.orchestration.specialization_learner as sl_mod
        history_file = tmp_path / "history.jsonl"
        monkeypatch.setattr(sl_mod, "SPECIALIZATION_HISTORY_FILE", history_file)
        tracker.record_attempt(self._make_record())
        assert history_file.exists()
        lines = history_file.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["agent"] == "ollama"
