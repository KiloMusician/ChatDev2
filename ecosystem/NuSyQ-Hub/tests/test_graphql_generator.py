"""
Tests for GraphQL Generator - Phase 3.1

Tests:
- Schema generation from models
- Query/Mutation creation
- Resolver scaffolding (Python, JavaScript, TypeScript)
- Type mapping (Python/TypeScript → GraphQL)
"""

import pytest
from src.generators.graphql_generator import (
    FieldType,
    GraphQLField,
    GraphQLInputType,
    GraphQLMutation,
    GraphQLQuery,
    GraphQLResolverGenerator,
    GraphQLSchemaGenerator,
    GraphQLType,
    GraphQLTypeMapper,
)


class TestGraphQLField:
    """Test GraphQL field definitions."""

    def test_field_creation(self):
        """Test creating a GraphQL field."""
        field = GraphQLField(
            name="id",
            field_type=FieldType.ID,
            is_required=True,
            description="Unique identifier",
        )

        assert field.name == "id"
        assert field.field_type == FieldType.ID
        assert field.is_required

    def test_field_with_list(self):
        """Test creating a list field."""
        field = GraphQLField(
            name="tags",
            field_type=FieldType.STRING,
            is_list=True,
        )

        assert field.is_list
        assert field.field_type == FieldType.STRING

    def test_field_with_enum(self):
        """Test field with enum type."""
        field = GraphQLField(
            name="status",
            field_type=FieldType.ENUM,
            enum_values=["ACTIVE", "INACTIVE", "PENDING"],
        )

        assert field.field_type == FieldType.ENUM
        assert len(field.enum_values) == 3


class TestGraphQLType:
    """Test GraphQL type definitions."""

    def test_simple_type_creation(self):
        """Test creating a simple GraphQL type."""
        fields = [
            GraphQLField("id", FieldType.ID, is_required=True),
            GraphQLField("name", FieldType.STRING, is_required=True),
            GraphQLField("email", FieldType.STRING),
        ]

        user_type = GraphQLType(
            name="User",
            fields=fields,
            description="Represents a user in the system",
        )

        assert user_type.name == "User"
        assert len(user_type.fields) == 3

    def test_type_with_relationships(self):
        """Test type with nested object references."""
        fields = [
            GraphQLField("id", FieldType.ID, is_required=True),
            GraphQLField("title", FieldType.STRING, is_required=True),
            GraphQLField("author", FieldType.OBJECT),
            GraphQLField("tags", FieldType.OBJECT, is_list=True),
        ]

        post_type = GraphQLType(
            name="Post",
            fields=fields,
        )

        assert len(post_type.fields) == 4


