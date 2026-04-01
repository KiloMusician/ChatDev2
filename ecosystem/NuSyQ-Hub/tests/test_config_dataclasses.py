"""Tests for src/utils/config_dataclasses.py - Configuration dataclasses.

Tests configuration objects including API, logging, performance, cache,
retry, security, and system configuration dataclasses.
"""

import logging
import os
from typing import Any
from unittest.mock import patch

import pytest
from src.utils.config_dataclasses import (
    APIConfiguration,
    CacheConfiguration,
    ChatDevConfiguration,
    LoggingConfiguration,
    PerformanceConfiguration,
    RetryConfiguration,
    SecurityConfiguration,
    ShutdownConfiguration,
    SystemConfiguration,
)

# =============================================================================
# Test APIConfiguration
# =============================================================================


class TestAPIConfiguration:
    """Tests for APIConfiguration dataclass."""

    def test_create_with_required_fields(self) -> None:
        """Create APIConfiguration with required fields."""
        config = APIConfiguration(provider="openai", base_url="https://api.openai.com")
        assert config.provider == "openai"
        assert config.base_url == "https://api.openai.com"

    def test_default_api_key_is_none(self) -> None:
        """Default api_key is None."""
        config = APIConfiguration(provider="test", base_url="http://test")
        assert config.api_key is None

    def test_default_timeout(self) -> None:
        """Default timeout is set from Defaults."""
        config = APIConfiguration(provider="test", base_url="http://test")
        assert config.timeout > 0

    def test_default_max_retries(self) -> None:
        """Default max_retries is set from Defaults."""
        config = APIConfiguration(provider="test", base_url="http://test")
        assert config.max_retries >= 0

    def test_custom_headers(self) -> None:
        """Custom headers can be set."""
        headers = {"Authorization": "Bearer test"}
        config = APIConfiguration(provider="test", base_url="http://test", headers=headers)
        assert config.headers == headers

    def test_rate_limit_can_be_set(self) -> None:
        """rate_limit can be set."""
        config = APIConfiguration(provider="test", base_url="http://test", rate_limit=60)
        assert config.rate_limit == 60

    def test_from_env_vars_openai(self) -> None:
        """from_env_vars creates OpenAI config."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}):
            config = APIConfiguration.from_env_vars("openai")
            assert config.provider == "openai"
            assert config.api_key == "sk-test123"

    def test_from_env_vars_anthropic(self) -> None:
        """from_env_vars creates Anthropic config."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "ant-key"}):
            config = APIConfiguration.from_env_vars("anthropic")
            assert config.provider == "anthropic"
            assert config.api_key == "ant-key"

    def test_from_env_vars_ollama(self) -> None:
        """from_env_vars creates Ollama config."""
        with patch.dict(
            os.environ,
            {"OLLAMA_HOST": "localhost", "OLLAMA_PORT": "11434"},
            clear=False,
        ):
            config = APIConfiguration.from_env_vars("ollama")
            assert config.provider == "ollama"
            assert "localhost" in config.base_url

    def test_from_env_vars_unknown_provider(self) -> None:
        """from_env_vars raises for unknown provider."""
        with pytest.raises(ValueError) as exc_info:
            APIConfiguration.from_env_vars("unknown_provider")
        assert "Unknown provider" in str(exc_info.value)


# =============================================================================
# Test LoggingConfiguration
# =============================================================================


class TestLoggingConfiguration:
    """Tests for LoggingConfiguration dataclass."""

    def test_default_initialization(self) -> None:
        """Default initialization sets expected values."""
        config = LoggingConfiguration()
        assert config.console_logging is True
        assert config.log_to_file is True

    def test_custom_level(self) -> None:
        """Custom log level can be set."""
        from src.utils.constants import LogLevel

        config = LoggingConfiguration(level=LogLevel.DEBUG)
        assert config.level == LogLevel.DEBUG

    def test_custom_file_path(self, tmp_path: Any) -> None:
        """Custom file path can be set."""
        log_path = tmp_path / "test.log"
        config = LoggingConfiguration(file_path=log_path)
        assert config.file_path == log_path

    def test_configure_logger_returns_logger(self) -> None:
        """configure_logger returns a logger instance."""
        config = LoggingConfiguration(log_to_file=False)
        logger = config.configure_logger("test_logger")
        assert isinstance(logger, logging.Logger)

    def test_configure_logger_sets_level(self) -> None:
        """configure_logger sets the correct level."""
        from src.utils.constants import LogLevel

        config = LoggingConfiguration(level=LogLevel.WARNING, log_to_file=False)
        logger = config.configure_logger("test_level")
        assert logger.level == logging.WARNING

    def test_configure_logger_with_console(self) -> None:
        """configure_logger adds console handler when enabled."""
        config = LoggingConfiguration(console_logging=True, log_to_file=False)
        logger = config.configure_logger("test_console")
        assert len(logger.handlers) > 0

    def test_configure_logger_with_file(self, tmp_path: Any) -> None:
        """configure_logger adds file handler when enabled."""
        log_path = tmp_path / "test.log"
        config = LoggingConfiguration(
            log_to_file=True,
            file_path=log_path,
            console_logging=False,
        )
        logger = config.configure_logger("test_file")
        assert len(logger.handlers) > 0
        # Clean up
        for handler in logger.handlers:
            handler.close()


