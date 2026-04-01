"""KILO-FOOLISH AI Coordination Layer.

Intelligently routes tasks between multiple AI assistants.

---
Standard Library Typing Import Workaround:
To avoid shadowing by legacy src/typing.py, temporarily remove src from sys.path before importing typing.
This ensures all downstream imports (dataclasses, etc.) get the stdlib typing module.
Legacy compatibility is preserved; this block is idempotent and safe for repeated imports.
OmniTag: [typing_workaround, stdlib_preservation, legacy_compat]
MegaTag: [SYSTEM_CORE, IMPORT_HEALING, RECURSIVE_BOOT]
---
"""

import logging
import sys as _sys

logger = logging.getLogger(__name__)

_removed_src = False
_src_path = None
try:
    import os

    _src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if _src_path in _sys.path:
        _sys.path.remove(_src_path)
        _removed_src = True
except (OSError, RuntimeError) as _e:
    logger.warning(f"[KILO-FOOLISH] Typing import workaround failed: {_e}")
finally:
    if _removed_src and _src_path:
        _sys.path.insert(0, _src_path)


import asyncio
import importlib
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, cast

# Centralized service configuration using factory pattern
from src.utils.config_factory import get_service_config

SecretsManager: Any
try:
    _secrets_module = importlib.import_module("src.core.secrets")
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    _secrets_module = importlib.import_module("KILO_Core.secrets")
SecretsManager = _secrets_module.SecretsManager

# Import our AI integrations
from .ollama_integration import get_ollama_instance


def _load_ollama_host() -> Callable[[], str] | None:
    try:
        from src.utils.config_helper import get_ollama_host as _get_ollama_host

        if callable(_get_ollama_host):
            return cast(Callable[[], str], _get_ollama_host)
        return None
    except (ImportError, ModuleNotFoundError):
        return None


get_ollama_host = _load_ollama_host()

# Initialize SecretsManager
secrets_manager = SecretsManager()

# Example usage - get Ollama host from config factory
_config = get_service_config()
service_config = _config._config if _config else None
ollama_host = secrets_manager.get_config(
    "ollama_host",
    (get_ollama_host() if callable(get_ollama_host) else None)
    or (
        service_config.get_ollama_url()
        if service_config and hasattr(service_config, "get_ollama_url")
        else None
    )
    or os.getenv("OLLAMA_BASE_URL")
    or f"{os.getenv('OLLAMA_HOST', 'http://127.0.0.1')}:{os.getenv('OLLAMA_PORT', '11434')}",
)

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available")


class TaskType(Enum):
    """ZetaSet Quantum-Infused Task Types for AI Coordination.

    Each task type is tagged for modularity, quantum context, and best practices.
    """

    CODE_GENERATION = "code_generation"  # Generate code from description
    CODE_REVIEW = "code_review"  # Review code for quality
    DEBUGGING = "debugging"  # Debug errors and issues
    DOCUMENTATION = "documentation"  # Generate documentation
    PLANNING = "planning"  # Project planning and strategy
    ANALYSIS = "analysis"  # Deep analysis and insights
    CREATIVE = "creative"  # Creative writing, ideation
    CONVERSATION = "conversation"  # General chat, Q&A
    SYSTEM_ADMIN = "system_admin"  # System administration tasks
    SECURITY_REVIEW = "security_review"  # Security assessment
    TESTING = "testing"  # Automated and manual testing
    REFACTORING = "refactoring"  # Code refactoring
    PERFORMANCE_OPTIMIZATION = "performance_optimization"  # Optimize code performance
    DATA_CLEANING = "data_cleaning"  # Clean and preprocess data
    DATA_VISUALIZATION = "data_visualization"  # Visualize data
    MODEL_TRAINING = "model_training"  # Train ML models
    MODEL_EVALUATION = "model_evaluation"  # Evaluate ML models
    MODEL_DEPLOYMENT = "model_deployment"  # Deploy models
    PROMPT_ENGINEERING = "prompt_engineering"  # Engineer prompts for LLMs
    CONTEXT_SYNTHESIS = "context_synthesis"  # Synthesize context for tasks
    MEMORY_AUGMENTATION = "memory_augmentation"  # Enhance memory/context
    QUANTUM_SIMULATION = "quantum_simulation"  # Simulate quantum systems
    SYMBOLIC_REASONING = "symbolic_reasoning"  # Symbolic AI reasoning
    TAGGING = "tagging"  # Tag code, data, or context
    LEXEME_GENERATION = "lexeme_generation"  # Generate musical lexemes
    FEEDBACK_LOOP = "feedback_loop"  # Recursive feedback
    SELF_HEALING = "self_healing"  # Automated self-healing
    ERROR_HANDLING = "error_handling"  # Robust error handling
    LOGGING = "logging"  # Modular logging
    CONTEXT_PROPAGATION = "context_propagation"  # Propagate context
    TOOL_INTEGRATION = "tool_integration"  # Integrate external tools
    GAME_ENGINE_HOOK = "game_engine_hook"  # Game engine integration
    MEMORY_PALACE = "memory_palace"  # Memory palace operations
    REPOSITORY_SCAN = "repository_scan"  # Scan repository for files
    SYSTEM_AUDIT = "system_audit"  # Audit system health
    IMPORT_VALIDATION = "import_validation"  # Validate imports
    FILE_ORGANIZATION = "file_organization"  # Organize files
    CONTEXT_COMPRESSION = "context_compression"  # Compress context
    MULTI_AGENT_COORDINATION = "multi_agent_coordination"  # Coordinate agents
    AI_ORCHESTRATION = "ai_orchestration"  # Orchestrate AI models
    CONSCIOUSNESS_EVOLUTION = "consciousness_evolution"  # Track consciousness
    SESSION_TRACKING = "session_tracking"  # Track sessions
    SYSTEM_MONITORING = "system_monitoring"  # Monitor system metrics
    DASHBOARD_GENERATION = "dashboard_generation"  # Generate dashboards
    API_INTEGRATION = "api_integration"  # Integrate APIs
    SECRETS_MANAGEMENT = "secrets_management"  # Manage secrets
    ENVIRONMENT_SETUP = "environment_setup"  # Setup environments
    VIRTUAL_ENV_MANAGEMENT = "virtual_env_management"  # Manage virtual envs
    PACKAGE_MANAGEMENT = "package_management"  # Manage packages
    EXTENSION_MANAGEMENT = "extension_management"  # Manage IDE extensions
    USER_PROFILE_ENHANCEMENT = "user_profile_enhancement"  # Enhance user profiles
    REPOSITORY_CONSCIOUSNESS = "repository_consciousness"  # Cultivate repo knowledge


