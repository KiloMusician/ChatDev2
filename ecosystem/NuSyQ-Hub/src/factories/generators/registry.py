"""src/factories/generators/registry.py - Generator Registry.

Provides discovery and selection of code generators based on:
- Language requirements
- Provider availability
- Cost/speed preferences

Usage:
    from src.factories.generators import GeneratorRegistry, get_generator

    registry = GeneratorRegistry()

    # Get specific generator
    ollama = registry.get("ollama")

    # Get best generator for a language
    rust_gen = registry.get_for_language("rust")

    # Get all available generators
    available = registry.list_available()
"""

import contextlib
import logging
from typing import Any, Optional, cast

from src.factories.generators.base import AbstractGenerator

logger = logging.getLogger(__name__)


class GeneratorRegistry:
    """Registry for discovering and selecting code generators.

    Manages available generators and provides intelligent selection
    based on language, availability, and preferences.
    """

    _instance: Optional["GeneratorRegistry"] = None

    def __init__(self):
        """Initialize the registry with available generators."""
        self._generators: dict[str, AbstractGenerator] = {}
        self._generator_classes: dict[str, type[AbstractGenerator]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default generator implementations."""
        # Import here to avoid circular imports
        try:
            from src.factories.generators.ollama_generator import \
                OllamaGenerator

            self._generator_classes["ollama"] = OllamaGenerator
        except ImportError as e:
            logger.warning(f"Could not import OllamaGenerator: {e}")

        try:
            from src.factories.generators.claude_generator import \
                ClaudeGenerator

            self._generator_classes["claude"] = ClaudeGenerator
        except ImportError as e:
            logger.warning(f"Could not import ClaudeGenerator: {e}")

        try:
            from src.factories.generators.openai_generator import \
                OpenAIGenerator

            self._generator_classes["openai"] = OpenAIGenerator
        except ImportError as e:
            logger.warning(f"Could not import OpenAIGenerator: {e}")

        # ChatDev is handled specially - we try to detect the path
        try:
            from src.factories.ai_orchestrator import AIOrchestrator
            from src.factories.generators.chatdev_generator import \
                ChatDevGenerator

            # Try to detect ChatDev path via orchestrator
            orchestrator = AIOrchestrator()
            if orchestrator.chatdev_path:
                try:
                    chatdev_gen = ChatDevGenerator(orchestrator.chatdev_path)
                    self._generators["chatdev"] = cast(AbstractGenerator, chatdev_gen)
                    logger.debug(f"ChatDev registered at {orchestrator.chatdev_path}")
                except Exception as e:
                    logger.debug(f"ChatDev initialization failed: {e}")
            else:
                # Store class for manual instantiation with path
                self._generator_classes["chatdev"] = cast(type[AbstractGenerator], ChatDevGenerator)
                logger.debug("ChatDev path not detected, manual path required")
        except ImportError as e:
            logger.debug(f"ChatDevGenerator not available: {e}")

    def register(self, name: str, generator: AbstractGenerator) -> None:
        """Register a generator instance.

        Args:
            name: Provider name (e.g., 'ollama')
            generator: Generator instance
        """
        self._generators[name.lower()] = generator
        logger.info(f"Registered generator: {name}")

    def register_class(self, name: str, generator_class: type[AbstractGenerator]) -> None:
        """Register a generator class (lazy instantiation).

        Args:
            name: Provider name
            generator_class: Generator class (not instance)
        """
        self._generator_classes[name.lower()] = generator_class

    def get(self, name: str, **kwargs) -> AbstractGenerator:
        """Get a generator by name.

        Creates the generator if not already instantiated.

        Args:
            name: Provider name (ollama, claude, openai, chatdev)
            **kwargs: Arguments passed to generator constructor

        Returns:
            Generator instance

        Raises:
            KeyError: If generator not found
        """
        name = name.lower()

        # Return cached instance if exists and no kwargs
        if name in self._generators and not kwargs:
            return self._generators[name]

        # Create new instance from class
        if name in self._generator_classes:
            generator_class = self._generator_classes[name]
            try:
                generator = generator_class(**kwargs)
                # Cache if no custom kwargs
                if not kwargs:
                    self._generators[name] = generator
                return generator
            except Exception as e:
                raise ValueError(f"Failed to create {name} generator: {e}") from e

        raise KeyError(
            f"Generator '{name}' not found. Available: {', '.join(self._generator_classes.keys())}"
        )

    def get_or_none(self, name: str) -> AbstractGenerator | None:
        """Get a generator or None if not available."""
        try:
            gen = self.get(name)
            if gen.is_available():
                return gen
            return None
        except (KeyError, Exception):
            return None

    def get_for_language(
        self,
        language: str,
        prefer_local: bool = True,
    ) -> AbstractGenerator | None:
        """Get the best available generator for a language.

        Args:
            language: Language name (e.g., 'rust')
            prefer_local: Prefer local generators (Ollama) over API

        Returns:
            Best available generator or None
        """
        language = language.lower()

        # Try to use language registry for provider recommendations
        try:
            from src.factories.languages import get_language_registry

            registry = get_language_registry()
            lang = registry.get(language)
            preferred_providers = lang.providers
        except Exception:
            # Default order
            preferred_providers = ["ollama", "claude", "openai"]

        if prefer_local and "ollama" in preferred_providers:
            # Ensure Ollama is tried first if available
            preferred_providers = ["ollama"] + [p for p in preferred_providers if p != "ollama"]

        # Try each provider in order
        for provider in preferred_providers:
            gen = self.get_or_none(provider)
            if gen and gen.supports_language(language):
                return gen

        return None

    def list_all(self) -> list[str]:
        """Get list of all registered generator names."""
        return list(set(self._generators.keys()) | set(self._generator_classes.keys()))

    def list_available(self) -> list[str]:
        """Get list of currently available generators."""
        available = []
        for name in self.list_all():
            try:
                gen = self.get(name)
                if gen.is_available():
                    available.append(name)
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)
        return available

    def list_for_language(self, language: str) -> list[str]:
        """Get list of generators that support a language."""
        language = language.lower()
        supporting = []
        for name in self.list_all():
            try:
                gen = self.get(name)
                if gen.supports_language(language):
                    supporting.append(name)
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)
        return supporting

    def get_capabilities(self, name: str) -> dict[str, Any]:
        """Get capabilities for a generator."""
        gen = self.get(name)
        return gen.get_capabilities()

    def get_all_capabilities(self) -> dict[str, dict[str, Any]]:
        """Get capabilities for all generators."""
        caps = {}
        for name in self.list_all():
            with contextlib.suppress(Exception):
                caps[name] = self.get_capabilities(name)
        return caps

    @classmethod
    def get_instance(cls) -> "GeneratorRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None


def get_generator(name: str, **kwargs) -> AbstractGenerator:
    """Convenience function to get a generator.

    Args:
        name: Provider name (ollama, claude, openai)
        **kwargs: Arguments for generator constructor

    Returns:
        Generator instance
    """
    return GeneratorRegistry.get_instance().get(name, **kwargs)


def get_generator_for_language(language: str) -> AbstractGenerator | None:
    """Get the best available generator for a language.

    Args:
        language: Language name

    Returns:
        Best generator or None
    """
    return GeneratorRegistry.get_instance().get_for_language(language)


def list_available_generators() -> list[str]:
    """Get list of available generator names."""
    return GeneratorRegistry.get_instance().list_available()
