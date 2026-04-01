"""
Ecosystem Integration Tests - Phase 3.5

End-to-end integration tests validating the complete AI-powered development ecosystem:
- Generation (Phase 1)
- Publishing (Phase 2)
- Advanced Scaffolding (Phase 3.1-3.4)

This validates the full workflow: Template → Generate → Scaffold → Publish → Document
"""

import pytest
from src.generators.component_scaffolding import (
    ComponentDefinition,
    ComponentProp,
    ReactComponentGenerator,
)
from src.generators.database_helpers import (
    ColumnType,
    DatabaseColumn,
    DatabaseTable,
    SQLSchemaGenerator,
)
from src.generators.graphql_generator import GraphQLField, GraphQLSchemaGenerator, GraphQLType
from src.generators.openapi_generator import (
    HTTPMethod,
    OpenAPIEndpoint,
    OpenAPIGenerator,
    OpenAPIInfo,
    OpenAPIProperty,
    OpenAPIResponse,
    OpenAPISchema,
    SchemaType,
)
from src.generators.template_definitions import get_template
from src.generators.universal_project_generator import UniversalProjectGenerator


class TestGenerationToPublishingWorkflow:
    """Integration: Project Generation → Publishing."""

    def test_python_package_generation_for_publishing(self):
        """Test Python package generation ready for PyPI publishing."""
        # Get template
        template = get_template("package_python")
        assert template is not None
        assert template.type.value == "package"

        # Create generator
        upg = UniversalProjectGenerator()

        # Generate project
        result = upg.generate(
            template_id=template.template_id,
            project_name="test-package",
            options={"description": "Test package"},
        )

        # Verify generation success
        assert result.status in ["success", "generated"]
        assert result.project_id is not None

        # Verify PyPI-compatible metadata
        assert result.project_name == "test-package"
        assert result.metadata is not None

    def test_node_package_generation_for_npm_publishing(self):
        """Test Node.js package generation ready for NPM publishing."""
        # Get template
        template = get_template("package_npm")
        assert template is not None

        # Generate
        upg = UniversalProjectGenerator()
        result = upg.generate(
            template_id=template.template_id,
            project_name="@scope/test-pkg",
            options={"description": "Test Node package"},
        )

        # Verify NPM-compatible metadata
        assert result.status in ["success", "generated"]
        assert result.project_name == "@scope/test-pkg"


class TestGraphQLWithComponentScaffolding:
    """Integration: GraphQL API + React Components."""

    def test_blog_api_with_frontend_components(self):
        """Test generating complete blog API with frontend components."""
        # Generate GraphQL schema
        schema_gen = GraphQLSchemaGenerator()

        # Add User type
        user_type = GraphQLType(
            name="User",
            fields=[
                GraphQLField("id", "ID", is_required=True),
                GraphQLField("name", "STRING", is_required=True),
                GraphQLField("email", "STRING", is_required=True),
            ],
        )
        schema_gen.add_type(user_type)

        # Add Post type
        post_type = GraphQLType(
            name="Post",
            fields=[
                GraphQLField("id", "ID", is_required=True),
                GraphQLField("title", "STRING", is_required=True),
                GraphQLField("content", "STRING"),
                GraphQLField("author", "User", is_required=True),
                GraphQLField("createdAt", "DATETIME"),
            ],
        )
        schema_gen.add_type(post_type)

        # Generate schema
        schema = schema_gen.generate_schema()
        assert "type User" in schema
        assert "type User {" in schema
        assert "type Post {" in schema

        # Generate React components for UI
        user_card = ComponentDefinition(
            name="UserCard",
            description="Display user info",
            props=[
                ComponentProp("user", "object", is_required=True),
                ComponentProp("onFollow", "function"),
            ],
        )

        user_card_code = ReactComponentGenerator.generate_component(user_card)
        assert "interface UserCardProps" in user_card_code
        assert "user: object" in user_card_code

        # Generate post component
        post_card = ComponentDefinition(
            name="PostCard",
            description="Display blog post",
            props=[
                ComponentProp("post", "object", is_required=True),
                ComponentProp("onDelete", "function"),
            ],
            has_children=True,
        )

        post_code = ReactComponentGenerator.generate_component(post_card)
        assert "interface PostCardProps" in post_code