class TestGraphQLSchemaGenerator:
    """Test schema generation."""

    def test_schema_generator_initialization(self):
        """Test schema generator can be created."""
        generator = GraphQLSchemaGenerator()

        assert generator.types == {}
        assert generator.queries == []
        assert generator.mutations == []

    def test_add_type_to_schema(self):
        """Test adding a type to schema."""
        generator = GraphQLSchemaGenerator()

        user_type = GraphQLType(
            name="User",
            fields=[
                GraphQLField("id", FieldType.ID, is_required=True),
                GraphQLField("name", FieldType.STRING, is_required=True),
            ],
        )

        generator.add_type(user_type)

        assert "User" in generator.types
        assert generator.types["User"].name == "User"

    def test_add_query_to_schema(self):
        """Test adding a query operation."""
        generator = GraphQLSchemaGenerator()

        query = GraphQLQuery(
            name="getUser",
            return_type="User",
            parameters=[GraphQLField("id", FieldType.ID, is_required=True)],
            description="Get user by ID",
        )

        generator.add_query(query)

        assert len(generator.queries) == 1
        assert generator.queries[0].name == "getUser"

    def test_add_mutation_to_schema(self):
        """Test adding a mutation operation."""
        generator = GraphQLSchemaGenerator()

        mutation = GraphQLMutation(
            name="createUser",
            input_type="CreateUserInput",
            return_type="User",
            description="Create a new user",
        )

        generator.add_mutation(mutation)

        assert len(generator.mutations) == 1
        assert generator.mutations[0].name == "createUser"

    def test_schema_generation_simple(self):
        """Test generating a simple schema."""
        generator = GraphQLSchemaGenerator()

        # Add type
        user_type = GraphQLType(
            name="User",
            fields=[
                GraphQLField("id", FieldType.ID, is_required=True),
                GraphQLField("name", FieldType.STRING, is_required=True),
                GraphQLField("email", FieldType.STRING),
            ],
        )
        generator.add_type(user_type)

        # Add query
        query = GraphQLQuery(
            name="getUser",
            return_type="User",
            parameters=[GraphQLField("id", FieldType.ID, is_required=True)],
        )
        generator.add_query(query)

        schema = generator.generate_schema()

        assert "type User" in schema
        assert "id: ID!" in schema
        assert "name: String!" in schema
        assert "type Query" in schema
        assert "getUser(id: ID!): User" in schema

    def test_schema_with_mutations(self):
        """Test schema generation with mutations."""
        generator = GraphQLSchemaGenerator()

        # Add input type
        input_type = GraphQLInputType(
            name="CreateUserInput",
            fields=[
                GraphQLField("name", FieldType.STRING, is_required=True),
                GraphQLField("email", FieldType.STRING, is_required=True),
            ],
        )
        generator.add_input_type(input_type)

        # Add mutation
        mutation = GraphQLMutation(
            name="createUser",
            input_type="CreateUserInput",
            return_type="User",
        )
        generator.add_mutation(mutation)

        schema = generator.generate_schema()

        assert "input CreateUserInput" in schema
        assert "type Mutation" in schema
        assert "createUser(input: CreateUserInput!): User" in schema

    def test_enum_generation(self):
        """Test enum generation."""
        generator = GraphQLSchemaGenerator()

        generator.add_enum("UserStatus", ["ACTIVE", "INACTIVE", "SUSPENDED"])

        schema = generator.generate_schema()

        assert "enum UserStatus" in schema
        assert "ACTIVE" in schema
        assert "INACTIVE" in schema


class TestGraphQLResolverGenerator:
    """Test resolver code generation."""

    def test_python_resolver_generation(self):
        """Test Python resolver skeleton generation."""
        generator = GraphQLSchemaGenerator()

        query = GraphQLQuery(
            name="getAllUsers",
            return_type="[User]",
            parameters=[],
            description="Get all users",
        )
        generator.add_query(query)

        resolvers = GraphQLResolverGenerator.generate_resolver_skeleton(
            generator, language="python"
        )

        assert "class QueryResolver" in resolvers
        assert "async def getAllUsers" in resolvers
        assert "async def getAllUsers" in resolvers or "getAllUsers" in resolvers

    def test_javascript_resolver_generation(self):
        """Test JavaScript resolver skeleton generation."""
        generator = GraphQLSchemaGenerator()

        query = GraphQLQuery(
            name="getUser",
            return_type="User",
            parameters=[GraphQLField("id", FieldType.ID)],
        )
        generator.add_query(query)

        resolvers = GraphQLResolverGenerator.generate_resolver_skeleton(
            generator, language="javascript"
        )

        assert "Query:" in resolvers
        assert "getUser:" in resolvers
        assert "module.exports = resolvers" in resolvers

    def test_typescript_resolver_generation(self):
        """Test TypeScript resolver skeleton generation."""
        generator = GraphQLSchemaGenerator()

        mutation = GraphQLMutation(
            name="deleteUser",
            input_type="DeleteUserInput",
            return_type="Boolean",
        )
        generator.add_mutation(mutation)

        resolvers = GraphQLResolverGenerator.generate_resolver_skeleton(
            generator, language="typescript"
        )

        assert "export const resolvers" in resolvers
        assert "Mutation:" in resolvers
        assert "deleteUser" in resolvers

    def test_unsupported_language(self):
        """Test error handling for unsupported languages."""
        generator = GraphQLSchemaGenerator()

        with pytest.raises(ValueError):
            GraphQLResolverGenerator.generate_resolver_skeleton(generator, language="rust")


