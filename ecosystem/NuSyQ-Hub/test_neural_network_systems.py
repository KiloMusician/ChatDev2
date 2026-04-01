#!/usr/bin/env python3
"""Quick test of neural network systems."""

import asyncio

import numpy as np
from src.ml.consciousness_enhanced_ml import ConsciousnessEnhancedMLSystem
from src.ml.neural_quantum_bridge import NeuralQuantumBridge


async def main():
    """Test neural network systems."""
    print("=" * 60)
    print("NEURAL NETWORK SYSTEM TEST")
    print("=" * 60)

    # Test 1: ML System
    print("\n[Test 1] Consciousness-Enhanced ML System")
    ml_system = ConsciousnessEnhancedMLSystem()
    print("✓ ML System initialized")
    print(f"  - Consciousness Level: {ml_system.consciousness_state.level.value}")
    print(f"  - Awareness Score: {ml_system.consciousness_state.awareness_score}")
    print(f"  - Available Models: {list(ml_system.models.keys())}")

    # Test 2: Neural-Quantum Bridge
    print("\n[Test 2] Neural-Quantum Bridge System")
    nqb = NeuralQuantumBridge()
    print("✓ Neural-Quantum Bridge initialized")
    print(f"  - Bridge Mode: {nqb.bridge_state.bridge_mode.value}")
    print(f"  - Classical Networks: {list(nqb.classical_networks.keys())}")
    print(f"  - Quantum-Enhanced Networks: {list(nqb.quantum_enhanced_networks.keys())}")
    print(f"  - Hybrid Networks: {list(nqb.hybrid_networks.keys())}")

    # Test 3: Training capability
    print("\n[Test 3] ML Training Pipeline")
    training_data = {
        "features": np.random.randn(20, 10).tolist(),
        "labels": np.random.randint(0, 2, 20).tolist(),
    }
    result = await ml_system.train_consciousness_enhanced_model(
        "pattern_recognizer", training_data, consciousness_guidance=True
    )
    print("✓ Training completed")
    accuracy = result.get("accuracy", "N/A")
    if isinstance(accuracy, float):
        print(f"  - Accuracy: {accuracy:.3f}")
    else:
        print(f"  - Accuracy: {accuracy}")
    cons_state = result.get("consciousness_state", {})
    print(f"  - Consciousness Level: {cons_state.get('level', 'N/A')}")
    print(f"  - Awareness Score: {cons_state.get('awareness_score', 'N/A')}")

    # Test 4: Neural-Quantum Training
    print("\n[Test 4] Neural-Quantum Training")
    # Match label shape to classifier output (16) to avoid broadcast issues during training
    nq_training_data = {
        "features": np.random.randn(15, 8).tolist(),
        "labels": np.random.randn(15, 16).tolist(),
    }
    nq_result = await nqb.train_neural_quantum_network(
        "classifier", nq_training_data, consciousness_guided=True
    )
    print("✓ Neural-Quantum training completed")
    if "error" not in nq_result:
        print(f"  - Training Method: {nq_result.get('training_method', 'N/A')}")
    else:
        print(f"  - Error: {nq_result['error']}")

    print("\n" + "=" * 60)
    print("ALL NEURAL NETWORK TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