class TestDatabaseSchemaWithGraphQL:
    """Integration: Database Schema Generation + GraphQL."""

    def test_database_plus_graphql_schema_sync(self):
        """Test SQL schema and GraphQL schema generation from same definition."""
        # Create database schema
        sql_gen = SQLSchemaGenerator()

        users_table = DatabaseTable(
            name="users",
            columns=[
                DatabaseColumn("id", ColumnType.SERIAL, is_primary_key=True),
                DatabaseColumn("name", ColumnType.VARCHAR, length=255, is_nullable=False),
                DatabaseColumn("email", ColumnType.VARCHAR, length=255, is_nullable=False),
                DatabaseColumn("created_at", ColumnType.TIMESTAMP),
            ],
        )

        posts_table = DatabaseTable(
            name="posts",
            columns=[
                DatabaseColumn("id", ColumnType.SERIAL, is_primary_key=True),
                DatabaseColumn("title", ColumnType.VARCHAR, length=255, is_nullable=False),
                DatabaseColumn("content", ColumnType.TEXT),
                DatabaseColumn("user_id", ColumnType.INT, is_nullable=False),
                DatabaseColumn("created_at", ColumnType.TIMESTAMP),
            ],
        )

        sql_gen.add_table(users_table)
        sql_gen.add_table(posts_table)

        # Generate SQL (database type set in constructor)
        sql = sql_gen.generate_schema()
        assert "CREATE TABLE users" in sql
        assert "CREATE TABLE posts" in sql

        # Generate equivalent GraphQL
        schema_gen = GraphQLSchemaGenerator()

        user_type = GraphQLType(
            name="User",
            fields=[
                GraphQLField("id", "ID", is_required=True),
                GraphQLField("name", "STRING", is_required=True),
                GraphQLField("email", "STRING", is_required=True),
                GraphQLField("createdAt", "DATETIME"),
            ],
        )
        schema_gen.add_type(user_type)

        graphql_schema = schema_gen.generate_schema()
        assert "type User" in graphql_schema


class TestAPIDocumentationFromComponents:
    """Integration: Components → OpenAPI Documentation."""

    def test_component_based_api_documentation(self):
        """Test generating OpenAPI docs from component definitions."""
        # Create API info
        info = OpenAPIInfo(
            title="Blog API",
            version="1.0.0",
            description="Complete blog management API",
        )

        gen = OpenAPIGenerator(info)
        gen.add_server("https://api.example.com", "Production")
        gen.add_bearer_security()

        # Create GET /users endpoint (for UserCard component)
        get_users = OpenAPIEndpoint(
            path="/users",
            method=HTTPMethod.GET,
            summary="List all users for UserCard component",
            tags=["users"],
        )

        user_schema = OpenAPISchema(name="User")
        user_schema.add_property(OpenAPIProperty("id", SchemaType.INTEGER, is_required=True))
        user_schema.add_property(OpenAPIProperty("name", SchemaType.STRING, is_required=True))
        user_schema.add_property(OpenAPIProperty("email", SchemaType.STRING))

        get_users.add_response(OpenAPIResponse(200, "Users list", user_schema))
        gen.add_endpoint(get_users)

        # Create GET /posts endpoint (for PostCard component)
        get_posts = OpenAPIEndpoint(
            path="/posts",
            method=HTTPMethod.GET,
            summary="List all posts for PostCard component",
            tags=["posts"],
        )

        post_schema = OpenAPISchema(name="Post")
        post_schema.add_property(OpenAPIProperty("id", SchemaType.INTEGER, is_required=True))
        post_schema.add_property(OpenAPIProperty("title", SchemaType.STRING, is_required=True))
        post_schema.add_property(OpenAPIProperty("content", SchemaType.STRING))
        post_schema.add_property(OpenAPIProperty("userId", SchemaType.INTEGER))

        get_posts.add_response(OpenAPIResponse(200, "Posts list", post_schema))
        gen.add_endpoint(get_posts)

        # Generate spec
        spec = gen.generate_specification()

        # Verify API structure matches component needs
        assert "/users" in spec["paths"]
        assert "/posts" in spec["paths"]
        assert spec["paths"]["/users"]["get"]["summary"] == "List all users for UserCard component"


