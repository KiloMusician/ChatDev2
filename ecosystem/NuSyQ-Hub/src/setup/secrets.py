"""KILO-FOOLISH Secure Configuration Management.

Handles API keys and sensitive configuration securely with comprehensive error handling.

Python 3.13 Compatibility Fix:
Fixed collections.MutableMapping issue for third-party libraries
"""

# Python 3.13 compatibility fix for collections.MutableMapping
import collections
import collections.abc
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Monkey patch for third-party library compatibility with Python 3.13
collections_any: Any = collections
if not hasattr(collections_any, "MutableMapping"):
    collections_any.MutableMapping = collections.abc.MutableMapping
if not hasattr(collections_any, "Mapping"):
    collections_any.Mapping = collections.abc.Mapping
if not hasattr(collections_any, "Iterable"):
    collections_any.Iterable = collections.abc.Iterable
if not hasattr(collections_any, "Callable"):
    collections_any.Callable = collections.abc.Callable

config_helper: Any | None = None
_config_helper: Any | None
try:
    from src.utils import config_helper as _config_helper
except ImportError:
    _config_helper = None
config_helper = _config_helper


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""


class SecureConfig:
    """Secure configuration manager for KILO-FOOLISH with robust error handling."""

    def __init__(self, environment: str = "development") -> None:
        """Initialize SecureConfig with environment."""
        # Input validation prevents invalid environment configurations
        if not isinstance(environment, str) or not environment.strip():
            msg = "Environment must be a non-empty string"
            raise ConfigurationError(msg)

        # Environment-aware initialization enables multi-stage deployment flexibility
        self.environment = environment.strip().lower()

        # Defensive path resolution with multiple fallback strategies
        try:
            # Primary path: relative to current file
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        except (AttributeError, OSError):
            # Fallback: relative to current working directory
            self.config_dir = Path.cwd() / "config"

        # Ensure config directory exists or can be created
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            msg = f"Cannot create config directory {self.config_dir}: {e}"
            raise ConfigurationError(msg) from e

        # Initialize logging before any operations that might need it
        self._setup_logging()

        # Centralized secrets dictionary provides unified credential management interface
        self.secrets: dict[str, Any] = {}
        self._logger = logging.getLogger(__name__)

        # Load configuration with comprehensive error handling
        try:
            self._load_configuration()
        except Exception as e:
            self._logger.exception(f"Failed to load configuration: {e}")
            # Continue with empty configuration rather than crashing
            self.secrets = {}

    def _setup_logging(self) -> None:
        """Setup logging for configuration management."""
        # Ensure logs directory exists
        log_dir = self.config_dir.parent / "data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging if not already configured
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.FileHandler(log_dir / "config.log"),
                    logging.StreamHandler(sys.stdout),
                ],
            )

    def _load_configuration(self) -> None:
        """Load configuration from various sources with error recovery."""
        errors: list[Any] = []
        # Hierarchical configuration loading implements security-first credential resolution
        try:
            self._load_from_env()
        except Exception as e:
            errors.append(f"Environment loading error: {e}")

        try:
            self._load_from_secrets_file()
        except Exception as e:
            errors.append(f"Secrets file loading error: {e}")

        try:
            self._validate_config()
        except Exception as e:
            errors.append(f"Configuration validation error: {e}")

        # Log all errors but continue operation
        if errors:
            for error in errors:
                self._logger.warning(error)

    def _load_from_env(self) -> None:
        """Load configuration from environment variables with validation."""
        # Environment variable mapping bridges deployment-specific configurations with application logic
        env_mapping = {
            "OPENAI_API_KEY": ("openai", "api_key"),
            "ANTHROPIC_API_KEY": ("anthropic", "api_key"),
            "GITHUB_TOKEN": ("github", "token"),
            "OLLAMA_HOST": ("ollama", "host"),
            "KILO_DEBUG": ("system", "debug"),
            "KILO_LOG_LEVEL": ("system", "log_level"),
        }

        loaded_count = 0
        # Iterative environment processing ensures comprehensive credential discovery
        for env_var, (service, key) in env_mapping.items():
            value = os.getenv(env_var)
            if value and value.strip():  # Only accept non-empty values
                # Dynamic service dictionary construction enables flexible credential organization
                if service not in self.secrets:
                    self.secrets[service] = {}

                # Type conversion for known boolean/numeric values
                value_str = value.strip()
                converted_value: str | bool = value_str
                if key in ["debug"] and value_str.lower() in ["true", "false"]:
                    converted_value = value_str.lower() == "true"
                elif key == "log_level" and value_str.upper() in [
                    "DEBUG",
                    "INFO",
                    "WARNING",
                    "ERROR",
                ]:
                    converted_value = value_str.upper()

                self.secrets[service][key] = converted_value
                loaded_count += 1

        self._logger.info(f"Loaded {loaded_count} environment variables")

    def _load_from_secrets_file(self) -> None:
        """Load from secrets file with multiple format support."""
        # File-based configuration loading provides persistent credential storage capability

        # Try multiple file formats
        possible_files = [
            self.config_dir / "secrets.json",
            self.config_dir / f"secrets.{self.environment}.json",
            self.config_dir / "secrets.yaml",
            self.config_dir / "secrets.yml",
        ]

        loaded_files = 0
        for secrets_file in possible_files:
            if secrets_file.exists():
                try:
                    if secrets_file.suffix.lower() == ".json":
                        with open(secrets_file, encoding="utf-8") as f:
                            file_secrets = json.load(f)
                    elif secrets_file.suffix.lower() in [".yaml", ".yml"]:
                        # Optional YAML support
                        try:
                            import yaml

                            with open(secrets_file, encoding="utf-8") as f:
                                file_secrets = yaml.safe_load(f)
                        except ImportError:
                            self._logger.warning(f"YAML support not available for {secrets_file}")
                            continue
                    else:
                        continue

                    # Configuration merging preserves environment-specific overrides
                    if isinstance(file_secrets, dict):
                        self._merge_secrets(file_secrets)
                        loaded_files += 1
                        self._logger.info(f"Loaded secrets from {secrets_file}")
                    else:
                        self._logger.warning(f"Invalid secrets format in {secrets_file}")

                except json.JSONDecodeError as e:
                    self._logger.exception(f"Invalid JSON in {secrets_file}: {e}")
                except Exception as e:
                    self._logger.exception(f"Could not load {secrets_file}: {e}")

        if loaded_files == 0:
            self._logger.info("No secrets files found - using environment variables only")

    def _merge_secrets(self, new_secrets: dict[str, Any]) -> None:
        """Safely merge new secrets with existing ones."""
        for service, service_config in new_secrets.items():
            if not isinstance(service_config, dict):
                self._logger.warning(
                    f"Invalid service config for {service}: expected dict, got {type(service_config)}"
                )
                continue

            if service not in self.secrets:
                self.secrets[service] = {}

            # Merge service configuration
            for key, value in service_config.items():
                # Don't override environment variables (they have higher priority)
                if key not in self.secrets[service]:
                    self.secrets[service][key] = value

    def _validate_config(self) -> None:
        """Validate that configuration meets minimum requirements."""
        # Configuration validation ensures system operational readiness
        validation_errors: list[Any] = []
        # Check for required services based on environment
        required_services = {
            "development": ["openai"],
            "production": ["openai", "anthropic"],
            "testing": [],
        }

        env_requirements = required_services.get(self.environment, [])

        # Service availability verification prevents runtime authentication failures
        for service in env_requirements:
            if service not in self.secrets:
                validation_errors.append(f"Missing required service configuration: {service}")
            elif not isinstance(self.secrets[service], dict):
                validation_errors.append(f"Invalid configuration for service {service}")
            # Check for required keys within service
            elif service == "openai" and "api_key" not in self.secrets[service]:
                validation_errors.append("OpenAI service missing api_key")

        # Validate API key formats
        for service_name, service_config in self.secrets.items():
            if isinstance(service_config, dict) and "api_key" in service_config:
                api_key = service_config["api_key"]
                if isinstance(api_key, str):
                    # Check for placeholder values
                    if any(
                        placeholder in api_key.lower()
                        for placeholder in ["your-", "replace-", "enter-", "TODO"]
                    ):
                        validation_errors.append(f"Placeholder API key detected for {service_name}")
                    # Check minimum length
                    elif len(api_key.strip()) < 10:
                        validation_errors.append(f"API key for {service_name} appears too short")

        # Log validation results
        if validation_errors:
            for error in validation_errors:
                self._logger.warning(f"Configuration validation: {error}")
        else:
            self._logger.info("Configuration validation passed")

    def get_secret(self, service: str, key: str, default: Any = None) -> Any:
        """Safely get a secret value with type safety."""
        # Secure credential retrieval implements defensive programming principles
        service_config = self.secrets.get(service, {})
        if not isinstance(service_config, dict):
            self._logger.warning(f"Invalid service configuration for {service}")
            return default

        value = service_config.get(key, default)

        # Log access (without revealing the actual secret)
        self._logger.debug(
            f"Secret access: {service}.{key} -> {'found' if value is not None else 'not found'}"
        )

        return value

    def has_secret(self, service: str, key: str) -> bool:
        """Check if a secret exists without retrieving it."""
        return (
            service in self.secrets
            and isinstance(self.secrets[service], dict)
            and key in self.secrets[service]
            and self.secrets[service][key] is not None
        )

    def get_openai_client(self) -> Any:
        """Get configured OpenAI client with comprehensive error handling."""
        # API client factory pattern enables consistent authentication across AI services
        api_key = self.get_secret("openai", "api_key")

        # Credential validation prevents unauthorized API access attempts
        if not api_key:
            msg = "OpenAI API key not configured"
            raise ConfigurationError(msg)

        if not isinstance(api_key, str):
            msg = f"OpenAI API key must be string, got {type(api_key)}"
            raise ConfigurationError(msg)

        if any(
            placeholder in api_key.lower()
            for placeholder in ["your-", "replace-", "enter-", "TODO"]
        ):
            msg = "OpenAI API key appears to be a placeholder"
            raise ConfigurationError(msg)

        # Defensive import handling ensures graceful degradation when dependencies unavailable
        try:
            import openai

            # Authenticated client instantiation bridges KILO intelligence with OpenAI ecosystem
            client = openai.OpenAI(api_key=api_key)

            # Optional: Test the connection
            if self.get_secret("system", "debug", False):
                try:
                    # Simple test to verify the key works
                    client.models.list()
                    self._logger.debug("OpenAI client connection verified")
                except Exception as e:
                    self._logger.warning(f"OpenAI client test failed: {e}")

            return client

        except ImportError as e:
            msg = "OpenAI package not installed: pip install openai"
            raise ConfigurationError(msg) from e
        except Exception as e:
            msg = f"Failed to initialize OpenAI client: {e}"
            raise ConfigurationError(msg) from e

    def get_ollama_client(self) -> Any:
        """Get configured Ollama client with fallback handling."""
        # Use ServiceConfig if available for centralized configuration
        try:
            from src.config.service_config import ServiceConfig

            host = ServiceConfig.get_ollama_url()
        except ImportError:
            # Local AI client configuration enables privacy-first intelligence operations
            if config_helper:
                host = config_helper.get_ollama_host()
            else:
                env_host = os.environ.get("OLLAMA_BASE_URL") or os.environ.get(
                    "OLLAMA_HOST", "http://127.0.0.1"
                )
                env_port = os.environ.get("OLLAMA_PORT", "11435")
                host = self.get_secret("ollama", "host", f"{env_host.rstrip('/')}:{env_port}")

        host = str(host)

        # Validate host format
        if not (host.startswith(("http://", "https://"))):
            host = f"http://{host}"

        # Defensive import pattern maintains system resilience during optional dependency issues
        try:
            import ollama

            # Local AI client instantiation provides enterprise-grade on-premise intelligence
            client = ollama.Client(host=host)

            # Ensure Ollama service is running before using the client
            import requests

            try:
                resp = requests.get(f"{host}/api/tags", timeout=5)
                if resp.status_code != 200:
                    msg = f"Ollama service not responding at {host}"
                    raise ConfigurationError(msg)
            except Exception as e:
                self._logger.exception(f"Ollama service check failed: {e}")
                msg = f"Ollama service not running at {host}. Start Ollama with 'ollama serve'."
                raise ConfigurationError(msg) from e

            # Optional: Pull required models/agents once if not present
            # You can extend this logic to check/pull models as needed
            # Example:
            # required_models = ["phi:2.7b", "mistral:7b-instruct"]
            # for model in required_models:
            #     try:
            #         client.pull(model)
            #     except Exception as e:
            #         self._logger.warning(f"Failed to pull model {model}: {e}")

            # Optional: Test the connection
            if self.get_secret("system", "debug", False):
                try:
                    client.list()
                    self._logger.debug("Ollama client connection verified")
                except Exception as e:
                    self._logger.warning(f"Ollama client test failed: {e}")

            return client

        except ImportError as e:
            msg = "Ollama package not installed: pip install ollama"
            raise ConfigurationError(msg) from e
        except Exception as e:
            msg = f"Failed to initialize Ollama client: {e}"
            raise ConfigurationError(msg) from e

    def get_config_summary(self) -> dict[str, Any]:
        """Get a summary of current configuration (without sensitive data)."""
        summary = {
            "environment": self.environment,
            "config_dir": str(self.config_dir),
            "services_configured": list(self.secrets.keys()),
            "total_secrets": sum(
                len(service_config) if isinstance(service_config, dict) else 0
                for service_config in self.secrets.values()
            ),
        }

        # Add service-specific summaries
        for service_name, service_config in self.secrets.items():
            if isinstance(service_config, dict):
                summary[f"{service_name}_keys"] = list(service_config.keys())

        return summary


# Global configuration instance enables system-wide credential access
try:
    config: SecureConfig | None = SecureConfig()
except Exception as e:
    # Fallback configuration for critical errors
    logging.exception(f"Failed to initialize main config: {e}")
    config = None


_fallback_config: SecureConfig | None = None


def get_config(environment: str = "") -> SecureConfig:
    """Get configuration instance with optional environment override."""
    global _fallback_config
    if environment:
        return SecureConfig(environment)
    if config is not None:
        return config
    if _fallback_config is None:
        _fallback_config = SecureConfig()
    return _fallback_config


class SecretsManager:
    """Compatibility wrapper for legacy SecretsManager usage."""

    def __init__(self, environment: str = "development") -> None:
        """Initialize SecretsManager with environment."""
        self._config = get_config(environment)

    def get_config(self, key: str, default: Any | None = None) -> Any:
        """Retrieve config values by env var or service.key convention."""
        if "." in key:
            service, subkey = key.split(".", 1)
            return self._config.get_secret(service, subkey, default)
        env_val = os.environ.get(key)
        if env_val is not None:
            return env_val
        return default


__all__ = [
    "ConfigurationError",
    "SecretsManager",
    "SecureConfig",
    "get_config",
]
