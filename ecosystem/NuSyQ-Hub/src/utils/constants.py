#!/usr/bin/env python3
"""🎯 KILO-FOOLISH Constants and Enums.

Centralized constants and enums for consistent usage across the system.

OmniTag: {
    "purpose": "constants_and_enums_system",
    "type": "configuration_management",
    "evolution_stage": "v1.0_foundation"
}
MegaTag: {
    "scope": "system_constants",
    "integration_points": ["model_names", "api_endpoints", "file_paths", "status_codes"],
    "quantum_context": "universal_constants"
}
RSHTS: ΞΨΩ∞⟨CONSTANTS⟩→ΦΣΣ
"""

import os
from enum import Enum, Flag, IntEnum, auto
from pathlib import Path
from typing import Any, ClassVar

_ServiceConfig: Any | None
_config_helper: Any | None

try:
    from src.config.service_config import ServiceConfig as _ServiceConfig
except ImportError:
    _ServiceConfig = None

try:
    from src.utils import config_helper as _config_helper
except ImportError:
    _config_helper = None


def _resolve_ollama_default() -> str:
    if _ServiceConfig is not None:
        url = _ServiceConfig.get_ollama_url()
        if isinstance(url, str):
            return url.rstrip("/")
    if _config_helper and hasattr(_config_helper, "get_ollama_host"):
        host_value = _config_helper.get_ollama_host()
        if isinstance(host_value, str):
            return host_value.rstrip("/")
    host = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST", "http://127.0.0.1")
    port = os.getenv("OLLAMA_PORT", "11434")
    return f"{str(host).rstrip('/')}:{port}"


OLLAMA_DEFAULT = _resolve_ollama_default()


class AIModel(Enum):
    """Available AI model names."""

    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"

    # Ollama models
    LLAMA2 = "llama2"
    LLAMA2_7B = "llama2:7b"
    LLAMA2_13B = "llama2:13b"
    CODELLAMA = "codellama"
    MISTRAL = "mistral"
    NEURAL_CHAT = "neural-chat"

    # Claude models
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"

    @classmethod
    def get_openai_models(cls) -> list[str]:
        """Get list of OpenAI model names."""
        return [
            cls.GPT_3_5_TURBO.value,
            cls.GPT_4.value,
            cls.GPT_4_TURBO.value,
            cls.GPT_4O.value,
            cls.GPT_4O_MINI.value,
        ]

    @classmethod
    def get_ollama_models(cls) -> list[str]:
        """Get list of Ollama model names."""
        return [
            cls.LLAMA2.value,
            cls.LLAMA2_7B.value,
            cls.LLAMA2_13B.value,
            cls.CODELLAMA.value,
            cls.MISTRAL.value,
            cls.NEURAL_CHAT.value,
        ]

    @classmethod
    def get_claude_models(cls) -> list[str]:
        """Get list of Claude model names."""
        return [
            cls.CLAUDE_3_HAIKU.value,
            cls.CLAUDE_3_SONNET.value,
            cls.CLAUDE_3_OPUS.value,
        ]


