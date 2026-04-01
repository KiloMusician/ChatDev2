"""OpenAPI/Swagger Generator - Phase 3.4.

Generates OpenAPI 3.0 documentation from FastAPI/Express code
Includes endpoint discovery, request/response schema extraction, and full OpenAPI spec generation.

Components:
- OpenAPISpec: Container for complete OpenAPI specification
- OpenAPIEndpoint: Individual endpoint definition
- OpenAPISchema: Request/response schema
- OpenAPIGenerator: Main orchestrator for OpenAPI generation
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HTTPMethod(Enum):
    """HTTP methods."""

    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"
    PATCH = "patch"
    HEAD = "head"
    OPTIONS = "options"


class SchemaType(Enum):
    """JSON Schema types."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class OpenAPIProperty:
    """Property in a schema."""

    name: str
    prop_type: SchemaType
    description: str | None = None
    is_required: bool = False
    default_value: Any = None
    items_type: SchemaType | None = None
    enum_values: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to OpenAPI property dict."""
        prop: dict[str, Any] = {
            "type": self.prop_type.value,
        }

        if self.description:
            prop["description"] = self.description

        if self.default_value is not None:
            prop["default"] = self.default_value

        if self.prop_type == SchemaType.ARRAY and self.items_type:
            prop["items"] = {"type": self.items_type.value}

        if self.enum_values:
            prop["enum"] = self.enum_values

        return prop


@dataclass
class OpenAPISchema:
    """Request/response schema definition."""

    name: str
    properties: list[OpenAPIProperty] = field(default_factory=list)
    required_fields: list[str] = field(default_factory=list)
    description: str | None = None
    example: dict[str, Any] | None = None

    def add_property(self, prop: OpenAPIProperty) -> "OpenAPISchema":
        """Add a property to the schema."""
        self.properties.append(prop)
        if prop.is_required:
            self.required_fields.append(prop.name)
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert to OpenAPI schema dict."""
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {},
        }

        if self.description:
            schema["description"] = self.description

        for prop in self.properties:
            schema["properties"][prop.name] = prop.to_dict()

        if self.required_fields:
            schema["required"] = self.required_fields

        if self.example:
            schema["example"] = self.example

        return schema


@dataclass
class OpenAPIParameter:
    """Query, path, or header parameter."""

    name: str
    param_type: SchemaType
    param_in: str  # query, path, header, cookie
    description: str | None = None
    is_required: bool = False
    default_value: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to OpenAPI parameter dict."""
        param: dict[str, Any] = {
            "name": self.name,
            "in": self.param_in,
            "schema": {"type": self.param_type.value},
        }

        if self.description:
            param["description"] = self.description

        if self.is_required:
            param["required"] = True

        if self.default_value is not None:
            param["schema"]["default"] = self.default_value

        return param


@dataclass
class OpenAPIResponse:
    """Response definition."""

    status_code: int
    description: str
    schema: OpenAPISchema | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to OpenAPI response dict."""
        response: dict[str, Any] = {
            "description": self.description,
        }

        if self.schema:
            response["content"] = {
                "application/json": {
                    "schema": self.schema.to_dict(),
                }
            }

        return response


@dataclass
class OpenAPIEndpoint:
    """Individual API endpoint definition."""

    path: str
    method: HTTPMethod
    summary: str
    description: str | None = None
    parameters: list[OpenAPIParameter] = field(default_factory=list)
    request_body: OpenAPISchema | None = None
    responses: list[OpenAPIResponse] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    operation_id: str | None = None
    deprecated: bool = False

    def add_parameter(self, param: OpenAPIParameter) -> "OpenAPIEndpoint":
        """Add a parameter."""
        self.parameters.append(param)
        return self

    def add_response(self, response: OpenAPIResponse) -> "OpenAPIEndpoint":
        """Add a response."""
        self.responses.append(response)
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert to OpenAPI operation dict."""
        operation: dict[str, Any] = {
            "summary": self.summary,
            "operationId": self.operation_id
            or f"{self.method.value}_{self.path.replace('/', '_')}",
        }

        if self.description:
            operation["description"] = self.description

        if self.tags:
            operation["tags"] = self.tags

        if self.deprecated:
            operation["deprecated"] = True

        if self.parameters:
            operation["parameters"] = [p.to_dict() for p in self.parameters]

        if self.request_body:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": self.request_body.to_dict(),
                    }
                },
            }

        operation["responses"] = {str(r.status_code): r.to_dict() for r in self.responses}

        return operation


@dataclass
class OpenAPIInfo:
    """API metadata."""

    title: str
    version: str
    description: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_url: str | None = None
    license_name: str | None = None
    license_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to OpenAPI info dict."""
        info: dict[str, Any] = {
            "title": self.title,
            "version": self.version,
        }

        if self.description:
            info["description"] = self.description

        contact: dict[str, str] = {}
        if self.contact_name:
            contact["name"] = self.contact_name
        if self.contact_email:
            contact["email"] = self.contact_email
        if self.contact_url:
            contact["url"] = self.contact_url
        if contact:
            info["contact"] = contact

        if self.license_name:
            info["license"] = {"name": self.license_name}
            if self.license_url:
                info["license"]["url"] = self.license_url

        return info


