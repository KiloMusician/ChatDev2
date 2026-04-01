"""ChatDev Complete MCP Integration - Full Tool Wiring.

Integrates ChatDev MCP server with Tool Registry and Project Indexer
into unified NuSyQ MCP server. Provides comprehensive access to:
  - ChatDev project generation/management
  - Hub code quality utilities (Black, Ruff, Pytest)
  - Project semantic search and indexing
  - Quest system logging

OmniTag: {
    "purpose": "Full ChatDev ecosystem MCP integration",
    "dependencies": ["chatdev_mcp_server", "chatdev_tool_registry", "chatdev_project_indexer"],
    "context": "Unified MCP tool orchestration, Phase 2 implementation",
    "evolution_stage": "v1.0"
}
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Setup path for imports
hub_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(hub_root))

from src.config.feature_flag_manager import get_feature_flag_manager
from src.integration.chatdev_mcp_server import get_chatdev_mcp_server
from src.integration.chatdev_tool_registry import get_chatdev_tool_registry
from src.rag.chatdev_project_indexer import get_chatdev_project_indexer


class ChatDevMCPIntegration:
    """Complete integration of ChatDev with NuSyQ MCP server."""

    def __init__(self):
        """Initialize integration."""
        self.feature_flag_manager = get_feature_flag_manager()
        self.chatdev_server: Any | None = None
        self.tool_registry: Any | None = None
        self.project_indexer: Any | None = None
        self.is_initialized = False
        self.registered_tools: list[str] = []

    def initialize_all_components(self) -> bool:
        """Initialize all ChatDev components.

        Returns:
            True if successful
        """
        # Check feature flag
        if not self.feature_flag_manager.is_feature_enabled("chatdev_mcp_enabled"):
            logger.warning("ChatDev MCP disabled via feature flag")
            return False

        try:
            # Initialize all components
            self.chatdev_server = get_chatdev_mcp_server()
            self.tool_registry = get_chatdev_tool_registry()
            self.project_indexer = get_chatdev_project_indexer()

            self.is_initialized = True

            logger.info("✅ All ChatDev components initialized")
            logger.info(f"   • ChatDev MCP Server: {4} tools")
            logger.info(f"   • Tool Registry: {len(self.tool_registry.tools)} tools")
            logger.info(
                f"   • Project Indexer: {len(self.project_indexer.indexed_projects)} projects indexed"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False

    def get_complete_tool_manifest(self) -> list[dict[str, Any]]:
        """Get complete tool manifest from all components.

        Returns:
            List of all tool definitions
        """
        if not self.is_initialized:
            return []

        chatdev_server = self.chatdev_server
        tool_registry = self.tool_registry
        if chatdev_server is None or tool_registry is None:
            return []

        manifest: list[dict[str, Any]] = []

        # ChatDev MCP tools (4 tools) - extract from mcp_tools
        for tool in chatdev_server.mcp_tools:
            manifest.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.input_schema,
                }
            )

        # Hub utility tools (5 tools: Black, Ruff, Pytest, Quest, Health)
        manifest.extend(tool_registry.export_manifest())

        # Project indexing tools (3 tools)
        manifest.extend(self._get_indexing_tools_manifest())

        return manifest

    def _get_indexing_tools_manifest(self) -> list[dict[str, Any]]:
        """Get project indexing tool definitions.

        Returns:
            Tool manifest items
        """
        return [
            {
                "name": "chatdev_search_projects",
                "description": "Search indexed ChatDev projects by semantic similarity",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "top_k": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "chatdev_index_workspace",
                "description": "Index/re-index ChatDev workspace projects",
                "inputSchema": {
                    "type": "object",
                    "properties": {"start_fresh": {"type": "boolean", "default": False}},
                },
            },
            {
                "name": "chatdev_project_summary",
                "description": "Get metadata for indexed project",
                "inputSchema": {
                    "type": "object",
                    "properties": {"project_name": {"type": "string"}},
                    "required": ["project_name"],
                },
            },
        ]

    async def handle_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle tool call from NuSyQ MCP server.

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if not self.is_initialized:
            return {"success": False, "error": "ChatDev not initialized"}
        chatdev_server = self.chatdev_server
        tool_registry = self.tool_registry
        if chatdev_server is None or tool_registry is None:
            return {"success": False, "error": "ChatDev components unavailable"}

        # Route to appropriate handler
        if tool_name.startswith("chatdev_") and tool_name not in [
            "chatdev_search_projects",
            "chatdev_index_workspace",
            "chatdev_project_summary",
        ]:
            # ChatDev MCP server tools
            result = chatdev_server.handle_tool_call(tool_name, arguments)
            return result if isinstance(result, dict) else {"success": True, "result": result}
        elif (
            tool_name.startswith("run_")
            or tool_name.startswith("check_")
            or tool_name.startswith("log_")
        ):
            # Tool registry utilities
            tool_result = await tool_registry.invoke_tool(
                tool_name, arguments, caller_role="Agent", environment="development"
            )
            return (
                tool_result
                if isinstance(tool_result, dict)
                else {"success": True, "result": tool_result}
            )
        elif tool_name == "chatdev_search_projects":
            return await self._handle_search_projects(**arguments)
        elif tool_name == "chatdev_index_workspace":
            return await self._handle_index_workspace(**arguments)
        elif tool_name == "chatdev_project_summary":
            return await self._handle_project_summary(**arguments)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    async def _handle_search_projects(self, query: str, top_k: int = 5) -> dict[str, Any]:
        """Handle project search.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Search results
        """
        project_indexer = self.project_indexer
        if project_indexer is None:
            return {"success": False, "error": "Project indexer unavailable"}
        try:
            results = project_indexer.search_projects(query, top_k=top_k)

            return {
                "success": True,
                "query": query,
                "results_count": len(results),
                "results": results,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_index_workspace(self, start_fresh: bool = False) -> dict[str, Any]:
        """Handle workspace indexing.

        Args:
            start_fresh: Clear existing index

        Returns:
            Indexing results
        """
        project_indexer = self.project_indexer
        if project_indexer is None:
            return {"success": False, "error": "Project indexer unavailable"}
        try:
            count = project_indexer.index_workspace(start_fresh=start_fresh)

            return {
                "success": True,
                "indexed_projects": count,
                "total_documents": len(project_indexer.documents),
                "status": "complete",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _handle_project_summary(self, project_name: str) -> dict[str, Any]:
        """Handle project summary request.

        Args:
            project_name: Project name

        Returns:
            Project metadata
        """
        project_indexer = self.project_indexer
        if project_indexer is None:
            return {"success": False, "error": "Project indexer unavailable"}
        try:
            project = project_indexer.indexed_projects.get(project_name)

            if not project:
                return {"success": False, "error": f"Project not found: {project_name}"}

            doc_count = len(
                [d for d in project_indexer.documents if d.project_name == project_name]
            )

            return {"success": True, "project": project.__dict__, "document_count": doc_count}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_all_tools(self) -> list[str]:
        """List all available tools.

        Returns:
            Tool names
        """
        if not self.is_initialized:
            return []
        chatdev_server = self.chatdev_server
        tool_registry = self.tool_registry
        if chatdev_server is None or tool_registry is None:
            return []

        tools: list[str] = []

        # ChatDev MCP tools
        for t in chatdev_server.mcp_tools:
            tools.append(t.name)

        # Tool registry
        for t in tool_registry.tools.values():
            tools.append(t.name)

        # Indexing tools
        tools.extend(
            ["chatdev_search_projects", "chatdev_index_workspace", "chatdev_project_summary"]
        )

        return sorted(tools)


# Global instance
_integration: ChatDevMCPIntegration | None = None


def get_chatdev_mcp_integration() -> ChatDevMCPIntegration:
    """Get global integration instance.

    Returns:
        ChatDevMCPIntegration instance
    """
    global _integration
    if _integration is None:
        _integration = ChatDevMCPIntegration()
    return _integration


async def test_complete_integration():
    """Test complete ChatDev MCP integration."""
    logger.info("=" * 70)
    logger.info("PHASE 2: ChatDev Complete MCP Integration Test")
    logger.info("=" * 70)

    integration = get_chatdev_mcp_integration()

    # Initialize
    logger.info("\n1️⃣  Initializing all components...")
    if not integration.initialize_all_components():
        logger.error("Failed to initialize")
        return

    logger.info("   ✅ Components initialized")

    # Get manifest
    logger.info("\n2️⃣  Getting complete tool manifest...")
    manifest = integration.get_complete_tool_manifest()
    logger.info(f"   ✅ {len(manifest)} total tools available")

    # List all tools
    logger.info("\n3️⃣  Available Tools:")
    tools = integration.list_all_tools()
    for i, tool in enumerate(tools, 1):
        category = "🤖" if "chatdev" in tool else "🔧"
        logger.info(f"   {category} {i:2d}. {tool}")

    # Test sample tools
    logger.info("\n4️⃣  Testing sample tools...")
    chatdev_server = integration.chatdev_server
    tool_registry = integration.tool_registry
    project_indexer = integration.project_indexer
    if chatdev_server is None or tool_registry is None or project_indexer is None:
        logger.error("   ❌ Integration components unavailable after initialization")
        return

    # Test ChatDev list_projects
    logger.info("   Testing: chatdev_list_projects")
    result = chatdev_server.list_projects()
    if result.get("success"):
        count = len(result.get("projects", []))
        logger.info(f"   ✅ Found {count} projects")

    # Test tool registry access
    logger.info("   Testing: get_tools_for_role(Programmer)")
    programmer_tools = tool_registry.get_tools_for_role("Programmer")
    logger.info(f"   ✅ Programmer has {len(programmer_tools)} tools")

    # Test project indexer
    logger.info("   Testing: project indexer status")
    indexed = len(project_indexer.indexed_projects)
    docs = len(project_indexer.documents)
    logger.info(f"   ✅ {indexed} projects indexed, {docs} documents")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("✅ PHASE 2 INTEGRATION COMPLETE")
    logger.info("   • ChatDev MCP: 4 tools")
    logger.info(f"   • Tool Registry: {len(tool_registry.tools)} tools")
    logger.info(f"   • Project Indexer: {indexed} projects, {docs} documents")
    logger.info(f"   • Total: {len(tools)} tools ready for agents")
    logger.info("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(test_complete_integration())
