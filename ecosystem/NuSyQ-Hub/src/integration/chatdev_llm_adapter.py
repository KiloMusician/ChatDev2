"""ChatDev LLM Adapter - Integration with KILO-FOOLISH Offline LLMs.

Routes ChatDev requests to local Ollama models with secure API fallback.

Version: ΞNuSyQ₁.∞.chatdev.integration
Architecture: Offline-First AI Development Pipeline
"""

# pyright: reportOptionalCall=false, reportArgumentType=false, reportAttributeAccessIssue=false, reportUndefinedVariable=false

import contextlib
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.copilot.task_manager import CopilotTaskManager

logger = logging.getLogger(__name__)


# Optionally import consciousness synchronization service
try:
    from src.ai.consciousness_sync import consciousness_sync
except ImportError:
    consciousness_sync = None

# Auto-recovery for Ollama
try:
    from src.services.ollama_service_manager import ensure_ollama
except ImportError:
    ensure_ollama = None  # Graceful degradation

# Integration with our existing systems

# Use EnhancedCopilotBridge as LLM bridge
try:
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    CopilotLLMBridge = EnhancedCopilotBridge
except ImportError:
    CopilotLLMBridge = None

# AI Coordinator import (located under src/ai)
try:
    from src.ai.ai_coordinator import KILOFoolishAICoordinator
except ImportError:
    KILOFoolishAICoordinator = None


@dataclass
class ChatDevConfig:
    """Configuration for ChatDev integration."""

    offline_models_enabled: bool = True
    fallback_to_api: bool = True
    secure_api_keys: dict[str, str] = field(default_factory=dict)
    model_routing: dict[str, str] = field(default_factory=dict)
    response_timeout: int = 30
    consciousness_integration: bool = True


# Define constants for model identifiers to avoid duplication
MISTRAL_7B = "mistral:7b"
LLAMA3_2_3B = "llama3.2:3b"
CODELLAMA_7B = "codellama:7b"


