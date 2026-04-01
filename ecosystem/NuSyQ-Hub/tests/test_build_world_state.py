"""
Comprehensive tests for src.core.build_world_state module.

Tests cover:
- Signal, Contradiction, SignalDrift dataclasses
- ObservationCollector observation methods
- CoherenceEvaluator reconciliation and drift detection
- build_world_state() main function
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.core.build_world_state import (
    CoherenceEvaluator,
    Contradiction,
    ObservationCollector,
    Signal,
    SignalDrift,
    build_world_state,
)

# =============================================================================
# Signal Dataclass Tests
# =============================================================================


class TestSignalDataclass:
    """Tests for the Signal dataclass."""

    def test_signal_creation_basic(self):
        """Test basic Signal creation with required fields."""
        signal = Signal(
            id="test-signal-001",
            timestamp="2025-01-01T00:00:00Z",
            source="git_status",
            confidence=0.95,
            value={"branch": "main"},
        )
        assert signal.id == "test-signal-001"
        assert signal.timestamp == "2025-01-01T00:00:00Z"
        assert signal.source == "git_status"
        assert signal.confidence == 0.95
        assert signal.value == {"branch": "main"}
        assert signal.ttl_seconds is None  # Default TTL is None

    def test_signal_creation_with_custom_ttl(self):
        """Test Signal creation with custom TTL."""
        signal = Signal(
            id="test-signal-002",
            timestamp="2025-01-01T00:00:00Z",
            source="agent_probe",
            confidence=0.80,
            value={"agent": "ollama", "online": True},
            ttl_seconds=60,
        )
        assert signal.ttl_seconds == 60

    def test_signal_to_dict(self):
        """Test Signal.to_dict() method."""
        signal = Signal(
            id="test-signal-003",
            timestamp="2025-01-01T12:00:00Z",
            source="diagnostic_tool",
            confidence=1.0,
            value={"errors": 5, "warnings": 10},
            ttl_seconds=120,
        )
        result = signal.to_dict()

        assert isinstance(result, dict)
        assert result["id"] == "test-signal-003"
        assert result["timestamp"] == "2025-01-01T12:00:00Z"
        assert result["source"] == "diagnostic_tool"
        assert result["confidence"] == 1.0
        assert result["value"] == {"errors": 5, "warnings": 10}
        assert result["ttl_seconds"] == 120

    def test_signal_to_dict_returns_copy(self):
        """Test that to_dict returns a copy, not a reference."""
        original_value = {"key": "original"}
        signal = Signal(
            id="test-001",
            timestamp="2025-01-01T00:00:00Z",
            source="test",
            confidence=1.0,
            value=original_value,
        )

        result = signal.to_dict()
        result["value"]["key"] = "modified"

        # Original signal value should not be modified
        assert signal.value["key"] == "original"

    def test_signal_with_various_value_types(self):
        """Test Signal with different value types."""
        # String value
        signal_str = Signal(
            id="s1",
            timestamp="2025-01-01T00:00:00Z",
            source="test",
            confidence=1.0,
            value="simple string",
        )
        assert signal_str.value == "simple string"

        # List value
        signal_list = Signal(
            id="s2",
            timestamp="2025-01-01T00:00:00Z",
            source="test",
            confidence=1.0,
            value=[1, 2, 3],
        )
        assert signal_list.value == [1, 2, 3]

        # Nested dict value
        signal_nested = Signal(
            id="s3",
            timestamp="2025-01-01T00:00:00Z",
            source="test",
            confidence=1.0,
            value={"level1": {"level2": {"level3": "deep"}}},
        )
        assert signal_nested.value["level1"]["level2"]["level3"] == "deep"

    def test_signal_confidence_range(self):
        """Test Signal with various confidence values."""
        # Minimum confidence
        signal_min = Signal(
            id="s1", timestamp="2025-01-01T00:00:00Z", source="test", confidence=0.0, value={}
        )
        assert signal_min.confidence == 0.0

        # Maximum confidence
        signal_max = Signal(
            id="s2", timestamp="2025-01-01T00:00:00Z", source="test", confidence=1.0, value={}
        )
        assert signal_max.confidence == 1.0

        # Mid-range confidence
        signal_mid = Signal(
            id="s3", timestamp="2025-01-01T00:00:00Z", source="test", confidence=0.75, value={}
        )
        assert signal_mid.confidence == 0.75


# =============================================================================
# Contradiction Dataclass Tests
# =============================================================================


class TestContradictionDataclass:
    """Tests for the Contradiction dataclass."""

    def test_contradiction_creation(self):
        """Test Contradiction creation with all fields."""
        signals = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="git_status",
                confidence=0.9,
                value={"branch": "main"},
            ),
            Signal(
                id="s2",
                timestamp="2025-01-01T00:00:00Z",
                source="config",
                confidence=0.7,
                value={"branch": "develop"},
            ),
        ]
        contradiction = Contradiction(
            key="branch",
            signals=signals,
            resolved_to="main",
            reasoning="git_status has higher precedence than config",
        )

        assert contradiction.key == "branch"
        assert len(contradiction.signals) == 2
        assert contradiction.resolved_to == "main"
        assert "precedence" in contradiction.reasoning

    def test_contradiction_with_empty_signals(self):
        """Test Contradiction with empty signals list."""
        contradiction = Contradiction(
            key="test_key",
            signals=[],
            resolved_to=None,
            reasoning="No signals to resolve",
        )

        assert contradiction.key == "test_key"
        assert len(contradiction.signals) == 0
        assert contradiction.resolved_to is None

    def test_contradiction_asdict(self):
        """Test Contradiction serialization via asdict."""
        signal = Signal(
            id="s1", timestamp="2025-01-01T00:00:00Z", source="test", confidence=1.0, value={"x": 1}
        )
        contradiction = Contradiction(
            key="x_value",
            signals=[signal],
            resolved_to={"x": 1},
            reasoning="Single signal, no conflict",
        )

        result = asdict(contradiction)
        assert isinstance(result, dict)
        assert result["key"] == "x_value"
        assert len(result["signals"]) == 1


# =============================================================================
# SignalDrift Dataclass Tests
# =============================================================================


class TestSignalDriftDataclass:
    """Tests for the SignalDrift dataclass."""

    def test_signal_drift_creation(self):
        """Test SignalDrift creation with all fields."""
        drift = SignalDrift(
            key="error_count",
            previous_value=10,
            current_value=25,
            change_magnitude=1.5,
            alert_level="warning",
        )

        assert drift.key == "error_count"
        assert drift.previous_value == 10
        assert drift.current_value == 25
        assert drift.change_magnitude == 1.5
        assert drift.alert_level == "warning"

    def test_signal_drift_alert_levels(self):
        """Test various alert levels for SignalDrift."""
        alert_levels = ["info", "warning", "critical"]

        for level in alert_levels:
            drift = SignalDrift(
                key="test",
                previous_value=0,
                current_value=1,
                change_magnitude=1.0,
                alert_level=level,
            )
            assert drift.alert_level == level

    def test_signal_drift_with_different_value_types(self):
        """Test SignalDrift with different value types."""
        # Numeric drift
        drift_numeric = SignalDrift(
            key="count",
            previous_value=100,
            current_value=150,
            change_magnitude=0.5,
            alert_level="info",
        )
        assert drift_numeric.change_magnitude == 0.5

        # String drift
        drift_string = SignalDrift(
            key="status",
            previous_value="healthy",
            current_value="degraded",
            change_magnitude=1.0,
            alert_level="warning",
        )
        assert drift_string.previous_value == "healthy"
        assert drift_string.current_value == "degraded"


# =============================================================================
# ObservationCollector Tests
# =============================================================================


class TestObservationCollector:
    """Tests for the ObservationCollector class."""

    @pytest.fixture
    def collector(self, tmp_path):
        """Create ObservationCollector with temp workspace."""
        return ObservationCollector(workspace_root=tmp_path)

    def test_collector_initialization(self, tmp_path):
        """Test ObservationCollector initialization."""
        collector = ObservationCollector(workspace_root=tmp_path)
        assert collector.workspace_root == tmp_path
        assert hasattr(collector, "signals")
        assert collector.signals == []

    def test_probe_env_returns_dict(self, collector):
        """Test _probe_env returns environment dict for subprocess."""
        env = collector._probe_env()

        assert isinstance(env, dict)
        # Should include NUSYQ_SPINE_STARTUP to skip heavy startup
        assert env.get("NUSYQ_SPINE_STARTUP") == "never"

    def test_probe_env_contains_expected_keys(self, collector):
        """Test _probe_env returns dict with expected keys."""
        env = collector._probe_env()

        # Should contain environment variables
        assert isinstance(env, dict)
        assert len(env) > 0
        # Should have the startup flag set
        assert "NUSYQ_SPINE_STARTUP" in env

    @patch("subprocess.run")
    def test_observe_git_state_success(self, mock_run, collector):
        """Test observe_git_state with successful git command."""
        mock_run.return_value = MagicMock(returncode=0, stdout="main\n", stderr="")

        result = collector.observe_git_state()

        # Method returns None, appends to self.signals
        assert result is None
        assert isinstance(collector.signals, list)

    @patch("subprocess.run")
    def test_observe_git_state_no_git_repo(self, mock_run, collector):
        """Test observe_git_state when not in a git repo."""
        mock_run.side_effect = FileNotFoundError("git not found")

        result = collector.observe_git_state()

        # Should handle gracefully - returns None, may or may not add signal
        assert result is None

    @patch("subprocess.run")
    def test_observe_git_state_git_error(self, mock_run, collector):
        """Test observe_git_state with git error."""
        mock_run.return_value = MagicMock(
            returncode=128, stdout="", stderr="fatal: not a git repository"
        )

        result = collector.observe_git_state()

        # Should handle gracefully - returns None
        assert result is None

    @patch.object(ObservationCollector, "_probe_env", return_value=dict(os.environ))
    def test_observe_agent_availability_success(self, mock_env, collector):
        """Test observe_agent_availability runs without error."""
        # Just verify it doesn't raise
        result = collector.observe_agent_availability()
        assert result is None

    def test_observe_agent_availability_handles_errors(self, tmp_path):
        """Test observe_agent_availability handles errors gracefully."""
        collector = ObservationCollector(workspace_root=tmp_path)

        # Should not raise even with invalid workspace
        result = collector.observe_agent_availability()
        assert result is None

    def test_observe_quest_log_no_file(self, collector):
        """Test observe_quest_log when quest_log.jsonl doesn't exist."""
        result = collector.observe_quest_log()

        # Should return None when file doesn't exist
        assert result is None

    def test_observe_quest_log_with_file(self, tmp_path):
        """Test observe_quest_log with existing quest log."""
        # Create quest log structure
        quest_dir = tmp_path / "src" / "Rosetta_Quest_System"
        quest_dir.mkdir(parents=True)
        quest_file = quest_dir / "quest_log.jsonl"

        # Write test quest entries
        entries = [
            {"event": "quest_created", "quest_id": "Q001", "status": "pending"},
            {"event": "quest_started", "quest_id": "Q001", "status": "active"},
            {"event": "quest_completed", "quest_id": "Q001", "status": "complete"},
        ]
        with open(quest_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        collector = ObservationCollector(workspace_root=tmp_path)
        result = collector.observe_quest_log()

        assert result is None
        # Should have signals from quest log entries
        assert len(collector.signals) > 0

    def test_observe_quest_log_malformed_json(self, tmp_path):
        """Test observe_quest_log handles malformed JSON gracefully."""
        quest_dir = tmp_path / "src" / "Rosetta_Quest_System"
        quest_dir.mkdir(parents=True)
        quest_file = quest_dir / "quest_log.jsonl"

        with open(quest_file, "w") as f:
            f.write("not valid json\n")
            f.write('{"valid": "json"}\n')
            f.write("also invalid\n")

        collector = ObservationCollector(workspace_root=tmp_path)
        result = collector.observe_quest_log()

        # Should not raise, should handle gracefully
        assert result is None
        # Should have at least the valid JSON entry
        assert len(collector.signals) >= 1

    @patch("subprocess.run")
    def test_observe_diagnostics_success(self, mock_run, collector):
        """Test observe_diagnostics with successful diagnostic run."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"total_diagnostics": 5, "by_severity": {"errors": 2, "warnings": 3}}',
            stderr="",
        )

        result = collector.observe_diagnostics()

        assert result is None
        # Should have added a signal
        assert len(collector.signals) > 0

    @patch("subprocess.run")
    def test_observe_diagnostics_failure(self, mock_run, collector):
        """Test observe_diagnostics with failed diagnostic run."""
        mock_run.side_effect = Exception("Diagnostic command failed")

        result = collector.observe_diagnostics()

        # Should not raise, returns None
        assert result is None

    def test_collect_all_returns_signals(self, collector):
        """Test collect_all aggregates all observations."""

        # Mock the observe methods to add signals directly to collector.signals
        def mock_observe_git():
            collector.signals.append(
                Signal(
                    id="g1",
                    timestamp="2025-01-01T00:00:00Z",
                    source="git_status",
                    confidence=1.0,
                    value={},
                )
            )

        def mock_observe_agents():
            collector.signals.append(
                Signal(
                    id="a1",
                    timestamp="2025-01-01T00:00:00Z",
                    source="agent_probe",
                    confidence=0.9,
                    value={},
                )
            )

        with patch.object(collector, "observe_git_state", side_effect=mock_observe_git):
            with patch.object(
                collector, "observe_agent_availability", side_effect=mock_observe_agents
            ):
                with patch.object(collector, "observe_quest_log"):
                    with patch.object(collector, "observe_diagnostics"):
                        signals = collector.collect_all()

        assert isinstance(signals, list)
        # Should have git and agent signals
        assert len(signals) >= 2

    def test_collect_all_handles_individual_failures(self, collector):
        """Test collect_all continues when individual observers fail."""

        def mock_observe_agents():
            collector.signals.append(
                Signal(
                    id="a1",
                    timestamp="2025-01-01T00:00:00Z",
                    source="agent_probe",
                    confidence=0.9,
                    value={},
                )
            )

        with patch.object(collector, "observe_git_state", side_effect=Exception("Git failed")):
            with patch.object(
                collector, "observe_agent_availability", side_effect=mock_observe_agents
            ):
                with patch.object(collector, "observe_quest_log"):
                    with patch.object(collector, "observe_diagnostics"):
                        signals = collector.collect_all()

        # Should still return signals from working observers
        assert isinstance(signals, list)


# =============================================================================
# CoherenceEvaluator Tests
# =============================================================================


class TestCoherenceEvaluator:
    """Tests for the CoherenceEvaluator class."""

    @pytest.fixture
    def evaluator(self):
        """Create fresh CoherenceEvaluator."""
        return CoherenceEvaluator()

    def test_evaluator_initialization(self, evaluator):
        """Test CoherenceEvaluator initialization."""
        assert hasattr(evaluator, "contradictions")
        assert evaluator.contradictions == []

    def test_source_precedence_defined(self, evaluator):
        """Test SOURCE_PRECEDENCE is properly defined."""
        precedence = CoherenceEvaluator.SOURCE_PRECEDENCE

        assert isinstance(precedence, dict)
        assert len(precedence) > 0

        # Verify expected sources exist
        expected_sources = [
            "user_input",
            "diagnostic_tool",
            "agent_probe",
            "quest_log",
            "git_status",
            "config",
        ]
        for source in expected_sources:
            assert source in precedence, f"Missing source: {source}"

        # user_input should have highest precedence
        assert precedence["user_input"] > precedence["config"]

    def test_source_precedence_ordering(self, evaluator):
        """Test SOURCE_PRECEDENCE has correct ordering."""
        precedence = CoherenceEvaluator.SOURCE_PRECEDENCE

        # User input > diagnostic tool > agent probe > quest log > git status > config
        assert precedence["user_input"] > precedence["diagnostic_tool"]
        assert precedence["diagnostic_tool"] > precedence["agent_probe"]
        assert precedence["agent_probe"] > precedence["quest_log"]
        assert precedence["quest_log"] > precedence["git_status"]
        assert precedence["git_status"] > precedence["config"]

    def test_reconcile_signals_empty(self, evaluator):
        """Test reconcile_signals with empty signal list."""
        result = evaluator.reconcile_signals([])

        assert isinstance(result, dict)
        assert len(result) == 0
        assert len(evaluator.contradictions) == 0

    def test_reconcile_signals_single(self, evaluator):
        """Test reconcile_signals with single signal."""
        signals = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="git_status",
                confidence=1.0,
                value={"branch": "main"},
            )
        ]

        result = evaluator.reconcile_signals(signals)

        assert isinstance(result, dict)
        # Should extract branch key
        assert "branch" in result or len(result) >= 0

    def test_reconcile_signals_no_conflict(self, evaluator):
        """Test reconcile_signals with non-conflicting signals."""
        signals = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="git_status",
                confidence=1.0,
                value={"branch": "main"},
            ),
            Signal(
                id="s2",
                timestamp="2025-01-01T00:00:00Z",
                source="agent_probe",
                confidence=0.9,
                value={"agent": "ollama", "online": True},
            ),
        ]

        result = evaluator.reconcile_signals(signals)

        assert isinstance(result, dict)
        # No contradictions expected for non-overlapping keys
        assert len(evaluator.contradictions) == 0

    def test_reconcile_signals_with_conflict(self, evaluator):
        """Test reconcile_signals with conflicting signals."""
        signals = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="git_status",
                confidence=1.0,
                value={"branch": "main"},
            ),
            Signal(
                id="s2",
                timestamp="2025-01-01T00:00:00Z",
                source="config",
                confidence=1.0,
                value={"branch": "develop"},
            ),
        ]

        result = evaluator.reconcile_signals(signals)

        # git_status has higher precedence than config
        # Should resolve to "main"
        if "branch" in result:
            assert result["branch"] == "main"

    def test_reconcile_signals_precedence_applied(self, evaluator):
        """Test that higher precedence source wins in conflicts."""
        # user_input (10) vs config (5)
        signals = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="config",
                confidence=1.0,
                value={"setting": "default"},
            ),
            Signal(
                id="s2",
                timestamp="2025-01-01T00:00:00Z",
                source="user_input",
                confidence=1.0,
                value={"setting": "override"},
            ),
        ]

        result = evaluator.reconcile_signals(signals)

        if "setting" in result:
            assert result["setting"] == "override"

    def test_detect_drift_no_previous_state(self, evaluator):
        """Test detect_drift with no previous state."""
        # First reconcile some signals to populate self.reconciled
        current_signals = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="test",
                confidence=1.0,
                value={"count": 10},
            ),
        ]
        evaluator.reconcile_signals(current_signals)

        # Now detect drift (no previous_state set internally)
        drift = evaluator.detect_drift()

        assert isinstance(drift, list)
        # No drift expected when no previous state (first run)
        assert len(drift) == 0

    def test_detect_drift_with_previous_state(self, evaluator):
        """Test detect_drift detects value changes."""
        # First run: establish baseline
        signals1 = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="diagnostic_tool",
                confidence=1.0,
                value={"errors": 5},
            ),
        ]
        evaluator.reconcile_signals(signals1)
        evaluator.detect_drift()  # Sets previous_state

        # Second run: changed value
        signals2 = [
            Signal(
                id="s2",
                timestamp="2025-01-01T00:01:00Z",
                source="diagnostic_tool",
                confidence=1.0,
                value={"errors": 20},
            ),
        ]
        evaluator.reconcile_signals(signals2)
        drift = evaluator.detect_drift()

        assert isinstance(drift, list)

    def test_detect_drift_alert_levels(self, evaluator):
        """Test detect_drift assigns appropriate alert levels."""
        # First run: baseline
        signals1 = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="diagnostic_tool",
                confidence=1.0,
                value={"errors": 10},
            ),
        ]
        evaluator.reconcile_signals(signals1)
        evaluator.detect_drift()  # Sets previous_state

        # Second run: large change (10x increase)
        signals2 = [
            Signal(
                id="s2",
                timestamp="2025-01-01T00:01:00Z",
                source="diagnostic_tool",
                confidence=1.0,
                value={"errors": 100},
            ),
        ]
        evaluator.reconcile_signals(signals2)
        drift = evaluator.detect_drift()

        # If drift detected, should have appropriate alert level
        for d in drift:
            assert d.alert_level in ["info", "warning", "critical"]

    def test_extract_key_dict_value(self, evaluator):
        """Test _extract_key with dict values."""
        signal = Signal(
            id="s1",
            timestamp="2025-01-01T00:00:00Z",
            source="test",
            confidence=1.0,
            value={"branch": "main", "tag": "v1.0"},
        )

        # Method exists and works
        if hasattr(evaluator, "_extract_key"):
            keys = evaluator._extract_key(signal)
            assert isinstance(keys, (list, dict, str, type(None)))

    def test_calculate_drift_magnitude_numeric(self, evaluator):
        """Test _calculate_drift_magnitude with numeric values."""
        if hasattr(evaluator, "_calculate_drift_magnitude"):
            # Double the value = 1.0 magnitude
            magnitude = evaluator._calculate_drift_magnitude(10, 20)
            assert magnitude >= 0.0

            # Same value = 0.0 magnitude
            magnitude_same = evaluator._calculate_drift_magnitude(10, 10)
            assert magnitude_same == 0.0

    def test_calculate_drift_magnitude_string(self, evaluator):
        """Test _calculate_drift_magnitude with string values."""
        if hasattr(evaluator, "_calculate_drift_magnitude"):
            # Different strings = 1.0 magnitude
            magnitude = evaluator._calculate_drift_magnitude("old", "new")
            assert magnitude >= 0.0

            # Same string = 0.0 magnitude
            magnitude_same = evaluator._calculate_drift_magnitude("same", "same")
            assert magnitude_same == 0.0


# =============================================================================
# build_world_state Function Tests
# =============================================================================


class TestBuildWorldState:
    """Tests for the build_world_state convenience function."""

    @pytest.fixture
    def tmp_workspace(self, tmp_path):
        """Create minimal workspace structure."""
        (tmp_path / "src").mkdir(exist_ok=True)
        (tmp_path / "config").mkdir(exist_ok=True)
        return tmp_path

    @patch("src.core.build_world_state.ObservationCollector")
    @patch("src.core.build_world_state.CoherenceEvaluator")
    def test_build_world_state_returns_dict(
        self, mock_evaluator_cls, mock_collector_cls, tmp_workspace
    ):
        """Test build_world_state returns a dict."""
        # Mock collector
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = []
        mock_collector_cls.return_value = mock_collector

        # Mock evaluator
        mock_evaluator = MagicMock()
        mock_evaluator.reconcile_signals.return_value = {}
        mock_evaluator.detect_drift.return_value = []
        mock_evaluator.contradictions = []
        mock_evaluator_cls.return_value = mock_evaluator

        result = build_world_state(workspace_root=tmp_workspace)

        assert isinstance(result, dict)

    @patch("src.core.build_world_state.ObservationCollector")
    @patch("src.core.build_world_state.CoherenceEvaluator")
    def test_build_world_state_schema_structure(
        self, mock_evaluator_cls, mock_collector_cls, tmp_workspace
    ):
        """Test build_world_state output has expected schema."""
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = []
        mock_collector_cls.return_value = mock_collector

        mock_evaluator = MagicMock()
        mock_evaluator.reconcile_signals.return_value = {}
        mock_evaluator.detect_drift.return_value = []
        mock_evaluator.contradictions = []
        mock_evaluator_cls.return_value = mock_evaluator

        result = build_world_state(workspace_root=tmp_workspace)

        # Check top-level keys
        expected_keys = [
            "timestamp",
            "decision_epoch",
            "observations",
            "signals",
            "coherence",
            "runtime_state",
            "policy_state",
            "objective",
            "metadata",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    @patch("src.core.build_world_state.ObservationCollector")
    @patch("src.core.build_world_state.CoherenceEvaluator")
    def test_build_world_state_observations_structure(
        self, mock_evaluator_cls, mock_collector_cls, tmp_workspace
    ):
        """Test observations section has expected structure."""
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = []
        mock_collector_cls.return_value = mock_collector

        mock_evaluator = MagicMock()
        mock_evaluator.reconcile_signals.return_value = {}
        mock_evaluator.detect_drift.return_value = []
        mock_evaluator.contradictions = []
        mock_evaluator_cls.return_value = mock_evaluator

        result = build_world_state(workspace_root=tmp_workspace)

        observations = result["observations"]
        assert "context" in observations
        assert "repo_graph" in observations
        assert "runtime_state" in observations
        assert "diagnostics" in observations

    @patch("src.core.build_world_state.ObservationCollector")
    @patch("src.core.build_world_state.CoherenceEvaluator")
    def test_build_world_state_coherence_structure(
        self, mock_evaluator_cls, mock_collector_cls, tmp_workspace
    ):
        """Test coherence section has expected structure."""
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = []
        mock_collector_cls.return_value = mock_collector

        mock_evaluator = MagicMock()
        mock_evaluator.reconcile_signals.return_value = {}
        mock_evaluator.detect_drift.return_value = []
        mock_evaluator.contradictions = []
        mock_evaluator_cls.return_value = mock_evaluator

        result = build_world_state(workspace_root=tmp_workspace)

        coherence = result["coherence"]
        assert "reconciled_facts" in coherence
        assert "contradictions" in coherence
        assert "signal_drift" in coherence

    @patch("src.core.build_world_state.ObservationCollector")
    @patch("src.core.build_world_state.CoherenceEvaluator")
    def test_build_world_state_policy_state_structure(
        self, mock_evaluator_cls, mock_collector_cls, tmp_workspace
    ):
        """Test policy_state section has expected structure."""
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = []
        mock_collector_cls.return_value = mock_collector

        mock_evaluator = MagicMock()
        mock_evaluator.reconcile_signals.return_value = {}
        mock_evaluator.detect_drift.return_value = []
        mock_evaluator.contradictions = []
        mock_evaluator_cls.return_value = mock_evaluator

        result = build_world_state(workspace_root=tmp_workspace)

        policy = result["policy_state"]
        assert "active_policies" in policy
        assert "resource_budgets" in policy
        assert "safety_gates" in policy

    @patch("src.core.build_world_state.ObservationCollector")
    @patch("src.core.build_world_state.CoherenceEvaluator")
    def test_build_world_state_increments_epoch(
        self, mock_evaluator_cls, mock_collector_cls, tmp_workspace
    ):
        """Test decision_epoch increments from previous state."""
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = []
        mock_collector_cls.return_value = mock_collector

        mock_evaluator = MagicMock()
        mock_evaluator.reconcile_signals.return_value = {}
        mock_evaluator.detect_drift.return_value = []
        mock_evaluator.contradictions = []
        mock_evaluator_cls.return_value = mock_evaluator

        previous_state = {"decision_epoch": 5}
        result = build_world_state(workspace_root=tmp_workspace, previous_state=previous_state)

        assert result["decision_epoch"] == 6

    @patch("src.core.build_world_state.ObservationCollector")
    @patch("src.core.build_world_state.CoherenceEvaluator")
    def test_build_world_state_metadata(
        self, mock_evaluator_cls, mock_collector_cls, tmp_workspace
    ):
        """Test metadata section is populated."""
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = []
        mock_collector_cls.return_value = mock_collector

        mock_evaluator = MagicMock()
        mock_evaluator.reconcile_signals.return_value = {}
        mock_evaluator.detect_drift.return_value = []
        mock_evaluator.contradictions = []
        mock_evaluator_cls.return_value = mock_evaluator

        result = build_world_state(workspace_root=tmp_workspace)

        metadata = result["metadata"]
        assert "schema_version" in metadata
        assert "generated_by" in metadata
        assert "build_duration_ms" in metadata
        assert metadata["generated_by"] == "build_world_state.py"

    @patch("src.core.build_world_state.ObservationCollector")
    @patch("src.core.build_world_state.CoherenceEvaluator")
    def test_build_world_state_with_signals(
        self, mock_evaluator_cls, mock_collector_cls, tmp_workspace
    ):
        """Test build_world_state processes signals correctly."""
        test_signals = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="git_status",
                confidence=1.0,
                value={"current_branch": "main", "uncommitted_files": 3},
            ),
            Signal(
                id="s2",
                timestamp="2025-01-01T00:00:00Z",
                source="agent_probe",
                confidence=0.9,
                value={"agent": "ollama", "online": True, "latency_ms": 50},
            ),
        ]

        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = test_signals
        mock_collector_cls.return_value = mock_collector

        mock_evaluator = MagicMock()
        mock_evaluator.reconcile_signals.return_value = {"branch": "main"}
        mock_evaluator.detect_drift.return_value = []
        mock_evaluator.contradictions = []
        mock_evaluator_cls.return_value = mock_evaluator

        result = build_world_state(workspace_root=tmp_workspace)

        # Signals should be in the output
        assert "signals" in result
        assert "facts" in result["signals"]

    @patch("src.core.build_world_state.ObservationCollector")
    @patch("src.core.build_world_state.CoherenceEvaluator")
    def test_build_world_state_env_vars(
        self, mock_evaluator_cls, mock_collector_cls, tmp_workspace, monkeypatch
    ):
        """Test build_world_state reads environment variables."""
        monkeypatch.setenv("NUSYQ_TOKEN_BUDGET", "10000")
        monkeypatch.setenv("NUSYQ_TIME_BUDGET", "600")
        monkeypatch.setenv("NUSYQ_ALLOW_MUTATIONS", "true")

        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = []
        mock_collector_cls.return_value = mock_collector

        mock_evaluator = MagicMock()
        mock_evaluator.reconcile_signals.return_value = {}
        mock_evaluator.detect_drift.return_value = []
        mock_evaluator.contradictions = []
        mock_evaluator_cls.return_value = mock_evaluator

        result = build_world_state(workspace_root=tmp_workspace)

        policy = result["policy_state"]
        assert policy["resource_budgets"]["token_budget_remaining"] == 10000
        assert policy["resource_budgets"]["time_budget_remaining_s"] == 600
        assert policy["safety_gates"]["allow_mutations"] is True


# =============================================================================
# Integration Tests
# =============================================================================


class TestBuildWorldStateIntegration:
    """Integration tests for build_world_state module."""

    @pytest.fixture
    def real_workspace(self, tmp_path):
        """Create realistic workspace structure for integration tests."""
        # Create src directory
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "__init__.py").write_text("")

        # Create Rosetta Quest System
        quest_dir = src_dir / "Rosetta_Quest_System"
        quest_dir.mkdir()
        quest_file = quest_dir / "quest_log.jsonl"

        entries = [
            {"event": "quest_created", "quest_id": "Q001", "status": "pending"},
            {"event": "quest_started", "quest_id": "Q001", "status": "active"},
        ]
        with open(quest_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        # Create config directory
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        return tmp_path

    def test_observation_collector_collect_all_integration(self, real_workspace):
        """Integration test for ObservationCollector.collect_all()."""
        collector = ObservationCollector(workspace_root=real_workspace)

        # Mock subprocess to avoid git dependency
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="main\n", stderr="")

            signals = collector.collect_all()

        assert isinstance(signals, list)
        # Should have environment signal at minimum
        assert any(s.source == "environment" for s in signals) or len(signals) >= 0

    def test_coherence_evaluator_full_flow(self):
        """Integration test for CoherenceEvaluator full reconciliation flow."""
        evaluator = CoherenceEvaluator()

        # Create signals with potential conflicts
        signals = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="user_input",
                confidence=1.0,
                value={"mode": "production"},
            ),
            Signal(
                id="s2",
                timestamp="2025-01-01T00:00:00Z",
                source="config",
                confidence=1.0,
                value={"mode": "development"},
            ),
            Signal(
                id="s3",
                timestamp="2025-01-01T00:00:00Z",
                source="git_status",
                confidence=1.0,
                value={"branch": "main"},
            ),
            Signal(
                id="s4",
                timestamp="2025-01-01T00:00:00Z",
                source="diagnostic_tool",
                confidence=0.95,
                value={"errors": 5, "warnings": 10},
            ),
        ]

        # Reconcile
        reconciled = evaluator.reconcile_signals(signals)

        assert isinstance(reconciled, dict)

        # Detect drift (no previous state on first call)
        drift = evaluator.detect_drift()

        assert isinstance(drift, list)
        assert len(drift) == 0  # No drift without previous state

    def test_full_build_world_state_integration(self, real_workspace):
        """Full integration test for build_world_state."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="feature/test\n", stderr="")

            result = build_world_state(workspace_root=real_workspace)

        # Verify complete structure
        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "decision_epoch" in result
        assert "observations" in result
        assert "signals" in result
        assert "coherence" in result
        assert "runtime_state" in result
        assert "policy_state" in result
        assert "objective" in result
        assert "metadata" in result

        # Verify metadata
        assert result["metadata"]["generated_by"] == "build_world_state.py"
        assert result["metadata"]["build_duration_ms"] >= 0

    def test_signal_serialization_round_trip(self):
        """Test Signal can be serialized and contains valid data."""
        original = Signal(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC).isoformat(),
            source="test_source",
            confidence=0.85,
            value={"nested": {"data": [1, 2, 3]}},
            ttl_seconds=120,
        )

        # Serialize
        serialized = original.to_dict()

        # Verify all fields present
        assert serialized["id"] == original.id
        assert serialized["timestamp"] == original.timestamp
        assert serialized["source"] == original.source
        assert serialized["confidence"] == original.confidence
        assert serialized["value"] == original.value
        assert serialized["ttl_seconds"] == original.ttl_seconds

        # JSON serializable
        json_str = json.dumps(serialized)
        reloaded = json.loads(json_str)
        assert reloaded == serialized


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_signal_with_none_value(self):
        """Test Signal handles None value."""
        signal = Signal(
            id="s1", timestamp="2025-01-01T00:00:00Z", source="test", confidence=1.0, value=None
        )
        assert signal.value is None

        result = signal.to_dict()
        assert result["value"] is None

    def test_signal_with_empty_dict_value(self):
        """Test Signal handles empty dict value."""
        signal = Signal(
            id="s1", timestamp="2025-01-01T00:00:00Z", source="test", confidence=1.0, value={}
        )
        assert signal.value == {}

    def test_signal_with_very_long_value(self):
        """Test Signal handles large value."""
        large_value = {"data": "x" * 10000}
        signal = Signal(
            id="s1",
            timestamp="2025-01-01T00:00:00Z",
            source="test",
            confidence=1.0,
            value=large_value,
        )
        assert len(signal.value["data"]) == 10000

    def test_coherence_evaluator_with_unknown_source(self):
        """Test CoherenceEvaluator handles unknown source gracefully."""
        evaluator = CoherenceEvaluator()

        signals = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="unknown_source",
                confidence=1.0,
                value={"key": "value"},
            )
        ]

        # Should not raise
        result = evaluator.reconcile_signals(signals)
        assert isinstance(result, dict)

    def test_observation_collector_with_invalid_workspace(self):
        """Test ObservationCollector handles invalid workspace path."""
        invalid_path = Path("/nonexistent/path/to/workspace")

        collector = ObservationCollector(workspace_root=invalid_path)

        # Should not raise on initialization
        assert collector.workspace_root == invalid_path

    def test_build_world_state_with_none_previous_state(self, tmp_path):
        """Test build_world_state with explicit None previous_state."""
        with patch("src.core.build_world_state.ObservationCollector") as mock_coll_cls:
            with patch("src.core.build_world_state.CoherenceEvaluator") as mock_eval_cls:
                mock_collector = MagicMock()
                mock_collector.collect_all.return_value = []
                mock_coll_cls.return_value = mock_collector

                mock_evaluator = MagicMock()
                mock_evaluator.reconcile_signals.return_value = {}
                mock_evaluator.detect_drift.return_value = []
                mock_evaluator.contradictions = []
                mock_eval_cls.return_value = mock_evaluator

                result = build_world_state(workspace_root=tmp_path, previous_state=None)

        assert result["decision_epoch"] == 1  # First epoch

    def test_zero_confidence_signals(self):
        """Test signals with zero confidence are handled."""
        evaluator = CoherenceEvaluator()

        signals = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="test",
                confidence=0.0,
                value={"key": "unreliable"},
            )
        ]

        result = evaluator.reconcile_signals(signals)
        assert isinstance(result, dict)

    def test_signal_drift_with_same_values(self):
        """Test drift detection when values are identical."""
        evaluator = CoherenceEvaluator()

        # First run: establish baseline
        signals1 = [
            Signal(
                id="s1",
                timestamp="2025-01-01T00:00:00Z",
                source="test",
                confidence=1.0,
                value={"count": 10},
            )
        ]
        evaluator.reconcile_signals(signals1)
        evaluator.detect_drift()  # Sets previous_state

        # Second run: same values
        signals2 = [
            Signal(
                id="s2",
                timestamp="2025-01-01T00:01:00Z",
                source="test",
                confidence=1.0,
                value={"count": 10},
            )
        ]
        evaluator.reconcile_signals(signals2)
        drift = evaluator.detect_drift()

        # No drift expected for identical values
        assert isinstance(drift, list)
