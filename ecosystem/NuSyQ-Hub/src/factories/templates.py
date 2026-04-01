"""Project Template System - Flexible, JSON/YAML-based definitions.

Templates define project structure without rigid code constraints.
Supports: games (Godot, Unity), CLIs (Python, Node), libraries (packages).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import]


@dataclass
class BaseProjectTemplate:
    """Base template for all project types."""

    name: str
    type: str  # "game", "cli", "library", "custom"
    language: str  # "python", "javascript", "gdscript", "csharp"
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    file_structure: dict[str, str] = field(default_factory=dict)
    runtime_profile: str = (
        "native_terminal"  # electron_local|electron_web_wrapper|godot_export|native_terminal
    )
    feature_flags: dict[str, bool] = field(default_factory=dict)

    # AI generation hints
    complexity: int = 5  # 1-10 scale, determines AI provider selection
    requires_multifile: bool = True  # ChatDev if True, Ollama if False
    generation_hints: list[str] = field(default_factory=list)  # Hints for AI code generation

    def to_dict(self) -> dict[str, Any]:
        """Serialize template to dict."""
        return {
            "name": self.name,
            "type": self.type,
            "language": self.language,
            "description": self.description,
            "metadata": self.metadata,
            "dependencies": self.dependencies,
            "file_structure": self.file_structure,
            "runtime_profile": self.runtime_profile,
            "feature_flags": self.feature_flags,
            "complexity": self.complexity,
            "requires_multifile": self.requires_multifile,
            "generation_hints": self.generation_hints,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseProjectTemplate":
        """Deserialize template from dict."""
        return cls(**dict(data))


@dataclass
class BaseGame(BaseProjectTemplate):
    """Game-specific template (Godot, Unity, Pygame, etc.)."""

    engine: str | None = None  # "godot", "unity", "pygame", "terminal", None
    engine_version: str | None = None
    target_platforms: list[str] = field(default_factory=lambda: ["windows", "linux"])
    genre: str | None = None  # "cyberpunk", "rpg", "platformer", "roguelike", etc.

    # Godot-specific
    godot_translate: bool = False  # Python → GDScript translation
    godot_project_path: Path | None = None

    def __post_init__(self):
        """Set game-specific defaults."""
        if self.type != "game":
            self.type = "game"
        self.complexity = max(self.complexity, 6)  # Games are complex
        self.requires_multifile = True  # Always use ChatDev for games

        # Infer runtime profile for common game stacks when not explicitly set.
        runtime_profile = (self.runtime_profile or "").strip().lower()
        if runtime_profile in {"", "native_terminal"}:
            if self.engine == "godot" or self.language == "gdscript":
                self.runtime_profile = "godot_export"
            elif self.language in {"javascript", "typescript"}:
                self.runtime_profile = "electron_local"

        # Add engine to metadata
        if self.engine:
            self.metadata["engine"] = self.engine
            self.metadata["engine_version"] = self.engine_version
            self.metadata["godot_translate"] = self.godot_translate

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseGame":
        """Deserialize game template from dict."""
        payload = dict(data)

        # Extract game-specific fields
        game_fields = {
            "engine": payload.pop("engine", None),
            "engine_version": payload.pop("engine_version", None),
            "target_platforms": payload.pop("target_platforms", ["windows", "linux"]),
            "genre": payload.pop("genre", None),
            "godot_translate": payload.pop("godot_translate", False),
        }
        # Remove fields not in base dataclass (may come from templates)
        payload.pop("godot_project_path", None)
        # Move entry_point and packaging to metadata if present (CLI-style fields)
        entry_point = payload.pop("entry_point", None)
        packaging = payload.pop("packaging", None)
        if entry_point:
            payload.setdefault("metadata", {})["entry_point"] = entry_point
        if packaging:
            payload.setdefault("metadata", {})["packaging"] = packaging
        # Remove any other CLI-specific fields that may leak in
        payload.pop("cli_framework", None)
        return cls(**payload, **game_fields)


@dataclass
class BaseCLI(BaseProjectTemplate):
    """CLI application template (Python, Node, Go)."""

    entry_point: str = "main.py"
    cli_framework: str | None = None  # "click", "argparse", "commander", etc.
    packaging: str | None = None  # "pyinstaller", "pkg", None

    def __post_init__(self):
        """Set CLI-specific defaults."""
        if self.type != "cli":
            self.type = "cli"
        self.complexity = max(self.complexity, 3)  # CLIs are moderate
        self.metadata["entry_point"] = self.entry_point
        self.metadata["cli_framework"] = self.cli_framework


@dataclass
class BaseLibrary(BaseProjectTemplate):
    """Library/package template (Python package, npm package, Rust crate)."""

    package_name: str = ""
    license: str = "MIT"
    publish_registry: str | None = None  # "pypi", "npm", "crates.io"
    include_tests: bool = True

    def __post_init__(self):
        """Set library-specific defaults."""
        if self.type != "library":
            self.type = "library"
        self.complexity = max(self.complexity, 4)  # Libraries need structure
        self.requires_multifile = True  # Use ChatDev for proper packaging
        self.metadata["package_name"] = self.package_name or self.name
        self.metadata["license"] = self.license


@dataclass
class BaseWebApp(BaseProjectTemplate):
    """Web application template (Flask, FastAPI, Django).

    OmniTag: [webapp, web, api, backend, fullstack]

    Supports common web frameworks with integrated features:
    - Authentication (JWT, OAuth, session-based)
    - Database integration (SQLAlchemy, async support)
    - Docker containerization
    - CI/CD pipeline generation
    """

    framework: str | None = None  # "flask", "fastapi", "django"
    auth_method: str | None = None  # "jwt", "oauth", "session"
    database: str | None = None  # "sqlite", "postgres", "mysql", "mongo"
    include_docker: bool = True
    include_ci: bool = False
    entry_point: str = "src/app.py"
    async_support: bool = False

    # Web-specific fields
    dev_dependencies: list[str] = field(default_factory=list)
    hooks: dict[str, list[str]] = field(default_factory=dict)
    integrations: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self):
        """Set webapp-specific defaults."""
        if self.type != "webapp":
            self.type = "webapp"
        self.complexity = max(self.complexity, 5)  # Web apps are moderately complex
        self.requires_multifile = True  # Always use ChatDev for web apps

        # Add framework info to metadata
        self.metadata["framework"] = self.framework
        self.metadata["auth_method"] = self.auth_method
        self.metadata["database"] = self.database
        self.metadata["async_support"] = self.async_support
        self.metadata["entry_point"] = self.entry_point

    def to_dict(self) -> dict[str, Any]:
        """Serialize webapp template to dict."""
        data = super().to_dict()
        data.update(
            {
                "framework": self.framework,
                "auth_method": self.auth_method,
                "database": self.database,
                "include_docker": self.include_docker,
                "include_ci": self.include_ci,
                "entry_point": self.entry_point,
                "async_support": self.async_support,
                "dev_dependencies": self.dev_dependencies,
                "hooks": self.hooks,
                "integrations": self.integrations,
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseWebApp":
        """Deserialize webapp template from dict."""
        payload = dict(data)
        metadata = payload.get("metadata", {}) or {}
        integrations_raw = payload.pop("integrations", {})
        if isinstance(integrations_raw, list):
            normalized_integrations: dict[str, bool] = {}
            for item in integrations_raw:
                if isinstance(item, dict):
                    for key, value in item.items():
                        normalized_integrations[str(key)] = bool(value)
            integrations_raw = normalized_integrations

        # Extract webapp-specific fields
        webapp_fields = {
            "framework": payload.pop("framework", metadata.get("framework")),
            "auth_method": payload.pop("auth_method", metadata.get("auth_method")),
            "database": payload.pop("database", metadata.get("database")),
            "include_docker": payload.pop("include_docker", True),
            "include_ci": payload.pop("include_ci", False),
            "entry_point": payload.pop("entry_point", "src/app.py"),
            "async_support": payload.pop(
                "async_support",
                bool(metadata.get("async", metadata.get("async_support", False))),
            ),
            "dev_dependencies": payload.pop("dev_dependencies", []),
            "hooks": payload.pop("hooks", {}),
            "integrations": integrations_raw,
        }
        # Remove version if present (not in base dataclass)
        payload.pop("version", None)
        return cls(**payload, **webapp_fields)


def load_template(path_or_name: str | Path) -> BaseProjectTemplate:
    """Load template from YAML or JSON file."""
    # Handle both string names and Path objects
    if isinstance(path_or_name, str):
        # Try to resolve as template name first
        config_path = Path("config/templates")
        for suffix in [".yaml", ".yml", ".json"]:
            candidate = config_path / f"{path_or_name}{suffix}"
            if candidate.exists():
                path = candidate
                break
        else:
            # If not found as name, treat as file path
            path = Path(path_or_name)
    else:
        path = path_or_name

    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")

    suffix = path.suffix.lower()
    with open(path, encoding="utf-8") as f:
        if suffix == ".yaml" or suffix == ".yml":
            data = yaml.safe_load(f)
        elif suffix == ".json":
            data = json.load(f)
        else:
            raise ValueError(f"Unsupported template format: {suffix}")

    # Determine template class based on type
    template_type = data.get("type", "project")
    if template_type == "game":
        return BaseGame.from_dict(data)
    elif template_type == "cli":
        return BaseCLI.from_dict(data)
    elif template_type == "library":
        return BaseLibrary.from_dict(data)
    elif template_type == "webapp":
        return BaseWebApp.from_dict(data)
    else:
        return BaseProjectTemplate.from_dict(data)


def save_template(template: BaseProjectTemplate, path: Path) -> None:
    """Save template to YAML or JSON file."""
    suffix = path.suffix.lower()
    data = template.to_dict()

    with open(path, "w", encoding="utf-8") as f:
        if suffix == ".yaml" or suffix == ".yml":
            yaml.safe_dump(data, f, default_flow_style=False)
        elif suffix == ".json":
            json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported template format: {suffix}")
