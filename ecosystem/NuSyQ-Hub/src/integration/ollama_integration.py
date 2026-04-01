"""Enhanced Ollama integration for KILO-FOOLISH AI Intermediary.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Async"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import collections
import importlib
import json
import logging
import os
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests

ConfigManager: Any | None = None
try:
    from src.core.config_manager import ConfigManager as _ConfigManager

    ConfigManager = _ConfigManager
except ImportError:
    ConfigManager = None

ServiceConfigClass: Any | None = None
try:
    _service_module = importlib.import_module("src.config.service_config")
    ServiceConfigClass = getattr(_service_module, "ServiceConfig", None)
except ImportError:
    ServiceConfigClass = None

get_ollama_host: Callable[[], str] | None = None
_get_ollama_host: Callable[[], str] | None
try:
    from src.utils.config_helper import get_ollama_host as _get_ollama_host
except (ImportError, ModuleNotFoundError):  # pragma: no cover - keep fallback minimal
    _get_ollama_host = None
get_ollama_host = _get_ollama_host

# Python 3.13 compatibility fix for deprecated collections ABC aliases
for _attr in ("MutableMapping", "Mapping", "Iterable", "Callable"):
    if not hasattr(collections, _attr):
        setattr(collections, _attr, getattr(collections.abc, _attr))

logger = logging.getLogger(__name__)


class KILOOllamaIntegration:
    """Enhanced Ollama integration for KILO-FOOLISH."""

    def __init__(self, host: str | None = None) -> None:
        """Initialize Ollama integration with flexible host configuration.

        Priority: explicit host arg > config/settings.json 'ollama.host' > env > ServiceConfig.
        """
        project_root = Path(__file__).parent.parent.parent
        cfg_host = None
        if ConfigManager is not None:
            cfg = ConfigManager(project_root / "config" / "settings.json")
            cfg_host = cfg.get("ollama.host", None)
        env_host = os.environ.get("OLLAMA_API_URL")
        service_host = ServiceConfigClass.get_ollama_url() if ServiceConfigClass else None
        self.host = host or cfg_host or env_host or service_host
        self.logger = logging.getLogger(__name__)
        self._availability_cache: bool | None = None

    def generate(
        self, model: str, prompt: str, timeout: float = 30.0, **kwargs: Any
    ) -> dict[str, Any] | None:
        """Generate text using Ollama."""
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs,
                },
                timeout=timeout,
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    return data
                return None
            self.logger.warning("Ollama request failed with status %s", response.status_code)
            return None
        except requests.RequestException as e:
            self.logger.exception("Ollama integration error: %s", e)
            return None

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Chat with Ollama using chat API."""
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={"model": model, "messages": messages, **kwargs},
                timeout=timeout,
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    return data
                return None
            self.logger.warning("Ollama chat failed with status %s", response.status_code)
            return None
        except requests.RequestException as e:
            self.logger.exception("Ollama chat error: %s", e)
            return None

    def is_available(self, timeout: float = 3.0) -> bool:
        """Check if Ollama server is reachable."""
        if self._availability_cache is not None:
            return self._availability_cache
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=timeout)
            self._availability_cache = response.status_code == 200
        except requests.RequestException:
            self._availability_cache = False
        try:
            from src.system.agent_awareness import emit as _emit

            _emit(
                "ollama",
                f"Ollama availability: {self._availability_cache} host={self.host}",
                level="INFO" if self._availability_cache else "WARNING",
                source="ollama_integration",
            )
        except Exception:
            pass
        return self._availability_cache


class OllamaIntegration(KILOOllamaIntegration):
    """Alias for backwards compatibility."""


_kilo_ollama_instance: KILOOllamaIntegration | None = None


def get_ollama_instance() -> KILOOllamaIntegration:
    """Return a singleton instance of KILOOllamaIntegration."""
    global _kilo_ollama_instance
    if _kilo_ollama_instance is None:
        _kilo_ollama_instance = KILOOllamaIntegration()
    return _kilo_ollama_instance


ollama = KILOOllamaIntegration()


class EnhancedOllamaHub:
    """Enhanced Ollama hub with model specialization."""

    def __init__(self, config_path: str = "config/ollama_models.json") -> None:
        """Initialize EnhancedOllamaHub with config_path."""
        self.config_path = Path(config_path)
        self.base_url = (
            (get_ollama_host() if get_ollama_host is not None else None)
            or (ServiceConfigClass.get_ollama_url() if ServiceConfigClass is not None else None)
            or os.getenv("OLLAMA_BASE_URL")
            or f"{os.getenv('OLLAMA_HOST', 'http://127.0.0.1')}:{os.getenv('OLLAMA_PORT', '11434')}"
        )
        self.models: dict[str, dict[str, Any]] = {}
        self.model_specializations = {
            "code_analysis": ["codellama", "deepseek-coder"],
            "general_conversation": ["mistral", "llama2"],
            "reasoning": ["phi", "mistral"],
            "creative": ["llama2", "mistral"],
            "debugging": ["codellama", "deepseek-coder"],
        }

    async def initialize(self) -> None:
        """Initialize the Ollama hub."""
        await self._load_model_config()
        await self._verify_models()

    async def _load_model_config(self) -> None:
        """Load model configuration."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                config = json.load(f)
                self.models = config.get("ollama", {}).get("models", {})
                self.base_url = config.get("ollama", {}).get("base_url", self.base_url)
        else:
            warnings.warn(
                f"Ollama model config not found at {self.config_path}. Using default configuration.",
                RuntimeWarning,
                stacklevel=2,
            )
            # Provide a minimal default so the hub can still function
            self.models = {
                "mistral": {"full_name": "mistral:latest"},
            }

    async def _verify_models(self) -> None:
        """Verify that configured models are available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                payload = response.json()
                if isinstance(payload, dict):
                    available = {model["name"] for model in payload.get("models", [])}
                else:
                    available = set()

                # Check our models
                working_models: dict[str, Any] = {}
                for name, config in self.models.items():
                    if any(config["full_name"] in avail for avail in available):
                        working_models[name] = config

                self.models = working_models

        except (ConnectionError, TimeoutError, OSError, AttributeError):
            logger.debug(
                "Suppressed AttributeError/ConnectionError/OSError/TimeoutError", exc_info=True
            )

    async def select_optimal_model(self, task_type: str, _complexity: int = 1) -> str | None:
        """Select the best model for a specific task."""
        # Get models that specialize in this task type
        specialized_models = self.model_specializations.get(task_type, [])

        # Filter to available models
        available_specialized = [m for m in specialized_models if m in self.models]

        if available_specialized:
            # For now, return the first available specialized model
            # Could add more sophisticated selection logic based on complexity
            return available_specialized[0]

        # Fallback to any available model
        if self.models:
            return next(iter(self.models.keys()))

        return None

    async def generate_response(
        self,
        prompt: str,
        model_name: str | None = None,
        task_type: str = "general_conversation",
    ) -> str:
        """Generate response using optimal model selection."""
        if not model_name:
            model_name = await self.select_optimal_model(task_type)

        if not model_name or model_name not in self.models:
            msg = f"Model not available: {model_name}"
            raise ValueError(msg)

        model_config = self.models[model_name]
        full_model_name = model_config["full_name"]

        try:
            payload = {
                "model": full_model_name,
                "prompt": prompt,
                "stream": False,
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict):
                    return str(result.get("response", ""))
                return str(result)
            msg = f"Ollama API error: {response.status_code}"
            raise Exception(msg)

        except Exception as e:
            msg = f"Failed to generate response: {e}"
            raise Exception(msg) from e
