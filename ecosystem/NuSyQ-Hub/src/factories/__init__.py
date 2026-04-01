"""NuSyQ Factory System - Game/Program Development Suite.

This module provides a general-purpose factory for generating games, programs,
and packages using multi-AI orchestration (ChatDev, Ollama, Claude, OpenAI).

Key Components:
- ProjectFactory: Template-based project generation (sync)
- AsyncProjectFactory: Async project generation with parallel file support
- ArtifactRegistry: Version control and build tracking
- AIOrchestrator: Intelligent AI provider selection
- LanguageRegistry: Multi-language support (8 languages)
- GeneratorRegistry: Pluggable AI code generators
- Templates: Reusable project definitions (game, CLI, library)

Usage:
    # Sync generation
    from src.factories import ProjectFactory
    factory = ProjectFactory()
    project = factory.create("CyberTerminal", template="default_game")

    # Async generation (recommended for multi-file projects)
    from src.factories import AsyncProjectFactory
    factory = AsyncProjectFactory()
    result = await factory.generate("MyCLI", template="rust_cli")

    # Language support
    from src.factories import get_language_registry
    registry = get_language_registry()
    print(registry.list_names())  # ['python', 'rust', 'typescript', ...]
"""

from src.factories.ai_orchestrator import AIOrchestrator
from src.factories.artifact_registry import ArtifactRegistry
from src.factories.async_factory import (AsyncProjectFactory, generate_sync,
                                         quick_generate)
from src.factories.languages import (Language, LanguageRegistry,
                                     get_language_profiles,
                                     get_language_registry)
from src.factories.packaging_adapters import (PackagingContext,
                                              RuntimePackagingAdapter,
                                              build_runtime_packaging_adapter)
from src.factories.project_factory import ProjectFactory
from src.factories.templates import (BaseCLI, BaseGame, BaseLibrary,
                                     BaseProjectTemplate, BaseWebApp,
                                     load_template)

__all__ = [
    "AIOrchestrator",
    # Registry and orchestration
    "ArtifactRegistry",
    "AsyncProjectFactory",
    "BaseCLI",
    "BaseGame",
    "BaseLibrary",
    # Templates
    "BaseProjectTemplate",
    "BaseWebApp",
    # Language support
    "Language",
    "LanguageRegistry",
    # Packaging
    "PackagingContext",
    # Core factories
    "ProjectFactory",
    "RuntimePackagingAdapter",
    "build_runtime_packaging_adapter",
    "generate_sync",
    "get_language_profiles",
    "get_language_registry",
    "load_template",
    "quick_generate",
]
