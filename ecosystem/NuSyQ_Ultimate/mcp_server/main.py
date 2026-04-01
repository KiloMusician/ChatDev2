"""
NuSyQ MCP Server - Model Context Protocol Integration
=====================================================

Purpose:
    Bridges Claude Code AI assistant with the local NuSyQ AI ecosystem.
    Provides access to Ollama models, file operations, Jupyter execution,
    and system information via the Model Context Protocol (MCP).

Architecture:
    - FastAPI-based REST server with async support
    - MCP-compliant endpoints for tool discovery and execution
    - Integration with ConfigManager for unified settings
    - Health monitoring and component status tracking

Key Features:
    1. Ollama model querying (local LLM inference)
    2. File system operations (read/write with encoding support)
    3. Jupyter code execution (Python evaluation)
    4. System information retrieval (config, models, health)
    5. Health checks for all components

Security Considerations:
    - CORS enabled for development (restrict in production)
    - File operations need path validation
    - Code execution requires sandboxing in production
    - Authentication should be added for remote access

cspell: ignore sandboxing, setgid, Pyodide, coro, ASGI
"""

# Disable 'broad-except' lint warnings for this module while we
# iteratively harden exception handling in specific functions.
# Also disable 'too-many-lines' as this is a monolithic FastAPI application
# server where all tools/endpoints are cohesively bundled together.
# Also disable 'no-name-in-module' for pydantic imports (false positive).
# pylint: disable=broad-except,try-except-raise,too-many-lines
# pylint: disable=no-name-in-module
# pylint: disable=no-member

import asyncio
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import psutil  # type: ignore[import-untyped]
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

if TYPE_CHECKING:
    import aiohttp  # type: ignore
else:
    try:
        import aiohttp
    except ImportError:
        aiohttp = None
        logging.getLogger("nusyq-mcp-server").warning(
            "aiohttp not available; HTTP checks will fallback to CLI."
        )

# === Configuration Manager Import ===
# Import centralized configuration management system

# Add parent directory to Python path to access shared modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import agent router for intelligent task routing
try:
    from config.agent_router import AgentRouter, Task, TaskComplexity, TaskType

    AGENT_ROUTER_AVAILABLE = True
except ImportError:
    AGENT_ROUTER_AVAILABLE = False
    logging.getLogger("nusyq-mcp-server").warning(
        "Agent router not available. Tasks will be routed to default models."
    )
    # Fallback TaskComplexity enum so server code referring to
    # TaskComplexity.SIMPLE/MODERATE etc. doesn't NameError when
    # the agent router package is missing.
    try:
        from enum import Enum

        class TaskComplexity(Enum):
            SIMPLE = "simple"
            MODERATE = "moderate"
            COMPLEX = "complex"
            CRITICAL = "critical"

    except Exception:
        # Best-effort fallback if enum import fails (very unlikely)
        class TaskComplexity:  # type: ignore
            SIMPLE = "simple"
            MODERATE = "moderate"
            COMPLEX = "complex"
            CRITICAL = "critical"


# Import query cache
try:
    from mcp_server.query_cache import get_cache

    QUERY_CACHE_AVAILABLE = True
except ImportError:
    QUERY_CACHE_AVAILABLE = False
    logging.getLogger("nusyq-mcp-server").warning(
        "Query cache not available. All queries will hit Ollama directly."
    )

# Import performance metrics
try:
    from mcp_server.performance_metrics import get_metrics

    PERFORMANCE_METRICS_AVAILABLE = True
except ImportError:
    PERFORMANCE_METRICS_AVAILABLE = False
    logging.getLogger("nusyq-mcp-server").warning(
        "Performance metrics not available. Metrics tracking disabled."
    )

try:
    import config.config_manager as _config_module

    ConfigManager = _config_module.ConfigManager
except ImportError:
    # Graceful fallback if ConfigManager is unavailable. Define a
    # clearly-named fallback implementation and bind it to
    # 'ConfigManager' so rest of the code can reference that name.
    class _FallbackConfigManager:
        """Minimal fallback configuration manager"""

        @staticmethod
        def load_config(_file_path: str) -> None:
            """
            Fallback config loader.
            Returns None when flexibility_manager unavailable.
            """
            # _file_path intentionally unused in fallback
            return None

        @staticmethod
        def reload_all() -> Dict[str, Any]:
            """Fallback reload_all - returns empty results"""
            return {"status": "fallback", "configs_loaded": []}

        @staticmethod
        def get_config(config_name: str) -> Dict[str, Any]:
            """Fallback get_config - returns empty config"""
            return {"name": config_name, "status": "unavailable"}

    ConfigManager = _FallbackConfigManager  # type: ignore[assignment]

try:
    from config.adaptive_timeout_manager import (
        AgentType as TimeoutAgentType,
    )
    from config.adaptive_timeout_manager import (
        TaskComplexity as TimeoutTaskComplexity,
    )
    from config.adaptive_timeout_manager import (
        get_timeout_manager,
    )

    ADAPTIVE_TIMEOUT_AVAILABLE = True
except ImportError:
    ADAPTIVE_TIMEOUT_AVAILABLE = False
    # Provide fallback TimeoutAgentType and TimeoutTaskComplexity enums so
    # downstream code that references these names still functions even when
    # the adaptive timeout manager package isn't installed in the image.
    try:
        from enum import Enum

        class TimeoutAgentType(Enum):
            LOCAL_FAST = "local_fast"
            LOCAL_QUALITY = "local_quality"

        class TimeoutTaskComplexity(Enum):
            TRIVIAL = "trivial"
            SIMPLE = "simple"
            MODERATE = "moderate"
            COMPLEX = "complex"
            CRITICAL = "critical"

    except Exception:
        # Defensive plain-class fallback
        class TimeoutAgentType:  # type: ignore
            LOCAL_FAST = "local_fast"
            LOCAL_QUALITY = "local_quality"

        class TimeoutTaskComplexity:  # type: ignore
            TRIVIAL = "trivial"
            SIMPLE = "simple"
            MODERATE = "moderate"
            COMPLEX = "complex"
            CRITICAL = "critical"


# === Logging Configuration ===
# Structured logging with timestamps for debugging and monitoring

# Create logs directory if it doesn't exist
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging with both console and file handlers
logger = logging.getLogger("nusyq-mcp-server")
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