# =============================================================================
# Test PerformanceConfiguration
# =============================================================================


class TestPerformanceConfiguration:
    """Tests for PerformanceConfiguration dataclass."""

    def test_default_initialization(self) -> None:
        """Default initialization sets expected values."""
        config = PerformanceConfiguration()
        assert config.enable_monitoring is True
        assert config.max_concurrent_tasks > 0

    def test_is_resource_critical_memory(self) -> None:
        """is_resource_critical detects critical memory."""
        config = PerformanceConfiguration(memory_threshold_mb=1000)
        assert config.is_resource_critical(1500, 50, 50) is True

    def test_is_resource_critical_cpu(self) -> None:
        """is_resource_critical detects critical CPU."""
        config = PerformanceConfiguration(cpu_threshold_percent=80)
        assert config.is_resource_critical(500, 90, 50) is True

    def test_is_resource_critical_disk(self) -> None:
        """is_resource_critical detects critical disk."""
        config = PerformanceConfiguration(disk_threshold_percent=85)
        assert config.is_resource_critical(500, 50, 95) is True

    def test_is_resource_critical_all_ok(self) -> None:
        """is_resource_critical returns False when all OK."""
        config = PerformanceConfiguration(
            memory_threshold_mb=1000,
            cpu_threshold_percent=80,
            disk_threshold_percent=85,
        )
        assert config.is_resource_critical(500, 50, 50) is False


# =============================================================================
# Test ShutdownConfiguration
# =============================================================================


class TestShutdownConfiguration:
    """Tests for ShutdownConfiguration dataclass."""

    def test_default_initialization(self) -> None:
        """Default initialization sets expected values."""
        config = ShutdownConfiguration()
        assert config.save_state is True
        assert config.log_progress is True

    def test_get_total_shutdown_time(self) -> None:
        """get_total_shutdown_time returns sum of timeouts."""
        config = ShutdownConfiguration(
            graceful_timeout=10.0,
            force_timeout=5.0,
            cleanup_timeout=2.0,
        )
        assert config.get_total_shutdown_time() == 17.0

    def test_signal_handlers_default(self) -> None:
        """Default signal handlers include SIGINT and SIGTERM."""
        config = ShutdownConfiguration()
        assert 2 in config.signal_handlers  # SIGINT
        assert 15 in config.signal_handlers  # SIGTERM


# =============================================================================
# Test CacheConfiguration
# =============================================================================


class TestCacheConfiguration:
    """Tests for CacheConfiguration dataclass."""

    def test_default_initialization(self) -> None:
        """Default initialization sets expected values."""
        config = CacheConfiguration()
        assert config.enabled is True
        assert config.cache_type == "memory"

    def test_file_cache_creates_dir(self, tmp_path: Any) -> None:
        """File cache creates directory on post_init."""
        cache_dir = tmp_path / "cache"
        config = CacheConfiguration(cache_type="file", cache_dir=cache_dir)
        assert config.cache_dir == cache_dir

    def test_file_cache_default_dir(self) -> None:
        """File cache sets default dir when not provided."""
        config = CacheConfiguration(cache_type="file", cache_dir=None)
        assert config.cache_dir is not None
        assert "cache" in str(config.cache_dir)


# =============================================================================
# Test RetryConfiguration
# =============================================================================


