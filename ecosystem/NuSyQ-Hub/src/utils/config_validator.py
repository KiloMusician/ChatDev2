import os
import socket
from typing import Any, ClassVar


class ConfigValidator:
    VALIDATION_METHODS: ClassVar[dict[str, str]] = {
        "path": "validate_path",
        "host": "validate_host",
        "port": "validate_port",
        "timeout": "validate_timeout",
    }

    REQUIRED_FIELDS: ClassVar[dict[str, set[str]]] = {
        "chatdev": {"path"},
        "ollama": {"host", "path"},
        "vscode": {"path"},
        "context_server": {"host", "port"},
        "timeouts": {"default", "long"},
        "feature_flags": set(),
    }

    @staticmethod
    def validate_path(path: str) -> bool:
        if not os.path.exists(path):
            msg = f"Path {path} does not exist."
            raise ValueError(msg)
        if not os.access(path, os.R_OK):
            msg = f"Path {path} is not readable."
            raise ValueError(msg)
        return True

    @staticmethod
    def validate_host(host: str) -> bool:
        try:
            socket.gethostbyname(host)
        except socket.gaierror as host_error:
            msg = f"Host {host} is not accessible."
            raise ValueError(msg) from host_error
        return True

    @staticmethod
    def validate_port(port: int) -> bool:
        if port <= 0 or not isinstance(port, int):
            msg = f"Port {port} must be a positive integer."
            raise ValueError(msg)
        return True

    @staticmethod
    def validate_timeout(timeout: int) -> bool:
        if timeout <= 0 or not isinstance(timeout, int):
            msg = f"Timeout {timeout} must be a positive integer."
            raise ValueError(msg)
        return True

    @classmethod
    def _check_missing_fields(
        cls,
        key: str,
        value: dict[str, Any],
        required_fields: dict[str, set[str]],
    ) -> str | None:
        """Check if required fields are missing from config section."""
        if key not in required_fields:
            return None
        missing_fields = required_fields[key].difference(value.keys())
        if missing_fields:
            return f"Missing fields: {', '.join(missing_fields)}"
        return None

    @classmethod
    def _validate_sub_fields(
        cls,
        key: str,
        value: dict[str, Any],
    ) -> dict[str, str]:
        """Validate individual fields within a config section."""
        errors: dict[str, str] = {}
        for sub_key, sub_value in value.items():
            method_name = cls.VALIDATION_METHODS.get(sub_key)
            if method_name:
                try:
                    validation_method = getattr(cls, method_name)
                    validation_method(sub_value)
                except ValueError as e:
                    errors[f"{key}.{sub_key}"] = str(e)
        return errors

    @classmethod
    def validate_config(
        cls,
        config_dict: dict[str, Any],
        required_fields: dict[str, set[str]] | None = None,
        optional_fields: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Validate configuration dictionary against required and optional fields."""
        if required_fields is None:
            required_fields = dict(cls.REQUIRED_FIELDS)
        if optional_fields is None:
            optional_fields = {}
        validation_report: dict[str, str] = {}

        for key, value in config_dict.items():
            if not isinstance(value, dict):
                validation_report[key] = "Expected object-like configuration section."
                continue
            # Check if field is known
            if key not in required_fields and key not in optional_fields:
                validation_report[key] = f"Unknown field: {key}"
                continue

            # Check for missing required fields
            missing_error = cls._check_missing_fields(key, value, required_fields)
            if missing_error:
                validation_report[key] = missing_error
                continue

            # Validate sub-fields
            sub_errors = cls._validate_sub_fields(key, value)
            validation_report.update(sub_errors)

        return validation_report


# Example usage
config = {
    "chatdev": {"path": "/path/to/chatdev"},
    "ollama": {"host": "ollama.example.com", "path": "/path/to/ollama"},
    "vscode": {"path": "/path/to/vscode"},
    "context_server": {"host": "server.example.com", "port": 8080},
    "timeouts": {"default": 10, "long": 60},
    "feature_flags": {},
}

validator = ConfigValidator()
report = validator.validate_config(config)


# Unit test examples
def test_validate_path() -> None:
    assert ConfigValidator.validate_path("/path/to/existing/file") is True
    try:
        ConfigValidator.validate_path("/path/to/nonexistent/file")
    except ValueError as e:
        assert str(e) == "Path /path/to/nonexistent/file does not exist."


def test_validate_host() -> None:
    assert ConfigValidator.validate_host("google.com") is True
    try:
        ConfigValidator.validate_host("nonexistenthost.example.com")
    except ValueError as e:
        assert str(e) == "Host nonexistenthost.example.com is not accessible."


def test_validate_port() -> None:
    assert ConfigValidator.validate_port(8080) is True
    try:
        ConfigValidator.validate_port(-1)
    except ValueError as e:
        assert str(e) == "Port -1 must be a positive integer."


def test_validate_timeout() -> None:
    assert ConfigValidator.validate_timeout(60) is True
    try:
        ConfigValidator.validate_timeout(-1)
    except ValueError as e:
        assert str(e) == "Timeout -1 must be a positive integer."