class TaskStatus(Enum):
    """Task execution status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    TIMEOUT = "timeout"

    def is_terminal(self) -> bool:
        """Check if this is a terminal status."""
        return self in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        }

    def is_active(self) -> bool:
        """Check if this is an active status."""
        return self in {TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.RETRYING}


class LogLevel(IntEnum):
    """Logging level constants."""

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class RepositoryType(Enum):
    """Repository type classifications."""

    KILO_FOOLISH = "kilo_foolish"
    NUSYQ_HUB = "nusyq_hub"
    CHATDEV_CORE = "chatdev_core"
    INTEGRATION = "integration"
    EXTERNAL = "external"


class FileExtension(Enum):
    """Common file extensions."""

    PYTHON = ".py"
    JSON = ".json"
    YAML = ".yaml"
    YML = ".yml"
    MARKDOWN = ".md"
    TEXT = ".txt"
    LOG = ".log"
    CONFIG = ".config"
    TOML = ".toml"
    INI = ".ini"


class APIEndpoint(Enum):
    """API endpoint constants."""

    OPENAI_BASE = "https://api.openai.com/v1"
    OPENAI_CHAT = "https://api.openai.com/v1/chat/completions"
    OPENAI_MODELS = "https://api.openai.com/v1/models"

    # Use ServiceConfig for Ollama endpoints if available; otherwise rely on env defaults
    OLLAMA_BASE = OLLAMA_DEFAULT
    OLLAMA_GENERATE = f"{OLLAMA_BASE}/api/generate"
    OLLAMA_CHAT = f"{OLLAMA_BASE}/api/chat"
    OLLAMA_MODELS = f"{OLLAMA_BASE}/api/tags"

    ANTHROPIC_BASE = "https://api.anthropic.com"
    ANTHROPIC_MESSAGES = "https://api.anthropic.com/v1/messages"

    @classmethod
    def get_ollama_base(cls) -> str:
        if _ServiceConfig is None:
            return cls.OLLAMA_BASE.value
        url = _ServiceConfig.get_ollama_url()
        return url if isinstance(url, str) else cls.OLLAMA_BASE.value

    @classmethod
    def get_ollama_generate(cls) -> str:
        base = cls.get_ollama_base()
        return f"{base}/api/generate"

    @classmethod
    def get_ollama_chat(cls) -> str:
        base = cls.get_ollama_base()
        return f"{base}/api/chat"

    @classmethod
    def get_ollama_models(cls) -> str:
        base = cls.get_ollama_base()
        return f"{base}/api/tags"


class SystemPriority(IntEnum):
    """System priority levels."""

    CRITICAL = 100
    HIGH = 75
    MEDIUM = 50
    LOW = 25
    BACKGROUND = 10


class ShutdownPhase(Enum):
    """Graceful shutdown phases."""

    RUNNING = "running"
    SHUTDOWN_REQUESTED = "shutdown_requested"
    GRACEFUL_STOPPING = "graceful_stopping"
    FORCE_STOPPING = "force_stopping"
    STOPPED = "stopped"


class ModuleType(Enum):
    """Module type classifications."""

    CORE = "core"
    INTEGRATION = "integration"
    AI = "ai"
    SYSTEM = "system"
    UTILS = "utils"
    INTERFACE = "interface"
    DIAGNOSTICS = "diagnostics"
    ORCHESTRATION = "orchestration"
    CONSCIOUSNESS = "consciousness"
    HEALING = "healing"
    ANALYSIS = "analysis"
    TAGGING = "tagging"
    ML = "ml"
    QUANTUM = "quantum"


class ConfigKey(Enum):
    """Configuration key constants."""

    OPENAI_API_KEY = "OPENAI_API_KEY"
    ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
    OLLAMA_HOST = "OLLAMA_HOST"
    OLLAMA_PORT = "OLLAMA_PORT"
    LOG_LEVEL = "LOG_LEVEL"
    MAX_RETRIES = "MAX_RETRIES"
    TIMEOUT_SECONDS = "TIMEOUT_SECONDS"
    DEFAULT_MODEL = "DEFAULT_MODEL"
    CHATDEV_PATH = "CHATDEV_PATH"
    WORKSPACE_ROOT = "WORKSPACE_ROOT"


class ErrorCode(IntEnum):
    """System error codes."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    CONFIG_ERROR = 2
    API_ERROR = 3
    NETWORK_ERROR = 4
    TIMEOUT_ERROR = 5
    AUTHENTICATION_ERROR = 6
    PERMISSION_ERROR = 7
    FILE_NOT_FOUND = 8
    INVALID_INPUT = 9
    RESOURCE_EXHAUSTED = 10


class QualityMetric(Enum):
    """Code quality metrics."""

    CYCLOMATIC_COMPLEXITY = "cyclomatic_complexity"
    CODE_COVERAGE = "code_coverage"
    DUPLICATE_CODE = "duplicate_code"
    TECHNICAL_DEBT = "technical_debt"
    MAINTAINABILITY_INDEX = "maintainability_index"
    SECURITY_HOTSPOTS = "security_hotspots"
    RELIABILITY_RATING = "reliability_rating"
    PERFORMANCE_SCORE = "performance_score"


class PerformanceCategory(Enum):
    """Performance monitoring categories."""

    PRODUCTIVITY = "productivity"
    SYSTEM_HEALTH = "system_health"
    API_LATENCY = "api_latency"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    ERROR_RATE = "error_rate"


class ComponentCapability(Flag):
    """Component capability flags."""

    MONITORING = auto()
    LOGGING = auto()
    CACHING = auto()
    RETRY_LOGIC = auto()
    GRACEFUL_SHUTDOWN = auto()
    HEALTH_CHECK = auto()
    METRICS_COLLECTION = auto()
    ERROR_HANDLING = auto()
    CONFIGURATION = auto()
    AUTHENTICATION = auto()


# Path constants
class Paths:
    """System path constants."""

    # Base directories
    WORKSPACE_ROOT = Path.cwd()
    SRC_DIR = WORKSPACE_ROOT / "src"
    DATA_DIR = WORKSPACE_ROOT / "data"
    LOGS_DIR = WORKSPACE_ROOT / "logs"
    CONFIG_DIR = WORKSPACE_ROOT / "config"
    DOCS_DIR = WORKSPACE_ROOT / "docs"
    TESTS_DIR = WORKSPACE_ROOT / "tests"
    SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"

    # Specific subdirectories
    CORE_DIR = SRC_DIR / "core"
    AI_DIR = SRC_DIR / "ai"
    UTILS_DIR = SRC_DIR / "utils"
    INTEGRATION_DIR = SRC_DIR / "integration"
    SYSTEM_DIR = SRC_DIR / "system"

    # Config files
    SETTINGS_JSON = CONFIG_DIR / "settings.json"
    SECRETS_JSON = CONFIG_DIR / "secrets.json"
    PYPROJECT_TOML = WORKSPACE_ROOT / "pyproject.toml"
    REQUIREMENTS_TXT = WORKSPACE_ROOT / "requirements.txt"

    # Log files
    MAIN_LOG = LOGS_DIR / "main.log"
    ERROR_LOG = LOGS_DIR / "error.log"
    PERFORMANCE_LOG = LOGS_DIR / "performance.log"

    # Agent session files
    AGENT_SESSIONS_DIR = DOCS_DIR / "Agent-Sessions"
    CURRENT_SESSION_LOG = AGENT_SESSIONS_DIR / f"SESSION_{Path(__file__).stat().st_mtime}.md"


