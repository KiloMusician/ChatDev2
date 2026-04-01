"""src/factories/generators - Pluggable AI Code Generation System.

THE canonical location for all code generators (Sprint 3 consolidation).

Provides a unified interface for multiple AI providers:
- Ollama (local LLM)
- Claude (Anthropic API)
- OpenAI (GPT API)
- ChatDev (multi-agent system)

Also includes specialized generators for:
- GraphQL schemas and resolvers
- OpenAPI/Swagger specifications
- React/Vue component scaffolding

Usage:
    from src.factories.generators import get_generator, GeneratorRegistry

    # Get a specific generator
    generator = get_generator("ollama")
    result = await generator.generate(template, context)

    # Or use the registry
    registry = GeneratorRegistry.get_instance()
    generator = registry.get_for_language("rust")  # Returns best provider for Rust

    # Specialized generators
    from src.factories.generators.specialized import GraphQLSchemaGenerator
"""

from src.factories.generators.base import (AbstractGenerator, FileResult,
                                           GenerationContext, GenerationResult)
from src.factories.generators.chatdev_generator import ChatDevGenerator
from src.factories.generators.registry import (GeneratorRegistry,
                                               get_generator,
                                               get_generator_for_language,
                                               list_available_generators)


# Lazy imports for optional generators
def get_ollama_generator(**kwargs):
    from src.factories.generators.ollama_generator import OllamaGenerator

    return OllamaGenerator(**kwargs)


def get_claude_generator(**kwargs):
    from src.factories.generators.claude_generator import ClaudeGenerator

    return ClaudeGenerator(**kwargs)


def get_openai_generator(**kwargs):
    from src.factories.generators.openai_generator import OpenAIGenerator

    return OpenAIGenerator(**kwargs)


# Re-export specialized generators for convenience
def get_graphql_generator():
    from src.factories.generators.specialized import GraphQLSchemaGenerator

    return GraphQLSchemaGenerator()


def get_openapi_generator(info):
    from src.factories.generators.specialized import OpenAPIGenerator

    return OpenAPIGenerator(info)


__all__ = [
    # Base classes
    "AbstractGenerator",
    # AI Generators
    "ChatDevGenerator",
    "FileResult",
    "GenerationContext",
    "GenerationResult",
    # Registry
    "GeneratorRegistry",
    "get_claude_generator",
    "get_generator",
    "get_generator_for_language",
    # Specialized generators
    "get_graphql_generator",
    "get_ollama_generator",
    "get_openai_generator",
    "get_openapi_generator",
    "list_available_generators",
]
