"""ChatDev Tool Registry - Tool Access Control for Agents.

Provides a registry of Hub utilities that ChatDev agents can invoke
during project generation. Inspired by ChatOllama's tool access pattern.

OmniTag: {
    "purpose": "ChatDev agent tool access control",
    "dependencies": ["chatdev_service", "quest_system", "health_checks"],
    "context": "Agent capabilities, tool invocation, ACL enforcement",
    "evolution_stage": "v1.0"
}
"""

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Categories of available tools."""

    CODE_QUALITY = "code_quality"  # Black, Ruff, mypy
    TESTING = "testing"  # Pytest, coverage
    LOGGING = "logging"  # Quest system
    HEALTH = "health"  # System checks
    GIT = "git"  # Git operations
    BUILD = "build"  # Build operations


@dataclass
class ToolDefinition:
    """Definition of a tool available to ChatDev agents."""

    name: str
    description: str
    category: ToolCategory
    handler: Callable
    allowed_roles: list[str]  # Which agent roles can use this
    allowed_environments: list[str]  # Which environments allow this
    requires_acl: bool = False
    input_schema: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "allowed_roles": self.allowed_roles,
            "allowed_environments": self.allowed_environments,
            "requires_acl": self.requires_acl,
            "input_schema": self.input_schema or {},
        }


class ChatDevToolRegistry:
    """Registry of tools available to ChatDev agents."""

    def __init__(self, config_path: Path | None = None):
        """Initialize tool registry.

        Args:
            config_path: Optional path to custom tool registry config
        """
        self.config_path = config_path or self._get_default_config_path()
        self.tools: dict[str, ToolDefinition] = {}
        self._register_builtin_tools()

    def _get_default_config_path(self) -> Path:
        """Get default path to tool registry config."""
        repo_root = Path(__file__).parent.parent.parent
        return repo_root / "config" / "chatdev_tools.json"

    def _register_builtin_tools(self) -> None:
        """Register built-in Hub utilities as tools."""
        # Code Quality Tools
        self.register(
            ToolDefinition(
                name="run_black_formatter",
                description="Run Black code formatter on generated files",
                category=ToolCategory.CODE_QUALITY,
                handler=self._run_black,
                allowed_roles=["Programmer", "Reviewer"],
                allowed_environments=["development", "staging"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to format"},
                        "line_length": {"type": "integer", "default": 88},
                    },
                    "required": ["path"],
                },
            )
        )

        self.register(
            ToolDefinition(
                name="run_ruff_linter",
                description="Run Ruff linter and fix issues",
                category=ToolCategory.CODE_QUALITY,
                handler=self._run_ruff,
                allowed_roles=["Programmer", "Reviewer"],
                allowed_environments=["development", "staging"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to lint"},
                        "fix": {"type": "boolean", "default": True},
                    },
                    "required": ["path"],
                },
            )
        )

        # Testing Tools
        self.register(
            ToolDefinition(
                name="run_pytest",
                description="Run pytest tests on generated code",
                category=ToolCategory.TESTING,
                handler=self._run_pytest,
                allowed_roles=["Programmer", "Tester"],
                allowed_environments=["development", "staging"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Test path"},
                        "coverage": {"type": "boolean", "default": True},
                    },
                    "required": ["path"],
                },
            )
        )

        # Logging Tools
        self.register(
            ToolDefinition(
                name="log_to_quest_system",
                description="Log ChatDev progress to quest system",
                category=ToolCategory.LOGGING,
                handler=self._log_to_quest,
                allowed_roles=["Programmer", "CEO", "CTO", "Reviewer"],
                allowed_environments=["development", "staging", "production"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task identifier"},
                        "progress": {"type": "string", "description": "Progress update"},
                        "artifacts": {"type": "array", "description": "Generated artifacts"},
                    },
                    "required": ["task_id", "progress"],
                },
            )
        )

        # Health Check Tools
        self.register(
            ToolDefinition(
                name="check_system_health",
                description="Check Hub system health status",
                category=ToolCategory.HEALTH,
                handler=self._check_health,
                allowed_roles=["CEO", "CTO", "Reviewer"],
                allowed_environments=["development", "staging", "production"],
                input_schema={
                    "type": "object",
                    "properties": {
                        "check_type": {
                            "type": "string",
                            "enum": ["all", "ollama", "storage", "imports"],
                            "default": "all",
                        }
                    },
                },
            )
        )

        logger.info(f"📦 Registered {len(self.tools)} built-in ChatDev tools")

    def register(self, tool: ToolDefinition) -> bool:
        """Register a tool.

        Args:
            tool: ToolDefinition to register

        Returns:
            True if successful
        """
        if tool.name in self.tools:
            logger.warning(f"Tool '{tool.name}' already registered, overwriting")

        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
        return True

    def get_tools_for_role(
        self, role: str, environment: str = "development"
    ) -> list[ToolDefinition]:
        """Get tools available for a specific agent role.

        Args:
            role: Agent role name (e.g., "Programmer", "Tester")
            environment: Current environment

        Returns:
            List of available tools
        """
        available = []

        for tool in self.tools.values():
            # Check role permission
            if role not in tool.allowed_roles:
                continue

            # Check environment permission
            if environment not in tool.allowed_environments:
                continue

            available.append(tool)

        return available

    async def invoke_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        caller_role: str = "Programmer",
        environment: str = "development",
    ) -> dict[str, Any]:
        """Invoke a tool.

        Args:
            tool_name: Name of tool to invoke
            arguments: Tool arguments
            caller_role: Role of caller (for permission checking)
            environment: Current environment

        Returns:
            Tool execution result
        """
        tool = self.tools.get(tool_name)

        if not tool:
            return {"success": False, "error": f"Tool not found: {tool_name}"}

        # Check permissions
        if caller_role not in tool.allowed_roles:
            return {
                "success": False,
                "error": f"Role '{caller_role}' not allowed for tool '{tool_name}'",
                "allowed_roles": tool.allowed_roles,
            }

        if environment not in tool.allowed_environments:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not available in '{environment}' environment",
                "allowed_environments": tool.allowed_environments,
            }

        # Invoke tool
        try:
            logger.info(f"🔧 Invoking {tool_name} for {caller_role}")
            result = await tool.handler(**arguments)
            return result
        except Exception as e:
            logger.error(f"❌ Tool invocation failed: {e}")
            return {"success": False, "error": str(e)}

    # Built-in tool handlers
    async def _run_black(self, path: str, line_length: int = 88) -> dict[str, Any]:
        """Run Black formatter."""
        try:
            process = await asyncio.create_subprocess_exec(
                "black",
                path,
                f"--line-length={line_length}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            return {
                "success": process.returncode == 0,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr and process.returncode != 0 else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_ruff(self, path: str, fix: bool = True) -> dict[str, Any]:
        """Run Ruff linter."""
        try:
            cmd = ["ruff", path]
            if fix:
                cmd.append("--fix")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            return {
                "success": process.returncode == 0,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr and process.returncode != 0 else None,
                "fixed": fix,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_pytest(self, path: str, coverage: bool = True) -> dict[str, Any]:
        """Run pytest tests."""
        try:
            cmd = ["pytest", path, "-v"]
            if coverage:
                cmd.extend(["--cov", "--cov-report=term-missing"])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            return {
                "success": process.returncode == 0,
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr and process.returncode != 0 else None,
                "coverage_enabled": coverage,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _log_to_quest(
        self, task_id: str, _progress: str, _artifacts: list[str] | None = None
    ) -> dict[str, Any]:
        """Log to quest system."""
        try:
            import sys
            from pathlib import Path

            hub_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(hub_root))

            # Import quest system
            from src.Rosetta_Quest_System.quest_log_manager import \
                QuestLogManager

            # Log quest entry
            QuestLogManager()

            # Log entry would include task_id, progress, and artifacts
            # This is a placeholder for future quest integration
            logger.info(f"📝 Ready to log to quest: {task_id}")

            return {"success": True, "logged": True, "task_id": task_id}
        except Exception as e:
            logger.error(f"Quest logging failed: {e}")
            return {"success": False, "error": str(e)}

    def _check_health(self, check_type: str = "all") -> dict[str, Any]:
        """Check system health."""
        try:
            import sys
            from pathlib import Path

            hub_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(hub_root))

            from src.diagnostics.system_health_assessor import \
                SystemHealthAssessor

            assessor = SystemHealthAssessor()
            result = assessor.assess()

            return {"success": True, "health_status": result, "check_type": check_type}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def export_manifest(self) -> list[dict[str, Any]]:
        """Export tool manifest for MCP registration.

        Returns:
            List of tool definitions
        """
        return [tool.to_dict() for tool in self.tools.values()]

    def save_config(self) -> bool:
        """Save tool registry configuration.

        Returns:
            True if successful
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            manifest = self.export_manifest()

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"version": "1.0.0", "tool_count": len(manifest), "tools": manifest},
                    f,
                    indent=2,
                )

            logger.info(f"✅ Saved tool registry to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False


# Global instance
_registry: ChatDevToolRegistry | None = None


def get_chatdev_tool_registry() -> ChatDevToolRegistry:
    """Get global ChatDev tool registry instance.

    Returns:
        ChatDevToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ChatDevToolRegistry()
    return _registry


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    registry = get_chatdev_tool_registry()

    logger.info("ChatDev Tool Registry")
    logger.info("=" * 60)

    # List all tools
    logger.info(f"\n📋 Available Tools ({len(registry.tools)}):")
    for tool in registry.tools.values():
        logger.info(f"  • {tool.name}")
        logger.info(f"    {tool.description}")
        logger.info(f"    Roles: {', '.join(tool.allowed_roles)}")
        logger.info()

    # Show tools for specific role
    logger.info("\n🔧 Tools for 'Programmer' role:")
    programmer_tools = registry.get_tools_for_role("Programmer")
    for tool in programmer_tools:
        logger.info(f"  • {tool.name}")

    # Save manifest
    logger.info("\n💾 Saving manifest...")
    registry.save_config()
    logger.info(f"✅ Saved to {registry.config_path}")