# Default configurations
class Defaults:
    """Default configuration values."""

    # API settings
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 30
    DEFAULT_MODEL = AIModel.GPT_3_5_TURBO.value

    # Logging settings
    LOG_LEVEL = LogLevel.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Performance settings
    MAX_CONCURRENT_TASKS = 10
    HEALTH_CHECK_INTERVAL = 60  # seconds
    METRICS_COLLECTION_INTERVAL = 30  # seconds

    # Shutdown settings
    GRACEFUL_SHUTDOWN_TIMEOUT = 30.0  # seconds
    FORCE_SHUTDOWN_TIMEOUT = 10.0  # seconds

    # Cache settings
    CACHE_TTL = 3600  # seconds (1 hour)
    MAX_CACHE_SIZE = 1000

    # Ollama settings
    OLLAMA_HOST = OLLAMA_DEFAULT
    OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", 11434))

    # File settings
    MAX_FILE_SIZE_MB = 100
    BACKUP_RETENTION_DAYS = 30


# Message templates
class MessageTemplates:
    """Standard message templates."""

    STARTUP_SUCCESS = "🚀 {component} started successfully"
    STARTUP_FAILED = "❌ {component} failed to start: {error}"
    SHUTDOWN_REQUESTED = "🛑 Graceful shutdown requested for {component}"
    SHUTDOWN_COMPLETE = "✅ {component} shutdown completed"
    CONFIG_LOADED = "📋 Configuration loaded from {path}"
    CONFIG_ERROR = "❌ Configuration error in {path}: {error}"
    API_REQUEST_SUCCESS = "✅ API request to {endpoint} completed successfully"
    API_REQUEST_FAILED = "❌ API request to {endpoint} failed: {error}"
    RETRY_ATTEMPT = "🔄 Retry attempt {attempt}/{max_attempts} for {operation}"
    CACHE_HIT = "💾 Cache hit for key: {key}"
    CACHE_MISS = "📥 Cache miss for key: {key}"
    HEALTH_CHECK_PASS = "✅ Health check passed for {component}"
    HEALTH_CHECK_FAIL = "❌ Health check failed for {component}: {error}"


# Validation patterns
class ValidationPatterns:
    """Common validation patterns."""

    EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    UUID_REGEX = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    SEMVER_REGEX = r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
    API_KEY_REGEX = r"^[a-zA-Z0-9_-]{32,}$"

    # File name validation
    SAFE_FILENAME_CHARS: ClassVar[set] = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    )

    # Model name validation
    VALID_MODEL_NAMES: ClassVar[set] = {model.value for model in AIModel}


def get_all_constants() -> dict[str, Any]:
    """Get all constants as a dictionary for inspection."""
    constants: dict[str, Any] = {}
    # Add all enum values
    for enum_class in [
        AIModel,
        TaskStatus,
        LogLevel,
        RepositoryType,
        FileExtension,
        APIEndpoint,
        SystemPriority,
        ShutdownPhase,
        ModuleType,
        ConfigKey,
        ErrorCode,
        QualityMetric,
        PerformanceCategory,
    ]:
        constants[enum_class.__name__] = {member.name: member.value for member in enum_class}

    # Add other constants
    constants["Paths"] = {
        attr: getattr(Paths, attr) for attr in dir(Paths) if not attr.startswith("_")
    }
    constants["Defaults"] = {
        attr: getattr(Defaults, attr) for attr in dir(Defaults) if not attr.startswith("_")
    }
    constants["MessageTemplates"] = {
        attr: getattr(MessageTemplates, attr)
        for attr in dir(MessageTemplates)
        if not attr.startswith("_")
    }
    constants["ValidationPatterns"] = {
        attr: getattr(ValidationPatterns, attr)
        for attr in dir(ValidationPatterns)
        if not attr.startswith("_")
    }

    return constants


if __name__ == "__main__":
    # Demonstration of constants usage

    for _model in AIModel:
        pass

    for _status in TaskStatus:
        pass

    for _endpoint in APIEndpoint:
        pass

    capabilities = (
        ComponentCapability.MONITORING
        | ComponentCapability.LOGGING
        | ComponentCapability.GRACEFUL_SHUTDOWN
    )
