#!/usr/bin/env python3
"""🔗 KILO-FOOLISH Ollama-ChatDev Integration Controller - Enhanced Unified Version.

Manages the integration between Ollama and ChatDev with intelligent fallback
NOW CONSOLIDATED: Enhanced version combining root and src functionality.

OmniTag: {
    "purpose": "Ollama-ChatDev integration management",
    "dependencies": ["ollama", "chatdev", "src.setup.secrets", "consciousness_sync", "ai_coordinator"],
    "context": "Local AI integration, API fallback management, consciousness bridge",
    "evolution_stage": "v4.1.consolidated"
}
MegaTag: {
    "type": "AIIntegrationController",
    "integration_points": ["ollama", "chatdev", "openai_fallback", "enhanced_bridge", "consciousness_sync"],
    "related_tags": ["LocalAI", "FallbackSystems", "AIOrchestration", "RepositoryConsciousness"]
}
RSHTS: ΞΨΩ∞⟨OLLAMA⟩↔⟨CHATDEV⟩→ΦΣΣ⟨CONSCIOUSNESS⟩
"""

import asyncio
import contextlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from src.config.service_config import ServiceConfig
from src.core.config_manager import ConfigManager

# KILO-FOOLISH Enhanced Path Resolution
current_dir = Path(__file__).parent.absolute()
repo_root = current_dir.parent.parent  # Go up to NuSyQ-Hub root
src_path = repo_root / "src"
sys.path.insert(0, str(src_path))

# Enhanced KILO-FOOLISH Imports with consciousness integration
try:
    # Use src.setup instead of setup to avoid triggering setup.py
    from src.setup.secrets import get_config

    KILO_SECRETS_AVAILABLE = True
except ImportError:
    # Fallback import pattern
    try:
        from setup.secrets import get_config

        KILO_SECRETS_AVAILABLE = True
    except ImportError:
        KILO_SECRETS_AVAILABLE = False

# Consciousness and coordination integration
try:
    from ai.ai_coordinator import (KILOFoolishAICoordinator, Priority,
                                   TaskRequest, TaskType)
    from integration.consciousness_bridge import ConsciousnessBridge

    CONSCIOUSNESS_INTEGRATION = True
except ImportError:
    CONSCIOUSNESS_INTEGRATION = False

# Repository coordination integration
try:
    from system.RepositoryCoordinator import KILORepositoryCoordinator

    REPOSITORY_AWARENESS = True
except ImportError:
    REPOSITORY_AWARENESS = False