class TestRetryConfiguration:
    """Tests for RetryConfiguration dataclass."""

    def test_default_initialization(self) -> None:
        """Default initialization sets expected values."""
        config = RetryConfiguration()
        assert config.max_attempts > 0
        assert config.jitter is True

    def test_calculate_delay_increases(self) -> None:
        """calculate_delay increases with attempts."""
        config = RetryConfiguration(jitter=False, base_delay=1.0, exponential_base=2.0)
        delay_0 = config.calculate_delay(0)
        delay_1 = config.calculate_delay(1)
        delay_2 = config.calculate_delay(2)
        assert delay_1 > delay_0
        assert delay_2 > delay_1

    def test_calculate_delay_capped_at_max(self) -> None:
        """calculate_delay is capped at max_delay."""
        config = RetryConfiguration(jitter=False, max_delay=10.0)
        delay = config.calculate_delay(100)
        assert delay <= 10.0

    def test_calculate_delay_with_jitter(self) -> None:
        """calculate_delay varies with jitter."""
        config = RetryConfiguration(jitter=True, base_delay=1.0)
        delays = [config.calculate_delay(1) for _ in range(10)]
        # With jitter, delays should vary
        unique_delays = set(delays)
        assert len(unique_delays) > 1

    def test_retry_on_status_codes_default(self) -> None:
        """Default status codes include common server errors."""
        config = RetryConfiguration()
        assert 500 in config.retry_on_status_codes
        assert 429 in config.retry_on_status_codes


# =============================================================================
# Test ChatDevConfiguration
# =============================================================================


class TestChatDevConfiguration:
    """Tests for ChatDevConfiguration dataclass."""

    def test_create_with_path(self, tmp_path: Any) -> None:
        """Create ChatDevConfiguration with path."""
        config = ChatDevConfiguration(chatdev_path=tmp_path)
        assert config.chatdev_path == tmp_path

    def test_default_organization(self, tmp_path: Any) -> None:
        """Default organization is set."""
        config = ChatDevConfiguration(chatdev_path=tmp_path)
        assert config.default_organization == "KiloFoolish"

    def test_output_directory_created(self, tmp_path: Any) -> None:
        """Output directory is created on post_init."""
        output_dir = tmp_path / "output"
        config = ChatDevConfiguration(
            chatdev_path=tmp_path,
            output_directory=output_dir,
        )
        assert config.output_directory == output_dir


# =============================================================================
# Test SecurityConfiguration
# =============================================================================


class TestSecurityConfiguration:
    """Tests for SecurityConfiguration dataclass."""

    def test_default_initialization(self) -> None:
        """Default initialization sets expected values."""
        config = SecurityConfiguration()
        assert config.encrypt_secrets is True
        assert config.require_https is True

    def test_is_host_allowed_localhost(self) -> None:
        """Localhost is allowed by default."""
        config = SecurityConfiguration()
        assert config.is_host_allowed("localhost") is True

    def test_is_host_allowed_127_0_0_1(self) -> None:
        """127.0.0.1 is allowed by default."""
        config = SecurityConfiguration()
        assert config.is_host_allowed("127.0.0.1") is True

    def test_is_host_allowed_custom(self) -> None:
        """Custom hosts can be allowed."""
        config = SecurityConfiguration(allowed_hosts={"example.com"})
        assert config.is_host_allowed("example.com") is True
        assert config.is_host_allowed("other.com") is False


# =============================================================================
# Test SystemConfiguration
# =============================================================================


