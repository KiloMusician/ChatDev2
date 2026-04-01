"""src/factories/generators/base.py - Abstract Generator Interface.

Defines the pluggable interface for AI code generation providers.
All generators (Ollama, Claude, OpenAI, ChatDev) implement this interface.

Design Goals:
- Unified interface for all AI providers
- Support for parallel file generation
- Language-aware generation
- Structured results with diagnostics
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.factories.templates import BaseProjectTemplate


@dataclass
class FileResult:
    """Result of generating a single file."""

    filepath: str
    content: str
    success: bool = True
    error: str | None = None
    tokens_used: int = 0
    generation_time_ms: int = 0
    is_placeholder: bool = False

    @property
    def size_bytes(self) -> int:
        """Get content size in bytes."""
        return len(self.content.encode("utf-8"))


@dataclass
class GenerationContext:
    """Context for code generation request."""

    project_name: str
    description: str
    template: BaseProjectTemplate
    output_path: Path

    # Optional overrides
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout_seconds: int = 180

    # Language info (auto-populated if not set)
    language: str | None = None
    entry_point: str | None = None

    # Generation hints
    hints: list[str] = field(default_factory=list)

    # Context from already-generated files (for coherent multi-file generation)
    generated_files: dict[str, str] = field(default_factory=dict)

    # Feature flags
    parallel: bool = True  # Enable parallel file generation
    include_tests: bool = True
    include_docs: bool = True
    dry_run: bool = False  # If True, don't write files, just simulate

    def __post_init__(self):
        """Populate language info from template if not set."""
        if self.language is None:
            self.language = getattr(self.template, "language", "python")
        if not self.hints and hasattr(self.template, "generation_hints"):
            self.hints = self.template.generation_hints or []


@dataclass
class GenerationResult:
    """Result of generating a complete project."""

    project_name: str
    output_path: Path
    provider: str  # "ollama", "claude", "openai", "chatdev"
    model: str

    # File results
    files: list[FileResult] = field(default_factory=list)

    # Aggregated stats
    total_tokens: int = 0
    total_files: int = 0
    successful_files: int = 0
    placeholder_files: int = 0
    failed_files: int = 0

    # Timing
    start_time: datetime | None = None
    end_time: datetime | None = None
    total_time_ms: int = 0

    # Cost estimate
    estimated_cost_usd: float = 0.0

    # Errors
    errors: list[dict[str, str]] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

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

    def add_file(self, file_result: FileResult) -> None:
        """Add a file result and update stats."""
        self.files.append(file_result)
        self.total_files += 1
        self.total_tokens += file_result.tokens_used

        if file_result.success:
            self.successful_files += 1
            if file_result.is_placeholder:
                self.placeholder_files += 1
        else:
            self.failed_files += 1
            if file_result.error:
                self.errors.append(
                    {
                        "file": file_result.filepath,
                        "error": file_result.error,
                    }
                )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "project_name": self.project_name,
            "output_path": str(self.output_path),
            "provider": self.provider,
            "model": self.model,
            "total_files": self.total_files,
            "successful_files": self.successful_files,
            "placeholder_files": self.placeholder_files,
            "failed_files": self.failed_files,
            "success_rate": self.success_rate,
            "total_tokens": self.total_tokens,
            "total_time_ms": self.total_time_ms,
            "estimated_cost_usd": self.estimated_cost_usd,
            "errors": self.errors,
            "metadata": self.metadata,
        }


class AbstractGenerator(ABC):
    """Abstract base class for AI code generators.

    All generators (Ollama, Claude, OpenAI, ChatDev) implement this interface.
    Provides a unified API for the ProjectFactory to use any provider.

    Subclasses must implement:
    - generate(): Main generation method
    - generate_file(): Single file generation
    - supports_language(): Language compatibility check
    - provider_name: Provider identifier
    - get_capabilities(): Provider capability info
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'ollama', 'claude', 'openai')."""
        pass

    @abstractmethod
    async def generate(
        self,
        context: GenerationContext,
    ) -> GenerationResult:
        """Generate a complete project.

        Args:
            context: Generation context with template, description, etc.

        Returns:
            GenerationResult with all file results and stats
        """
        pass

    @abstractmethod
    async def generate_file(
        self,
        filepath: str,
        description: str,
        context: GenerationContext,
    ) -> FileResult:
        """Generate a single file.

        Args:
            filepath: Target file path (relative to project root)
            description: Description of what the file should contain
            context: Generation context

        Returns:
            FileResult with content or error
        """
        pass

    @abstractmethod
    def supports_language(self, language: str) -> bool:
        """Check if this generator supports a language.

        Args:
            language: Language name (e.g., 'python', 'rust')

        Returns:
            True if language is supported
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> dict[str, Any]:
        """Get provider capabilities.

        Returns dict with:
        - supported_languages: List of supported languages
        - max_tokens: Maximum tokens per request
        - supports_parallel: Whether parallel generation is supported
        - cost_per_1k_tokens: Cost estimate
        - requires_api_key: Whether API key is needed
        - local: Whether provider runs locally
        """
        pass

    def is_available(self) -> bool:
        """Check if the generator is currently available.

        Override in subclasses to check API keys, service availability, etc.
        """
        return True

    def get_supported_languages(self) -> set[str]:
        """Get set of supported language names."""
        caps = self.get_capabilities()
        return set(caps.get("supported_languages", []))

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost in USD for given token count."""
        caps = self.get_capabilities()
        cost_per_1k = float(caps.get("cost_per_1k_tokens", 0.0) or 0.0)
        return (tokens / 1000) * cost_per_1k

    def _build_project_context(self, context: GenerationContext) -> str:
        """Build context string for LLM prompt."""
        template = context.template
        lines = [
            f"Project: {context.project_name}",
            f"Description: {context.description}",
            f"Type: {template.type}",
            f"Language: {context.language}",
        ]

        if template.dependencies:
            lines.append(f"Dependencies: {', '.join(template.dependencies)}")

        if context.entry_point:
            lines.append(f"Entry point: {context.entry_point}")

        if hasattr(template, "runtime_profile"):
            lines.append(f"Runtime: {template.runtime_profile}")

        if context.hints:
            lines.append("\nGeneration hints:")
            for hint in context.hints:
                lines.append(f"- {hint}")

        if context.generated_files:
            lines.append("\nAlready generated files:")
            for filepath, _snippet in list(context.generated_files.items())[:5]:
                lines.append(f"- {filepath}")

        return "\n".join(lines)

    def _build_file_prompt(
        self,
        filepath: str,
        description: str,
        context: GenerationContext,
    ) -> str:
        """Build prompt for generating a specific file."""
        project_context = self._build_project_context(context)

        # Get code fence from language registry
        try:
            from src.factories.languages import get_language_registry

            registry = get_language_registry()
            lang = registry.get_or_default(context.language or "python")
            code_fence = lang.code_fence
        except Exception:
            code_fence = context.language or "python"

        prompt = f"""{project_context}

