"""src/factories/languages.py - Multi-language support system.

Provides a declarative, extensible language registry for the project factory.
Languages are defined in config/languages.yaml and loaded at runtime.

Usage:
    from src.factories.languages import LanguageRegistry, get_language_registry

    registry = get_language_registry()
    python = registry.get("python")
    print(python.run_cmd)  # "python {entry_point}"

    # Check provider support
    if registry.supports_provider("rust", "ollama"):
        # Generate Rust code with Ollama
        pass
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml  # type: ignore[import]


@dataclass
class LanguageComments:
    """Comment syntax for a language."""

    single: str = "#"
    multi_start: str = '"""'
    multi_end: str = '"""'


@dataclass
class Language:
    """Represents a programming language configuration.

    Loaded from config/languages.yaml at runtime.
    """

    name: str
    display_name: str
    extensions: list[str]
    entry_file: str
    code_fence: str
    providers: list[str]

    # Optional fields
    dependency_file: str | None = None
    install_cmd: str | None = None
    run_cmd: str = ""
    build_cmd: str | None = None
    package_cmd: str | None = None
    capabilities: list[str] = field(default_factory=list)
    comments: LanguageComments = field(default_factory=LanguageComments)
    notes: str | None = None

    # Computed for backward compatibility with LANGUAGE_PROFILES
    @property
    def fallback_entry(self) -> str:
        """Alias for entry_file (backward compatibility)."""
        return self.entry_file

    def to_profile_dict(self) -> dict[str, str]:
        """Convert to the old LANGUAGE_PROFILES format for backward compatibility.

        Returns dict with: fallback_entry, dependency_file, install_cmd, run_cmd, code_fence
        """
        return {
            "fallback_entry": self.entry_file,
            "dependency_file": self.dependency_file or "",
            "install_cmd": self.install_cmd or "",
            "run_cmd": self.run_cmd,
            "code_fence": self.code_fence,
        }

    def format_run_cmd(self, entry_point: str | None = None) -> str:
        """Format run command with entry point substitution."""
        ep = entry_point or self.entry_file
        return self.run_cmd.format(entry_point=ep)

    def format_package_cmd(self, entry_point: str | None = None) -> str:
        """Format package command with entry point substitution."""
        if not self.package_cmd:
            return ""
        ep = entry_point or self.entry_file
        return self.package_cmd.format(entry_point=ep)


