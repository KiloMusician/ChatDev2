"""Docker Builder - Generate Dockerfiles and build/push images.

Supports:
- Python applications
- Node.js/JavaScript applications
- Multi-stage builds
- Docker Compose
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


@dataclass
class DockerConfig:
    """Docker build and push configuration."""

    project_name: str
    version: str
    language: str  # "python", "node", "javascript"

    # Base image
    base_image: str

    # Registry
    registry: str = "docker.io"  # docker.io, ghcr.io, etc.
    username: str = ""  # Docker Hub username

    # Build settings
    working_dir: str = "/app"
    expose_ports: list[int] = None
    environment_vars: dict[str, str] = None

    # Dependencies
    requirements_file: str | None = None  # requirements.txt, package.json, etc.

    # Health check
    healthcheck_cmd: str | None = None
    healthcheck_interval: int = 30

    def __post_init__(self):
        """Implement __post_init__."""
        if self.expose_ports is None:
            self.expose_ports = []
        if self.environment_vars is None:
            self.environment_vars = {"NODE_ENV": "production"}


class DockerfileGenerator:
    """Generate Dockerfile from configuration."""

    # Base images for common languages
    BASE_IMAGES: ClassVar[dict] = {
        "python:3.8": "python:3.8-slim",
        "python:3.9": "python:3.9-slim",
        "python:3.10": "python:3.10-slim",
        "python:3.11": "python:3.11-slim",
        "python:3.12": "python:3.12-slim",
        "node:16": "node:16-alpine",
        "node:18": "node:18-alpine",
        "node:20": "node:20-alpine",
    }

    @staticmethod
    def generate_python_dockerfile(config: DockerConfig) -> str:
        """Generate Dockerfile for Python application."""
        dockerfile = f"""# {config.project_name} - Python {config.version}
FROM {config.base_image}

WORKDIR {config.working_dir}

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends\\
    build-essential\\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser {config.working_dir}
USER appuser

"""

        # Add expose ports
        if config.expose_ports:
            for port in config.expose_ports:
                dockerfile += f"EXPOSE {port}\n"

        # Add environment variables
        if config.environment_vars:
            for key, value in config.environment_vars.items():
                dockerfile += f"ENV {key}={value}\n"

        # Add health check
        if config.healthcheck_cmd:
            dockerfile += f"""
HEALTHCHECK --interval={config.healthcheck_interval}s --timeout=5s --start-period=10s --retries=3 \\
    CMD {config.healthcheck_cmd}
"""

        # Add entrypoint
        dockerfile += f"""
CMD ["python", "-m", "{config.project_name}"]
"""

        return dockerfile

    @staticmethod
    def generate_node_dockerfile(config: DockerConfig) -> str:
        """Generate Dockerfile for Node.js application."""
        dockerfile = f"""# {config.project_name} - Node.js {config.version}
FROM {config.base_image}

WORKDIR {config.working_dir}

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build (if needed)
RUN npm run build --if-present

# Create non-root user
RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser && chown -R appuser:appuser {config.working_dir}
USER appuser

"""

        # Add expose ports
        if config.expose_ports:
            for port in config.expose_ports:
                dockerfile += f"EXPOSE {port}\n"

        # Add environment variables
        if config.environment_vars:
            for key, value in config.environment_vars.items():
                dockerfile += f"ENV {key}={value}\n"

        # Add health check
        if config.healthcheck_cmd:
            dockerfile += f"""
HEALTHCHECK --interval={config.healthcheck_interval}s --timeout=5s --start-period=10s --retries=3 \\
    CMD {config.healthcheck_cmd}
"""

        # Add entrypoint
        dockerfile += """
CMD ["node", "dist/index.js"]
"""

        return dockerfile

    @staticmethod
    def generate_dockerfile(config: DockerConfig) -> str:
        """Generate appropriate Dockerfile based on language."""
        if "python" in config.language.lower():
            return DockerfileGenerator.generate_python_dockerfile(config)
        elif "node" in config.language.lower() or "javascript" in config.language.lower():
            return DockerfileGenerator.generate_node_dockerfile(config)
        else:
            raise ValueError(f"Unsupported language: {config.language}")


class DockerBuilder:
    """Build and push Docker images."""

    def __init__(self, project_path: Path, registry_credentials: dict[str, str] | None = None):
        """Initialize Docker builder.

        Args:
            project_path: Path to project
            registry_credentials: Dict with 'username' and 'password' for Docker Hub
        """
        self.project_path = Path(project_path)
        self.registry_credentials = registry_credentials or {}

    def generate_dockerfile(self, config: DockerConfig, output_path: Path | None = None) -> str:
        """Generate and optionally write Dockerfile.

        Args:
            config: Docker configuration
            output_path: Where to save Dockerfile (default: project_path/Dockerfile)

        Returns:
            Dockerfile content
        """
        dockerfile = DockerfileGenerator.generate_dockerfile(config)

        output_path = output_path or (self.project_path / "Dockerfile")
        output_path.write_text(dockerfile)
        logger.info(f"Generated Dockerfile: {output_path}")

        return dockerfile

    def generate_dockerignore(self) -> str:
        """Generate .dockerignore file."""
        dockerignore = """# Git
