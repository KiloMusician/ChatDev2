"""Universal Project Generator (UPG) - Core orchestration engine.

Coordinates template loading, AI provider selection, code generation,
artifact registration, and integration with NuSyQ systems.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from src.generators.template_definitions import (AIProvider, ProjectTemplate,
                                                 ProjectType, get_template,
                                                 list_templates)

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of a project generation."""

    project_id: str
    template_id: str
    project_name: str
    output_path: str
    status: str  # "success", "in_progress", "failed"
    ai_provider: str
    generation_time: float
    created_at: str
    metadata: dict[str, Any]
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class UniversalProjectGenerator:
    """Core universal project generator combining.

    - Template loading & validation
    - AI provider selection
    - Code generation orchestration
    - Artifact registration
    - NuSyQ system integration.
    """

    def __init__(
        self,
        output_base: Path | None = None,
        registry_path: Path | None = None,
        quest_log_path: Path | None = None,
    ):
        """Initialize the UPG.

        Args:
            output_base: Base directory for generated projects (default: projects/generated/)
            registry_path: Path to artifact registry (default: config/artifact_registry.json)
            quest_log_path: Path to quest log (default: src/Rosetta_Quest_System/quest_log.jsonl)
        """
        self.output_base = Path(output_base or "projects/generated")
        self.registry_path = Path(registry_path or "config/artifact_registry.json")
        self.quest_log_path = Path(quest_log_path or "src/Rosetta_Quest_System/quest_log.jsonl")

        # Ensure directories exist
        self.output_base.mkdir(parents=True, exist_ok=True)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.quest_log_path.parent.mkdir(parents=True, exist_ok=True)

        self.registry: dict[str, Any] = self._load_registry()

    def _load_registry(self) -> dict[str, Any]:
        """Load artifact registry from disk."""
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        return {"projects": [], "last_updated": None}

    def _save_registry(self) -> None:
        """Save artifact registry to disk."""
        self.registry["last_updated"] = datetime.utcnow().isoformat()
        with open(self.registry_path, "w") as f:
            json.dump(self.registry, f, indent=2)

    def get_template(self, template_id: str) -> ProjectTemplate | None:
        """Retrieve a template by ID."""
        return get_template(template_id)

    def list_templates(self, project_type: ProjectType | None = None) -> list[ProjectTemplate]:
        """List available templates."""
        return list_templates(project_type)

    def validate_template(self, template: ProjectTemplate) -> tuple[bool, list[str]]:
        """Validate template completeness.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        if not template.template_id:
            errors.append("Template must have template_id")
        if not template.name:
            errors.append("Template must have name")
        if template.complexity < 1 or template.complexity > 10:
            errors.append(f"Complexity must be 1-10, got {template.complexity}")
        if not template.starter_files and not template.ai_enhancement_available:
            errors.append("Template must have starter_files if AI enhancement disabled")
        if not template.primary_ai_provider:
            errors.append("Template must specify primary_ai_provider")

        return len(errors) == 0, errors

    def select_ai_provider(self, template: ProjectTemplate) -> AIProvider:
        """Select AI provider based on template complexity.

        Claude Method():
        - Complexity 8-10: ChatDev (multi-agent orchestration)
        - Complexity 5-7: Also ChatDev (scaffold + enhancement)
        - Complexity 1-4: Ollama (qwen2.5-coder local generation)

        Note: Template's primary_ai_provider is respected if set.
        """
        if template.primary_ai_provider != AIProvider.OLLAMA:
            return template.primary_ai_provider

        # Fallback to complexity-based routing
        if template.complexity >= 6:
            return AIProvider.CHATDEV
        return AIProvider.OLLAMA

    def _create_project_directory(self, project_name: str) -> Path:
        """Create and return project output directory."""
        project_dir = self.output_base / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def _write_starter_files(self, project_dir: Path, template: ProjectTemplate) -> None:
        """Write template starter files to project directory."""
        for filename, content in template.starter_files.items():
            file_path = project_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            logger.debug(f"Created: {file_path}")

    def _write_project_metadata(
        self, project_dir: Path, template: ProjectTemplate, project_id: str
    ) -> None:
        """Write .nusyq.json metadata file."""
        metadata = {
            "project_id": project_id,
            "template_id": template.template_id,
            "template_name": template.name,
            "created_at": datetime.utcnow().isoformat(),
            "complexity": template.complexity,
            "language": template.language.value,
            "type": template.type.value,
            "ai_provider": template.primary_ai_provider.value,
        }

        metadata_file = project_dir / ".nusyq.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        logger.debug(f"Created metadata: {metadata_file}")

    def _register_artifact(self, result: GenerationResult) -> None:
        """Register generated project in artifact registry."""
        artifact = {
            "project_id": result.project_id,
            "template_id": result.template_id,
            "name": result.project_name,
            "path": str(result.output_path),
            "status": result.status,
            "ai_provider": result.ai_provider,
            "created_at": result.created_at,
        }

        self.registry["projects"].append(artifact)
        self._save_registry()
        logger.info(f"Registered artifact: {result.project_id}")

    def _log_quest(self, result: GenerationResult) -> None:
        """Log project generation as quest event."""
        quest_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "project_generated",
            "project_id": result.project_id,
            "template_id": result.template_id,
            "project_name": result.project_name,
            "status": result.status,
            "metadata": result.metadata,
        }

        with open(self.quest_log_path, "a") as f:
            f.write(json.dumps(quest_event) + "\n")

        logger.info(f"Logged quest: {result.template_id} -> {result.project_name}")

    def generate(
        self,
        template_id: str,
        project_name: str,
        _project_type: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> GenerationResult:
        """Generate a new project from template.

        Args:
            template_id: ID of template to use
            project_name: Name for the generated project
            project_type: Project type (game, webapp, package, etc.)
            options: Additional customization options

        Returns:
            GenerationResult with project metadata and status
        """
        import time

        start_time = time.time()
        project_id = str(uuid.uuid4())[:8]

        try:
            # 1. Load and validate template
            template = self.get_template(template_id)
            if not template:
                return GenerationResult(
                    project_id=project_id,
                    template_id=template_id,
                    project_name=project_name,
                    output_path="",
                    status="failed",
                    ai_provider="none",
                    generation_time=time.time() - start_time,
                    created_at=datetime.utcnow().isoformat(),
                    metadata={},
                    error_message=f"Template not found: {template_id}",
                )

            is_valid, errors = self.validate_template(template)
            if not is_valid:
                return GenerationResult(
                    project_id=project_id,
                    template_id=template_id,
                    project_name=project_name,
                    output_path="",
                    status="failed",
                    ai_provider="none",
                    generation_time=time.time() - start_time,
                    created_at=datetime.utcnow().isoformat(),
                    metadata={},
                    error_message=f"Template validation failed: {'; '.join(errors)}",
                )

            # 2. Select AI provider
            ai_provider = self.select_ai_provider(template)

            # 3. Create project directory
            project_dir = self._create_project_directory(project_name)

            # 4. Write starter files
            self._write_starter_files(project_dir, template)

            # 5. Write metadata
            self._write_project_metadata(project_dir, template, project_id)

            # 6. Create success result
            result = GenerationResult(
                project_id=project_id,
                template_id=template_id,
                project_name=project_name,
                output_path=str(project_dir),
                status="success",
                ai_provider=ai_provider.value,
                generation_time=time.time() - start_time,
                created_at=datetime.utcnow().isoformat(),
                metadata={
                    "language": template.language.value,
                    "type": template.type.value,
                    "complexity": template.complexity,
                    "options": options or {},
                },
            )

            # 7. Register & log
            self._register_artifact(result)
            self._log_quest(result)

            logger.info(f"✅ Generated project: {project_name} (id={project_id})")
            return result

        except Exception as e:
            logger.error(f"❌ Generation failed: {e!s}")
            return GenerationResult(
                project_id=project_id,
                template_id=template_id,
                project_name=project_name,
                output_path="",
                status="failed",
                ai_provider="none",
                generation_time=time.time() - start_time,
                created_at=datetime.utcnow().isoformat(),
                metadata={},
                error_message=str(e),
            )

    def get_project_info(self, project_id: str) -> dict[str, Any] | None:
        """Retrieve information about a generated project."""
        projects = self.registry.get("projects", [])
        if not isinstance(projects, list):
            return None
        for artifact in projects:
            if isinstance(artifact, dict) and artifact.get("project_id") == project_id:
                return cast(dict[str, Any], artifact)
        return None

    def list_generated_projects(self) -> list[dict[str, Any]]:
        """List all generated projects."""
        return self.registry.get("projects", [])

    def get_template_complexity_info(self, template_id: str) -> dict[str, Any] | None:
        """Get complexity information for a template."""
        template = self.get_template(template_id)
        if not template:
            return None

        return {
            "template_id": template_id,
            "name": template.name,
            "complexity": template.complexity,
            "estimated_time": template.estimated_generation_time,
            "ai_provider": template.primary_ai_provider.value,
            "language": template.language.value,
        }


if __name__ == "__main__":
    # Quick test
    upg = UniversalProjectGenerator()

    # List available templates
    templates = upg.list_templates()
    logger.info(f"Available templates: {len(templates)}")
    for t in templates:
        logger.info(f"  - {t.template_id}: {t.name} (complexity={t.complexity})")

    # Generate a test project
    result = upg.generate("package_python", "my_test_package")
    logger.info(f"\nGeneration result: {result.status}")
    if result.status == "success":
        logger.info(f"  Output: {result.output_path}")
        logger.info(f"  Time: {result.generation_time:.2f}s")
