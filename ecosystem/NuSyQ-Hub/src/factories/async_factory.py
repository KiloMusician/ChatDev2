"""src/factories/async_factory.py - Async Project Factory.

Provides async/await interface for project generation using the new
generator system. Enables parallel file generation and better performance.

Usage:
    from src.factories.async_factory import AsyncProjectFactory

    factory = AsyncProjectFactory()

    # Generate with auto-selected provider
    result = await factory.generate("MyGame", template="godot_2d_game")

    # Generate with specific provider
    result = await factory.generate("MyTool", template="rust_cli", provider="ollama")

    # Generate with specific language
    result = await factory.generate("MyCLI", language="typescript")
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.factories.ai_orchestrator import AIOrchestrator
from src.factories.artifact_registry import ArtifactRegistry
from src.factories.generators import (AbstractGenerator, GenerationContext,
                                      GenerationResult, GeneratorRegistry)
from src.factories.languages import get_language_registry
from src.factories.templates import BaseProjectTemplate, load_template

logger = logging.getLogger(__name__)


@dataclass
class AsyncGeneratedProject:
    """Result of async factory project generation."""

    name: str
    type: str
    version: str
    output_path: Path
    provider: str
    model: str
    template_name: str

    # Generation stats
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    placeholder_files: int = 0
    total_tokens: int = 0
    total_time_ms: int = 0
    estimated_cost_usd: float = 0.0

    # Metadata
    language: str = "python"
    parallel: bool = True
    template_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, str]] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Return True if generation was mostly successful."""
        return self.successful_files > 0 and self.failed_files < self.total_files // 2

    @property
    def success_rate(self) -> float:
        """Return success rate as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.successful_files / self.total_files) * 100

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "output_path": str(self.output_path),
            "provider": self.provider,
            "model": self.model,
            "template_name": self.template_name,
            "language": self.language,
            "total_files": self.total_files,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "placeholder_files": self.placeholder_files,
            "success_rate": self.success_rate,
            "total_tokens": self.total_tokens,
            "total_time_ms": self.total_time_ms,
            "estimated_cost_usd": self.estimated_cost_usd,
            "parallel": self.parallel,
            "errors": self.errors or [],
        }


class AsyncProjectFactory:
    """Async factory for generating projects using the new generator system.

    Provides:
    - Async/await interface for non-blocking generation
    - Parallel file generation within projects
    - Automatic provider selection based on language
    - Integration with LanguageRegistry and GeneratorRegistry
    """

    def __init__(
        self,
        template_dir: Path | None = None,
        output_dir: Path | None = None,
    ):
        """Initialize async factory.

        Args:
            template_dir: Directory containing project templates
            output_dir: Directory for generated projects
        """
        base_path = Path(__file__).parent.parent.parent

        if template_dir is None:
            template_dir = base_path / "config" / "templates"
        if output_dir is None:
            output_dir = base_path / "projects" / "generated"

        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.registry = ArtifactRegistry()
        self.generator_registry = GeneratorRegistry.get_instance()
        self.language_registry = get_language_registry()
        self.orchestrator = AIOrchestrator()

    async def generate(
        self,
        name: str,
        template: str | None = None,
        language: str | None = None,
        provider: str | None = None,
        description: str = "",
        version: str = "1.0.0",
        parallel: bool = True,
        auto_register: bool = True,
        custom_template: dict[str, Any] | None = None,
        **kwargs,
    ) -> AsyncGeneratedProject:
        """Generate a project asynchronously.

        Args:
            name: Project name
            template: Template name (e.g., "rust_cli", "godot_2d_game")
            language: Target language (used if no template specified)
            provider: Force specific provider ("ollama", "claude", "openai")
            description: Project description
            version: Version string
            parallel: Enable parallel file generation
            auto_register: Register in artifact registry
            custom_template: Inline template dict (overrides template file)
            **kwargs: Additional context options

        Returns:
            AsyncGeneratedProject with results and stats
        """
        # Load or create template
        template_obj, template_path = self._resolve_template(template, language, custom_template)

        # Determine language
        lang = str(language or getattr(template_obj, "language", "python"))

        # Select generator
        generator = self._select_generator(lang, provider)
        if generator is None:
            raise ValueError(
                f"No available generator for language '{lang}'. "
                f"Available providers: {self.generator_registry.list_available()}"
            )

        # Create output directory
        output_path = self.output_dir / name
        output_path.mkdir(parents=True, exist_ok=True)

        # Build generation context
        context = GenerationContext(
            project_name=name,
            description=description or template_obj.description,
            template=template_obj,
            output_path=output_path,
            language=lang,
            parallel=parallel,
            **kwargs,
        )

        # Generate project
        logger.info(f"Generating '{name}' with {generator.provider_name} ({lang})")
        gen_result = await generator.generate(context)

        # Build result
        result = AsyncGeneratedProject(
            name=name,
            type=template_obj.type,
            version=version,
            output_path=output_path,
            provider=generator.provider_name,
            model=gen_result.model,
            template_name=template or "custom",
            language=lang,
            total_files=gen_result.total_files,
            successful_files=gen_result.successful_files,
            failed_files=gen_result.failed_files,
            placeholder_files=gen_result.placeholder_files,
            total_tokens=gen_result.total_tokens,
            total_time_ms=gen_result.total_time_ms,
            estimated_cost_usd=gen_result.estimated_cost_usd,
            parallel=parallel,
            template_path=template_path,
            metadata=gen_result.metadata,
            errors=gen_result.errors,
        )

        # Write generation diagnostics
        self._write_diagnostics(output_path, result, gen_result)

        # Register in artifact registry
        if auto_register and result.success:
            self.registry.register(
                name=name,
                project_type=template_obj.type,
                version=version,
                source_path=output_path,
                ai_provider=generator.provider_name,
                token_cost=result.estimated_cost_usd,
                model_used=gen_result.model,
                description=description,
                metadata={
                    "async_factory": True,
                    "language": lang,
                    "parallel": parallel,
                    "generation_stats": result.to_dict(),
                },
            )

        logger.info(
            f"Generated '{name}': {result.successful_files}/{result.total_files} files in {result.total_time_ms}ms"
        )

        return result

    def _resolve_template(
        self,
        template_name: str | None,
        language: str | None,
        custom_template: dict[str, Any] | None,
    ) -> tuple[BaseProjectTemplate, Path | None]:
        """Resolve template from name, language, or custom dict."""
        if custom_template:
            return BaseProjectTemplate.from_dict(custom_template), None

        if template_name:
            template_path = self.template_dir / f"{template_name}.yaml"
            if not template_path.exists():
                # Try without extension
                for ext in [".yaml", ".yml", ".json"]:
                    candidate = self.template_dir / f"{template_name}{ext}"
                    if candidate.exists():
                        template_path = candidate
                        break
                else:
                    raise FileNotFoundError(
                        f"Template not found: {template_name}. Available: {self._list_templates()}"
                    )
            return load_template(template_path), template_path

        # Create minimal template from language
        if language:
            lang_obj = self.language_registry.get_or_default(language)
            return (
                BaseProjectTemplate(
                    name="generated",
                    type="cli",
                    language=language,
                    description="Generated project",
                    file_structure={lang_obj.entry_file: "Main entry point"},
                ),
                None,
            )

        # Default Python template
        return (
            BaseProjectTemplate(
                name="generated",
                type="cli",
                language="python",
                description="Generated project",
                file_structure={"main.py": "Main entry point"},
            ),
            None,
        )

    def _select_generator(
        self,
        language: str,
        provider: str | None,
    ) -> AbstractGenerator | None:
        """Select the best generator for the request."""
        if provider:
            # Use specified provider
            try:
                gen = self.generator_registry.get(provider)
                if gen.is_available():
                    return gen
                logger.warning(f"Provider {provider} not available, auto-selecting")
            except KeyError:
                logger.warning(f"Provider {provider} not found, auto-selecting")

        # Auto-select based on language
        return self.generator_registry.get_for_language(language, prefer_local=True)

    def _list_templates(self) -> list[str]:
        """List available template names."""
        templates = []
        for path in self.template_dir.glob("*.yaml"):
            templates.append(path.stem)
        for path in self.template_dir.glob("*.yml"):
            templates.append(path.stem)
        return sorted(templates)

    def _write_diagnostics(
        self,
        output_path: Path,
        result: AsyncGeneratedProject,
        gen_result: GenerationResult,
    ) -> None:
        """Write generation diagnostics to output directory."""
        import json

        diagnostics = {
            "generated_at": datetime.now().isoformat(),
            "factory": "AsyncProjectFactory",
            "provider": result.provider,
            "model": result.model,
            "language": result.language,
            "template": result.template_name,
            "stats": {
                "total_files": result.total_files,
                "successful_files": result.successful_files,
                "failed_files": result.failed_files,
                "placeholder_files": result.placeholder_files,
                "success_rate": result.success_rate,
                "total_tokens": result.total_tokens,
                "total_time_ms": result.total_time_ms,
                "estimated_cost_usd": result.estimated_cost_usd,
            },
            "files": [
                {
                    "path": f.filepath,
                    "success": f.success,
                    "tokens": f.tokens_used,
                    "time_ms": f.generation_time_ms,
                    "is_placeholder": f.is_placeholder,
                }
                for f in gen_result.files
            ],
            "errors": result.errors or [],
        }

        diag_path = output_path / ".factory_diagnostics.json"
        with open(diag_path, "w", encoding="utf-8") as f:
            json.dump(diagnostics, f, indent=2)

    async def generate_batch(
        self,
        projects: list[dict[str, Any]],
        max_concurrent: int = 3,
    ) -> list[AsyncGeneratedProject]:
        """Generate multiple projects concurrently.

        Args:
            projects: List of project configs (each passed to generate())
            max_concurrent: Max concurrent generations

        Returns:
            List of AsyncGeneratedProject results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_one(config: dict[str, Any]) -> AsyncGeneratedProject:
            async with semaphore:
                return await self.generate(**config)

        tasks = [generate_one(config) for config in projects]
        return await asyncio.gather(*tasks, return_exceptions=False)

    def list_templates(self) -> list[dict[str, Any]]:
        """List all available templates with metadata."""
        import importlib

        yaml = importlib.import_module("yaml")

        templates = []
        for path in sorted(self.template_dir.glob("*.yaml")):
            try:
                with open(path) as f:
                    data = yaml.safe_load(f)
                templates.append(
                    {
                        "name": path.stem,
                        "display_name": data.get("name", path.stem),
                        "type": data.get("type", "unknown"),
                        "language": data.get("language", "unknown"),
                        "description": data.get("description", ""),
                    }
                )
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)
        return templates

    def list_languages(self) -> list[str]:
        """List all supported languages."""
        return self.language_registry.list_names()

    def list_providers(self) -> list[str]:
        """List all available providers."""
        return self.generator_registry.list_available()


# Convenience function for quick generation
async def quick_generate(
    name: str,
    template: str | None = None,
    language: str | None = None,
    **kwargs,
) -> AsyncGeneratedProject:
    """Quick project generation with sensible defaults.

    Args:
        name: Project name
        template: Template name (optional)
        language: Language (optional, derived from template if not set)
        **kwargs: Additional options

    Returns:
        AsyncGeneratedProject result
    """
    factory = AsyncProjectFactory()
    return await factory.generate(name, template=template, language=language, **kwargs)


# Sync wrapper for CLI/non-async contexts
def generate_sync(
    name: str,
    template: str | None = None,
    language: str | None = None,
    **kwargs,
) -> AsyncGeneratedProject:
    """Synchronous wrapper for project generation.

    Use this from non-async contexts (CLI, scripts).
    """
    return asyncio.run(quick_generate(name, template=template, language=language, **kwargs))