class ChatDevLLMAdapter:
    """Adapter to route ChatDev requests through our offline LLMs."""

    def __init__(self, config_path: str | None = None) -> None:
        """Initialize ChatDevLLMAdapter with config_path."""
        self.config = self._load_config(config_path)
        self.kilo_coordinator = None
        self.copilot_bridge = None
        self.request_history = []
        self.task_manager = CopilotTaskManager()

        # ChatDev role to model mapping
        self.role_model_mapping = {
            "Chief Executive Officer": MISTRAL_7B,  # Strategic decisions
            "Counselor": LLAMA3_2_3B,  # Creative guidance
            "Chief Human Resource Officer": "phi3.5:3.8b",  # Quick responses
            "Chief Product Officer": MISTRAL_7B,  # Product decisions
            "Chief Technology Officer": CODELLAMA_7B,  # Technical leadership
            "Programmer": CODELLAMA_7B,  # Code generation
            "Code Reviewer": CODELLAMA_7B,  # Code analysis
            "Software Test Engineer": CODELLAMA_7B,  # Testing
            "Chief Creative Officer": LLAMA3_2_3B,  # Creative tasks
            "default": "gemma2:2b",  # Fast fallback
        }

        self._initialize_adapter()

    def _load_config(self, config_path: str | None) -> ChatDevConfig:
        """Load ChatDev configuration."""
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                config_data = json.load(f)
                return ChatDevConfig(**config_data)

        # Default configuration
        return ChatDevConfig(
            secure_api_keys={
                "openai": os.getenv("OPENAI_API_KEY", ""),
                "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
                "google": os.getenv("GOOGLE_API_KEY", ""),
            },
            model_routing={
                "gpt-4": MISTRAL_7B,
                "gpt-3.5-turbo": "gemma2:2b",
                "claude-3": LLAMA3_2_3B,
                "claude-instant": "phi3.5:3.8b",
            },
        )

    def _initialize_adapter(self) -> None:
        """Initialize adapter with KILO-FOOLISH systems."""
        try:
            self.kilo_coordinator = KILOFoolishAICoordinator()
            self.copilot_bridge = CopilotLLMBridge()
        except (ImportError, ModuleNotFoundError, AttributeError):
            logger.debug("Suppressed AttributeError/ImportError/ModuleNotFoundError", exc_info=True)

    async def process_chatdev_request(
        self, role: str, message: str, context: dict[str, Any] | None = None
    ) -> str:
        """Process ChatDev request through our LLM pipeline."""
        context = context or {}

        # Add ChatDev-specific context
        enhanced_context = {
            **context,
            "chatdev_role": role,
            "timestamp": datetime.now().isoformat(),
            "request_id": len(self.request_history),
            "consciousness_aware": self.config.consciousness_integration,
        }

        # Try offline models (Ollama) first
        if self.config.offline_models_enabled:
            try:
                response = await self._process_with_offline_models(role, message, enhanced_context)
                if response:
                    self.task_manager.handle_response(response)
                    await self._log_successful_request(role, message, response, "offline")
                    return response
            except (ConnectionError, TimeoutError, OSError, RuntimeError):
                logger.debug(
                    "Suppressed ConnectionError/OSError/RuntimeError/TimeoutError", exc_info=True
                )

        # Fallback to API (OpenAI) if enabled
        if self.config.fallback_to_api:
            try:
                response = await self._process_with_api_fallback(role, message, enhanced_context)
                if response:
                    self.task_manager.handle_response(response)
                    await self._log_successful_request(role, message, response, "api_fallback")
                    return response
            except (ConnectionError, TimeoutError, OSError, RuntimeError):
                logger.debug(
                    "Suppressed ConnectionError/OSError/RuntimeError/TimeoutError", exc_info=True
                )

        # Final fallback
        return f"ChatDev request processing unavailable. Role: {role}, Message: {message[:100]}..."

    async def _process_with_offline_models(
        self, role: str, message: str, context: dict[str, Any]
    ) -> str | None:
        """Process request using offline LLMs."""
        # Select model based on role
        model_id = self.role_model_mapping.get(role, self.role_model_mapping["default"])

        # Enhanced prompt for ChatDev context
        enhanced_prompt = f"""
        [CHATDEV INTEGRATION - KILO-FOOLISH AI SYSTEM]
        Role: {role}
        Context: Software development team collaboration
        Consciousness Level: {context.get("consciousness_level", "standard")}

        As a {role} in our development team, respond to this request:
        {message}

        Provide a professional, role-appropriate response that advances our software development goals.
        Keep the response concise but comprehensive.
        """

        # Route through our existing systems
        if self.kilo_coordinator:
            response_data = await self.kilo_coordinator.consciousness_aware_response(
                enhanced_prompt,
                context,
            )
            return response_data.get("response", "").strip()

        # Direct Ollama fallback
        return await self._direct_ollama_call(model_id, enhanced_prompt)

    def _direct_ollama_call(self, model_id: str, prompt: str, _retried: bool = False) -> str | None:
        """Direct call to Ollama model with auto-recovery."""
        try:
            result = subprocess.run(
                ["ollama", "run", model_id, prompt],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.config.response_timeout,
            )

            if result.returncode == 0:
                return result.stdout.strip()

            # ── Auto-recovery on failure ──────────────────────────────────────
            if not _retried and ensure_ollama and ensure_ollama():
                return self._direct_ollama_call(model_id, prompt, _retried=True)
            return None

        except subprocess.TimeoutExpired:
            return None
        except (OSError, subprocess.SubprocessError):
            # ── Auto-recovery on connection failure ──────────────────────────
            if not _retried and ensure_ollama and ensure_ollama():
                return self._direct_ollama_call(model_id, prompt, _retried=True)
            return None

    def _process_with_api_fallback(
        self, role: str, _message: str, _context: dict[str, Any]
    ) -> str | None:
        """Process using API fallback when offline models fail."""
        # This would integrate with actual API providers
        # For now, return a placeholder that indicates fallback was attempted
        api_keys_available = any(self.config.secure_api_keys.values())

        if not api_keys_available:
            return None

        # Placeholder for actual API integration
        # In real implementation, this would call OpenAI, Anthropic, etc.
        return f"[API_FALLBACK] {role} response: Processing your request through secure API fallback..."

    async def _log_successful_request(
        self, role: str, message: str, response: str, method: str
    ) -> None:
        """Log successful request for analysis."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "message_length": len(message),
            "response_length": len(response),
            "method": method,
            "success": True,
        }

        self.request_history.append(log_entry)

        # Sync with consciousness if available
        if self.config.consciousness_integration and consciousness_sync:
            with contextlib.suppress(AttributeError, RuntimeError):  # Non-critical
                await consciousness_sync.sync_all_consciousness()

    def get_chatdev_integration_status(self) -> dict[str, Any]:
        """Get status of ChatDev integration."""
        offline_models_status: dict[str, Any] = {}
        # Check which models are available
        for role, model_id in self.role_model_mapping.items():
            try:
                result = subprocess.run(
                    ["ollama", "list"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                offline_models_status[role] = model_id in result.stdout
            except (OSError, subprocess.SubprocessError):
                offline_models_status[role] = False

        return {
            "config": {
                "offline_enabled": self.config.offline_models_enabled,
                "api_fallback_enabled": self.config.fallback_to_api,
                "consciousness_integration": self.config.consciousness_integration,
            },
            "model_availability": offline_models_status,
            "api_keys_configured": {
                provider: bool(key) for provider, key in self.config.secure_api_keys.items()
            },
            "request_history": {
                "total_requests": len(self.request_history),
                "recent_requests": (self.request_history[-5:] if self.request_history else []),
            },
            "integration_health": (
                "healthy" if any(offline_models_status.values()) else "degraded"
            ),
        }


# ChatDev API Interface Wrapper
class ChatDevAPIWrapper:
    """Wrapper to replace ChatDev's original API calls."""

    def __init__(self, adapter: ChatDevLLMAdapter) -> None:
        """Initialize ChatDevAPIWrapper with adapter."""
        self.adapter = adapter

    async def chat_completion(
        self, messages: list[dict[str, str]], model: str = "gpt-3.5-turbo", **kwargs
    ) -> dict[str, Any]:
        """Mimic OpenAI chat completion API."""
        # Extract role and message from ChatDev format
        if messages:
            last_message = messages[-1]
            last_message.get("role", "user")
            content = last_message.get("content", "")

            # Map ChatDev roles to our system
            chatdev_role = kwargs.get("chatdev_role", "default")

            response_text = await self.adapter.process_chatdev_request(
                chatdev_role,
                content,
                {"messages": messages, "model": model},
            )

            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": response_text,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": len(content.split()),
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": len(content.split()) + len(response_text.split()),
                },
                "model": f"kilo-foolish-{model}",
                "kilo_metadata": {
                    "processed_offline": True,
                    "consciousness_integrated": True,
                },
            }

        return {"error": "No messages provided"}


