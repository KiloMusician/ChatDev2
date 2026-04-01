"""
Tests for OpenAPI/Swagger Generator - Phase 3.4

Tests:
- OpenAPI schema generation
- Endpoint definition
- Parameter handling
- Response handling
- Complete API specification generation
- JSON and YAML output
"""

import json

import pytest
from src.generators.openapi_generator import (
    HTTPMethod,
    OpenAPIEndpoint,
    OpenAPIGenerator,
    OpenAPIInfo,
    OpenAPIParameter,
    OpenAPIProperty,
    OpenAPIResponse,
    OpenAPISchema,
    RESTAPIDocumentationBuilder,
    SchemaType,
)


class TestOpenAPIProperty:
    """Test property definitions in schemas."""

    def test_string_property(self):
        """Test creating a string property."""
        prop = OpenAPIProperty(
            name="name",
            prop_type=SchemaType.STRING,
            description="User name",
            is_required=True,
        )

        assert prop.name == "name"
        assert prop.prop_type == SchemaType.STRING
        assert prop.is_required

    def test_property_to_dict(self):
        """Test converting property to OpenAPI dict."""
        prop = OpenAPIProperty(
            name="age",
            prop_type=SchemaType.INTEGER,
            description="User age",
            default_value=0,
        )

        prop_dict = prop.to_dict()

        assert prop_dict["type"] == "integer"
        assert prop_dict["description"] == "User age"
        assert prop_dict["default"] == 0

    def test_enum_property(self):
        """Test property with enum values."""
        prop = OpenAPIProperty(
            name="status",
            prop_type=SchemaType.STRING,
            enum_values=["active", "inactive", "pending"],
        )

        prop_dict = prop.to_dict()

        assert prop_dict["enum"] == ["active", "inactive", "pending"]

    def test_array_property(self):
        """Test array property."""
        prop = OpenAPIProperty(
            name="tags",
            prop_type=SchemaType.ARRAY,
            items_type=SchemaType.STRING,
        )

        prop_dict = prop.to_dict()

        assert prop_dict["type"] == "array"
        assert prop_dict["items"]["type"] == "string"


class TestOpenAPISchema:
    """Test schema definitions."""

    def test_simple_schema_creation(self):
        """Test creating a simple schema."""
        schema = OpenAPISchema(
            name="User",
            description="User object",
        )

        schema.add_property(OpenAPIProperty("id", SchemaType.INTEGER, is_required=True))
        schema.add_property(OpenAPIProperty("name", SchemaType.STRING, is_required=True))

        assert len(schema.properties) == 2
        assert "id" in schema.required_fields

    def test_schema_to_dict(self):
        """Test converting schema to OpenAPI dict."""
        schema = OpenAPISchema(name="Product")
        schema.add_property(OpenAPIProperty("id", SchemaType.INTEGER, is_required=True))
        schema.add_property(OpenAPIProperty("name", SchemaType.STRING, is_required=True))
        schema.add_property(OpenAPIProperty("price", SchemaType.NUMBER))

        schema_dict = schema.to_dict()

        assert schema_dict["type"] == "object"
        assert "id" in schema_dict["properties"]
        assert schema_dict["required"] == ["id", "name"]

    def test_schema_with_example(self):
        """Test schema with example data."""
        schema = OpenAPISchema(
            name="User",
            example={
                "id": 1,
                "name": "John Doe",
            },
        )

        schema_dict = schema.to_dict()

        assert schema_dict["example"] == {"id": 1, "name": "John Doe"}


class TestOpenAPIParameter:
    """Test parameter definitions."""

    def test_query_parameter(self):
        """Test query parameter."""
        param = OpenAPIParameter(
            name="limit",
            param_type=SchemaType.INTEGER,
            param_in="query",
            description="Max results",
            default_value=10,
        )

        param_dict = param.to_dict()

        assert param_dict["in"] == "query"
        assert param_dict["schema"]["type"] == "integer"
        assert param_dict["schema"]["default"] == 10

    def test_path_parameter(self):
        """Test path parameter."""
        param = OpenAPIParameter(
            name="id",
            param_type=SchemaType.INTEGER,
            param_in="path",
            is_required=True,
        )

        param_dict = param.to_dict()

        assert param_dict["in"] == "path"
        assert param_dict["required"]

    def test_header_parameter(self):
        """Test header parameter."""
        param = OpenAPIParameter(
            name="X-Token",
            param_type=SchemaType.STRING,
            param_in="header",
        )

        param_dict = param.to_dict()

        assert param_dict["in"] == "header"


