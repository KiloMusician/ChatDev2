"""Tests for adaptive_timeout_manager.

Auto-generated smoke tests to establish basic coverage.
"""

from src.agents.adaptive_timeout_manager import (
    AdaptiveTimeoutManager,
)


def test_adaptivetimeoutmanager_instantiation():
    """Test that AdaptiveTimeoutManager can be instantiated."""
    instance = AdaptiveTimeoutManager()
    assert instance is not None


def test_adaptivetimeoutmanager_get_timeout():
    """Test AdaptiveTimeoutManager.get_timeout() method."""
    manager = AdaptiveTimeoutManager()

    # Test with small model
    timeout_3b = manager.get_timeout("phi3.5:3b", "code_generation", "simple")
    assert timeout_3b > 0
    assert timeout_3b == 30.0  # Default 3b model timeout

    # Test with large model
    timeout_14b = manager.get_timeout("qwen2.5-coder:14b", "code_generation", "simple")
    assert timeout_14b == 120.0  # Default 14b model timeout

    # Test complexity multiplier
    timeout_complex = manager.get_timeout("qwen2.5-coder:14b", "code_generation", "complex")
    assert timeout_complex == 120.0 * 2.0  # complex = 2x multiplier


def test_adaptivetimeoutmanager_record_attempt():
    """Test AdaptiveTimeoutManager.record_attempt() method."""
    manager = AdaptiveTimeoutManager()

    # Record a successful attempt
    manager.record_attempt(
        model="qwen2.5-coder:14b", task_type="code_generation", duration=75.0, success=True
    )

    # Check that metrics were recorded
    model_key = "qwen2.5-coder:14b:code_generation"
    assert model_key in manager.metrics["model_performance"]
    assert manager.metrics["model_performance"][model_key]["attempts"] >= 1
    assert manager.metrics["model_performance"][model_key]["successes"] >= 1


def test_get_timeout_manager():
    """Test get_timeout_manager() function."""
    from src.agents.adaptive_timeout_manager import get_timeout_manager

    # Get the global timeout manager instance
    manager = get_timeout_manager()
    assert manager is not None
    assert isinstance(manager, AdaptiveTimeoutManager)

    # Verify it's the same instance (singleton)
    manager2 = get_timeout_manager()
    assert manager is manager2
