"""
NuSyQ MCP Server - Modular Architecture Implementation
======================================================

Purpose:
    Bridges Claude Code AI assistant with the local NuSyQ AI ecosystem using
    a modular, maintainable architecture with proper separation of concerns.

Architecture:
    - FastAPI-based REST server with async support
    - MCP-compliant endpoints for tool discovery and execution
    - Modular service layer with dependency injection
    - Enhanced security and validation
    - Comprehensive configuration management

Key Features:
    1. Ollama model querying (async HTTP client)
    2. File system operations (secure path validation)
    3. Jupyter code execution (sandboxed)
    4. ChatDev multi-agent framework integration
    5. System information and health monitoring

Security:
    - Input validation with Pydantic models
    - Path traversal protection
    - File size limits and content validation
    - Code safety checks for dangerous operations
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

# Import modular services
from src import (
    ChatDevRequest,
    ChatDevService,
    ConfigManager,
    FileOperationsService,
    FileReadRequest,
    FileWriteRequest,
    JupyterRequest,
    JupyterService,
    MCPRequest,
    MCPResponse,
    OllamaQueryRequest,
    OllamaService,
    SecurityValidator,
    SystemInfoRequest,
    SystemInfoService,
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nusyq-mcp-server")


class NuSyQMCPServer:
    """
    Main MCP Server for NuSyQ AI Ecosystem Integration

    Modular architecture with service-oriented design pattern.
    """

    def __init__(self):
        """Initialize MCP server with modular services"""
        # Initialize configuration manager
        self.config_manager = ConfigManager()

        # Initialize security validator
        security_config = self.config_manager.get_security_config()
        self.security = SecurityValidator(
            allowed_paths=security_config.allowed_paths,
        )

        # Initialize service layer — pass resolved configs, not the manager
        self.ollama_service = OllamaService(self.config_manager.get_ollama_config())
        self.chatdev_service = ChatDevService(self.config_manager)
        self.file_service = FileOperationsService(
            security_config.security_config if hasattr(security_config, "security_config") else None
        )
        self.system_service = SystemInfoService(self.config_manager)
        self.jupyter_service = JupyterService(self.config_manager)

        # Initialize FastAPI application
        self.app = FastAPI(
            title="NuSyQ MCP Server (Modular)",
            description="Model Context Protocol server for NuSyQ AI ecosystem",
            version="2.0.0",
        )

        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """Configure FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Register all FastAPI HTTP routes"""

        @self.app.get("/")
        async def root():
            """Server information endpoint"""
            return {
                "name": "NuSyQ MCP Server (Modular)",
                "version": "2.0.0",
                "status": "running",
                "architecture": "modular",
                "capabilities": [
                    "ollama_integration",
                    "chatdev_multi_agent",
                    "file_operations",
                    "jupyter_execution",
                    "system_monitoring",
                ],
            }

        @self.app.post("/mcp", response_model=MCPResponse)
        async def mcp_endpoint(request: MCPRequest):
            """Main Model Context Protocol endpoint"""
            try:
                if request.method == "tools/list":
                    tools = self._get_available_tools()
                    return MCPResponse(result={"tools": tools}, id=request.id)
                elif request.method == "tools/call":
                    tool_name = request.params.get("name")
                    arguments = request.params.get("arguments", {})
                    result = await self._execute_tool(tool_name, arguments)
                    return MCPResponse(result=result, id=request.id)
                else:
                    return MCPResponse(
                        error={
                            "code": -32601,
                            "message": f"Method not found: {request.method}",
                        },
                        id=request.id,
                    )
            except ValidationError as e:
                logger.error(f"Validation error: {e}")
                return MCPResponse(error={"code": -32602, "message": str(e)}, id=request.id)
            except Exception as e:
                logger.error(f"MCP request failed: {e}")
                return MCPResponse(error={"code": -32603, "message": str(e)}, id=request.id)

        @self.app.get("/health")
        async def health_check():
            """Component health check endpoint"""
            health_status = await self.system_service.check_component_health()
            return {
                "status": "healthy" if all(health_status.values()) else "degraded",
                "timestamp": datetime.now().isoformat(),
                "components": health_status,
            }

    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available MCP tools with schemas"""
        return [
            {
                "name": "ollama_query",
                "description": "Query Ollama models for code generation and analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "model": {"type": "string", "description": "Model name"},
                        "prompt": {"type": "string", "description": "Query prompt"},
                        "max_tokens": {"type": "integer", "default": 100},
                    },
                    "required": ["model", "prompt"],
                },
            },
            {
                "name": "chatdev_create",
                "description": "Create software using ChatDev multi-agent framework",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Development task"},
                        "model": {"type": "string", "default": "qwen2.5-coder:7b"},
                        "config": {"type": "string", "default": "NuSyQ_Ollama"},
                        "timeout": {"type": "integer", "default": 300},
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
                        "path": {"type": "string"},
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
                        "path": {"type": "string"},
                        "content": {"type": "string"},
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
                        "code": {"type": "string"},
                        "kernel": {"type": "string", "default": "python3"},
                    },
                    "required": ["code"],
                },
            },
        ]

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool using modular services"""
        try:
            if tool_name == "ollama_query":
                request = OllamaQueryRequest(**arguments)
                return await self.ollama_service.query(request)

            elif tool_name == "chatdev_create":
                request = ChatDevRequest(**arguments)
                return await self.chatdev_service.create_software(request)

            elif tool_name == "file_read":
                request = FileReadRequest(**arguments)
                return self.file_service.read_file(request)

            elif tool_name == "file_write":
                request = FileWriteRequest(**arguments)
                return self.file_service.write_file(request)

            elif tool_name == "system_info":
                request = SystemInfoRequest(**arguments)
                return await self.system_service.get_info(request)

            elif tool_name == "run_jupyter_cell":
                request = JupyterRequest(**arguments)
                return self.jupyter_service.execute_code(request)

            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except ValidationError as e:
            logger.error(f"Validation error for {tool_name}: {e}")
            return {"success": False, "error": f"Validation error: {str(e)}"}
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return {"success": False, "error": str(e)}

    async def start(self, host: str = "localhost", port: int = 8000):
        """Start the MCP server"""
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()


def main():
    """Main entry point"""
    logger.info("Starting NuSyQ MCP Server (Modular Architecture)")

    server = NuSyQMCPServer()

    # Get server config
    service_config = server.config_manager.get_service_config()

    logger.info(f"Server starting on {service_config.host}:{service_config.port}")

    # Run server
    asyncio.run(server.start(host=service_config.host, port=service_config.port))


if __name__ == "__main__":
    main()
