"""Tests for src/utils/settings.py — _ensure_scheme, DEFAULT_SETTINGS, load_settings."""

import json


class TestEnsureScheme:
    """Tests for _ensure_scheme helper."""

    def test_plain_url_gets_http_prefix(self):
        from src.utils.settings import _ensure_scheme
        result = _ensure_scheme("localhost:11434")
        assert result.startswith("http://")

    def test_http_url_unchanged(self):
        from src.utils.settings import _ensure_scheme
        url = "http://127.0.0.1:11434"
        assert _ensure_scheme(url) == url

    def test_https_url_unchanged(self):
        from src.utils.settings import _ensure_scheme
        url = "https://example.com/api"
        assert _ensure_scheme(url) == url

    def test_hostname_only_gets_prefix(self):
        from src.utils.settings import _ensure_scheme
        result = _ensure_scheme("myhost")
        assert result == "http://myhost"


class TestDefaultOllamaUrl:
    """Tests for _default_ollama_url with env overrides."""

    def test_returns_string(self):
        from src.utils.settings import _default_ollama_url
        url = _default_ollama_url()
        assert isinstance(url, str)
        assert len(url) > 0

    def test_respects_ollama_base_url_env(self, monkeypatch):
        from src.utils.settings import _default_ollama_url
        monkeypatch.setattr("src.utils.settings.SERVICE_CONFIG_AVAILABLE", False)
        monkeypatch.setattr("src.utils.settings.ServiceConfig", None)
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.1.100:11434")
        result = _default_ollama_url()
        assert "192.168.1.100" in result

    def test_base_url_strips_trailing_slash(self, monkeypatch):
        from src.utils.settings import _default_ollama_url
        monkeypatch.setattr("src.utils.settings.SERVICE_CONFIG_AVAILABLE", False)
        monkeypatch.setattr("src.utils.settings.ServiceConfig", None)
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://myhost:11434/")
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        monkeypatch.delenv("OLLAMA_PORT", raising=False)
        result = _default_ollama_url()
        assert not result.endswith("/")

    def test_fallback_uses_host_and_port_env(self, monkeypatch):
        from src.utils.settings import _default_ollama_url
        monkeypatch.setattr("src.utils.settings.SERVICE_CONFIG_AVAILABLE", False)
        monkeypatch.setattr("src.utils.settings.ServiceConfig", None)
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        monkeypatch.setenv("OLLAMA_HOST", "http://10.0.0.1")
        monkeypatch.setenv("OLLAMA_PORT", "9999")
        result = _default_ollama_url()
        assert "10.0.0.1" in result


class TestDefaultSettings:
    """Tests for DEFAULT_SETTINGS dict structure."""

    def test_is_dict(self):
        from src.utils.settings import DEFAULT_SETTINGS
        assert isinstance(DEFAULT_SETTINGS, dict)

    def test_has_chatdev_key(self):
        from src.utils.settings import DEFAULT_SETTINGS
        assert "chatdev" in DEFAULT_SETTINGS

    def test_has_ollama_key(self):
        from src.utils.settings import DEFAULT_SETTINGS
        assert "ollama" in DEFAULT_SETTINGS
        assert "host" in DEFAULT_SETTINGS["ollama"]

    def test_has_timeouts(self):
        from src.utils.settings import DEFAULT_SETTINGS
        timeouts = DEFAULT_SETTINGS["timeouts"]
        assert "default" in timeouts
        assert "long" in timeouts
        assert timeouts["default"] > 0
        assert timeouts["long"] > timeouts["default"]

    def test_has_feature_flags(self):
        from src.utils.settings import DEFAULT_SETTINGS
        flags = DEFAULT_SETTINGS["feature_flags"]
        assert "enable_chatdev" in flags
        assert "enable_ollama" in flags
        assert isinstance(flags["enable_chatdev"], bool)
        assert isinstance(flags["enable_ollama"], bool)

    def test_context_server_has_port(self):
        from src.utils.settings import DEFAULT_SETTINGS
        cs = DEFAULT_SETTINGS["context_server"]
        assert "port" in cs
        assert isinstance(cs["port"], int)


class TestLoadSettings:
    """Tests for load_settings() function."""

    def test_returns_dict(self, tmp_path):
        from src.utils.settings import load_settings
        result = load_settings(str(tmp_path / "nonexistent.json"))
        assert isinstance(result, dict)

    def test_missing_file_returns_defaults(self, tmp_path):
        from src.utils.settings import DEFAULT_SETTINGS, load_settings
        result = load_settings(str(tmp_path / "missing.json"))
        # Should have all default top-level keys
        for key in DEFAULT_SETTINGS:
            assert key in result

    def test_loads_from_file(self, tmp_path):
        from src.utils.settings import load_settings
        config_file = tmp_path / "settings.json"
        config_file.write_text(json.dumps({"chatdev": {"path": "/custom/path"}}), encoding="utf-8")
        result = load_settings(str(config_file))
        assert result["chatdev"]["path"] == "/custom/path"

    def test_merges_with_defaults(self, tmp_path):
        from src.utils.settings import load_settings
        config_file = tmp_path / "settings.json"
        config_file.write_text(json.dumps({"chatdev": {"path": "/x"}}), encoding="utf-8")
        result = load_settings(str(config_file))
        # Other defaults still present
        assert "ollama" in result
        assert "timeouts" in result

    def test_invalid_json_falls_back_to_defaults(self, tmp_path):
        from src.utils.settings import DEFAULT_SETTINGS, load_settings
        config_file = tmp_path / "bad.json"
        config_file.write_text("not valid json {{{", encoding="utf-8")
        result = load_settings(str(config_file))
        for key in DEFAULT_SETTINGS:
            assert key in result

    def test_extra_keys_in_file_preserved(self, tmp_path):
        from src.utils.settings import load_settings
        config_file = tmp_path / "extra.json"
        config_file.write_text(json.dumps({"custom_key": "custom_val"}), encoding="utf-8")
        result = load_settings(str(config_file))
        assert result.get("custom_key") == "custom_val"

    def test_nested_partial_override(self, tmp_path):
        from src.utils.settings import load_settings
        config_file = tmp_path / "partial.json"
        config_file.write_text(
            json.dumps({"feature_flags": {"experimental_mode": True}}), encoding="utf-8"
        )
        result = load_settings(str(config_file))
        # Override applied
        assert result["feature_flags"]["experimental_mode"] is True
        # Defaults preserved
        assert "enable_chatdev" in result["feature_flags"]