class AIProvider(Enum):
    """Available AI providers."""

    COPILOT = "copilot"
    OLLAMA = "ollama"
    OPENAI = "openai"
    AUTO = "auto"


class Priority(Enum):
    """Task priorities."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskRequest:
    """AI task request structure."""

    task_type: TaskType
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.MEDIUM
    preferred_provider: AIProvider = AIProvider.AUTO
    timeout: int = 60
    requires_privacy: bool = False
    max_tokens: int = 2048
    temperature: float = 0.7
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResponse:
    """AI task response structure."""

    content: str
    provider: AIProvider
    model: str
    task_type: TaskType
    execution_time: float
    tokens_used: int | None = None
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class AIProviderInterface(ABC):
    """Abstract interface for AI providers."""

    @abstractmethod
    async def process_task(self, request: TaskRequest) -> TaskResponse:
        """Process a task request."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""

    @abstractmethod
    def get_capabilities(self) -> list[TaskType]:
        """Get supported task types."""

    @abstractmethod
    def estimate_cost(self, request: TaskRequest) -> float:
        """Estimate relative cost for this request."""


class OllamaProvider(AIProviderInterface):
    """Ollama AI provider implementation."""

    def __init__(self) -> None:
        """Initialize OllamaProvider."""
        self.ollama: Any | None = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize Ollama connection."""
        try:
            self.ollama = get_ollama_instance()
        except (ConnectionError, OSError, RuntimeError) as e:
            logging.exception("Failed to initialize Ollama: %s", e)
            self.ollama = None

    async def process_task(self, request: TaskRequest) -> TaskResponse:
        """Process task using Ollama."""
        start_time = time.time()

        if not self.is_available():
            return TaskResponse(
                content="",
                provider=AIProvider.OLLAMA,
                model="unavailable",
                task_type=request.task_type,
                execution_time=0,
                error="Ollama not available",
            )

        try:
            # Ensure ollama instance is initialized
            if self.ollama is None:
                msg = "Ollama integration is not initialized."
                raise RuntimeError(msg)
            # Check for required methods
            for method_name in [
                "code_assistance",
                "project_planning",
                "conversation_mode",
            ]:
                if not hasattr(self.ollama, method_name):
                    msg = f"Ollama integration missing method: {method_name}"
                    raise AttributeError(msg)
            # Route based on task type
            if request.task_type in [
                TaskType.CODE_GENERATION,
                TaskType.CODE_REVIEW,
                TaskType.DEBUGGING,
            ]:
                result = self.ollama.code_assistance(request.content)
            elif request.task_type in [TaskType.PLANNING, TaskType.ANALYSIS]:
                result = self.ollama.project_planning(request.content)
            else:
                result = self.ollama.conversation_mode(request.content)

            execution_time = time.time() - start_time

            return TaskResponse(
                content=result,
                provider=AIProvider.OLLAMA,
                model="ollama-local",
                task_type=request.task_type,
                execution_time=execution_time,
                confidence=0.8,  # Ollama generally reliable for local tasks
            )

        except (ConnectionError, ValueError, RuntimeError, OSError) as e:
            execution_time = time.time() - start_time
            return TaskResponse(
                content="",
                provider=AIProvider.OLLAMA,
                model="ollama-local",
                task_type=request.task_type,
                execution_time=execution_time,
                error=str(e),
            )

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        if self.ollama is None:
            self._initialize()

        if self.ollama is None or not hasattr(self.ollama, "client"):
            return False
        return bool(self.ollama.client._health_check())

    def get_capabilities(self) -> list[TaskType]:
        """Get Ollama capabilities."""
        return [
            TaskType.CODE_GENERATION,
            TaskType.CODE_REVIEW,
            TaskType.DEBUGGING,
            TaskType.PLANNING,
            TaskType.ANALYSIS,
            TaskType.CONVERSATION,
            TaskType.CREATIVE,
        ]

    def estimate_cost(self, request: TaskRequest) -> float:
        """Estimate cost (Ollama is local, so cost is just compute time)."""
        base_cost = len(request.content) / 1000  # Simple length-based estimate
        if request.task_type in [TaskType.CODE_GENERATION, TaskType.ANALYSIS]:
            base_cost *= 1.5  # More complex tasks cost more
        return base_cost


class OpenAIProvider(AIProviderInterface):
    """OpenAI provider implementation."""

    def __init__(self) -> None:
        """Initialize OpenAIProvider."""
        self.client: Any | None = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize OpenAI client."""
        if not OPENAI_AVAILABLE:
            return

        try:
            from KILO_Core.secrets import config

            api_key = config.get_secret("openai", "api_key")
            if api_key and "your-" not in api_key:
                self.client = openai.OpenAI(api_key=api_key)
        except (ImportError, KeyError, ValueError) as e:
            logging.exception("Failed to initialize OpenAI: %s", e)
            self.client = None

    async def process_task(self, request: TaskRequest) -> TaskResponse:
        """Process task using OpenAI."""
        start_time = time.time()

        if not self.is_available():
            return TaskResponse(
                content="",
                provider=AIProvider.OPENAI,
                model="unavailable",
                task_type=request.task_type,
                execution_time=0,
                error="OpenAI not available",
            )

        try:
            # Select model based on task complexity
            model = self._select_model(request.task_type, request.priority)

            # Create system prompt based on task type
            system_prompt = self._create_system_prompt(request.task_type)

            # Ensure self.client is initialized and has the correct method
            if self.client is None or not hasattr(self.client, "chat"):
                msg = "OpenAI client is not properly initialized or missing 'chat' attribute."
                raise RuntimeError(msg)

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.content},
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                timeout=request.timeout,
            )

            execution_time = time.time() - start_time

            # Safely extract content, fallback to empty string if None
            content = ""
            if response and hasattr(response, "choices") and response.choices:
                message_content = getattr(response.choices[0].message, "content", "")
                if message_content is not None:
                    content = message_content

            return TaskResponse(
                content=content,
                provider=AIProvider.OPENAI,
                model=model,
                task_type=request.task_type,
                execution_time=execution_time,
                tokens_used=(
                    response.usage.total_tokens
                    if hasattr(response, "usage") and response.usage
                    else None
                ),
                confidence=0.9,  # OpenAI generally high quality
            )

        except (ConnectionError, ValueError, RuntimeError) as e:
            execution_time = time.time() - start_time
            return TaskResponse(
                content="",
                provider=AIProvider.OPENAI,
                model=model if "model" in locals() else "unknown",
                task_type=request.task_type,
                execution_time=execution_time,
                error=str(e),
            )

    def _select_model(self, task_type: TaskType, priority: Priority) -> str:
        """Select appropriate OpenAI model."""
        if priority == Priority.CRITICAL or task_type in [
            TaskType.PLANNING,
            TaskType.ANALYSIS,
        ]:
            return "gpt-4"
        if task_type in [TaskType.CODE_GENERATION, TaskType.CODE_REVIEW]:
            return "gpt-3.5-turbo"
        return "gpt-3.5-turbo"

    def _create_system_prompt(self, task_type: TaskType) -> str:
        """Create system prompt based on task type."""
        base_prompt = "You are an AI assistant for the KILO-FOOLISH development project."

        prompts = {
            TaskType.CODE_GENERATION: (
                f"{base_prompt} Focus on creating clean, well-documented, "
                "enterprise-grade code with proper error handling."
            ),
            TaskType.CODE_REVIEW: (
                f"{base_prompt} Review code for best practices, security, performance, and maintainability."
            ),
            TaskType.DEBUGGING: (
                f"{base_prompt} Help debug issues with detailed analysis and practical solutions."
            ),
            TaskType.PLANNING: (
                f"{base_prompt} Provide strategic planning and architectural guidance for AI-assisted development."
            ),
            TaskType.ANALYSIS: (
                f"{base_prompt} Perform deep analysis with actionable insights and recommendations."
            ),
            TaskType.SECURITY_REVIEW: (
                f"{base_prompt} Focus on security best practices, vulnerability assessment, and secure coding."
            ),
        }

        return prompts.get(task_type, base_prompt)

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        if self.client is None:
            self._initialize()

        return self.client is not None

    def get_capabilities(self) -> list[TaskType]:
        """Get OpenAI capabilities."""
        return list(TaskType)  # OpenAI supports all task types

    def estimate_cost(self, request: TaskRequest) -> float:
        """Estimate OpenAI cost."""
        token_estimate = len(request.content) / 4  # Rough token estimation
        if request.task_type in [TaskType.PLANNING, TaskType.ANALYSIS]:
            return token_estimate * 0.03  # Higher cost for complex tasks
        return token_estimate * 0.002  # Estimated cost in USD per token for standard tasks


