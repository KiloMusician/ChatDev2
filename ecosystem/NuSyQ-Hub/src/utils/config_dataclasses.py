#!/usr/bin/env python3
"""⚙️ KILO-FOOLISH Configuration Data Classes.

Structured configuration objects using dataclasses for type safety and validation.

OmniTag: {
    "purpose": "configuration_dataclasses",
    "type": "configuration_management",
    "evolution_stage": "v1.0_foundation"
}
MegaTag: {
    "scope": "config_objects",
    "integration_points": ["settings", "secrets", "api_config", "system_config"],
    "quantum_context": "configuration_consciousness"
}
RSHTS: ΞΨΩ∞⟨CONFIG_DATA⟩→ΦΣΣ
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .constants import AIModel, APIEndpoint, Defaults, LogLevel

logger = logging.getLogger(__name__)


@dataclass
class APIConfiguration:
    """Configuration for API connections."""

    provider: str  # "openai", "anthropic", "ollama"
    base_url: str
    api_key: str | None = None
    model: str = Defaults.DEFAULT_MODEL
    timeout: float = Defaults.TIMEOUT_SECONDS
    max_retries: int = Defaults.MAX_RETRIES
    rate_limit: int | None = None  # requests per minute
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.provider == "openai" and self.model not in AIModel.get_openai_models():
            logger.warning(f"Model {self.model} not in OpenAI model list")
        elif self.provider == "ollama" and self.model not in AIModel.get_ollama_models():
            logger.warning(f"Model {self.model} not in Ollama model list")
        elif self.provider == "anthropic" and self.model not in AIModel.get_claude_models():
            logger.warning(f"Model {self.model} not in Claude model list")

    @classmethod
    def from_env_vars(cls, provider: str) -> "APIConfiguration":
        """Create configuration from environment variables."""
        import os

        if provider == "openai":
            return cls(
                provider="openai",
                base_url=APIEndpoint.OPENAI_BASE.value,
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", AIModel.GPT_3_5_TURBO.value),
            )
        if provider == "anthropic":
            return cls(
                provider="anthropic",
                base_url=APIEndpoint.ANTHROPIC_BASE.value,
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=os.getenv("ANTHROPIC_MODEL", AIModel.CLAUDE_3_HAIKU.value),
            )
        if provider == "ollama":
            host = os.getenv("OLLAMA_HOST", Defaults.OLLAMA_HOST)
            port = os.getenv("OLLAMA_PORT", Defaults.OLLAMA_PORT)
            return cls(
                provider="ollama",
                base_url=f"http://{host}:{port}",
                model=os.getenv("OLLAMA_MODEL", AIModel.LLAMA2.value),
            )
        msg = f"Unknown provider: {provider}"
        raise ValueError(msg)


@dataclass
class LoggingConfiguration:
    """Configuration for logging system."""

    level: LogLevel = LogLevel.INFO
    format: str = Defaults.LOG_FORMAT
    date_format: str = Defaults.LOG_DATE_FORMAT
    file_path: Path | None = None
    max_file_size_mb: int = 10
    backup_count: int = 5
    console_logging: bool = True
    structured_logging: bool = True
    log_to_file: bool = True

    def configure_logger(self, name: str | None = None) -> logging.Logger:
        """Configure and return a logger with this configuration."""
        logger = logging.getLogger(name)
        logger.setLevel(self.level.value)

        # Clear existing handlers
        logger.handlers.clear()

        formatter = logging.Formatter(self.format, self.date_format)

        if self.console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        if self.log_to_file and self.file_path:
            from logging.handlers import RotatingFileHandler

            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                self.file_path,
                maxBytes=self.max_file_size_mb * 1024 * 1024,
                backupCount=self.backup_count,
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger


@dataclass
class PerformanceConfiguration:
    """Configuration for performance monitoring."""

    enable_monitoring: bool = True
    metrics_collection_interval: int = Defaults.METRICS_COLLECTION_INTERVAL
    health_check_interval: int = Defaults.HEALTH_CHECK_INTERVAL
    max_concurrent_tasks: int = Defaults.MAX_CONCURRENT_TASKS
    timeout_threshold: float = 30.0
    memory_threshold_mb: int = 1000
    cpu_threshold_percent: float = 80.0
    disk_threshold_percent: float = 85.0

    def is_resource_critical(
        self, memory_mb: float, cpu_percent: float, disk_percent: float
    ) -> bool:
        """Check if any resource is at critical levels."""
        return (
            memory_mb > self.memory_threshold_mb
            or cpu_percent > self.cpu_threshold_percent
            or disk_percent > self.disk_threshold_percent
        )


@dataclass
class ShutdownConfiguration:
    """Configuration for graceful shutdown."""

    graceful_timeout: float = Defaults.GRACEFUL_SHUTDOWN_TIMEOUT
    force_timeout: float = Defaults.FORCE_SHUTDOWN_TIMEOUT
    cleanup_timeout: float = 5.0
    save_state: bool = True
    log_progress: bool = True
    signal_handlers: list[int] = field(default_factory=lambda: [2, 15])  # SIGINT, SIGTERM

    def get_total_shutdown_time(self) -> float:
        """Get total time for complete shutdown."""
        return self.graceful_timeout + self.force_timeout + self.cleanup_timeout


@dataclass
class CacheConfiguration:
    """Configuration for caching system."""

    enabled: bool = True
    ttl_seconds: int = Defaults.CACHE_TTL
    max_size: int = Defaults.MAX_CACHE_SIZE
    cache_type: str = "memory"  # "memory", "redis", "file"
    cache_dir: Path | None = None
    compression: bool = False

    def __post_init__(self) -> None:
        """Validate cache configuration."""
        if self.cache_type == "file" and not self.cache_dir:
            self.cache_dir = Path.cwd() / "cache"
        elif self.cache_type == "file" and self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class RetryConfiguration:
    """Configuration for retry logic."""

    max_attempts: int = Defaults.MAX_RETRIES
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_status_codes: set[int] = field(default_factory=lambda: {500, 502, 503, 504, 429})
    retry_on_exceptions: set[type] = field(default_factory=lambda: {ConnectionError, TimeoutError})

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = min(self.base_delay * (self.exponential_base**attempt), self.max_delay)

        if self.jitter:
            import random

            delay = delay * (0.5 + random.random() * 0.5)

        return delay


@dataclass
class ChatDevConfiguration:
    """Configuration for ChatDev integration."""

    chatdev_path: Path
    default_model: str = AIModel.GPT_3_5_TURBO.value
    default_organization: str = "KiloFoolish"
    enable_monitoring: bool = True
    output_directory: Path | None = None
    template_directory: Path | None = None
    max_execution_time: int = 3600  # seconds

    def __post_init__(self) -> None:
        """Validate ChatDev configuration."""
        if not self.chatdev_path.exists():
            logger.warning(f"ChatDev path does not exist: {self.chatdev_path}")

        if self.output_directory and not self.output_directory.exists():
            self.output_directory.mkdir(parents=True, exist_ok=True)


@dataclass
class SecurityConfiguration:
    """Configuration for security settings."""

    encrypt_secrets: bool = True
    secrets_file: Path = Path("config/secrets.json")
    api_key_rotation_days: int = 90
    max_failed_attempts: int = 3
    lockout_duration_minutes: int = 15
    require_https: bool = True
    allowed_hosts: set[str] = field(default_factory=lambda: {"localhost", "127.0.0.1"})

    def is_host_allowed(self, host: str) -> bool:
        """Check if host is in allowed list."""
        return host in self.allowed_hosts


@dataclass
class SystemConfiguration:
    """Main system configuration combining all components."""

    api_configs: dict[str, APIConfiguration] = field(default_factory=dict)
    logging: LoggingConfiguration = field(default_factory=LoggingConfiguration)
    performance: PerformanceConfiguration = field(default_factory=PerformanceConfiguration)
    shutdown: ShutdownConfiguration = field(default_factory=ShutdownConfiguration)
    cache: CacheConfiguration = field(default_factory=CacheConfiguration)
    retry: RetryConfiguration = field(default_factory=RetryConfiguration)
    chatdev: ChatDevConfiguration | None = None
    security: SecurityConfiguration = field(default_factory=SecurityConfiguration)

    # System metadata
    config_version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    environment: str = "development"  # development, staging, production

    def __post_init__(self) -> None:
        """Initialize default API configurations if none provided."""
        if not self.api_configs:
            try:
                self.api_configs = {
                    "openai": APIConfiguration.from_env_vars("openai"),
                    "anthropic": APIConfiguration.from_env_vars("anthropic"),
                    "ollama": APIConfiguration.from_env_vars("ollama"),
                }
            except Exception as e:
                logger.warning(f"Failed to initialize API configs from env vars: {e}")

    def get_primary_api_config(self) -> APIConfiguration | None:
        """Get the primary API configuration (first available with API key)."""
        for config in self.api_configs.values():
            if config.api_key:
                return config
        return None

    def validate(self) -> list[str]:
        """Validate entire configuration and return list of issues."""
        issues: list[Any] = []
        # Check for at least one valid API configuration
        valid_apis = [cfg for cfg in self.api_configs.values() if cfg.api_key]
        if not valid_apis:
            issues.append("No valid API configuration found (missing API keys)")

        # Validate logging configuration
        if self.logging.log_to_file and not self.logging.file_path:
            issues.append("Log file path required when file logging is enabled")

        # Validate performance thresholds
        if self.performance.memory_threshold_mb <= 0:
            issues.append("Memory threshold must be positive")

        # Validate shutdown timeouts
        if self.shutdown.graceful_timeout <= 0:
            issues.append("Graceful shutdown timeout must be positive")

        return issues

    def save_to_file(self, file_path: Path) -> None:
        """Save configuration to JSON file."""
        config_dict = asdict(self)

        # Convert Path objects to strings for JSON serialization
        def convert_paths(obj):
            if isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_paths(item) for item in obj]
            if isinstance(obj, Path):
                return str(obj)
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, set):
                return list(obj)
            return obj

        config_dict = convert_paths(config_dict)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(config_dict, f, indent=2)

        logger.info(f"Configuration saved to {file_path}")

    @classmethod
    def load_from_file(cls, file_path: Path) -> "SystemConfiguration":
        """Load configuration from JSON file."""
        with open(file_path) as f:
            config_dict = json.load(f)

        # Convert string paths back to Path objects
        def convert_paths(obj, key=None):
            if isinstance(obj, dict):
                return {k: convert_paths(v, k) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_paths(item) for item in obj]
            if isinstance(obj, str) and key and ("path" in key.lower() or "dir" in key.lower()):
                return Path(obj)
            return obj

        config_dict = convert_paths(config_dict)

        # Reconstruct nested dataclass objects
        # This is simplified - in practice you'd want more robust deserialization
        return cls(**config_dict)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()


def create_default_config() -> SystemConfiguration:
    """Create a default system configuration."""
    from utils.constants import Paths

    return SystemConfiguration(
        logging=LoggingConfiguration(
            level=LogLevel.INFO,
            file_path=Paths.MAIN_LOG,
            console_logging=True,
        ),
        chatdev=ChatDevConfiguration(
            chatdev_path=Path(
                os.getenv("CHATDEV_PATH", "../ChatDev_CORE/ChatDev-main")
            ).expanduser(),
            output_directory=Paths.DATA_DIR / "chatdev_output",
        ),
        environment="development",
    )


def load_or_create_config(config_path: Path) -> SystemConfiguration:
    """Load configuration from file or create default if not exists."""
    if config_path.exists():
        try:
            config = SystemConfiguration.load_from_file(config_path)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.exception(f"Failed to load config from {config_path}: {e}")
            logger.info("Creating default configuration")

    config = create_default_config()
    config.save_to_file(config_path)
    return config


if __name__ == "__main__":
    # Demonstration of configuration system

    # Create default configuration
    config = create_default_config()

    # Validate configuration
    issues = config.validate()
    if issues:
        for _issue in issues:
            pass
    else:
        pass

    # Show retry calculation
    for attempt in range(4):
        delay = config.retry.calculate_delay(attempt)

    # Test performance monitoring
    config.performance.enable_monitoring = True
    is_critical = config.performance.is_resource_critical(1200, 85, 90)
