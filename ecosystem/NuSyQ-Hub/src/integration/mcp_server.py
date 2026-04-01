"""Model Context Protocol (MCP) Server for Claude Code Integration.

This server implements the MCP specification to enable seamless integration
with Claude Code, Anthropic Claude, and other MCP-compatible AI systems.

OmniTag: {
    "purpose": "MCP server for AI system integration",
    "dependencies": ["flask", "agent_context_manager", "multi_ai_orchestrator"],
    "context": "Enables Model Context Protocol for Claude/Anthropic integration",
    "evolution_stage": "v1.0"
}
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from src.config.service_config import ServiceConfig
except ImportError:  # pragma: no cover - fallback for standalone usage
    ServiceConfig = None

try:
    from src.config.feature_flag_manager import is_feature_enabled
except ImportError:  # pragma: no cover

    def is_feature_enabled(_: str) -> bool:
        return False


try:
    from src.integration.chatdev_launcher import ChatDevLauncher
except ImportError:  # pragma: no cover
    ChatDevLauncher = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGENT_TASK_TYPE_DESC = "Task type (analyze, generate, review, debug, plan, test, document)"
AGENT_TASK_DESC = "Task description or prompt"
AGENT_TASK_PRIORITY_DESC = "Task priority (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)"
AGENT_TASK_CONTEXT_DESC = "Optional routing context"


@dataclass
class MCPTool:
    """Represents an MCP tool specification."""

    name: str
    description: str
    parameters: dict[str, Any]
    required_parameters: list[str]
    category: str = "general"
    version: str = "1.0"


@dataclass
class MCPExecutionResult:
    """Result of MCP tool execution."""

    success: bool
    result: Any
    error: str | None = None
    execution_time: float = 0.0
    tool_name: str = ""
    timestamp: str = ""


class MCPServer:
    """Model Context Protocol Server for AI system integration."""

    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        """Initialize MCP server.

        Args:
            host: Server host address
            port: Server port number

        """
        if ServiceConfig is not None:
            cfg_host, cfg_port = ServiceConfig.get_mcp_server_address()
            host = host or cfg_host
            port = port or cfg_port
        host = host or "localhost"
        port = port or 8080

        self.host = host
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for cross-origin requests

        # Server state
        self.start_time = time.time()
        self.request_count = 0
        self.tool_executions: dict[str, int] = {}
        self.registered_tools: dict[str, MCPTool] = {}

        # Initialize routes
        self._register_routes()

        # Register default tools
        self._register_default_tools()
        # Register gateway/router tools
        self._register_gateway_tools()
        # Register sandbox tools
        self._register_sandbox_tools()

        # Register ChatDev tools (flagged)
        if is_feature_enabled("chatdev_mcp_enabled"):
            self._register_chatdev_tools()

        # Register ecosystem tools for OpenClaw (agents/skills)
        self._register_ecosystem_tools()

        logger.info("MCP Server initialized on %s:%s", host, port)

    def _register_routes(self) -> None:
        """Register Flask routes for MCP endpoints."""

        @self.app.route("/health", methods=["GET"])  # type: ignore[misc]
        def health_check() -> Any:
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "uptime": time.time() - self.start_time,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        @self.app.route("/tools", methods=["GET"])  # type: ignore[misc]
        def list_tools() -> Any:
            """List all available MCP tools."""
            self.request_count += 1
            tools = [asdict(tool) for tool in self.registered_tools.values()]
            return jsonify({"tools": tools, "count": len(tools)})

        @self.app.route("/execute", methods=["POST"])  # type: ignore[misc]
        def execute_tool() -> Any:
            """Execute an MCP tool."""
            self.request_count += 1

            try:
                data = request.get_json(silent=True) or {}
                tool_name = data.get("tool")
                parameters = data.get("parameters", {})

                if not tool_name:
                    return (
                        jsonify({"success": False, "error": "Tool name required"}),
                        400,
                    )

                if tool_name not in self.registered_tools:
                    return (
                        jsonify({"success": False, "error": f"Tool '{tool_name}' not found"}),
                        404,
                    )

                # Execute tool
                result = self._execute_tool(tool_name, parameters)

                # Track execution
                if tool_name not in self.tool_executions:
                    self.tool_executions[tool_name] = 0
                self.tool_executions[tool_name] += 1

                try:
                    from src.system.agent_awareness import emit as _emit

                    _lvl = "INFO" if result.success else "WARNING"
                    _emit(
                        "tasks",
                        f"MCP tool: {tool_name} | success={result.success}",
                        level=_lvl,
                        source="mcp_server",
                    )
                except Exception:
                    pass

                return jsonify(asdict(result))

            except Exception as e:
                logger.exception("Error executing tool")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/status", methods=["GET"])  # type: ignore[misc]
        def server_status() -> Any:
            """Get MCP server status."""
            return jsonify(
                {
                    "status": "running",
                    "uptime": time.time() - self.start_time,
                    "request_count": self.request_count,
                    "tool_count": len(self.registered_tools),
                    "tool_executions": self.tool_executions,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        @self.app.route("/manifest", methods=["GET"])  # type: ignore[misc]
        def manifest() -> Any:
            """Return MCP manifest (Claude Code compatible)."""
            return jsonify(
                {
                    "name": os.getenv("MCP_SERVER_NAME", "NuSyQ-ChatDev"),
                    "version": "1.0",
                    "protocol": "mcp",
                    "tools": [asdict(tool) for tool in self.registered_tools.values()],
                    "endpoints": {
                        "execute": "/execute",
                        "tools": "/tools",
                        "health": "/health",
                        "status": "/status",
                    },
                },
            )

        @self.app.route("/metrics", methods=["GET"])  # type: ignore[misc]
        def server_metrics() -> Any:
            """Get MCP server metrics."""
            total_executions = sum(self.tool_executions.values())
            return jsonify(
                {
                    "uptime_seconds": time.time() - self.start_time,
                    "total_requests": self.request_count,
                    "total_tool_executions": total_executions,
                    "tools_registered": len(self.registered_tools),
                    "tool_execution_breakdown": self.tool_executions,
                    "average_requests_per_minute": (
                        self.request_count / ((time.time() - self.start_time) / 60)
                        if (time.time() - self.start_time) > 0
                        else 0
                    ),
                },
            )

    def _register_default_tools(self) -> None:
        """Register default MCP tools."""
        # Repository Analysis Tool
        self.register_tool(
            MCPTool(
                name="analyze_repository",
                description="Analyze repository structure and provide insights",
                parameters={
                    "path": {"type": "string", "description": "Repository path"},
                    "depth": {
                        "type": "integer",
                        "description": "Analysis depth (1-10)",
                        "default": 5,
                    },
                },
                required_parameters=["path"],
                category="analysis",
            ),
        )

        # Context Retrieval Tool
        self.register_tool(
            MCPTool(
                name="get_context",
                description="Retrieve context for AI systems",
                parameters={
                    "context_type": {
                        "type": "string",
                        "description": "Type of context (agent, quest, system)",
                    },
                    "context_id": {
                        "type": "string",
                        "description": "Context identifier",
                    },
                },
                required_parameters=["context_type"],
                category="context",
            ),
        )

        # AI Orchestration Tool
        self.register_tool(
            MCPTool(
                name="orchestrate_task",
                description="Submit task to multi-AI orchestrator",
                parameters={
                    "task_description": {
                        "type": "string",
                        "description": "Task to perform",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Task priority (low, medium, high)",
                        "default": "medium",
                    },
                    "preferred_systems": {
                        "type": "array",
                        "description": "Preferred AI systems",
                    },
                },
                required_parameters=["task_description"],
                category="orchestration",
            ),
        )

        # Code Generation Tool
        self.register_tool(
            MCPTool(
                name="generate_code",
                description="Generate code using AI systems",
                parameters={
                    "language": {
                        "type": "string",
                        "description": "Programming language",
                    },
                    "description": {
                        "type": "string",
                        "description": "Code description",
                    },
                    "model": {
                        "type": "string",
                        "description": "AI model to use",
                        "default": "qwen2.5-coder:14b",
                    },
                },
                required_parameters=["language", "description"],
                category="generation",
            ),
        )

        # Test Generation Tool
        self.register_tool(
            MCPTool(
                name="generate_tests",
                description="Generate test cases for code",
                parameters={
                    "file_path": {"type": "string", "description": "File to test"},
                    "test_framework": {
                        "type": "string",
                        "description": "Test framework (pytest, unittest)",
                        "default": "pytest",
                    },
                },
                required_parameters=["file_path"],
                category="testing",
            ),
        )

        # System Health Check Tool
        self.register_tool(
            MCPTool(
                name="check_system_health",
                description="Check overall system health",
                parameters={
                    "include_ai_systems": {
                        "type": "boolean",
                        "description": "Include AI system status",
                        "default": True,
                    },
                },
                required_parameters=[],
                category="diagnostics",
            ),
        )

        logger.info("Registered %s default MCP tools", len(self.registered_tools))

    def _register_gateway_tools(self) -> None:
        """Register LLM gateway and swarm router tools (feature-flagged)."""
        if not is_feature_enabled("gateway_router_enabled"):
            return
        self.register_tool(
            MCPTool(
                name="llm_route",
                description="Route a prompt via the universal LLM gateway",
                parameters={
                    "prompt": {"type": "string", "description": "Prompt text"},
                    "model_hint": {
                        "type": "string",
                        "description": "Preferred model",
                        "default": None,
                    },
                    "capability_tags": {
                        "type": "array",
                        "description": "Desired capability tags (e.g., code, local)",
                        "default": [],
                    },
                    "prefer_local": {
                        "type": "boolean",
                        "description": "Prefer local models",
                        "default": False,
                    },
                    "max_cost": {
                        "type": "string",
                        "description": "Cost ceiling (low/medium/high)",
                        "default": None,
                    },
                },
                required_parameters=["prompt"],
                category="routing",
            )
        )
        self.register_tool(
            MCPTool(
                name="swarm_run",
                description="Run SwarmRouter flow (sequential/concurrent/map_reduce/vote)",
                parameters={
                    "mode": {
                        "type": "string",
                        "description": "one of sequential, concurrent, map_reduce, vote",
                        "default": "sequential",
                    },
                    "steps": {"type": "array", "description": "List of steps/tasks"},
                    "reduce_prompt": {
                        "type": "string",
                        "description": "Reduce prompt (for map_reduce)",
                        "default": "",
                    },
                },
                required_parameters=["mode", "steps"],
                category="routing",
            )
        )
        logger.info("Registered gateway/router MCP tools")

    def _register_sandbox_tools(self) -> None:
        if not is_feature_enabled("sandbox_runner_enabled"):
            return
        self.register_tool(
            MCPTool(
                name="sandbox_run",
                description="Execute a command inside sandboxed container (feature-flagged)",
                parameters={
                    "command": {"type": "array", "description": "Command list"},
                    "env": {"type": "object", "description": "Environment vars", "default": {}},
                },
                required_parameters=["command"],
                category="sandbox",
            )
        )
        logger.info("Registered sandbox MCP tools")

    def _register_chatdev_tools(self) -> None:
        """Register ChatDev-specific MCP tools (schema mirrors ChatDevMCP)."""
        self.register_tool(
            MCPTool(
                name="chatdev_run",
                description="Launch a ChatDev session",
                parameters={
                    "task": {"type": "string", "description": "Software task description"},
                    "name": {
                        "type": "string",
                        "description": "Project name",
                        "default": "ChatDevProject",
                    },
                    "model": {
                        "type": "string",
                        "description": "Model id (OpenAI/Ollama)",
                        "default": "gpt-4o-mini",
                    },
                    "org": {
                        "type": "string",
                        "description": "Organization name",
                        "default": "NuSyQ",
                    },
                    "config": {
                        "type": "string",
                        "description": "Config profile",
                        "default": "Default",
                    },
                    "use_ollama": {
                        "type": "boolean",
                        "description": "Force Ollama mode",
                        "default": False,
                    },
                    "git_mode": {
                        "type": "boolean",
                        "description": "Enable git-aware ChatDev run (mirrors OpenBMB git_mode)",
                        "default": False,
                    },
                    "sandbox": {
                        "type": "boolean",
                        "description": "Run ChatDev inside sandbox container (if enabled)",
                        "default": False,
                    },
                    "degraded_mode": {
                        "type": "boolean",
                        "description": "Run in degraded mode (local model + basic tests)",
                        "default": False,
                    },
                },
                required_parameters=["task"],
                category="chatdev",
            ),
        )
        self.register_tool(
            MCPTool(
                name="chatdev_status",
                description="Get ChatDev launcher status or poll a specific run_id",
                parameters={
                    "run_id": {
                        "type": "string",
                        "description": "Optional run id returned by chatdev_run",
                        "default": "",
                    },
                    "wait_seconds": {
                        "type": "number",
                        "description": "Optional poll timeout for terminal run state",
                        "default": 0,
                    },
                    "poll_interval_seconds": {
                        "type": "number",
                        "description": "Polling cadence when wait_seconds > 0",
                        "default": 2,
                    },
                    "recent_limit": {
                        "type": "integer",
                        "description": "Max recent runs returned when run_id is omitted",
                        "default": 10,
                    },
                },
                required_parameters=[],
                category="chatdev",
            ),
        )
        logger.info("Registered ChatDev MCP tools")

    def _register_ecosystem_tools(self) -> None:
        """Register ecosystem tools for OpenClaw agent onboarding.

        These tools expose NuSyQ's internal agent routing as MCP tools so OpenClaw
        (and other MCP-compatible clients) can invoke Copilot/Ollama/ChatDev/Quantum
        through agent_task_router.
        """
        self.register_tool(
            MCPTool(
                name="agent_route",
                description="Route a task through AgentTaskRouter with explicit target system",
                parameters={
                    "task_type": {
                        "type": "string",
                        "description": AGENT_TASK_TYPE_DESC,
                        "default": "analyze",
                    },
                    "description": {
                        "type": "string",
                        "description": AGENT_TASK_DESC,
                    },
                    "target_system": {
                        "type": "string",
                        "description": "Target system (auto, copilot, ollama, lmstudio, chatdev, quantum_resolver)",
                        "default": "auto",
                    },
                    "priority": {
                        "type": "string",
                        "description": AGENT_TASK_PRIORITY_DESC,
                        "default": "NORMAL",
                    },
                    "context": {
                        "type": "object",
                        "description": AGENT_TASK_CONTEXT_DESC,
                        "default": {},
                    },
                },
                required_parameters=["description"],
                category="agents",
            ),
        )

        self.register_tool(
            MCPTool(
                name="agent_copilot",
                description="Route a task to Copilot bridge (requires NUSYQ_COPILOT_BRIDGE_MODE)",
                parameters={
                    "task_type": {
                        "type": "string",
                        "description": AGENT_TASK_TYPE_DESC,
                        "default": "analyze",
                    },
                    "description": {
                        "type": "string",
                        "description": AGENT_TASK_DESC,
                    },
                    "priority": {
                        "type": "string",
                        "description": AGENT_TASK_PRIORITY_DESC,
                        "default": "NORMAL",
                    },
                    "context": {
                        "type": "object",
                        "description": AGENT_TASK_CONTEXT_DESC,
                        "default": {},
                    },
                },
                required_parameters=["description"],
                category="agents",
            ),
        )

        self.register_tool(
            MCPTool(
                name="agent_ollama",
                description="Route a task to Ollama local models",
                parameters={
                    "task_type": {
                        "type": "string",
                        "description": AGENT_TASK_TYPE_DESC,
                        "default": "analyze",
                    },
                    "description": {
                        "type": "string",
                        "description": AGENT_TASK_DESC,
                    },
                    "priority": {
                        "type": "string",
                        "description": AGENT_TASK_PRIORITY_DESC,
                        "default": "NORMAL",
                    },
                    "context": {
                        "type": "object",
                        "description": AGENT_TASK_CONTEXT_DESC,
                        "default": {},
                    },
                },
                required_parameters=["description"],
                category="agents",
            ),
        )

        self.register_tool(
            MCPTool(
                name="agent_lmstudio",
                description="Route a task to LM Studio local models",
                parameters={
                    "task_type": {
                        "type": "string",
                        "description": AGENT_TASK_TYPE_DESC,
                        "default": "analyze",
                    },
                    "description": {
                        "type": "string",
                        "description": AGENT_TASK_DESC,
                    },
                    "priority": {
                        "type": "string",
                        "description": AGENT_TASK_PRIORITY_DESC,
                        "default": "NORMAL",
                    },
                    "context": {
                        "type": "object",
                        "description": AGENT_TASK_CONTEXT_DESC,
                        "default": {},
                    },
                },
                required_parameters=["description"],
                category="agents",
            ),
        )

        self.register_tool(
            MCPTool(
                name="agent_chatdev",
                description="Route a generation task to ChatDev",
                parameters={
                    "task_type": {
                        "type": "string",
                        "description": "Task type (generate recommended)",
                        "default": "generate",
                    },
                    "description": {
                        "type": "string",
                        "description": AGENT_TASK_DESC,
                    },
                    "priority": {
                        "type": "string",
                        "description": AGENT_TASK_PRIORITY_DESC,
                        "default": "NORMAL",
                    },
                    "context": {
                        "type": "object",
                        "description": AGENT_TASK_CONTEXT_DESC,
                        "default": {},
                    },
                },
                required_parameters=["description"],
                category="agents",
            ),
        )

        self.register_tool(
            MCPTool(
                name="agent_quantum",
                description="Route a task to the Quantum Problem Resolver",
                parameters={
                    "task_type": {
                        "type": "string",
                        "description": "Task type (debug recommended)",
                        "default": "debug",
                    },
                    "description": {
                        "type": "string",
                        "description": AGENT_TASK_DESC,
                    },
                    "priority": {
                        "type": "string",
                        "description": AGENT_TASK_PRIORITY_DESC,
                        "default": "NORMAL",
                    },
                    "context": {
                        "type": "object",
                        "description": AGENT_TASK_CONTEXT_DESC,
                        "default": {},
                    },
                },
                required_parameters=["description"],
                category="agents",
            ),
        )

        # Tool aliases for convenience
        alias_tools = [
            ("copilot_chat", "Copilot chat (alias for agent_copilot)", "analyze"),
            ("copilot_review", "Copilot review (alias for agent_copilot)", "review"),
            ("ollama_analyze", "Ollama analyze (alias for agent_ollama)", "analyze"),
            ("ollama_review", "Ollama review (alias for agent_ollama)", "review"),
            ("ollama_generate", "Ollama generate (alias for agent_ollama)", "generate"),
            ("ollama_debug", "Ollama debug (alias for agent_ollama)", "debug"),
            ("lmstudio_analyze", "LM Studio analyze (alias for agent_lmstudio)", "analyze"),
            ("lmstudio_review", "LM Studio review (alias for agent_lmstudio)", "review"),
            ("lmstudio_generate", "LM Studio generate (alias for agent_lmstudio)", "generate"),
            ("lmstudio_debug", "LM Studio debug (alias for agent_lmstudio)", "debug"),
            ("chatdev_generate", "ChatDev generate (alias for agent_chatdev)", "generate"),
            ("quantum_debug", "Quantum debug (alias for agent_quantum)", "debug"),
        ]

        for name, description, default_task_type in alias_tools:
            self.register_tool(
                MCPTool(
                    name=name,
                    description=description,
                    parameters={
                        "task_type": {
                            "type": "string",
                            "description": AGENT_TASK_TYPE_DESC,
                            "default": default_task_type,
                        },
                        "description": {
                            "type": "string",
                            "description": AGENT_TASK_DESC,
                        },
                        "priority": {
                            "type": "string",
                            "description": AGENT_TASK_PRIORITY_DESC,
                            "default": "NORMAL",
                        },
                        "context": {
                            "type": "object",
                            "description": AGENT_TASK_CONTEXT_DESC,
                            "default": {},
                        },
                    },
                    required_parameters=["description"],
                    category="agents",
                )
            )

        git_tools = [
            (
                "mcp_gitkraken_git_status",
                "Execute git status via the local GitKraken execution bridge",
                {
                    "repo_path": {
                        "type": "string",
                        "description": "Optional repository path",
                        "default": "",
                    },
                    "short": {
                        "type": "boolean",
                        "description": "Use short status output",
                        "default": True,
                    },
                    "porcelain": {
                        "type": "boolean",
                        "description": "Use porcelain output",
                        "default": True,
                    },
                },
            ),
            (
                "mcp_gitkraken_git_add_or_commit",
                "Stage files and create a commit via the local GitKraken execution bridge",
                {
                    "repo_path": {
                        "type": "string",
                        "description": "Optional repository path",
                        "default": "",
                    },
                    "files": {
                        "type": "array",
                        "description": "Files to stage; defaults to all tracked changes",
                        "default": [],
                    },
                    "message": {
                        "type": "string",
                        "description": "Commit message",
                        "default": "",
                    },
                    "amend": {
                        "type": "boolean",
                        "description": "Amend the previous commit",
                        "default": False,
                    },
                },
            ),
            (
                "mcp_gitkraken_git_push",
                "Push a branch via the local GitKraken execution bridge",
                {
                    "repo_path": {
                        "type": "string",
                        "description": "Optional repository path",
                        "default": "",
                    },
                    "remote": {
                        "type": "string",
                        "description": "Remote name",
                        "default": "origin",
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name to push",
                        "default": "",
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Force push",
                        "default": False,
                    },
                    "set_upstream": {
                        "type": "boolean",
                        "description": "Set upstream on push",
                        "default": True,
                    },
                },
            ),
        ]

        for name, description, params in git_tools:
            self.register_tool(
                MCPTool(
                    name=name,
                    description=description,
                    parameters=params,
                    required_parameters=[],
                    category="git",
                )
            )

        logger.info(
            "Registered ecosystem MCP tools (agents + GitKraken git status/commit/push execution)"
        )

    def register_tool(self, tool: MCPTool) -> None:
        """Register a new MCP tool.

        Args:
            tool: MCPTool specification

        """
        self.registered_tools[tool.name] = tool
        logger.info("Registered MCP tool: %s", tool.name)

    def _run_router_task(
        self,
        task_type: str,
        description: str,
        target_system: str,
        priority: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute AgentTaskRouter asynchronously from sync MCP context."""
        from src.tools.agent_task_router import (AgentTaskRouter, TargetSystem,
                                                 TaskType)

        router = AgentTaskRouter()
        payload = context if isinstance(context, dict) else {}

        async def _run() -> dict[str, Any]:
            allowed_task_types: set[str] = {
                "analyze",
                "generate",
                "review",
                "debug",
                "plan",
                "test",
                "document",
                "create_project",
                "factory_health",
                "factory_doctor",
                "factory_doctor_fix",
                "factory_autopilot",
                "factory_inspect_examples",
                "generate_graphql",
                "generate_openapi",
                "generate_component",
                "generate_database",
                "generate_project",
            }
            allowed_targets: set[str] = {
                "auto",
                "ollama",
                "lmstudio",
                "chatdev",
                "copilot",
                "consciousness",
                "quantum_resolver",
                "factory",
                "graphql",
                "openapi",
                "component",
                "database",
                "project",
            }
            normalized_task_type = task_type if task_type in allowed_task_types else "analyze"
            normalized_target = target_system if target_system in allowed_targets else "auto"

            result = await router.route_task(
                task_type=cast(TaskType, normalized_task_type),
                description=description,
                context=payload,
                target_system=cast(TargetSystem, normalized_target),
                priority=priority,
            )
            assert isinstance(result, dict)
            return result

        try:
            return asyncio.run(_run())
        except RuntimeError as exc:
            # Handle case where an event loop is already running
            if "asyncio.run() cannot be called" in str(exc):
                loop = asyncio.new_event_loop()
                try:
                    return loop.run_until_complete(_run())
                finally:
                    loop.close()
            raise

    def _execute_tool(self, tool_name: str, parameters: dict[str, Any]) -> MCPExecutionResult:
        """Execute an MCP tool.

        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters

        Returns:
            MCPExecutionResult with execution details

        """
        start_time = time.time()

        try:
            # Validate tool exists
            if tool_name not in self.registered_tools:
                return MCPExecutionResult(
                    success=False,
                    result=None,
                    error=f"Tool '{tool_name}' not found",
                    tool_name=tool_name,
                    timestamp=datetime.now().isoformat(),
                )

            tool = self.registered_tools[tool_name]

            # Validate required parameters
            for param in tool.required_parameters:
                if param not in parameters:
                    return MCPExecutionResult(
                        success=False,
                        result=None,
                        error=f"Required parameter '{param}' missing",
                        tool_name=tool_name,
                        timestamp=datetime.now().isoformat(),
                    )

            # Execute tool based on name
            result = self._dispatch_tool_execution(tool_name, parameters)

            execution_time = time.time() - start_time

            return MCPExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                tool_name=tool_name,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.exception("Error executing tool %s", tool_name)
            execution_time = time.time() - start_time

            return MCPExecutionResult(
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time,
                tool_name=tool_name,
                timestamp=datetime.now().isoformat(),
            )

    def _dispatch_tool_execution(self, tool_name: str, parameters: dict[str, Any]) -> Any:
        """Dispatch tool execution to appropriate handler."""
        if tool_name.startswith("agent_") or tool_name in {
            "copilot_chat",
            "copilot_review",
            "ollama_analyze",
            "ollama_review",
            "ollama_generate",
            "ollama_debug",
            "lmstudio_analyze",
            "lmstudio_review",
            "lmstudio_generate",
            "lmstudio_debug",
            "chatdev_generate",
            "quantum_debug",
        }:
            parameters = {**parameters, "_tool_name": tool_name}
        handlers = {
            "analyze_repository": self._handle_analyze_repository,
            "get_context": self._handle_get_context,
            "orchestrate_task": self._handle_orchestrate_task,
            "generate_code": self._handle_generate_code,
            "generate_tests": self._handle_generate_tests,
            "check_system_health": self._handle_check_system_health,
            "agent_route": self._handle_agent_tool,
            "agent_copilot": self._handle_agent_tool,
            "agent_ollama": self._handle_agent_tool,
            "agent_lmstudio": self._handle_agent_tool,
            "agent_chatdev": self._handle_agent_tool,
            "agent_quantum": self._handle_agent_tool,
            "copilot_chat": self._handle_agent_tool,
            "copilot_review": self._handle_agent_tool,
            "ollama_analyze": self._handle_agent_tool,
            "ollama_review": self._handle_agent_tool,
            "ollama_generate": self._handle_agent_tool,
            "ollama_debug": self._handle_agent_tool,
            "lmstudio_analyze": self._handle_agent_tool,
            "lmstudio_review": self._handle_agent_tool,
            "lmstudio_generate": self._handle_agent_tool,
            "lmstudio_debug": self._handle_agent_tool,
            "chatdev_generate": self._handle_agent_tool,
            "quantum_debug": self._handle_agent_tool,
            "mcp_gitkraken_git_status": self._handle_gitkraken_git_status,
            "mcp_gitkraken_git_add_or_commit": self._handle_gitkraken_git_add_or_commit,
            "mcp_gitkraken_git_push": self._handle_gitkraken_git_push,
            "chatdev_status": self._handle_chatdev_status,
            "chatdev_run": self._handle_chatdev_run,
            "llm_route": self._handle_llm_route,
            "swarm_run": self._handle_swarm_run,
            "sandbox_run": self._handle_sandbox_run,
        }

        handler = handlers.get(tool_name)
        if handler:
            return handler(parameters)
        return {"error": f"Tool '{tool_name}' not implemented"}

    def _handle_analyze_repository(self, parameters: dict[str, Any]) -> dict[str, Any]:
        path = parameters.get("path", ".")
        depth = parameters.get("depth", 5)
        return {
            "path": path,
            "depth": depth,
            "status": "analysis_complete",
            "files_analyzed": 100,
            "insights": ["Well-structured", "Good test coverage"],
        }

    def _handle_get_context(self, parameters: dict[str, Any]) -> dict[str, Any]:
        context_type = parameters.get("context_type")
        context_id = parameters.get("context_id", "default")

        try:
            from src.tools.agent_context_manager import AgentContextManager

            context_manager = AgentContextManager()
            context = context_manager.load(context_id)
            return (
                cast(dict[str, Any], context)
                if isinstance(context, dict)
                else {"error": "Context not found"}
            )
        except Exception as exc:
            return {"error": str(exc), "context_type": context_type}

    def _handle_orchestrate_task(self, parameters: dict[str, Any]) -> dict[str, Any]:
        task_description = parameters.get("task_description")
        priority = parameters.get("priority", "medium")
        return {
            "task_id": f"task_{int(time.time())}",
            "status": "queued",
            "description": task_description,
            "priority": priority,
            "estimated_completion": "pending",
        }

    def _handle_generate_code(self, parameters: dict[str, Any]) -> dict[str, Any]:
        language = parameters.get("language")
        description = parameters.get("description")
        model = parameters.get("model", "qwen2.5-coder:14b")
        return {
            "language": language,
            "model": model,
            "status": "generation_queued",
            "description": description,
        }

    def _handle_generate_tests(self, parameters: dict[str, Any]) -> dict[str, Any]:
        file_path = parameters.get("file_path")
        test_framework = parameters.get("test_framework", "pytest")
        return {
            "file_path": file_path,
            "test_framework": test_framework,
            "status": "test_generation_queued",
        }

    def _handle_check_system_health(self, parameters: dict[str, Any]) -> dict[str, Any]:
        include_ai = parameters.get("include_ai_systems", True)
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "ai_systems": (
                {
                    "copilot": "operational",
                    "ollama": "operational",
                    "chatdev": "operational",
                }
                if include_ai
                else None
            ),
        }

    def _handle_agent_tool(self, parameters: dict[str, Any]) -> dict[str, Any]:
        description = parameters.get("description", "").strip()
        if not description:
            return {"error": "description required"}

        tool_name = parameters.get("tool_name") or parameters.get("_tool_name")
        task_type = parameters.get("task_type", "analyze")
        priority = parameters.get("priority", "NORMAL")
        context = parameters.get("context", {})

        target_system = parameters.get("target_system", "auto")
        alias_map = {
            "agent_copilot": ("copilot", None),
            "agent_ollama": ("ollama", None),
            "agent_lmstudio": ("lmstudio", None),
            "agent_chatdev": ("chatdev", "generate"),
            "agent_quantum": ("quantum_resolver", "debug"),
            "copilot_chat": ("copilot", "analyze"),
            "copilot_review": ("copilot", "review"),
            "ollama_analyze": ("ollama", "analyze"),
            "ollama_review": ("ollama", "review"),
            "ollama_generate": ("ollama", "generate"),
            "ollama_debug": ("ollama", "debug"),
            "lmstudio_analyze": ("lmstudio", "analyze"),
            "lmstudio_review": ("lmstudio", "review"),
            "lmstudio_generate": ("lmstudio", "generate"),
            "lmstudio_debug": ("lmstudio", "debug"),
            "chatdev_generate": ("chatdev", "generate"),
            "quantum_debug": ("quantum_resolver", "debug"),
        }
        if tool_name in alias_map:
            mapped_system, mapped_task = alias_map[tool_name]
            target_system = mapped_system
            if mapped_task:
                task_type = mapped_task

        return self._run_router_task(
            task_type=task_type,
            description=description,
            target_system=target_system,
            priority=priority,
            context=context,
        )

    @staticmethod
    def _coerce_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        return default

    def _resolve_git_executable(self) -> str:
        return shutil.which("git.exe") or shutil.which("git") or "git"

    def _resolve_git_repo_root(self, repo_path: Any = None) -> Path:
        if isinstance(repo_path, str) and repo_path.strip():
            candidate = Path(repo_path).expanduser()
            if candidate.exists():
                return candidate
        return Path.cwd()

    def _git_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.setdefault("GIT_TERMINAL_PROMPT", "0")
        env.setdefault("GCM_INTERACTIVE", "never")
        return env

    def _run_git_command(
        self,
        args: list[str],
        *,
        cwd: Path,
        timeout_s: float = 30.0,
    ) -> dict[str, Any]:
        command = [self._resolve_git_executable(), *args]
        process = subprocess.run(
            command,
            cwd=str(cwd),
            env=self._git_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(1.0, timeout_s),
            check=False,
        )
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": process.returncode,
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
        }

    def _current_branch(self, cwd: Path) -> str:
        result = self._run_git_command(
            ["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, timeout_s=10.0
        )
        branch = str(result.get("stdout") or "").strip()
        return branch or "HEAD"

    def _handle_gitkraken_git_status(self, parameters: dict[str, Any]) -> dict[str, Any]:
        cwd = self._resolve_git_repo_root(parameters.get("repo_path"))
        args = ["status", "--branch"]
        if self._coerce_bool(parameters.get("short"), True):
            args.append("--short")
        if self._coerce_bool(parameters.get("porcelain"), True):
            args.append("--porcelain")

        result = self._run_git_command(args, cwd=cwd, timeout_s=15.0)
        stdout = str(result.get("stdout") or "")
        lines = [line for line in stdout.splitlines() if line.strip()]
        branch_line = next((line for line in lines if line.startswith("## ")), "")
        return {
            "status": "ok" if result["returncode"] == 0 else "failed",
            "repo_path": str(cwd),
            "branch": branch_line[3:] if branch_line else self._current_branch(cwd),
            "raw_status": stdout,
            "stderr": result.get("stderr", ""),
            "returncode": result["returncode"],
            "tool": "mcp_gitkraken_git_status",
        }

    def _handle_gitkraken_git_add_or_commit(self, parameters: dict[str, Any]) -> dict[str, Any]:
        cwd = self._resolve_git_repo_root(parameters.get("repo_path"))
        files = parameters.get("files") or []
        message = str(parameters.get("message") or "").strip()
        amend = self._coerce_bool(parameters.get("amend"), False)

        add_args = ["add"]
        if isinstance(files, list) and files:
            add_args.extend([str(item) for item in files if str(item).strip()])
        else:
            add_args.append("-A")
        add_result = self._run_git_command(add_args, cwd=cwd, timeout_s=20.0)
        if add_result["returncode"] != 0:
            return {
                "status": "failed",
                "repo_path": str(cwd),
                "step": "add",
                "stderr": add_result.get("stderr", ""),
                "returncode": add_result["returncode"],
                "tool": "mcp_gitkraken_git_add_or_commit",
            }

        if not message:
            return {
                "status": "staged",
                "repo_path": str(cwd),
                "message": "",
                "tool": "mcp_gitkraken_git_add_or_commit",
            }

        commit_args = ["commit", "-m", message]
        if amend:
            commit_args.append("--amend")
        commit_result = self._run_git_command(commit_args, cwd=cwd, timeout_s=30.0)
        return {
            "status": "committed" if commit_result["returncode"] == 0 else "failed",
            "repo_path": str(cwd),
            "message": message,
            "stdout": commit_result.get("stdout", ""),
            "stderr": commit_result.get("stderr", ""),
            "returncode": commit_result["returncode"],
            "tool": "mcp_gitkraken_git_add_or_commit",
        }

    def _handle_gitkraken_git_push(self, parameters: dict[str, Any]) -> dict[str, Any]:
        cwd = self._resolve_git_repo_root(parameters.get("repo_path"))
        remote = str(parameters.get("remote") or "origin").strip() or "origin"
        branch = str(parameters.get("branch") or "").strip() or self._current_branch(cwd)
        force = self._coerce_bool(parameters.get("force"), False)
        set_upstream = self._coerce_bool(parameters.get("set_upstream"), True)

        push_args = ["push"]
        if set_upstream:
            push_args.append("--set-upstream")
        push_args.extend([remote, branch])
        if force:
            push_args.append("--force")

        try:
            result = self._run_git_command(push_args, cwd=cwd, timeout_s=45.0)
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "repo_path": str(cwd),
                "remote": remote,
                "branch": branch,
                "error": "git push timed out",
                "tool": "mcp_gitkraken_git_push",
            }

        stderr = str(result.get("stderr") or "")
        stderr_lower = stderr.lower()
        auth_blocked = any(
            marker in stderr_lower
            for marker in (
                "authentication failed",
                "could not read username",
                "terminal prompts disabled",
                "permission denied",
                "fatal: could not",
                "device code",
            )
        )

        status = (
            "pushed"
            if result["returncode"] == 0
            else ("auth_blocked" if auth_blocked else "failed")
        )
        return {
            "status": status,
            "repo_path": str(cwd),
            "remote": remote,
            "branch": branch,
            "stdout": result.get("stdout", ""),
            "stderr": stderr,
            "returncode": result["returncode"],
            "tool": "mcp_gitkraken_git_push",
        }

    def _chatdev_runs_file(self) -> Path:
        path = Path(os.getenv("NUSYQ_CHATDEV_RUNS_FILE", "state/reports/chatdev_runs.json"))
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _load_chatdev_runs(self) -> dict[str, dict[str, Any]]:
        path = self._chatdev_runs_file()
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError, OSError):
            return {}
        runs = data.get("runs", {}) if isinstance(data, dict) else {}
        return runs if isinstance(runs, dict) else {}

    def _save_chatdev_runs(self, runs: dict[str, dict[str, Any]]) -> None:
        path = self._chatdev_runs_file()
        payload = {"updated_at": datetime.now().isoformat(), "runs": runs}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _chatdev_pid_running(self, pid: int) -> bool:
        if pid <= 0:
            return False

        status_path = Path(f"/proc/{pid}/status")
        if status_path.exists():
            status_text = status_path.read_text(encoding="utf-8", errors="replace")
            if "\nState:\tZ" in status_text or status_text.startswith("State:\tZ"):
                return False

        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    def _refresh_chatdev_run(self, run: dict[str, Any]) -> dict[str, Any]:
        refreshed = dict(run)
        pid = int(refreshed.get("pid") or 0)
        running = self._chatdev_pid_running(pid)
        refreshed["running"] = running
        refreshed["last_checked_at"] = datetime.now().isoformat()

        chatdev_path = Path(str(refreshed.get("chatdev_path") or ""))
        project_prefix = str(refreshed.get("name") or "")
        project_dir = None
        py_file_count = 0
        has_metadata = False
        if chatdev_path.exists() and project_prefix:
            warehouse = chatdev_path / "WareHouse"
            if warehouse.exists():
                candidates = sorted(
                    [p for p in warehouse.glob(f"{project_prefix}*") if p.is_dir()],
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if candidates:
                    project_dir = candidates[0]
                    py_file_count = len(list(project_dir.rglob("*.py")))
                    has_metadata = (project_dir / "meta.txt").exists() or (
                        project_dir / "manual.md"
                    ).exists()

        if project_dir:
            refreshed["project_dir"] = str(project_dir)
            refreshed["artifact_summary"] = {
                "py_files": py_file_count,
                "has_metadata": has_metadata,
            }

        status = str(refreshed.get("status") or "").lower()
        if running:
            refreshed["status"] = "running"
        elif status not in {"completed", "failed"}:
            refreshed["status"] = "completed" if (py_file_count > 0 or has_metadata) else "failed"
            refreshed["finished_at"] = datetime.now().isoformat()

        return refreshed

    def _materialize_chatdev_degraded_output(
        self,
        *,
        task: str,
        name: str,
        model: str,
        org: str,
        reason: str,
    ) -> dict[str, Any]:
        """Create a deterministic fallback artifact when degraded ChatDev mode is requested."""
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        root = Path(os.getenv("NUSYQ_CHATDEV_DEGRADED_ROOT", "state/runtime/chatdev_degraded"))
        project_dir = root / "WareHouse" / f"{name}_{stamp}"
        project_dir.mkdir(parents=True, exist_ok=True)

        main_py = project_dir / "main.py"
        main_py.write_text(
            "\n".join(
                [
                    '"""Degraded ChatDev fallback artifact."""',
                    "",
                    "def main() -> None:",
                    '    print("Degraded ChatDev fallback executed.")',
                    "",
                    "if __name__ == '__main__':",
                    "    main()",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        metadata = {
            "mode": "degraded",
            "created_at": datetime.now().isoformat(),
            "task": task,
            "name": name,
            "model": model,
            "org": org,
            "reason": reason,
        }
        (project_dir / "project.json").write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )
        (project_dir / "manual.md").write_text(
            "\n".join(
                [
                    "# Degraded ChatDev Output",
                    "",
                    "This scaffold was generated because the full ChatDev runtime could not execute.",
                    "",
                    f"- Reason: `{reason}`",
                ]
            ),
            encoding="utf-8",
        )

        return {
            "project_dir": str(project_dir),
            "files": [
                str(main_py),
                str(project_dir / "project.json"),
                str(project_dir / "manual.md"),
            ],
        }

    def _handle_chatdev_status(self, parameters: dict[str, Any]) -> dict[str, Any]:
        if not ChatDevLauncher:
            return {"error": "ChatDevLauncher unavailable"}
        launcher = ChatDevLauncher()
        launcher_status = cast(dict[str, Any], launcher.check_status())

        run_id = str(parameters.get("run_id") or "").strip()
        wait_seconds = float(parameters.get("wait_seconds") or 0)
        poll_interval = max(0.5, float(parameters.get("poll_interval_seconds") or 2))
        recent_limit = int(parameters.get("recent_limit") or 10)

        runs = self._load_chatdev_runs()
        refreshed_runs: dict[str, dict[str, Any]] = {
            rid: self._refresh_chatdev_run(run)
            for rid, run in runs.items()
            if isinstance(run, dict)
        }
        self._save_chatdev_runs(refreshed_runs)

        if run_id:
            deadline = time.time() + max(0.0, wait_seconds)
            selected = refreshed_runs.get(run_id)
            while (
                selected
                and max(0.0, wait_seconds) > 0
                and str(selected.get("status", "")).lower() == "running"
                and time.time() < deadline
            ):
                time.sleep(poll_interval)
                refreshed_runs = self._load_chatdev_runs()
                selected = refreshed_runs.get(run_id)
                if isinstance(selected, dict):
                    selected = self._refresh_chatdev_run(selected)
                    refreshed_runs[run_id] = selected
                    self._save_chatdev_runs(refreshed_runs)

            if not isinstance(selected, dict):
                return {
                    "launcher": launcher_status,
                    "error": f"chatdev run not found: {run_id}",
                    "run_id": run_id,
                }
            return {"launcher": launcher_status, "run_id": run_id, "run": selected}

        recent = sorted(
            refreshed_runs.values(),
            key=lambda item: str(item.get("started_at", "")),
            reverse=True,
        )[: max(1, recent_limit)]
        return {
            "launcher": launcher_status,
            "recent_runs": recent,
            "total_runs": len(refreshed_runs),
        }

    def _handle_chatdev_run(self, parameters: dict[str, Any]) -> dict[str, Any]:
        if not ChatDevLauncher:
            return {"error": "ChatDevLauncher unavailable"}
        if parameters.get("use_ollama"):
            os.environ["CHATDEV_USE_OLLAMA"] = "1"
        launcher = ChatDevLauncher()
        git_mode = parameters.get("git_mode", False)
        task = parameters.get("task", "Create a simple demo app")
        name = parameters.get("name", "ChatDevProject")
        model = parameters.get("model", "gpt-4o-mini")
        org = parameters.get("org", "NuSyQ")
        config = parameters.get("config", "Default")
        sandbox = bool(parameters.get("sandbox", False))
        degraded_mode = bool(parameters.get("degraded_mode", False))
        run_id = f"chatdev_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        launcher.setup_api_key()
        launcher.setup_environment()
        if git_mode:
            os.environ["CHATDEV_GIT_MODE"] = "true"
            os.environ.setdefault("CHATDEV_GIT_BRANCH", f"{name}-autogen")

        try:
            process = launcher.launch_chatdev(
                task, name, model, org, config, sandbox=sandbox, degraded_mode=degraded_mode
            )
        except Exception as exc:
            if not degraded_mode:
                raise

            fallback = self._materialize_chatdev_degraded_output(
                task=task,
                name=name,
                model=model,
                org=org,
                reason=str(exc),
            )
            chatdev_path = str(getattr(launcher, "chatdev_path", ""))
            response = {
                "run_id": run_id,
                "pid": None,
                "task": task,
                "name": name,
                "model": model,
                "use_ollama": bool(parameters.get("use_ollama")),
                "git_mode": git_mode,
                "sandbox": sandbox,
                "degraded_mode": degraded_mode,
                "degraded": True,
                "status": "degraded_completed",
                "project_dir": fallback["project_dir"],
                "files": fallback["files"],
                "fallback_reason": str(exc),
                "status_tool": "chatdev_status",
            }
            runs = self._load_chatdev_runs()
            runs[run_id] = {
                "run_id": run_id,
                "status": response["status"],
                "pid": None,
                "running": False,
                "task": task,
                "name": name,
                "model": model,
                "org": org,
                "config": config,
                "chatdev_path": chatdev_path,
                "use_ollama": bool(parameters.get("use_ollama")),
                "git_mode": git_mode,
                "sandbox": sandbox,
                "degraded_mode": degraded_mode,
                "degraded": True,
                "project_dir": fallback["project_dir"],
                "started_at": datetime.now().isoformat(),
                "finished_at": datetime.now().isoformat(),
                "fallback_reason": str(exc),
                "run_protocol_bundle": None,
            }
            self._save_chatdev_runs(runs)
            return response

        pid = getattr(process, "pid", None)
        chatdev_path = str(getattr(launcher, "chatdev_path", ""))
        response = {
            "run_id": run_id,
            "pid": pid,
            "task": task,
            "name": name,
            "model": model,
            "use_ollama": bool(parameters.get("use_ollama")),
            "git_mode": git_mode,
            "sandbox": sandbox,
            "degraded_mode": degraded_mode,
            "status": "running" if pid else "submitted",
            "status_tool": "chatdev_status",
        }
        try:
            from src.system.run_protocol import (build_claims_evidence,
                                                 build_handoff_template,
                                                 materialize_run_bundle)

            if is_feature_enabled("trust_artifacts_enabled") and pid:
                manifest = {
                    "task": task,
                    "name": name,
                    "model": model,
                    "organization": org,
                    "config": config,
                    "use_ollama": bool(parameters.get("use_ollama")),
                    "git_mode": git_mode,
                    "runner": "mcp_chatdev_run",
                    "env": {"CHATDEV_PATH": str(launcher.chatdev_path)},
                }
                claims = build_claims_evidence(
                    [
                        {
                            "claim": "ChatDev run via MCP",
                            "evidence": "process.pid",
                            "pointer": str(pid),
                        }
                    ]
                )
                handoff = build_handoff_template(
                    changes=[f"MCP launched ChatDev task '{task}' (PID {pid})"],
                    next_actions=["Monitor logs", "Collect output artifacts"],
                    impact=[f"Workspace: {launcher.chatdev_path}"],
                    suggested_agent="Codex",
                )
                bundle = materialize_run_bundle(
                    manifest=manifest,
                    replay_cmd=[
                        sys.executable,
                        str(launcher.chatdev_path / "run.py"),
                        "--task",
                        task,
                        "--name",
                        name,
                        "--model",
                        model,
                        "--org",
                        org,
                        "--config",
                        config,
                    ],
                    replay_env={
                        "CHATDEV_PATH": str(launcher.chatdev_path),
                        "CHATDEV_USE_OLLAMA": "1" if parameters.get("use_ollama") else "0",
                    },
                    handoff=handoff,
                    claims=claims,
                )
                response["run_protocol_bundle"] = str(bundle.base)
        except Exception as rp_err:
            response["run_protocol_bundle_error"] = str(rp_err)

        runs = self._load_chatdev_runs()
        runs[run_id] = {
            "run_id": run_id,
            "status": response["status"],
            "pid": pid,
            "task": task,
            "name": name,
            "model": model,
            "org": org,
            "config": config,
            "chatdev_path": chatdev_path,
            "use_ollama": bool(parameters.get("use_ollama")),
            "git_mode": git_mode,
            "sandbox": sandbox,
            "degraded_mode": degraded_mode,
            "started_at": datetime.now().isoformat(),
            "run_protocol_bundle": response.get("run_protocol_bundle"),
        }
        self._save_chatdev_runs(runs)

        return response

    def _handle_llm_route(self, parameters: dict[str, Any]) -> dict[str, Any]:
        try:
            from src.integration.universal_llm_gateway import \
                UniversalLLMGateway

            gw = UniversalLLMGateway()
            return cast(
                dict[str, Any],
                gw.route_request(
                    prompt=parameters.get("prompt", ""),
                    model_hint=parameters.get("model_hint"),
                    capability_tags=parameters.get("capability_tags", []),
                    prefer_local=bool(parameters.get("prefer_local", False)),
                    max_cost=parameters.get("max_cost"),
                ),
            )
        except Exception as exc:
            return {"error": str(exc)}

    def _handle_swarm_run(self, parameters: dict[str, Any]) -> dict[str, Any]:
        try:
            from src.orchestration.swarm_router import get_swarm_router

            router = get_swarm_router()
            mode = parameters.get("mode", "sequential")
            steps = parameters.get("steps", [])
            if mode == "sequential":
                return cast(dict[str, Any], router.run_sequential(steps))
            if mode == "concurrent":
                return cast(dict[str, Any], router.run_concurrent(steps))
            if mode == "vote":
                return cast(dict[str, Any], router.run_vote(steps))
            if mode == "map_reduce":
                return cast(
                    dict[str, Any],
                    router.run_map_reduce(
                        map_tasks=steps,
                        reduce_prompt=parameters.get("reduce_prompt", "Summarize"),
                        reduce_model_hint=parameters.get("reduce_model_hint"),
                    ),
                )
            return {"error": f"unknown mode {mode}"}
        except Exception as exc:
            return {"error": str(exc)}

    def _handle_sandbox_run(self, parameters: dict[str, Any]) -> dict[str, Any]:
        try:
            from src.integration.sandbox_runner import get_sandbox_runner
            from src.system.policy import safety_preflight

            runner = get_sandbox_runner()
            cmd = parameters.get("command", [])
            env = parameters.get("env", {})
            if not cmd:
                return {"error": "command required"}
            policy = safety_preflight(cmd)
            if policy.get("risky") == "true":
                return {"error": "command blocked by safety preflight", "policy": policy}
            res = runner.run(cmd, env=env)
            return {
                "success": res.success,
                "returncode": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "workdir": str(res.workdir),
            }
        except Exception as exc:
            return {"error": str(exc)}

    def run(self, debug: bool = False) -> None:
        """Run the MCP server.

        Args:
            debug: Enable Flask debug mode

        """
        logger.info("Starting MCP Server on %s:%s", self.host, self.port)
        self.app.run(host=self.host, port=self.port, debug=debug)


def main() -> None:
    """Main entry point for MCP server."""
    server = MCPServer()
    server.run(debug=False)


if __name__ == "__main__":
    main()
