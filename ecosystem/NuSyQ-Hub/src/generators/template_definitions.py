"""Template Schema Definition for Universal Project Generator.

Defines the structure, validation, and metadata for all project templates.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

AUTHOR_NUSYQ = "NuSyQ"
REQ_NODEJS_18 = "nodejs>=18"
REQ_PYTHON_39 = "python>=3.9"
EST_TIME_10_15_MINUTES = "10-15 minutes"
KEYWORD_AUTOMATION = "automation"
FILENAME_PACKAGE_JSON = "package.json"


class ProjectType(str, Enum):
    """Project type classification."""

    GAME = "game"
    WEBAPP = "webapp"
    PACKAGE = "package"
    EXTENSION = "extension"
    CLI = "cli"
    LIBRARY = "library"


class LanguageType(str, Enum):
    """Programming languages supported."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GDSCRIPT = "gdscript"
    CSHARP = "csharp"
    RUST = "rust"


class AIProvider(str, Enum):
    """AI providers for code generation."""

    CHATDEV = "chatdev"  # Complex, multi-file projects
    OLLAMA = "ollama"  # Standard projects (qwen2.5-coder)
    CLAUDE = "claude"  # Simple projects / already coded


@dataclass
class FileTemplate:
    """Definition of a file to be generated."""

    path: str  # Relative path: "src/main.py", "package.json"
    template_type: str  # "starter" (provided), "generated" (AI), "copy" (static)
    content_key: str | None = None  # Key in starter_files to load content
    ai_prompt: str | None = None  # Prompt for AI if template_type="generated"
    skip_if_exists: bool = False  # Don't overwrite if file exists


@dataclass
class DependencyInfo:
    """Project dependency specification."""

    name: str  # Package name
    version: str  # Version constraint (e.g., ">=1.0.0")
    category: str  # "core", "dev", "optional"
    note: str | None = None


@dataclass
class HookScript:
    """Post-generation hook to run."""

    name: str  # Identifier
    when: str  # "post_create", "pre_test", "post_generate"
    command: str  # Shell command to execute
    description: str  # Human-readable description
    required: bool = False  # Fail if hook fails
    timeout: int = 300  # Seconds


@dataclass
class IntegrationPoint:
    """Integration with NuSyQ systems."""

    system: str  # "quest", "smart_search", "rpg", "api"
    config: dict[str, Any]  # System-specific config


@dataclass
class ProjectTemplate:
    """Complete project template specification."""

    # Required fields (no defaults)
    template_id: str
    name: str
    type: ProjectType
    language: LanguageType
    description: str
    complexity: int  # 1-10, determines AI provider
    estimated_generation_time: str  # "5-10 minutes"
    author: str
    primary_ai_provider: AIProvider
    starter_files: dict[str, str]  # filename -> content (starter code)

    # Optional fields (with defaults)
    version: str = "1.0.0"
    created: str = "2026-02-04"
    ai_enhancement_available: bool = True
    ai_prompt_override: str | None = None
    file_templates: list[FileTemplate] = field(default_factory=list)
    dependencies: list[DependencyInfo] = field(default_factory=list)
    customizable_options: dict[str, Any] = field(default_factory=dict)
    hooks: list[HookScript] = field(default_factory=list)
    integrations: list[IntegrationPoint] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)  # Tools needed
    validation_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for YAML serialization."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "type": self.type.value,
            "language": self.language.value,
            "description": self.description,
            "complexity": self.complexity,
            "estimated_generation_time": self.estimated_generation_time,
            "author": self.author,
            "version": self.version,
            "created": self.created,
            "primary_ai_provider": self.primary_ai_provider.value,
            "ai_enhancement_available": self.ai_enhancement_available,
            "starter_files": self.starter_files,
            "customizable_options": self.customizable_options,
            "tags": self.tags,
            "keywords": self.keywords,
            "prerequisites": self.prerequisites,
        }


