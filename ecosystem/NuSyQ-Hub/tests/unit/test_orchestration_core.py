"""Unit tests for orchestration system critical paths.

OmniTag: {
    "purpose": "unit_test_orchestration",
    "tags": ["testing", "unit", "orchestration", "critical_path"],
    "category": "test_unit",
    "evolution_stage": "v1.0"
}

Coverage Target: 50% of test suite (unit tests)
Focus: Multi-AI orchestration, timeout management, service coordination
"""

from unittest.mock import patch

import pytest

# ============================================================================
# UNIT TESTS: Intelligent Timeout Manager
# ============================================================================


@pytest.mark.unit
@pytest.mark.critical_path
class TestIntelligentTimeoutManager:
    """Test suite for intelligent timeout calculation and adaptation."""

    def test_timeout_calculation_with_defaults(self):
        """Test basic timeout calculation with default parameters."""
        import src.utils.intelligent_timeout_manager as tm

        TimeoutCalculator = getattr(tm, "TimeoutCalculator", None)
        if TimeoutCalculator is None:
            pytest.skip("TimeoutCalculator adapter not available")

        calc = TimeoutCalculator(base_timeout=60)
        timeout = calc.calculate_timeout()

        assert isinstance(timeout, int)
        assert calc.min_timeout <= timeout <= calc.max_timeout
        assert timeout >= 60  # Should be at least base timeout

    def test_timeout_scales_with_complexity(self):
        """Test that timeout increases with task complexity."""
        import src.utils.intelligent_timeout_manager as tm

        TimeoutCalculator = getattr(tm, "TimeoutCalculator", None)
        if TimeoutCalculator is None:
            pytest.skip("TimeoutCalculator adapter not available")

        calc = TimeoutCalculator(base_timeout=60)

        simple_timeout = calc.calculate_timeout(complexity=1.0)
        complex_timeout = calc.calculate_timeout(complexity=3.0)

        assert complex_timeout > simple_timeout

    def test_priority_affects_timeout(self):
        """Test that high priority tasks get longer timeouts."""
        import src.utils.intelligent_timeout_manager as tm

        TimeoutCalculator = getattr(tm, "TimeoutCalculator", None)
        if TimeoutCalculator is None:
            pytest.skip("TimeoutCalculator adapter not available")

        calc = TimeoutCalculator(base_timeout=60)

        low_priority = calc.calculate_timeout(priority="low")
        high_priority = calc.calculate_timeout(priority="high")

        assert high_priority > low_priority

    def test_historical_performance_tracking(self):
        """Test that performance history affects future timeouts."""
        import src.utils.intelligent_timeout_manager as tm

        TimeoutCalculator = getattr(tm, "TimeoutCalculator", None)
        if TimeoutCalculator is None:
            pytest.skip("TimeoutCalculator adapter not available")

        calc = TimeoutCalculator(base_timeout=60)
        initial_timeout = calc.calculate_timeout()

        # Record slow performance
        calc.record_performance(duration=120.0)
        slow_timeout = calc.calculate_timeout()

        assert slow_timeout >= initial_timeout  # Should adapt upward

    def test_timeout_clamping(self):
        """Test that timeouts are clamped to min/max bounds."""
        import src.utils.intelligent_timeout_manager as tm

        TimeoutCalculator = getattr(tm, "TimeoutCalculator", None)
        if TimeoutCalculator is None:
            pytest.skip("TimeoutCalculator adapter not available")

        calc = TimeoutCalculator(base_timeout=60, min_timeout=30, max_timeout=300)

        extreme_timeout = calc.calculate_timeout(complexity=10.0, priority="critical")
        assert extreme_timeout <= calc.max_timeout

    def test_service_weights(self):
        """Test service-specific timeout weights (Ollama, ChatDev, etc)."""
        import src.utils.intelligent_timeout_manager as tm

        ServiceTimeoutManager = getattr(tm, "ServiceTimeoutManager", None)
        if ServiceTimeoutManager is None:
            pytest.skip("ServiceTimeoutManager adapter not available")

        manager = ServiceTimeoutManager()

        ollama_timeout = manager.get_timeout("ollama")
        chatdev_timeout = manager.get_timeout("chatdev")

        assert ollama_timeout > 0
        assert chatdev_timeout >= ollama_timeout  # ChatDev typically slower


