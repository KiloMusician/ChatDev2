"""src/factories/generators/claude_generator.py - Anthropic Claude Generator.

Implements the AbstractGenerator interface for Claude API.
Supports multi-file generation with context preservation.

Features:
- Async parallel file generation
- Model selection (Haiku, Sonnet, Opus)
- Smart rate limiting to respect API limits
- Full multi-file project generation
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

import aiohttp

from src.factories.generators.base import (AbstractGenerator, FileResult,
                                           GenerationContext, GenerationResult)

logger = logging.getLogger(__name__)


class ClaudeGenerator(AbstractGenerator):
    """Claude API generator with async support.

    Uses Anthropic's Claude API for code generation.
    Requires ANTHROPIC_API_KEY environment variable.
    """

    API_BASE = "https://api.anthropic.com/v1"

    # Available models
    MODELS: ClassVar[dict] = {
        "haiku": "claude-3-haiku-20240307",
        "sonnet": "claude-sonnet-4-20250514",
        "opus": "claude-opus-4-20250514",
    }

    DEFAULT_MODEL = "claude-3-haiku-20240307"

    # Cost per 1K tokens (approximate)
    COSTS: ClassVar[dict] = {
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
        "claude-opus-4-20250514": {"input": 0.015, "output": 0.075},
    }

    # Languages Claude excels at
    SUPPORTED_LANGUAGES: ClassVar[set] = {
        "python",
        "javascript",
        "typescript",
        "rust",
        "go",
        "csharp",
        "java",
        "cpp",
        "c",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "haskell",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_parallel: int = 2,  # Lower than Ollama due to rate limits
        timeout_seconds: int = 60,
    ):
        """Initialize Claude generator.

        Args:
            api_key: Anthropic API key (or use ANTHROPIC_API_KEY env)
            model: Model to use (haiku, sonnet, opus, or full model name)
            max_parallel: Max concurrent requests
            timeout_seconds: Request timeout
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = self._resolve_model(model)
        self.max_parallel = max_parallel
        self.timeout_seconds = timeout_seconds
        self._semaphore = asyncio.Semaphore(max_parallel)

    def _resolve_model(self, model: str | None) -> str:
        """Resolve model shorthand to full model name."""
        if model is None:
            return self.DEFAULT_MODEL
        if model in self.MODELS:
            return self.MODELS[model]
        return model

    @property
    def provider_name(self) -> str:
        return "claude"

    def supports_language(self, language: str) -> bool:
        return language.lower() in self.SUPPORTED_LANGUAGES

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "supported_languages": list(self.SUPPORTED_LANGUAGES),
            "max_tokens": 4096,
            "supports_parallel": True,
            "cost_per_1k_tokens": self.COSTS.get(self.model, {}).get("output", 0.00125),
            "requires_api_key": True,
            "local": False,
            "models": list(self.MODELS.values()),
            "default_model": self.model,
        }

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def generate(self, context: GenerationContext) -> GenerationResult:
        """Generate a complete project using Claude.

        Args:
            context: Generation context with template and settings

        Returns:
            GenerationResult with all files and stats
        """
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

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
            try:
                from src.factories.languages import get_language_registry

                registry = get_language_registry()
                lang = registry.get_or_default(context.language or "python")
                file_structure = {lang.entry_file: "Main entry point"}
            except Exception:
                file_structure = {"main.py": "Main entry point"}

        # Detect entry point
        if not context.entry_point:
            context.entry_point = next(iter(file_structure.keys()))

        # Generate files in parallel
        if context.parallel and len(file_structure) > 1:
            file_results = await self._generate_parallel(file_structure, context)
        else:
            file_results = await self._generate_sequential(file_structure, context)

        # Add all results and write files
        total_cost = 0.0
        for file_result in file_results:
            result.add_file(file_result)

            if file_result.success:
                file_path = context.output_path / file_result.filepath
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_result.content, encoding="utf-8")
                context.generated_files[file_result.filepath] = file_result.content[:500]

            # Estimate cost
            total_cost += self.estimate_cost(file_result.tokens_used)

        result.end_time = datetime.now()
        result.total_time_ms = int((result.end_time - start_time).total_seconds() * 1000)
        result.estimated_cost_usd = total_cost
        result.metadata = {
            "parallel": context.parallel,
            "max_parallel": self.max_parallel,
            "model": model,
        }

        try:
            from src.system.agent_awareness import emit as _emit

            _status = "success" if getattr(result, "success_count", 1) > 0 else "partial"
            _emit(
                "tasks",
                f"Claude factory: {context.project_name} | files={result.total_files}"
                f" status={_status} time={result.total_time_ms}ms",
                level="INFO",
                source="claude_generator",
            )
        except Exception:
            pass

        return result

    async def _generate_parallel(
        self,
        file_structure: dict[str, str],
        context: GenerationContext,
    ) -> list[FileResult]:
        """Generate files in parallel with rate limiting."""
        logger.info(f"Generating {len(file_structure)} files in parallel (max {self.max_parallel})")

        tasks = [
            self._generate_with_semaphore(filepath, description, context)
            for filepath, description in file_structure.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

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
            # Add small delay to avoid rate limiting
            await asyncio.sleep(0.5)
            return await self.generate_file(filepath, description, context)

    async def _generate_sequential(
        self,
        file_structure: dict[str, str],
        context: GenerationContext,
    ) -> list[FileResult]:
        """Generate files sequentially."""
        logger.info(f"Generating {len(file_structure)} files sequentially")
        results = []

        for filepath, description in file_structure.items():
            result = await self.generate_file(filepath, description, context)
            results.append(result)

            if result.success:
                context.generated_files[filepath] = result.content[:500]

            await asyncio.sleep(0.3)

        return results

    async def generate_file(
        self,
        filepath: str,
        description: str,
        context: GenerationContext,
    ) -> FileResult:
        """Generate a single file using Claude API.

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

        logger.debug(f"Generating {filepath} with Claude...")

        prompt = self._build_file_prompt(filepath, description, context)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": model,
            "max_tokens": context.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    f"{self.API_BASE}/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=context.timeout_seconds),
                ) as response,
            ):
                if response.status == 200:
                    data = await response.json()
                    raw_content = data.get("content", [{}])[0].get("text", "")
                    usage = data.get("usage", {})
                    tokens = usage.get("output_tokens", 0) + usage.get("input_tokens", 0)

                    content = self._clean_code_output(raw_content, ext)
                    placeholder = self._placeholder_content(ext)
                    is_placeholder = content.strip() == placeholder.strip()

                    gen_time = int((time.time() - start_time) * 1000)
                    logger.debug(f"  Generated {filepath} ({len(content)} bytes)")

                    return FileResult(
                        filepath=filepath,
                        content=content,
                        success=True,
                        tokens_used=tokens,
                        generation_time_ms=gen_time,
                        is_placeholder=is_placeholder,
                    )
                else:
                    error_data = await response.json()
                    error_msg = error_data.get("error", {}).get("message", str(response.status))
                    logger.warning(f"  Failed {filepath}: {error_msg}")
                    return FileResult(
                        filepath=filepath,
                        content=self._placeholder_content(ext),
                        success=False,
                        error=f"API error: {error_msg}",
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


def get_claude_generator(
    model: str | None = None,
    max_parallel: int = 2,
) -> ClaudeGenerator:
    """Factory function to create a ClaudeGenerator."""
    return ClaudeGenerator(model=model, max_parallel=max_parallel)
