"""ChatDev Orchestrator Bridge - Unified ChatDev Access.

Provides a simplified interface to ChatDev multi-agent development through
the AgentOrchestrationHub.

Canonical implementation: src/agents/agent_orchestration_hub.py
"""

from pathlib import Path
from typing import Any

from src.agents.agent_orchestration_hub import get_agent_orchestration_hub
from src.LOGGING.modular_logging_system import get_logger

logger = get_logger(__name__)


class ChatDevDevelopmentOrchestrator:
    """Simplified interface to ChatDev through the orchestration hub.

    This class provides an easy-to-use interface for ChatDev multi-agent
    development while delegating all work to the AgentOrchestrationHub.
    """

    def __init__(self, project_root: str | Path | None = None):
        """Initialize ChatDev orchestrator.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._hub = get_agent_orchestration_hub(root_path=self.project_root)

        logger.info(
            "ChatDevDevelopmentOrchestrator initialized",
            extra={"project_root": str(self.project_root)},
        )

    async def develop_software(
        self,
        project_description: str,
        requirements: list[str] | None = None,
        output_dir: str | Path | None = None,
        team_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Develop software using ChatDev multi-agent system.

        Args:
            project_description: High-level project description
            requirements: Specific requirements list
            output_dir: Where to save generated code
            team_config: Custom team configuration

        Returns:
            Development result with code artifacts
        """
        context = {}
        if output_dir:
            context["output_dir"] = str(output_dir)

        result = await self._hub.route_to_chatdev(
            project_description=project_description,
            requirements=requirements,
            team_composition=team_config,
            context=context,
        )

        return result

    async def review_code(
        self, code_path: str | Path, focus_areas: list[str] | None = None
    ) -> dict[str, Any]:
        """Review code using ChatDev's multi-agent review process.

        Args:
            code_path: Path to code to review
            focus_areas: Specific areas to focus on

        Returns:
            Review results with suggestions
        """
        context = {
            "code_path": str(code_path),
            "focus_areas": focus_areas or ["quality", "security", "performance"],
        }

        result = await self._hub.route_task(
            task_type="code_review",
            description=f"Multi-agent code review of {code_path}",
            context=context,
        )

        return result


__all__ = ["ChatDevDevelopmentOrchestrator"]