.git
.gitignore
.gitattributes

# IDE
.vscode
.idea
*.swp
*.swo
*~

# Build artifacts
build/
dist/
*.egg-info
__pycache__
node_modules
npm-debug.log

# Tests
.pytest_cache
coverage
.nyc_output

# Environment
.env
.env.local
.npmrc

# OS
.DS_Store
Thumbs.db

# Documentation
docs/
README.md
"""

        dockerignore_path = self.project_path / ".dockerignore"
        dockerignore_path.write_text(dockerignore)
        logger.info(f"Generated .dockerignore: {dockerignore_path}")

        return dockerignore

    def build(
        self, config: DockerConfig, tag: str | None = None, no_cache: bool = False
    ) -> dict[str, Any]:
        """Build Docker image.

        Args:
            config: Docker configuration
            tag: Custom image tag (default: username/project:version)
            no_cache: Build without cache

        Returns:
            Result dict with status and image info
        """
        try:
            logger.info(f"Building Docker image for {config.project_name}")

            # Generate files if not present
            dockerfile_path = self.project_path / "Dockerfile"
            if not dockerfile_path.exists():
                self.generate_dockerfile(config, dockerfile_path)

            if not (self.project_path / ".dockerignore").exists():
                self.generate_dockerignore()

            # Determine image tag
            if not tag:
                tag = f"{config.username}/{config.project_name}:{config.version}"
                if config.registry != "docker.io":
                    tag = f"{config.registry}/{tag}"

            # Build command
            build_cmd = ["docker", "build", "-t", tag]
            if no_cache:
                build_cmd.append("--no-cache")
            build_cmd.append(str(self.project_path))

            logger.info(f"Building image: {tag}")
            result = subprocess.run(build_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Build failed: {result.stderr}")
                return {
                    "status": "failed",
                    "error": result.stderr,
                }

            logger.info(f"Successfully built image: {tag}")
            return {
                "status": "success",
                "image": tag,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Docker build failed: {e!s}")
            return {
                "status": "failed",
                "error": str(e),
            }

    def push(self, image_tag: str, dry_run: bool = False) -> dict[str, Any]:
        """Push image to registry.

        Args:
            image_tag: Full image tag (registry/username/project:version)
            dry_run: If True, don't actually push

        Returns:
            Result dict with status and URL
        """
        try:
            if not dry_run:
                logger.info(f"Pushing image: {image_tag}")
                push_cmd = ["docker", "push", image_tag]
                result = subprocess.run(push_cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    logger.error(f"Push failed: {result.stderr}")
                    return {
                        "status": "failed",
                        "error": result.stderr,
                    }

            # Parse registry from tag
            registry = "docker.io"
            if "/" in image_tag and "." in image_tag.split("/")[0]:
                registry = image_tag.split("/")[0]

            logger.info(f"Successfully pushed image: {image_tag}")
            return {
                "status": "success",
                "image": image_tag,
                "url": f"https://{registry}/r/{image_tag.split('/')[-1].split(':')[0]}",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Docker push failed: {e!s}")
            return {
                "status": "failed",
                "error": str(e),
            }

    def build_and_push(
        self, config: DockerConfig, tag: str | None = None, dry_run: bool = False
    ) -> dict[str, Any]:
        """Build and push image in one operation.

        Args:
            config: Docker configuration
            tag: Custom image tag
            dry_run: If True, build but don't push

        Returns:
            Result dict with build and push status
        """
        # Build
        build_result = self.build(config, tag)
        if build_result["status"] != "success":
            return build_result

        # Push
        image_tag = build_result["image"]
        push_result = self.push(image_tag, dry_run=dry_run)

        return {
            "status": push_result["status"],
            "build": build_result,
            "push": push_result,
        }

    def generate_docker_compose(self, config: DockerConfig, services: dict[str, Any]) -> str:
        """Generate docker-compose.yml file.

        Args:
            config: Docker configuration
            services: Dict of service definitions

        Returns:
            Docker Compose YAML content
        """
        compose_dict = {
            "version": "3.8",
            "services": {
                config.project_name: {
                    "build": ".",
                    "image": f"{config.username}/{config.project_name}:{config.version}",
                    "ports": (
                        [f"{port}:{port}" for port in config.expose_ports]
                        if config.expose_ports
                        else []
                    ),
                    "environment": config.environment_vars or {},
                    "restart": "unless-stopped",
                }
            },
        }

        # Add additional services if provided
        if services:
            compose_dict["services"].update(services)

        # Convert to YAML-like format
        import yaml

        try:
            yaml_content = yaml.dump(compose_dict, default_flow_style=False, sort_keys=False)
        except ImportError:
            # Fallback if PyYAML not available
            yaml_content = json.dumps(compose_dict, indent=2)

        return yaml_content