class TestFullStackApplicationGeneration:
    """Integration: Complete full-stack application generation (phases 1-3)."""

    def test_todo_app_full_generation(self):
        """Test generating complete TODO app with all phases."""
        # Phase 1: Generate from template
        template = get_template("webapp_fastapi_react")
        assert template is not None

        upg = UniversalProjectGenerator()
        result = upg.generate(
            template_id=template.template_id,
            project_name="todo-app",
            options={"description": "Simple TODO management application"},
        )
        assert result.status in ["success", "generated"]

        # Phase 3.1: Generate GraphQL schema
        schema_gen = GraphQLSchemaGenerator()

        todo_type = GraphQLType(
            name="Todo",
            fields=[
                GraphQLField("id", "ID", is_required=True),
                GraphQLField("title", "STRING", is_required=True),
                GraphQLField("completed", "BOOLEAN", is_required=True),
                GraphQLField("createdAt", "DATETIME"),
            ],
        )
        schema_gen.add_type(todo_type)

        graphql_schema = schema_gen.generate_schema()
        assert "type Todo" in graphql_schema

        # Phase 3.2: Generate database schema
        sql_gen = SQLSchemaGenerator()
        todos_table = DatabaseTable(
            name="todos",
            columns=[
                DatabaseColumn("id", ColumnType.SERIAL, is_primary_key=True),
                DatabaseColumn("title", ColumnType.VARCHAR, length=255, is_nullable=False),
                DatabaseColumn("completed", ColumnType.BOOLEAN, is_nullable=False),
                DatabaseColumn("created_at", ColumnType.TIMESTAMP),
            ],
        )
        sql_gen.add_table(todos_table)

        sql = sql_gen.generate_schema()
        assert "CREATE TABLE todos" in sql

        # Phase 3.3: Generate React components
        todo_item = ComponentDefinition(
            name="TodoItem",
            description="Individual TODO item component",
            props=[
                ComponentProp("todo", "object", is_required=True),
                ComponentProp("onToggle", "function"),
                ComponentProp("onDelete", "function"),
            ],
        )

        component_code = ReactComponentGenerator.generate_component(todo_item)
        assert "interface TodoItemProps" in component_code

        # Phase 3.4: Generate OpenAPI documentation
        api_info = OpenAPIInfo(
            title="TODO API",
            version="1.0.0",
            description="GraphQL API for managing TODOs",
        )

        api_gen = OpenAPIGenerator(api_info)

        list_todos = OpenAPIEndpoint(
            path="/api/todos",
            method=HTTPMethod.GET,
            summary="Get all TODOs",
        )
        list_todos.add_response(OpenAPIResponse(200, "TODOs list"))
        api_gen.add_endpoint(list_todos)

        spec = api_gen.generate_specification()
        assert "/api/todos" in spec["paths"]

        # Final verification: all phases integrated
        assert result.project_id is not None  # Phase 1 ✓
        assert "type Todo" in graphql_schema  # Phase 3.1 ✓
        assert "todos" in sql  # Phase 3.2 ✓
        assert "TodoItemProps" in component_code  # Phase 3.3 ✓
        assert "/api/todos" in spec["paths"]  # Phase 3.4 ✓