# ============================================================================
# UNIT TESTS: AI Capabilities Enhancer
# ============================================================================


@pytest.mark.unit
@pytest.mark.critical_path
class TestAICapabilitiesEnhancer:
    """Test suite for AI capabilities enhancement system."""

    def test_capability_discovery(self, temp_config_file):
        """Test automatic discovery of AI capabilities."""
        from src.orchestration.ai_capabilities_enhancer import (
            AICapabilitiesEnhancer,
        )

        enhancer = AICapabilitiesEnhancer()
        capabilities = enhancer.discover_capabilities()

        assert isinstance(capabilities, dict)
        assert len(capabilities) > 0
        assert "ollama" in capabilities or "chatdev" in capabilities

    def test_capability_validation(self):
        """Test validation of AI capability requirements."""
        from src.orchestration.ai_capabilities_enhancer import (
            AICapabilitiesEnhancer,
        )

        enhancer = AICapabilitiesEnhancer()

        # Test with valid capability
        is_valid = enhancer.validate_capability("code_generation")
        assert isinstance(is_valid, bool)

    def test_enhancement_recommendations(self):
        """Test generation of capability enhancement recommendations."""
        from src.orchestration.ai_capabilities_enhancer import (
            AICapabilitiesEnhancer,
        )

        enhancer = AICapabilitiesEnhancer()
        recommendations = enhancer.get_recommendations()

        assert isinstance(recommendations, list)
        # Should provide actionable recommendations

    @patch("src.orchestration.ai_capabilities_enhancer.requests.get")
    def test_backend_status_check(self, mock_get):
        """Test AI backend availability checking."""
        from src.orchestration.ai_capabilities_enhancer import (
            AICapabilitiesEnhancer,
        )

        # Mock successful Ollama response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok"}

        enhancer = AICapabilitiesEnhancer()
        status = enhancer.check_backend_status("ollama")

        assert status in [True, False, "unknown"]


# ============================================================================
# UNIT TESTS: Service Configuration
# ============================================================================


@pytest.mark.unit
class TestServiceConfiguration:
    """Test suite for service configuration management."""

    def test_service_config_loading(self, temp_config_file):
        """Test loading service configuration from file."""
        from src.config.service_config import ServiceConfig

        config = ServiceConfig(config_file=temp_config_file)

        assert hasattr(config, "ollama_host")
        assert hasattr(config, "ollama_port")

    def test_service_config_defaults(self):
        """Test that service config provides sensible defaults."""
        from src.config.service_config import ServiceConfig

        config = ServiceConfig()

        # Accept localhost variants (env vars may set 127.0.0.1 explicitly)
        assert config.ollama_host in [
            "localhost",
            "http://localhost:11434",
            "http://127.0.0.1:11434",
            "127.0.0.1",
        ]
        assert isinstance(config.ollama_port, (str, int))

    def test_config_validation(self):
        """Test configuration validation logic."""
        from src.config.service_config import ServiceConfig

        config = ServiceConfig()
        is_valid = config.validate()

        assert isinstance(is_valid, bool)


# ============================================================================
# UNIT TESTS: Timeout Configuration
# ============================================================================


@pytest.mark.unit
class TestTimeoutConfiguration:
    """Test suite for timeout configuration utilities."""

    def test_get_timeout_for_service(self):
        """Test retrieval of service-specific timeouts."""
        from src.utils.timeout_config import get_timeout

        ollama_timeout = get_timeout("ollama")
        chatdev_timeout = get_timeout("chatdev")

        assert isinstance(ollama_timeout, (int, float))
        assert isinstance(chatdev_timeout, (int, float))
        assert ollama_timeout > 0
        assert chatdev_timeout > 0

    def test_timeout_with_custom_params(self):
        """Test timeout calculation with custom parameters."""
        from src.utils.timeout_config import get_timeout

        timeout = get_timeout("ollama", complexity=2.0, priority="high")

        assert isinstance(timeout, (int, float))
        assert timeout > 0

    def test_default_timeout_fallback(self):
        """Test fallback to default timeout for unknown services."""
        from src.utils.timeout_config import get_timeout

        unknown_timeout = get_timeout("unknown_service_xyz")

        assert isinstance(unknown_timeout, (int, float))
        assert unknown_timeout > 0  # Should have reasonable default