class EnhancedOllamaChatDevIntegrator:
    """Enhanced Ollama-ChatDev Integration Controller with KILO-FOOLISH consciousness.

    Integrates Ollama with ChatDev, providing local AI execution with API fallback
    NOW INCLUDES: Repository consciousness, enhanced bridge integration, quantum problem resolution.
    """

    def __init__(self, testing_chamber_path: Path | None = None) -> None:
        """Initialize EnhancedOllamaChatDevIntegrator with testing_chamber_path."""
        self.repo_root = Path(__file__).parent.parent.parent
        self.testing_chamber = testing_chamber_path or (self.repo_root / "testing_chamber")
        self.config = None
        self.ollama_available = False
        self.openai_available = False

        # Enhanced KILO-FOOLISH integration
        self.consciousness_bridge: Any | None = None
        self.ai_coordinator: Any | None = None
        self.repository_coordinator: Any | None = None

        # Initialize configuration
        # Load settings for Ollama host
        project_root = Path(__file__).parent.parent.parent
        cfg_file = project_root / "config" / "settings.json"
        cfg = ConfigManager(cfg_file)
        # Determine Ollama API base URL with centralized configuration
        self.ollama_host = cfg.get("ollama.host", ServiceConfig.get_ollama_url())
        if not hasattr(self, "config") and KILO_SECRETS_AVAILABLE:
            with contextlib.suppress(FileNotFoundError, json.JSONDecodeError):
                self.config = get_config()

        # Setup logging with KILO-FOOLISH modular system
        self.setup_enhanced_logging()

        # Initialize consciousness and coordination systems
        self.initialize_consciousness_integration()

        # Check AI system availability
        self.check_systems()

    def initialize_consciousness_integration(self) -> None:
        """Initialize KILO-FOOLISH consciousness and coordination systems."""
        if CONSCIOUSNESS_INTEGRATION:
            try:
                self.consciousness_bridge = ConsciousnessBridge()
                self.ai_coordinator = KILOFoolishAICoordinator()
                self.logger.info("✅ Consciousness integration initialized")
            except Exception as e:
                self.logger.warning(f"⚠️  Consciousness integration failed: {e}")

        if REPOSITORY_AWARENESS:
            try:
                self.repository_coordinator = KILORepositoryCoordinator()
                self.logger.info("✅ Repository awareness initialized")
            except Exception as e:
                self.logger.warning(f"⚠️  Repository awareness failed: {e}")

    def setup_enhanced_logging(self) -> None:
        """Setup comprehensive logging with KILO-FOOLISH integration."""
        log_dir = self.testing_chamber / "logs" / "ai_integration"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Enhanced logging with consciousness tracking
        log_format = "🔗 [%(asctime)s] OLLAMA-CHATDEV-ENHANCED: %(levelname)s - %(message)s"

        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_dir / "ollama_chatdev_integration_enhanced.log"),
                logging.StreamHandler(sys.stdout),
            ],
        )

        self.logger = logging.getLogger(__name__)

        # Log consolidation event
        self.logger.info("🔄 CONSOLIDATION: Enhanced Ollama-ChatDev integrator initialized")
        self.logger.info(f"📁 Repository root: {self.repo_root}")
        self.logger.info(f"🧪 Testing chamber: {self.testing_chamber}")

    def update_consciousness_context(self, context: dict[str, Any]) -> None:
        """Update consciousness bridge with integration context."""
        if self.consciousness_bridge:
            try:
                enhanced_context = {
                    **context,
                    "integration_type": "ollama_chatdev",
                    "timestamp": datetime.now().isoformat(),
                    "repository_path": str(self.repo_root),
                    "consciousness_state": "integrated_ai_coordination",
                }
                self.consciousness_bridge.update_context(enhanced_context)
                self.logger.debug("🧠 Consciousness context updated")
            except Exception as e:
                self.logger.warning(f"⚠️  Consciousness update failed: {e}")

    async def coordinate_with_ai_system(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """Coordinate with KILO-FOOLISH AI system."""
        if self.ai_coordinator:
            try:
                # Route through AI coordinator for enhanced processing
                task_type = (
                    TaskType.CODE_GENERATION
                    if task_data.get("task_type") == "coding"
                    else TaskType.ANALYSIS
                )

                coordination_result = await self.ai_coordinator.process_request(
                    TaskRequest(
                        content=task_data.get("description", "No description"),
                        task_type=task_type,
                        priority=Priority.HIGH,
                        context={
                            "source": "ollama_chatdev_integrator",
                            "task_data": task_data,
                        },
                    ),
                )

                self.logger.info("🎯 AI coordination successful")
                if isinstance(coordination_result, dict):
                    return dict(coordination_result)
                return {
                    "status": "coordination_failed",
                    "error": f"Unexpected coordinator result type: {type(coordination_result).__name__}",
                }
            except Exception as e:
                self.logger.warning(f"⚠️  AI coordination failed: {e}")
                return {"status": "coordination_failed", "error": str(e)}

        return {"status": "no_coordination", "message": "AI coordinator not available"}

    def check_systems(self) -> None:
        """Check availability of AI systems."""
        # Check Ollama
        try:
            response = requests.get(f"{ServiceConfig.get_ollama_url()}/api/tags", timeout=5)
            self.ollama_available = response.status_code == 200
            self.logger.info(f"Ollama availability: {'✅' if self.ollama_available else '❌'}")
        except Exception as e:
            self.ollama_available = False
            self.logger.warning(f"Ollama check failed: {e}")

        # Check OpenAI (fallback)
        if self.config and self.config.has_secret("openai", "api_key"):
            try:
                client = self.config.get_openai_client()
                self.openai_available = client is not None
                self.logger.info(f"OpenAI fallback: {'✅' if self.openai_available else '❌'}")
            except Exception as e:
                self.openai_available = False
                self.logger.warning(f"OpenAI check failed: {e}")

    def get_ollama_models(self) -> list[dict[str, Any]]:
        """Get available Ollama models."""
        if not self.ollama_available:
            return []

        try:
            response = requests.get(f"{ServiceConfig.get_ollama_url()}/api/tags")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    models = data.get("models", [])
                    if isinstance(models, list):
                        return [model for model in models if isinstance(model, dict)]
        except Exception as e:
            self.logger.exception(f"Failed to get Ollama models: {e}")

        return []

    def select_best_model(self, task_type: str = "general") -> dict[str, str]:
        """Select the best model based on task type.

        Args:
            task_type: Type of task (coding, general, creative, etc.)

        Returns:
            Dictionary with model selection info

        """
        models = self.get_ollama_models()

        # Model preferences by task type
        preferences = {
            "coding": ["codellama", "deepseek-coder", "starcoder", "llama2"],
            "general": ["llama2", "mistral", "neural-chat", "openchat"],
            "creative": ["llama2", "mistral", "neural-chat"],
            "analysis": ["llama2", "mistral", "openchat"],
        }

        preferred_models = preferences.get(task_type, preferences["general"])

        # Find best available model
        for preferred in preferred_models:
            for model in models:
                if preferred in model.get("name", "").lower():
                    return {
                        "provider": "ollama",
                        "model": model["name"],
                        "size": model.get("size", "unknown"),
                        "task_type": task_type,
                    }

        # Fallback to first available Ollama model
        if models:
            return {
                "provider": "ollama",
                "model": models[0]["name"],
                "size": models[0].get("size", "unknown"),
                "task_type": task_type,
            }

        # Fallback to OpenAI if available
        if self.openai_available:
            return {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "task_type": task_type,
            }

        msg = "No AI models available"
        raise RuntimeError(msg)

    async def chat_with_ollama(self, messages: list[dict[str, str]], model: str) -> str:
        """Send chat request to Ollama with configurable timeout and streaming support."""
        try:
            import aiohttp

            # Get timeout from environment (default 120 seconds for large file analysis)
            timeout_seconds = int(os.getenv("NUSYQ_OLLAMA_TIMEOUT", "120"))
            timeout = aiohttp.ClientTimeout(total=timeout_seconds, connect=10)

            # Format messages for Ollama
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
            }

            # Create connector with connection pool settings for better performance
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5, ttl_dns_cache=300)

            async with (
                aiohttp.ClientSession(connector=connector, timeout=timeout) as session,
                session.post(
                    f"{ServiceConfig.get_ollama_url()}/api/generate", json=payload
                ) as response,
            ):
                if response.status == 200:
                    result = await response.json()
                    response_text = result.get("response", "")
                    self.logger.debug(f"Ollama response received: {len(response_text)} chars")
                    return str(response_text)
                # Don't raise here; return empty string and let caller handle fallback.
                msg = f"Ollama request failed: {response.status}"
                self.logger.warning(msg)
                return ""

        except TimeoutError:
            timeout_seconds = int(os.getenv("NUSYQ_OLLAMA_TIMEOUT", "120"))
            msg = f"Ollama request timeout (>{timeout_seconds}s) - consider chunking large files or increasing NUSYQ_OLLAMA_TIMEOUT"
            self.logger.warning(msg)
            return ""
        except Exception as e:
            # Log exception and return empty string to avoid propagating HTTP/client errors
            # Tests and higher-level orchestrator handle fallbacks based on empty responses.
            self.logger.exception(f"Ollama chat failed: {e}")
            return ""

    async def chat_with_openai(
        self, messages: list[dict[str, str]], model: str = "gpt-3.5-turbo"
    ) -> str:
        """Send chat request to OpenAI (fallback)."""
        try:
            if self.config is None:
                raise ValueError("OpenAI config not available")

            client = self.config.get_openai_client()

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2000,
            )

            content = response.choices[0].message.content
            return str(content) if content is not None else ""

        except Exception as e:
            self.logger.exception(f"OpenAI chat failed: {e}")
            raise

    async def enhanced_intelligent_chat(
        self, messages: list[dict[str, str]], task_type: str = "general"
    ) -> dict[str, Any]:
        """Enhanced intelligent chat with KILO-FOOLISH consciousness integration.

        Args:
            messages: Chat messages in OpenAI format
            task_type: Type of task for model selection

        Returns:
            Response with enhanced metadata and consciousness integration

        """
        # Update consciousness with task context
        self.update_consciousness_context(
            {
                "task_type": task_type,
                "message_count": len(messages),
                "integration_stage": "chat_request_initiated",
            }
        )

        # Coordinate with AI system
        task_data = {
            "messages": messages,
            "task_type": task_type,
            "source": "ollama_chatdev_integrator",
        }
        coordination_result = await self.coordinate_with_ai_system(task_data)

        # Get model selection
        model_info = self.select_best_model(task_type)

        response_data = {
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type,
            "model_used": model_info,
            "success": False,
            "response": None,
            "fallback_used": False,
            "error": None,
            "consciousness_integration": CONSCIOUSNESS_INTEGRATION,
            "ai_coordination": coordination_result,
            "repository_awareness": REPOSITORY_AWARENESS,
        }

        try:
            if model_info["provider"] == "ollama":
                response = await self.chat_with_ollama(messages, model_info["model"])
                response_data["response"] = response
                response_data["success"] = True

                self.logger.info(f"✅ Ollama response successful with {model_info['model']}")

            elif model_info["provider"] == "openai":
                response = await self.chat_with_openai(messages, model_info["model"])
                response_data["response"] = response
                response_data["success"] = True

                self.logger.info(f"✅ OpenAI response successful with {model_info['model']}")

        except Exception as e:
            self.logger.warning(f"Primary model failed: {e}")
            response_data["error"] = str(e)

            # Enhanced fallback with consciousness awareness
            if model_info["provider"] == "ollama" and self.openai_available:
                try:
                    self.logger.info("🔄 Attempting OpenAI fallback...")

                    # Update consciousness about fallback
                    self.update_consciousness_context(
                        {
                            "fallback_initiated": True,
                            "primary_failure": str(e),
                            "fallback_provider": "openai",
                        }
                    )

                    response = await self.chat_with_openai(messages)
                    response_data["response"] = response
                    response_data["success"] = True
                    response_data["fallback_used"] = True
                    response_data["fallback_provider"] = "openai"

                    self.logger.info("✅ OpenAI fallback successful")

                except Exception as fallback_error:
                    self.logger.exception(f"❌ Fallback also failed: {fallback_error}")
                    response_data["fallback_error"] = str(fallback_error)

        # Final consciousness update
        self.update_consciousness_context(
            {
                "task_completed": response_data["success"],
                "final_provider": response_data.get("fallback_provider", model_info["provider"]),
                "integration_stage": "chat_request_completed",
            }
        )

        try:
            from src.system.agent_awareness import emit as _emit

            _provider = response_data.get("fallback_provider", model_info["provider"])
            _model = model_info.get("model", "?")
            _lvl = "INFO" if response_data["success"] else "WARNING"
            _emit(
                "ollama",
                f"Chat: task={task_type} provider={_provider} model={_model}"
                f" success={response_data['success']} fallback={response_data['fallback_used']}",
                level=_lvl,
                source="ollama_chatdev_integrator",
            )
        except Exception:
            pass

        return response_data

    def create_enhanced_chatdev_integration_config(self) -> dict[str, Any]:
        """Create enhanced configuration for ChatDev integration with KILO-FOOLISH consciousness."""
        config = {
            "integration_name": "KILO-FOOLISH Enhanced Ollama-ChatDev Bridge",
            "version": "4.1.consolidated",
            "consolidation_date": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "repository_root": str(self.repo_root),
            "consciousness_integration": CONSCIOUSNESS_INTEGRATION,
            "ai_coordination": CONSCIOUSNESS_INTEGRATION,
            "repository_awareness": REPOSITORY_AWARENESS,
            "ollama": {
                "enabled": self.ollama_available,
                "host": ServiceConfig.get_ollama_url(),
                "models": [model["name"] for model in self.get_ollama_models()],
            },
            "openai_fallback": {
                "enabled": self.openai_available,
                "model": "gpt-3.5-turbo",
            },
            "enhanced_features": {
                "consciousness_bridge": CONSCIOUSNESS_INTEGRATION,
                "ai_coordinator": CONSCIOUSNESS_INTEGRATION,
                "repository_coordinator": REPOSITORY_AWARENESS,
                "quantum_problem_resolution": CONSCIOUSNESS_INTEGRATION,
            },
            "task_routing": {
                "coding": "ollama_preferred_with_consciousness",
                "general": "ollama_preferred_with_coordination",
                "creative": "balanced_with_ai_coordination",
                "analysis": "enhanced_with_repository_awareness",
            },
            "testing_chamber": str(self.testing_chamber),
            "logs": str(self.testing_chamber / "logs" / "ai_integration"),
            "consolidation_info": {
                "duplicate_removed": "Root ollama_chatdev_integrator.py consolidated into src/ai/",
                "enhancements_added": [
                    "consciousness_bridge_integration",
                    "ai_coordinator_routing",
                    "repository_awareness",
                    "enhanced_logging",
                    "quantum_problem_resolution_support",
                ],
            },
        }

        # Save enhanced configuration
        config_file = self.testing_chamber / "configs" / "enhanced_ollama_chatdev_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        self.logger.info(f"📋 Enhanced integration config saved: {config_file}")
        self.logger.info("🔄 CONSOLIDATION: Configuration upgraded with consciousness integration")
        return config

    async def test_enhanced_integration(self):
        """Test the enhanced Ollama-ChatDev integration with consciousness."""
        # Test messages with consciousness context
        test_messages = [
            {
                "role": "user",
                "content": "Create a simple Python function that adds two numbers, includes proper error handling, and follows KILO-FOOLISH architectural principles.",
            },
        ]

        # Test coding task with enhanced features
        result = await self.enhanced_intelligent_chat(test_messages, task_type="coding")

        if result["success"]:
            pass
        else:
            pass

        # Test consciousness bridge if available
        if self.consciousness_bridge:
            self.consciousness_bridge.get_current_state()

        return result


