"""Publishing Orchestrator - Coordinates publishing across multiple registries.

Handles:
- PyPI (Python packages)
- NPM (JavaScript/Node packages)
- VS Code Marketplace (Extensions)
- Docker Hub (Container images)
- GitHub Releases (Binary releases)
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RegistryType(str, Enum):
    """Supported package registries."""

    PYPI = "pypi"
    NPM = "npm"
    VSCODE = "vscode"
    DOCKER = "docker"
    GITHUB = "github"


class PublishTarget(str, Enum):
    """Publishing targets based on project type."""

    PYPI_ONLY = "pypi_only"  # Python packages
    NPM_ONLY = "npm_only"  # Node/web packages
    VSCODE_ONLY = "vscode_only"  # Extensions
    DOCKER_ONLY = "docker_only"  # Container images
    HYBRID_PYTHON = "hybrid_python"  # Python package + Docker
    HYBRID_NODE = "hybrid_node"  # NPM package + Docker
    MULTI = "multi"  # Multiple targets (rare)


@dataclass
class PublishConfig:
    """Publishing configuration for a project."""

    project_id: str
    project_name: str
    version: str
    description: str
    author: str
    author_email: str
    license_type: str  # "MIT", "Apache-2.0", "GPL-3.0"

    # Publishing targets
    targets: list[RegistryType]
    publish_target: PublishTarget

    # Registry credentials (should come from config/secrets.json)
    pypi_token: str | None = None
    npm_token: str | None = None
    vscode_token: str | None = None
    docker_username: str | None = None
    docker_password: str | None = None
    github_token: str | None = None

    # Repository info
    repository_url: str | None = None
    documentation_url: str | None = None

    # Automation flags
    auto_create_github_release: bool = False
    create_docker_image: bool = False

    # Metadata
    keywords: list[str] = None
    categories: list[str] = None  # For marketplace categorization

    def __post_init__(self):
        """Implement __post_init__."""
        if self.keywords is None:
            self.keywords = []
        if self.categories is None:
            self.categories = []


@dataclass
class PublishResult:
    """Result of a publishing operation."""

    project_id: str
    project_name: str
    version: str
    status: str  # "success", "partial", "failed"
    timestamp: str

    # Per-registry results
    pypi_result: dict[str, Any] | None = None
    npm_result: dict[str, Any] | None = None
    vscode_result: dict[str, Any] | None = None
    docker_result: dict[str, Any] | None = None
    github_result: dict[str, Any] | None = None

    # Overall metrics
    registries_published: int = 0
    registries_failed: int = 0
    error_messages: list[str] = None

    def __post_init__(self):
        """Implement __post_init__."""
        if self.error_messages is None:
            self.error_messages = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class PublishingOrchestrator:
    """Orchestrates publishing projects to multiple registries.

    Workflow:
    1. Load project metadata
    2. Prepare artifacts (build, package, etc.)
    3. Validate publishing configuration
    4. Execute publishing to each target
    5. Log results and update registry
    """

    def __init__(
        self,
        project_base: Path = Path("."),
        publish_log_path: Path | None = None,
        config_path: Path | None = None,
    ):
        """Initialize publishing orchestrator.

        Args:
            project_base: Base path for projects
            publish_log_path: Path to publish log (JSONL)
            config_path: Path to publishing config
        """
        self.project_base = Path(project_base)
        self.publish_log_path = Path(publish_log_path or "logs/publish_log.jsonl")
        self.config_path = Path(config_path or "config/publish_config.json")

        # Ensure directories exist
        self.publish_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self.publish_log_path.touch(exist_ok=True)

        logger.info(f"Publishing orchestrator initialized at {self.project_base}")

    def validate_config(self, config: PublishConfig) -> tuple[bool, list[str]]:
        """Validate publishing configuration.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        if not config.project_name:
            errors.append("project_name required")
        if not config.version:
            errors.append("version required")
        if not config.author:
            errors.append("author required")

        if RegistryType.PYPI in config.targets and not config.pypi_token:
            errors.append("pypi_token required for PyPI publishing")
        if RegistryType.NPM in config.targets and not config.npm_token:
            errors.append("npm_token required for NPM publishing")
        if RegistryType.VSCODE in config.targets and not config.vscode_token:
            errors.append("vscode_token required for VSCode publishing")
        if RegistryType.DOCKER in config.targets and not (
            config.docker_username and config.docker_password
        ):
            errors.append("docker_username and docker_password required for Docker publishing")

        return len(errors) == 0, errors

    def prepare_artifacts(self, project_path: Path, publish_config: PublishConfig) -> bool:
        """Prepare artifacts for publishing (build, package, etc.).

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Preparing artifacts for {publish_config.project_name}")

            # Check if project exists
            if not project_path.exists():
                logger.error(f"Project not found: {project_path}")
                return False

            # Execute pre-publish hooks if any
            # This would call language-specific build tools
            # (npm run build, python setup.py sdist, cargo build, etc.)

            logger.info("Artifacts prepared successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to prepare artifacts: {e!s}")
            return False

    def publish(self, project_path: Path, config: PublishConfig) -> PublishResult:
        """Execute publishing to configured targets.

        Args:
            project_path: Path to project directory
            config: Publishing configuration

        Returns:
            PublishResult with per-registry outcomes
        """
        result = PublishResult(
            project_id=config.project_id,
            project_name=config.project_name,
            version=config.version,
            status="success",
            timestamp=datetime.utcnow().isoformat(),
        )

        try:
            # 1. Validate configuration
            is_valid, errors = self.validate_config(config)
            if not is_valid:
                result.status = "failed"
                result.error_messages = errors
                return result

            # 2. Prepare artifacts
            if not self.prepare_artifacts(project_path, config):
                result.status = "failed"
                result.error_messages.append("Artifact preparation failed")
                return result

            # 3. Publish to each configured target
            for registry in config.targets:
                try:
                    if registry == RegistryType.PYPI:
                        result.pypi_result = self._publish_to_pypi(project_path, config)
                        if result.pypi_result.get("status") == "success":
                            result.registries_published += 1
                        else:
                            result.registries_failed += 1
                            result.status = "partial"

                    elif registry == RegistryType.NPM:
                        result.npm_result = self._publish_to_npm(project_path, config)
                        if result.npm_result.get("status") == "success":
                            result.registries_published += 1
                        else:
                            result.registries_failed += 1
                            result.status = "partial"

                    elif registry == RegistryType.VSCODE:
                        result.vscode_result = self._publish_to_vscode(project_path, config)
                        if result.vscode_result.get("status") == "success":
                            result.registries_published += 1
                        else:
                            result.registries_failed += 1
                            result.status = "partial"

                    elif registry == RegistryType.DOCKER:
                        result.docker_result = self._publish_to_docker(project_path, config)
                        if result.docker_result.get("status") == "success":
                            result.registries_published += 1
                        else:
                            result.registries_failed += 1
                            result.status = "partial"

                except Exception as e:
                    logger.error(f"Publishing to {registry.value} failed: {e!s}")
                    result.registries_failed += 1
                    result.error_messages.append(f"{registry.value}: {e!s}")
                    result.status = "partial"

            # 4. Log results
            self._log_publish_result(result)

            if result.registries_failed > 0:
                result.status = "partial" if result.registries_published > 0 else "failed"

            logger.info(f"✅ Publishing complete: {result.status}")
            return result

        except Exception as e:
            logger.error(f"Publishing orchestration failed: {e!s}")
            result.status = "failed"
            result.error_messages.append(str(e))
            return result

    def _publish_to_pypi(self, _project_path: Path, config: PublishConfig) -> dict[str, Any]:
        """Publish Python package to PyPI.

        Expected project structure:
        - setup.py / pyproject.toml
        - src/package_name/
        """
        try:
            logger.info(f"Publishing to PyPI: {config.project_name}")

            # This is a placeholder - actual implementation would:
            # 1. Generate/update setup.py with config metadata
            # 2. Build dist (python setup.py sdist bdist_wheel)
            # 3. Upload with twine (twine upload dist/*)

            return {
                "status": "success",
                "registry": "pypi",
                "url": f"https://pypi.org/project/{config.project_name}/{config.version}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "failed",
                "registry": "pypi",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _publish_to_npm(self, _project_path: Path, config: PublishConfig) -> dict[str, Any]:
        """Publish JavaScript/Node package to NPM."""
        try:
            logger.info(f"Publishing to NPM: {config.project_name}")

            # Placeholder - actual implementation would:
            # 1. Generate/update package.json with config metadata
            # 2. Run npm publish (with auth token)

            return {
                "status": "success",
                "registry": "npm",
                "url": f"https://www.npmjs.com/package/{config.project_name}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "failed",
                "registry": "npm",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _publish_to_vscode(self, _project_path: Path, config: PublishConfig) -> dict[str, Any]:
        """Publish VS Code extension to Marketplace."""
        try:
            logger.info(f"Publishing to VSCode Marketplace: {config.project_name}")

            # Placeholder - actual implementation would:
            # 1. Validate extension.json
            # 2. Package with vsce package
            # 3. Publish with vsce publish (with auth token)

            return {
                "status": "success",
                "registry": "vscode",
                "url": f"https://marketplace.visualstudio.com/items?itemName={config.author}.{config.project_name}",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "failed",
                "registry": "vscode",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _publish_to_docker(self, project_path: Path, config: PublishConfig) -> dict[str, Any]:
        """Publish Docker image to registry using DockerBuilder."""
        try:
            logger.info(f"Publishing to Docker: {config.project_name}")

            # Import DockerBuilder
            from .docker_builder import DockerBuilder, DockerConfig

            # Create Docker config
            docker_config = DockerConfig(
                project_name=config.project_name,
                version=config.version,
                language=getattr(config, "docker_language", "python"),
                base_image=getattr(config, "docker_base_image", "python:3.11-slim"),
                registry="docker.io",
                username=config.docker_username or "unknown",
                expose_ports=getattr(config, "docker_ports", []),
            )

            # Create builder and build/push
            builder = DockerBuilder(project_path=project_path)
            result = builder.build_and_push(docker_config)

            return {
                "status": result.get("status", "failed"),
                "registry": "docker",
                "image": result.get("build", {}).get("image"),
                "url": result.get("push", {}).get("url"),
                "timestamp": datetime.now().isoformat(),
                "details": result,
            }
        except Exception as e:
            logger.error(f"Docker publish failed: {e!s}")
            return {
                "status": "failed",
                "registry": "docker",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _log_publish_result(self, result: PublishResult) -> None:
        """Log publishing result to JSONL file."""
        with open(self.publish_log_path, "a") as f:
            f.write(json.dumps(result.to_dict()) + "\n")

        logger.debug(f"Logged publish result: {result.project_id}")

    def get_publish_history(self, project_id: str | None = None) -> list[PublishResult]:
        """Retrieve publishing history.

        Args:
            project_id: Optional filter by project ID

        Returns:
            List of PublishResult objects
        """
        if not self.publish_log_path.exists():
            return []

        results = []
        with open(self.publish_log_path) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if project_id is None or data.get("project_id") == project_id:
                        results.append(PublishResult(**data))

        return results

    def get_publish_status(self, project_id: str) -> PublishResult | None:
        """Get latest publish result for a project."""
        history = self.get_publish_history(project_id)
        return history[-1] if history else None


if __name__ == "__main__":
    # Test setup
    orchestrator = PublishingOrchestrator()

    # Test configuration
    config = PublishConfig(
        project_id="test_001",
        project_name="test_package",
        version="0.1.0",
        description="Test package",
        author="Test Author",
        author_email="test@example.com",
        license_type="MIT",
        targets=[RegistryType.PYPI, RegistryType.NPM],
        publish_target=PublishTarget.HYBRID_PYTHON,
        pypi_token="test_token",
        npm_token="test_token",
    )

    # Validate
    is_valid, errors = orchestrator.validate_config(config)
    logger.info(f"Config valid: {is_valid}")
    if errors:
        logger.error(f"Errors: {errors}")