class TestOpenAPIResponse:
    """Test response definitions."""

    def test_success_response(self):
        """Test successful response."""
        response = OpenAPIResponse(
            status_code=200,
            description="Successful response",
        )

        response_dict = response.to_dict()

        assert response_dict["description"] == "Successful response"

    def test_response_with_schema(self):
        """Test response with schema."""
        schema = OpenAPISchema(name="User")
        schema.add_property(OpenAPIProperty("id", SchemaType.INTEGER))

        response = OpenAPIResponse(
            status_code=200,
            description="User data",
            schema=schema,
        )

        response_dict = response.to_dict()

        assert "content" in response_dict
        assert "application/json" in response_dict["content"]


class TestOpenAPIEndpoint:
    """Test endpoint definitions."""

    def test_simple_get_endpoint(self):
        """Test simple GET endpoint."""
        endpoint = OpenAPIEndpoint(
            path="/users",
            method=HTTPMethod.GET,
            summary="List users",
        )

        endpoint.add_response(OpenAPIResponse(200, "Users list"))

        endpoint_dict = endpoint.to_dict()

        assert endpoint_dict["summary"] == "List users"
        assert "200" in endpoint_dict["responses"]

    def test_post_endpoint_with_request_body(self):
        """Test POST endpoint with request body."""
        schema = OpenAPISchema(name="CreateUser")
        schema.add_property(OpenAPIProperty("name", SchemaType.STRING, is_required=True))

        endpoint = OpenAPIEndpoint(
            path="/users",
            method=HTTPMethod.POST,
            summary="Create user",
            request_body=schema,
        )

        endpoint.add_response(OpenAPIResponse(201, "User created"))

        endpoint_dict = endpoint.to_dict()

        assert "requestBody" in endpoint_dict
        assert "201" in endpoint_dict["responses"]

    def test_endpoint_with_parameters(self):
        """Test endpoint with parameters."""
        endpoint = OpenAPIEndpoint(
            path="/users/{id}",
            method=HTTPMethod.GET,
            summary="Get user",
        )

        endpoint.add_parameter(
            OpenAPIParameter("id", SchemaType.INTEGER, param_in="path", is_required=True)
        )
        endpoint.add_parameter(
            OpenAPIParameter("include_posts", SchemaType.BOOLEAN, param_in="query")
        )

        endpoint_dict = endpoint.to_dict()

        assert len(endpoint_dict["parameters"]) == 2

    def test_endpoint_with_tags(self):
        """Test endpoint with tags."""
        endpoint = OpenAPIEndpoint(
            path="/users",
            method=HTTPMethod.GET,
            summary="List users",
            tags=["users"],
        )

        endpoint_dict = endpoint.to_dict()

        assert endpoint_dict["tags"] == ["users"]


class TestOpenAPIInfo:
    """Test API info."""

    def test_minimal_info(self):
        """Test minimal API info."""
        info = OpenAPIInfo(
            title="My API",
            version="1.0.0",
        )

        info_dict = info.to_dict()

        assert info_dict["title"] == "My API"
        assert info_dict["version"] == "1.0.0"

    def test_info_with_contact(self):
        """Test info with contact."""
        info = OpenAPIInfo(
            title="My API",
            version="1.0.0",
            contact_name="Support",
            contact_email="support@example.com",
        )

        info_dict = info.to_dict()

        assert "contact" in info_dict
        assert info_dict["contact"]["name"] == "Support"
        assert info_dict["contact"]["email"] == "support@example.com"