Generate the file: {filepath}
Purpose: {description}

Requirements:
- Write complete, working code for {filepath}
- Follow {context.language} best practices and conventions
- Include necessary imports and dependencies
- Add clear comments for complex logic
- Make the code production-ready

Output ONLY the file contents wrapped in a {code_fence} code block.
Do not include any explanation before or after the code block.

```{code_fence}
"""
        return prompt

    def _clean_code_output(self, code: str, _file_ext: str) -> str:
        """Clean LLM output to extract just the code."""
        import re

        # Remove markdown code fences
        # Handle ```language\n...\n``` pattern
        fence_pattern = r"^```\w*\n?(.*?)```\s*$"
        match = re.search(fence_pattern, code, re.DOTALL)
        if match:
            code = match.group(1)

        # Also handle leading/trailing whitespace
        code = code.strip()

        # If still has fence markers, try more aggressive cleanup
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)

        return code

    def _placeholder_content(self, ext: str) -> str:
        """Get placeholder content for a file type."""
        placeholders = {
            ".py": "# Placeholder - generation pending\npass\n",
            ".js": "// Placeholder - generation pending\n",
            ".ts": "// Placeholder - generation pending\n",
            ".rs": "// Placeholder - generation pending\nfn main() {}\n",
            ".go": "package main\n\n// Placeholder - generation pending\nfunc main() {}\n",
            ".cs": "// Placeholder - generation pending\nclass Program { static void Main() {} }\n",
            ".gd": "extends Node\n# Placeholder - generation pending\n",
            ".lua": "-- Placeholder - generation pending\n",
            ".md": "# Placeholder\n\n_Generation pending._\n",
            ".json": "{}\n",
            ".yaml": "# Placeholder\n",
            ".yml": "# Placeholder\n",
            ".toml": "# Placeholder\n",
        }
        return placeholders.get(ext.lower(), "# Placeholder\n")
