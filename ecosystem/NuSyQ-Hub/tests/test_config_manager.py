"""Comprehensive tests for src/core/config_manager.py.

Tests ConfigManager class and global configuration functions for:
- Multi-source configuration loading
- Dotted key notation navigation
- Environment variable overrides with type casting
- Configuration validation and hot-reload
"""

import json
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.config_manager import (
    ConfigManager,
    get_context_server_config,
    get_global_config,
    get_ollama_config,
    get_system_config,
    get_zeta_config,
    set_global_config,
)


class TestConfigManagerInit:
    """Test ConfigManager initialization."""

    def test_init_without_config_path(self) -> None:
        """Initialize with no config path."""
        cm = ConfigManager()
        assert cm._config == {}
        assert cm._config_path is None
        assert cm._last_modified is None

    def test_init_with_valid_config_path(self, tmp_path: Path) -> None:
        """Initialize with valid config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"key": "value"}')

        cm = ConfigManager(config_file)
        assert cm._config == {"key": "value"}
        assert cm._config_path == config_file
        assert cm._last_modified is not None

    def test_init_with_nonexistent_path(self, tmp_path: Path) -> None:
        """Initialize with path that doesn't exist."""
        cm = ConfigManager(tmp_path / "missing.json")
        assert cm._config == {}


