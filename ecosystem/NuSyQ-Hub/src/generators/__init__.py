"""src/generators - DEPRECATED - Use src/factories/generators instead.

This module is maintained for backward compatibility.
All new code should import from src.factories.generators.

Migration (Sprint 3):
- Template definitions → src.factories.templates
- Code generators → src.factories.generators.registry
- Specialized generators → src.factories.generators.specialized

Example migration:
    # OLD (deprecated)
    from src.generators.template_definitions import ProjectType, get_template
    from src.generators.universal_project_generator import UniversalProjectGenerator

    # NEW (recommended)
    from src.factories.templates import load_template, BaseProjectTemplate
    from src.factories.generators import GeneratorRegistry, get_generator
"""

import warnings
from typing import TYPE_CHECKING

# Emit deprecation warning on import
warnings.warn(
    "src.generators is deprecated. Use src.factories.generators instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from canonical locations for backward compatibility

# Template definitions (kept for API compatibility)
# Specialized generators - re-export from new location
from src.factories.generators.specialized import (  # Components; OpenAPI; GraphQL
    ComponentDefinition, ComponentFramework, ComponentProp,
    ComponentStylesGenerator, FastAPIDocumentationGenerator, FieldType,
    GraphQLField, GraphQLInputType, GraphQLMutation, GraphQLQuery,
    GraphQLResolverGenerator, GraphQLSchemaGenerator, GraphQLType,
    GraphQLTypeMapper, HTTPMethod, OpenAPIEndpoint, OpenAPIGenerator,
    OpenAPIInfo, OpenAPIParameter, OpenAPIProperty, OpenAPIResponse,
    OpenAPISchema, ReactComponentGenerator, RESTAPIDocumentationBuilder,
    SchemaType, StyleStrategy, VueComponentGenerator)
from src.generators.template_definitions import (TEMPLATES, AIProvider,
                                                 DependencyInfo, FileTemplate,
                                                 HookScript, IntegrationPoint,
                                                 LanguageType, ProjectTemplate,
                                                 ProjectType, get_template,
                                                 list_template_ids,
                                                 list_templates)

# Universal project generator - lazy import to avoid circular dependency
# Direct import from legacy location for backward compatibility
# Canonical location: src.factories.generators.specialized.universal_project_generator
_GenerationResult = None
_UniversalProjectGenerator = None


def __getattr__(name: str):
    """Lazy import for universal_project_generator to avoid circular imports."""
    global _GenerationResult, _UniversalProjectGenerator

    if name == "GenerationResult":
        if _GenerationResult is None:
            from src.factories.generators.specialized.universal_project_generator import \
                GenerationResult as _GR

            _GenerationResult = _GR
        return _GenerationResult

    if name == "UniversalProjectGenerator":
        if _UniversalProjectGenerator is None:
            from src.factories.generators.specialized.universal_project_generator import \
                UniversalProjectGenerator as _UPG

            _UniversalProjectGenerator = _UPG
        return _UniversalProjectGenerator

    raise AttributeError(f"module 'src.generators' has no attribute '{name}'")


# New factory-based generators
if TYPE_CHECKING:
    from src.factories.generators.registry import GeneratorRegistry


def get_generator_registry() -> "GeneratorRegistry":
    """Get the factory-based generator registry.

    This is the recommended way to access generators.
    """
    from src.factories.generators.registry import GeneratorRegistry

    return GeneratorRegistry.get_instance()


__all__ = [
    "TEMPLATES",
    # Deprecated (but still exported for compatibility)
    "AIProvider",
    # Components (moved to specialized)
    "ComponentDefinition",
    "ComponentFramework",
    "ComponentProp",
    "ComponentStylesGenerator",
    "DependencyInfo",
    # OpenAPI (moved to specialized)
    "FastAPIDocumentationGenerator",
    # GraphQL (moved to specialized)
    "FieldType",
    "FileTemplate",
    "GenerationResult",
    "GraphQLField",
    "GraphQLInputType",
    "GraphQLMutation",
    "GraphQLQuery",
    "GraphQLResolverGenerator",
    "GraphQLSchemaGenerator",
    "GraphQLType",
    "GraphQLTypeMapper",
    "HTTPMethod",
    "HookScript",
    "IntegrationPoint",
    "LanguageType",
    "OpenAPIEndpoint",
    "OpenAPIGenerator",
    "OpenAPIInfo",
    "OpenAPIParameter",
    "OpenAPIProperty",
    "OpenAPIResponse",
    "OpenAPISchema",
    "ProjectTemplate",
    "ProjectType",
    "RESTAPIDocumentationBuilder",
    "ReactComponentGenerator",
    "SchemaType",
    "StyleStrategy",
    "UniversalProjectGenerator",
    "VueComponentGenerator",
    # New recommended API
    "get_generator_registry",
    "get_template",
    "list_template_ids",
    "list_templates",
]
