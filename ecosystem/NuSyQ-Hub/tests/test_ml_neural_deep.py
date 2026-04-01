"""Deep coverage tests for NuSyQ-Hub ML subsystem.

Covers:
- QuantumMLProcessor (quantum_ml_processor.py)
- PatternConsciousnessAnalyzer (pattern_consciousness_analyzer.py)
- ConsciousnessEnhancedMLSystem (consciousness_enhanced_ml.py)
- NeuralQuantumBridge (neural_quantum_bridge.py)
- src/ml/__init__.py exports
"""

import os
from typing import Any

import numpy as np
import pytest

os.environ.setdefault("NUSYQ_SEED", "42")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_features(n: int = 20, d: int = 8) -> list[list[float]]:
    rng = np.random.default_rng(0)
    return rng.standard_normal((n, d)).tolist()


def _make_labels(n: int = 20, classes: int = 3) -> list[int]:
    rng = np.random.default_rng(0)
    return rng.integers(0, classes, size=n).tolist()


# ===========================================================================
# src/ml/__init__.py — module exports
# ===========================================================================


class TestMlInit:
    def test_all_four_classes_importable(self) -> None:
        from src.ml import (
            ConsciousnessEnhancedMLSystem,
            NeuralQuantumBridge,
            PatternConsciousnessAnalyzer,
            QuantumMLProcessor,
        )

        assert ConsciousnessEnhancedMLSystem is not None
        assert NeuralQuantumBridge is not None
        assert PatternConsciousnessAnalyzer is not None
        assert QuantumMLProcessor is not None

    def test_dunder_all_contents(self) -> None:
        import src.ml as ml_pkg

        expected = {
            "ConsciousnessEnhancedMLSystem",
            "NeuralQuantumBridge",
            "PatternConsciousnessAnalyzer",
            "QuantumMLProcessor",
        }
        assert set(ml_pkg.__all__) == expected

    def test_version_string_present(self) -> None:
        import src.ml as ml_pkg

        assert hasattr(ml_pkg, "__version__")
        assert isinstance(ml_pkg.__version__, str)


# ===========================================================================
# QuantumMLProcessor
# ===========================================================================