class TestGraphQLTypeMapper:
    """Test type mapping utilities."""

    def test_python_type_mapping(self):
        """Test Python to GraphQL type mapping."""
        assert GraphQLTypeMapper.map_python_type("str") == FieldType.STRING
        assert GraphQLTypeMapper.map_python_type("int") == FieldType.INT
        assert GraphQLTypeMapper.map_python_type("float") == FieldType.FLOAT
        assert GraphQLTypeMapper.map_python_type("bool") == FieldType.BOOLEAN
        assert GraphQLTypeMapper.map_python_type("datetime") == FieldType.DATETIME

    def test_typescript_type_mapping(self):
        """Test TypeScript to GraphQL type mapping."""
        assert GraphQLTypeMapper.map_typescript_type("string") == FieldType.STRING
        assert GraphQLTypeMapper.map_typescript_type("number") == FieldType.INT
        assert GraphQLTypeMapper.map_typescript_type("boolean") == FieldType.BOOLEAN
        assert GraphQLTypeMapper.map_typescript_type("Date") == FieldType.DATETIME

    def test_unknown_type_mapping(self):
        """Test mapping unknown types defaults to OBJECT."""
        assert GraphQLTypeMapper.map_python_type("CustomClass") == FieldType.OBJECT
        assert GraphQLTypeMapper.map_typescript_type("CustomInterface") == FieldType.OBJECT


class TestGraphQLIntegration:
    """Integration tests for complete GraphQL workflows."""

    def test_complete_blog_schema(self):
        """Test creating a complete blog schema."""
        generator = GraphQLSchemaGenerator()

        # Define types
        user_type = GraphQLType(
            name="User",
            fields=[
                GraphQLField("id", FieldType.ID, is_required=True),
                GraphQLField("name", FieldType.STRING, is_required=True),
                GraphQLField("email", FieldType.STRING, is_required=True),
            ],
        )

        post_type = GraphQLType(
            name="Post",
            fields=[
                GraphQLField("id", FieldType.ID, is_required=True),
                GraphQLField("title", FieldType.STRING, is_required=True),
                GraphQLField("content", FieldType.STRING, is_required=True),
                GraphQLField("author", FieldType.OBJECT),
                GraphQLField("createdAt", FieldType.DATETIME),
            ],
        )

        generator.add_type(user_type)
        generator.add_type(post_type)

        # Define queries
        generator.add_query(
            GraphQLQuery(
                name="getAllUsers",
                return_type="[User]",
                parameters=[],
            )
        )
        generator.add_query(
            GraphQLQuery(
                name="getPost",
                return_type="Post",
                parameters=[GraphQLField("id", FieldType.ID, is_required=True)],
            )
        )

        # Define mutations
        generator.add_mutation(
            GraphQLMutation(
                name="createPost",
                input_type="CreatePostInput",
                return_type="Post",
            )
        )

        schema = generator.generate_schema()

        # Verify schema contains all expected elements
        assert "type User" in schema
        assert "type Post" in schema
        assert "type Query" in schema
        assert "type Mutation" in schema
        assert "getAllUsers" in schema
        assert "getPost" in schema
        assert "createPost" in schema

    def test_resolver_with_full_schema(self):
        """Test resolver generation with complete schema."""
        generator = GraphQLSchemaGenerator()

        query = GraphQLQuery(
            name="getItems",
            return_type="[Item]",
            parameters=[
                GraphQLField("limit", FieldType.INT),
                GraphQLField("offset", FieldType.INT),
            ],
        )
        generator.add_query(query)

        # Generate schema
        schema = generator.generate_schema()
        assert "type Query" in schema

        # Generate resolvers in multiple languages
        python_resolvers = GraphQLResolverGenerator.generate_resolver_skeleton(generator, "python")
        assert "def getItems" in python_resolvers

        js_resolvers = GraphQLResolverGenerator.generate_resolver_skeleton(generator, "javascript")
        assert "getItems:" in js_resolvers

        ts_resolvers = GraphQLResolverGenerator.generate_resolver_skeleton(generator, "typescript")
        assert "getItems" in ts_resolvers


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