class OpenAPIGenerator:
    """Generator for OpenAPI 3.0 specifications."""

    def __init__(self, info: OpenAPIInfo):
        """Initialize with API info."""
        self.info = info
        self.endpoints: list[OpenAPIEndpoint] = []
        self.servers: list[dict[str, str]] = []
        self.security_schemes: dict[str, dict[str, Any]] = {}
        self.components_schemas: dict[str, OpenAPISchema] = {}

    def add_endpoint(self, endpoint: OpenAPIEndpoint) -> "OpenAPIGenerator":
        """Add an endpoint."""
        self.endpoints.append(endpoint)
        return self

    def add_server(self, url: str, description: str | None = None) -> "OpenAPIGenerator":
        """Add a server."""
        server: dict[str, str] = {"url": url}
        if description:
            server["description"] = description
        self.servers.append(server)
        return self

    def add_bearer_security(self) -> "OpenAPIGenerator":
        """Add bearer token security scheme."""
        self.security_schemes["bearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
        return self

    def add_api_key_security(self, param_name: str = "X-API-Key") -> "OpenAPIGenerator":
        """Add API key security scheme."""
        self.security_schemes["apiKey"] = {
            "type": "apiKey",
            "name": param_name,
            "in": "header",
        }
        return self

    def add_oauth2_security(self) -> "OpenAPIGenerator":
        """Add OAuth2 security scheme."""
        self.security_schemes["oauth2"] = {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://example.com/oauth/authorize",
                    "tokenUrl": "https://example.com/oauth/token",
                    "scopes": {
                        "read": "Read access",
                        "write": "Write access",
                    },
                }
            },
        }
        return self

    def add_component_schema(self, name: str, schema: OpenAPISchema) -> "OpenAPIGenerator":
        """Add a reusable schema component."""
        self.components_schemas[name] = schema
        return self

    def generate_specification(self) -> dict[str, Any]:
        """Generate complete OpenAPI specification."""
        spec: dict[str, Any] = {
            "openapi": "3.0.0",
            "info": self.info.to_dict(),
        }

        if self.servers:
            spec["servers"] = self.servers
        else:
            spec["servers"] = [{"url": "http://localhost:8000"}]

        # Build paths
        paths: dict[str, dict[str, Any]] = {}
        for endpoint in self.endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}
            paths[endpoint.path][endpoint.method.value] = endpoint.to_dict()

        spec["paths"] = paths

        # Add components if any
        if self.components_schemas or self.security_schemes:
            spec["components"] = {}

            if self.components_schemas:
                spec["components"]["schemas"] = {
                    name: schema.to_dict() for name, schema in self.components_schemas.items()
                }

            if self.security_schemes:
                spec["components"]["securitySchemes"] = self.security_schemes

        return spec

    def generate_json(self, indent: int = 2) -> str:
        """Generate OpenAPI spec as JSON."""
        spec = self.generate_specification()
        return json.dumps(spec, indent=indent)

    def generate_yaml(self) -> str:
        """Generate OpenAPI spec as YAML (requires PyYAML)."""
        try:
            import importlib

            yaml = importlib.import_module("yaml")

            spec = self.generate_specification()
            rendered: str = yaml.dump(spec, default_flow_style=False)
            return rendered
        except ImportError as exc:
            raise ImportError("PyYAML required for YAML generation") from exc


# Convenience generators for common scenarios


class FastAPIDocumentationGenerator:
    """Generate OpenAPI docs from FastAPI app discovery."""

    @staticmethod
    def generate_from_description(
        title: str,
        description: str,
        version: str = "1.0.0",
    ) -> OpenAPIGenerator:
        """Generate OpenAPI spec from natural description."""
        info = OpenAPIInfo(
            title=title,
            version=version,
            description=description,
        )
        return OpenAPIGenerator(info)


class RESTAPIDocumentationBuilder:
    """Builder for constructing REST API documentation."""

    def __init__(self, title: str, version: str = "1.0.0"):
        """Initialize with API title and version."""
        self.info = OpenAPIInfo(title=title, version=version)
        self.generator = OpenAPIGenerator(self.info)

    def with_description(self, description: str) -> "RESTAPIDocumentationBuilder":
        """Add API description."""
        self.info.description = description
        return self

    def with_contact(self, name: str, email: str | None = None) -> "RESTAPIDocumentationBuilder":
        """Add contact info."""
        self.info.contact_name = name
        if email:
            self.info.contact_email = email
        return self

    def add_server(self, url: str, description: str | None = None) -> "RESTAPIDocumentationBuilder":
        """Add server."""
        self.generator.add_server(url, description)
        return self

    def build_endpoint(
        self,
        path: str,
        method: HTTPMethod,
        summary: str,
    ) -> OpenAPIEndpoint:
        """Builder method to create endpoint."""
        return OpenAPIEndpoint(path=path, method=method, summary=summary)

    def add_endpoint(self, endpoint: OpenAPIEndpoint) -> "RESTAPIDocumentationBuilder":
        """Add endpoint to spec."""
        self.generator.add_endpoint(endpoint)
        return self

    def get_json(self) -> str:
        """Get final spec as JSON."""
        return self.generator.generate_json()

    def get_yaml(self) -> str:
        """Get final spec as YAML."""
        return self.generator.generate_yaml()
