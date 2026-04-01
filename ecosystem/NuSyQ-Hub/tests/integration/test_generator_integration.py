"""Integration tests for Phase 3 generator orchestration.

Tests end-to-end integration:
- AgentTaskRouter routing to generators
- Generator wrapper functions
- File generation and output
- Convenience function access

Author: GitHub Copilot
Created: 2025-12-26
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from src.orchestration.generator_integration import (
    generate_database_schema as generate_schema_wrapper,
)
from src.orchestration.generator_integration import (
    generate_graphql_api as generate_graphql_wrapper,
)
from src.orchestration.generator_integration import (
    generate_openapi_spec as generate_openapi_wrapper,
)
from src.orchestration.generator_integration import (
    generate_react_component as generate_component_wrapper,
)
from src.orchestration.generator_integration import (
    generate_universal_project as generate_project_wrapper,
)
from src.tools.agent_task_router import (
    AgentTaskRouter,
    generate_database_schema,
    generate_graphql_api,
    generate_openapi_spec,
    generate_react_component,
    generate_universal_project,
)


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp(prefix="nusyq_generator_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def router():
    """Create AgentTaskRouter instance with learner disabled for deterministic tests."""
    r = AgentTaskRouter()
    # Disable SpecializationLearner: live production data can reroute tasks
    # to real agents (e.g. lmstudio), making assertions non-deterministic.
    r._specialization_learner = False
    return r


# ============================================================================
# WRAPPER FUNCTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_graphql_wrapper_basic(temp_output_dir: Path) -> None:
    """Test GraphQL wrapper generates schema files."""
    result = await generate_graphql_wrapper(
        "User authentication API",
        {"entities": ["User"], "output_path": str(temp_output_dir)},
    )

    assert result["status"] == "success"
    assert result["generator"] == "graphql"
    assert "files" in result
    assert Path(result["output_path"]).exists()


@pytest.mark.asyncio
async def test_openapi_wrapper_basic(temp_output_dir: Path) -> None:
    """Test OpenAPI wrapper generates spec files."""
    result = await generate_openapi_wrapper(
        "Task management API",
        {
            "endpoints": [{"path": "/tasks", "methods": ["GET"]}],
            "output_path": str(temp_output_dir),
        },
    )

    assert result["status"] == "success"
    assert result["generator"] == "openapi"
    assert "files" in result


@pytest.mark.asyncio
async def test_react_component_wrapper_basic(temp_output_dir: Path) -> None:
    """Test React component wrapper generates component files."""
    result = await generate_component_wrapper(
        "Product card component",
        {"component_name": "ProductCard", "output_path": str(temp_output_dir)},
    )

    assert result["status"] == "success"
    assert result["generator"] == "component"
    assert "files" in result


@pytest.mark.asyncio
async def test_database_schema_wrapper_basic(temp_output_dir: Path) -> None:
    """Test database schema wrapper generates SQL files."""
    result = await generate_schema_wrapper(
        "User database schema",
        {"tables": [{"name": "users", "columns": []}], "output_path": str(temp_output_dir)},
    )

    assert result["status"] == "success"
    assert result["generator"] == "database"
    assert "files" in result


@pytest.mark.asyncio
async def test_universal_project_wrapper_basic(temp_output_dir: Path) -> None:
    """Test universal project wrapper generates project structure."""
    result = await generate_project_wrapper(
        "FastAPI microservice",
        {"project_type": "api", "language": "python", "output_path": str(temp_output_dir)},
    )

    assert result["status"] == "success"
    assert result["generator"] == "project"
    assert "files" in result


# ============================================================================
# ROUTER INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_router_graphql_integration(router: AgentTaskRouter, temp_output_dir: Path) -> None:
    """Test routing GraphQL task through AgentTaskRouter."""
    result = await router.route_task(
        "generate_graphql",
        "E-commerce product catalog",
        {"entities": ["Product", "Category"], "output_path": str(temp_output_dir)},
        "graphql",
    )

    assert result["status"] == "success"
    assert result["generator"] == "graphql"
    assert "files" in result


@pytest.mark.asyncio
async def test_router_openapi_integration(router: AgentTaskRouter, temp_output_dir: Path) -> None:
    """Test routing OpenAPI task through AgentTaskRouter."""
    result = await router.route_task(
        "generate_openapi",
        "User management REST API",
        {
            "endpoints": [{"path": "/users", "methods": ["GET", "POST"]}],
            "output_path": str(temp_output_dir),
        },
        "openapi",
    )

    assert result["status"] == "success"
    assert result["generator"] == "openapi"


@pytest.mark.asyncio
async def test_router_component_integration(router: AgentTaskRouter, temp_output_dir: Path) -> None:
    """Test routing React component task through AgentTaskRouter."""
    result = await router.route_task(
        "generate_component",
        "User profile card",
        {"component_name": "UserProfileCard", "output_path": str(temp_output_dir)},
        "component",
    )

    assert result["status"] == "success"
    assert result["generator"] == "component"


@pytest.mark.asyncio
async def test_router_database_integration(router: AgentTaskRouter, temp_output_dir: Path) -> None:
    """Test routing database schema task through AgentTaskRouter."""
    result = await router.route_task(
        "generate_database",
        "Authentication database",
        {
            "tables": [{"name": "users", "columns": []}, {"name": "sessions", "columns": []}],
            "output_path": str(temp_output_dir),
        },
        "database",
    )

    assert result["status"] == "success"
    assert result["generator"] == "database"


@pytest.mark.asyncio
async def test_router_project_integration(router: AgentTaskRouter, temp_output_dir: Path) -> None:
    """Test routing universal project task through AgentTaskRouter."""
    result = await router.route_task(
        "generate_project",
        "Express REST API server",
        {
            "project_type": "api",
            "language": "javascript",
            "framework": "express",
            "output_path": str(temp_output_dir),
        },
        "project",
    )

    assert result["status"] == "success"
    assert result["generator"] == "project"


# ============================================================================
# CONVENIENCE FUNCTION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_convenience_graphql(temp_output_dir: Path) -> None:
    """Test GraphQL convenience function."""
    result = await generate_graphql_api(
        "Blog API",
        {"entities": ["Post", "Comment"], "output_path": str(temp_output_dir)},
    )

    assert result["status"] == "success"
    assert result["generator"] == "graphql"


@pytest.mark.asyncio
async def test_convenience_openapi(temp_output_dir: Path) -> None:
    """Test OpenAPI convenience function."""
    result = await generate_openapi_spec(
        "Task tracker API",
        {
            "endpoints": [{"path": "/tasks", "methods": ["GET"]}],
            "output_path": str(temp_output_dir),
        },
    )

    assert result["status"] == "success"
    assert result["generator"] == "openapi"


@pytest.mark.asyncio
async def test_convenience_component(temp_output_dir: Path) -> None:
    """Test React component convenience function."""
    result = await generate_react_component(
        "Task list",
        {"component_name": "TaskList", "output_path": str(temp_output_dir)},
    )

    assert result["status"] == "success"
    assert result["generator"] == "component"


@pytest.mark.asyncio
async def test_convenience_database(temp_output_dir: Path) -> None:
    """Test database schema convenience function."""
    result = await generate_database_schema(
        "Task database",
        {"tables": [{"name": "tasks", "columns": []}], "output_path": str(temp_output_dir)},
    )

    assert result["status"] == "success"
    assert result["generator"] == "database"


@pytest.mark.asyncio
async def test_convenience_project(temp_output_dir: Path) -> None:
    """Test universal project convenience function."""
    result = await generate_universal_project(
        "Django web app",
        {
            "project_type": "web",
            "language": "python",
            "framework": "django",
            "output_path": str(temp_output_dir),
        },
    )

    assert result["status"] == "success"
    assert result["generator"] == "project"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_graphql_wrapper_invalid_context() -> None:
    """Test GraphQL wrapper handles invalid context gracefully."""
    result = await generate_graphql_wrapper("Test API", {"invalid_key": "value"})
    # Should handle gracefully, may use defaults or return error status
    assert "status" in result


@pytest.mark.asyncio
async def test_router_invalid_target_system(router: AgentTaskRouter) -> None:
    """Test router handles invalid target system gracefully."""
    # Router defaults invalid systems to 'auto' instead of raising
    result = await router.route_task("test", "description", {}, "invalid_system")
    # Should fall back to orchestrator submission
    assert result["status"] == "submitted"
    assert "task_id" in result


# ============================================================================
# MULTI-GENERATOR WORKFLOW TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_multi_generator_workflow(temp_output_dir: Path) -> None:
    """Test workflow using multiple generators sequentially."""
    # 1. Generate database schema
    db_result = await generate_database_schema(
        "E-commerce database",
        {
            "tables": [{"name": "products", "columns": []}],
            "output_path": str(temp_output_dir / "db"),
        },
    )
    assert db_result["status"] == "success"

    # 2. Generate GraphQL API
    api_result = await generate_graphql_api(
        "Product catalog API",
        {"entities": ["Product"], "output_path": str(temp_output_dir / "api")},
    )
    assert api_result["status"] == "success"

    # 3. Generate React component
    ui_result = await generate_react_component(
        "Product list component",
        {"component_name": "ProductList", "output_path": str(temp_output_dir / "ui")},
    )
    assert ui_result["status"] == "success"

    # All three generators completed successfully
    assert db_result["generator"] == "database"
    assert api_result["generator"] == "graphql"
    assert ui_result["generator"] == "component"


# ============================================================================
# FILE OUTPUT VERIFICATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_graphql_file_generation(temp_output_dir: Path) -> None:
    """Test GraphQL generator actually creates files."""
    result = await generate_graphql_api(
        "User API",
        {"entities": ["User"], "output_path": str(temp_output_dir)},
    )

    assert result["status"] == "success"
    output_path = Path(result["output_path"])
    assert output_path.exists()

    # Check common GraphQL files exist
    files = result.get("files", {})
    assert len(files) > 0


@pytest.mark.asyncio
async def test_component_file_generation(temp_output_dir: Path) -> None:
    """Test React component generator creates component files."""
    result = await generate_react_component(
        "Button component",
        {"component_name": "CustomButton", "output_path": str(temp_output_dir)},
    )

    assert result["status"] == "success"
    files = result.get("files", {})
    assert len(files) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