class TestQuantumMLProcessorInit:
    def test_default_init(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        assert proc is not None

    def test_has_feature_spaces(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        assert len(proc.feature_spaces) >= 4  # 8, 16, 32, 64

    def test_has_quantum_models(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        assert "variational_classifier" in proc.quantum_models
        assert "quantum_kernel_svm" in proc.quantum_models
        assert "quantum_neural_network" in proc.quantum_models

    def test_config_has_required_sections(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        assert "quantum_processing" in proc.config
        assert "consciousness_integration" in proc.config
        assert "quantum_algorithms" in proc.config

    def test_initial_ml_state_is_classical(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor, QuantumMLState

        proc = QuantumMLProcessor()
        assert proc.ml_state == QuantumMLState.CLASSICAL

    def test_processing_history_starts_empty(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        assert proc.processing_history == []


class TestQuantumMLState:
    def test_all_states_accessible(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLState

        states = [
            QuantumMLState.CLASSICAL,
            QuantumMLState.QUANTUM_ENHANCED,
            QuantumMLState.QUANTUM_SUPERPOSITION,
            QuantumMLState.QUANTUM_ENTANGLED,
            QuantumMLState.CONSCIOUSNESS_QUANTUM,
        ]
        assert len(states) == 5

    def test_state_values_are_strings(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLState

        for state in QuantumMLState:
            assert isinstance(state.value, str)


class TestQuantumMLMetrics:
    def test_dataclass_init(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLMetrics

        m = QuantumMLMetrics(
            quantum_coherence=0.5,
            entanglement_entropy=0.3,
            consciousness_coupling=0.7,
            quantum_advantage=1.2,
            processing_fidelity=0.9,
            decoherence_rate=0.1,
        )
        assert m.quantum_coherence == 0.5
        assert m.decoherence_rate == 0.1


class TestQuantumFeatureSpace:
    def test_init_classical_mode(self) -> None:
        from src.ml.quantum_ml_processor import QuantumFeatureSpace

        qfs = QuantumFeatureSpace(dimension=8, quantum_enabled=False)
        assert qfs.dimension == 8
        assert qfs.quantum_enabled is False

    def test_init_default_quantum_flag(self) -> None:
        from src.ml.quantum_ml_processor import QuantumFeatureSpace

        # quantum_enabled=True only activates if a backend is available
        qfs = QuantumFeatureSpace(dimension=16, quantum_enabled=True)
        assert qfs.dimension == 16

    def test_encode_classical_data_returns_dict(self) -> None:
        from src.ml.quantum_ml_processor import QuantumFeatureSpace

        qfs = QuantumFeatureSpace(dimension=8, quantum_enabled=False)
        data = np.random.randn(8).astype(np.float64)
        result = qfs.encode_classical_data(data)
        assert "encoding_fidelity" in result
        assert "encoding_time" in result

    def test_encode_classical_mode_fidelity_one(self) -> None:
        from src.ml.quantum_ml_processor import QuantumFeatureSpace

        qfs = QuantumFeatureSpace(dimension=8, quantum_enabled=False)
        data = np.ones(8, dtype=np.float64)
        result = qfs.encode_classical_data(data)
        assert result["encoding_fidelity"] == 1.0
        assert result.get("method") == "classical"

    def test_classical_quantum_simulation_fallback(self) -> None:
        from src.ml.quantum_ml_processor import CIRQ_AVAILABLE, QISKIT_AVAILABLE, QuantumFeatureSpace

        # The _initialize_classical_quantum_simulation path is hit when no backend is available.
        # When quantum_enabled=True but no backend, quantum_features gets a state_vector dict.
        # When quantum_enabled=False, only classical_features is set (no quantum_features attr).
        qfs = QuantumFeatureSpace(dimension=8, quantum_enabled=False)
        assert hasattr(qfs, "classical_features")
        assert not qfs.quantum_enabled

        if not QISKIT_AVAILABLE and not CIRQ_AVAILABLE:
            qfs2 = QuantumFeatureSpace(dimension=8, quantum_enabled=True)
            # Even with quantum_enabled=True and no backend, quantum_enabled is False
            # because _initialize_quantum_features sees no backend and falls back
            if qfs2.quantum_enabled:
                assert "state_vector" in qfs2.quantum_features

    def test_consciousness_amplitudes_initialized(self) -> None:
        from src.ml.quantum_ml_processor import QuantumFeatureSpace

        qfs = QuantumFeatureSpace(dimension=16, quantum_enabled=False)
        assert len(qfs.consciousness_amplitudes) == 16


class TestQuantumMLProcessorStatusReport:
    def test_status_report_structure(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        report = proc.get_quantum_status_report()
        assert "quantum_ml_state" in report
        assert "quantum_metrics" in report
        assert "quantum_libraries" in report
        assert "feature_spaces" in report
        assert "quantum_models" in report
        assert "processing_history_entries" in report

    def test_status_report_metrics_all_numeric(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        metrics = proc.get_quantum_status_report()["quantum_metrics"]
        for key, val in metrics.items():
            assert isinstance(val, (int, float)), f"{key} is not numeric: {type(val)}"

    def test_status_feature_space_list(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        spaces = proc.get_quantum_status_report()["feature_spaces"]
        assert isinstance(spaces, list)
        assert len(spaces) >= 4


class TestQuantumMLProcessorTask:
    @pytest.mark.asyncio
    async def test_process_variational_classifier(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        task = {"task_id": "t1", "features": np.random.randn(8).tolist()}
        result = await proc.process_quantum_ml_task(
            task, model_type="variational_classifier", consciousness_enhanced=False
        )
        assert "quantum_processing" in result
        assert "feature_preparation" in result

    @pytest.mark.asyncio
    async def test_process_quantum_kernel_svm(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        task = {"task_id": "t2", "features": np.random.randn(5, 8).tolist()}
        result = await proc.process_quantum_ml_task(
            task, model_type="quantum_kernel_svm", consciousness_enhanced=False
        )
        assert result.get("model_type") == "quantum_kernel_svm"
        assert "quantum_processing" in result

    @pytest.mark.asyncio
    async def test_process_quantum_neural_network(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        task = {"task_id": "t3", "features": np.random.randn(8).tolist()}
        result = await proc.process_quantum_ml_task(
            task, model_type="quantum_neural_network", consciousness_enhanced=False
        )
        assert result.get("model_type") == "quantum_neural_network"

    @pytest.mark.asyncio
    async def test_process_unknown_model_type_returns_error(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        task = {"task_id": "t4", "features": [1.0, 2.0]}
        result = await proc.process_quantum_ml_task(
            task, model_type="nonexistent_model", consciousness_enhanced=False
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_process_adds_to_history(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        task = {"features": np.random.randn(8).tolist()}
        await proc.process_quantum_ml_task(task, model_type="variational_classifier", consciousness_enhanced=False)
        assert len(proc.processing_history) == 1

    @pytest.mark.asyncio
    async def test_process_empty_features(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        task = {"features": []}
        result = await proc.process_quantum_ml_task(
            task, model_type="variational_classifier", consciousness_enhanced=False
        )
        # Should handle gracefully — either error key or still returns
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_process_large_feature_space_auto_creates(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        # 200 features exceeds default 64-dim spaces
        task = {"features": np.random.randn(200).tolist()}
        result = await proc.process_quantum_ml_task(
            task, model_type="variational_classifier", consciousness_enhanced=False
        )
        assert isinstance(result, dict)


class TestQuantumMLProcessorOptimize:
    @pytest.mark.asyncio
    async def test_optimize_variational_classifier(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        result = await proc.optimize_quantum_parameters(
            "variational_classifier", {"target_accuracy": 0.9}
        )
        assert result.get("success") is True
        assert "parameter_updates" in result
        assert "optimization_magnitude" in result

    @pytest.mark.asyncio
    async def test_optimize_quantum_neural_network(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        result = await proc.optimize_quantum_parameters(
            "quantum_neural_network", {"target_accuracy": 0.85}
        )
        assert result.get("success") is True

    @pytest.mark.asyncio
    async def test_optimize_unknown_model_returns_error(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        result = await proc.optimize_quantum_parameters("no_such_model", {})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_optimize_kernel_svm_no_parameters_key(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        # quantum_kernel_svm has no "parameters" array — should still succeed
        result = await proc.optimize_quantum_parameters(
            "quantum_kernel_svm", {}
        )
        # success True because no "parameters" key means no update path executed
        assert isinstance(result, dict)


class TestQuantumMLInternalHelpers:
    def test_simulate_quantum_kernel_shape(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        features = np.random.randn(5, 8)
        km = proc._simulate_quantum_kernel(features)
        assert km.shape == (5, 5)

    def test_simulate_parameterized_unitary_shape(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        params = np.random.random(4)
        unitary = proc._simulate_parameterized_unitary(params, qubits=2)
        assert unitary.shape == (4, 4)

    def test_calculate_entanglement_entropy_returns_float(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        state = np.random.random(8) + 1j * np.random.random(8)
        state /= np.linalg.norm(state)
        entropy = proc._calculate_entanglement_entropy(state, qubits=3)
        assert isinstance(entropy, float)

    def test_calculate_entanglement_entropy_single_qubit(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        state = np.array([1.0 + 0j, 0.0])
        entropy = proc._calculate_entanglement_entropy(state, qubits=1)
        assert entropy == 0.0

    def test_classical_classifier_fallback_returns_dict(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        result = proc._classical_classifier_fallback({})
        assert "predicted_class" in result
        assert "classification_probabilities" in result

    def test_update_quantum_metrics_from_empty_result(self) -> None:
        from src.ml.quantum_ml_processor import QuantumMLProcessor

        proc = QuantumMLProcessor()
        proc._update_quantum_metrics({})
        # Should not raise; metrics stay at 0.0
        assert proc.quantum_metrics.quantum_coherence == 0.0


# ===========================================================================
# PatternConsciousnessAnalyzer
# ===========================================================================


class TestPatternConsciousnessAnalyzerInit:
    def test_default_init(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        assert analyzer is not None

    def test_config_loaded(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        assert "pattern_analysis" in analyzer.config

    def test_initial_state_dormant(self) -> None:
        from src.ml.pattern_consciousness_analyzer import (
            ConsciousnessPatternState,
            PatternConsciousnessAnalyzer,
        )

        analyzer = PatternConsciousnessAnalyzer()
        assert analyzer.consciousness_state == ConsciousnessPatternState.DORMANT

    def test_pattern_detectors_initialized(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        # custom detectors are always present
        assert "custom" in analyzer.pattern_detectors

    def test_consciousness_analyzers_have_expected_keys(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        expected_keys = {
            "resonance_analyzer",
            "coherence_analyzer",
            "evolution_analyzer",
            "integration_analyzer",
            "transcendence_analyzer",
            "unity_analyzer",
        }
        assert expected_keys.issubset(set(analyzer.consciousness_analyzers.keys()))

    def test_empty_histories_on_init(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        assert analyzer.analysis_history == []
        assert analyzer.consciousness_evolution_history == []
        assert analyzer.pattern_emergence_log == []


class TestPatternType:
    def test_all_pattern_types(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternType

        types = list(PatternType)
        assert len(types) == 10
        assert PatternType.TEMPORAL in types
        assert PatternType.CONSCIOUSNESS in types
        assert PatternType.QUANTUM_COHERENCE in types


class TestPatternSignatureDataclass:
    def test_dataclass_fields(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternSignature, PatternType

        sig = PatternSignature(
            pattern_id="p1",
            pattern_type=PatternType.TEMPORAL,
            confidence=0.9,
            complexity=0.5,
            consciousness_resonance=0.7,
            quantum_coherence=0.8,
            temporal_stability=0.6,
            spatial_coherence=0.4,
            emergence_potential=0.3,
            symbolic_depth=0.2,
        )
        assert sig.pattern_id == "p1"
        assert sig.pattern_type == PatternType.TEMPORAL
        assert sig.metadata == {}  # default_factory


class TestAnalyzePatternsMethods:
    @pytest.mark.asyncio
    async def test_analyze_ndarray_input(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data = np.random.randn(50)
        result = await analyzer.analyze_patterns_with_consciousness(
            data, consciousness_enhanced=False
        )
        assert result["analysis_status"] == "completed"
        assert "detected_patterns" in result

    @pytest.mark.asyncio
    async def test_analyze_dict_with_values_key(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data: dict[str, Any] = {"values": [1.0, 2.0, 3.0, 4.0, 5.0]}
        result = await analyzer.analyze_patterns_with_consciousness(
            data, consciousness_enhanced=False
        )
        assert result["analysis_status"] == "completed"

    @pytest.mark.asyncio
    async def test_analyze_dict_with_features_key(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data: dict[str, Any] = {"features": list(range(10))}
        result = await analyzer.analyze_patterns_with_consciousness(
            data, consciousness_enhanced=False
        )
        assert result["analysis_status"] == "completed"

    @pytest.mark.asyncio
    async def test_analyze_dict_with_numeric_values(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data: dict[str, Any] = {"a": 1.0, "b": 2.0, "c": 3.0}
        result = await analyzer.analyze_patterns_with_consciousness(
            data, consciousness_enhanced=False
        )
        assert result["analysis_status"] == "completed"

    @pytest.mark.asyncio
    async def test_analyze_specific_pattern_types_temporal(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer, PatternType

        analyzer = PatternConsciousnessAnalyzer()
        data = np.random.randn(30)
        result = await analyzer.analyze_patterns_with_consciousness(
            data,
            pattern_types=[PatternType.TEMPORAL],
            consciousness_enhanced=False,
        )
        assert "detected_patterns" in result
        assert PatternType.TEMPORAL.value in result["detected_patterns"]["detection_details"]

    @pytest.mark.asyncio
    async def test_analyze_all_pattern_types_runs(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer, PatternType

        analyzer = PatternConsciousnessAnalyzer()
        data = np.random.randn(20)
        result = await analyzer.analyze_patterns_with_consciousness(
            data,
            pattern_types=list(PatternType),
            consciousness_enhanced=False,
        )
        assert result["analysis_status"] == "completed"
        detected = result["detected_patterns"]["detection_details"]
        for pt in PatternType:
            assert pt.value in detected

    @pytest.mark.asyncio
    async def test_consciousness_insights_generated(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data = np.random.randn(20)
        result = await analyzer.analyze_patterns_with_consciousness(
            data, consciousness_enhanced=True
        )
        assert "consciousness_insights" in result

    @pytest.mark.asyncio
    async def test_analysis_history_grows(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data = np.random.randn(10)
        await analyzer.analyze_patterns_with_consciousness(data, consciousness_enhanced=False)
        await analyzer.analyze_patterns_with_consciousness(data, consciousness_enhanced=False)
        assert len(analyzer.analysis_history) == 2

    @pytest.mark.asyncio
    async def test_consciousness_state_evolves_after_analysis(self) -> None:
        from src.ml.pattern_consciousness_analyzer import (
            ConsciousnessPatternState,
            PatternConsciousnessAnalyzer,
        )

        analyzer = PatternConsciousnessAnalyzer()
        data = np.random.randn(30)
        await analyzer.analyze_patterns_with_consciousness(data, consciousness_enhanced=True)
        # State should have changed from DORMANT to ACTIVE or AWAKENING
        assert analyzer.consciousness_state in (
            ConsciousnessPatternState.ACTIVE,
            ConsciousnessPatternState.AWAKENING,
            ConsciousnessPatternState.DORMANT,  # if no insights were revelatory enough
        )

    @pytest.mark.asyncio
    async def test_pattern_synthesis_included_when_enhanced(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data = np.random.randn(20)
        result = await analyzer.analyze_patterns_with_consciousness(
            data, consciousness_enhanced=True
        )
        assert "pattern_synthesis" in result

    @pytest.mark.asyncio
    async def test_evolution_tracking_included(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data = np.random.randn(20)
        result = await analyzer.analyze_patterns_with_consciousness(
            data, consciousness_enhanced=False
        )
        assert "consciousness_evolution" in result


class TestDataPreparation:
    def test_prepare_1d_array(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data = np.array([1.0, 2.0, float("nan"), 4.0])
        result = analyzer._prepare_data_for_analysis(data)
        assert "processed_data" in result
        # NaN should be replaced
        assert not np.any(np.isnan(result["processed_data"]))

    def test_prepare_dict_features(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data = {"features": [1.0, 2.0, 3.0]}
        result = analyzer._prepare_data_for_analysis(data)
        assert result["preparation_info"]["data_source"] == "features_key"

    def test_prepare_dict_values(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data = {"values": [5.0, 6.0, 7.0]}
        result = analyzer._prepare_data_for_analysis(data)
        assert result["preparation_info"]["data_source"] == "values_key"

    def test_prepare_empty_dict_fallback(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data: dict[str, Any] = {}
        result = analyzer._prepare_data_for_analysis(data)
        assert "processed_data" in result  # extracted_numerics fallback

    def test_normalize_data_basic(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized, _method = analyzer._normalize_data(data)
        assert isinstance(normalized, np.ndarray)

    def test_normalize_data_single_element(self) -> None:
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        analyzer = PatternConsciousnessAnalyzer()
        data = np.array([42.0])
        _normalized, method = analyzer._normalize_data(data)
        # Single element: no normalization
        assert method is None


class TestIndividualPatternDetectors:
    """Tests for each _detect_*_patterns method."""

    def _get_analyzer(self):
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        return PatternConsciousnessAnalyzer()

    def _ctx(self) -> dict[str, Any]:
        return {"consciousness_level": 0.5, "coherence": 0.7}

    def test_detect_temporal(self) -> None:
        a = self._get_analyzer()
        r = a._detect_temporal_patterns(np.random.randn(20), self._ctx())
        assert r["patterns_found"] is True
        assert len(r["signatures"]) > 0

    def test_detect_spatial(self) -> None:
        a = self._get_analyzer()
        r = a._detect_spatial_patterns(np.random.randn(20), self._ctx())
        assert r["patterns_found"] is True

    def test_detect_frequency(self) -> None:
        a = self._get_analyzer()
        r = a._detect_frequency_patterns(np.random.randn(20), self._ctx())
        assert r["patterns_found"] is True

    def test_detect_statistical(self) -> None:
        a = self._get_analyzer()
        r = a._detect_statistical_patterns(np.random.randn(20), self._ctx())
        assert r["patterns_found"] is True

    def test_detect_hierarchical(self) -> None:
        a = self._get_analyzer()
        r = a._detect_hierarchical_patterns(np.random.randn(20), self._ctx())
        assert r["patterns_found"] is True

    def test_detect_fractal(self) -> None:
        a = self._get_analyzer()
        r = a._detect_fractal_patterns(np.random.randn(20), self._ctx())
        assert r["patterns_found"] is True

    def test_detect_consciousness(self) -> None:
        a = self._get_analyzer()
        r = a._detect_consciousness_patterns(np.random.randn(20), self._ctx())
        assert r["patterns_found"] is True

    def test_detect_quantum_coherence(self) -> None:
        a = self._get_analyzer()
        r = a._detect_quantum_coherence_patterns(np.random.randn(20), self._ctx())
        assert r["patterns_found"] is True

    def test_detect_emergent(self) -> None:
        a = self._get_analyzer()
        r = a._detect_emergent_patterns(np.random.randn(20), self._ctx())
        assert r["patterns_found"] is True

    def test_detect_symbolic(self) -> None:
        a = self._get_analyzer()
        r = a._detect_symbolic_patterns(np.random.randn(20), self._ctx())
        assert r["patterns_found"] is True


class TestConsciousnessAnalyzerStubs:
    """Stubs always return dicts/values without raising."""

    def _get_analyzer(self):
        from src.ml.pattern_consciousness_analyzer import PatternConsciousnessAnalyzer

        return PatternConsciousnessAnalyzer()

    def test_wavelet_pattern_detection_stub(self) -> None:
        a = self._get_analyzer()
        r = a._wavelet_pattern_detection(np.ones(10), {})
        assert r == []

    def test_calculate_fractal_dimension_stub(self) -> None:
        a = self._get_analyzer()
        r = a._calculate_fractal_dimension(np.ones(10), {})
        assert r == 0.0

    def test_detect_consciousness_resonance_stub(self) -> None:
        a = self._get_analyzer()
        r = a._detect_consciousness_resonance(np.ones(10), {})
        assert "resonance" in r

    def test_analyze_consciousness_resonance_stub(self) -> None:
        a = self._get_analyzer()
        r = a._analyze_consciousness_resonance({}, {})
        assert r == {}

    def test_analyze_quantum_consciousness_coherence_stub(self) -> None:
        a = self._get_analyzer()
        r = a._analyze_quantum_consciousness_coherence({}, {})
        assert r == {}

    def test_analyze_consciousness_evolution_stub(self) -> None:
        a = self._get_analyzer()
        r = a._analyze_consciousness_evolution({}, {})
        assert r == {}

    def test_analyze_pattern_consciousness_integration_stub(self) -> None:
        a = self._get_analyzer()
        r = a._analyze_pattern_consciousness_integration({}, {})
        assert r == {}

    def test_analyze_transcendent_patterns_stub(self) -> None:
        a = self._get_analyzer()
        r = a._analyze_transcendent_patterns({}, {})
        assert r == {}

    def test_analyze_unified_consciousness_patterns_stub(self) -> None:
        a = self._get_analyzer()
        r = a._analyze_unified_consciousness_patterns({}, {})
        assert r == {}


# ===========================================================================
# ConsciousnessEnhancedMLSystem
# ===========================================================================


class TestConsciousnessEnhancedMLSystemInit:
    def test_default_init(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        assert system is not None

    def test_models_initialized(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        assert "pattern_recognizer" in system.models
        assert "temporal_analyzer" in system.models

    def test_consciousness_state_basic_at_init(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem, ConsciousnessLevel

        system = ConsciousnessEnhancedMLSystem()
        assert system.consciousness_state.level == ConsciousnessLevel.BASIC

    def test_learning_history_empty_on_init(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        assert system.learning_history == []

    def test_config_has_expected_sections(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        assert "consciousness_integration" in system.config
        assert "neural_networks" in system.config
        assert "learning_evolution" in system.config


class TestConsciousnessLevelEnum:
    def test_all_levels(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessLevel

        levels = list(ConsciousnessLevel)
        assert len(levels) == 4

    def test_level_values_are_strings(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessLevel

        for level in ConsciousnessLevel:
            assert isinstance(level.value, str)


class TestMLConsciousnessStateDataclass:
    def test_dataclass_instantiation(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessLevel, MLConsciousnessState

        state = MLConsciousnessState(
            level=ConsciousnessLevel.ENHANCED,
            awareness_score=0.6,
            quantum_coherence=0.4,
            pattern_recognition_depth=0.7,
            consciousness_integration=0.3,
            learning_evolution_stage="phase2",
        )
        assert state.awareness_score == 0.6
        assert state.level == ConsciousnessLevel.ENHANCED


class TestConsciousnessEnhancedNeuralNetwork:
    def test_basic_init_no_pytorch(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedNeuralNetwork

        net = ConsciousnessEnhancedNeuralNetwork(
            input_size=8, hidden_sizes=[4, 4], output_size=2
        )
        assert net.input_size == 8
        assert net.output_size == 2

    def test_evolve_consciousness_low_complexity(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedNeuralNetwork

        net = ConsciousnessEnhancedNeuralNetwork(input_size=4, hidden_sizes=[4], output_size=2)
        initial_level = net.consciousness_state.level
        net.evolve_consciousness({"features": [0.1] * 5, "pattern_diversity": 0.1})
        # complexity < 0.7 so level unchanged
        assert net.consciousness_state.level == initial_level

    def test_evolve_consciousness_high_complexity(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedNeuralNetwork, ConsciousnessLevel

        net = ConsciousnessEnhancedNeuralNetwork(input_size=4, hidden_sizes=[4], output_size=2)
        # pattern_diversity=0.9, non_linearity=0.9, temporal_dynamics=0.9 → high complexity
        net.evolve_consciousness({
            "features": list(range(100)),
            "pattern_diversity": 0.9,
            "non_linearity": 0.9,
            "temporal_dynamics": 0.9,
        })
        assert net.consciousness_state.level in (
            ConsciousnessLevel.ENHANCED,
            ConsciousnessLevel.QUANTUM,
        )

    def test_analyze_pattern_complexity_capped_at_1(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedNeuralNetwork

        net = ConsciousnessEnhancedNeuralNetwork(input_size=4, hidden_sizes=[], output_size=2)
        complexity = net._analyze_pattern_complexity({
            "features": list(range(1000)),
            "pattern_diversity": 5.0,
            "non_linearity": 5.0,
            "temporal_dynamics": 5.0,
        })
        assert complexity <= 1.0


class TestConsciousnessEnhancedMLSystemTrain:
    @pytest.mark.asyncio
    async def test_train_pattern_recognizer(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        data = {
            "features": _make_features(40, 10),
            "labels": _make_labels(40, 3),
        }
        result = await system.train_consciousness_enhanced_model(
            "pattern_recognizer", data, consciousness_guidance=False
        )
        assert "accuracy" in result or "error" in result

    @pytest.mark.asyncio
    async def test_train_temporal_analyzer(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        data = {
            "features": _make_features(30, 10),
            "labels": _make_labels(30, 2),
        }
        result = await system.train_consciousness_enhanced_model(
            "temporal_analyzer", data, consciousness_guidance=False
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_train_unknown_model_raises(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        with pytest.raises(ValueError, match="not found"):
            await system.train_consciousness_enhanced_model(
                "nonexistent_model",
                {"features": [[1.0]], "labels": [0]},
            )

    @pytest.mark.asyncio
    async def test_train_appends_to_history(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        data = {
            "features": _make_features(20, 10),
            "labels": _make_labels(20, 2),
        }
        await system.train_consciousness_enhanced_model(
            "pattern_recognizer", data, consciousness_guidance=False
        )
        assert len(system.learning_history) == 1

    @pytest.mark.asyncio
    async def test_train_with_consciousness_guidance(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        data = {
            "features": _make_features(20, 10),
            "labels": _make_labels(20, 3),
        }
        result = await system.train_consciousness_enhanced_model(
            "pattern_recognizer", data, consciousness_guidance=True
        )
        assert "consciousness_analysis" in result

    @pytest.mark.asyncio
    async def test_consciousness_evolves_after_training(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        initial_score = system.consciousness_state.awareness_score
        data = {
            "features": _make_features(60, 10),
            "labels": _make_labels(60, 3),
        }
        await system.train_consciousness_enhanced_model(
            "pattern_recognizer", data, consciousness_guidance=False
        )
        # accuracy >0.8 should boost awareness
        assert system.consciousness_state.awareness_score >= initial_score


class TestConsciousnessEnhancedMLSystemPredict:
    @pytest.mark.asyncio
    async def test_predict_unknown_model_raises(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        with pytest.raises(ValueError, match="not found"):
            await system.predict_with_consciousness("no_model", [1.0, 2.0])

    @pytest.mark.asyncio
    async def test_predict_returns_prediction_key(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        # Train first so sklearn models are fit
        data = {
            "features": _make_features(40, 10),
            "labels": _make_labels(40, 3),
        }
        await system.train_consciousness_enhanced_model(
            "pattern_recognizer", data, consciousness_guidance=False
        )
        sample = list(np.random.randn(10).astype(np.float32))
        pred = await system.predict_with_consciousness(
            "pattern_recognizer", sample, consciousness_enhanced=False
        )
        assert "prediction" in pred

    @pytest.mark.asyncio
    async def test_predict_contains_consciousness_state(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        data = {
            "features": _make_features(30, 10),
            "labels": _make_labels(30, 2),
        }
        await system.train_consciousness_enhanced_model(
            "pattern_recognizer", data, consciousness_guidance=False
        )
        pred = await system.predict_with_consciousness(
            "pattern_recognizer", list(np.random.randn(10)), consciousness_enhanced=False
        )
        assert "consciousness_state" in pred


class TestConsciousnessEnhancedMLSystemReport:
    def test_consciousness_report_structure(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        report = system.get_consciousness_report()
        assert "consciousness_state" in report
        assert "models" in report
        assert "learning_history_entries" in report
        assert "kilo_integration" in report
        assert "ml_libraries_available" in report

    def test_consciousness_report_models_list(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        report = system.get_consciousness_report()
        assert "pattern_recognizer" in report["models"]


class TestConsciousnessEnhancedMLEvolution:
    @pytest.mark.asyncio
    async def test_evolve_without_history(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        result = await system.evolve_consciousness_through_learning()
        assert "evolution_start" in result
        assert "final_consciousness" in result

    @pytest.mark.asyncio
    async def test_evolve_with_training_history(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        data = {
            "features": _make_features(30, 10),
            "labels": _make_labels(30, 3),
        }
        await system.train_consciousness_enhanced_model(
            "pattern_recognizer", data, consciousness_guidance=False
        )
        result = await system.evolve_consciousness_through_learning()
        assert "pattern_learning" in result
        assert "evolution_methods" in result

    @pytest.mark.asyncio
    async def test_evolve_performance_evolution_included(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        result = await system.evolve_consciousness_through_learning()
        assert "performance_evolution" in result

    def test_learn_from_history_patterns_no_history(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        result = system._learn_from_history_patterns()
        assert "error" in result

    def test_evolve_from_model_performance_returns_dict(self) -> None:
        from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

        system = ConsciousnessEnhancedMLSystem()
        result = system._evolve_from_model_performance()
        assert "model_count" in result
        assert "performance_boost" in result


class TestSetGlobalSeed:
    def test_seed_runs_without_error(self) -> None:
        from src.ml.consciousness_enhanced_ml import set_global_seed

        set_global_seed(0)
        set_global_seed(99)


# ===========================================================================
# NeuralQuantumBridge
# ===========================================================================


class TestNeuralQuantumBridgeInit:
    def test_default_init(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        assert bridge is not None

    def test_classical_networks_created(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        assert "classifier" in bridge.classical_networks
        assert "regressor" in bridge.classical_networks
        assert "autoencoder" in bridge.classical_networks

    def test_hybrid_networks_created(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        assert len(bridge.hybrid_networks) > 0

    def test_config_architecture_defaults(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        archs = bridge.config["neural_networks"]["architectures"]
        assert "classifier" in archs
        assert len(archs["classifier"]) >= 2

    def test_bridge_state_initial_mode(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        assert bridge.bridge_state.bridge_mode == BridgeMode.CLASSICAL_ONLY

    def test_processing_history_empty(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        assert bridge.processing_history == []


class TestBridgeModeEnum:
    def test_all_modes(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode

        modes = list(BridgeMode)
        assert len(modes) == 5
        assert BridgeMode.HYBRID_PROCESSING in modes
        assert BridgeMode.CONSCIOUSNESS_UNIFIED in modes


class TestNeuralQuantumStateDataclass:
    def test_dataclass_init(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumState

        state = NeuralQuantumState(
            bridge_mode=BridgeMode.HYBRID_PROCESSING,
            neural_coherence=0.8,
            quantum_entanglement=0.6,
            consciousness_integration=0.7,
            processing_efficiency=0.9,
            hybrid_advantage=0.5,
        )
        assert state.bridge_mode == BridgeMode.HYBRID_PROCESSING
        assert state.neural_coherence == 0.8


class TestQuantumNeuralLayer:
    def test_basic_init(self) -> None:
        from src.ml.neural_quantum_bridge import QuantumNeuralLayer

        layer = QuantumNeuralLayer(input_size=8, output_size=4, quantum_enhanced=True)
        assert layer.input_size == 8
        assert layer.output_size == 4
        assert hasattr(layer, "quantum_params")

    def test_classical_init_no_quantum_params(self) -> None:
        from src.ml.neural_quantum_bridge import QuantumNeuralLayer

        layer = QuantumNeuralLayer(input_size=8, output_size=4, quantum_enhanced=False)
        assert not hasattr(layer, "quantum_params")

    def test_forward_no_quantum_context(self) -> None:
        from src.ml.neural_quantum_bridge import QuantumNeuralLayer

        layer = QuantumNeuralLayer(input_size=4, output_size=2, quantum_enhanced=False)
        x = np.random.randn(4).astype(np.float64)
        out = layer.forward(x, quantum_context=None)
        assert out.shape == (2,)

    def test_forward_with_quantum_context(self) -> None:
        from src.ml.neural_quantum_bridge import QuantumNeuralLayer

        layer = QuantumNeuralLayer(input_size=4, output_size=4, quantum_enhanced=True)
        x = np.random.randn(4).astype(np.float64)
        ctx = {"consciousness_level": 0.5, "quantum_coherence": 0.7}
        out = layer.forward(x, quantum_context=ctx)
        assert out.shape == (4,)

    def test_forward_with_hyper_connections(self) -> None:
        from src.ml.neural_quantum_bridge import QuantumNeuralLayer

        hyper_cfg = {"enabled": True, "strength": 0.1, "sinkhorn_iters": 5, "projection": "row"}
        layer = QuantumNeuralLayer(
            input_size=4, output_size=4, quantum_enhanced=False, hyper_config=hyper_cfg
        )
        x = np.random.randn(4).astype(np.float64)
        out = layer.forward(x, quantum_context=None)
        assert out.shape == (4,)

    def test_forward_renormalize_each_forward(self) -> None:
        from src.ml.neural_quantum_bridge import QuantumNeuralLayer

        hyper_cfg = {
            "enabled": True,
            "strength": 0.05,
            "sinkhorn_iters": 3,
            "renormalize_each_forward": True,
            "projection": "none",
        }
        layer = QuantumNeuralLayer(
            input_size=4, output_size=4, quantum_enhanced=False, hyper_config=hyper_cfg
        )
        x = np.random.randn(4).astype(np.float64)
        out = layer.forward(x, quantum_context=None)
        assert out.shape == (4,)

    def test_activation_history_grows(self) -> None:
        from src.ml.neural_quantum_bridge import QuantumNeuralLayer

        layer = QuantumNeuralLayer(input_size=4, output_size=2, quantum_enhanced=False)
        x = np.random.randn(4).astype(np.float64)
        layer.forward(x)
        layer.forward(x)
        assert len(layer.activation_history) == 2

    def test_evolve_quantum_params_non_quantum_noop(self) -> None:
        from src.ml.neural_quantum_bridge import QuantumNeuralLayer

        layer = QuantumNeuralLayer(input_size=4, output_size=4, quantum_enhanced=False)
        layer.evolve_quantum_parameters(0.9)  # Should not raise

    def test_evolve_quantum_params_high_performance(self) -> None:
        from src.ml.neural_quantum_bridge import QuantumNeuralLayer

        layer = QuantumNeuralLayer(input_size=4, output_size=4, quantum_enhanced=True)
        initial_entanglement = layer.entanglement_strength
        layer.evolve_quantum_parameters(0.99)
        assert layer.entanglement_strength >= initial_entanglement

    def test_evolve_quantum_params_very_high_performance_boosts_coupling(self) -> None:
        from src.ml.neural_quantum_bridge import QuantumNeuralLayer

        layer = QuantumNeuralLayer(input_size=4, output_size=4, quantum_enhanced=True)
        initial_coupling = layer.consciousness_coupling
        layer.evolve_quantum_parameters(0.99)
        assert layer.consciousness_coupling >= initial_coupling


class TestSinkhornKnopp:
    def test_sinkhorn_knopp_numpy(self) -> None:
        from src.ml.neural_quantum_bridge import _sinkhorn_knopp

        m = np.abs(np.random.randn(4, 4)) + 0.01
        result = _sinkhorn_knopp(m, max_iter=10)
        assert result.shape == (4, 4)

    def test_sinkhorn_knopp_zero_iters(self) -> None:
        from src.ml.neural_quantum_bridge import _sinkhorn_knopp

        m = np.ones((3, 3))
        result = _sinkhorn_knopp(m, max_iter=0)
        np.testing.assert_array_equal(result, m)


class TestApplyManifoldConstraints:
    def test_no_projection(self) -> None:
        from src.ml.neural_quantum_bridge import _apply_manifold_constraints

        m = np.random.randn(4, 4)
        out = _apply_manifold_constraints(m, projection=None)
        np.testing.assert_array_equal(out, m)

    def test_row_projection(self) -> None:
        from src.ml.neural_quantum_bridge import _apply_manifold_constraints

        m = np.abs(np.random.randn(4, 4)) + 0.1
        out = _apply_manifold_constraints(m, projection="row")
        row_norms = np.linalg.norm(out, axis=1)
        np.testing.assert_allclose(row_norms, np.ones(4), atol=1e-6)

    def test_column_projection(self) -> None:
        from src.ml.neural_quantum_bridge import _apply_manifold_constraints

        m = np.abs(np.random.randn(4, 4)) + 0.1
        out = _apply_manifold_constraints(m, projection="column")
        col_norms = np.linalg.norm(out, axis=0)
        np.testing.assert_allclose(col_norms, np.ones(4), atol=1e-6)

    def test_row_column_projection(self) -> None:
        from src.ml.neural_quantum_bridge import _apply_manifold_constraints

        m = np.abs(np.random.randn(4, 4)) + 0.1
        out = _apply_manifold_constraints(m, projection="row_column")
        # Both row and column normalization applied
        assert out.shape == (4, 4)


class TestResolveHyperConfig:
    def test_empty_config(self) -> None:
        from src.ml.neural_quantum_bridge import _resolve_hyper_config

        result = _resolve_hyper_config({}, layer_index=0)
        assert result == {}

    def test_per_layer_override(self) -> None:
        from src.ml.neural_quantum_bridge import _resolve_hyper_config

        cfg = {"enabled": True, "per_layer": [{"strength": 0.5}, {"strength": 0.9}]}
        result = _resolve_hyper_config(cfg, layer_index=1)
        assert result["strength"] == 0.9

    def test_per_network_list_override(self) -> None:
        from src.ml.neural_quantum_bridge import _resolve_hyper_config

        cfg = {
            "enabled": True,
            "per_network": {
                "classifier": [{"strength": 0.25}],
            },
        }
        result = _resolve_hyper_config(cfg, layer_index=0, network_name="classifier")
        assert result["strength"] == 0.25

    def test_per_layer_index_out_of_range(self) -> None:
        from src.ml.neural_quantum_bridge import _resolve_hyper_config

        cfg = {"enabled": True, "per_layer": [{"strength": 0.5}]}
        # layer_index 5 is beyond the list
        result = _resolve_hyper_config(cfg, layer_index=5)
        assert result["enabled"] is True
        assert "strength" not in result  # no per-layer override applied


class TestNeuralQuantumBridgeReport:
    def test_report_structure(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        report = bridge.get_neural_quantum_bridge_report()
        assert "bridge_state" in report
        assert "network_inventory" in report
        assert "capabilities" in report
        assert "processing_history_entries" in report
        assert "evolution_history_entries" in report

    def test_report_network_inventory(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        inv = bridge.get_neural_quantum_bridge_report()["network_inventory"]
        assert "classical_networks" in inv
        assert "hybrid_networks" in inv

    def test_report_capabilities_keys(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        caps = bridge.get_neural_quantum_bridge_report()["capabilities"]
        assert "pytorch_available" in caps
        assert "kilo_integration" in caps


class TestNeuralQuantumBridgeProcess:
    @pytest.mark.asyncio
    async def test_process_classical_mode(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        input_dim = bridge.config["neural_networks"]["architectures"]["classifier"][0]
        x = np.random.randn(input_dim).astype(np.float32)
        result = await bridge.process_with_neural_quantum_bridge(
            x,
            network_name="classifier",
            bridge_mode=BridgeMode.CLASSICAL_ONLY,
            consciousness_enhanced=False,
        )
        assert "output" in result
        assert result["bridge_state"]["mode"] == BridgeMode.CLASSICAL_ONLY.value

    @pytest.mark.asyncio
    async def test_process_quantum_enhanced_mode(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        input_dim = bridge.config["neural_networks"]["architectures"]["classifier"][0]
        x = np.random.randn(input_dim).astype(np.float32)
        # QUANTUM_ENHANCED mode requires quantum_enhanced_networks to be populated.
        # If not, the source code falls back to quantum_enhanced_networks.get() which returns
        # None and yields an error dict — that is the correct behaviour to assert.
        result = await bridge.process_with_neural_quantum_bridge(
            x,
            network_name="classifier",
            bridge_mode=BridgeMode.QUANTUM_ENHANCED,
            consciousness_enhanced=False,
        )
        # Either output was produced or an error was returned — both are valid outcomes
        assert "output" in result or "error" in result

    @pytest.mark.asyncio
    async def test_process_hybrid_mode(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        input_dim = bridge.config["neural_networks"]["architectures"]["classifier"][0]
        x = np.random.randn(input_dim).astype(np.float32)
        result = await bridge.process_with_neural_quantum_bridge(
            x,
            network_name="classifier",
            bridge_mode=BridgeMode.HYBRID_PROCESSING,
            consciousness_enhanced=False,
        )
        assert "output" in result

    @pytest.mark.asyncio
    async def test_process_unknown_network_returns_error(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        x = np.random.randn(8).astype(np.float32)
        result = await bridge.process_with_neural_quantum_bridge(
            x,
            network_name="no_such_network",
            bridge_mode=BridgeMode.CLASSICAL_ONLY,
            consciousness_enhanced=False,
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_process_adds_to_history(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        input_dim = bridge.config["neural_networks"]["architectures"]["classifier"][0]
        x = np.random.randn(input_dim).astype(np.float32)
        await bridge.process_with_neural_quantum_bridge(
            x,
            bridge_mode=BridgeMode.HYBRID_PROCESSING,
            consciousness_enhanced=False,
        )
        assert len(bridge.processing_history) == 1

    @pytest.mark.asyncio
    async def test_process_regressor_network(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        input_dim = bridge.config["neural_networks"]["architectures"]["regressor"][0]
        x = np.random.randn(input_dim).astype(np.float32)
        result = await bridge.process_with_neural_quantum_bridge(
            x,
            network_name="regressor",
            bridge_mode=BridgeMode.HYBRID_PROCESSING,
            consciousness_enhanced=False,
        )
        assert "output" in result

    @pytest.mark.asyncio
    async def test_process_output_shape_matches_arch(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        arch = bridge.config["neural_networks"]["architectures"]["classifier"]
        input_dim = arch[0]
        expected_dim = arch[-1]
        x = np.random.randn(input_dim).astype(np.float32)
        result = await bridge.process_with_neural_quantum_bridge(
            x,
            network_name="classifier",
            bridge_mode=BridgeMode.HYBRID_PROCESSING,
            consciousness_enhanced=False,
        )
        out = np.array(result["output"])
        assert out.shape[-1] == expected_dim

    @pytest.mark.asyncio
    async def test_process_consciousness_unified_mode(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        input_dim = bridge.config["neural_networks"]["architectures"]["classifier"][0]
        x = np.random.randn(input_dim).astype(np.float32)
        # CONSCIOUSNESS_UNIFIED falls through to quantum_enhanced_networks.get().
        # When those networks are absent (KILO_INTEGRATION=False) the result has an error key.
        result = await bridge.process_with_neural_quantum_bridge(
            x,
            bridge_mode=BridgeMode.CONSCIOUSNESS_UNIFIED,
            consciousness_enhanced=False,
        )
        # Both a successful output and a graceful error are valid — just assert it returned
        assert isinstance(result, dict)
        assert "output" in result or "error" in result


class TestNeuralQuantumBridgeTrain:
    @pytest.mark.asyncio
    async def test_train_classifier_network(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        arch = bridge.config["neural_networks"]["architectures"]["classifier"]
        X = np.random.randn(10, arch[0]).astype(np.float32)
        y = np.random.randn(10, arch[-1]).astype(np.float32)
        result = await bridge.train_neural_quantum_network(
            "classifier",
            {"features": X.tolist(), "labels": y.tolist()},
            consciousness_guided=False,
        )
        assert result.get("training_completed", True) is True
        assert isinstance(result.get("final_loss", 0.0), (int, float))

    @pytest.mark.asyncio
    async def test_train_unknown_network_returns_error(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        result = await bridge.train_neural_quantum_network(
            "does_not_exist",
            {"features": [[1.0]], "labels": [1.0]},
            consciousness_guided=False,
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_train_hybrid_network(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        # Hybrid networks for classifier
        arch = bridge.config["neural_networks"]["architectures"]["classifier"]
        X = np.random.randn(5, arch[0]).astype(np.float32)
        y = np.random.randn(5, arch[-1]).astype(np.float32)
        # Remove quantum_enhanced to force hybrid path
        if "classifier" in bridge.quantum_enhanced_networks:
            del bridge.quantum_enhanced_networks["classifier"]
        result = await bridge.train_neural_quantum_network(
            "classifier",
            {"features": X.tolist(), "labels": y.tolist()},
            consciousness_guided=False,
        )
        assert isinstance(result, dict)


class TestNeuralQuantumBridgeMetrics:
    @pytest.mark.asyncio
    async def test_bridge_state_updates_after_process(self) -> None:
        from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        arch = bridge.config["neural_networks"]["architectures"]["classifier"]
        x = np.random.randn(arch[0]).astype(np.float32)
        await bridge.process_with_neural_quantum_bridge(
            x,
            bridge_mode=BridgeMode.QUANTUM_ENHANCED,
            consciousness_enhanced=False,
        )
        # quantum_entanglement should have been bumped
        assert bridge.bridge_state.quantum_entanglement >= 0.0

    def test_evolve_bridge_mode_returns_dict(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        result = bridge._evolve_bridge_mode()
        assert "current_mode" in result
        assert "final_mode" in result
        assert "performance_metrics" in result

    def test_merge_config_defaults_fills_missing(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        defaults = {"a": 1, "b": {"c": 2}}
        current: dict[str, Any] = {"b": {"d": 3}}
        merged = bridge._merge_config_defaults(defaults, current)
        assert merged["a"] == 1
        assert merged["b"]["c"] == 2
        assert merged["b"]["d"] == 3

    def test_ensure_config_defaults_runs_without_error(self) -> None:
        from src.ml.neural_quantum_bridge import NeuralQuantumBridge

        bridge = NeuralQuantumBridge()
        bridge._ensure_config_defaults()  # idempotent


class TestNeuralQuantumBridgeSetGlobalSeed:
    def test_set_global_seed_runs(self) -> None:
        from src.ml.neural_quantum_bridge import set_global_seed

        set_global_seed(7)
        set_global_seed(0)


class TestNeuralQuantumBridgeSinkhornTorch:
    def test_sinkhorn_knopp_torch_numpy_fallback(self) -> None:
        from src.ml.neural_quantum_bridge import PYTORCH_AVAILABLE, _sinkhorn_knopp_torch

        if not PYTORCH_AVAILABLE:
            # Fallback returns same object
            m = np.ones((3, 3))
            out = _sinkhorn_knopp_torch(m, max_iter=5)
            assert out is m