class CopilotProvider(AIProviderInterface):
    """Copilot provider (simulation - real integration via IDE)."""

    async def process_task(self, request: TaskRequest) -> TaskResponse:
        """Simulate Copilot interaction."""
        start_time = time.time()

        # Copilot works best with IDE integration
        suggestion = self._generate_copilot_suggestion(request)

        execution_time = time.time() - start_time

        return TaskResponse(
            content=suggestion,
            provider=AIProvider.COPILOT,
            model="copilot",
            task_type=request.task_type,
            execution_time=execution_time,
            confidence=0.85,
        )

    def _generate_copilot_suggestion(self, request: TaskRequest) -> str:
        """Generate suggestion for using Copilot."""
        suggestions = {
            TaskType.CODE_GENERATION: (
                "💡 Copilot Suggestion: Open your IDE and type a comment "
                f"describing: '{request.content[:100]}...' then let Copilot "
                "generate the code."
            ),
            TaskType.CODE_REVIEW: (
                "💡 Copilot Suggestion: Highlight the code in your IDE and ask "
                "Copilot to review it. Use Ctrl+I to open inline chat."
            ),
            TaskType.DEBUGGING: (
                "💡 Copilot Suggestion: Place cursor on error line and use "
                "Copilot Chat to explain the issue and get fixes."
            ),
            TaskType.DOCUMENTATION: (
                "💡 Copilot Suggestion: Select the function/class and ask "
                "Copilot to generate documentation in your preferred format."
            ),
            TaskType.PLANNING: (
                "🧠 Copilot Suggestion: Outline your project goals in a markdown "
                "file, then ask Copilot to generate a project plan."
            ),
            TaskType.ANALYSIS: (
                "🔍 Copilot Suggestion: Paste your data or code and ask Copilot for deep analysis and insights."
            ),
            TaskType.CREATIVE: (
                "🎨 Copilot Suggestion: Start a creative writing prompt and let Copilot continue the story or idea."
            ),
            TaskType.CONVERSATION: (
                "💬 Copilot Suggestion: Use Copilot Chat for general Q&A and brainstorming."
            ),
            TaskType.SYSTEM_ADMIN: (
                "🖥️ Copilot Suggestion: Describe your system admin task and let Copilot generate scripts or commands."
            ),
            TaskType.SECURITY_REVIEW: (
                "🛡️ Copilot Suggestion: Ask Copilot to review your code for security vulnerabilities and best practices."
            ),
            TaskType.TESTING: (
                "🧪 Copilot Suggestion: Highlight your code and ask Copilot to generate unit or integration tests."
            ),
            TaskType.REFACTORING: (
                "♻️ Copilot Suggestion: Select legacy code and ask Copilot to refactor for clarity and performance."
            ),
            TaskType.PERFORMANCE_OPTIMIZATION: (
                "⚡ Copilot Suggestion: Ask Copilot to suggest optimizations for speed and resource usage."
            ),
            TaskType.DATA_CLEANING: (
                "🧹 Copilot Suggestion: Paste your dataset and ask Copilot to generate cleaning scripts."
            ),
            TaskType.DATA_VISUALIZATION: (
                "📊 Copilot Suggestion: Describe your data and ask Copilot to generate visualization code."
            ),
            TaskType.MODEL_TRAINING: (
                "🤖 Copilot Suggestion: Provide your training data and ask Copilot to generate model training code."
            ),
            TaskType.MODEL_EVALUATION: (
                "📝 Copilot Suggestion: Ask Copilot to generate evaluation metrics and analysis for your model."
            ),
            TaskType.MODEL_DEPLOYMENT: (
                "🚀 Copilot Suggestion: Ask Copilot to generate deployment scripts for your ML model."
            ),
            TaskType.PROMPT_ENGINEERING: (
                "🗣️ Copilot Suggestion: Describe your LLM task and ask Copilot to engineer an optimal prompt."
            ),
            TaskType.CONTEXT_SYNTHESIS: (
                "🔗 Copilot Suggestion: Ask Copilot to synthesize context from multiple files or sources."
            ),
            TaskType.MEMORY_AUGMENTATION: (
                "🧠 Copilot Suggestion: Request Copilot to enhance memory/context handling in your code."
            ),
            TaskType.QUANTUM_SIMULATION: (
                "🌀 Copilot Suggestion: Ask Copilot to generate code for simulating quantum systems."
            ),
            TaskType.SYMBOLIC_REASONING: (
                "🔣 Copilot Suggestion: Request Copilot to implement symbolic AI reasoning logic."
            ),
            TaskType.TAGGING: (
                "🏷️ Copilot Suggestion: Ask Copilot to add tags to code, data, or context for traceability."
            ),
            TaskType.LEXEME_GENERATION: (
                "🎵 Copilot Suggestion: Request Copilot to generate musical lexemes for context synthesis."
            ),
            TaskType.FEEDBACK_LOOP: (
                "🔄 Copilot Suggestion: Ask Copilot to implement recursive feedback loops in your system."
            ),
            TaskType.SELF_HEALING: (
                "🩹 Copilot Suggestion: Request Copilot to add self-healing logic to your scripts."
            ),
            TaskType.ERROR_HANDLING: (
                "❗ Copilot Suggestion: Ask Copilot to add robust error handling to your code."
            ),
            TaskType.LOGGING: (
                "📝 Copilot Suggestion: Request Copilot to implement modular logging throughout your codebase."
            ),
            TaskType.CONTEXT_PROPAGATION: (
                "🌊 Copilot Suggestion: Ask Copilot to propagate context between modules and functions."
            ),
            TaskType.TOOL_INTEGRATION: (
                "🔌 Copilot Suggestion: Request Copilot to integrate external tools or APIs."
            ),
            TaskType.GAME_ENGINE_HOOK: (
                "🎮 Copilot Suggestion: Ask Copilot to generate hooks for game engine integration."
            ),
            TaskType.MEMORY_PALACE: (
                "🏰 Copilot Suggestion: Request Copilot to implement memory palace operations for context retention."
            ),
            TaskType.REPOSITORY_SCAN: (
                "🔎 Copilot Suggestion: Ask Copilot to scan the repository for files and dependencies."
            ),
            TaskType.SYSTEM_AUDIT: (
                "🩺 Copilot Suggestion: Request Copilot to audit system health and configuration."
            ),
            TaskType.IMPORT_VALIDATION: (
                "✅ Copilot Suggestion: Ask Copilot to validate and fix import statements in your code."
            ),
            TaskType.FILE_ORGANIZATION: (
                "🗂️ Copilot Suggestion: Request Copilot to organize files and folders for clarity."
            ),
            TaskType.CONTEXT_COMPRESSION: (
                "🧬 Copilot Suggestion: Ask Copilot to compress and summarize context for LLMs."
            ),
            TaskType.MULTI_AGENT_COORDINATION: (
                "🤝 Copilot Suggestion: Request Copilot to coordinate multiple agents for complex tasks."
            ),
            TaskType.AI_ORCHESTRATION: (
                "🎼 Copilot Suggestion: Ask Copilot to orchestrate AI models for collaborative workflows."
            ),
            TaskType.CONSCIOUSNESS_EVOLUTION: (
                "🌌 Copilot Suggestion: Request Copilot to track and evolve system consciousness."
            ),
            TaskType.SESSION_TRACKING: (
                "📅 Copilot Suggestion: Ask Copilot to implement session tracking and management."
            ),
            TaskType.SYSTEM_MONITORING: (
                "📈 Copilot Suggestion: Request Copilot to monitor system metrics and performance."
            ),
            TaskType.DASHBOARD_GENERATION: (
                "📊 Copilot Suggestion: Ask Copilot to generate dashboards for system status."
            ),
            TaskType.API_INTEGRATION: (
                "🔗 Copilot Suggestion: Request Copilot to integrate external APIs for extended functionality."
            ),
            TaskType.SECRETS_MANAGEMENT: (
                "🔒 Copilot Suggestion: Ask Copilot to implement secrets management and secure storage."
            ),
            TaskType.ENVIRONMENT_SETUP: (
                "⚙️ Copilot Suggestion: Request Copilot to automate environment setup scripts."
            ),
            TaskType.VIRTUAL_ENV_MANAGEMENT: (
                "🐍 Copilot Suggestion: Ask Copilot to manage virtual environments for Python projects."
            ),
            TaskType.PACKAGE_MANAGEMENT: (
                "📦 Copilot Suggestion: Request Copilot to manage package installation and updates."
            ),
            TaskType.EXTENSION_MANAGEMENT: (
                "🧩 Copilot Suggestion: Ask Copilot to manage IDE extensions and plugins."
            ),
            TaskType.USER_PROFILE_ENHANCEMENT: "👤 Copilot Suggestion: Request Copilot to enhance user profiles and personalization.",
            TaskType.REPOSITORY_CONSCIOUSNESS: "🧠 Copilot Suggestion: Ask Copilot to cultivate repository knowledge and context.",
        }
        return suggestions.get(
            request.task_type,
            f"💡 Copilot Suggestion: Use Copilot Chat in your IDE for: {request.content}",
        )

    def get_capabilities(self) -> list[TaskType]:
        """Get Copilot capabilities."""
        return [
            TaskType.CODE_GENERATION,
            TaskType.CODE_REVIEW,
            TaskType.DEBUGGING,
            TaskType.DOCUMENTATION,
        ]

    def estimate_cost(self, _request: TaskRequest) -> float:
        """Copilot has subscription cost, so usage cost is low."""
        return 0.1  # Low cost per request

    def is_available(self) -> bool:
        """Copilot is always available (simulated)."""
        return True


