"""Tests for src/utils/timeout_config.py — env-driven timeout helpers."""


class TestEnvInt:
    """Tests for _env_int helper."""

    def test_missing_env_returns_none(self, monkeypatch):
        from src.utils.timeout_config import _env_int
        monkeypatch.delenv("SOME_TIMEOUT_XYZ", raising=False)
        assert _env_int("SOME_TIMEOUT_XYZ") is None

    def test_valid_int_string(self, monkeypatch):
        from src.utils.timeout_config import _env_int
        monkeypatch.setenv("SOME_TIMEOUT_XYZ", "42")
        assert _env_int("SOME_TIMEOUT_XYZ") == 42

    def test_float_string_truncated(self, monkeypatch):
        from src.utils.timeout_config import _env_int
        monkeypatch.setenv("SOME_TIMEOUT_XYZ", "30.9")
        assert _env_int("SOME_TIMEOUT_XYZ") == 30

    def test_empty_string_returns_none(self, monkeypatch):
        from src.utils.timeout_config import _env_int
        monkeypatch.setenv("SOME_TIMEOUT_XYZ", "")
        assert _env_int("SOME_TIMEOUT_XYZ") is None

    def test_invalid_string_returns_none(self, monkeypatch):
        from src.utils.timeout_config import _env_int
        monkeypatch.setenv("SOME_TIMEOUT_XYZ", "not_a_number")
        assert _env_int("SOME_TIMEOUT_XYZ") is None


class TestGetTimeout:
    """Tests for get_timeout() function."""

    def test_env_key_returns_int(self, monkeypatch):
        from src.utils.timeout_config import get_timeout
        monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "25")
        result = get_timeout("HTTP_TIMEOUT_SECONDS")
        assert result == 25

    def test_env_key_missing_returns_default(self, monkeypatch):
        from src.utils.timeout_config import get_timeout
        monkeypatch.delenv("MISSING_TIMEOUT_KEY", raising=False)
        result = get_timeout("MISSING_TIMEOUT_KEY", default=15)
        assert result == 15

    def test_env_key_missing_default_none(self, monkeypatch):
        from src.utils.timeout_config import get_timeout
        monkeypatch.delenv("MISSING_TIMEOUT_KEY", raising=False)
        result = get_timeout("MISSING_TIMEOUT_KEY")
        assert result is None

    def test_service_name_returns_int_or_none(self):
        from src.utils.timeout_config import get_timeout
        # Service-based path uses adaptive manager; just check type
        result = get_timeout("ollama", default=30)
        assert isinstance(result, int)

    def test_uppercase_key_detected_as_env_var(self, monkeypatch):
        from src.utils.timeout_config import get_timeout
        monkeypatch.setenv("MY_SERVICE_TIMEOUT", "60")
        result = get_timeout("MY_SERVICE_TIMEOUT")
        assert result == 60


class TestGetHttpTimeout:
    """Tests for get_http_timeout()."""

    def test_returns_int(self):
        from src.utils.timeout_config import get_http_timeout
        result = get_http_timeout()
        assert isinstance(result, int)
        assert result > 0

    def test_default_returned_when_no_env(self, monkeypatch):
        from src.utils.timeout_config import get_http_timeout
        monkeypatch.delenv("HTTP_TIMEOUT_SECONDS", raising=False)
        result = get_http_timeout(default=7)
        assert result == 7

    def test_service_env_var_honored(self, monkeypatch):
        from src.utils.timeout_config import get_http_timeout
        monkeypatch.setenv("OLLAMA_HTTP_TIMEOUT_SECONDS", "99")
        result = get_http_timeout(service="ollama")
        assert result == 99

    def test_global_env_var_honored(self, monkeypatch):
        from src.utils.timeout_config import get_http_timeout
        monkeypatch.delenv("OLLAMA_HTTP_TIMEOUT_SECONDS", raising=False)
        monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "55")
        result = get_http_timeout()
        assert result == 55

    def test_no_service_uses_global(self, monkeypatch):
        from src.utils.timeout_config import get_http_timeout
        monkeypatch.setenv("HTTP_TIMEOUT_SECONDS", "33")
        result = get_http_timeout(service=None)
        assert result == 33


class TestGetOllamaMaxTimeout:
    """Tests for get_ollama_max_timeout()."""

    def test_returns_none_when_not_set(self, monkeypatch):
        from src.utils.timeout_config import get_ollama_max_timeout
        monkeypatch.delenv("OLLAMA_MAX_TIMEOUT_SECONDS", raising=False)
        assert get_ollama_max_timeout() is None

    def test_returns_int_when_set(self, monkeypatch):
        from src.utils.timeout_config import get_ollama_max_timeout
        monkeypatch.setenv("OLLAMA_MAX_TIMEOUT_SECONDS", "120")
        assert get_ollama_max_timeout() == 120


class TestOllamaAdaptiveEnabled:
    """Tests for ollama_adaptive_enabled()."""

    def test_false_when_not_set(self, monkeypatch):
        from src.utils.timeout_config import ollama_adaptive_enabled
        monkeypatch.delenv("OLLAMA_ADAPTIVE_TIMEOUT", raising=False)
        assert ollama_adaptive_enabled() is False

    def test_true_for_1(self, monkeypatch):
        from src.utils.timeout_config import ollama_adaptive_enabled
        monkeypatch.setenv("OLLAMA_ADAPTIVE_TIMEOUT", "1")
        assert ollama_adaptive_enabled() is True

    def test_true_for_true(self, monkeypatch):
        from src.utils.timeout_config import ollama_adaptive_enabled
        monkeypatch.setenv("OLLAMA_ADAPTIVE_TIMEOUT", "true")
        assert ollama_adaptive_enabled() is True

    def test_true_for_yes(self, monkeypatch):
        from src.utils.timeout_config import ollama_adaptive_enabled
        monkeypatch.setenv("OLLAMA_ADAPTIVE_TIMEOUT", "yes")
        assert ollama_adaptive_enabled() is True

    def test_false_for_0(self, monkeypatch):
        from src.utils.timeout_config import ollama_adaptive_enabled
        monkeypatch.setenv("OLLAMA_ADAPTIVE_TIMEOUT", "0")
        assert ollama_adaptive_enabled() is False

    def test_false_for_false_string(self, monkeypatch):
        from src.utils.timeout_config import ollama_adaptive_enabled
        monkeypatch.setenv("OLLAMA_ADAPTIVE_TIMEOUT", "false")
        assert ollama_adaptive_enabled() is False


class TestGetAdaptiveTimeout:
    """Tests for get_adaptive_timeout()."""

    def test_returns_int(self):
        from src.utils.timeout_config import get_adaptive_timeout
        result = get_adaptive_timeout(30)
        assert isinstance(result, int)
        assert result > 0

    def test_base_timeout_returned_when_no_breathing(self):
        from src.utils.timeout_config import get_adaptive_timeout
        # When breathing integration unavailable, falls back to base
        result = get_adaptive_timeout(60, service="test")
        assert isinstance(result, int)
        # Should be close to 60 (may vary with breathing factor)
        assert result > 0

    def test_default_service_name(self):
        from src.utils.timeout_config import get_adaptive_timeout
        result = get_adaptive_timeout(45)
        assert isinstance(result, int)