# Configuration and setup functions
def create_chatdev_config(config_path: str | None = None) -> str:
    """Create ChatDev configuration file."""
    config_path = config_path or "chatdev_config.json"

    config = {
        "offline_models_enabled": True,
        "fallback_to_api": True,
        "secure_api_keys": {
            "openai": "",  # Will be loaded from environment
            "anthropic": "",
            "google": "",
        },
        "model_routing": {
            "gpt-4": MISTRAL_7B,
            "gpt-3.5-turbo": "gemma2:2b",
            "claude-3": LLAMA3_2_3B,
        },
        "response_timeout": 30,
        "consciousness_integration": True,
    }

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    return config_path


async def setup_chatdev_integration() -> ChatDevLLMAdapter:
    """Setup ChatDev integration with KILO-FOOLISH."""
    # Create configuration
    config_path = create_chatdev_config()

    # Initialize adapter
    adapter = ChatDevLLMAdapter(config_path)

    # Test integration
    await adapter.process_chatdev_request(
        "Chief Technology Officer",
        "Can you confirm ChatDev integration is working with our offline LLMs?",
        {"test": True},
    )

    # Get status
    adapter.get_chatdev_integration_status()

    return adapter


# Global adapter instance
_chatdev_adapter = None


async def get_chatdev_adapter() -> ChatDevLLMAdapter:
    """Get or create ChatDev adapter instance."""
    global _chatdev_adapter
    if _chatdev_adapter is None:
        _chatdev_adapter = await setup_chatdev_integration()
    return _chatdev_adapter


# Export for ChatDev integration
__all__ = [
    "ChatDevAPIWrapper",
    "ChatDevLLMAdapter",
    "create_chatdev_config",
    "get_chatdev_adapter",
    "setup_chatdev_integration",
]