class LLMRegistry:
    """Dynamic registry for LLM/agent providers."""

    def __init__(self) -> None:
        """Initialize LLMRegistry."""
        self._providers: dict[str, AIProviderInterface] = {}
        self._lock = threading.Lock()
        # Track busy-state for providers (tests expect is_busy / set_busy)
        self._busy: dict[str, bool] = {}

    def register(self, name: str, provider: AIProviderInterface) -> None:
        with self._lock:
            self._providers[name] = provider

    def unregister(self, name: str) -> None:
        with self._lock:
            if name in self._providers:
                del self._providers[name]

    def get(self, name: str) -> AIProviderInterface | None:
        return self._providers.get(name)

    def all(self) -> dict[str, AIProviderInterface]:
        return dict(self._providers)

    def available(self) -> dict[str, AIProviderInterface]:
        return {k: v for k, v in self._providers.items() if v.is_available()}

    def is_busy(self, name: str) -> bool:
        """Return whether a registered provider is currently marked busy."""
        return bool(self._busy.get(name, False))

    def set_busy(self, name: str, busy: bool) -> None:
        """Mark a provider as busy or not busy."""
        with self._lock:
            if name in self._providers:
                self._busy[name] = bool(busy)

    def available_nonbusy(self) -> list[str]:
        """Return list of provider names that are available and not busy."""
        return [
            name
            for name, prov in self._providers.items()
            if prov.is_available() and not self._busy.get(name, False)
        ]


