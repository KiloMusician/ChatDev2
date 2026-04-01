"""Claude Orchestrator Bridge - Claude API Integration.

Provides integration with Claude (Anthropic) API through the orchestration hub.

Canonical implementation: src/agents/agent_orchestration_hub.py
"""

from pathlib import Path
from typing import Any

from src.agents.agent_orchestration_hub import get_agent_orchestration_hub
from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


class ClaudeOrchestrator:
    """Interface to Claude AI through the orchestration hub.

    This class provides Claude-specific methods while routing through
    the AgentOrchestrationHub for unified coordination.
    """

    def __init__(self, root_path: Path | None = None):
        """Initialize Claude orchestrator.

        Args:
            root_path: Repository root path
        """
        self.root_path = root_path or Path.cwd()
        self._hub = get_agent_orchestration_hub(root_path=self.root_path)

        logger.info("ClaudeOrchestrator initialized")

    async def analyze_code(
        self,
        code_path: str | Path,
        analysis_type: str = "comprehensive",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Analyze code using Claude.

        Args:
            code_path: Path to code file
            analysis_type: Type of analysis (comprehensive, security, performance)
            context: Additional context

        Returns:
            Analysis results
        """
        context = context or {}
        context.update(
            {
                "code_path": str(code_path),
                "analysis_type": analysis_type,
                "model": "claude",
            }
        )

        result = await self._hub.route_task(
            task_type="code_analysis",
            description=f"{analysis_type} code analysis of {code_path}",
            context=context,
            target_service="claude",
        )

        return result

    async def generate_code(
        self,
        specification: str,
        language: str = "python",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate code using Claude.

        Args:
            specification: What to generate
            language: Programming language
            context: Additional context

        Returns:
            Generated code result
        """
        context = context or {}
        context.update({"language": language, "model": "claude"})

        result = await self._hub.route_task(
            task_type="code_generation",
            description=specification,
            context=context,
            target_service="claude",
        )

        return result

    async def chat(
        self, message: str, conversation_history: list[dict[str, str]] | None = None
    ) -> dict[str, Any]:
        """Have a conversation with Claude.

        Args:
            message: User message
            conversation_history: Previous messages

        Returns:
            Claude's response
        """
        context = {
            "conversation_history": conversation_history or [],
            "model": "claude",
        }

        result = await self._hub.route_task(
            task_type="conversation",
            description=message,
            context=context,
            target_service="claude",
        )

        return result

    async def orchestrate(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
        systems: list[str] | None = None,
        mode: str = "consensus",
    ) -> dict[str, Any]:
        """Route a task through the Claude orchestration layer."""
        return await self._hub.route_to_claude(
            task_description=task_description,
            context=context,
            systems=systems,
            mode=mode,
        )


__all__ = ["ClaudeOrchestrator"]