class TestConfigManagerLoadConfig:
    """Test load_config method."""

    def test_load_valid_json(self, tmp_path: Path) -> None:
        """Load valid JSON config."""
        config_file = tmp_path / "test.json"
        config_data = {"server": {"host": "localhost", "port": 8080}}
        config_file.write_text(json.dumps(config_data))

        cm = ConfigManager()
        result = cm.load_config(config_file)

        assert result is True
        assert cm._config == config_data
        assert cm._config_path == config_file

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Load returns False for missing file."""
        cm = ConfigManager()
        result = cm.load_config(tmp_path / "missing.json")

        assert result is False
        assert cm._config == {}

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Load handles invalid JSON gracefully."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ invalid json }")

        cm = ConfigManager()
        result = cm.load_config(config_file)

        assert result is False
        assert cm._config == {}

    def test_load_nested_config(self, tmp_path: Path) -> None:
        """Load deeply nested configuration."""
        config_file = tmp_path / "nested.json"
        config_data = {"level1": {"level2": {"level3": {"value": "deep"}}}}
        config_file.write_text(json.dumps(config_data))

        cm = ConfigManager()
        cm.load_config(config_file)

        assert cm._config == config_data


class TestConfigManagerGet:
    """Test get method with dotted key notation and type casting."""

    @pytest.fixture
    def configured_manager(self, tmp_path: Path) -> ConfigManager:
        """Create manager with test configuration."""
        config_file = tmp_path / "config.json"
        config_data = {
            "server": {"host": "localhost", "port": 8080, "enabled": True, "ratio": 1.5},
            "database": {"name": "testdb"},
            "simple_key": "simple_value",
        }
        config_file.write_text(json.dumps(config_data))
        return ConfigManager(config_file)

    def test_get_dotted_key(self, configured_manager: ConfigManager) -> None:
        """Get value using dotted notation."""
        assert configured_manager.get("server.host") == "localhost"
        assert configured_manager.get("server.port") == 8080
        assert configured_manager.get("database.name") == "testdb"

    def test_get_simple_key(self, configured_manager: ConfigManager) -> None:
        """Get top-level key."""
        assert configured_manager.get("simple_key") == "simple_value"

    def test_get_missing_key_returns_default(self, configured_manager: ConfigManager) -> None:
        """Missing key returns default value."""
        assert configured_manager.get("missing.key", "default") == "default"
        assert configured_manager.get("server.missing", 42) == 42

    def test_get_missing_key_no_default(self, configured_manager: ConfigManager) -> None:
        """Missing key with no default returns None."""
        assert configured_manager.get("missing.key") is None

    def test_get_env_override_string(self, configured_manager: ConfigManager) -> None:
        """Environment variable overrides config value (string)."""
        with patch.dict(os.environ, {"SERVER_HOST": "override.host"}):
            assert configured_manager.get("server.host", "default") == "override.host"

    def test_get_env_override_bool_true(self, configured_manager: ConfigManager) -> None:
        """Environment variable override for boolean True values."""
        test_cases = ["1", "true", "yes", "on", "TRUE", "YES"]
        for val in test_cases:
            with patch.dict(os.environ, {"SERVER_ENABLED": val}):
                result = configured_manager.get("server.enabled", False)
                assert result is True, f"Expected True for {val}"

    def test_get_env_override_bool_false(self, configured_manager: ConfigManager) -> None:
        """Environment variable override for boolean False values."""
        with patch.dict(os.environ, {"SERVER_ENABLED": "0"}):
            result = configured_manager.get("server.enabled", False)
            assert result is False

    def test_get_env_override_int(self, configured_manager: ConfigManager) -> None:
        """Environment variable override for integer."""
        with patch.dict(os.environ, {"SERVER_PORT": "9999"}):
            assert configured_manager.get("server.port", 0) == 9999

    def test_get_env_override_float(self, configured_manager: ConfigManager) -> None:
        """Environment variable override for float."""
        with patch.dict(os.environ, {"SERVER_RATIO": "2.75"}):
            assert configured_manager.get("server.ratio", 0.0) == 2.75

    def test_get_env_override_list(self, configured_manager: ConfigManager) -> None:
        """Environment variable override for list (comma-separated)."""
        with patch.dict(os.environ, {"SERVER_HOSTS": "host1, host2, host3"}):
            result = configured_manager.get("server.hosts", [])
            assert result == ["host1", "host2", "host3"]

    def test_get_env_override_invalid_int(self, configured_manager: ConfigManager) -> None:
        """Invalid int env var returns string."""
        with patch.dict(os.environ, {"SERVER_PORT": "not_a_number"}):
            result = configured_manager.get("server.port", 0)
            assert result == "not_a_number"


class TestConfigManagerSet:
    """Test set method."""

    def test_set_simple_key(self) -> None:
        """Set top-level key."""
        cm = ConfigManager()
        cm.set("key", "value")
        assert cm._config == {"key": "value"}

    def test_set_dotted_key(self) -> None:
        """Set nested key creates path."""
        cm = ConfigManager()
        cm.set("server.host", "localhost")
        assert cm._config == {"server": {"host": "localhost"}}

    def test_set_deeply_nested(self) -> None:
        """Set deeply nested key."""
        cm = ConfigManager()
        cm.set("a.b.c.d", "deep")
        assert cm._config == {"a": {"b": {"c": {"d": "deep"}}}}

    def test_set_overwrites_existing(self) -> None:
        """Set overwrites existing value."""
        cm = ConfigManager()
        cm.set("key", "old")
        cm.set("key", "new")
        assert cm._config["key"] == "new"


class TestConfigManagerGetSection:
    """Test get_section method."""

    def test_get_existing_section(self, tmp_path: Path) -> None:
        """Get existing section returns dict."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"server": {"host": "host", "port": 80}}')
        cm = ConfigManager(config_file)

        section = cm.get_section("server")
        assert section == {"host": "host", "port": 80}

    def test_get_missing_section(self, tmp_path: Path) -> None:
        """Missing section returns empty dict."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"server": {}}')
        cm = ConfigManager(config_file)

        section = cm.get_section("missing")
        assert section == {}

    def test_get_non_dict_section(self, tmp_path: Path) -> None:
        """Non-dict section returns empty dict."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"key": "string_value"}')
        cm = ConfigManager(config_file)

        section = cm.get_section("key")
        assert section == {}


class TestConfigManagerHotReload:
    """Test hot-reload functionality."""

    def test_has_config_changed_no_path(self) -> None:
        """No config path returns False."""
        cm = ConfigManager()
        assert cm.has_config_changed() is False

    def test_has_config_changed_file_deleted(self, tmp_path: Path) -> None:
        """Deleted file returns False."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        cm = ConfigManager(config_file)

        config_file.unlink()
        assert cm.has_config_changed() is False

    def test_has_config_changed_file_modified(self, tmp_path: Path) -> None:
        """Modified file returns True."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"v": 1}')
        cm = ConfigManager(config_file)

        # Ensure different mtime
        time.sleep(0.1)
        config_file.write_text('{"v": 2}')

        assert cm.has_config_changed() is True

    def test_reload_if_changed_no_change(self, tmp_path: Path) -> None:
        """No reload when file unchanged."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"v": 1}')
        cm = ConfigManager(config_file)

        result = cm.reload_if_changed()
        assert result is False

    def test_reload_if_changed_file_modified(self, tmp_path: Path) -> None:
        """Reload when file changed."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"v": 1}')
        cm = ConfigManager(config_file)

        # Modify file
        time.sleep(0.1)
        config_file.write_text('{"v": 2}')

        result = cm.reload_if_changed()
        assert result is True
        assert cm._config == {"v": 2}