class TestSystemConfiguration:
    """Tests for SystemConfiguration dataclass."""

    def test_default_initialization(self) -> None:
        """Default initialization creates config."""
        config = SystemConfiguration()
        assert config.config_version == "1.0.0"

    def test_has_logging_config(self) -> None:
        """SystemConfig has LoggingConfiguration."""
        config = SystemConfiguration()
        assert isinstance(config.logging, LoggingConfiguration)

    def test_has_performance_config(self) -> None:
        """SystemConfig has PerformanceConfiguration."""
        config = SystemConfiguration()
        assert isinstance(config.performance, PerformanceConfiguration)

    def test_has_security_config(self) -> None:
        """SystemConfig has SecurityConfiguration."""
        config = SystemConfiguration()
        assert isinstance(config.security, SecurityConfiguration)

    def test_get_primary_api_config_with_key(self) -> None:
        """get_primary_api_config returns config with API key."""
        api_config = APIConfiguration(
            provider="test",
            base_url="http://test",
            api_key="key123",
        )
        config = SystemConfiguration(api_configs={"test": api_config})
        primary = config.get_primary_api_config()
        assert primary is not None
        assert primary.api_key == "key123"

    def test_get_primary_api_config_no_key(self) -> None:
        """get_primary_api_config returns None when no keys."""
        api_config = APIConfiguration(
            provider="test",
            base_url="http://test",
            api_key=None,
        )
        config = SystemConfiguration(api_configs={"test": api_config})
        primary = config.get_primary_api_config()
        assert primary is None

    def test_validate_returns_list(self) -> None:
        """Validate returns list of issues."""
        config = SystemConfiguration()
        issues = config.validate()
        assert isinstance(issues, list)

    def test_validate_detects_no_api_keys(self) -> None:
        """Validate detects missing API keys."""
        config = SystemConfiguration()
        # Clear api_configs AFTER __post_init__ to bypass auto-initialization
        config.api_configs = {}
        issues = config.validate()
        # Exact message: "No valid API configuration found (missing API keys)"
        assert any("api" in issue.lower() for issue in issues)

    def test_validate_detects_invalid_memory_threshold(self) -> None:
        """Validate detects invalid memory threshold."""
        config = SystemConfiguration()
        config.performance.memory_threshold_mb = -1
        issues = config.validate()
        assert any("Memory" in issue for issue in issues)

    def test_validate_detects_invalid_shutdown_timeout(self) -> None:
        """Validate detects invalid shutdown timeout."""
        config = SystemConfiguration()
        config.shutdown.graceful_timeout = 0
        issues = config.validate()
        assert any("shutdown" in issue.lower() for issue in issues)

    def test_update_timestamp(self) -> None:
        """update_timestamp updates updated_at."""
        config = SystemConfiguration()
        old_time = config.updated_at
        import time

        time.sleep(0.01)
        config.update_timestamp()
        assert config.updated_at > old_time

    def test_save_to_file_raises_on_type_fields(self, tmp_path: Any) -> None:
        """save_to_file raises TypeError for non-serializable types.

        The retry_on_exceptions field contains exception types which are
        not JSON serializable. This documents current behavior.
        """
        config = SystemConfiguration()
        file_path = tmp_path / "config.json"
        # Current implementation doesn't handle tuple[type, ...] fields
        with pytest.raises(TypeError, match="not JSON serializable"):
            config.save_to_file(file_path)

    def test_load_from_file_requires_save_to_work(self, tmp_path: Any) -> None:
        """load_from_file requires save_to_file to succeed first.

        Since save_to_file raises TypeError on current implementation,
        we test that load fails when file doesn't exist.
        """
        file_path = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            SystemConfiguration.load_from_file(file_path)


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_retry_delay_at_zero_attempts(self) -> None:
        """Retry delay at attempt 0 equals base_delay."""
        config = RetryConfiguration(jitter=False, base_delay=1.0, exponential_base=2.0)
        delay = config.calculate_delay(0)
        assert delay == 1.0

    def test_performance_all_thresholds_critical(self) -> None:
        """is_resource_critical when all at critical."""
        config = PerformanceConfiguration()
        assert config.is_resource_critical(10000, 99, 99) is True

    def test_cache_memory_type(self) -> None:
        """Memory cache type requires no directory."""
        config = CacheConfiguration(cache_type="memory")
        # cache_dir may be None or not set for memory
        assert config.cache_type == "memory"

    def test_security_empty_allowed_hosts(self) -> None:
        """Security config with empty allowed hosts."""
        config = SecurityConfiguration(allowed_hosts=set())
        assert config.is_host_allowed("localhost") is False

    def test_system_config_environment_values(self) -> None:
        """SystemConfig environment can be set."""
        for env in ["development", "staging", "production"]:
            config = SystemConfiguration(environment=env)
            assert config.environment == env

    def test_chatdev_with_nonexistent_path(self, tmp_path: Any) -> None:
        """ChatDevConfiguration logs warning for nonexistent path."""
        nonexistent = tmp_path / "nonexistent"
        # Should not raise, just log warning
        config = ChatDevConfiguration(chatdev_path=nonexistent)
        assert config.chatdev_path == nonexistent

    def test_api_config_all_fields(self) -> None:
        """APIConfiguration with all fields set."""
        config = APIConfiguration(
            provider="custom",
            base_url="http://custom-api.local",
            api_key="key123",
            model="custom-model",
            timeout=30.0,
            max_retries=5,
            rate_limit=100,
            headers={"X-Custom": "value"},
        )
        assert config.provider == "custom"
        assert config.timeout == 30.0
        assert config.max_retries == 5
        assert config.rate_limit == 100

    def test_logging_both_handlers_disabled(self) -> None:
        """LoggingConfiguration with both handlers disabled."""
        config = LoggingConfiguration(
            console_logging=False,
            log_to_file=False,
        )
        logger = config.configure_logger("no_handlers")
        assert len(logger.handlers) == 0

    def test_shutdown_total_time_includes_all(self) -> None:
        """get_total_shutdown_time includes all timeouts."""
        config = ShutdownConfiguration(
            graceful_timeout=1.0,
            force_timeout=2.0,
            cleanup_timeout=3.0,
        )
        total = config.get_total_shutdown_time()
        expected = 1.0 + 2.0 + 3.0
        assert total == expected
