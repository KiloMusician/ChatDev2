"""
Configuration Management Service
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml  # type: ignore


@dataclass
class ServiceConfig:
    """Service configuration"""

    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    max_connections: int = 100
    timeout: int = 30


@dataclass
class OllamaConfig:
    """Ollama configuration with adaptive timeout support"""

    host: str = "localhost"
    port: int = 11434
    models: Optional[Dict[str, str]] = None
    timeout: int = 60  # Fallback default, overridden by AdaptiveTimeoutManager
    use_adaptive_timeout: bool = True  # Enable adaptive learning timeouts

    def __post_init__(self):
        if self.models is None:
            self.models = {}


@dataclass
class SecurityConfig:
    """Security configuration"""

    allowed_paths: Optional[list] = None
    max_file_size: int = 10485760  # 10MB
    rate_limit: int = 100
    enable_auth: bool = False

    def __post_init__(self):
        if self.allowed_paths is None:
            self.allowed_paths = [
                str(Path.cwd()),
                str(Path.home() / "Documents"),
                str(Path.home() / "Desktop"),
            ]


class ConfigManager:
    """Enhanced configuration manager with validation"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "nusyq.manifest.yaml")
        self.logger = logging.getLogger(__name__)
        self._config_cache: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file with error handling"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self._config_cache = yaml.safe_load(f) or {}
                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self._config_cache = self._get_default_config()
                self.save_config()
                self.logger.warning(f"Config file not found, created default: {self.config_path}")
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error: {e}")
            self._config_cache = self._get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self._config_cache = self._get_default_config()

    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config_cache, f, default_flow_style=False)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def get_service_config(self) -> ServiceConfig:
        """Get service configuration with defaults"""
        service_data = self._config_cache.get("service", {})
        return ServiceConfig(
            host=service_data.get("host", "localhost"),
            port=service_data.get("port", 8000),
            debug=service_data.get("debug", False),
            max_connections=service_data.get("max_connections", 100),
            timeout=service_data.get("timeout", 30),
        )

    def get_ollama_config(self) -> OllamaConfig:
        """Get Ollama configuration with defaults"""
        ollama_data = self._config_cache.get("ollama", {})
        return OllamaConfig(
            host=ollama_data.get("host", "localhost"),
            port=ollama_data.get("port", 11434),
            models=ollama_data.get("models", {}),
            timeout=ollama_data.get("timeout", 60),
        )

    def get_security_config(self) -> SecurityConfig:
        """Get security configuration with defaults"""
        security_data = self._config_cache.get("security", {})
        return SecurityConfig(
            allowed_paths=security_data.get("allowed_paths"),
            max_file_size=security_data.get("max_file_size", 10485760),
            rate_limit=security_data.get("rate_limit", 100),
            enable_auth=security_data.get("enable_auth", False),
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        keys = key.split(".")
        value = self._config_cache
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key"""
        keys = key.split(".")
        config = self._config_cache
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values"""
        self._config_cache.update(updates)
        self.save_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure"""
        return {
            "service": {
                "host": "localhost",
                "port": 8000,
                "debug": False,
                "max_connections": 100,
                "timeout": 30,
            },
            "ollama": {
                "host": "localhost",
                "port": 11434,
                "models": {
                    "qwen2.5-coder:7b": "Code generation and analysis",
                    "llama3.1:8b": "General purpose conversations",
                    "codellama:7b": "Code completion and debugging",
                    "phi3.5": "Lightweight reasoning tasks",
                },
                "timeout": 60,
            },
            "security": {
                "allowed_paths": [
                    str(Path.cwd()),
                    str(Path.home() / "Documents"),
                    str(Path.home() / "Desktop"),
                ],
                "max_file_size": 10485760,
                "rate_limit": 100,
                "enable_auth": False,
            },
            "chatdev": {"path": "./ChatDev", "config": "NuSyQ_Ollama", "timeout": 300},
            "jupyter": {"kernel": "python3", "timeout": 60, "max_code_length": 10000},
        }

    def validate_config(self) -> bool:
        """Validate configuration structure"""
        required_sections = ["service", "ollama", "security"]
        for section in required_sections:
            if section not in self._config_cache:
                self.logger.error(f"Missing required config section: {section}")
                return False
        return True

    def reload_config(self) -> None:
        """Reload configuration from file"""
        self.load_config()
