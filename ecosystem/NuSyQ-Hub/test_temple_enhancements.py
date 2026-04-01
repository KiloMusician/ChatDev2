"""Quick verification test for temple floor enhancements."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from consciousness.temple_of_knowledge.floor_2_patterns import Floor2PatternRecognition
from consciousness.temple_of_knowledge.floor_3_systems import Floor3SystemsThinking
from consciousness.temple_of_knowledge.floor_4_metacognition import Floor4Metacognition


def test_floor_2_pattern_recognition():
    """Test AST-based pattern recognition."""
    floor = Floor2PatternRecognition()

    # Test singleton pattern detection
    singleton_code = """
class MySingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
"""

    results = floor.recognize_pattern(singleton_code)
    print("✅ Floor 2 - Pattern Recognition Test:")
    print(f"   Detected {len(results)} patterns")
    for pattern in results:
        print(f"   - {pattern['pattern']}: confidence={pattern['confidence']}")

    assert len(results) > 0, "Should detect at least one pattern"
    assert any(p["pattern"] == "singleton" for p in results), "Should detect singleton"
    print()


def test_floor_3_feedback_loop():
    """Test causal analysis feedback loop detection."""
    floor = Floor3SystemsThinking()

    result = floor.detect_feedback_loop(
        "Population Growth", ["births", "population", "growth", "resources"]
    )

    print("✅ Floor 3 - Feedback Loop Test:")
    print(f"   System: {result['system']}")
    print(f"   Loop Type: {result['loop_type']}")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Causal Links: {len(result['causal_links'])}")
    for link in result["causal_links"]:
        print(f"   - {link['from']} {link['polarity']} {link['to']}")

    assert result["loop_type"] is not None, "Should detect loop type"
    assert len(result["causal_links"]) > 0, "Should have causal links"
    print()


def test_floor_4_bias_detection():
    """Test enhanced bias detection."""
    floor = Floor4Metacognition()

    result = floor.detect_bias(
        agent_id="test_agent",
        decision="We should adopt technology X immediately",
        evidence=["X is new", "X is the latest", "X was released recently"],
        context="We've already invested months researching X",
    )

    print("✅ Floor 4 - Bias Detection Test:")
    print(f"   Detected {result['bias_count']} biases")
    for bias in result["detected_biases"]:
        print(f"   - {bias['bias']}: confidence={bias['confidence']}")
        print(f"     Reason: {bias['reason']}")
        print(f"     Fix: {bias['recommendation']}")

    assert result["bias_count"] > 0, "Should detect biases"
    # Should detect recency bias (all evidence is recent)
    assert any(
        b["bias"] == "Recency" for b in result["detected_biases"]
    ), "Should detect recency bias"
    # Should detect sunk cost (context mentions investment)
    assert any(
        b["bias"] == "Sunk Cost" for b in result["detected_biases"]
    ), "Should detect sunk cost"
    print()


if __name__ == "__main__":
    print("=== Temple Floor Enhancement Verification ===\n")

    try:
        test_floor_2_pattern_recognition()
        test_floor_3_feedback_loop()
        test_floor_4_bias_detection()

        print("=" * 50)
        print("✅ ALL TEMPLE FLOOR TESTS PASSED")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