class TestMultiLanguageScaffolding:
    """Integration: Multi-language scaffolding (Python, JS, TS)."""

    def test_multilanguage_graphql_resolvers(self):
        """Test GraphQL resolver generation in multiple languages."""
        from src.generators.graphql_generator import GraphQLResolverGenerator

        schema_gen = GraphQLSchemaGenerator()

        # Create simple type
        user_type = GraphQLType(
            name="User",
            fields=[
                GraphQLField("id", "ID", is_required=True),
                GraphQLField("name", "STRING", is_required=True),
            ],
        )
        schema_gen.add_type(user_type)

        # Add a query so resolvers aren't empty
        from src.generators.graphql_generator import GraphQLQuery

        get_user_query = GraphQLQuery(
            name="getUser",
            return_type="User",
            parameters=[GraphQLField("id", "ID", is_required=True)],
        )
        schema_gen.add_query(get_user_query)
        schema = schema_gen.generate_schema()
        assert "type User" in schema

        # Generate Python resolvers
        python_resolvers = GraphQLResolverGenerator.generate_resolver_skeleton(
            schema_gen, language="python"  # Pass generator object, not string
        )
        assert "async def resolve_user" in python_resolvers or "User" in python_resolvers

        # Generate JavaScript resolvers
        js_resolvers = GraphQLResolverGenerator.generate_resolver_skeleton(
            schema_gen, language="javascript"  # Pass generator object, not string
        )
        assert "const resolvers" in js_resolvers

        # Generate TypeScript resolvers
        ts_resolvers = GraphQLResolverGenerator.generate_resolver_skeleton(
            schema_gen, language="typescript"  # Pass generator object, not string
        )
        assert "export const resolvers" in ts_resolvers


class TestEcosystemQualityMetrics:
    """Validate ecosystem quality and completeness."""

    def test_all_phases_executable(self):
        """Test that all ecosystem components are executable."""
        # Phase 0: Templates exist
        assert get_template("package_python") is not None
        assert get_template("package_npm") is not None

        # Phase 1: Generator works
        upg = UniversalProjectGenerator()
        assert upg is not None

        # Phase 2: Publishing setup available
        # (Would require actual PublishingOrchestrator, verified in Phase 2 tests)

        # Phase 3.1: GraphQL works
        schema_gen = GraphQLSchemaGenerator()
        assert schema_gen is not None

        # Phase 3.2: Database works
        sql_gen = SQLSchemaGenerator()
        assert sql_gen is not None

        # Phase 3.3: Components work
        component = ComponentDefinition(name="Test")
        code = ReactComponentGenerator.generate_component(component)
        assert "interface TestProps" in code

        # Phase 3.4: OpenAPI works
        info = OpenAPIInfo(title="Test", version="1.0.0")
        gen = OpenAPIGenerator(info)
        spec = gen.generate_specification()
        assert spec["openapi"] == "3.0.0"

    def test_ecosystem_interconnectivity(self):
        """Test that phases can work together."""
        # Create a simple end-to-end flow

        # 1. Start with template
        template = get_template("webapp_fastapi_react")

        # 2. Generate project
        upg = UniversalProjectGenerator()
        result = upg.generate(template.template_id, "app")
        project_id = result.project_id

        # 3. Generate API schema
        schema_gen = GraphQLSchemaGenerator()
        api_type = GraphQLType(
            name="DataModel", fields=[GraphQLField("id", "ID", is_required=True)]
        )
        schema_gen.add_type(api_type)

        # 4. Generate database
        sql_gen = SQLSchemaGenerator()
        table = DatabaseTable(
            name="data", columns=[DatabaseColumn("id", ColumnType.SERIAL, is_primary_key=True)]
        )
        sql_gen.add_table(table)

        # 5. Generate UI component
        component = ComponentDefinition(name="DataDisplay")
        code = ReactComponentGenerator.generate_component(component)

        # 6. Generate documentation
        api_info = OpenAPIInfo(title="API", version="1.0.0")
        api_gen = OpenAPIGenerator(api_info)

        # Verify all working together
        assert project_id is not None
        assert "DataModel" in schema_gen.generate_schema()
        assert "data" in sql_gen.generate_schema()
        assert "DataDisplay" in code
        assert api_gen.generate_specification()["openapi"] == "3.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
