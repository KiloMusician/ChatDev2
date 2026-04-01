"""ChatDev MCP Server Wrapper.

Exposes ChatDev as a Model Context Protocol (MCP) server for uniform
agent coordination. Inspired by fuzemobi/ChatDevMCP.

OmniTag: {
    "purpose": "ChatDev MCP server integration",
    "dependencies": ["chatdev2", "mcp_server", "agent_task_router"],
    "context": "Multi-agent coordination, uniform tool interface",
    "evolution_stage": "v1.0"
}
"""

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add repo root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.chatdev2_config import ChatDev2Config, get_chatdev2_config
from src.config.feature_flag_manager import is_feature_enabled
from src.integration.chatdev_resilience_handler import (
    ResilientChatDevHandler, create_ollama_runner, load_resilience_config)
from src.resilience.mission_control_attestation import AuditLog

logger = logging.getLogger(__name__)

# Module-level constants
DEFAULT_MODEL_NAME = "qwen2.5-coder:7b"
OLLAMA_MODEL_DESC = "Ollama model to use"
FEATURE_DISABLED_MSG = "ChatDev MCP feature is disabled"


@dataclass
class MCPToolDefinition:
    """MCP tool definition for ChatDev operations."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: str  # Method name to call


class ChatDevMCPServer:
    """MCP server wrapper for ChatDev.

    Provides standardized tool interface for ChatDev operations,
    allowing other agents (Copilot, Ollama, Consciousness) to invoke
    ChatDev uniformly via MCP protocol.

    Features:
    - Standardized ChatDev tool registration
    - Async operation support
    - Progress tracking and logging
    - Integration with NuSyQ MCP server
    - Feature flag gating
    """

    def __init__(self, chatdev_config: ChatDev2Config | None = None):
        """Initialize ChatDev MCP server.

        Args:
            chatdev_config: Optional ChatDev2Config instance
        """
        self.config = chatdev_config or get_chatdev2_config()
        self.mcp_tools: list[MCPToolDefinition] = []
        self.audit_log = AuditLog()
        self.resilient_handler = self._build_resilient_handler()
        self._register_tools()

    def _build_resilient_handler(self) -> ResilientChatDevHandler:
        """Create a ResilientChatDevHandler for ChatDev operations.

        Uses config/chatdev_resilience_config.json for Ollama fallback settings.
        When OpenAI fails (429, quota, timeout), automatically switches to local Ollama.
        """
        config = load_resilience_config()

        # Bind primary runner to OpenAI-backed ChatDev
        async def primary_runner(
            task: str, model: str = DEFAULT_MODEL_NAME, name: str | None = None
        ):
            return await self._run_chatdev_generate(
                task=task, model=model, name=name, degraded=False
            )

        # Use config-driven Ollama runner for fallback
        fallback_model = config.get("fallback_chain", [{}])[0].get("model", "qwen2.5-coder:7b")
        ollama_runner = create_ollama_runner(model=fallback_model, config=config)

        return ResilientChatDevHandler(
            primary_runner=primary_runner,
            degraded_runner=ollama_runner,
            audit_log=self.audit_log,
        )

    def _register_tools(self) -> None:
        """Register ChatDev tools with MCP protocol."""
        # Tool: Generate Software Project
        self.mcp_tools.append(
            MCPToolDefinition(
                name="chatdev_generate_project",
                description="Generate a software project using ChatDev multi-agent team",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Project description/requirements",
                        },
                        "model": {
                            "type": "string",
                            "description": OLLAMA_MODEL_DESC,
                            "default": DEFAULT_MODEL_NAME,
                        },
                        "name": {"type": "string", "description": "Project name (optional)"},
                    },
                    "required": ["task"],
                },
                handler="generate_project",
            )
        )

        # Tool: Continue Project Development
        self.mcp_tools.append(
            MCPToolDefinition(
                name="chatdev_continue_project",
                description="Continue development on an existing ChatDev project",
                input_schema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to existing project",
                        },
                        "task": {
                            "type": "string",
                            "description": "Additional requirements or changes",
                        },
                        "model": {
                            "type": "string",
                            "description": OLLAMA_MODEL_DESC,
                            "default": DEFAULT_MODEL_NAME,
                        },
                    },
                    "required": ["project_path", "task"],
                },
                handler="continue_project",
            )
        )

        # Tool: Review Project
        self.mcp_tools.append(
            MCPToolDefinition(
                name="chatdev_review_project",
                description="Review a ChatDev project for quality and issues",
                input_schema={
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to project to review",
                        },
                        "model": {
                            "type": "string",
                            "description": "Ollama model to use",
                            "default": "qwen2.5-coder:14b",
                        },
                    },
                    "required": ["project_path"],
                },
                handler="review_project",
            )
        )

        # Tool: List Projects
        self.mcp_tools.append(
            MCPToolDefinition(
                name="chatdev_list_projects",
                description="List all ChatDev generated projects",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Max number of projects to return",
                            "default": 10,
                        }
                    },
                },
                handler="list_projects",
            )
        )

    async def generate_project(
        self, task: str, model: str = DEFAULT_MODEL_NAME, name: str | None = None
    ) -> dict[str, Any]:
        """Generate a software project using ChatDev with resilience wrapper."""
        if not is_feature_enabled("chatdev_mcp_enabled"):
            return {
                "success": False,
                "error": "ChatDev MCP feature is disabled",
                "help": "Enable 'chatdev_mcp_enabled' in feature_flags.json",
            }

        logger.info(f"🚀 ChatDev MCP: Generating project - {task[:50]}...")

        # Delegate to resilient handler for checkpoint/retry/degraded + attestation
        result = await self.resilient_handler.execute_generate_project(
            task=task,
            model=model,
            agent="chatdev_mcp_server",
            use_sandbox=False,
            project_name=name,
            operation="chatdev_generate_project",
        )

        return result

    async def continue_project(
        self, project_path: str, task: str, model: str = DEFAULT_MODEL_NAME
    ) -> dict[str, Any]:
        """Continue development on existing project.

        Args:
            project_path: Path to existing project
            task: Additional requirements
            model: Ollama model to use

        Returns:
            Result dictionary
        """
        if not is_feature_enabled("chatdev_mcp_enabled"):
            return {"success": False, "error": "ChatDev MCP feature is disabled"}

        logger.info(f"🔄 ChatDev MCP: Continuing project - {project_path}")

        # Use degraded fallback pathway until incremental support exists
        return await self.resilient_handler.execute_generate_project(
            task=f"Continue project: {task}",
            model=model,
            agent="chatdev_mcp_server",
            project_name=Path(project_path).name,
            operation="chatdev_continue_project",
        )

    async def review_project(
        self, project_path: str, model: str = "qwen2.5-coder:14b"
    ) -> dict[str, Any]:
        """Review a ChatDev project.

        Args:
            project_path: Path to project
            model: Ollama model to use

        Returns:
            Review results
        """
        if not is_feature_enabled("chatdev_mcp_enabled"):
            return {"success": False, "error": "ChatDev MCP feature is disabled"}

        logger.info(f"🔍 ChatDev MCP: Reviewing project - {project_path}")

        # Implementation: Analyze project files and generate review
        project = Path(project_path)

        if not project.exists():
            return {"success": False, "error": "Project not found"}

        files = list(project.rglob("*.py"))

        # Lightweight review routed through resilient handler (placeholder primary)
        review_result = await self.resilient_handler.execute_generate_project(
            task=f"Review project at {project_path}",
            model=model,
            agent="chatdev_mcp_server",
            project_name=Path(project_path).name,
            operation="chatdev_review_project",
        )

        review_result.setdefault("project_path", str(project))
        review_result.setdefault("total_files", len(files))
        review_result.setdefault(
            "note", "Review uses resilient wrapper; integrate Ollama for deep review"
        )

        return review_result

    def list_projects(self, limit: int = 10) -> dict[str, Any]:
        """List ChatDev projects.

        Args:
            limit: Max projects to return

        Returns:
            List of projects
        """
        workspace = self.config.workspace_path

        if not workspace.exists():
            return {"success": True, "projects": []}

        projects = []
        for project_dir in sorted(workspace.iterdir(), reverse=True):
            if project_dir.is_dir() and not project_dir.name.startswith("."):
                projects.append(
                    {
                        "name": project_dir.name,
                        "path": str(project_dir),
                        "modified": project_dir.stat().st_mtime,
                    }
                )

                if len(projects) >= limit:
                    break

        return {"success": True, "projects": projects, "total": len(projects)}

    async def _run_chatdev_generate(
        self,
        task: str,
        model: str = DEFAULT_MODEL_NAME,
        name: str | None = None,
        degraded: bool = False,
    ) -> dict[str, Any]:
        """Internal helper to run ChatDev generation command.

        Args:
            task: Task description
            model: Model to use
            name: Optional project name
            degraded: If True, indicates degraded-mode call
        """
        # Generate project name if not provided
        if not name:
            import time

            name = (
                f"nusyq_mcp_{int(time.time())}"
                if not degraded
                else f"nusyq_mcp_deg_{int(time.time())}"
            )

        cmd = self.config.get_run_command(task, model)

        # Override name for reproducibility
        if "--name" in cmd:
            # Replace following element after --name
            try:
                idx = cmd.index("--name")
                if idx + 1 < len(cmd):
                    cmd[idx + 1] = name
            except ValueError:
                logger.debug("Suppressed ValueError", exc_info=True)
        else:
            cmd.extend(["--name", name])

        logger.info(
            f"📝 Running ChatDev ({'degraded' if degraded else 'primary'}): {' '.join(cmd)}"
        )

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            project_path = self.config.workspace_path / name
            return {
                "project_name": name,
                "project_path": str(project_path),
                "model_used": model,
                "output": stdout.decode("utf-8", errors="ignore"),
            }

        raise RuntimeError(
            f"ChatDev run failed (code {process.returncode}): {stderr.decode('utf-8', errors='ignore')}"
        )

    def get_tool_manifest(self) -> list[dict[str, Any]]:
        """Get MCP tool manifest for registration.

        Returns:
            List of tool definitions for MCP server
        """
        return [
            {"name": tool.name, "description": tool.description, "inputSchema": tool.input_schema}
            for tool in self.mcp_tools
        ]

    async def handle_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Handle MCP tool call.

        Args:
            tool_name: Name of tool to invoke
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        # Find tool definition
        tool = next((t for t in self.mcp_tools if t.name == tool_name), None)

        if not tool:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        # Get handler method
        handler = getattr(self, tool.handler, None)

        if not handler:
            return {"success": False, "error": f"Handler not found: {tool.handler}"}

        # Execute handler
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)

            return result
        except Exception as e:
            logger.error(f"❌ Tool execution error: {e}")
            return {"success": False, "error": str(e)}


# Global instance
_mcp_server: ChatDevMCPServer | None = None


def get_chatdev_mcp_server() -> ChatDevMCPServer:
    """Get global ChatDev MCP server instance.

    Returns:
        ChatDevMCPServer instance
    """
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = ChatDevMCPServer()
    return _mcp_server


# CLI for testing
async def main() -> None:
    """Test ChatDev MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="ChatDev MCP Server")
    parser.add_argument("--tool", help="Tool to test")
    parser.add_argument("--task", help="Task description")
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME, help="Ollama model")

    args = parser.parse_args()

    server = get_chatdev_mcp_server()

    if args.tool == "generate":
        if not args.task:
            logger.error("Error: --task required for generate")
            return

        result = await server.generate_project(args.task, args.model)
        logger.info(json.dumps(result, indent=2))

    elif args.tool == "list":
        result = server.list_projects()
        logger.info(json.dumps(result, indent=2))

    else:
        # Show manifest
        manifest = server.get_tool_manifest()
        logger.info("ChatDev MCP Tool Manifest:")
        logger.info(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