class AICoordinator:
    def __init__(self) -> None:
        """Initialize AICoordinator."""
        self.secrets_manager = SecretsManager()
        # Defensive: use dict() to avoid pylint complaining about attribute presence
        self.config = dict(getattr(self.secrets_manager, "_secrets_cache", {}) or {})

        # Initialize core provider objects (used by coordination logic)
        self._provider_objects = {
            AIProvider.OLLAMA: OllamaProvider(),
            AIProvider.OPENAI: OpenAIProvider(),
            AIProvider.COPILOT: CopilotProvider(),
        }

        # User-registered providers (simple dict) for lightweight routing tests
        # Kept separate from core providers to avoid breaking existing logic
        self.providers: dict[str, dict[str, Any]] = {}

        # Initialize task tracking
        self.task_history: list[Any] = []
        self.performance_metrics: dict[str, Any] = {}

        # Initialize llm_registry
        self.llm_registry = LLMRegistry()

    async def process_chatdev_task(self, request: TaskRequest) -> TaskResponse:
        """Robust ChatDev/Ollama routing logic with recursive healing, context propagation, and cultivation hooks.

        OmniTag: [chatdev_task, ollama_fallback, procedural_healing, context_propagation]
        MegaTag: [AI_ORCHESTRATION, RECURSIVE_EVOLUTION].
        """
        response = None
        # Try Ollama first
        if self._provider_objects[AIProvider.OLLAMA].is_available():
            response = await self._provider_objects[AIProvider.OLLAMA].process_task(request)
            # If Ollama fails, fallback to OpenAI, then Copilot
            if response.error:
                if self._provider_objects[AIProvider.OPENAI].is_available():
                    response = await self._provider_objects[AIProvider.OPENAI].process_task(request)
                elif self._provider_objects[AIProvider.COPILOT].is_available():
                    response = await self._provider_objects[AIProvider.COPILOT].process_task(
                        request
                    )
        # Ollama not available, fallback to OpenAI, then Copilot
        elif self._provider_objects[AIProvider.OPENAI].is_available():
            response = await self._provider_objects[AIProvider.OPENAI].process_task(request)
        else:
            response = await self._provider_objects[AIProvider.COPILOT].process_task(request)

        # Procedural healing/cultivation for ChatDev
        if response and response.error:
            # Attempt self-healing by retrying with Copilot and logging
            response = await self._provider_objects[AIProvider.COPILOT].process_task(request)
            logging.warning(
                "ChatDev task failed, attempted procedural healing via Copilot fallback."
            )

        # Cultivate system if requested
        if request.context.get("cultivate_system"):
            logging.info("Cultivating system via ChatDev procedural request.")
            # Optionally trigger bridge/orchestra here
            try:
                from src.copilot.copilot_enhancement_bridge import \
                    cultivate_bridge_understanding

                cultivate_bridge_understanding(
                    [
                        f"ChatDev task: {request.content}",
                        f"Provider used: {response.provider if response else 'None'}",
                    ],
                    ["Procedural healing triggered", "Context propagated"],
                )
            except (ImportError, AttributeError, RuntimeError) as e:
                logging.warning("Bridge cultivation hook failed: %s", e)

        # Record metrics and propagate context
        self._record_performance(request, response)
        # Optionally propagate context to memory system, logging, etc.
        try:
            from src.copilot.copilot_enhancement_bridge import \
                get_enhanced_bridge

            bridge = get_enhanced_bridge()
            bridge.store_context_memory(
                {
                    "query": request.content,
                    "provider": str(response.provider) if response else "None",
                    "error": response.error if response else None,
                    "timestamp": time.time(),
                    "context": request.context,
                }
            )
        except (ImportError, AttributeError, ValueError) as e:
            logging.debug("Context propagation to bridge failed: %s", e)

        return response

    async def process_request(self, request: TaskRequest) -> TaskResponse:
        """Process an AI request with intelligent routing and ChatDev/Orchestration support."""
        # Special handling for ChatDev tasks
        if request.context.get("chatdev_task"):
            return await self.process_chatdev_task(request)

        # Auto-select provider if not specified
        if request.preferred_provider == AIProvider.AUTO:
            selected_provider = self._select_optimal_provider(request)
        else:
            selected_provider = request.preferred_provider

        # Execute task
        provider = self._provider_objects[selected_provider]
        response = await provider.process_task(request)

        # Handle fallback if primary provider failed
        if response.error and selected_provider != AIProvider.COPILOT:
            fallback_provider = self._get_fallback_provider(selected_provider, request)
            if fallback_provider:
                logging.warning(
                    "Primary provider %s failed, trying fallback %s",
                    selected_provider,
                    fallback_provider,
                )
                response = await self._provider_objects[fallback_provider].process_task(request)

        # Record metrics
        self._record_performance(request, response)

        return response

    def _select_optimal_provider(self, request: TaskRequest) -> AIProvider:
        """Select the best provider for this request."""
        # Privacy requirements force local processing
        if request.requires_privacy:
            if self._provider_objects[AIProvider.OLLAMA].is_available():
                return AIProvider.OLLAMA
            return AIProvider.COPILOT

        # Critical tasks prefer OpenAI for quality
        if request.priority == Priority.CRITICAL:
            if self._provider_objects[AIProvider.OPENAI].is_available():
                return AIProvider.OPENAI
            if self._provider_objects[AIProvider.OLLAMA].is_available():
                return AIProvider.OLLAMA
            return AIProvider.COPILOT

        # Task-specific routing
        task_routing = {
            TaskType.CODE_GENERATION: [
                AIProvider.COPILOT,
                AIProvider.OLLAMA,
                AIProvider.OPENAI,
            ],
            TaskType.CODE_REVIEW: [
                AIProvider.COPILOT,
                AIProvider.OPENAI,
                AIProvider.OLLAMA,
            ],
            TaskType.DEBUGGING: [
                AIProvider.COPILOT,
                AIProvider.OLLAMA,
                AIProvider.OPENAI,
            ],
            TaskType.PLANNING: [
                AIProvider.OPENAI,
                AIProvider.OLLAMA,
                AIProvider.COPILOT,
            ],
            TaskType.ANALYSIS: [
                AIProvider.OPENAI,
                AIProvider.OLLAMA,
                AIProvider.COPILOT,
            ],
            TaskType.CREATIVE: [
                AIProvider.OLLAMA,
                AIProvider.OPENAI,
                AIProvider.COPILOT,
            ],
            TaskType.SECURITY_REVIEW: [
                AIProvider.OPENAI,
                AIProvider.OLLAMA,
                AIProvider.COPILOT,
            ],
        }

        preferred_order = task_routing.get(
            request.task_type,
            [AIProvider.OLLAMA, AIProvider.OPENAI, AIProvider.COPILOT],
        )

        # Return first available provider in preferred order
        for provider in preferred_order:
            if self._provider_objects[provider].is_available():
                return provider

        # Fallback to Copilot (always available)
        return AIProvider.COPILOT

    def _get_fallback_provider(
        self, failed_provider: AIProvider, _request: TaskRequest
    ) -> AIProvider | None:
        """Get fallback provider when primary fails."""
        fallback_chain = {
            AIProvider.OPENAI: AIProvider.OLLAMA,
            AIProvider.OLLAMA: AIProvider.COPILOT,
            AIProvider.COPILOT: None,
        }

        fallback = fallback_chain.get(failed_provider)
        if fallback and self._provider_objects[fallback].is_available():
            return fallback
        return None

    def _record_performance(self, request: TaskRequest, response: TaskResponse) -> None:
        """Record performance metrics for future optimization."""
        provider_key = response.provider.value
        task_key = request.task_type.value

        if provider_key not in self.performance_metrics:
            self.performance_metrics[provider_key] = {}

        if task_key not in self.performance_metrics[provider_key]:
            self.performance_metrics[provider_key][task_key] = {
                "total_requests": 0,
                "successful_requests": 0,
                "avg_execution_time": 0,
                "avg_confidence": 0,
            }

        metrics = self.performance_metrics[provider_key][task_key]
        metrics["total_requests"] += 1

        if not response.error:
            metrics["successful_requests"] += 1
            # Update running averages
            metrics["avg_execution_time"] = (
                metrics["avg_execution_time"] + response.execution_time
            ) / 2
            metrics["avg_confidence"] = (metrics["avg_confidence"] + response.confidence) / 2

        # Store task in history (keep last 100)
        self.task_history.append(
            {
                "request": request,
                "response": response,
                "timestamp": time.time(),
            }
        )

        if len(self.task_history) > 100:
            self.task_history.pop(0)

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status."""
        status: dict[str, Any] = {
            "providers": {},
            "performance": self.performance_metrics,
            "recent_tasks": len(self.task_history),
        }

        for provider_type, provider in self._provider_objects.items():
            status["providers"][provider_type.value] = {
                "available": provider.is_available(),
                "capabilities": [cap.value for cap in provider.get_capabilities()],
            }

        return status

    async def health_check(self) -> bool:
        """Perform system health check."""
        available_providers = 0

        for provider in self._provider_objects.values():
            if provider.is_available():
                available_providers += 1

        return available_providers > 0

    # ------------------------------------------------------------------
    # Lightweight provider management for generated tests
    # ------------------------------------------------------------------
    def register_provider(self, name: str, capabilities: dict[str, Any]) -> None:
        """Register a simple provider with capabilities for routing tests."""
        self.providers[name] = capabilities

    def route_task(self, task: tuple[str, str, int]) -> tuple[str, tuple[str, str, int]]:
        """Route a task to the highest-priority provider matching type.

        Args:
            task: Tuple of (task_type, content, priority)

        Returns:
            (provider_name, task)

        Raises:
            ValueError: if no provider matches the task type.
        """
        if len(task) != 3:
            raise ValueError("Invalid task format. Expected (task_type, content, priority).")

        task_type, content, priority = task

        # Filter providers that match the task type
        candidates = [
            (name, caps) for name, caps in self.providers.items() if caps.get("type") == task_type
        ]

        if not candidates:
            raise ValueError("No provider available for the given task type.")

        # Choose provider with highest 'priority' value (default 0)
        selected_name, _ = max(candidates, key=lambda item: item[1].get("priority", 0))

        return selected_name, (task_type, content, priority)


# Global coordinator instance
_coordinator = None


def get_coordinator() -> AICoordinator:
    """Get or create global coordinator instance."""
    global _coordinator
    if _coordinator is None:
        _coordinator = AICoordinator()
    return _coordinator


# Convenience functions for common tasks
async def ai_code_help(
    prompt: str, language: str = "python", priority: Priority = Priority.MEDIUM
) -> str:
    """Get AI assistance for coding."""
    request = TaskRequest(
        task_type=TaskType.CODE_GENERATION,
        content=f"Language: {language}\nTask: {prompt}",
        priority=priority,
    )

    coordinator = get_coordinator()
    response = await coordinator.process_request(request)

    return response.content


async def ai_review_code(code: str, language: str = "python") -> str:
    """Get AI code review."""
    request = TaskRequest(
        task_type=TaskType.CODE_REVIEW,
        content=f"Review this {language} code:\n\n{code}",
        priority=Priority.HIGH,
    )

    coordinator = get_coordinator()
    response = await coordinator.process_request(request)

    return response.content


async def ai_debug_help(error: str, code: str = "", context: str = "") -> str:
    """Get AI debugging assistance."""
    content = f"Error: {error}"
    if code:
        content += f"\n\nCode:\n{code}"
    if context:
        content += f"\n\nContext: {context}"

    request = TaskRequest(
        task_type=TaskType.DEBUGGING,
        content=content,
        priority=Priority.HIGH,
    )

    coordinator = get_coordinator()
    response = await coordinator.process_request(request)

    return response.content


async def ai_plan_project(goal: str, context: str = "") -> str:
    """Get AI project planning assistance."""
    content = f"Goal: {goal}"
    if context:
        content += f"\n\nContext: {context}"

    request = TaskRequest(
        task_type=TaskType.PLANNING,
        content=content,
        priority=Priority.MEDIUM,
    )

    coordinator = get_coordinator()
    response = await coordinator.process_request(request)

    return response.content


if __name__ == "__main__":
    # Test the coordination system
    async def test_coordinator() -> None:
        coordinator = get_coordinator()

        # Test health check
        healthy = await coordinator.health_check()
        logger.info(f"System healthy: {healthy}")

        # Test status
        status = coordinator.get_system_status()
        logger.info(f"System status: {status}")

        # Test code generation
        response = await ai_code_help("Create a function to validate email addresses")
        logger.info(f"Code help response: {response[:200]}...")

    asyncio.run(test_coordinator())

# KILO-FOOLISH Compatibility Aliases
KILOFoolishAICoordinator = AICoordinator