# File handler with rotation (10MB per file, keep 5 backups)
file_handler = RotatingFileHandler(
    logs_dir / "mcp_server.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
)
file_handler.setFormatter(file_formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Initialize terminal logging (best-effort) so server logs also propagate into
# the workspace TerminalManager channels when available.
try:
    # Import via package path to ensure repo root resolution works when running
    # the server as a module or script.
    from src.system.init_terminal import init_terminal_logging

    init_terminal_logging(channel="NuSyQ-MCP", level=logging.INFO)
except Exception:
    # non-fatal if the terminal logging shim isn't
    # available in this environment
    logger.debug("Terminal logging shim not available; continuing without it")

# === Constants ===
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"


# === Pydantic Models for Request/Response Validation ===


class MCPRequest(BaseModel):
    """
    Model Context Protocol request structure

    Attributes:
        method: MCP method name (e.g., "tools/list", "tools/call")
        params: Method parameters as key-value dictionary
        id: Optional request identifier for tracking/correlation
    """

    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[str] = None


class MCPResponse(BaseModel):
    """
    Model Context Protocol response structure

    Attributes:
        result: Successful operation result
        error: Error information (code and message) if failed
        id: Request identifier for correlation
    """

    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class ToolRequest(BaseModel):
    """
    Direct tool execution request (non-MCP endpoint)

    Attributes:
        name: Tool name to execute
        arguments: Tool-specific arguments
    """

    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class NuSyQMCPServer:
    """
    Main MCP Server for NuSyQ AI Ecosystem Integration

    This class orchestrates the Model Context Protocol server that bridges
    Claude Code with local AI infrastructure (Ollama, Jupyter, file system).

    Responsibilities:
        - Initialize FastAPI application with MCP endpoints
        - Manage configuration loading and validation
        - Execute tool requests (Ollama queries, file ops, etc.)
        - Monitor component health
        - Provide system information and diagnostics

    Architecture Pattern:
        Uses dependency injection for configuration and follows
        async/await patterns for non-blocking operations.
    """

    def __init__(self):
        """
        Initialize MCP server components

        Setup order:
            1. Initialize ConfigManager for centralized settings
            2. Create FastAPI app with metadata
            3. Configure middleware (CORS, etc.)
            4. Register all HTTP routes
            5. Load all configuration files
            6. Set security allowed paths
            7. Initialize agent router for intelligent task routing
        """
        # Use NuSyQ root directory as base path for ConfigManager
        # (mcp_server/main.py is one level down from repo root)
        nusyq_root = Path(__file__).parent.parent
        self.config_manager = ConfigManager(str(nusyq_root))
        self.app = FastAPI(
            title="NuSyQ MCP Server",
            description="Model Context Protocol server for NuSyQ AI ecosystem",
            version="1.0.0",
        )

        # Security: Define allowed base paths for file operations
        self.allowed_base_paths = [
            Path.home(),  # User home directory
            Path.cwd(),  # Current working directory
            Path.cwd().parent,  # Parent of current dir (for NuSyQ repo)
        ]

        # Initialize agent router if available
        self.agent_router = None
        if AGENT_ROUTER_AVAILABLE:
            try:
                self.agent_router = AgentRouter()
                logger.info("Agent router initialized successfully")
            except Exception as e:
                logger.warning("Failed to initialize agent router: %s", e)

        # Initialize query cache if available
        self.query_cache = None
        if QUERY_CACHE_AVAILABLE:
            try:
                self.query_cache = get_cache(max_size=100, ttl_seconds=300)
                logger.info("Query cache initialized (size=100, ttl=300s)")
            except Exception as e:
                logger.warning("Failed to initialize query cache: %s", e)

        # Initialize performance metrics if available
        self.metrics = None
        if PERFORMANCE_METRICS_AVAILABLE:
            try:
                self.metrics = get_metrics()
                logger.info("Performance metrics initialized")
            except Exception as e:
                logger.warning("Failed to initialize metrics: %s", e)

        # Initialize adaptive timeout manager if available
        self.timeout_manager = None
        if ADAPTIVE_TIMEOUT_AVAILABLE:
            try:
                self.timeout_manager = get_timeout_manager()
            except Exception as e:
                logger.warning("Failed to initialize adaptive timeout manager: %s", e)

        self._setup_middleware()
        self._setup_routes()
        self._load_configs()

    def _infer_timeout_agent_type(self, model: str) -> TimeoutAgentType:
        """Map model name to adaptive timeout agent type."""
        name = model.lower()
        if any(key in name for key in ("phi3.5", "qwen2.5-coder:7b")):
            return TimeoutAgentType.LOCAL_FAST
        return TimeoutAgentType.LOCAL_QUALITY

    def _infer_timeout_complexity(self, prompt: str) -> TimeoutTaskComplexity:
        """Estimate task complexity from prompt length."""
        length = len(prompt or "")
        if length < 50:
            return TimeoutTaskComplexity.TRIVIAL
        if length < 150:
            return TimeoutTaskComplexity.SIMPLE
        if length < 500:
            return TimeoutTaskComplexity.MODERATE
        if length < 1500:
            return TimeoutTaskComplexity.COMPLEX
        return TimeoutTaskComplexity.CRITICAL

    def _map_task_complexity(self, complexity: TaskComplexity) -> TimeoutTaskComplexity:
        """Map router complexity to adaptive timeout complexity."""
        mapping = {
            TaskComplexity.SIMPLE: TimeoutTaskComplexity.SIMPLE,
            TaskComplexity.MODERATE: TimeoutTaskComplexity.MODERATE,
            TaskComplexity.COMPLEX: TimeoutTaskComplexity.COMPLEX,
            TaskComplexity.CRITICAL: TimeoutTaskComplexity.CRITICAL,
        }
        return mapping.get(complexity, TimeoutTaskComplexity.MODERATE)

    def _resolve_agent_models(self, agent_names: List[str]) -> tuple[List[str], Dict[str, str]]:
        """
        Resolve agent registry names to Ollama model names.

        Returns:
            (model_names, model_to_agent)
        """
        model_names: List[str] = []
        model_to_agent: Dict[str, str] = {}

        for name in agent_names:
            agent = self.agent_router.get_agent_by_name(name) if self.agent_router else None
            model = None
            if agent and agent.model:
                model = agent.model
            elif ":" in name:
                model = name

            if model:
                model_names.append(model)
                model_to_agent[model] = name
            else:
                logger.debug("Skipping non-Ollama agent for consensus: %s", name)

        return model_names, model_to_agent

    def _validate_path(self, file_path: Path) -> Path:
        """
        Validate file path for security (prevent path traversal attacks)

        Security Checks:
            1. Resolve path to absolute form
            2. Normalize path (remove ../ sequences)
            3. Verify path is within allowed base directories
            4. Check for null bytes and other dangerous characters

        Args:
            file_path: Path to validate

        Returns:
            Resolved absolute Path object

        Raises:
            ValueError: If path is outside allowed directories or
                contains dangerous patterns
        """
        try:
            # Resolve to absolute path (handles relative paths and symlinks)
            resolved_path = file_path.resolve()

            # Check for null bytes (directory traversal attack vector)
            if "\0" in str(file_path):
                raise ValueError("Path contains null bytes")

            # Verify path is within at least one allowed base path
            is_allowed = any(resolved_path.is_relative_to(base) for base in self.allowed_base_paths)

            if not is_allowed:
                allowed_str = ", ".join(str(p) for p in self.allowed_base_paths)
                raise ValueError(
                    f"Access denied: Path '{resolved_path}' is "
                    f"outside allowed directories: {allowed_str}"
                )

            return resolved_path

        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid path: {e}") from e

    def _setup_middleware(self):
        """
        Configure FastAPI middleware stack

        CORS Configuration:
            - Uses environment variable ALLOWED_ORIGINS for production
            - Defaults to local development origins
            - Credentials support enabled for authenticated requests

        Environment Variables:
            ALLOWED_ORIGINS: Comma-separated list of allowed origins
            Example: "https://app.example.com,https://api.example.com"
        """
        # Get allowed origins from environment or use development defaults
        allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
        if allowed_origins_env:
            allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
        else:
            # Development defaults
            allowed_origins = [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000",
            ]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )

    def _load_configs(self):
        """
        Load all YAML configuration files via ConfigManager

        Loads:
            - nusyq.manifest.yaml (system manifest)
            - knowledge-base.yaml (learning log)
            - AI_Hub/ai-ecosystem.yaml (AI model configs)
            - config/tasks.yaml (task definitions)

        Note: Errors are logged but don't prevent server startup
        """
        try:
            results = self.config_manager.reload_all()
            logger.info("Configuration load results: %s", results)
        except (RuntimeError, ValueError, OSError) as e:
            # Expected, recoverable configuration loading issues
            logger.error("Failed to load configurations: %s", e)
            # Do not re-raise here; a missing config should not
            # prevent server startup. Unexpected exceptions will
            # propagate to the caller so they can be handled by a
            # higher-level startup handler (keeps failures visible).

    def _setup_routes(self):
        """
        Register all FastAPI HTTP routes

        Routes:
            GET  /          - Server info and capabilities
            POST /mcp       - Main MCP protocol endpoint
            POST /tools/execute - Direct tool execution
            GET  /health    - Component health checks
        """

        @self.app.get("/")
        def root():
            """
            Root endpoint - provides basic server information.

            Returns a small summary including available MCP tools,
            server version and a timestamp. This is intentionally
            lightweight and safe to call frequently.
            """
            project_name = "NuSyQ MCP Server"
            tools_result = self._get_available_tools()
            return {
                "success": True,
                "project_name": project_name,
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
                "available_tools": tools_result.get("tools", []),
            }

        @self.app.post("/mcp")
        async def mcp_endpoint(request: MCPRequest):
            """
            Main Model Context Protocol endpoint

            Handles MCP-compliant requests for tool discovery and execution.

            Supported Methods:
                - tools/list: Returns available tools with schemas
                - tools/call: Executes a specific tool with arguments

            Error Codes:
                -32601: Method not found
                -32603: Internal error during execution

            Args:
                request: MCPRequest with method, params, and optional id

            Returns:
                MCPResponse with result or error
            """
            try:
                if request.method == "tools/list":
                    tools_result = self._get_available_tools()
                    return MCPResponse(result=tools_result, id=request.id)
                elif request.method == "tools/call":
                    tool_name = request.params.get("name")
                    if not isinstance(tool_name, str):
                        return MCPResponse(
                            error={
                                "code": -32602,
                                "message": ("Invalid params: 'name' must be a string"),
                            },
                            id=request.id,
                        )
                    tool_args = request.params.get("arguments", {})
                    result = await self._execute_tool(tool_name, tool_args)
                    return MCPResponse(result=result, id=request.id)
                else:
                    return MCPResponse(
                        error={
                            "code": -32601,
                            "message": (f"Method not found: {request.method}"),
                        },
                        id=request.id,
                    )
            except (ValueError, TypeError, KeyError) as e:
                # Parameter validation / type errors
                logger.error("MCP request failed (client error): %s", e)
                return MCPResponse(
                    error={"code": -32602, "message": str(e)},
                    id=request.id,
                )

        @self.app.post("/tools/execute")
        async def execute_tool(request: ToolRequest):
            """
            Direct tool execution endpoint (non-MCP)

            Simpler alternative to MCP endpoint for direct tool calls.
            Useful for testing and simple integrations.

            Args:
                request: ToolRequest with name and arguments

            Returns:
                Success indicator and tool result

            Raises:
                HTTPException: 500 if tool execution fails
            """
            try:
                result = await self._execute_tool(
                    request.name,
                    request.arguments,
                )
                return {"success": True, "result": result}
            except (ValueError, KeyError, RuntimeError, HTTPException) as e:
                logger.error("Tool execution failed: %s", e)
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.app.get("/health")
        async def health_check():
            """
            Component health check endpoint

            Monitors:
                - Server uptime/status
                - Ollama service availability
                - Configuration load status
                - Component connectivity

            Returns:
                Health status with timestamp and component details
            """
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": await self._check_component_health(),
            }

        # Lightweight liveness probe (minimal info) for orchestration tooling
        @self.app.get("/health/liveness")
        def liveness_probe():
            return {"status": "alive", "timestamp": datetime.now().isoformat()}

    def _get_available_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get list of all available MCP tools with JSON schemas

        Returns tool definitions following MCP specification:
        - name: Unique tool identifier
        - description: Human-readable purpose
        - inputSchema: JSON Schema for parameters

        Returns:
            Dictionary with 'tools' key containing list of tool definitions
        """
        tools = [
            {
                "name": "ollama_query",
                "description": ("Query Ollama models for code generation and analysis"),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "description": ("Model name (e.g., qwen2.5-coder:7b)"),
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Query prompt",
                        },
                        "max_tokens": {
                            "type": "integer",
                            "default": 100,
                            "description": ("Max completion tokens (default: 100)"),
                        },
                    },
                    "required": ["model", "prompt"],
                },
            },
            {
                "name": "chatdev_create",
                "description": (
                    "Create software using ChatDev multi-agent framework with local models"
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": ("Software development task description"),
                        },
                        "model": {
                            "type": "string",
                            "default": DEFAULT_OLLAMA_MODEL,
                            "description": "Ollama model to use",
                        },
                        "config": {
                            "type": "string",
                            "default": "NuSyQ_Ollama",
                            "description": "ChatDev configuration",
                        },
                        "timeout": {
                            "type": "integer",
                            "default": 300,
                            "description": "Maximum execution time in seconds",
                        },
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "file_read",
                "description": "Read file contents",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "encoding": {"type": "string", "default": "utf-8"},
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "file_write",
                "description": "Write content to file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {
                            "type": "string",
                            "description": "File content",
                        },
                        "encoding": {"type": "string", "default": "utf-8"},
                    },
                    "required": ["path", "content"],
                },
            },
            {
                "name": "system_info",
                "description": "Get system and AI ecosystem information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "component": {
                            "type": "string",
                            "enum": ["all", "ollama", "models", "config"],
                        }
                    },
                },
            },
            {
                "name": "run_jupyter_cell",
                "description": "Execute code in Jupyter environment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute",
                        },
                        "kernel": {"type": "string", "default": "python3"},
                    },
                    "required": ["code"],
                },
            },
            {
                "name": "ai_council_session",
                "description": (
                    "Convene the AI Council for high-level architectural "
                    "discussions, warnings, strategic decisions, and "
                    "multi-agent collaboration. 11-agent governance "
                    "system with Executive/Technical/Advisory tiers."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_type": {
                            "type": "string",
                            "enum": [
                                "STANDUP",
                                "EMERGENCY",
                                "ADVISORY",
                                "REFLECTION",
                                "QUANTUM_WINK",
                            ],
                            "description": ("Type of council session to execute"),
                        },
                        "topic": {
                            "type": "string",
                            "description": ("Discussion topic or problem statement"),
                        },
                        "context": {
                            "type": "object",
                            "description": ("Additional context (files, errors, etc.)"),
                            "default": {},
                        },
                    },
                    "required": ["session_type", "topic"],
                },
            },
            {
                "name": "query_github_copilot",
                "description": (
                    "Submit a query to GitHub Copilot (the agent you're "
                    "talking to now!) for code assistance, implementation "
                    "guidance, or technical questions. Use this for "
                    "bidirectional AI collaboration."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": ("Question or task for GitHub Copilot"),
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["critical", "high", "normal", "low"],
                            "default": "normal",
                            "description": "Query priority level",
                        },
                        "context": {
                            "type": "object",
                            "description": ("Additional context (code snippets, files, etc.)"),
                            "default": {},
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "multi_agent_orchestration",
                "description": (
                    "Orchestrate a multi-agent conversation with Ollama "
                    "models, AI Council, and ChatDev. Supports 4 "
                    "conversation modes: TURN_TAKING, PARALLEL_CONSENSUS, "
                    "REFLECTION, CHATDEV_WORKFLOW."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Task description for agents",
                        },
                        "agents": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of agent names to include",
                            "default": ["ollama_qwen_14b", "ollama_qwen_7b"],
                        },
                        "mode": {
                            "type": "string",
                            "enum": [
                                "TURN_TAKING",
                                "PARALLEL_CONSENSUS",
                                "REFLECTION",
                                "CHATDEV_WORKFLOW",
                            ],
                            "default": "TURN_TAKING",
                            "description": ("Conversation orchestration mode"),
                        },
                        "task_type": {
                            "type": "string",
                            "enum": [
                                "docstring",
                                "code_generation",
                                "refactoring",
                                "bug_fix",
                                "architecture",
                                "security_audit",
                                "documentation",
                                "test_generation",
                                "code_review",
                                "full_feature",
                                "codebase_search",
                            ],
                            "default": "code_generation",
                            "description": ("Routing hint for task type"),
                        },
                        "complexity": {
                            "type": "string",
                            "enum": [
                                "simple",
                                "moderate",
                                "complex",
                                "critical",
                            ],
                            "default": "moderate",
                            "description": ("Routing hint for task complexity"),
                        },
                        "include_ai_council": {
                            "type": "boolean",
                            "default": False,
                            "description": ("Whether to include AI Council in discussion"),
                        },
                        "implement_with_chatdev": {
                            "type": "boolean",
                            "default": False,
                            "description": ("Whether to implement result using ChatDev"),
                        },
                    },
                    "required": ["task"],
                },
            },
            {
                "name": "cache_stats",
                "description": (
                    "Get query cache statistics including hit/miss rates, "
                    "cache size, and entry details. Useful for monitoring "
                    "performance and cache effectiveness."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_entries": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include detailed entry information",
                        }
                    },
                    "required": [],
                },
            },
            {
                "name": "performance_metrics",
                "description": (
                    "Get comprehensive performance metrics including query "
                    "latency, throughput, agent performance, cache "
                    "effectiveness, and system resource usage."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "time_window_minutes": {
                            "type": "number",
                            "default": None,
                            "description": ("Limit stats to last N minutes (omit for all time)"),
                        },
                        "export_to_file": {
                            "type": "boolean",
                            "default": False,
                            "description": "Export metrics to JSON file",
                        },
                    },
                    "required": [],
                },
            },
        ]
        return {"tools": tools}

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific tool by name

        Dispatcher method that routes tool execution to appropriate handlers.

        Supported Tools:
            - ollama_query: Query local Ollama LLMs
            - chatdev_create: Create software using ChatDev framework
            - file_read: Read file contents
            - file_write: Write content to files
            - system_info: Get ecosystem information
            - run_jupyter_cell: Execute Python code

        Args:
            tool_name: Name of tool to execute
            arguments: Tool-specific parameters

        Returns:
            Tool execution result dictionary

        Raises:
            ValueError: If tool_name is not recognized
        """
        if tool_name == "ollama_query":
            return await self._ollama_query(arguments)
        elif tool_name == "chatdev_create":
            return await self._chatdev_create(arguments)
        elif tool_name == "file_read":
            return await self._file_read(arguments)
        elif tool_name == "file_write":
            return await self._file_write(arguments)
        elif tool_name == "system_info":
            return await self._system_info(arguments)
        elif tool_name == "run_jupyter_cell":
            return await self._run_jupyter_cell(arguments)
        elif tool_name == "ai_council_session":
            return await self._ai_council_session(arguments)
        elif tool_name == "query_github_copilot":
            return await self._query_github_copilot(arguments)
        elif tool_name == "multi_agent_orchestration":
            return await self._multi_agent_orchestration(arguments)
        elif tool_name == "cache_stats":
            return await self._get_cache_stats(arguments)
        elif tool_name == "performance_metrics":
            return await self._get_performance_metrics(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _ollama_query(
        self,
        args: Dict[str, Any],
        max_retries: int = 3,
        base_delay: float = 1.0,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Query local Ollama LLM models with caching and retry logic

        Sends prompts to locally-hosted Ollama models for code
        generation, analysis, or general-purpose LLM tasks.
        Uses non-streaming mode for synchronous responses.
        Implements exponential backoff retry for transient failures.
        Caches responses for repeated queries (5min TTL).

        Args:
            args: Dictionary with:
                - model (str): Ollama model name
                - prompt (str): Input prompt for the model
                - max_tokens (int, optional): Max completion tokens
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Initial retry delay in seconds (default: 1.0)
            use_cache: Whether to use query cache (default: True)

        Returns:
            Dictionary with:
                - success (bool): Whether request succeeded
                - response (str): Model's generated text
                - model (str): Model that processed request
                - prompt_tokens (int): Estimated input tokens
                - completion_tokens (int): Estimated output tokens
                - retries (int): Number of retries needed
                - cached (bool): Whether response was from cache
                - error (str, optional): Error message if failed

        Note:
            Requires ai_ecosystem config with Ollama base_url
        """
        start_time = time.time()

        model = args["model"]
        prompt = args["prompt"]
        max_tokens = args.get("max_tokens", 100)

        # Check cache first
        if use_cache and self.query_cache:
            cached_result = self.query_cache.get(model, prompt, max_tokens)
            if cached_result:
                # Record cache hit metric
                if self.metrics:
                    self.metrics.record_query(
                        model=model,
                        prompt_length=len(prompt),
                        response_length=len(cached_result.get("response", "")),
                        duration=time.time() - start_time,
                        cached=True,
                        success=True,
                        retries=0,
                    )

                logger.debug(
                    "Cache HIT for %s query (%.1f%% hit rate)",
                    model,
                    self.query_cache.get_stats()["hit_rate"],
                )
                cached_result["cached"] = True
                return cached_result

        # Load Ollama configuration from ecosystem settings
        ai_config = self.config_manager.get_config("ai_ecosystem")
        if not ai_config:
            raise ValueError("AI ecosystem configuration not loaded")

        ollama_url = ai_config["local_models"]["ollama"]["base_url"]
        timeout_seconds = 60
        if self.timeout_manager:
            agent_type = self._infer_timeout_agent_type(model)
            task_complexity = self._infer_timeout_complexity(prompt)
            recommendation = self.timeout_manager.get_timeout(
                agent_type=agent_type, task_complexity=task_complexity
            )
            timeout_seconds = recommendation.timeout_seconds

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                # Make asynchronous HTTP request to Ollama API
                timeout = aiohttp.ClientTimeout(total=timeout_seconds)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        f"{ollama_url}/api/generate",
                        json={
                            "model": model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {"num_predict": max_tokens},
                        },
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            api_response = {
                                "success": True,
                                "response": result.get("response", ""),
                                "model": model,
                                # Simple token estimation
                                "prompt_tokens": len(prompt.split()),
                                "completion_tokens": len(result.get("response", "").split()),
                                "retries": attempt,
                                "cached": False,
                            }

                            # Store in cache
                            if use_cache and self.query_cache:
                                self.query_cache.put(model, prompt, max_tokens, api_response)
                                logger.debug(
                                    "Cached response for %s (size: %d)",
                                    model,
                                    self.query_cache.get_stats()["size"],
                                )

                            # Record successful query metric
                            if self.metrics:
                                response_len = len(api_response["response"])
                                self.metrics.record_query(
                                    model=model,
                                    prompt_length=len(prompt),
                                    response_length=response_len,
                                    duration=time.time() - start_time,
                                    cached=False,
                                    success=True,
                                    retries=attempt,
                                )

                            return api_response
                        else:
                            raise ValueError(f"Ollama request failed: {response.status}")

            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
                ValueError,
                OSError,
            ) as e:
                last_error = e
                if attempt < max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        "Ollama query failed (attempt %d/%d): %s. Retrying in %.1fs...",
                        attempt + 1,
                        max_retries + 1,
                        str(e),
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "Ollama query failed after %d attempts: %s",
                        max_retries + 1,
                        str(e),
                    )

        # Record failed query metric
        if self.metrics:
            self.metrics.record_query(
                model=model,
                prompt_length=len(prompt),
                response_length=0,
                duration=time.time() - start_time,
                cached=False,
                success=False,
                retries=max_retries,
                error=str(last_error),
            )

        return {
            "success": False,
            "error": str(last_error),
            "retries": max_retries,
            "cached": False,
        }

    async def _chatdev_create(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create software using ChatDev multi-agent framework with Ollama

        Args:
            args: Dictionary with:
                - task (str): Development task description
                                - model (str, optional):
                                    Ollama model (default: "qwen2.5-coder:7b")
                                - config (str, optional):
                                    ChatDev config (default: "NuSyQ_Ollama")
                - timeout (int, optional): Max execution time (default: 300s)

        Returns:
            Dictionary with:
                - success (bool): Whether ChatDev completed successfully
                - project_name (str): Generated project identifier
                - output_path (str): Path to generated code
                - summary (str): Brief description of what was created
                - logs (str): ChatDev execution logs
                - error (str, optional): Error message if failed
        """
        task = args.get("task")
        model = args.get("model", DEFAULT_OLLAMA_MODEL)
        config = args.get("config", "NuSyQ_Ollama")
        timeout = args.get("timeout", 300)

        if not task:
            return {"success": False, "error": "Task description is required"}

        try:
            # Generate project name from task
            project_name = re.sub(r"\W", "_", task[:30])
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = f"NuSyQ_{project_name}_{timestamp}"

            # Check if ChatDev is available
            chatdev_path = Path("ChatDev")
            if not chatdev_path.exists():
                return {
                    "success": False,
                    "error": "ChatDev not found in workspace",
                }

            # Prepare command
            cmd = [
                sys.executable,
                str(chatdev_path / "run.py"),
                "--task",
                task,
                "--config",
                config,
                "--name",
                project_name,
                "--org",
                "NuSyQ",
            ]

            # Set environment to use Ollama (mock OpenAI key)
            env = os.environ.copy()
            env["OPENAI_API_KEY"] = "ollama-local-model"
            env["NUSYQ_OLLAMA_MODEL"] = model

            logger.info(
                "Starting ChatDev: task='%s', model=%s, config=%s",
                task,
                model,
                config,
            )

            # Execute ChatDev (pass timeout through to async runner)
            result = await self._run_subprocess(cmd, env=env, proc_timeout=timeout)

            # Determine output path
            warehouse_path = chatdev_path / "WareHouse" / project_name

            if result.get("returncode") == 0:
                # Success - parse output and provide summary
                summary = f"Created software project: {project_name}"
                if await asyncio.to_thread(warehouse_path.exists):
                    files = await asyncio.to_thread(lambda: list(warehouse_path.glob("*")))
                    summary += f" ({len(files)} files generated)"

                return {
                    "success": True,
                    "project_name": project_name,
                    "output_path": str(warehouse_path),
                    "summary": summary,
                    "logs": (result.get("stdout", "")[-1000:]),
                    "model_used": model,
                    "config_used": config,
                }
            else:
                # Failure - return error information
                error_msg = result.get("stderr") or "ChatDev execution failed"
                return {
                    "success": False,
                    "error": error_msg,
                    "logs": (result.get("stdout", "")[-1000:] if result.get("stdout") else ""),
                    "command": " ".join(cmd),
                }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": (f"ChatDev timed out after {timeout} seconds"),
                "suggestion": "Try a simpler task or increase timeout",
            }
        except (OSError, ValueError) as e:
            return {
                "success": False,
                "error": f"ChatDev execution failed: {str(e)}",
            }

    async def _file_read(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Read file contents from local filesystem with security validation

        Args:
            args: Dictionary with:
                - path (str): File path (absolute or relative)
                - encoding (str, optional): Text encoding (default: "utf-8")

        Returns:
            Dictionary with:
                - success (bool): Whether read succeeded
                - content (str): File contents
                - path (str): Resolved file path
                - size (int): Content length in characters
                - error (str, optional): Error message if failed

        Security Features:
            ✅ Path traversal protection via _validate_path()
            ✅ Only allows access within approved base directories
            ✅ Prevents null byte injection
            ✅ Resolves symlinks before validation
        """
        file_path = Path(args["path"])
        encoding = args.get("encoding", "utf-8")

        try:
            # ✅ SEC-002 FIXED: Validate path before accessing
            validated_path = self._validate_path(file_path)

            if not await asyncio.to_thread(validated_path.exists):
                raise FileNotFoundError(f"File not found: {validated_path}")

            content = await asyncio.to_thread(validated_path.read_text, encoding)
            return {
                "success": True,
                "content": content,
                "path": str(validated_path),
                "size": len(content),
            }
        except UnicodeDecodeError as e:
            return {"success": False, "error": str(e)}
        except ValueError as e:
            # Security validation failed
            return {"success": False, "error": f"Security error: {str(e)}"}
        except FileNotFoundError:
            raise
        except OSError as e:
            return {"success": False, "error": str(e)}

    async def _file_write(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write content to file on local filesystem with security validation

        Creates parent directories automatically if they don't exist.

        Args:
            args: Dictionary with:
                - path (str): Target file path
                - content (str): Content to write
                - encoding (str, optional): Text encoding (default: "utf-8")

        Returns:
            Dictionary with:
                - success (bool): Whether write succeeded
                - path (str): Written file path
                - size (int): Written content length
                - error (str, optional): Error message if failed

        Security Features:
            ✅ Path traversal protection via _validate_path()
            ✅ Prevents writing to system directories
            ✅ Blocks dangerous file extensions (.exe, .dll, .sys, etc.)
            ✅ Content size limits (prevent disk exhaustion)
        """
        file_path = Path(args["path"])
        content = args["content"]
        encoding = args.get("encoding", "utf-8")

        # Security: Dangerous file extensions to block
        # pylint: disable=invalid-name
        BLOCKED_EXTENSIONS = {  # noqa: N806
            ".exe",
            ".dll",
            ".sys",
            ".bat",
            ".cmd",
            ".ps1",
            ".sh",
            ".bash",
            ".msi",
            ".app",
            ".com",
            ".scr",
            ".vbs",
            ".jar",
            ".pif",
        }

        try:
            # ✅ SEC-003 FIXED: Validate path before writing
            validated_path = self._validate_path(file_path)

            # Block dangerous file extensions
            if validated_path.suffix.lower() in BLOCKED_EXTENSIONS:
                return {
                    "success": False,
                    "error": (
                        f"Security error: Writing {validated_path.suffix} files is not allowed"
                    ),
                }

            # Content size limit (10MB max)
            # pylint: disable=invalid-name
            MAX_FILE_SIZE = 10 * 1024 * 1024  # noqa: N806 (10MB)
            if len(content.encode(encoding)) > MAX_FILE_SIZE:
                max_mb = MAX_FILE_SIZE / (1024 * 1024)
                return {
                    "success": False,
                    "error": (f"Security error: Content exceeds maximum size ({max_mb:.1f}MB)"),
                }

            # Ensure parent directories exist (run blocking ops in thread)
            parent_path = validated_path.parent
            validated_parent = self._validate_path(parent_path)
            await asyncio.to_thread(validated_parent.mkdir, parents=True, exist_ok=True)

            # Write content (run blocking operation in thread)
            await asyncio.to_thread(validated_path.write_text, content, encoding)
            return {
                "success": True,
                "path": str(validated_path),
                "size": len(content),
            }
        except UnicodeEncodeError as e:
            return {"success": False, "error": str(e)}
        except ValueError as e:
            # Security validation failed
            return {"success": False, "error": f"Security error: {str(e)}"}
        except OSError as e:
            return {"success": False, "error": str(e)}

    async def _system_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve NuSyQ ecosystem system information

        Gathers information about configurations, Ollama status, and
        available AI models. Supports filtered queries for specific components.

        Args:
            args: Dictionary with:
                - component (str, optional): Filter by component
                  Options: "all", "config", "ollama", "models"
                  Default: "all"

        Returns:
            Dictionary with:
                - success (bool): Whether query succeeded
                - info (dict): Requested system information
                  - configurations (dict): Config load status
                  - ollama_status (dict): Ollama service info
                  - available_models (list): Model definitions
                - error (str, optional): Error message if failed
        """
        component = args.get("component", "all")

        ai_config = self.config_manager.get_config("ai_ecosystem")

        def _get_config_status() -> Dict[str, bool]:
            return {
                name: bool(self.config_manager.get_config(name))
                for name in [
                    "manifest",
                    "knowledge_base",
                    "ai_ecosystem",
                    "tasks",
                ]
            }

        async def _get_ollama_status() -> Dict[str, Any]:
            # Prefer async HTTP check when possible, fallback to CLI
            try:
                if ai_config and "local_models" in ai_config and aiohttp is not None:
                    ollama_url = ai_config["local_models"]["ollama"]["base_url"]
                    timeout = aiohttp.ClientTimeout(total=5)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        tags_url = f"{ollama_url}/api/tags"
                        async with session.get(tags_url) as resp:
                            return {"running": resp.status == 200}
                # fallback
                result = await self._run_subprocess(["ollama", "list"])
                return {
                    "running": result.get("returncode") == 0,
                    "models": (
                        result.get("stdout", "").strip().split("\n")[1:]
                        if result.get("returncode") == 0
                        else []
                    ),
                }
            except aiohttp.ClientError as e:
                return {"running": False, "error": str(e)}
            except (asyncio.TimeoutError, OSError) as e:
                # Network timeouts, missing binary or OS-level errors
                return {"running": False, "error": str(e)}

        def _get_available_models() -> List[Dict[str, Any]]:
            if ai_config and "local_models" in ai_config:
                return ai_config["local_models"]["ollama"].get("models", [])
            return []

        def _get_health_status() -> Dict[str, Any]:
            """Get detailed system health information"""
            health = {}

            # Disk space check
            try:
                disk = psutil.disk_usage(".")
                health["disk"] = {
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent_used": disk.percent,
                    "status": (
                        "healthy"
                        if disk.percent < 80
                        else "warning"
                        if disk.percent < 90
                        else "critical"
                    ),
                }
            except Exception as e:
                health["disk"] = {"error": str(e)}

            # Memory check
            try:
                mem = psutil.virtual_memory()
                health["memory"] = {
                    "total_gb": mem.total / (1024**3),
                    "available_gb": mem.available / (1024**3),
                    "percent_used": mem.percent,
                    "status": (
                        "healthy"
                        if mem.percent < 80
                        else "warning"
                        if mem.percent < 90
                        else "critical"
                    ),
                }
            except Exception as e:
                health["memory"] = {"error": str(e)}

            # CPU check
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                health["cpu"] = {
                    "percent_used": cpu_percent,
                    "count": psutil.cpu_count(),
                    "status": (
                        "healthy"
                        if cpu_percent < 70
                        else "warning"
                        if cpu_percent < 90
                        else "critical"
                    ),
                }
            except Exception as e:
                health["cpu"] = {"error": str(e)}

            # Component health
            health["components"] = {
                "query_cache": ("available" if self.query_cache else "unavailable"),
                "performance_metrics": ("available" if self.metrics else "unavailable"),
                "agent_router": ("available" if self.agent_router else "unavailable"),
                "knowledge_base": (
                    "available"
                    if self.config_manager.get_config("knowledge_base")
                    else "unavailable"
                ),
            }

            # Overall status
            statuses = [
                health.get("disk", {}).get("status"),
                health.get("memory", {}).get("status"),
                health.get("cpu", {}).get("status"),
            ]
            if "critical" in statuses:
                health["overall_status"] = "critical"
            elif "warning" in statuses:
                health["overall_status"] = "warning"
            else:
                health["overall_status"] = "healthy"

            return health

        info: Dict[str, Any] = {}

        if component in ["all", "config"]:
            info["configurations"] = _get_config_status()

        if component in ["all", "ollama"]:
            info["ollama_status"] = await _get_ollama_status()

        if component in ["all", "models"]:
            info["available_models"] = _get_available_models()

        if component in ["all", "health"]:
            info["health"] = _get_health_status()

        return {"success": True, "info": info}

    async def _get_cache_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get query cache statistics

        Args:
            args: Dictionary with:
                - include_entries (bool): Include entry details

        Returns:
            Dictionary with cache statistics or error
        """
        if not self.query_cache:
            return {"success": False, "error": "Query cache not available"}

        include_entries = args.get("include_entries", False)

        stats = self.query_cache.get_stats()

        if include_entries:
            stats["entries"] = self.query_cache.get_entries_info()

        return {"success": True, "cache_stats": stats}

    async def _get_performance_metrics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics

        Args:
            args: Dictionary with:
                - time_window_minutes (int, optional): Limit to last N minutes
                - export_to_file (bool, optional): Export to JSON file

        Returns:
            Dictionary with performance metrics or error
        """
        if not self.metrics:
            return {
                "success": False,
                "error": "Performance metrics not available",
            }

        time_window = args.get("time_window_minutes")
        export = args.get("export_to_file", False)

        summary = self.metrics.get_summary(time_window)

        result = {"success": True, "metrics": summary}

        if export:
            filepath = self.metrics.export_summary(time_window_minutes=time_window)
            result["exported_to"] = str(filepath)

        return result

    async def _run_jupyter_cell(self, args: Dict[str, Any]) -> Dict[str, Any]:
        # Contains intentional try-except-raise for asyncio cancellation
        """
        Execute Python code in subprocess (Jupyter-style)

        WARNING: This is a simplified implementation that executes Python
        code directly via subprocess. Production systems should use proper
        Jupyter kernel communication (jupyter_client library) for:
        - Variable persistence across cells
        - Rich output handling (plots, HTML, etc.)
        - Kernel state management
        - Security sandboxing

        Args:
            args: Dictionary with:
                - code (str): Python code to execute
                - kernel (str, optional): Kernel type (currently ignored)

        Returns:
            Dictionary with:
                - success (bool): Whether execution completed without errors
                - stdout (str): Standard output
                - stderr (str): Standard error
                - return_code (int): Process exit code
                - error (str, optional): Exception message if failed

        Security Note:
            ⚠️ Executes arbitrary Python code without sandboxing.

            Production Isolation Strategies:
            1. Use Docker containers with resource limits
            2. Implement RestrictedPython for safer eval
            3. Use subprocess with limited permissions (setuid/setgid)
            4. Consider Pyodide for WASM-based sandboxing
            5. Add code analysis/scanning before execution

            For now: Basic subprocess isolation with timeout protection
        """
        code = args["code"]

        try:
            # Execute Python code in isolated subprocess
            result = await self._run_subprocess([sys.executable, "-c", code])
            return {
                "success": result.get("returncode") == 0,
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "return_code": result.get("returncode"),
            }
        except (asyncio.TimeoutError, OSError) as e:
            logger.exception("Jupyter cell execution failed: %s", e)
            return {"success": False, "error": str(e)}

    async def _run_subprocess(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        proc_timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run a subprocess command asynchronously

        Args:
            command: Command and arguments as list of strings
            env: Optional environment variables dictionary

        Returns:
            Dictionary with:
                - stdout (str): Standard output
                - stderr (str): Standard error
                - returncode (int): Process exit code
        """
        # Ensure command is a list
        if isinstance(command, str):
            command = command.split()

        try:
            if proc_timeout:
                # Use asyncio timeout context manager when a timeout is set
                try:
                    async with asyncio.timeout(proc_timeout):
                        process = await asyncio.create_subprocess_exec(
                            *command,
                            env=env,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        stdout, stderr = await process.communicate()
                except asyncio.TimeoutError:
                    logger.error("Subprocess timed out after %s seconds", proc_timeout)
                    return {
                        "stdout": "",
                        "stderr": "Timeout",
                        "returncode": -1,
                    }
            else:
                # No timeout - run normally
                process = await asyncio.create_subprocess_exec(
                    *command,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()

            return {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "returncode": process.returncode,
            }
        except asyncio.CancelledError:
            # Allow cancellations to propagate naturally
            raise
        except FileNotFoundError as e:
            logger.error("File not found: %s", e)
            return {"stdout": "", "stderr": str(e), "returncode": -1}
        except OSError as e:
            logger.error("Subprocess failed: %s", e)
            return {"stdout": "", "stderr": str(e), "returncode": -1}

    async def _ai_council_session(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convene the AI Council for governance and strategic decisions

        Executes a multi-agent AI Council session with 11 agents across
        Executive, Technical, and Advisory tiers.

        Args:
            args: Dictionary with:
                - session_type (str): Type of session
                  (STANDUP, EMERGENCY, etc.)
                - topic (str): Discussion topic
                - context (dict, optional): Additional context data

        Returns:
            Dictionary with:
                - success (bool): Whether council session completed
                - session_id (str): Unique session identifier
                - summary (str): Executive summary of decisions
                - council_output (dict): Full council discussion results
                - session_log_path (str): Path to detailed session log
                - error (str, optional): Error message if failed
        """
        session_type = args.get("session_type", "STANDUP")
        topic = args["topic"]

        logger.info("AI Council session requested: %s on '%s'", session_type, topic)

        try:
            # Execute AI Council via subprocess (async CLI call)
            cmd = [
                sys.executable,
                "config/ai_council.py",
                session_type.lower(),
                "--topic",
                topic,
            ]

            # AI Council coordination can take time:
            # - Advisory: 1-3min (quick consensus)
            # - Debate: 5-15min (multi-round discussion)
            # - Development: 10-30min+ (code generation with review)
            # Using 600s (10min) as reasonable safety limit
            result = await self._run_subprocess(cmd, proc_timeout=600)

            if result.get("returncode") == 0:
                # Parse output for session info
                stdout = result.get("stdout", "")

                # Extract session ID from output
                session_match = re.search(r"Session ID: (\w+)", stdout)
                session_id = session_match.group(1) if session_match else "unknown"

                return {
                    "success": True,
                    "session_id": session_id,
                    "session_type": session_type,
                    "topic": topic,
                    "summary": ("AI Council session completed. Check session log for details."),
                    "output": stdout[-500:],  # Last 500 chars
                    "session_log_path": (f"Logs/multi_agent_sessions/session_{session_id}.json"),
                }
            else:
                return {
                    "success": False,
                    "error": "AI Council execution failed",
                    "stderr": result.get("stderr", ""),
                }

        except (asyncio.TimeoutError, OSError) as e:
            logger.exception("AI Council session failed: %s", e)
            return {"success": False, "error": str(e)}

    async def _query_github_copilot(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a query to GitHub Copilot (bidirectional AI collaboration)

        This creates a query response that Claude Code can use to
        interact with GitHub Copilot. Since this is running inside
        the MCP server that Copilot uses, we create a response file
        that Copilot can monitor and respond to.

        Args:
            args: Dictionary with:
                - query (str): Question for GitHub Copilot
                - priority (str): Query priority level
                - context (dict, optional): Additional context

        Returns:
            Dictionary with:
                - success (bool): Whether query was submitted
                - query_id (str): Unique query identifier
                - status (str): Query status
                - message (str): Status message
                - response_path (str): Where Copilot should write response
                - error (str, optional): Error message if failed
        """
        query = args["query"]
        priority = args.get("priority", "normal")
        context = args.get("context", {})

        logger.info(
            "GitHub Copilot query from Claude Code: '%s...' (priority: %s)",
            query[:50],
            priority,
        )

        try:
            # Create query file for Copilot to monitor
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_id = f"claude_query_{timestamp}"

            query_dir = Path("Logs/claude_copilot_queries")
            query_dir.mkdir(parents=True, exist_ok=True)

            query_file = query_dir / f"{query_id}.json"

            query_data = {
                "query_id": query_id,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "priority": priority,
                "context": context,
                "from": "claude_code",
                "to": "github_copilot",
                "status": "pending",
            }

            # Write query file
            await asyncio.to_thread(query_file.write_text, json.dumps(query_data, indent=2))

            logger.info("Query file created: %s", query_file)

            # Return instructions for Claude Code
            return {
                "success": True,
                "query_id": query_id,
                "status": "submitted",
                "message": (
                    "Query submitted to GitHub Copilot. "
                    "Response will be available in the response "
                    "file when ready."
                ),
                "query_file": str(query_file),
                "response_file": str(query_dir / f"{query_id}_response.json"),
                "instructions": (
                    "GitHub Copilot will process this query and "
                    "write a response. You can check the response "
                    "file or use the file_read tool to retrieve "
                    "the answer when ready."
                ),
            }

        except (OSError, asyncio.TimeoutError) as e:
            logger.exception("Failed to create Copilot query: %s", e)
            return {"success": False, "error": str(e)}

    async def _parallel_agent_queries(
        self,
        agents: List[str],
        task: str,
        model_to_agent: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute queries in parallel across multiple Ollama agents

        Fallback mechanism when ConsensusOrchestrator is unavailable.
        Queries all agents concurrently and aggregates responses.

        Args:
            agents: List of agent/model names
            task: Task description

        Returns:
            Dictionary with aggregated results and agents used
        """
        logger.info("Running parallel queries on %d agents", len(agents))

        async def _timed_agent_query(agent: str) -> Dict[str, Any]:
            start_time = time.time()
            result = await self._ollama_query(
                {
                    "model": agent,
                    "prompt": (f"Task: {task}\n\nPlease provide analysis and recommendations."),
                    "max_tokens": 500,
                }
            )
            return {
                "agent": agent,
                "result": result,
                "duration": time.time() - start_time,
            }

        tasks = [_timed_agent_query(agent) for agent in agents]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error("Parallel queries failed: %s", e)
            return {
                "conclusion": str(e),
                "agents_used": agents,
                "response_count": 0,
            }

        # Aggregate responses
        conclusions = []
        for result in results:
            if not isinstance(result, dict):
                continue
            if result.get("result", {}).get("success"):
                conclusions.append(result["result"].get("response", ""))
            if self.metrics:
                model_name = result.get("agent", "unknown")
                agent_name = (
                    model_to_agent.get(model_name, model_name) if model_to_agent else model_name
                )
                self.metrics.record_agent(
                    agent_name=str(agent_name or "unknown"),
                    task_type="multi_agent_orchestration",
                    duration=result.get("duration", 0.0),
                    success=bool(result.get("result", {}).get("success")),
                )

        return {
            "conclusion": ("\n---\n".join(conclusions) if conclusions else "No responses received"),
            "agents_used": agents,
            "response_count": len(conclusions),
        }

    async def _multi_agent_orchestration(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate multi-agent collaboration with intelligent routing

        Orchestrates multi-agent collaboration using:
        1. Agent Router for intelligent task-to-agent routing
        2. Consensus Orchestrator for multi-model voting
        3. AI Council for strategy (optional)
        4. ChatDev for implementation (optional)

        Args:
            args: Dictionary with:
                - task (str): Task description
                - agents (list, optional): Agent names to include
                - mode (str): Conversation mode (default: PARALLEL_CONSENSUS)
                - include_ai_council (bool): Whether to convene council
                - implement_with_chatdev (bool): Whether to implement

        Returns:
            Dictionary with orchestration results
        """
        task = args["task"]
        agents = args.get("agents", [])
        mode = args.get("mode", "PARALLEL_CONSENSUS")
        task_type_value = args.get("task_type")
        complexity_value = args.get("complexity")
        include_council = args.get("include_ai_council", False)
        implement_chatdev = args.get("implement_with_chatdev", False)

        def _coerce_enum(enum_cls, value, default):
            if isinstance(value, enum_cls):
                return value
            if isinstance(value, str):
                try:
                    return enum_cls(value)
                except ValueError:
                    return default
            return default

        task_type = _coerce_enum(TaskType, task_type_value, TaskType.CODE_GENERATION)
        complexity = _coerce_enum(TaskComplexity, complexity_value, TaskComplexity.MODERATE)

        # Ensure types are correct for Task creation
        task_type_val: TaskType = (
            task_type if isinstance(task_type, TaskType) else TaskType.CODE_GENERATION
        )
        complexity_val: TaskComplexity = (
            complexity if isinstance(complexity, TaskComplexity) else TaskComplexity.MODERATE
        )

        logger.info(
            "Multi-agent orchestration: task='%s...', router=%s, mode=%s",
            task[:50],
            "enabled" if self.agent_router else "disabled",
            mode,
        )

        results = {
            "success": True,
            "task": task,
            "routing_decision": None,
            "phases": {},
            "agents_used": [],
        }

        try:
            # Phase 0: Intelligent agent selection via router
            if self.agent_router and not agents:
                logger.info("Phase 0: Routing task to optimal agents")
                try:
                    # Create task object for router
                    router_task = Task(
                        description=task,
                        task_type=task_type_val,
                        complexity=complexity_val,
                        requires_reasoning=True,
                    )

                    # Get routing decision
                    decision = self.agent_router.route_task(router_task)
                    results["routing_decision"] = {
                        "primary_agent": decision.agent.name,
                        "rationale": decision.rationale,
                        "estimated_cost": decision.estimated_cost,
                        "coordination": decision.coordination_pattern,
                    }

                    # Use router's agents
                    agents = [decision.agent.name]
                    agents.extend([a.name for a in decision.alternatives[:2]])

                    logger.info(
                        "Router: primary=%s, alternates=%s",
                        decision.agent.name,
                        [a.name for a in decision.alternatives[:2]],
                    )

                except Exception as route_err:
                    logger.warning("Agent routing failed: %s, using defaults", route_err)
                    agents = ["qwen2.5-coder:14b", "qwen2.5-coder:7b"]

            # Default agents if none selected
            if not agents:
                agents = ["qwen2.5-coder:14b", "qwen2.5-coder:7b"]

            results["agents_used"] = agents

            # Phase 1: AI Council (optional)
            if include_council:
                logger.info("Phase 1: Convening AI Council")
                council_result = await self._ai_council_session(
                    {"session_type": "ADVISORY", "topic": task}
                )
                results["phases"]["council_session"] = council_result

            # Phase 2: Multi-agent consensus
            logger.info("Phase 2: Multi-agent consensus (%s)", mode)

            if self.timeout_manager:
                timeout_rec = self.timeout_manager.get_timeout(
                    agent_type=TimeoutAgentType.MULTI_AGENT,
                    task_complexity=self._map_task_complexity(complexity),
                )
                os.environ.setdefault("OLLAMA_ADAPTIVE_TIMEOUT", "1")
                os.environ.setdefault(
                    "OLLAMA_MAX_TIMEOUT_SECONDS",
                    str(int(timeout_rec.timeout_seconds)),
                )

            consensus_models, model_to_agent = self._resolve_agent_models(agents)
            if not consensus_models:
                consensus_models = [DEFAULT_OLLAMA_MODEL]

            # Try consensus orchestrator first
            try:
                # pylint: disable=import-outside-toplevel
                from src.orchestration.consensus_orchestrator import (
                    ConsensusOrchestrator,
                )

                logger.info("Running consensus on %d agents", len(consensus_models))
                orchestrator = ConsensusOrchestrator(consensus_models)

                # Use async version if available
                if hasattr(orchestrator, "run_consensus_async"):
                    consensus_result = await orchestrator.run_consensus_async(
                        task, voting="weighted"
                    )
                else:
                    # Fallback to sync version (handles event loop internally)
                    consensus_result = orchestrator.run_consensus(task, voting="weighted")

                discussion_result = {
                    "conclusion": (consensus_result.consensus_response),
                    "agreement_rate": (consensus_result.agreement_rate),
                    "voting_method": (consensus_result.voting_method),
                    "agents_used": consensus_result.models,
                    "response_count": (len(consensus_result.responses)),
                    "total_duration": (consensus_result.total_duration_sec),
                }

                if self.metrics:
                    for response in getattr(consensus_result, "responses", []):
                        agent_name = (
                            model_to_agent.get(response.model, response.model)
                            if model_to_agent
                            else response.model
                        )
                        self.metrics.record_agent(
                            agent_name=str(agent_name or "unknown"),
                            task_type="multi_agent_orchestration",
                            duration=getattr(response, "duration_sec", 0.0),
                            success=bool(getattr(response, "success", False)),
                        )

                logger.info(
                    "Consensus: agreement=%.1f%%, duration=%.1fs",
                    consensus_result.agreement_rate * 100,
                    consensus_result.total_duration_sec,
                )

            except ImportError as import_err:
                logger.warning(
                    "ConsensusOrchestrator unavailable: %s, using parallel queries",
                    import_err,
                )
                discussion_result = await self._parallel_agent_queries(
                    consensus_models, task, model_to_agent
                )

            results["phases"]["agent_consensus"] = discussion_result
            results["resolved_models"] = consensus_models

            # Phase 3: ChatDev implementation (optional)
            if implement_chatdev:
                logger.info("Phase 3: ChatDev implementation")
                chatdev_result = await self._chatdev_create(
                    {
                        "task": task,
                        "model": (agents[0] if agents else DEFAULT_OLLAMA_MODEL),
                    }
                )
                results["phases"]["chatdev"] = chatdev_result

            # Final summary
            results["final_result"] = (
                f"Orchestration complete. "
                f"Phases: {len(results['phases'])}, "
                f"Agents: {len(results['agents_used'])}"
            )

            # Record routing decision for learning
            if (
                self.agent_router
                and results.get("routing_decision")
                and isinstance(results.get("routing_decision"), dict)
                and results.get("success", True)
            ):
                try:
                    # Calculate total duration
                    total_duration = (
                        results.get("phases", {})
                        .get("agent_consensus", {})
                        .get("total_duration", 0.0)
                    )

                    # Record task completion
                    self.agent_router.record_task_completion(
                        agent_name=results["routing_decision"].get("primary_agent", "unknown"),
                        task_type="multi_agent_orchestration",
                        success=True,
                        duration=total_duration,
                        task_description=task[:100],  # First 100 chars
                    )
                    logger.debug("Recorded routing decision for learning")
                except Exception as learn_err:
                    logger.warning("Failed to record routing decision: %s", learn_err)

            return results

        except (OSError, asyncio.TimeoutError) as e:
            logger.exception("Orchestration failed: %s", e)
            return {
                "success": False,
                "error": str(e),
                "task": task,
                "agents_attempted": agents,
            }

    async def _check_component_health(self) -> Dict[str, bool]:
        """
        Check health status of ecosystem components

        Performs lightweight health checks on:
        - Ollama service (HTTP API availability)
        - Configuration system (manifest loaded)

        Returns:
            Dictionary mapping component names to health status (bool)
        """
        health = {}

        # Check Ollama API availability
        try:
            ai_config = self.config_manager.get_config("ai_ecosystem")
            if ai_config and "local_models" in ai_config:
                ollama_url = ai_config["local_models"]["ollama"]["base_url"]
                try:
                    timeout = aiohttp.ClientTimeout(total=5)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(f"{ollama_url}/api/tags") as resp:
                            health["ollama"] = resp.status == 200
                except aiohttp.ClientError as e:
                    logger.error("Health check failed for Ollama: %s", e)
                    health["ollama"] = False
            else:
                # If no config, try CLI/assume not running
                result = await self._run_subprocess(["ollama", "list"])
                health["ollama"] = result.get("returncode") == 0
        except (
            aiohttp.ClientError,
            asyncio.TimeoutError,
            OSError,
        ) as e:
            logger.error("Health check failed for Ollama: %s", e)
            health["ollama"] = False

        # Check configuration system
        health["configurations"] = bool(self.config_manager.get_config("manifest"))

        return health


def create_app() -> FastAPI:
    """
    Application factory for NuSyQ MCP Server

    Creates and configures the FastAPI application instance.
    Used by ASGI servers (uvicorn, gunicorn) and testing frameworks.

    Returns:
        Configured FastAPI application instance
    """
    server = NuSyQMCPServer()
    return server.app


if __name__ == "__main__":
    # Main entry point for standalone server execution
    # Configuration:
    #   - Host: 0.0.0.0 (all network interfaces)
    #   - Port: 8765
    #   - Log Level: INFO
    # Usage:
    #   python main.py
    #   # Or with uvicorn directly:
    #   uvicorn main:app --host 0.0.0.0 --port 8765 --reload
    app = create_app()
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.getenv("MCP_SERVER_PORT", "8765")),
            log_level="debug",
        )
    except Exception as e:
        # Ensure any startup exception is logged with full traceback so
        # running the script in a terminal shows the root cause instead
        # of an immediate silent exit. Include the exception in the log
        # message for clarity.
        logger.exception("Unhandled exception while starting MCP server: %s", e)
        raise
