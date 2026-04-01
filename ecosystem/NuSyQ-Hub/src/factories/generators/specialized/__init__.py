"""Specialized Generators - Domain-specific code generators.

These generators handle specific artifact types:
- GraphQL schemas and resolvers
- OpenAPI/Swagger specifications
- React/Vue component scaffolding
- Database helpers and migrations

Migrated from src/generators/ for consolidation (Sprint 3).
"""

from src.factories.generators.specialized.component_scaffolding import (
    ComponentDefinition, ComponentFramework, ComponentProp,
    ComponentStylesGenerator, ReactComponentGenerator, StyleStrategy,
    VueComponentGenerator)
from src.factories.generators.specialized.graphql_generator import (
    FieldType, GraphQLField, GraphQLInputType, GraphQLMutation, GraphQLQuery,
    GraphQLResolverGenerator, GraphQLSchemaGenerator, GraphQLType,
    GraphQLTypeMapper)
from src.factories.generators.specialized.openapi_generator import (
    FastAPIDocumentationGenerator, HTTPMethod, OpenAPIEndpoint,
    OpenAPIGenerator, OpenAPIInfo, OpenAPIParameter, OpenAPIProperty,
    OpenAPIResponse, OpenAPISchema, RESTAPIDocumentationBuilder, SchemaType)
from src.factories.generators.specialized.universal_project_generator import (
    GenerationResult, UniversalProjectGenerator)

__all__ = [
    # Components
    "ComponentDefinition",
    "ComponentFramework",
    "ComponentProp",
    "ComponentStylesGenerator",
    # OpenAPI
    "FastAPIDocumentationGenerator",
    # GraphQL
    "FieldType",
    # Universal Project Generator
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
    "OpenAPIEndpoint",
    "OpenAPIGenerator",
    "OpenAPIInfo",
    "OpenAPIParameter",
    "OpenAPIProperty",
    "OpenAPIResponse",
    "OpenAPISchema",
    "RESTAPIDocumentationBuilder",
    "ReactComponentGenerator",
    "SchemaType",
    "StyleStrategy",
    "UniversalProjectGenerator",
    "VueComponentGenerator",
]