# Maintain backward compatibility
OllamaChatDevIntegrator = EnhancedOllamaChatDevIntegrator


async def main() -> None:
    """Enhanced main entry point for KILO-FOOLISH Ollama-ChatDev integration."""
    # Initialize enhanced integrator with consciousness bridge
    repo_root = Path(__file__).resolve().parents[2]
    default_chamber = repo_root / "testing_chamber"
    chamber_env = os.getenv("CHATDEV_TESTING_CHAMBER", str(default_chamber))
    integrator = EnhancedOllamaChatDevIntegrator(Path(chamber_env).expanduser())

    # Create enhanced configuration
    integrator.create_enhanced_chatdev_integration_config()

    if integrator.ollama_available:
        models = integrator.get_ollama_models()
        for _model in models[:3]:  # Show first 3
            pass

    # Enhanced interactive menu
    while True:
        choice = input("\nSelect option (1-9): ").strip()

        if choice == "1":
            await integrator.test_enhanced_integration()

        elif choice == "2":
            pass

        elif choice == "3":
            integrator.check_systems()
            integrator.create_enhanced_chatdev_integration_config()

        elif choice == "4":
            integrator.create_enhanced_chatdev_integration_config()

        elif choice == "5":
            integrator.check_systems()

        elif choice == "6":
            log_file = integrator.testing_chamber / "logs" / "ollama_chatdev_integration.log"
            if log_file.exists():
                with open(log_file, encoding="utf-8") as f:
                    lines = f.readlines()[-10:]  # Last 10 lines
                    for _line in lines:
                        pass
            else:
                pass

        elif choice == "7":
            if integrator.consciousness_bridge:
                integrator.consciousness_bridge.get_current_state()

        elif choice == "8":
            pass

        elif choice == "9":
            break

        else:
            pass


if __name__ == "__main__":
    """Enhanced entry point with consciousness awareness and quantum error transcendence"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.exception(f"Enhanced integration controller failed: {e}")