# ============================================================================
# TEMPLATE SPECIFICATIONS (8-12 HIGH-VALUE TEMPLATES)
# ============================================================================

TEMPLATES = {
    # GAMES (2 templates)
    "game_godot_3d": ProjectTemplate(
        template_id="game_godot_3d",
        name="Godot 3D Game",
        type=ProjectType.GAME,
        language=LanguageType.GDSCRIPT,
        description="Full 3D game with Godot 4.x + NuSyQ integration",
        complexity=9,
        estimated_generation_time="30-45 minutes",
        author=AUTHOR_NUSYQ,
        primary_ai_provider=AIProvider.CHATDEV,
        ai_enhancement_available=True,
        starter_files={
            "project.godot": '[gd_resource type="GDScript"]\n# Godot 4.x project file',
            "scenes/Main.gd": "extends Node3D\n# Main scene controller",
            "scenes/Player.gd": "extends CharacterBody3D\n# Player character",
            "scenes/Enemy.gd": "extends CharacterBody3D\n# Enemy AI",
        },
        tags=["game", "godot", "3d", "multiplayer"],
        keywords=["3d", "physics", "networking", "godot"],
        prerequisites=["godot>=4.0"],
    ),
    "game_phaser_web": ProjectTemplate(
        template_id="game_phaser_web",
        name="Phaser Web Game",
        type=ProjectType.GAME,
        language=LanguageType.TYPESCRIPT,
        description="Browser-based 2D game with Phaser 3 + React frontend",
        complexity=7,
        estimated_generation_time="20-30 minutes",
        author=AUTHOR_NUSYQ,
        primary_ai_provider=AIProvider.CHATDEV,
        ai_enhancement_available=True,
        starter_files={
            "src/game.ts": "import Phaser from 'phaser';\n// Game config",
            "src/scenes/MainScene.ts": "export class MainScene extends Phaser.Scene {}",
            "src/index.tsx": "import React from 'react';\n// React app",
        },
        tags=["game", "phaser", "2d", "web", "react"],
        keywords=["browser", "game-dev", "typescript"],
        prerequisites=[REQ_NODEJS_18, "npm"],
    ),
    # WEBAPPS (3 templates)
    "webapp_fastapi_react": ProjectTemplate(
        template_id="webapp_fastapi_react",
        name="FastAPI + React Full-Stack",
        type=ProjectType.WEBAPP,
        language=LanguageType.PYTHON,
        description="Production-ready full-stack with FastAPI backend + React frontend",
        complexity=8,
        estimated_generation_time="15-25 minutes",
        author=AUTHOR_NUSYQ,
        primary_ai_provider=AIProvider.CHATDEV,
        ai_enhancement_available=True,
        starter_files={
            "backend/main.py": "from fastapi import FastAPI\n\napp = FastAPI()",
            "backend/models.py": "from pydantic import BaseModel\n# Data models",
            "frontend/src/App.tsx": "import React from 'react';\n\nexport default function App() {}",
            "docker-compose.yml": "version: '3.8'\nservices:\n  backend:\n    build: ./backend",
        },
        tags=["webapp", "fullstack", "fastapi", "react"],
        keywords=["rest-api", "responsive", "production-ready"],
        prerequisites=["python>=3.11", "nodejs>=18", "docker"],
    ),
    "webapp_nextjs": ProjectTemplate(
        template_id="webapp_nextjs",
        name="Next.js Full-Stack",
        type=ProjectType.WEBAPP,
        language=LanguageType.TYPESCRIPT,
        description="Next.js 14+ with API routes, database, authentication",
        complexity=8,
        estimated_generation_time="15-25 minutes",
        author=AUTHOR_NUSYQ,
        primary_ai_provider=AIProvider.CHATDEV,
        ai_enhancement_available=True,
        starter_files={
            "app/page.tsx": "export default function Home() { return <main></main>; }",
            "app/api/hello/route.ts": "export async function GET() { return Response.json({}); }",
            "env.local.example": "DATABASE_URL=postgresql://...",
        },
        tags=["webapp", "fullstack", "nextjs", "typescript"],
        keywords=["ssr", "ssg", "api-routes", "modern"],
        prerequisites=[REQ_NODEJS_18, "npm"],
    ),
    "webapp_minimal_fastapi": ProjectTemplate(
        template_id="webapp_minimal_fastapi",
        name="Minimal FastAPI REST API",
        type=ProjectType.WEBAPP,
        language=LanguageType.PYTHON,
        description="Simple REST API with FastAPI, perfect for microservices",
        complexity=3,
        estimated_generation_time="5-10 minutes",
        author=AUTHOR_NUSYQ,
        primary_ai_provider=AIProvider.OLLAMA,
        ai_enhancement_available=False,
        starter_files={
            "main.py": 'from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\nasync def root():\n    return {"message": "Hello World"}',
            "requirements.txt": "fastapi==0.104.1\nuvicorn==0.24.0",
            ".env": "ENVIRONMENT=development",
        },
        tags=["webapp", "api", "fastapi", "minimal"],
        keywords=["rest", "microservice"],
        prerequisites=[REQ_PYTHON_39],
    ),
    # PACKAGES (2 templates)
    "package_python": ProjectTemplate(
        template_id="package_python",
        name="Python Package (PyPI-Ready)",
        type=ProjectType.PACKAGE,
        language=LanguageType.PYTHON,
        description="Complete Python package with setuptools, pytest, documentation",
        complexity=4,
        estimated_generation_time=EST_TIME_10_15_MINUTES,
        author=AUTHOR_NUSYQ,
        primary_ai_provider=AIProvider.OLLAMA,
        ai_enhancement_available=True,
        starter_files={
            "src/mymodule/__init__.py": '"""My Python module."""',
            "src/mymodule/core.py": '"""Core functionality."""',
            "setup.py": "from setuptools import setup\n\nsetup(name='mymodule')",
            "pyproject.toml": "[build-system]\nrequires = ['setuptools']",
            "tests/test_core.py": "import pytest\n\ndef test_example():\n    pass",
        },
        tags=["package", "python", "pypi", "library"],
        keywords=["distribution", "reusable", "open-source"],
        prerequisites=[REQ_PYTHON_39, "pip"],
    ),
    "package_npm": ProjectTemplate(
        template_id="package_npm",
        name="NPM Package (npm Registry)",
        type=ProjectType.PACKAGE,
        language=LanguageType.TYPESCRIPT,
        description="ESM-first TypeScript package ready for npm",
        complexity=5,
        estimated_generation_time=EST_TIME_10_15_MINUTES,
        author=AUTHOR_NUSYQ,
        primary_ai_provider=AIProvider.OLLAMA,
        ai_enhancement_available=True,
        starter_files={
            "src/index.ts": "export function greet(name: string): string {}",
            "src/utils.ts": "// Utility functions",
            FILENAME_PACKAGE_JSON: '{"name":"mypackage","version":"0.1.0","type":"module"}',
            "tsconfig.json": '{"compilerOptions":{"target":"ES2020"}}',
            "tests/index.test.ts": "import { describe, it } from 'vitest';",
        },
        tags=["package", "npm", "typescript", "esm"],
        keywords=["distribution", "reusable"],
        prerequisites=[REQ_NODEJS_18, "npm"],
    ),
    # EXTENSIONS (2 templates)
    "extension_vscode": ProjectTemplate(
        template_id="extension_vscode",
        name="VS Code Extension",
        type=ProjectType.EXTENSION,
        language=LanguageType.TYPESCRIPT,
        description="VS Code extension with command palette and UI",
        complexity=6,
        estimated_generation_time="15-20 minutes",
        author=AUTHOR_NUSYQ,
        primary_ai_provider=AIProvider.OLLAMA,
        ai_enhancement_available=True,
        starter_files={
            "src/extension.ts": "import * as vscode from 'vscode';\n\nexport function activate() {}",
            "src/commands.ts": "// Command handlers",
            FILENAME_PACKAGE_JSON: '{"name":"myextension","version":"0.0.1","publisher":"user"}',
            ".vscodeignore": "**/*.ts\n!dist/**",
        },
        tags=["extension", "vscode", "typescript"],
        keywords=[KEYWORD_AUTOMATION, "productivity"],
        prerequisites=[REQ_NODEJS_18, "npm", "vsce"],
    ),
    "extension_browser": ProjectTemplate(
        template_id="extension_browser",
        name="Browser Extension",
        type=ProjectType.EXTENSION,
        language=LanguageType.JAVASCRIPT,
        description="Cross-browser extension for Chrome, Firefox, Edge",
        complexity=5,
        estimated_generation_time=EST_TIME_10_15_MINUTES,
        author=AUTHOR_NUSYQ,
        primary_ai_provider=AIProvider.OLLAMA,
        ai_enhancement_available=True,
        starter_files={
            "manifest.json": '{"manifest_version":3,"name":"My Extension"}',
            "src/popup.html": "<html><body><div id='app'></div></body></html>",
            "src/popup.js": "// Popup logic",
            "src/background.js": "// Background service worker",
        },
        tags=["extension", "browser", "javascript"],
        keywords=[KEYWORD_AUTOMATION, "content-script"],
        prerequisites=["nodejs>=16"],
    ),
    # CLI TOOLS (2 templates)
    "cli_python_click": ProjectTemplate(
        template_id="cli_python_click",
        name="Python CLI (Click)",
        type=ProjectType.CLI,
        language=LanguageType.PYTHON,
        description="Professional CLI tool with Click framework",
        complexity=3,
        estimated_generation_time=EST_TIME_10_15_MINUTES,
        author=AUTHOR_NUSYQ,
        primary_ai_provider=AIProvider.OLLAMA,
        ai_enhancement_available=True,
        starter_files={
            "src/cli.py": "import click\n\n@click.command()\ndef main():\n    pass",
            "setup.py": "from setuptools import setup\n\nsetup(entry_points={'console_scripts': ['mycli=cli:main']})",
            "tests/test_cli.py": "from click.testing import CliRunner",
        },
        tags=["cli", "python", "click", "tool"],
        keywords=["command-line", KEYWORD_AUTOMATION],
        prerequisites=[REQ_PYTHON_39],
    ),
    "cli_node_commander": ProjectTemplate(
        template_id="cli_node_commander",
        name="Node.js CLI (Commander)",
        type=ProjectType.CLI,
        language=LanguageType.TYPESCRIPT,
        description="Modern CLI tool with Commander.js",
        complexity=3,
        estimated_generation_time=EST_TIME_10_15_MINUTES,
        author=AUTHOR_NUSYQ,
        primary_ai_provider=AIProvider.OLLAMA,
        ai_enhancement_available=True,
        starter_files={
            "src/cli.ts": "import { program } from 'commander';\n\nprogram.parse();",
            FILENAME_PACKAGE_JSON: '{"bin":{"mycli":"./dist/cli.js"}}',
            "tsconfig.json": '{"compilerOptions":{"target":"ES2020"}}',
        },
        tags=["cli", "nodejs", "commander", "tool"],
        keywords=["command-line", KEYWORD_AUTOMATION],
        prerequisites=[REQ_NODEJS_18, "npm"],
    ),
}


def get_template(template_id: str) -> ProjectTemplate | None:
    """Retrieve a template by ID."""
    return TEMPLATES.get(template_id)


def list_templates(project_type: ProjectType | None = None) -> list[ProjectTemplate]:
    """List all templates, optionally filtered by type."""
    templates = list(TEMPLATES.values())
    if project_type:
        templates = [t for t in templates if t.type == project_type]
    return sorted(templates, key=lambda t: t.complexity)


def list_template_ids() -> list[str]:
    """Get list of all template IDs."""
    return sorted(TEMPLATES.keys())
