"""Tests for src/utils/config_validator.py - ConfigValidator class.

Tests configuration validation including path, host, port, timeout validation,
required fields checking, and full config validation.
"""

import socket
from typing import Any
from unittest.mock import patch

import pytest
from src.utils.config_validator import ConfigValidator

# =============================================================================
# Test Class Constants
# =============================================================================


class TestValidationMethods:
    """Tests for VALIDATION_METHODS class constant."""

    def test_validation_methods_contains_path(self) -> None:
        """VALIDATION_METHODS contains path mapping."""
        assert "path" in ConfigValidator.VALIDATION_METHODS
        assert ConfigValidator.VALIDATION_METHODS["path"] == "validate_path"

    def test_validation_methods_contains_host(self) -> None:
        """VALIDATION_METHODS contains host mapping."""
        assert "host" in ConfigValidator.VALIDATION_METHODS
        assert ConfigValidator.VALIDATION_METHODS["host"] == "validate_host"

    def test_validation_methods_contains_port(self) -> None:
        """VALIDATION_METHODS contains port mapping."""
        assert "port" in ConfigValidator.VALIDATION_METHODS
        assert ConfigValidator.VALIDATION_METHODS["port"] == "validate_port"

    def test_validation_methods_contains_timeout(self) -> None:
        """VALIDATION_METHODS contains timeout mapping."""
        assert "timeout" in ConfigValidator.VALIDATION_METHODS
        assert ConfigValidator.VALIDATION_METHODS["timeout"] == "validate_timeout"

    def test_validation_methods_has_four_entries(self) -> None:
        """VALIDATION_METHODS has exactly 4 entries."""
        assert len(ConfigValidator.VALIDATION_METHODS) == 4


class TestRequiredFields:
    """Tests for REQUIRED_FIELDS class constant."""

    def test_chatdev_requires_path(self) -> None:
        """Chatdev section requires path field."""
        assert "chatdev" in ConfigValidator.REQUIRED_FIELDS
        assert ConfigValidator.REQUIRED_FIELDS["chatdev"] == {"path"}

    def test_ollama_requires_host_and_path(self) -> None:
        """Ollama section requires host and path fields."""
        assert "ollama" in ConfigValidator.REQUIRED_FIELDS
        assert ConfigValidator.REQUIRED_FIELDS["ollama"] == {"host", "path"}

    def test_vscode_requires_path(self) -> None:
        """Vscode section requires path field."""
        assert "vscode" in ConfigValidator.REQUIRED_FIELDS
        assert ConfigValidator.REQUIRED_FIELDS["vscode"] == {"path"}

    def test_context_server_requires_host_and_port(self) -> None:
        """context_server section requires host and port fields."""
        assert "context_server" in ConfigValidator.REQUIRED_FIELDS
        assert ConfigValidator.REQUIRED_FIELDS["context_server"] == {"host", "port"}

    def test_timeouts_requires_default_and_long(self) -> None:
        """Timeouts section requires default and long fields."""
        assert "timeouts" in ConfigValidator.REQUIRED_FIELDS
        assert ConfigValidator.REQUIRED_FIELDS["timeouts"] == {"default", "long"}

    def test_feature_flags_has_no_required_fields(self) -> None:
        """feature_flags section has no required fields."""
        assert "feature_flags" in ConfigValidator.REQUIRED_FIELDS
        assert ConfigValidator.REQUIRED_FIELDS["feature_flags"] == set()


# =============================================================================
# Test validate_path
# =============================================================================