class LanguageRegistry:
    """Registry of supported programming languages.

    Loads language definitions from config/languages.yaml and provides
    lookup, validation, and provider compatibility checking.
    """

    _instance: Optional["LanguageRegistry"] = None

    def __init__(self, config_path: str | None = None):
        """Initialize the registry from YAML config.

        Args:
            config_path: Path to languages.yaml (default: config/languages.yaml)
        """
        if config_path is None:
            # Default to NuSyQ-Hub/config/languages.yaml
            config_path = str(Path(__file__).parent.parent.parent / "config" / "languages.yaml")

        self._config_path = Path(config_path)
        self._languages: dict[str, Language] = {}
        self._provider_notes: dict[str, dict[str, Any]] = {}
        self._template_recommendations: dict[str, dict[str, Any]] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load languages from YAML configuration."""
        if not self._config_path.exists():
            # Fall back to hardcoded defaults if config missing
            self._load_defaults()
            return

        with open(self._config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Load languages
        for name, lang_data in config.get("languages", {}).items():
            self._languages[name] = self._parse_language(name, lang_data)

        # Load provider notes
        self._provider_notes = config.get("provider_notes", {})

        # Load template recommendations
        self._template_recommendations = config.get("template_recommendations", {})

    def _parse_language(self, name: str, data: dict[str, Any]) -> Language:
        """Parse a language definition from YAML data."""
        # Parse comments
        comments_data = data.get("comments", {})
        comments = LanguageComments(
            single=comments_data.get("single", "#"),
            multi_start=comments_data.get("multi_start", '"""'),
            multi_end=comments_data.get("multi_end", '"""'),
        )

        return Language(
            name=name,
            display_name=data.get("display_name", name.title()),
            extensions=data.get("extensions", [f".{name}"]),
            entry_file=data.get("entry_file", "main.py"),
            dependency_file=data.get("dependency_file"),
            install_cmd=data.get("install_cmd"),
            run_cmd=data.get("run_cmd", f"{name} {{entry_point}}"),
            build_cmd=data.get("build_cmd"),
            package_cmd=data.get("package_cmd"),
            code_fence=data.get("code_fence", name),
            providers=data.get("providers", ["ollama"]),
            capabilities=data.get("capabilities", []),
            comments=comments,
            notes=data.get("notes"),
        )

    def _load_defaults(self) -> None:
        """Load hardcoded defaults if YAML config is missing."""
        defaults = {
            "python": Language(
                name="python",
                display_name="Python",
                extensions=[".py"],
                entry_file="main.py",
                dependency_file="requirements.txt",
                install_cmd="pip install -r requirements.txt",
                run_cmd="python {entry_point}",
                package_cmd="pyinstaller --onefile {entry_point}",
                code_fence="python",
                providers=["chatdev", "ollama", "claude", "openai"],
            ),
            "javascript": Language(
                name="javascript",
                display_name="JavaScript",
                extensions=[".js", ".mjs"],
                entry_file="index.js",
                dependency_file="package.json",
                install_cmd="npm install",
                run_cmd="node {entry_point}",
                code_fence="javascript",
                providers=["ollama", "claude", "openai"],
            ),
        }
        self._languages = defaults

    def get(self, name: str) -> Language:
        """Get a language by name.

        Args:
            name: Language name (case-insensitive)

        Returns:
            Language object

        Raises:
            KeyError: If language not found
        """
        key = name.lower()
        if key not in self._languages:
            raise KeyError(
                f"Language '{name}' not found. Available: {', '.join(self._languages.keys())}"
            )
        return self._languages[key]

    def get_or_default(self, name: str, default: str = "python") -> Language:
        """Get a language by name, falling back to default if not found.

        Args:
            name: Language name (case-insensitive)
            default: Default language name if not found

        Returns:
            Language object
        """
        try:
            return self.get(name)
        except KeyError:
            return self.get(default)

    def get_profile(self, name: str) -> dict[str, str]:
        """Get a language profile dict (backward compatible with LANGUAGE_PROFILES).

        Args:
            name: Language name

        Returns:
            Dict with fallback_entry, dependency_file, install_cmd, run_cmd, code_fence
        """
        return self.get_or_default(name).to_profile_dict()

    def list_all(self) -> list[Language]:
        """Get all registered languages."""
        return list(self._languages.values())

    def list_names(self) -> list[str]:
        """Get all language names."""
        return list(self._languages.keys())

    def exists(self, name: str) -> bool:
        """Check if a language exists."""
        return name.lower() in self._languages

    def supports_provider(self, language: str, provider: str) -> bool:
        """Check if a provider supports a language.

        Args:
            language: Language name
            provider: Provider name (chatdev, ollama, claude, openai)

        Returns:
            True if provider supports the language
        """
        try:
            lang = self.get(language)
            return provider.lower() in [p.lower() for p in lang.providers]
        except KeyError:
            return False

    def get_providers_for_language(self, language: str) -> list[str]:
        """Get list of providers that support a language."""
        try:
            return self.get(language).providers
        except KeyError:
            return []

    def get_languages_for_provider(self, provider: str) -> list[Language]:
        """Get all languages supported by a provider."""
        return [
            lang
            for lang in self._languages.values()
            if provider.lower() in [p.lower() for p in lang.providers]
        ]

    def get_by_extension(self, ext: str) -> Language | None:
        """Find a language by file extension.

        Args:
            ext: File extension (with or without leading dot)

        Returns:
            Language object or None if not found
        """
        if not ext.startswith("."):
            ext = f".{ext}"

        for lang in self._languages.values():
            if ext in lang.extensions:
                return lang
        return None

    def get_recommendation(self, template_type: str) -> dict[str, Any]:
        """Get language recommendation for a template type.

        Args:
            template_type: Type of template (game, cli, api, web)

        Returns:
            Dict with primary, alternatives, and notes
        """
        return self._template_recommendations.get(
            template_type,
            {
                "primary": "python",
                "alternatives": [],
                "notes": "Default to Python for unknown template types",
            },
        )

    def get_provider_info(self, provider: str) -> dict[str, Any]:
        """Get information about a provider's capabilities."""
        return self._provider_notes.get(provider, {})

    def register(self, language: Language) -> None:
        """Register a new language at runtime.

        Args:
            language: Language object to register
        """
        self._languages[language.name.lower()] = language

    def reload(self) -> None:
        """Reload configuration from YAML file."""
        self._languages.clear()
        self._provider_notes.clear()
        self._template_recommendations.clear()
        self._load_config()

    @classmethod
    def get_instance(cls, config_path: str | None = None) -> "LanguageRegistry":
        """Get singleton instance of LanguageRegistry.

        Args:
            config_path: Path to config (only used on first call)

        Returns:
            LanguageRegistry singleton
        """
        if cls._instance is None:
            cls._instance = cls(config_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        cls._instance = None


# Convenience function for getting the singleton
def get_language_registry() -> LanguageRegistry:
    """Get the global LanguageRegistry instance."""
    return LanguageRegistry.get_instance()


# Backward-compatible function that returns LANGUAGE_PROFILES-style dict
def get_language_profiles() -> dict[str, dict[str, str]]:
    """Get all language profiles in LANGUAGE_PROFILES format.

    For backward compatibility with code expecting the old dict format.
    """
    registry = get_language_registry()
    return {name: registry.get_profile(name) for name in registry.list_names()}
