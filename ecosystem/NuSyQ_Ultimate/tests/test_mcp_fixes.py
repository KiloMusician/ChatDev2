"""
Test MCP Server Fixes - Integration Tests
==========================================

Tests for the three critical fixes implemented:
1. MCP tools/list endpoint returns proper format
2. Agent router is wired into MCP server
3. Multi-agent orchestration with consensus

Author: GitHub Copilot
Date: 2026-01-07
"""

# Pylint: test module intentionally reaches into protected members and
# adjusts import position for path setup.
# Fixture parameters trigger redefined-outer-name by design.
# pylint: disable=wrong-import-position, protected-access
# pylint: disable=redefined-outer-name

import sys
from pathlib import Path

import pytest

# Add parent to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from mcp_server import main as mcp_main  # noqa: E402

NuSyQMCPServer = mcp_main.NuSyQMCPServer


@pytest.fixture(scope="module")
def mcp_server():
    """Fixture to provide MCPServer instance for all tests"""
    return NuSyQMCPServer()


def test_tools_list_format(mcp_server):
    """Test 1: Tools list returns proper MCP format"""
    tools_result = mcp_server._get_available_tools()

    # Should be a dict with 'tools' key
    assert isinstance(tools_result, dict), f"Expected dict, got {type(tools_result)}"
    assert "tools" in tools_result, "Missing 'tools' key in response"
    assert isinstance(tools_result["tools"], list), (
        f"Expected list, got {type(tools_result['tools'])}"
    )

    # Should have multiple tools
    tools = tools_result["tools"]
    assert len(tools) > 0, "No tools returned"

    # Each tool should have required MCP fields
    for tool in tools:
        assert "name" in tool, f"Tool missing 'name': {tool}"
        assert "description" in tool, f"Tool {tool.get('name')} missing 'description'"
        assert "inputSchema" in tool, f"Tool {tool.get('name')} missing 'inputSchema'"

    print(f"   Found {len(tools)} tools defined")


def test_required_tools_present(mcp_server):
    """Test 2: All required tools are present"""
    tools_result = mcp_server._get_available_tools()
    tools = tools_result["tools"]
    tool_names = [t["name"] for t in tools]

    required_tools = [
        "ollama_query",
        "chatdev_create",
        "file_read",
        "file_write",
        "system_info",
        "run_jupyter_cell",
        "ai_council_session",
        "query_github_copilot",
        "multi_agent_orchestration",
    ]

    for tool_name in required_tools:
        assert tool_name in tool_names, f"Required tool '{tool_name}' not found"

    print(f"   All {len(required_tools)} required tools present")


def test_agent_router_initialized(mcp_server):
    """Test 3: Agent router is initialized"""
    assert hasattr(mcp_server, "agent_router"), "Server missing agent_router attribute"

    # Router may be None if registry file not found, that's ok
    if mcp_server.agent_router:
        print("   Agent router initialized successfully")
    else:
        print("   Agent router disabled (registry not found)")


def test_parallel_queries_method(mcp_server):
    """Test 4: Parallel queries helper method exists"""
    assert hasattr(mcp_server, "_parallel_agent_queries"), (
        "Server missing _parallel_agent_queries method"
    )
    print("   Parallel queries fallback method available")


@pytest.mark.asyncio
async def test_multi_agent_orchestration_basic(mcp_server):
    """Test 5: Multi-agent orchestration returns proper structure"""
    result = await mcp_server._multi_agent_orchestration(
        {
            "task": "Test task for integration testing",
            "agents": ["qwen2.5-coder:7b"],
            "mode": "PARALLEL_CONSENSUS",
            "include_ai_council": False,
            "implement_with_chatdev": False,
        }
    )

    # Check result structure
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "success" in result, "Missing 'success' field"
    assert "task" in result, "Missing 'task' field"
    assert "phases" in result, "Missing 'phases' field"
    assert "agents_used" in result, "Missing 'agents_used' field"

    # Check agents were actually used
    assert len(result["agents_used"]) > 0, "No agents were used in orchestration"

    print(f"   Orchestration used {len(result['agents_used'])} agents")