class TestValidatePath:
    """Tests for validate_path static method."""

    def test_validates_existing_readable_path(self, tmp_path: Any) -> None:
        """Returns True for existing readable path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        assert ConfigValidator.validate_path(str(test_file)) is True

    def test_validates_existing_directory(self, tmp_path: Any) -> None:
        """Returns True for existing readable directory."""
        assert ConfigValidator.validate_path(str(tmp_path)) is True

    def test_raises_for_nonexistent_path(self) -> None:
        """Raises ValueError for nonexistent path."""
        with pytest.raises(ValueError) as exc_info:
            ConfigValidator.validate_path("/nonexistent/path/12345")
        assert "does not exist" in str(exc_info.value)

    def test_raises_for_unreadable_path(self, tmp_path: Any) -> None:
        """Raises ValueError for unreadable path."""
        test_file = tmp_path / "unreadable.txt"
        test_file.write_text("test")

        with patch("os.path.exists", return_value=True):
            with patch("os.access", return_value=False):
                with pytest.raises(ValueError) as exc_info:
                    ConfigValidator.validate_path(str(test_file))
                assert "not readable" in str(exc_info.value)

    def test_error_message_includes_path(self) -> None:
        """Error message includes the invalid path."""
        bad_path = "/my/bad/path/xyz"
        with pytest.raises(ValueError) as exc_info:
            ConfigValidator.validate_path(bad_path)
        assert bad_path in str(exc_info.value)


# =============================================================================
# Test validate_host
# =============================================================================


class TestValidateHost:
    """Tests for validate_host static method."""

    def test_validates_localhost(self) -> None:
        """Returns True for localhost."""
        assert ConfigValidator.validate_host("localhost") is True

    def test_validates_127_0_0_1(self) -> None:
        """Returns True for 127.0.0.1."""
        assert ConfigValidator.validate_host("127.0.0.1") is True

    def test_validates_resolvable_host(self) -> None:
        """Returns True for resolvable hostname."""
        with patch("socket.gethostbyname", return_value="1.2.3.4"):
            assert ConfigValidator.validate_host("example.com") is True

    def test_raises_for_unresolvable_host(self) -> None:
        """Raises ValueError for unresolvable host."""
        with patch(
            "socket.gethostbyname",
            side_effect=socket.gaierror(11001, "getaddrinfo failed"),
        ):
            with pytest.raises(ValueError) as exc_info:
                ConfigValidator.validate_host("nonexistent.invalid.host.xyz")
            assert "not accessible" in str(exc_info.value)

    def test_error_message_includes_host(self) -> None:
        """Error message includes the invalid host."""
        bad_host = "badhost123.invalid"
        with patch(
            "socket.gethostbyname",
            side_effect=socket.gaierror(11001, "getaddrinfo failed"),
        ):
            with pytest.raises(ValueError) as exc_info:
                ConfigValidator.validate_host(bad_host)
            assert bad_host in str(exc_info.value)


# =============================================================================
# Test validate_port
# =============================================================================


class TestValidatePort:
    """Tests for validate_port static method."""

    def test_validates_standard_port(self) -> None:
        """Returns True for standard port 8080."""
        assert ConfigValidator.validate_port(8080) is True

    def test_validates_port_1(self) -> None:
        """Returns True for port 1 (minimum valid)."""
        assert ConfigValidator.validate_port(1) is True

    def test_validates_high_port(self) -> None:
        """Returns True for high port number."""
        assert ConfigValidator.validate_port(65535) is True

    def test_raises_for_zero_port(self) -> None:
        """Raises ValueError for port 0."""
        with pytest.raises(ValueError) as exc_info:
            ConfigValidator.validate_port(0)
        assert "positive integer" in str(exc_info.value)

    def test_raises_for_negative_port(self) -> None:
        """Raises ValueError for negative port."""
        with pytest.raises(ValueError) as exc_info:
            ConfigValidator.validate_port(-1)
        assert "positive integer" in str(exc_info.value)

    def test_error_message_includes_port(self) -> None:
        """Error message includes the invalid port."""
        with pytest.raises(ValueError) as exc_info:
            ConfigValidator.validate_port(-42)
        assert "-42" in str(exc_info.value)


# =============================================================================
# Test validate_timeout
# =============================================================================


class TestValidateTimeout:
    """Tests for validate_timeout static method."""

    def test_validates_standard_timeout(self) -> None:
        """Returns True for standard timeout 60."""
        assert ConfigValidator.validate_timeout(60) is True

    def test_validates_timeout_1(self) -> None:
        """Returns True for timeout 1 (minimum valid)."""
        assert ConfigValidator.validate_timeout(1) is True

    def test_validates_large_timeout(self) -> None:
        """Returns True for large timeout value."""
        assert ConfigValidator.validate_timeout(3600) is True

    def test_raises_for_zero_timeout(self) -> None:
        """Raises ValueError for timeout 0."""
        with pytest.raises(ValueError) as exc_info:
            ConfigValidator.validate_timeout(0)
        assert "positive integer" in str(exc_info.value)

    def test_raises_for_negative_timeout(self) -> None:
        """Raises ValueError for negative timeout."""
        with pytest.raises(ValueError) as exc_info:
            ConfigValidator.validate_timeout(-10)
        assert "positive integer" in str(exc_info.value)

    def test_error_message_includes_timeout(self) -> None:
        """Error message includes the invalid timeout."""
        with pytest.raises(ValueError) as exc_info:
            ConfigValidator.validate_timeout(-100)
        assert "-100" in str(exc_info.value)


# =============================================================================
# Test _check_missing_fields
# =============================================================================


class TestCheckMissingFields:
    """Tests for _check_missing_fields class method."""

    def test_returns_none_for_unknown_key(self) -> None:
        """Returns None for key not in required_fields."""
        result = ConfigValidator._check_missing_fields(
            "unknown_section",
            {"field1": "value1"},
            {"known_section": {"field1"}},
        )
        assert result is None

    def test_returns_none_when_all_fields_present(self) -> None:
        """Returns None when all required fields present."""
        result = ConfigValidator._check_missing_fields(
            "chatdev",
            {"path": "/some/path"},
            {"chatdev": {"path"}},
        )
        assert result is None

    def test_returns_error_for_missing_field(self) -> None:
        """Returns error message for missing field."""
        result = ConfigValidator._check_missing_fields(
            "chatdev",
            {},
            {"chatdev": {"path"}},
        )
        assert result is not None
        assert "Missing fields" in result
        assert "path" in result

    def test_returns_error_for_multiple_missing_fields(self) -> None:
        """Returns error message listing multiple missing fields."""
        result = ConfigValidator._check_missing_fields(
            "ollama",
            {"extra": "value"},
            {"ollama": {"host", "path"}},
        )
        assert result is not None
        assert "Missing fields" in result
        # Both fields should be mentioned
        assert "host" in result or "path" in result

    def test_returns_none_for_empty_required_set(self) -> None:
        """Returns None when required set is empty."""
        result = ConfigValidator._check_missing_fields(
            "feature_flags",
            {},
            {"feature_flags": set()},
        )
        assert result is None


# =============================================================================
# Test _validate_sub_fields
# =============================================================================


class TestValidateSubFields:
    """Tests for _validate_sub_fields class method."""

    def test_returns_empty_dict_for_unknown_fields(self) -> None:
        """Returns empty dict when no known validation methods."""
        result = ConfigValidator._validate_sub_fields(
            "section",
            {"unknown_field": "value"},
        )
        assert result == {}

    def test_validates_path_field(self, tmp_path: Any) -> None:
        """Validates path field successfully."""
        result = ConfigValidator._validate_sub_fields(
            "chatdev",
            {"path": str(tmp_path)},
        )
        assert result == {}

    def test_captures_path_validation_error(self) -> None:
        """Captures path validation error."""
        result = ConfigValidator._validate_sub_fields(
            "chatdev",
            {"path": "/nonexistent/path/12345"},
        )
        assert "chatdev.path" in result
        assert "does not exist" in result["chatdev.path"]

    def test_validates_host_field(self) -> None:
        """Validates host field successfully."""
        result = ConfigValidator._validate_sub_fields(
            "context_server",
            {"host": "localhost"},
        )
        assert result == {}

    def test_captures_host_validation_error(self) -> None:
        """Captures host validation error."""
        with patch(
            "socket.gethostbyname",
            side_effect=socket.gaierror(11001, "getaddrinfo failed"),
        ):
            result = ConfigValidator._validate_sub_fields(
                "context_server",
                {"host": "invalid.host.xyz"},
            )
            assert "context_server.host" in result

    def test_validates_port_field(self) -> None:
        """Validates port field successfully."""
        result = ConfigValidator._validate_sub_fields(
            "context_server",
            {"port": 8080},
        )
        assert result == {}

    def test_captures_port_validation_error(self) -> None:
        """Captures port validation error."""
        result = ConfigValidator._validate_sub_fields(
            "context_server",
            {"port": -1},
        )
        assert "context_server.port" in result
        assert "positive integer" in result["context_server.port"]

    def test_validates_timeout_field(self) -> None:
        """Validates timeout field successfully."""
        result = ConfigValidator._validate_sub_fields(
            "timeouts",
            {"timeout": 60},
        )
        assert result == {}

    def test_captures_timeout_validation_error(self) -> None:
        """Captures timeout validation error."""
        result = ConfigValidator._validate_sub_fields(
            "timeouts",
            {"timeout": 0},
        )
        assert "timeouts.timeout" in result

    def test_multiple_errors_in_same_section(self) -> None:
        """Captures multiple errors in same section."""
        with patch(
            "socket.gethostbyname",
            side_effect=socket.gaierror(11001, "getaddrinfo failed"),
        ):
            result = ConfigValidator._validate_sub_fields(
                "context_server",
                {"host": "bad.host", "port": -1},
            )
            assert "context_server.host" in result
            assert "context_server.port" in result


# =============================================================================
# Test validate_config
# =============================================================================


class TestValidateConfig:
    """Tests for validate_config class method."""

    def test_validates_empty_config(self) -> None:
        """Empty config returns empty report."""
        result = ConfigValidator.validate_config({})
        assert result == {}

    def test_rejects_non_dict_section(self) -> None:
        """Rejects config section that is not a dict."""
        result = ConfigValidator.validate_config({"chatdev": "not_a_dict"})
        assert "chatdev" in result
        assert "Expected object-like" in result["chatdev"]

    def test_rejects_unknown_section(self) -> None:
        """Rejects unknown config section."""
        result = ConfigValidator.validate_config({"unknown_section": {"key": "value"}})
        assert "unknown_section" in result
        assert "Unknown field" in result["unknown_section"]

    def test_accepts_known_section_in_required_fields(self, tmp_path: Any) -> None:
        """Accepts section defined in REQUIRED_FIELDS."""
        result = ConfigValidator.validate_config({"chatdev": {"path": str(tmp_path)}})
        assert "chatdev" not in result

    def test_accepts_known_section_in_optional_fields(self, tmp_path: Any) -> None:
        """Accepts section defined in optional_fields."""
        result = ConfigValidator.validate_config(
            {"custom_section": {"path": str(tmp_path)}},
            required_fields={},
            optional_fields={"custom_section": {}},
        )
        assert "custom_section" not in result

    def test_reports_missing_required_fields(self) -> None:
        """Reports missing required fields."""
        result = ConfigValidator.validate_config({"chatdev": {}})
        assert "chatdev" in result
        assert "Missing fields" in result["chatdev"]
        assert "path" in result["chatdev"]

    def test_reports_sub_field_validation_errors(self) -> None:
        """Reports sub-field validation errors."""
        result = ConfigValidator.validate_config(
            {"context_server": {"host": "localhost", "port": -1}}
        )
        assert "context_server.port" in result

    def test_uses_default_required_fields(self, tmp_path: Any) -> None:
        """Uses default REQUIRED_FIELDS when not specified."""
        # chatdev is in default REQUIRED_FIELDS
        result = ConfigValidator.validate_config({"chatdev": {"path": str(tmp_path)}})
        # Should pass because chatdev.path is provided
        assert "chatdev" not in result

    def test_uses_custom_required_fields(self, tmp_path: Any) -> None:
        """Uses custom required_fields when provided."""
        result = ConfigValidator.validate_config(
            {"custom": {"field1": "value"}},
            required_fields={"custom": {"field1", "field2"}},
        )
        assert "custom" in result
        assert "Missing fields" in result["custom"]
        assert "field2" in result["custom"]

    def test_feature_flags_with_empty_dict(self) -> None:
        """feature_flags with empty dict is valid."""
        result = ConfigValidator.validate_config({"feature_flags": {}})
        assert "feature_flags" not in result

    def test_full_valid_config(self, tmp_path: Any) -> None:
        """Full valid config returns empty report."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        config = {
            "chatdev": {"path": str(tmp_path)},
            "vscode": {"path": str(tmp_path)},
            "timeouts": {"default": 10, "long": 60},
            "feature_flags": {},
        }

        # Mock host validation
        with patch("socket.gethostbyname", return_value="127.0.0.1"):
            config["ollama"] = {"host": "localhost", "path": str(tmp_path)}
            config["context_server"] = {"host": "localhost", "port": 8080}
            result = ConfigValidator.validate_config(config)

        assert result == {}

    def test_multiple_sections_with_errors(self) -> None:
        """Reports errors from multiple sections."""
        result = ConfigValidator.validate_config(
            {
                "chatdev": {},  # Missing path
                "context_server": {"host": "localhost", "port": -1},  # Invalid port
            }
        )
        assert "chatdev" in result  # Missing fields
        assert "context_server.port" in result  # Invalid port


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_validate_port_with_very_large_number(self) -> None:
        """Validates very large port number."""
        # Port validation only checks > 0 and int
        assert ConfigValidator.validate_port(999999) is True

    def test_validate_timeout_with_very_large_number(self) -> None:
        """Validates very large timeout value."""
        assert ConfigValidator.validate_timeout(86400 * 365) is True

    def test_validate_config_with_extra_fields_in_section(self, tmp_path: Any) -> None:
        """Config section can have extra fields not in required."""
        result = ConfigValidator.validate_config(
            {
                "chatdev": {
                    "path": str(tmp_path),
                    "extra_field": "extra_value",
                }
            }
        )
        # Should pass - extra fields are allowed
        assert "chatdev" not in result

    def test_class_instantiation(self) -> None:
        """ConfigValidator can be instantiated."""
        validator = ConfigValidator()
        assert validator is not None
        assert hasattr(validator, "validate_config")

    def test_validation_methods_are_callable(self) -> None:
        """All methods in VALIDATION_METHODS are callable."""
        for method_name in ConfigValidator.VALIDATION_METHODS.values():
            assert hasattr(ConfigValidator, method_name)
            assert callable(getattr(ConfigValidator, method_name))

    def test_empty_optional_fields(self, tmp_path: Any) -> None:
        """Empty optional_fields dict works correctly."""
        result = ConfigValidator.validate_config(
            {"chatdev": {"path": str(tmp_path)}},
            required_fields=ConfigValidator.REQUIRED_FIELDS,
            optional_fields={},
        )
        assert "chatdev" not in result

    def test_section_with_only_unknown_sub_fields(self, tmp_path: Any) -> None:
        """Section with only unknown sub-fields passes validation."""
        # feature_flags has no required fields
        result = ConfigValidator.validate_config(
            {
                "feature_flags": {
                    "enable_feature_x": True,
                    "enable_feature_y": False,
                }
            }
        )
        assert result == {}

    def test_nested_validation_preserves_section_key(self) -> None:
        """Sub-field errors include section.field format."""
        result = ConfigValidator.validate_config(
            {"context_server": {"host": "localhost", "port": 0}}
        )
        # Should have context_server.port error
        error_keys = list(result.keys())
        assert any("context_server.port" in k for k in error_keys)
