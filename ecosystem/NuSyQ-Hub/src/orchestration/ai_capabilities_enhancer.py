#!/usr/bin/env python3
"""🚀 AI Capabilities Enhancer - Full System Utilization.

=========================================================

Ensures AI agents can fully utilize the NuSyQ-Hub ecosystem for:
- Development workflows (code generation, testing, debugging)
- Game development (Godot integration, asset management)
- Web applications (React, Node.js, full-stack)
- Package creation (PyPI, npm publishing)
- Quest-based development (task tracking, milestones)
- Docker deployment (containerization, orchestration)
- Multi-agent coordination (ChatDev, Ollama, Copilot)

OmniTag: [ai_capabilities, orchestration, multi_agent, enhancement]
MegaTag: AI⨳ENHANCEMENT⦾FULL→CAPABILITY
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import requests

from src.utils.intelligent_timeout_manager import \
    get_intelligent_timeout_manager

logger = logging.getLogger(__name__)


class DevelopmentDomain(Enum):
    """Development domains supported by the system."""

    CODE_DEVELOPMENT = "code_development"
    GAME_DEVELOPMENT = "game_development"
    WEB_APPLICATIONS = "web_applications"
    PACKAGE_CREATION = "package_creation"
    QUEST_WORKFLOWS = "quest_workflows"
    DOCKER_DEPLOYMENT = "docker_deployment"
    TESTING_QA = "testing_qa"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"


class AICapability(Enum):
    """Core AI agent capabilities."""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    DEPLOYMENT = "deployment"
    MULTI_AGENT_COORD = "multi_agent_coordination"
    CREATIVE_GENERATION = "creative_generation"


@dataclass
class WorkflowTemplate:
    """Template for AI-driven workflows."""

    name: str
    domain: DevelopmentDomain
    capabilities: list[AICapability]
    steps: list[dict[str, Any]]
    timeout_profile: str
    complexity: float = 1.0
    requires_services: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "domain": self.domain.value,
            "capabilities": [c.value for c in self.capabilities],
            "steps": self.steps,
            "timeout_profile": self.timeout_profile,
            "complexity": self.complexity,
            "requires_services": self.requires_services,
        }


class AICapabilitiesEnhancer:
    """Enhances AI agent capabilities across all system domains."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize capabilities enhancer."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.timeout_manager = get_intelligent_timeout_manager()
        self.workflows: dict[str, WorkflowTemplate] = {}
        self._initialize_workflows()
        logger.info("🚀 AI Capabilities Enhancer initialized")

    def _initialize_workflows(self) -> None:
        """Initialize built-in workflow templates."""
        # Code Development Workflows
        self.workflows["python_package_creation"] = WorkflowTemplate(
            name="Python Package Creation",
            domain=DevelopmentDomain.PACKAGE_CREATION,
            capabilities=[
                AICapability.CODE_GENERATION,
                AICapability.TESTING,
                AICapability.DOCUMENTATION,
            ],
            steps=[
                {
                    "action": "generate_structure",
                    "tool": "chatdev",
                    "timeout": "chatdev",
                },
                {"action": "write_code", "tool": "copilot", "timeout": "http_general"},
                {"action": "create_tests", "tool": "ollama", "timeout": "ollama"},
                {"action": "generate_docs", "tool": "ollama", "timeout": "ollama"},
                {"action": "build_package", "tool": "local", "timeout": "http_general"},
            ],
            timeout_profile="package_creation",
            complexity=1.5,
            requires_services=["ollama", "chatdev"],
        )

        self.workflows["web_app_fullstack"] = WorkflowTemplate(
            name="Full-Stack Web Application",
            domain=DevelopmentDomain.WEB_APPLICATIONS,
            capabilities=[
                AICapability.CODE_GENERATION,
                AICapability.ARCHITECTURE,
                AICapability.DEPLOYMENT,
            ],
            steps=[
                {
                    "action": "design_architecture",
                    "tool": "chatdev",
                    "timeout": "chatdev",
                },
                {"action": "create_backend", "tool": "chatdev", "timeout": "chatdev"},
                {"action": "create_frontend", "tool": "chatdev", "timeout": "chatdev"},
                {
                    "action": "setup_database",
                    "tool": "local",
                    "timeout": "http_general",
                },
                {
                    "action": "create_docker",
                    "tool": "copilot",
                    "timeout": "http_general",
                },
                {"action": "deploy", "tool": "local", "timeout": "docker"},
            ],
            timeout_profile="web_development",
            complexity=2.0,
            requires_services=["chatdev", "docker"],
        )

        self.workflows["game_development_godot"] = WorkflowTemplate(
            name="Godot Game Development",
            domain=DevelopmentDomain.GAME_DEVELOPMENT,
            capabilities=[
                AICapability.CODE_GENERATION,
                AICapability.CREATIVE_GENERATION,
                AICapability.ARCHITECTURE,
            ],
            steps=[
                {"action": "design_game", "tool": "chatdev", "timeout": "chatdev"},
                {"action": "create_gdscript", "tool": "ollama", "timeout": "ollama"},
                {"action": "design_levels", "tool": "ollama", "timeout": "ollama"},
                {"action": "create_assets", "tool": "chatdev", "timeout": "chatdev"},
                {
                    "action": "integrate_systems",
                    "tool": "copilot",
                    "timeout": "http_general",
                },
            ],
            timeout_profile="game_development",
            complexity=2.0,
            requires_services=["ollama", "chatdev"],
        )

        self.workflows["quest_driven_development"] = WorkflowTemplate(
            name="Quest-Based Development",
            domain=DevelopmentDomain.QUEST_WORKFLOWS,
            capabilities=[
                AICapability.MULTI_AGENT_COORD,
                AICapability.CODE_GENERATION,
                AICapability.TESTING,
            ],
            steps=[
                {
                    "action": "load_quest",
                    "tool": "quest_system",
                    "timeout": "http_general",
                },
                {
                    "action": "analyze_requirements",
                    "tool": "ollama",
                    "timeout": "ollama",
                },
                {
                    "action": "generate_solution",
                    "tool": "chatdev",
                    "timeout": "chatdev",
                },
                {
                    "action": "implement_code",
                    "tool": "copilot",
                    "timeout": "http_general",
                },
                {"action": "test_solution", "tool": "local", "timeout": "http_general"},
                {
                    "action": "update_quest",
                    "tool": "quest_system",
                    "timeout": "http_general",
                },
            ],
            timeout_profile="quest_workflow",
            complexity=1.5,
            requires_services=["quest_system", "ollama", "chatdev"],
        )

        self.workflows["docker_deployment"] = WorkflowTemplate(
            name="Docker Multi-Service Deployment",
            domain=DevelopmentDomain.DOCKER_DEPLOYMENT,
            capabilities=[
                AICapability.DEPLOYMENT,
                AICapability.ARCHITECTURE,
                AICapability.DOCUMENTATION,
            ],
            steps=[
                {"action": "analyze_services", "tool": "ollama", "timeout": "ollama"},
                {
                    "action": "create_dockerfiles",
                    "tool": "copilot",
                    "timeout": "http_general",
                },
                {
                    "action": "create_compose",
                    "tool": "copilot",
                    "timeout": "http_general",
                },
                {"action": "setup_networking", "tool": "ollama", "timeout": "ollama"},
                {"action": "build_images", "tool": "docker", "timeout": "docker"},
                {"action": "deploy_stack", "tool": "docker", "timeout": "docker"},
            ],
            timeout_profile="docker_deployment",
            complexity=1.8,
            requires_services=["docker", "ollama"],
        )

        logger.info(f"📚 Loaded {len(self.workflows)} workflow templates")

    def get_workflow(self, workflow_name: str) -> WorkflowTemplate | None:
        """Get a workflow template by name."""
        return self.workflows.get(workflow_name)

    def list_workflows(
        self,
        domain: DevelopmentDomain | None = None,
        capability: AICapability | None = None,
    ) -> list[WorkflowTemplate]:
        """List available workflows, optionally filtered."""
        workflows = list(self.workflows.values())

        if domain:
            workflows = [w for w in workflows if w.domain == domain]

        if capability:
            workflows = [w for w in workflows if capability in w.capabilities]

        return workflows

    def get_domain_capabilities(self) -> dict[str, list[str]]:
        """Get capabilities organized by domain."""
        result: dict[str, list[str]] = {}

        for workflow in self.workflows.values():
            domain = workflow.domain.value
            if domain not in result:
                result[domain] = []

            for cap in workflow.capabilities:
                if cap.value not in result[domain]:
                    result[domain].append(cap.value)

        return result

    def get_service_requirements(self) -> dict[str, list[str]]:
        """Get required services for each workflow."""
        return {name: workflow.requires_services for name, workflow in self.workflows.items()}

    # ------------------------------------------------------------------
    # Capability discovery/validation and recommendations (test-facing)
    # ------------------------------------------------------------------
    def discover_capabilities(self) -> dict[str, Any]:
        """Discover available AI backends and features.

        Returns a dict keyed by backend name with availability flags.
        """
        backends = {
            "ollama": self.check_backend_status("ollama"),
            "chatdev": self.check_backend_status("chatdev"),
        }
        return {k: {"available": v} for k, v in backends.items()}

    def validate_capability(self, capability: str) -> bool:
        """Validate that a capability is recognized by the system."""
        try:
            return capability in {c.value for c in AICapability}
        except Exception:
            return False

    def get_recommendations(self) -> list[str]:
        """Return high-level capability enhancement recommendations."""
        recs = [
            "Increase unit test coverage to 70%+ for robustness",
            "Ensure Ollama models are pulled and running for code gen",
            "Enable ChatDev workflows for multi-agent development",
        ]
        return recs

    def check_backend_status(self, name: str) -> bool | str:
        """Check whether a backend is reachable.

        Returns True/False when determinable, otherwise 'unknown'.
        """
        try:
            if name.lower() == "ollama":
                url = "http://localhost:11434/api/tags"
                resp = requests.get(url, timeout=1.0)
                return bool(resp.status_code and resp.status_code < 500)
            if name.lower() == "chatdev":
                # ChatDev runtime not always online during tests
                return "unknown"
        except Exception:
            return False
        return "unknown"

    def validate_workflow_readiness(
        self,
        workflow_name: str,
        available_services: list[str],
    ) -> tuple[bool, list[str]]:
        """Check if all required services are available for a workflow.

        Returns:
            (is_ready, missing_services)
        """
        workflow = self.get_workflow(workflow_name)
        if not workflow:
            return False, [f"Unknown workflow: {workflow_name}"]

        missing = [svc for svc in workflow.requires_services if svc not in available_services]

        return len(missing) == 0, missing

    def calculate_workflow_timeout(
        self,
        workflow_name: str,
        complexity_override: float | None = None,
        priority: str = "normal",
    ) -> float:
        """Calculate adaptive timeout for a workflow."""
        workflow = self.get_workflow(workflow_name)
        if not workflow:
            return self.timeout_manager.get_timeout("http_general")

        complexity = complexity_override or workflow.complexity
        total_timeout = 0.0

        # Sum timeouts for each step
        for step in workflow.steps:
            timeout_key = step.get("timeout", "http_general")
            step_timeout = self.timeout_manager.get_timeout(
                timeout_key,
                complexity=complexity,
                priority=priority,
            )
            total_timeout += step_timeout

        return total_timeout

    def export_capabilities(self, output_path: Path | None = None) -> dict[str, Any]:
        """Export full capabilities map for AI agents."""
        output_path = output_path or self.project_root / "docs" / "AI_CAPABILITIES_MAP.json"

        capabilities_map = {
            "version": "1.0.0",
            "domains": {
                domain.value: {
                    "description": domain.name.replace("_", " ").title(),
                    "workflows": [
                        w.to_dict() for w in self.workflows.values() if w.domain == domain
                    ],
                }
                for domain in DevelopmentDomain
            },
            "capabilities": {
                cap.value: {
                    "description": cap.name.replace("_", " ").title(),
                    "workflows": [
                        name for name, w in self.workflows.items() if cap in w.capabilities
                    ],
                }
                for cap in AICapability
            },
            "service_requirements": self.get_service_requirements(),
        }

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(capabilities_map, f, indent=2)

        logger.info(f"📄 Capabilities map exported to: {output_path}")
        return capabilities_map

    def generate_agent_workflow_guide(
        self,
        output_path: Path | None = None,
    ) -> str:
        """Generate markdown guide for AI agents."""
        output_path = output_path or self.project_root / "docs" / "AI_WORKFLOW_GUIDE.md"

        guide_lines = [
            "# 🤖 AI Agent Workflow Guide",
            "",
            "This guide provides comprehensive workflow templates for AI agents to",
            "fully utilize the NuSyQ-Hub ecosystem.",
            "",
            "## 🎯 Available Workflows",
            "",
        ]

        # Group by domain
        for domain in DevelopmentDomain:
            domain_workflows = [w for w in self.workflows.values() if w.domain == domain]

            if not domain_workflows:
                continue

            guide_lines.append(f"### {domain.name.replace('_', ' ').title()}")
            guide_lines.append("")

            for workflow in domain_workflows:
                guide_lines.extend(
                    [
                        f"#### {workflow.name}",
                        "",
                        f"**Complexity:** {workflow.complexity}x",
                        f"**Required Services:** {', '.join(workflow.requires_services)}",
                        "",
                        "**Capabilities:**",
                    ]
                )

                for cap in workflow.capabilities:
                    guide_lines.append(f"- {cap.value}")

                guide_lines.extend(["", "**Steps:**", ""])

                for i, step in enumerate(workflow.steps, 1):
                    action = step["action"].replace("_", " ").title()
                    tool = step["tool"]
                    guide_lines.append(f"{i}. **{action}** (via {tool})")

                # Calculate timeout
                timeout = self.calculate_workflow_timeout(workflow.name)
                guide_lines.extend(
                    [
                        "",
                        f"**Estimated Time:** {timeout:.1f}s (adaptive)",
                        "",
                        "---",
                        "",
                    ]
                )

        # Add usage examples
        guide_lines.extend(
            [
                "## 💡 Usage Examples",
                "",
                "### Python Package Creation",
                "",
                "```python",
                "from src.orchestration.ai_capabilities_enhancer import AICapabilitiesEnhancer",
                "",
                "enhancer = AICapabilitiesEnhancer()",
                "workflow = enhancer.get_workflow('python_package_creation')",
                "timeout = enhancer.calculate_workflow_timeout('python_package_creation', priority='high')",
                "",
                "# Check readiness",
                "ready, missing = enhancer.validate_workflow_readiness(",
                "    'python_package_creation',",
                "    available_services=['ollama', 'chatdev', 'docker']",
                ")",
                "```",
                "",
                "### Web Application Development",
                "",
                "```python",
                "workflow = enhancer.get_workflow('web_app_fullstack')",
                "# Execute with ChatDev for multi-agent coordination",
                "```",
                "",
            ]
        )

        guide_content = "\n".join(guide_lines)

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(guide_content)

        logger.info(f"📄 Workflow guide written to: {output_path}")
        return guide_content


def main() -> None:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    enhancer = AICapabilitiesEnhancer()

    # Export capabilities
    enhancer.export_capabilities()

    # Generate workflow guide
    enhancer.generate_agent_workflow_guide()

    # Display summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ AI CAPABILITIES ENHANCEMENT COMPLETE")
    logger.info("=" * 80)
    logger.info(f"\n📚 Total Workflows: {len(enhancer.workflows)}")
    logger.info(f"🎯 Domains: {len(DevelopmentDomain)}")
    logger.info(f"⚡ Capabilities: {len(AICapability)}")

    logger.info("\n📊 Workflows by Domain:")
    for domain in DevelopmentDomain:
        count = len([w for w in enhancer.workflows.values() if w.domain == domain])
        if count > 0:
            logger.info(f"  - {domain.value}: {count}")

    logger.info("\n📄 Documentation Generated:")
    logger.info("  - docs/AI_CAPABILITIES_MAP.json")
    logger.info("  - docs/AI_WORKFLOW_GUIDE.md")
    logger.info()


if __name__ == "__main__":
    main()
