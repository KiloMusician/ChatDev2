"""src/factories/generators/ollama_generator.py - Ollama Local LLM Generator.

Implements the AbstractGenerator interface for local Ollama inference.
Supports parallel file generation for faster project creation.

Features:
- Async parallel file generation with asyncio.gather
- Automatic model selection based on language
- Rate limiting to prevent overwhelming Ollama
- Robust error handling with placeholders
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

import aiohttp

from src.factories.generators.base import (AbstractGenerator, FileResult,
                                           GenerationContext, GenerationResult)

logger = logging.getLogger(__name__)


class OllamaGenerator(AbstractGenerator):
    """Local Ollama LLM generator with parallel file generation.

    Uses asyncio for concurrent file generation, significantly reducing
    project creation time for multi-file projects.
    """

    # Default models by capability
    DEFAULT_MODEL = "qwen2.5-coder:7b"
    MODELS_BY_STRENGTH: ClassVar[dict] = {
        "fast": "qwen2.5-coder:3b",
        "balanced": "qwen2.5-coder:7b",
        "powerful": "deepseek-coder-v2:16b",
    }

    # Supported languages (Ollama supports all via general coding ability)
    SUPPORTED_LANGUAGES: ClassVar[set] = {
        "python",
        "javascript",
        "typescript",
        "rust",
        "go",
        "csharp",
        "gdscript",
        "lua",
        "java",
        "cpp",
        "c",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
    }

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str | None = None,
        max_parallel: int = 3,
        timeout_seconds: int = 180,
    ):
        """Initialize Ollama generator.

        Args:
            base_url: Ollama API base URL
            model: Model to use (default: qwen2.5-coder:7b)
            max_parallel: Max concurrent file generations
            timeout_seconds: Request timeout
        """
        self.base_url = base_url.rstrip("/")
        self.model = model or self.DEFAULT_MODEL
        self.max_parallel = max_parallel
        self.timeout_seconds = timeout_seconds
        self._semaphore = asyncio.Semaphore(max_parallel)

    @property
    def provider_name(self) -> str:
        return "ollama"

    def supports_language(self, language: str) -> bool:
        return language.lower() in self.SUPPORTED_LANGUAGES

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "supported_languages": list(self.SUPPORTED_LANGUAGES),
            "max_tokens": 8192,
            "supports_parallel": True,
            "cost_per_1k_tokens": 0.0,  # Free (local)
            "requires_api_key": False,
            "local": True,
            "models": list(self.MODELS_BY_STRENGTH.values()),
            "default_model": self.model,
        }

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        import requests

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    async def generate(self, context: GenerationContext) -> GenerationResult:
        """Generate a complete project using parallel file generation.

        Args:
            context: Generation context with template and settings

        Returns:
            GenerationResult with all files and stats
        """
        start_time = datetime.now()
        model = context.model or self.model

        result = GenerationResult(
            project_name=context.project_name,
            output_path=context.output_path,
            provider=self.provider_name,
            model=model,
            start_time=start_time,
        )

        # Ensure output directory exists
        context.output_path.mkdir(parents=True, exist_ok=True)

        # Get file structure from template
        file_structure = getattr(context.template, "file_structure", {})
        if not file_structure:
            # Get default entry from language registry
            try:
                from src.factories.languages import get_language_registry

                registry = get_language_registry()
                lang = registry.get_or_default(context.language or "python")
                file_structure = {lang.entry_file: "Main entry point"}
            except Exception:
                file_structure = {"main.py": "Main entry point"}

        # Detect entry point for context
        if not context.entry_point:
            context.entry_point = next(iter(file_structure.keys()))

        # Generate files (parallel or sequential based on context.parallel)
        if context.parallel and len(file_structure) > 1:
            file_results = await self._generate_parallel(file_structure, context, model)
        else:
            file_results = await self._generate_sequential(file_structure, context, model)

        # Add all results
        for file_result in file_results:
            result.add_file(file_result)

            # Write file to disk
            if file_result.success:
                file_path = context.output_path / file_result.filepath
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_result.content, encoding="utf-8")

                # Cache snippet for coherent generation
                context.generated_files[file_result.filepath] = file_result.content[:500]

        # Finalize result
        result.end_time = datetime.now()
        result.total_time_ms = int((result.end_time - start_time).total_seconds() * 1000)
        result.metadata = {
            "parallel": context.parallel,
            "max_parallel": self.max_parallel,
            "base_url": self.base_url,
        }

        try:
            from src.system.agent_awareness import emit as _emit

            _status = "success" if getattr(result, "success_count", 1) > 0 else "partial"
            _emit(
                "tasks",
                f"Ollama factory: {context.project_name} | files={result.total_files}"
                f" status={_status} time={result.total_time_ms}ms",
                level="INFO",
                source="ollama_generator",
            )
        except Exception:
            pass

        return result

    async def _generate_parallel(
        self,
        file_structure: dict[str, str],
        context: GenerationContext,
        _model: str,
    ) -> list[FileResult]:
        """Generate files in parallel using asyncio.gather."""
        logger.info(f"Generating {len(file_structure)} files in parallel (max {self.max_parallel})")

        tasks = [
            self._generate_with_semaphore(filepath, description, context)
            for filepath, description in file_structure.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed FileResults
        file_results = []
        for i, (filepath, _) in enumerate(file_structure.items()):
            if isinstance(results[i], Exception):
                file_results.append(
                    FileResult(
                        filepath=filepath,
                        content=self._placeholder_content(Path(filepath).suffix),
                        success=False,
                        error=str(results[i]),
                        is_placeholder=True,
                    )
                )
            else:
                file_results.append(results[i])

        return file_results

    async def _generate_with_semaphore(
        self,
        filepath: str,
        description: str,
        context: GenerationContext,
    ) -> FileResult:
        """Generate a file with semaphore for rate limiting."""
        async with self._semaphore:
            return await self.generate_file(filepath, description, context)

    async def _generate_sequential(
        self,
        file_structure: dict[str, str],
        context: GenerationContext,
        _model: str,
    ) -> list[FileResult]:
        """Generate files sequentially (for coherent multi-file projects)."""
        logger.info(f"Generating {len(file_structure)} files sequentially")
        results = []

        for filepath, description in file_structure.items():
            result = await self.generate_file(filepath, description, context)
            results.append(result)

            # Update context with generated content for coherence
            if result.success:
                context.generated_files[filepath] = result.content[:500]

            # Brief pause between generations
            await asyncio.sleep(0.2)

        return results

    async def generate_file(
        self,
        filepath: str,
        description: str,
        context: GenerationContext,
    ) -> FileResult:
        """Generate a single file using Ollama.

        Args:
            filepath: Target file path
            description: What the file should contain
            context: Generation context

        Returns:
            FileResult with generated content
        """
        start_time = time.time()
        ext = Path(filepath).suffix.lower()
        model = context.model or self.model

        logger.debug(f"Generating {filepath}...")

        prompt = self._build_file_prompt(filepath, description, context)

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": context.temperature,
                            "num_predict": context.max_tokens,
                        },
                    },
                    timeout=aiohttp.ClientTimeout(total=context.timeout_seconds),
                ) as response,
            ):
                if response.status == 200:
                    data = await response.json()
                    raw_content = data.get("response", "")
                    tokens = data.get("eval_count", 0)

                    # Clean the output
                    content = self._clean_code_output(raw_content, ext)

                    # Check if it's a placeholder
                    placeholder = self._placeholder_content(ext)
                    is_placeholder = content.strip() == placeholder.strip()

                    gen_time = int((time.time() - start_time) * 1000)
                    logger.debug(f"  Generated {filepath} ({len(content)} bytes, {tokens} tokens)")

                    return FileResult(
                        filepath=filepath,
                        content=content,
                        success=True,
                        tokens_used=tokens,
                        generation_time_ms=gen_time,
                        is_placeholder=is_placeholder,
                    )
                else:
                    error_text = await response.text()
                    logger.warning(f"  Failed {filepath}: HTTP {response.status}")
                    return FileResult(
                        filepath=filepath,
                        content=self._placeholder_content(ext),
                        success=False,
                        error=f"HTTP {response.status}: {error_text[:100]}",
                        is_placeholder=True,
                    )

        except TimeoutError:
            logger.warning(f"  Timeout generating {filepath}")
            return FileResult(
                filepath=filepath,
                content=self._placeholder_content(ext),
                success=False,
                error="Request timeout",
                is_placeholder=True,
            )
        except Exception as e:
            logger.warning(f"  Error generating {filepath}: {e}")
            return FileResult(
                filepath=filepath,
                content=self._placeholder_content(ext),
                success=False,
                error=str(e),
                is_placeholder=True,
            )


def get_ollama_generator(
    model: str | None = None,
    max_parallel: int = 3,
) -> OllamaGenerator:
    """Factory function to create an OllamaGenerator."""
    return OllamaGenerator(model=model, max_parallel=max_parallel)