class TestOpenAPIGenerator:
    """Test OpenAPI specification generator."""

    def test_basic_specification_generation(self):
        """Test generating basic OpenAPI spec."""
        info = OpenAPIInfo(title="Test API", version="1.0.0")
        gen = OpenAPIGenerator(info)

        endpoint = OpenAPIEndpoint(
            path="/test",
            method=HTTPMethod.GET,
            summary="Test endpoint",
        )
        endpoint.add_response(OpenAPIResponse(200, "Success"))

        gen.add_endpoint(endpoint)

        spec = gen.generate_specification()

        assert spec["openapi"] == "3.0.0"
        assert spec["info"]["title"] == "Test API"
        assert "/test" in spec["paths"]

    def test_add_servers(self):
        """Test adding servers."""
        info = OpenAPIInfo(title="API", version="1.0.0")
        gen = OpenAPIGenerator(info)

        gen.add_server("https://api.example.com", "Production")
        gen.add_server("https://staging.example.com", "Staging")

        spec = gen.generate_specification()

        assert len(spec["servers"]) == 2

    def test_add_bearer_security(self):
        """Test adding bearer token security."""
        info = OpenAPIInfo(title="API", version="1.0.0")
        gen = OpenAPIGenerator(info)

        gen.add_bearer_security()

        spec = gen.generate_specification()

        assert "components" in spec
        assert "securitySchemes" in spec["components"]
        assert "bearerAuth" in spec["components"]["securitySchemes"]

    def test_add_api_key_security(self):
        """Test adding API key security."""
        info = OpenAPIInfo(title="API", version="1.0.0")
        gen = OpenAPIGenerator(info)

        gen.add_api_key_security("Authorization")

        spec = gen.generate_specification()

        assert "apiKey" in spec["components"]["securitySchemes"]

    def test_json_generation(self):
        """Test JSON output generation."""
        info = OpenAPIInfo(title="API", version="1.0.0")
        gen = OpenAPIGenerator(info)

        endpoint = OpenAPIEndpoint(
            path="/test",
            method=HTTPMethod.GET,
            summary="Test",
        )
        endpoint.add_response(OpenAPIResponse(200, "OK"))
        gen.add_endpoint(endpoint)

        json_str = gen.generate_json()
        parsed = json.loads(json_str)

        assert parsed["openapi"] == "3.0.0"


class TestRESTAPIDocumentationBuilder:
    """Test REST API documentation builder."""

    def test_builder_pattern(self):
        """Test using builder pattern."""
        builder = RESTAPIDocumentationBuilder(
            title="User API",
            version="1.0.0",
        )

        builder.with_description("API for managing users")
        builder.with_contact("Support Team", "support@example.com")
        builder.add_server("https://api.example.com", "Production")

        endpoint = builder.build_endpoint(
            path="/users",
            method=HTTPMethod.GET,
            summary="List users",
        )
        endpoint.add_response(OpenAPIResponse(200, "Users list"))

        builder.add_endpoint(endpoint)

        json_str = builder.get_json()
        parsed = json.loads(json_str)

        assert parsed["info"]["title"] == "User API"
        assert parsed["info"]["description"] == "API for managing users"


class TestOpenAPIIntegration:
    """Integration tests for complete API specifications."""

    def test_complete_user_management_api(self):
        """Test generating complete user management API spec."""
        # API Info
        info = OpenAPIInfo(
            title="User Management API",
            version="2.0.0",
            description="Complete user management system",
            contact_name="API Support",
            contact_email="api@example.com",
        )

        gen = OpenAPIGenerator(info)
        gen.add_server("https://api.example.com/v2", "Production")
        gen.add_bearer_security()

        # List users endpoint
        list_users = OpenAPIEndpoint(
            path="/users",
            method=HTTPMethod.GET,
            summary="List all users",
            tags=["users"],
        )
        list_users.add_parameter(
            OpenAPIParameter("limit", SchemaType.INTEGER, "query", default_value=10)
        )
        list_users.add_response(OpenAPIResponse(200, "Users list"))
        list_users.add_response(OpenAPIResponse(401, "Unauthorized"))

        gen.add_endpoint(list_users)

        # Create user endpoint
        create_user_schema = OpenAPISchema(name="CreateUserRequest")
        create_user_schema.add_property(
            OpenAPIProperty("name", SchemaType.STRING, is_required=True)
        )
        create_user_schema.add_property(
            OpenAPIProperty("email", SchemaType.STRING, is_required=True)
        )

        create_user = OpenAPIEndpoint(
            path="/users",
            method=HTTPMethod.POST,
            summary="Create new user",
            request_body=create_user_schema,
            tags=["users"],
        )
        create_user.add_response(OpenAPIResponse(201, "User created"))

        gen.add_endpoint(create_user)

        # Get user by ID endpoint
        get_user = OpenAPIEndpoint(
            path="/users/{id}",
            method=HTTPMethod.GET,
            summary="Get user by ID",
            tags=["users"],
        )
        get_user.add_parameter(OpenAPIParameter("id", SchemaType.INTEGER, "path", is_required=True))
        get_user.add_response(OpenAPIResponse(200, "User data"))
        get_user.add_response(OpenAPIResponse(404, "User not found"))

        gen.add_endpoint(get_user)

        # Generate spec
        spec = gen.generate_specification()

        # Validation
        assert spec["openapi"] == "3.0.0"
        assert "/users" in spec["paths"]
        assert "/users/{id}" in spec["paths"]
        assert "get" in spec["paths"]["/users"]
        assert "post" in spec["paths"]["/users"]
        assert "bearerAuth" in spec["components"]["securitySchemes"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
