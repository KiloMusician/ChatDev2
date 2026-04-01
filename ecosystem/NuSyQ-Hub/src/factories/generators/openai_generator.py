"""src/factories/generators/openai_generator.py - OpenAI GPT Generator.

Implements the AbstractGenerator interface for OpenAI GPT API.
Supports multi-file generation with parallel processing.

Features:
- Async parallel file generation
- Model selection (GPT-4, GPT-4 Turbo, GPT-3.5)
- Rate limiting for API compliance
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


class OpenAIGenerator(AbstractGenerator):
    """OpenAI GPT generator with async support.

    Uses OpenAI's Chat Completions API for code generation.
    Requires OPENAI_API_KEY environment variable.
    """

    API_BASE = "https://api.openai.com/v1"

    # Available models
    MODELS: ClassVar[dict] = {
        "gpt4": "gpt-4",
        "gpt4-turbo": "gpt-4-turbo-preview",
        "gpt4o": "gpt-4o",
        "gpt4o-mini": "gpt-4o-mini",
        "gpt35": "gpt-3.5-turbo",
    }

    DEFAULT_MODEL = "gpt-4-turbo-preview"

    # Cost per 1K tokens (approximate)
    COSTS: ClassVar[dict] = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }

    # Languages OpenAI excels at
    SUPPORTED_LANGUAGES: ClassVar[set] = {
        "python",
        "javascript",
        "typescript",
        "go",
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
        api_key: str | None = None,
        model: str | None = None,
        max_parallel: int = 3,
        timeout_seconds: int = 90,
    ):
        """Initialize OpenAI generator.

        Args:
            api_key: OpenAI API key (or use OPENAI_API_KEY env)
            model: Model to use (gpt4, gpt4-turbo, gpt35, or full model name)
            max_parallel: Max concurrent requests
            timeout_seconds: Request timeout
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
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
        return "openai"

    def supports_language(self, language: str) -> bool:
        return language.lower() in self.SUPPORTED_LANGUAGES

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "supported_languages": list(self.SUPPORTED_LANGUAGES),
            "max_tokens": 4096,
            "supports_parallel": True,
            "cost_per_1k_tokens": self.COSTS.get(self.model, {}).get("output", 0.03),
            "requires_api_key": True,
            "local": False,
            "models": list(self.MODELS.values()),
            "default_model": self.model,
        }

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    async def generate(self, context: GenerationContext) -> GenerationResult:
        """Generate a complete project using OpenAI.

        Args:
            context: Generation context with template and settings

        Returns:
            GenerationResult with all files and stats
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")

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

        # Generate files
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
                f"OpenAI factory: {context.project_name} | files={result.total_files}"
                f" status={_status} time={result.total_time_ms}ms",
                level="INFO",
                source="openai_generator",
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
            await asyncio.sleep(0.3)  # Rate limiting
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

            await asyncio.sleep(0.2)

        return results

    async def generate_file(
        self,
        filepath: str,
        description: str,
        context: GenerationContext,
    ) -> FileResult:
        """Generate a single file using OpenAI API.

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

        logger.debug(f"Generating {filepath} with OpenAI...")

        prompt = self._build_file_prompt(filepath, description, context)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "max_tokens": context.max_tokens,
            "temperature": context.temperature,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert programmer. Generate clean, working, production-ready code. Output only the file contents in a code block.",
                },
                {"role": "user", "content": prompt},
            ],
        }

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    f"{self.API_BASE}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=context.timeout_seconds),
                ) as response,
            ):
                if response.status == 200:
                    data = await response.json()
                    raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    usage = data.get("usage", {})
                    tokens = usage.get("total_tokens", 0)

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


def get_openai_generator(
    model: str | None = None,
    max_parallel: int = 3,
) -> OpenAIGenerator:
    """Factory function to create an OpenAIGenerator."""
    return OpenAIGenerator(model=model, max_parallel=max_parallel)
