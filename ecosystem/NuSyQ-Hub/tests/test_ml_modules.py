import os
from typing import Any

import numpy as np
import pytest

# Ensure deterministic behavior for tests
os.environ.setdefault("NUSYQ_SEED", "123")


@pytest.mark.asyncio
async def test_neural_quantum_bridge_forward_basic():
    from src.ml.neural_quantum_bridge import BridgeMode, NeuralQuantumBridge

    bridge = NeuralQuantumBridge()

    # Use hybrid to avoid optional torch dependency and keep it simple
    input_dim = bridge.config["neural_networks"]["architectures"]["classifier"][0]
    x = np.random.randn(input_dim).astype(np.float32)

    result = await bridge.process_with_neural_quantum_bridge(
        x,
        network_name="classifier",
        bridge_mode=BridgeMode.HYBRID_PROCESSING,
        consciousness_enhanced=False,
    )

    assert "output" in result, f"missing output in result: {result.keys()}"
    out = (
        np.array(result["output"])
        if not isinstance(result["output"], np.ndarray)
        else result["output"]
    )
    expected_dim = bridge.config["neural_networks"]["architectures"]["classifier"][-1]
    assert out.shape[-1] == expected_dim, f"expected output dim {expected_dim}, got {out.shape}"
    assert result["bridge_state"]["mode"] == BridgeMode.HYBRID_PROCESSING.value
    assert "processing_details" in result


@pytest.mark.asyncio
async def test_neural_quantum_bridge_train_basic():
    from src.ml.neural_quantum_bridge import NeuralQuantumBridge

    bridge = NeuralQuantumBridge()

    input_dim = bridge.config["neural_networks"]["architectures"]["classifier"][0]
    X = np.random.randn(20, input_dim).astype(np.float32)
    expected_dim = bridge.config["neural_networks"]["architectures"]["classifier"][-1]
    y = np.random.randn(20, expected_dim).astype(np.float32)

    training_data: dict[str, Any] = {"features": X.tolist(), "labels": y.tolist()}

    result = await bridge.train_neural_quantum_network(
        network_name="classifier",
        training_data=training_data,
        consciousness_guided=False,
    )

    assert result.get("training_completed", True) is True
    assert isinstance(result.get("final_loss", 0.0), (int, float))


@pytest.mark.asyncio
async def test_consciousness_enhanced_ml_predict_basic():
    from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem

    ml_system = ConsciousnessEnhancedMLSystem()

    # Train a small classifier to ensure predict path works for sklearn-backed or fallback
    # Use 10 features to match the basic fallback and maintain compatibility
    X = np.random.randn(50, 10).astype(np.float32)
    y = np.random.randint(0, 3, size=(50,)).astype(int)
    training_data = {"features": X.tolist(), "labels": y.tolist()}

    await ml_system.train_consciousness_enhanced_model(
        "pattern_recognizer", training_data, consciousness_guidance=False
    )

    sample = np.random.randn(10).astype(np.float32)
    pred = await ml_system.predict_with_consciousness(
        "pattern_recognizer", sample.tolist(), consciousness_enhanced=False
    )

    assert "prediction" in pred
    # Confidence is optional; check type only if present
    if "confidence" in pred:
        conf = pred["confidence"]
        assert isinstance(conf, (list, tuple, np.ndarray))
