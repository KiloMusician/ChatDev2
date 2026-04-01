"""Tests for MCP Server functionality."""

from __future__ import annotations

import json

import pytest


@pytest.fixture
def mcp_server():
    """Fixture to create MCP server instance."""
    from src.integration.mcp_server import MCPServer

    server = MCPServer(host="localhost", port=8081)  # Use different port for testing
    return server


@pytest.fixture
def mcp_client(mcp_server):
    """Fixture to create test client for MCP server."""
    return mcp_server.app.test_client()


def test_health_check(mcp_client):
    """Test health check endpoint."""
    response = mcp_client.get("/health")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert "uptime" in data
    assert "timestamp" in data


def test_list_tools(mcp_client):
    """Test listing available tools."""
    response = mcp_client.get("/tools")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert "tools" in data
    assert "count" in data
    assert data["count"] >= 6  # At least 6 default tools


def test_list_tools_content(mcp_client):
    """Test that default tools are registered."""
    response = mcp_client.get("/tools")
    data = json.loads(response.data)

    tool_names = [tool["name"] for tool in data["tools"]]
    assert "analyze_repository" in tool_names
    assert "get_context" in tool_names
    assert "orchestrate_task" in tool_names
    assert "generate_code" in tool_names
    assert "generate_tests" in tool_names
    assert "check_system_health" in tool_names


def test_execute_tool_missing_name(mcp_client):
    """Test executing tool without name."""
    response = mcp_client.post(
        "/execute", data=json.dumps({"parameters": {}}), content_type="application/json"
    )
    assert response.status_code == 400

    data = json.loads(response.data)
    assert not data["success"]
    assert "Tool name required" in data["error"]


def test_execute_tool_not_found(mcp_client):
    """Test executing non-existent tool."""
    response = mcp_client.post(
        "/execute",
        data=json.dumps({"tool": "nonexistent_tool", "parameters": {}}),
        content_type="application/json",
    )
    assert response.status_code == 404

    data = json.loads(response.data)
    assert not data["success"]
    assert "not found" in data["error"]


def test_execute_analyze_repository(mcp_client):
    """Test executing analyze_repository tool."""
    response = mcp_client.post(
        "/execute",
        data=json.dumps({"tool": "analyze_repository", "parameters": {"path": ".", "depth": 5}}),
        content_type="application/json",
    )
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["success"]
    assert data["tool_name"] == "analyze_repository"
    assert "result" in data
    assert data["result"]["status"] == "analysis_complete"


def test_execute_get_context(mcp_client):
    """Test executing get_context tool."""
    response = mcp_client.post(
        "/execute",
        data=json.dumps(
            {
                "tool": "get_context",
                "parameters": {"context_type": "agent", "context_id": "test"},
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["success"]
    assert data["tool_name"] == "get_context"


def test_execute_orchestrate_task(mcp_client):
    """Test executing orchestrate_task tool."""
    response = mcp_client.post(
        "/execute",
        data=json.dumps(
            {
                "tool": "orchestrate_task",
                "parameters": {"task_description": "Test task", "priority": "high"},
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["success"]
    assert "task_id" in data["result"]
    assert data["result"]["status"] == "queued"


def test_execute_generate_code(mcp_client):
    """Test executing generate_code tool."""
    response = mcp_client.post(
        "/execute",
        data=json.dumps(
            {
                "tool": "generate_code",
                "parameters": {
                    "language": "python",
                    "description": "Function to add two numbers",
                },
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["success"]
    assert data["result"]["language"] == "python"


def test_execute_check_system_health(mcp_client):
    """Test executing check_system_health tool."""
    response = mcp_client.post(
        "/execute",
        data=json.dumps(
            {"tool": "check_system_health", "parameters": {"include_ai_systems": True}}
        ),
        content_type="application/json",
    )
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["success"]
    assert data["result"]["status"] == "healthy"
    assert data["result"]["ai_systems"] is not None


def test_server_status(mcp_client):
    """Test server status endpoint."""
    response = mcp_client.get("/status")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["status"] == "running"
    assert "uptime" in data
    assert "request_count" in data
    assert "tool_count" in data


def test_server_metrics(mcp_client):
    """Test server metrics endpoint."""
    # Execute a tool first to generate metrics
    mcp_client.post(
        "/execute",
        data=json.dumps({"tool": "check_system_health", "parameters": {}}),
        content_type="application/json",
    )

    response = mcp_client.get("/metrics")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert "uptime_seconds" in data
    assert "total_requests" in data
    assert "total_tool_executions" in data
    assert data["total_tool_executions"] >= 1


def test_tool_execution_tracking(mcp_client):
    """Test that tool executions are tracked."""
    # Execute same tool multiple times
    for _ in range(3):
        mcp_client.post(
            "/execute",
            data=json.dumps({"tool": "check_system_health", "parameters": {}}),
            content_type="application/json",
        )

    # Check metrics
    response = mcp_client.get("/metrics")
    data = json.loads(response.data)

    assert data["total_tool_executions"] >= 3


def test_execute_missing_required_parameter(mcp_client):
    """Test executing tool with missing required parameter."""
    response = mcp_client.post(
        "/execute",
        data=json.dumps(
            {"tool": "analyze_repository", "parameters": {}}
        ),  # Missing 'path' parameter
        content_type="application/json",
    )
    assert response.status_code == 200  # Returns 200 but with error in response

    data = json.loads(response.data)
    assert not data["success"]
    assert "missing" in data["error"].lower()


def test_execution_timing(mcp_client):
    """Test that execution time is tracked."""
    response = mcp_client.post(
        "/execute",
        data=json.dumps({"tool": "check_system_health", "parameters": {}}),
        content_type="application/json",
    )

    data = json.loads(response.data)
    assert "execution_time" in data
    assert data["execution_time"] >= 0