class TestConfigManagerValidation:
    """Test validate_required_keys method."""

    def test_all_keys_present(self, tmp_path: Path) -> None:
        """Validation passes when all keys exist."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"server": {"host": "h", "port": 80}}')
        cm = ConfigManager(config_file)

        result = cm.validate_required_keys(["server.host", "server.port"])
        assert result is True

    def test_some_keys_missing(self, tmp_path: Path) -> None:
        """Validation fails when keys missing."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"server": {"host": "h"}}')
        cm = ConfigManager(config_file)

        result = cm.validate_required_keys(["server.host", "server.port"])
        assert result is False

    def test_empty_required_list(self, tmp_path: Path) -> None:
        """Empty required list passes."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        cm = ConfigManager(config_file)

        result = cm.validate_required_keys([])
        assert result is True


class TestConfigManagerPersistence:
    """Test get_all_config and save_config methods."""

    def test_get_all_config_returns_copy(self, tmp_path: Path) -> None:
        """get_all_config returns copy not reference."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"key": "value"}')
        cm = ConfigManager(config_file)

        config = cm.get_all_config()
        config["key"] = "modified"

        assert cm._config["key"] == "value"

    def test_save_config_to_same_file(self, tmp_path: Path) -> None:
        """Save config to original file."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"key": "old"}')
        cm = ConfigManager(config_file)

        cm.set("key", "new")
        result = cm.save_config()

        assert result is True
        saved = json.loads(config_file.read_text())
        assert saved == {"key": "new"}

    def test_save_config_to_new_file(self, tmp_path: Path) -> None:
        """Save config to new file."""
        cm = ConfigManager()
        cm.set("key", "value")

        output = tmp_path / "output.json"
        result = cm.save_config(output)

        assert result is True
        assert output.exists()
        assert json.loads(output.read_text()) == {"key": "value"}

    def test_save_config_creates_directories(self, tmp_path: Path) -> None:
        """Save config creates parent directories."""
        cm = ConfigManager()
        cm.set("key", "value")

        output = tmp_path / "nested" / "dir" / "config.json"
        result = cm.save_config(output)

        assert result is True
        assert output.exists()

    def test_save_config_no_path_fails(self) -> None:
        """Save with no path returns False."""
        cm = ConfigManager()
        cm.set("key", "value")

        result = cm.save_config()
        assert result is False


class TestGlobalConfigFunctions:
    """Test global configuration singleton and convenience functions."""

    def test_get_global_config_singleton(self, tmp_path: Path) -> None:
        """get_global_config returns singleton."""
        # Reset global state
        import src.core.config_manager as mod

        mod._global_config_manager = None

        config1 = get_global_config()
        config2 = get_global_config()

        assert config1 is config2

    def test_set_global_config(self, tmp_path: Path) -> None:
        """set_global_config replaces singleton."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"custom": true}')

        custom = ConfigManager(config_file)
        set_global_config(custom)

        assert get_global_config() is custom

    def test_get_context_server_config(self, tmp_path: Path) -> None:
        """get_context_server_config returns section."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"context_server": {"host": "localhost"}}')
        set_global_config(ConfigManager(config_file))

        section = get_context_server_config()
        assert section == {"host": "localhost"}

    def test_get_ollama_config(self, tmp_path: Path) -> None:
        """get_ollama_config returns section."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"ollama": {"model": "llama3"}}')
        set_global_config(ConfigManager(config_file))

        section = get_ollama_config()
        assert section == {"model": "llama3"}

    def test_get_system_config(self, tmp_path: Path) -> None:
        """get_system_config returns section."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"system": {"debug": true}}')
        set_global_config(ConfigManager(config_file))

        section = get_system_config()
        assert section == {"debug": True}

    def test_get_zeta_config(self, tmp_path: Path) -> None:
        """get_zeta_config returns section."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"zeta": {"phase": "ZETA05"}}')
        set_global_config(ConfigManager(config_file))

        section = get_zeta_config()
        assert section == {"phase": "ZETA05"}

    def test_convenience_functions_missing_section(self, tmp_path: Path) -> None:
        """Convenience functions return empty dict for missing sections."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{}")
        set_global_config(ConfigManager(config_file))

        assert get_context_server_config() == {}
        assert get_ollama_config() == {}
        assert get_system_config() == {}
        assert get_zeta_config() == {}
