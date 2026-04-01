"""Project Factory - Template-based project generation.

Creates games, programs, and packages from templates + AI generation.
Orchestrates entire pipeline: template → AI generation → artifact registration.
"""

import json
import logging
import os
import re
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    from datetime import UTC
except ImportError:  # pragma: no cover - Python 3.10 fallback
    UTC = timezone.utc  # noqa: UP017

try:
    import requests
except ImportError:  # pragma: no cover - optional runtime dependency
    requests = None  # type: ignore[assignment]

from src.factories.ai_orchestrator import AIOrchestrator, AIProviderType
from src.factories.artifact_registry import ArtifactRegistry
from src.factories.languages import get_language_registry
from src.factories.packaging_adapters import (PackagingContext,
                                              build_runtime_packaging_adapter)
from src.factories.templates import (BaseGame, BaseProjectTemplate,
                                     load_template)

logger = logging.getLogger(__name__)


# LANGUAGE_PROFILES is now loaded dynamically from config/languages.yaml
# via the LanguageRegistry. This dict is kept for backward compatibility
# but delegates to the registry at runtime.
def _get_language_profiles() -> dict[str, dict[str, str]]:
    """Get language profiles from the LanguageRegistry.

    This replaces the hardcoded LANGUAGE_PROFILES dict with a dynamic
    loader that reads from config/languages.yaml.
    """
    try:
        from src.factories.languages import get_language_profiles

        return get_language_profiles()
    except Exception:
        # Fallback if registry fails to load
        return {
            "python": {
                "fallback_entry": "main.py",
                "dependency_file": "requirements.txt",
                "install_cmd": "pip install -r requirements.txt",
                "run_cmd": "python {entry_point}",
                "code_fence": "python",
            },
        }


# For backward compatibility, create a lazy-loading proxy
class _LanguageProfilesProxy(dict):
    """Lazy-loading dict that fetches from LanguageRegistry on first access."""

    _loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self.update(_get_language_profiles())
            self._loaded = True

    def __getitem__(self, key):
        self._ensure_loaded()
        return super().__getitem__(key)

    def get(self, key, default=None):
        self._ensure_loaded()
        return super().get(key, default)

    def __contains__(self, key):
        self._ensure_loaded()
        return super().__contains__(key)

    def keys(self):
        self._ensure_loaded()
        return super().keys()


LANGUAGE_PROFILES: dict[str, dict[str, str]] = _LanguageProfilesProxy()

RUNTIME_PROFILES = {
    "electron_local",
    "electron_web_wrapper",
    "godot_export",
    "native_terminal",
}

DEFAULT_GAME_FEATURE_FLAGS = {
    "data_pipeline": True,
    "event_router": True,
    "save_migration": True,
    "modding_api": True,
}

FOREIGN_WORKSPACE_MARKERS = (
    "steamapps\\common",
    "steamapps/common",
)


@dataclass
class GeneratedProject:
    """Result of factory project generation."""

    name: str
    type: str
    version: str
    output_path: Path
    ai_provider: str
    template_name: str
    template_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    chatdev_warehouse_path: Path | None = None
    token_cost: float = 0.0
    model_used: str | None = None


class ProjectFactory:
    """Factory for generating projects from templates and AI."""

    def __init__(self, template_dir: Path | None = None):
        """Initialize factory.

        Args:
            template_dir: Directory containing project templates (default: config/templates)
        """
        if template_dir is None:
            # Default to NuSyQ-Hub/config/templates
            template_dir = Path(__file__).parent.parent.parent / "config" / "templates"

        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.registry = ArtifactRegistry()
        self.orchestrator = AIOrchestrator()
        self._last_generation_diagnostics: dict[str, Any] = {}
        self._provider_policy_path = (
            Path(__file__).parent.parent.parent / "config" / "factory_provider_policy.json"
        )

        # Default output location
        self.output_root = Path(__file__).parent.parent.parent / "projects" / "generated"
        self.output_root.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        name: str,
        template: str = "default_game",
        version: str = "1.0.0",
        description: str = "",
        ai_provider: str | None = None,
        custom_template: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        auto_register: bool = True,
    ) -> GeneratedProject:
        """Create a new project from template.

        Args:
            name: Project name
            template: Template name (e.g., "default_game")
            version: Version string
            description: Project description
            ai_provider: Force specific provider ("chatdev", "ollama", etc.)
            custom_template: Inline template dict (overrides template file)
            metadata: Additional metadata to store
            auto_register: Automatically register in artifact registry

        Returns:
            GeneratedProject with output path and metadata
        """
        # Load or use custom template
        if custom_template:
            template_obj = BaseProjectTemplate.from_dict(custom_template)
            template_path = None
        else:
            template_path = self.template_dir / f"{template}.yaml"
            if not template_path.exists():
                raise FileNotFoundError(
                    f"Template not found: {template_path}. Available templates: {self._list_templates()}"
                )
            template_obj = load_template(template_path)

        # Select AI provider
        selected_provider = self.orchestrator.select_provider(
            complexity=template_obj.complexity,
            requires_multifile=template_obj.requires_multifile,
            user_preference=ai_provider,
        )
        self._last_generation_diagnostics = {}
        selected_provider, provider_policy_reason = self._apply_provider_policy_overrides(
            selected_provider, template_obj
        )

        # Generate project files using selected provider
        output_dir, model_used, token_cost, warehouse_path, provider_used = self._generate_project(
            name, template_obj, selected_provider, description
        )

        # Create result object
        merged_metadata = dict(metadata or {})
        diagnostics_entry_point = self._last_generation_diagnostics.get("entry_point")
        if not diagnostics_entry_point:
            language = (template_obj.language or "python").lower()
            profile = self._language_profile(language)
            file_structure = getattr(template_obj, "file_structure", {}) or {
                profile["fallback_entry"]: "Main entry point"
            }
            diagnostics_entry_point = self._detect_entry_point(template_obj, file_structure)
        generation_diagnostics = self._build_generation_diagnostics(
            selected_provider=selected_provider.value,
            used_provider=provider_used.value,
            output_path=output_dir,
            template=template_obj,
            entry_point=diagnostics_entry_point,
        )
        if provider_policy_reason:
            generation_diagnostics["provider_policy_reason"] = provider_policy_reason
        if generation_diagnostics:
            merged_metadata["factory_generation"] = generation_diagnostics
            self._write_generation_diagnostics(output_dir, generation_diagnostics)

        result = GeneratedProject(
            name=name,
            type=template_obj.type,
            version=version,
            output_path=output_dir,
            ai_provider=provider_used.value,
            template_name=template,
            template_path=template_path,
            metadata=merged_metadata,
            chatdev_warehouse_path=warehouse_path,
            token_cost=token_cost,
            model_used=model_used,
        )

        # Auto-register in artifact registry
        if auto_register:
            self.registry.register(
                name=name,
                project_type=template_obj.type,
                version=version,
                source_path=output_dir,
                ai_provider=provider_used.value,
                chatdev_warehouse_path=str(warehouse_path) if warehouse_path else None,
                token_cost=token_cost,
                model_used=model_used,
                description=description,
                metadata=merged_metadata,
            )

        try:
            from src.system.agent_awareness import emit as _emit

            _emit(
                "tasks",
                f"Project factory: {name} v{version} | provider={provider_used.value}"
                f" template={template} type={template_obj.type}",
                level="INFO",
                source="project_factory",
            )
        except Exception:
            pass

        return result

    def _generate_project(
        self,
        name: str,
        template: BaseProjectTemplate,
        provider: AIProviderType,
        description: str,
    ) -> tuple:
        """Generate project files using selected AI provider.

        Returns:
            (output_dir, model_used, token_cost, chatdev_warehouse_path, provider_used)
        """
        if provider == AIProviderType.CHATDEV:
            return self._generate_with_chatdev(name, template, description)

        elif provider == AIProviderType.OLLAMA:
            return self._generate_with_ollama(name, template, description)

        elif provider == AIProviderType.CLAUDE:
            return self._generate_with_claude(name, template, description)

        elif provider == AIProviderType.OPENAI:
            return self._generate_with_openai(name, template, description)

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _generate_with_chatdev(
        self, name: str, template: BaseProjectTemplate, description: str
    ) -> tuple:
        """Generate using ChatDev (multi-agent team)."""
        from src.factories.generators.chatdev_generator import ChatDevGenerator

        if not self.orchestrator.chatdev_path:
            logger.warning("ChatDev path unavailable; falling back to Ollama.")
            return self._generate_with_ollama(
                name,
                template,
                description,
                fallback_from="chatdev",
                fallback_reason="chatdev path unavailable",
            )
        try:
            generator = ChatDevGenerator(self.orchestrator.chatdev_path)
        except Exception as exc:
            logger.warning(f"ChatDev initialization failed ({exc}); falling back to Ollama.")
            return self._generate_with_ollama(
                name,
                template,
                description,
                fallback_from="chatdev",
                fallback_reason=f"chatdev initialization failed: {exc}",
            )

        # Create ChatDev task description
        task = self._build_chatdev_task(name, template, description)

        # Generate using ChatDev
        result = generator.generate(
            task=task,
            project_name=name,
            model="qwen2.5-coder:14b",
        )

        if not result.success:
            fallback_reason = result.error_message or "unknown chatdev error"
            log_fn = logger.info if fallback_reason == "forced health fallback" else logger.warning
            log_fn(
                "ChatDev generation failed (%s); falling back to Ollama.",
                fallback_reason,
            )
            return self._generate_with_ollama(
                name,
                template,
                description,
                fallback_from="chatdev",
                fallback_reason=fallback_reason,
            )

        if not result.warehouse_path.exists():
            logger.warning(
                "ChatDev did not produce a warehouse output path; falling back to Ollama."
            )
            return self._generate_with_ollama(
                name,
                template,
                description,
                fallback_from="chatdev",
                fallback_reason="chatdev missing warehouse output",
            )

        # Copy to factory output
        output_dir = self.output_root / name / template.type
        output_dir.mkdir(parents=True, exist_ok=True)

        if result.warehouse_path.exists():
            shutil.copytree(result.warehouse_path, output_dir, dirs_exist_ok=True)

        file_structure = getattr(template, "file_structure", {}) or {}
        if not file_structure:
            language = (template.language or "python").lower()
            profile = self._language_profile(language)
            file_structure = {profile["fallback_entry"]: "Main entry point"}
        entry_point = self._detect_entry_point(template, file_structure)
        self._write_support_files(
            output_path=output_dir,
            name=name,
            description=description,
            template=template,
            file_structure=file_structure,
            entry_point=entry_point,
        )
        generated_files = len([path for path in output_dir.rglob("*") if path.is_file()])
        self._last_generation_diagnostics = {
            "provider_chain": ["chatdev"],
            "chatdev_warehouse_path": str(result.warehouse_path),
            "chatdev_model": result.model_used,
            "entry_point": entry_point,
            "ollama_placeholder_files": 0,
            "generated_file_count": generated_files,
        }

        return (
            output_dir,
            result.model_used,
            result.token_cost,
            result.warehouse_path,
            AIProviderType.CHATDEV,
        )

    def _generate_with_ollama(
        self,
        name: str,
        template: BaseProjectTemplate,
        description: str,
        fallback_from: str | None = None,
        fallback_reason: str | None = None,
    ) -> tuple:
        """Generate using local Ollama LLM.

        Creates project structure and uses Ollama for code generation.
        Iterates through template file_structure for multi-file projects.
        """
        output_path = Path(self.output_root / name)
        output_path.mkdir(parents=True, exist_ok=True)

        model = "qwen2.5-coder:7b"
        tokens_used = 0
        generated_count = 0
        placeholder_count = 0
        generation_errors: list[dict[str, str]] = []
        language = (template.language or "python").lower()
        profile = self._language_profile(language)

        # Get file structure from template
        file_structure = getattr(template, "file_structure", {})
        if not file_structure:
            file_structure = {profile["fallback_entry"]: "Main entry point"}

        entry_point = self._detect_entry_point(template, file_structure)
        runtime_profile = self._resolve_runtime_profile(template)
        feature_flags = self._resolve_feature_flags(template)

        # Generate context for the full project
        project_context = f"""Project: {name}
Description: {description}
Type: {template.type}
Language: {template.language}
Dependencies: {", ".join(template.dependencies)}
Entry point: {entry_point}
Runtime profile: {runtime_profile}
Platform features: {", ".join([k for k, v in feature_flags.items() if v]) or "none"}
"""
        if hasattr(template, "generation_hints"):
            hints = template.generation_hints
            if hints:
                project_context += "\nGeneration hints:\n" + "\n".join(f"- {h}" for h in hints)

        generated_files: dict[str, str] = {}
        python_modules = self._python_module_index(file_structure)

        # Generate each file from the template structure
        for filepath, file_description in file_structure.items():
            logger.info(f"  Generating {filepath}...")

            # Create parent directories
            file_path = output_path / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Determine file type
            ext = file_path.suffix.lower()
            prompt = self._build_prompt_for_file(
                filepath=filepath,
                description=file_description,
                context=project_context,
                generated=generated_files,
                language=language,
            )

            try:
                if requests is None:
                    raise RuntimeError("requests library not available")
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.7, "num_predict": 4096},
                    },
                    timeout=180,
                )

                if response.status_code == 200:
                    result = response.json()
                    code = result.get("response", "")
                    tokens_used += result.get("eval_count", 0)

                    # Clean code output (remove markdown fences if present)
                    code = self._clean_code_output(code, ext)
                    if ext == ".py":
                        code = self._normalize_python_imports(
                            code=code,
                            filepath=filepath,
                            python_modules=python_modules,
                        )

                    # Write file and cache snippet for follow-up files.
                    file_path.write_text(code, encoding="utf-8")
                    generated_files[filepath] = code[:500]
                    logger.info(f"    ✅ Generated {filepath} ({len(code)} bytes)")
                    generated_count += 1
                    placeholder = self._placeholder_content_for_ext(ext)
                    if placeholder and code.strip() == placeholder.strip():
                        placeholder_count += 1
                else:
                    logger.warning(f"    ❌ Failed to generate {filepath}: {response.status_code}")
                    placeholder = self._placeholder_content_for_ext(ext)
                    file_path.write_text(placeholder, encoding="utf-8")
                    placeholder_count += 1
                    generation_errors.append(
                        {
                            "file": filepath,
                            "error": f"ollama http {response.status_code}",
                        }
                    )

                # Brief pause between generations to avoid overwhelming Ollama
                time.sleep(0.5)

            except Exception as e:
                logger.warning(f"    ❌ Error generating {filepath}: {e}")
                placeholder = self._placeholder_content_for_ext(ext)
                file_path.write_text(placeholder, encoding="utf-8")
                placeholder_count += 1
                generation_errors.append({"file": filepath, "error": str(e)})

        self._write_support_files(
            output_path=output_path,
            name=name,
            description=description,
            template=template,
            file_structure=file_structure,
            entry_point=entry_point,
        )
        provider_chain = [fallback_from, "ollama"] if fallback_from else ["ollama"]
        self._last_generation_diagnostics = {
            "provider_chain": provider_chain,
            "fallback_reason": fallback_reason,
            "ollama_model": model,
            "entry_point": entry_point,
            "ollama_files_targeted": len(file_structure),
            "ollama_files_generated": generated_count,
            "ollama_placeholder_files": placeholder_count,
            "ollama_errors": generation_errors[:20],
        }

        return output_path, model, tokens_used * 0.0001, None, AIProviderType.OLLAMA

    def _build_prompt_for_file(
        self,
        filepath: str,
        description: str,
        context: str,
        generated: dict[str, str],
        language: str,
    ) -> str:
        """Build a prompt based on file extension and template language."""
        path = Path(filepath)
        ext = path.suffix.lower()

        if ext == ".json":
            return self._build_json_prompt(filepath, description, context)

        if ext == ".md":
            return self._build_markdown_prompt(filepath, description, context)

        if ext == ".py":
            return self._build_python_prompt(filepath, description, context, generated)

        if ext in {".js", ".mjs", ".cjs"}:
            return self._build_code_prompt(
                filepath,
                description,
                context,
                generated,
                "JavaScript",
                [
                    "Use modern JavaScript syntax and keep functions cohesive.",
                    "Prefer explicit exports for reusable modules.",
                ],
            )

        if ext == ".ts":
            return self._build_code_prompt(
                filepath,
                description,
                context,
                generated,
                "TypeScript",
                [
                    "Use explicit interfaces/types where helpful.",
                    "Keep imports and exports consistent with generated files.",
                ],
            )

        if ext == ".go":
            return self._build_code_prompt(
                filepath,
                description,
                context,
                generated,
                "Go",
                [
                    "Return idiomatic Go code with proper package declaration.",
                    "Avoid pseudo-code or placeholders.",
                ],
            )

        if ext == ".cs":
            return self._build_code_prompt(
                filepath,
                description,
                context,
                generated,
                "C#",
                [
                    "Generate compilable C# code targeting .NET 8 style conventions.",
                    "Use namespaces and classes as appropriate.",
                ],
            )

        if ext in {".yaml", ".yml"}:
            return self._build_code_prompt(
                filepath,
                description,
                context,
                generated,
                "YAML",
                ["Output valid YAML only and preserve indentation consistency."],
            )

        if ext == ".toml":
            return self._build_code_prompt(
                filepath,
                description,
                context,
                generated,
                "TOML",
                ["Output valid TOML only."],
            )

        if ext == ".gd":
            return self._build_code_prompt(
                filepath,
                description,
                context,
                generated,
                "GDScript",
                [
                    "Use Godot 4-style GDScript syntax.",
                    "Keep script ready to attach to scenes.",
                ],
            )

        language_label = language.capitalize() if language else "plain text"
        return self._build_generic_prompt(filepath, description, context, language_label)

    def _build_code_prompt(
        self,
        filepath: str,
        description: str,
        context: str,
        generated: dict[str, str],
        language_label: str,
        rules: list[str],
    ) -> str:
        """Build prompt for structured source/config files."""
        context_snippets = ""
        if generated:
            context_snippets = "\n\nAlready generated files (for reference):\n"
            for fname, snippet in list(generated.items())[:5]:
                context_snippets += f"\n--- {fname} ---\n{snippet}...\n"

        rule_lines = "\n".join(f"- {rule}" for rule in rules)

        return f"""{context}
{context_snippets}

Now generate the {language_label} file for: {filepath}
Purpose: {description}

IMPORTANT:
- Output ONLY valid {language_label}, no markdown and no explanations
- Keep imports/paths consistent with previously generated files
{rule_lines}

Generate the complete {language_label} file:"""

    def _build_python_prompt(
        self, filepath: str, description: str, context: str, generated: dict[str, str]
    ) -> str:
        """Build prompt for Python file generation."""
        return self._build_code_prompt(
            filepath,
            description,
            context,
            generated,
            "Python",
            [
                "Include proper imports and keep module boundaries clean.",
                "Include docstrings for non-trivial classes/functions.",
                "Return complete runnable code, not snippets.",
                "Use relative imports when referencing sibling modules.",
            ],
        )

    def _build_json_prompt(self, filepath: str, description: str, context: str) -> str:
        """Build prompt for JSON file generation."""
        return f"""{context}

Generate the JSON data for: {filepath}
Purpose: {description}

IMPORTANT:
- Output ONLY valid JSON, no explanations or markdown
- Use proper JSON syntax with double quotes
- Make sure the structure is complete and usable

Generate the JSON file:"""

    def _build_markdown_prompt(self, filepath: str, description: str, context: str) -> str:
        """Build prompt for Markdown file generation."""
        return f"""{context}

Generate the Markdown file for: {filepath}
Purpose: {description}

Generate the Markdown:"""

    def _build_generic_prompt(
        self, filepath: str, description: str, context: str, language_label: str
    ) -> str:
        """Build prompt for generic file generation."""
        return f"""{context}

Generate the {language_label} file: {filepath}
Purpose: {description}

IMPORTANT:
- Output only file content, no markdown fences and no explanations
- Keep file content complete and directly usable

Generate the file content:"""

    def _python_module_index(self, file_structure: dict[str, str]) -> set[str]:
        """Build a module index for generated Python files."""
        modules: set[str] = set()
        for relpath in file_structure:
            path = Path(relpath)
            if path.suffix.lower() != ".py":
                continue
            parts = path.with_suffix("").parts
            if not parts:
                continue
            modules.add(".".join(parts))
            modules.add(parts[-1])
        return modules

    def _normalize_python_imports(
        self,
        code: str,
        filepath: str,
        python_modules: set[str],
    ) -> str:
        """Normalize generated Python imports for local package consistency."""
        path = Path(filepath)
        parent_parts = path.parent.parts
        in_game_package = bool(parent_parts and parent_parts[0] == "game")
        sibling_prefix = ".".join(parent_parts) if parent_parts else ""
        sibling_modules = {
            mod.rsplit(".", 1)[-1]
            for mod in python_modules
            if sibling_prefix and mod.startswith(f"{sibling_prefix}.")
        }
        game_modules = {mod.rsplit(".", 1)[-1] for mod in python_modules if mod.startswith("game.")}

        def _rewrite_from(match: re.Match[str]) -> str:
            source = match.group(1)
            remainder = match.group(2)
            if source == "game_state" and "engine" in sibling_modules:
                source = "engine"

            if in_game_package and "." not in source and source in sibling_modules:
                return f"from .{source} import {remainder}"

            if path.name == "main.py" and "." not in source and source in game_modules:
                return f"from game.{source} import {remainder}"

            return match.group(0)

        def _rewrite_import(match: re.Match[str]) -> str:
            source = match.group(1)
            alias = match.group(2) or ""
            if source == "game_state" and "engine" in sibling_modules:
                source = "engine"

            if in_game_package and "." not in source and source in sibling_modules:
                return f"from . import {source}{alias}"

            if path.name == "main.py" and "." not in source and source in game_modules:
                return f"import game.{source}{alias}"

            if path.name == "main.py" and "." not in source and source.startswith("game_"):
                normalized = source[len("game_") :]
                if normalized in game_modules:
                    alias_name = alias.strip().split()[-1] if alias else source
                    return f"import game.{normalized} as {alias_name}"

            return match.group(0)

        code = re.sub(r"(?m)^from\s+([A-Za-z_][\w\.]*)\s+import\s+(.+)$", _rewrite_from, code)
        code = re.sub(r"(?m)^import\s+([A-Za-z_][\w\.]*)(\s+as\s+\w+)?$", _rewrite_import, code)
        if path.name == "main.py":

            def _rewrite_main_relative(match: re.Match[str]) -> str:
                source = match.group(1)
                alias = match.group(2)
                normalized = source[len("game_") :] if source.startswith("game_") else source
                if normalized in game_modules:
                    if alias:
                        return f"from game import {normalized} as {alias}"
                    if source != normalized:
                        return f"from game import {normalized} as {source}"
                    return f"from game import {normalized}"
                return match.group(0)

            code = re.sub(
                r"(?m)^from\s+\.\s+import\s+([A-Za-z_][\w]*)(?:\s+as\s+([A-Za-z_][\w]*))?$",
                _rewrite_main_relative,
                code,
            )
        return code

    def _clean_code_output(self, code: str, ext: str) -> str:
        """Clean LLM output - remove markdown fences etc."""
        # Prefer fenced block content when present.
        block = re.search(r"```[^\n]*\n(.*?)```", code, flags=re.DOTALL)
        if block:
            code = block.group(1)
        # Remove any leftover fence markers.
        code = re.sub(r"^```[\w-]*\n?", "", code)
        code = re.sub(r"\n?```$", "", code)
        code = code.strip()

        if not code:
            return self._placeholder_content_for_ext(ext)

        # For JSON, ensure it starts with { or [
        if ext == ".json":
            # Find first { or [
            match = re.search(r"[\{\[]", code)
            if match:
                code = code[match.start() :]
            # Find last } or ]
            match = re.search(r"[\}\]](?!.*[\}\]])", code)
            if match:
                code = code[: match.end()]
            if not code:
                code = "{}"

        return f"{code}\n"

    def _placeholder_content_for_ext(self, ext: str) -> str:
        """Provide minimal valid fallback content when generation fails."""
        py_placeholder = '"""Generated placeholder module."""\n'
        placeholders = {
            ".py": py_placeholder,
            ".json": "{}\n",
            ".md": "# Placeholder\n",
            ".js": "// Generated placeholder module.\n",
            ".mjs": "// Generated placeholder module.\n",
            ".cjs": "// Generated placeholder module.\n",
            ".ts": "// Generated placeholder module.\nexport {};\n",
            ".go": "package main\n\nfunc main() {}\n",
            ".cs": (
                "namespace Generated;\n\n"
                "internal static class Program\n{\n"
                "    public static void Main(string[] args) { }\n}\n"
            ),
            ".yml": "# Generated placeholder config.\n",
            ".yaml": "# Generated placeholder config.\n",
            ".toml": "# Generated placeholder config.\n",
            ".gd": "extends Node\n",
        }
        return placeholders.get(ext, "")

    def _language_profile(self, language: str) -> dict[str, str]:
        """Get generation profile for a language with sane fallback defaults.

        Uses the LanguageRegistry for dynamic language support.
        Falls back to Python if language not found.
        """
        try:
            registry = get_language_registry()
            return registry.get_profile(language)
        except (KeyError, Exception):
            # Fallback to LANGUAGE_PROFILES dict for backward compatibility
            return LANGUAGE_PROFILES.get(
                language.lower(),
                LANGUAGE_PROFILES.get(
                    "python",
                    {
                        "fallback_entry": "main.py",
                        "dependency_file": "requirements.txt",
                        "install_cmd": "pip install -r requirements.txt",
                        "run_cmd": "python {entry_point}",
                        "code_fence": "python",
                    },
                ),
            )

    def _detect_entry_point(
        self, template: BaseProjectTemplate, file_structure: dict[str, str]
    ) -> str:
        """Determine primary entry point from metadata or file structure."""
        metadata_entry = template.metadata.get("entry_point")
        if isinstance(metadata_entry, str) and metadata_entry.strip():
            return metadata_entry.strip()

        language = (template.language or "python").lower()
        profile = self._language_profile(language)

        candidates = [
            profile["fallback_entry"],
            f"src/{Path(profile['fallback_entry']).name}",
            "main.py",
            "src/main.py",
            "main.js",
            "src/main.js",
            "main.ts",
            "src/main.ts",
            "main.go",
            "Program.cs",
        ]
        file_keys = set(file_structure.keys())
        for candidate in candidates:
            if candidate in file_keys:
                return candidate

        for path in file_structure:
            name = Path(path).name.lower()
            if name.startswith(
                (
                    "main",
                    "index",
                    "app",
                    "program",
                )
            ):
                return path

        return next(iter(file_structure.keys()))

    def _write_support_files(
        self,
        output_path: Path,
        name: str,
        description: str,
        template: BaseProjectTemplate,
        file_structure: dict[str, str],
        entry_point: str,
    ) -> None:
        """Create missing support files (README/deps/init) without clobbering template output."""
        language = (template.language or "python").lower()
        profile = self._language_profile(language)
        runtime_profile = self._resolve_runtime_profile(template)
        feature_flags = self._resolve_feature_flags(template)

        readme_path = output_path / "README.md"
        if "README.md" not in file_structure and not readme_path.exists():
            readme_path.write_text(
                self._build_readme(name, description, profile, entry_point), encoding="utf-8"
            )

        dependency_file = profile.get("dependency_file", "")
        if dependency_file:
            dependency_path = output_path / dependency_file
            if dependency_file not in file_structure and not dependency_path.exists():
                dependency_content = self._build_dependency_file(
                    name=name,
                    template=template,
                    entry_point=entry_point,
                    dependency_file=dependency_file,
                )
                if dependency_content:
                    dependency_path.parent.mkdir(parents=True, exist_ok=True)
                    dependency_path.write_text(dependency_content, encoding="utf-8")

        init_file = output_path / "__init__.py"
        if language == "python" and "__init__.py" not in file_structure and not init_file.exists():
            init_file.write_text(
                f'"""{name} - {description}"""\n__version__ = "1.0.0"\n',
                encoding="utf-8",
            )

        # Runtime and platform scaffolding layers.
        self._write_runtime_profile_packaging(
            output_path=output_path,
            name=name,
            template=template,
            runtime_profile=runtime_profile,
            entry_point=entry_point,
        )

        if feature_flags.get("data_pipeline"):
            self._write_data_pipeline_scaffold(output_path, language)
        if feature_flags.get("event_router"):
            self._write_event_router_scaffold(output_path, language)
        if feature_flags.get("save_migration"):
            self._write_save_migration_scaffold(output_path, language)
        if feature_flags.get("modding_api"):
            self._write_modding_api_scaffold(output_path, language)

        self._wire_runtime_bootstrap(
            output_path=output_path,
            language=language,
            entry_point=entry_point,
            feature_flags=feature_flags,
        )

    def _resolve_runtime_profile(self, template: BaseProjectTemplate) -> str:
        """Resolve runtime profile from template or infer a sensible default."""
        runtime_profile = (getattr(template, "runtime_profile", "") or "").strip().lower()
        if runtime_profile in RUNTIME_PROFILES:
            return runtime_profile

        language = (template.language or "").lower()
        if language == "gdscript" or template.metadata.get("engine") == "godot":
            return "godot_export"
        if template.type == "game" and language in {"javascript", "typescript"}:
            return "electron_local"
        return "native_terminal"

    def _resolve_feature_flags(self, template: BaseProjectTemplate) -> dict[str, bool]:
        """Resolve platform feature flags with game-friendly defaults."""
        is_game = template.type == "game"
        flags = {key: bool(value and is_game) for key, value in DEFAULT_GAME_FEATURE_FLAGS.items()}

        template_flags = getattr(template, "feature_flags", {}) or {}
        for key, value in template_flags.items():
            flags[str(key)] = bool(value)

        metadata_flags = template.metadata.get("platform_features", {}) or {}
        if isinstance(metadata_flags, dict):
            for key, value in metadata_flags.items():
                flags[str(key)] = bool(value)
        return flags

    def _wire_runtime_bootstrap(
        self,
        output_path: Path,
        language: str,
        entry_point: str,
        feature_flags: dict[str, bool],
    ) -> None:
        """Wire runtime scaffolds into generated entry points for active usage at startup."""
        if language != "python":
            return
        if not any(feature_flags.values()):
            return

        self._write_if_missing(
            output_path,
            "game/runtime_services.py",
            self._runtime_services_module_content(),
        )
        self._patch_python_entrypoint_for_runtime(output_path, entry_point)

    def _patch_python_entrypoint_for_runtime(self, output_path: Path, entry_point: str) -> None:
        """Inject runtime bootstrap into generated Python entrypoint."""
        entry_path = output_path / entry_point
        if not entry_path.exists() or entry_path.suffix.lower() != ".py":
            return

        marker = "# NuSyQ runtime bootstrap (auto-generated)"
        original = entry_path.read_text(encoding="utf-8")
        if marker in original:
            return

        snippet = (
            f"{marker}\n"
            "try:\n"
            "    from pathlib import Path as _NuSyQPath\n"
            "    from game.runtime_services import bootstrap_runtime_services as _nq_bootstrap\n"
            "    from game.runtime_services import emit_runtime_event as _nq_emit\n"
            "    NUSYQ_RUNTIME_SERVICES = _nq_bootstrap(_NuSyQPath(__file__).resolve().parent)\n"
            "    _nq_emit(\n"
            "        NUSYQ_RUNTIME_SERVICES,\n"
            "        'on_entrypoint_loaded',\n"
            "        {'entry_point': __name__},\n"
            "    )\n"
            "except Exception:\n"
            "    NUSYQ_RUNTIME_SERVICES = {}\n"
        )

        lines = original.splitlines(keepends=True)
        insert_at = 0

        if lines and lines[0].startswith("#!"):
            insert_at = 1
        if (
            insert_at < len(lines)
            and lines[insert_at].startswith("#")
            and "coding" in lines[insert_at]
        ):
            insert_at += 1

        if insert_at < len(lines) and lines[insert_at].lstrip().startswith(('"""', "'''")):
            stripped = lines[insert_at].lstrip()
            quote = stripped[:3]
            insert_at += 1
            if stripped.count(quote) < 2:
                while insert_at < len(lines):
                    if quote in lines[insert_at]:
                        insert_at += 1
                        break
                    insert_at += 1

        while insert_at < len(lines) and lines[insert_at].lstrip().startswith(
            "from __future__ import"
        ):
            insert_at += 1

        new_lines = [*lines[:insert_at], snippet, "\n", *lines[insert_at:]]
        entry_path.write_text("".join(new_lines), encoding="utf-8")

    def _runtime_services_module_content(self) -> str:
        """Return runtime bootstrap module that activates scaffold systems at play-time."""
        return (
            '"""Runtime bootstrap wiring for data pipeline, events, saves, and mods."""\n\n'
            "from __future__ import annotations\n\n"
            "import importlib.util\n"
            "import json\n"
            "from pathlib import Path\n"
            "from typing import Any\n\n"
            "try:\n"
            "    from .data_pipeline import DataPipeline\n"
            "except Exception:\n"
            "    DataPipeline = None\n\n"
            "try:\n"
            "    from .event_router import EventRouter\n"
            "except Exception:\n"
            "    EventRouter = None\n\n"
            "try:\n"
            "    from .modding_api import ModdingAPI\n"
            "except Exception:\n"
            "    ModdingAPI = None\n\n"
            "try:\n"
            "    from .save_system import migrate_save\n"
            "except Exception:\n"
            "    def migrate_save(data: dict[str, Any]) -> dict[str, Any]:\n"
            "        return data\n\n"
            "def _load_save(project_root: Path) -> dict[str, Any]:\n"
            "    save_path = project_root / 'saves' / 'save.json'\n"
            "    if save_path.exists():\n"
            "        try:\n"
            "            return json.loads(save_path.read_text(encoding='utf-8'))\n"
            "        except Exception:\n"
            "            return {\n"
            "                'version': 1,\n"
            "                'player': {},\n"
            "                'world': {},\n"
            "                'inventory': [],\n"
            "            }\n"
            "    return {\n"
            "        'version': 1,\n"
            "        'player': {},\n"
            "        'world': {},\n"
            "        'inventory': [],\n"
            "    }\n\n"
            "def _load_sample_mod(project_root: Path, api: Any) -> None:\n"
            "    mod_path = project_root / 'mods' / 'examples' / 'sample_mod.py'\n"
            "    if not mod_path.exists() or api is None:\n"
            "        return\n"
            "    try:\n"
            "        spec = importlib.util.spec_from_file_location('nusyq_sample_mod', mod_path)\n"
            "        if spec is None or spec.loader is None:\n"
            "            return\n"
            "        module = importlib.util.module_from_spec(spec)\n"
            "        spec.loader.exec_module(module)\n"
            "        register_fn = getattr(module, 'register', None)\n"
            "        if callable(register_fn):\n"
            "            register_fn(api)\n"
            "    except Exception:\n"
            "        return\n\n"
            "def emit_runtime_event(services: dict[str, Any], event_name: str, payload: dict[str, Any]) -> None:\n"
            "    router = services.get('event_router')\n"
            "    if router is not None:\n"
            "        try:\n"
            "            router.emit(event_name, payload)\n"
            "        except Exception:\n"
            "            pass\n"
            "    mod_api = services.get('modding_api')\n"
            "    if mod_api is not None:\n"
            "        try:\n"
            "            mod_api.dispatch(event_name, payload)\n"
            "        except Exception:\n"
            "            pass\n\n"
            "def bootstrap_runtime_services(project_root: Path) -> dict[str, Any]:\n"
            "    services: dict[str, Any] = {'project_root': str(project_root)}\n\n"
            "    if DataPipeline is not None:\n"
            "        try:\n"
            "            services['data_pipeline'] = DataPipeline(project_root)\n"
            "            services['catalogs'] = services['data_pipeline'].load_catalogs()\n"
            "        except Exception:\n"
            "            services['catalogs'] = {}\n\n"
            "    if EventRouter is not None:\n"
            "        try:\n"
            "            services['event_router'] = EventRouter()\n"
            "        except Exception:\n"
            "            pass\n\n"
            "    if ModdingAPI is not None:\n"
            "        try:\n"
            "            services['modding_api'] = ModdingAPI()\n"
            "        except Exception:\n"
            "            pass\n\n"
            "    services['save_data'] = migrate_save(_load_save(project_root))\n\n"
            "    mod_api = services.get('modding_api')\n"
            "    if mod_api is not None:\n"
            "        _load_sample_mod(project_root, mod_api)\n"
            "        try:\n"
            "            mod_api.dispatch('on_game_start', {'project_root': str(project_root)})\n"
            "        except Exception:\n"
            "            pass\n\n"
            "    emit_runtime_event(\n"
            "        services,\n"
            "        'runtime_bootstrap_complete',\n"
            "        {'has_catalogs': bool(services.get('catalogs'))},\n"
            "    )\n"
            "    return services\n"
        )

    def _write_if_missing(self, output_path: Path, relative_path: str, content: str) -> None:
        """Write a file only if it does not already exist."""
        target = output_path / relative_path
        if target.exists():
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def _load_provider_policy(self) -> dict[str, Any]:
        """Load optional provider-hardening policy."""
        if not self._provider_policy_path.exists():
            return {}
        try:
            data = json.loads(self._provider_policy_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _apply_provider_policy_overrides(
        self, selected: AIProviderType, template: BaseProjectTemplate
    ) -> tuple[AIProviderType, str | None]:
        """Apply configured provider policy to reduce avoidable fallback churn."""
        policy = self._load_provider_policy()
        if not policy:
            return selected, None

        prefer_ollama = bool(policy.get("prefer_ollama_for_multifile", False))
        if (
            prefer_ollama
            and selected == AIProviderType.CHATDEV
            and bool(getattr(template, "requires_multifile", False))
            and self.orchestrator.ollama_available
        ):
            return AIProviderType.OLLAMA, "policy prefer_ollama_for_multifile"

        force_provider = str(policy.get("force_provider", "")).strip().lower()
        if force_provider:
            try:
                forced = AIProviderType(force_provider)
                if self.orchestrator._provider_available(forced):
                    return forced, f"policy force_provider={force_provider}"
            except ValueError:
                logger.debug("Suppressed ValueError", exc_info=True)

        return selected, None

    def _build_generation_diagnostics(
        self,
        selected_provider: str,
        used_provider: str,
        output_path: Path,
        template: BaseProjectTemplate,
        entry_point: str,
    ) -> dict[str, Any]:
        """Build generation diagnostics snapshot for observability and debugging."""
        diagnostics = dict(self._last_generation_diagnostics or {})
        diagnostics.setdefault("selected_provider", selected_provider)
        diagnostics.setdefault("used_provider", used_provider)
        diagnostics.setdefault("runtime_profile", self._resolve_runtime_profile(template))
        diagnostics.setdefault("language", template.language)
        diagnostics.setdefault("entry_point", entry_point)
        diagnostics.setdefault(
            "feature_flags",
            [key for key, enabled in self._resolve_feature_flags(template).items() if enabled],
        )
        diagnostics.setdefault(
            "generated_file_count",
            len([path for path in output_path.rglob("*") if path.is_file()]),
        )
        diagnostics["generated_at"] = datetime.now(UTC).isoformat()
        return diagnostics

    def _write_generation_diagnostics(self, output_path: Path, diagnostics: dict[str, Any]) -> None:
        """Persist generation diagnostics for post-run triage."""
        report_path = output_path / "factory" / "generation_diagnostics.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(f"{json.dumps(diagnostics, indent=2)}\n", encoding="utf-8")

    def _write_runtime_profile_packaging(
        self,
        output_path: Path,
        name: str,
        template: BaseProjectTemplate,
        runtime_profile: str,
        entry_point: str,
    ) -> None:
        """Create runtime-profile packaging outputs via executable adapter classes."""
        context = PackagingContext(
            name=name,
            runtime_profile=runtime_profile,
            entry_point=entry_point,
            language=template.language,
            project_type=template.type,
            metadata=template.metadata or {},
        )
        adapter = build_runtime_packaging_adapter(runtime_profile)
        for relative_path, content in adapter.build_file_map(context).items():
            self._write_if_missing(output_path, relative_path, content)

        preflight = adapter.validate_layout(output_path, context)
        self._write_if_missing(
            output_path,
            "packaging/health/preflight.json",
            f"{json.dumps(preflight, indent=2)}\n",
        )
        hook_report = adapter.validate_executable_hooks(output_path, context)
        self._write_if_missing(
            output_path,
            "packaging/health/hook_validation.json",
            f"{json.dumps(hook_report, indent=2)}\n",
        )

    def _write_data_pipeline_scaffold(self, output_path: Path, language: str) -> None:
        """Create first-class JSON/YAML data pipeline scaffolding."""
        self._write_if_missing(
            output_path,
            "data/pipeline_manifest.yaml",
            "version: 1\n"
            "datasets:\n"
            "  - enemies\n"
            "  - items\n"
            "  - abilities\n"
            "  - localization\n"
            "locales:\n"
            "  - en\n"
            "default_locale: en\n",
        )
        self._write_if_missing(
            output_path,
            "data/enemies.json",
            json.dumps(
                [
                    {
                        "id": "goblin_scout",
                        "name_key": "enemy.goblin_scout.name",
                        "tier": 1,
                        "hp": 18,
                        "attack": 5,
                        "defense": 1,
                        "tags": ["humanoid", "skirmisher"],
                    }
                ],
                indent=2,
            )
            + "\n",
        )
        self._write_if_missing(
            output_path,
            "data/items.json",
            json.dumps(
                [
                    {
                        "id": "iron_sword",
                        "name_key": "item.iron_sword.name",
                        "slot": "weapon",
                        "rarity": "common",
                        "stats": {"attack": 3},
                    }
                ],
                indent=2,
            )
            + "\n",
        )
        self._write_if_missing(
            output_path,
            "data/abilities.json",
            json.dumps(
                [
                    {
                        "id": "bleeding_strike",
                        "name_key": "ability.bleeding_strike.name",
                        "cooldown": 2,
                        "effects": ["apply_bleed"],
                    }
                ],
                indent=2,
            )
            + "\n",
        )
        self._write_if_missing(
            output_path,
            "data/localization/en.json",
            json.dumps(
                {
                    "enemy.goblin_scout.name": "Goblin Scout",
                    "item.iron_sword.name": "Iron Sword",
                    "ability.bleeding_strike.name": "Bleeding Strike",
                },
                indent=2,
            )
            + "\n",
        )
        self._write_if_missing(
            output_path,
            "data/schemas/enemy.schema.json",
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": [
                        "id",
                        "name_key",
                        "hp",
                        "attack",
                        "defense",
                    ],
                    "properties": {
                        "id": {"type": "string"},
                        "name_key": {"type": "string"},
                        "tier": {
                            "type": "integer",
                            "minimum": 1,
                        },
                        "hp": {
                            "type": "integer",
                            "minimum": 1,
                        },
                        "attack": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "defense": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                indent=2,
            )
            + "\n",
        )
        self._write_if_missing(
            output_path,
            "data/schemas/item.schema.json",
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": [
                        "id",
                        "name_key",
                        "slot",
                        "rarity",
                    ],
                    "properties": {
                        "id": {"type": "string"},
                        "name_key": {"type": "string"},
                        "slot": {"type": "string"},
                        "rarity": {"type": "string"},
                        "stats": {"type": "object"},
                    },
                },
                indent=2,
            )
            + "\n",
        )
        self._write_if_missing(
            output_path,
            "data/schemas/ability.schema.json",
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": [
                        "id",
                        "name_key",
                        "effects",
                    ],
                    "properties": {
                        "id": {"type": "string"},
                        "name_key": {"type": "string"},
                        "cooldown": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "effects": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                indent=2,
            )
            + "\n",
        )

        module_paths = self._runtime_module_paths(language)
        module_path = module_paths.get("data_pipeline")
        if module_path:
            self._write_if_missing(
                output_path,
                module_path,
                self._data_pipeline_module_content(language),
            )

    def _write_event_router_scaffold(self, output_path: Path, language: str) -> None:
        """Create event-router scaffolding for combat proc chains."""
        self._write_if_missing(
            output_path,
            "data/events/combat_proc_chains.yaml",
            "version: 1\n"
            "events:\n"
            "  on_hit:\n"
            "    - id: bleed_proc\n"
            "      chance: 0.35\n"
            "      apply_effect: bleed\n"
            "  on_kill:\n"
            "    - id: soul_harvest\n"
            "      chance: 1.0\n"
            "      apply_effect: restore_mana\n",
        )
        module_path = self._runtime_module_paths(language).get("event_router")
        if module_path:
            self._write_if_missing(
                output_path, module_path, self._event_router_module_content(language)
            )

    def _write_save_migration_scaffold(self, output_path: Path, language: str) -> None:
        """Create versioned save/config schema scaffolding."""
        self._write_if_missing(
            output_path,
            "config/save_schema.json",
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "SaveData",
                    "type": "object",
                    "required": [
                        "version",
                        "player",
                        "world",
                    ],
                    "properties": {
                        "version": {
                            "type": "integer",
                            "minimum": 1,
                        },
                        "player": {"type": "object"},
                        "world": {"type": "object"},
                        "inventory": {"type": "array"},
                    },
                },
                indent=2,
            )
            + "\n",
        )
        self._write_if_missing(
            output_path,
            "config/user_config.schema.json",
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "title": "UserConfig",
                    "type": "object",
                    "properties": {
                        "audio": {"type": "object"},
                        "video": {"type": "object"},
                        "controls": {"type": "object"},
                        "accessibility": {"type": "object"},
                    },
                    "additionalProperties": False,
                },
                indent=2,
            )
            + "\n",
        )
        self._write_if_missing(
            output_path,
            "config/default_user_config.json",
            json.dumps(
                {
                    "audio": {"music_volume": 0.7, "sfx_volume": 0.8},
                    "video": {"ascii_mode": True, "screen_shake": True},
                    "controls": {
                        "up": "k",
                        "down": "j",
                        "left": "h",
                        "right": "l",
                    },
                    "accessibility": {"high_contrast": False},
                },
                indent=2,
            )
            + "\n",
        )
        self._write_if_missing(
            output_path,
            "migrations/save/README.md",
            "# Save Migration Registry\n\n"
            "Place versioned migration rules in this directory. Each migration should\n"
            "transform save data from version N to N+1.\n",
        )
        self._write_if_missing(
            output_path,
            "migrations/save/0001_initial.yaml",
            "from_version: 1\nto_version: 2\nchanges:\n  - op: add_default\n    path: $.player.perks\n    value: []\n",
        )
        module_path = self._runtime_module_paths(language).get("save_system")
        if module_path:
            self._write_if_missing(
                output_path, module_path, self._save_system_module_content(language)
            )

    def _write_modding_api_scaffold(self, output_path: Path, language: str) -> None:
        """Create script extensibility API boundary scaffolding."""
        self._write_if_missing(
            output_path,
            "mods/README.md",
            "# Modding API\n\n"
            "Mods run through a constrained API boundary. Use `mods/hooks.json` to register\n"
            "events and `mods/examples/` as a starting point.\n",
        )
        self._write_if_missing(
            output_path,
            "mods/hooks.json",
            json.dumps(
                {
                    "hooks": [
                        "on_game_start",
                        "on_turn_start",
                        "on_turn_end",
                        "on_entity_spawn",
                        "on_damage_applied",
                    ]
                },
                indent=2,
            )
            + "\n",
        )
        self._write_if_missing(
            output_path,
            "mods/manifest.schema.json",
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": [
                        "id",
                        "version",
                        "entry",
                    ],
                    "properties": {
                        "id": {"type": "string"},
                        "version": {"type": "string"},
                        "entry": {"type": "string"},
                        "hooks": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                indent=2,
            )
            + "\n",
        )

        sample_path = self._runtime_module_paths(language).get("sample_mod")
        if sample_path:
            self._write_if_missing(output_path, sample_path, self._sample_mod_content(language))

        module_path = self._runtime_module_paths(language).get("modding_api")
        if module_path:
            self._write_if_missing(
                output_path, module_path, self._modding_api_module_content(language)
            )

    def _runtime_module_paths(self, language: str) -> dict[str, str]:
        """Map language to runtime scaffold module paths."""
        if language == "python":
            return {
                "data_pipeline": "game/data_pipeline.py",
                "event_router": "game/event_router.py",
                "save_system": "game/save_system.py",
                "modding_api": "game/modding_api.py",
                "sample_mod": "mods/examples/sample_mod.py",
            }
        if language in {"javascript", "typescript"}:
            ext = "ts" if language == "typescript" else "js"
            return {
                "data_pipeline": f"src/game/dataPipeline.{ext}",
                "event_router": f"src/game/eventRouter.{ext}",
                "save_system": f"src/game/saveSystem.{ext}",
                "modding_api": f"src/game/moddingApi.{ext}",
                "sample_mod": f"mods/examples/sample_mod.{ext}",
            }
        if language == "gdscript":
            return {
                "data_pipeline": "scripts/data_pipeline.gd",
                "event_router": "scripts/event_router.gd",
                "save_system": "scripts/save_system.gd",
                "modding_api": "scripts/modding_api.gd",
                "sample_mod": "mods/examples/sample_mod.gd",
            }
        return {}

    def _data_pipeline_module_content(self, language: str) -> str:
        """Return language-specific data pipeline module content."""
        if language == "python":
            return (
                '"""Data pipeline loader for enemies/items/abilities/localization."""\n\n'
                "from __future__ import annotations\n\n"
                "import json\n"
                "from pathlib import Path\n"
                "from typing import Any\n\n"
                "class DataPipeline:\n"
                "    def __init__(self, root: Path):\n"
                "        self.root = root\n\n"
                "    def load_json(self, relative_path: str) -> Any:\n"
                "        path = self.root / relative_path\n"
                "        return json.loads(path.read_text(encoding='utf-8'))\n\n"
                "    def load_catalogs(self) -> dict[str, Any]:\n"
                "        return {\n"
                "            'enemies': self.load_json('data/enemies.json'),\n"
                "            'items': self.load_json('data/items.json'),\n"
                "            'abilities': self.load_json('data/abilities.json'),\n"
                "            'localization': self.load_json('data/localization/en.json'),\n"
                "        }\n"
            )
        if language in {"javascript", "typescript"}:
            return (
                "import fs from 'node:fs';\n\n"
                "export function loadJson(path) {\n"
                "  return JSON.parse(fs.readFileSync(path, 'utf-8'));\n"
                "}\n\n"
                "export function loadCatalogs(root = process.cwd()) {\n"
                "  return {\n"
                "    enemies: loadJson(`${root}/data/enemies.json`),\n"
                "    items: loadJson(`${root}/data/items.json`),\n"
                "    abilities: loadJson(`${root}/data/abilities.json`),\n"
                "    localization: loadJson(`${root}/data/localization/en.json`),\n"
                "  };\n"
                "}\n"
            )
        if language == "gdscript":
            return (
                "extends Node\n\n"
                "func load_json(path: String) -> Variant:\n"
                "    var file = FileAccess.open(path, FileAccess.READ)\n"
                "    if file == null:\n"
                "        return {}\n"
                "    var parsed = JSON.parse_string(file.get_as_text())\n"
                "    return parsed if parsed != null else {}\n"
            )
        return ""

    def _event_router_module_content(self, language: str) -> str:
        """Return language-specific event-router module content."""
        if language == "python":
            return (
                '"""Event router for combat and proc chain handling."""\n\n'
                "from __future__ import annotations\n\n"
                "from collections import defaultdict\n"
                "from typing import Any, Callable\n\n"
                "EventHandler = Callable[[dict[str, Any]], None]\n\n"
                "class EventRouter:\n"
                "    def __init__(self) -> None:\n"
                "        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)\n\n"
                "    def register(self, event_name: str, handler: EventHandler) -> None:\n"
                "        self._handlers[event_name].append(handler)\n\n"
                "    def emit(self, event_name: str, payload: dict[str, Any]) -> None:\n"
                "        for handler in self._handlers.get(event_name, []):\n"
                "            handler(payload)\n"
            )
        if language in {"javascript", "typescript"}:
            return (
                "export class EventRouter {\n"
                "  constructor() {\n"
                "    this.handlers = new Map();\n"
                "  }\n\n"
                "  register(eventName, handler) {\n"
                "    if (!this.handlers.has(eventName)) this.handlers.set(eventName, []);\n"
                "    this.handlers.get(eventName).push(handler);\n"
                "  }\n\n"
                "  emit(eventName, payload = {}) {\n"
                "    for (const handler of this.handlers.get(eventName) || []) handler(payload);\n"
                "  }\n"
                "}\n"
            )
        if language == "gdscript":
            return (
                "extends Node\n\n"
                "var handlers: Dictionary = {}\n\n"
                "func register(event_name: String, callable_ref: Callable) -> void:\n"
                "    if not handlers.has(event_name):\n"
                "        handlers[event_name] = []\n"
                "    handlers[event_name].append(callable_ref)\n\n"
                "func emit_event(event_name: String, payload: Dictionary) -> void:\n"
                "    if not handlers.has(event_name):\n"
                "        return\n"
                "    for cb in handlers[event_name]:\n"
                "        cb.call(payload)\n"
            )
        return ""

    def _save_system_module_content(self, language: str) -> str:
        """Return language-specific save versioning/migration module content."""
        if language == "python":
            return (
                '"""Versioned save system with migration hooks."""\n\n'
                "from __future__ import annotations\n\n"
                "from typing import Any, Callable\n\n"
                "CURRENT_SAVE_VERSION = 2\n"
                "Migration = Callable[[dict[str, Any]], dict[str, Any]]\n\n"
                "def migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:\n"
                "    data.setdefault('player', {}).setdefault('perks', [])\n"
                "    data['version'] = 2\n"
                "    return data\n\n"
                "MIGRATIONS: dict[int, Migration] = {1: migrate_v1_to_v2}\n\n"
                "def migrate_save(data: dict[str, Any]) -> dict[str, Any]:\n"
                "    version = int(data.get('version', 1))\n"
                "    while version < CURRENT_SAVE_VERSION:\n"
                "        migration = MIGRATIONS.get(version)\n"
                "        if migration is None:\n"
                "            raise ValueError(f'No migration from version {version}')\n"
                "        data = migration(data)\n"
                "        version = int(data.get('version', version + 1))\n"
                "    return data\n"
            )
        if language in {"javascript", "typescript"}:
            return (
                "export const CURRENT_SAVE_VERSION = 2;\n\n"
                "const migrations = {\n"
                "  1: (data) => {\n"
                "    data.player = data.player || {};\n"
                "    data.player.perks = data.player.perks || [];\n"
                "    data.version = 2;\n"
                "    return data;\n"
                "  },\n"
                "};\n\n"
                "export function migrateSave(data) {\n"
                "  let version = Number(data.version || 1);\n"
                "  while (version < CURRENT_SAVE_VERSION) {\n"
                "    const migration = migrations[version];\n"
                "    if (!migration) throw new Error(`No migration from version ${version}`);\n"
                "    data = migration(data);\n"
                "    version = Number(data.version || version + 1);\n"
                "  }\n"
                "  return data;\n"
                "}\n"
            )
        if language == "gdscript":
            return (
                "extends Node\n\n"
                "const CURRENT_SAVE_VERSION := 2\n\n"
                "func migrate_save(data: Dictionary) -> Dictionary:\n"
                '    var version := int(data.get("version", 1))\n'
                "    while version < CURRENT_SAVE_VERSION:\n"
                "        if version == 1:\n"
                '            if not data.has("player"):\n'
                '                data["player"] = {}\n'
                '            player_data = data["player"]\n'
                '            player_data["perks"] = player_data.get("perks", [])\n'
                '            data["version"] = 2\n'
                '        version = int(data.get("version", version + 1))\n'
                "    return data\n"
            )
        return ""

    def _modding_api_module_content(self, language: str) -> str:
        """Return language-specific modding API boundary module content."""
        if language == "python":
            return (
                '"""Sandboxed boundary for user script extensibility."""\n\n'
                "from __future__ import annotations\n\n"
                "from typing import Any, Callable\n\n"
                "class ModdingAPI:\n"
                "    def __init__(self) -> None:\n"
                "        self._hooks: dict[str, list[Callable[[dict[str, Any]], None]]] = {}\n\n"
                "    def register_hook(self, hook_name: str, callback: Callable[[dict[str, Any]], None]) -> None:\n"
                "        self._hooks.setdefault(hook_name, []).append(callback)\n\n"
                "    def dispatch(self, hook_name: str, payload: dict[str, Any]) -> None:\n"
                "        for callback in self._hooks.get(hook_name, []):\n"
                "            callback(payload)\n"
            )
        if language in {"javascript", "typescript"}:
            return (
                "export class ModdingApi {\n"
                "  constructor() {\n"
                "    this.hooks = new Map();\n"
                "  }\n\n"
                "  registerHook(name, callback) {\n"
                "    if (!this.hooks.has(name)) this.hooks.set(name, []);\n"
                "    this.hooks.get(name).push(callback);\n"
                "  }\n\n"
                "  dispatch(name, payload = {}) {\n"
                "    for (const callback of this.hooks.get(name) || []) callback(payload);\n"
                "  }\n"
                "}\n"
            )
        if language == "gdscript":
            return (
                "extends Node\n\n"
                "var hooks: Dictionary = {}\n\n"
                "func register_hook(name: String, callback_ref: Callable) -> void:\n"
                "    if not hooks.has(name):\n"
                "        hooks[name] = []\n"
                "    hooks[name].append(callback_ref)\n\n"
                "func dispatch(name: String, payload: Dictionary) -> void:\n"
                "    if not hooks.has(name):\n"
                "        return\n"
                "    for cb in hooks[name]:\n"
                "        cb.call(payload)\n"
            )
        return ""

    def _sample_mod_content(self, language: str) -> str:
        """Return a sample mod file for the selected language."""
        if language == "python":
            return (
                '"""Sample mod hook implementation."""\n\n'
                "def register(api):\n"
                "    def on_turn_start(payload):\n"
                "        _ = payload\n"
                "    api.register_hook('on_turn_start', on_turn_start)\n"
            )
        if language in {"javascript", "typescript"}:
            return (
                "export function register(api) {\n"
                "  api.registerHook('on_turn_start', (payload) => {\n"
                "    void payload;\n"
                "  });\n"
                "}\n"
            )
        if language == "gdscript":
            return (
                "extends Node\n\n"
                "func register(api) -> void:\n"
                '    api.register_hook("on_turn_start", Callable(self, "_on_turn_start"))\n\n'
                "func _on_turn_start(payload: Dictionary) -> void:\n"
                "    pass\n"
            )
        return ""

    def _build_dependency_file(
        self,
        name: str,
        template: BaseProjectTemplate,
        entry_point: str,
        dependency_file: str,
    ) -> str:
        """Build language-specific dependency manifest content."""
        dependencies = [dep.strip() for dep in (template.dependencies or []) if dep and dep.strip()]
        language = (template.language or "python").lower()

        if dependency_file == "requirements.txt":
            return "\n".join(dependencies) + ("\n" if dependencies else "")

        if dependency_file == "package.json":
            dependency_map: dict[str, str] = {}
            for dep in dependencies:
                dep_name = re.split(r"[<>=~! ]", dep, maxsplit=1)[0].strip()
                if dep_name:
                    dependency_map[dep_name] = "latest"

            package = {
                "name": self._safe_package_name(name),
                "version": "1.0.0",
                "private": True,
                "description": template.description or "",
                "scripts": {"start": f"node {entry_point}"},
                "dependencies": dependency_map,
            }
            return f"{json.dumps(package, indent=2)}\n"

        if dependency_file == "go.mod":
            module_name = self._safe_package_name(name).replace("-", "_")
            return f"module {module_name}\n\ngo 1.21\n"

        if dependency_file == "project.csproj":
            project_name = self._safe_package_name(name).replace("-", "_")
            return (
                '<Project Sdk="Microsoft.NET.Sdk">\n'
                "  <PropertyGroup>\n"
                "    <OutputType>Exe</OutputType>\n"
                "    <TargetFramework>net8.0</TargetFramework>\n"
                "    <RootNamespace>"
                f"{project_name}"
                "</RootNamespace>\n"
                "  </PropertyGroup>\n"
                "</Project>\n"
            )

        if dependency_file == "project.godot":
            return '[application]\nconfig/name="Generated Project"\n'

        if dependencies:
            return "\n".join(dependencies) + "\n"
        if language == "typescript":
            return '{\n  "compilerOptions": {\n    "target": "ES2022"\n  }\n}\n'
        return ""

    def _build_readme(
        self,
        name: str,
        description: str,
        profile: dict[str, str],
        entry_point: str,
    ) -> str:
        """Build language-aware README content."""
        install_cmd = profile.get("install_cmd", "")
        run_cmd_template = profile.get("run_cmd", "")
        run_cmd = run_cmd_template.format(entry_point=entry_point).strip()

        commands: list[str] = []
        if install_cmd:
            commands.append(install_cmd)
        if run_cmd:
            commands.append(run_cmd)

        command_block = "\n".join(commands) if commands else "# No default run command configured."
        description_text = description or f"Generated {name} project."
        return f"# {name}\n\n{description_text}\n\n## Run\n\n```bash\n{command_block}\n```\n"

    def _safe_package_name(self, name: str) -> str:
        """Normalize project name for package/module manifests."""
        normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower())
        normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
        return normalized or "generated-project"

    def _generate_with_claude(
        self, name: str, template: BaseProjectTemplate, description: str
    ) -> tuple:
        """Generate using Claude API.

        Requires ANTHROPIC_API_KEY environment variable.
        """
        output_path = Path(self.output_root / name)
        output_path.mkdir(parents=True, exist_ok=True)

        model = "claude-3-haiku-20240307"
        tokens_used = 0
        profile = self._language_profile((template.language or "python").lower())
        file_structure = getattr(template, "file_structure", {}) or {
            profile["fallback_entry"]: "Main entry point"
        }
        entry_point = self._detect_entry_point(template, file_structure)

        try:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            if requests is None:
                raise RuntimeError("requests library not available")

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 4096,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""Create a {template.language} project: {name}
Description: {description}
Type: {template.type}
Entry point: {entry_point}

Generate ONLY the contents of {entry_point}. Output only file content.""",
                        }
                    ],
                },
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                code = result.get("content", [{}])[0].get("text", "")
                tokens_used = result.get("usage", {}).get("output_tokens", 0)

                entry_path = output_path / entry_point
                entry_path.parent.mkdir(parents=True, exist_ok=True)
                entry_path.write_text(
                    self._clean_code_output(code, entry_path.suffix.lower()),
                    encoding="utf-8",
                )
                self._write_support_files(
                    output_path=output_path,
                    name=name,
                    description=description,
                    template=template,
                    file_structure=file_structure,
                    entry_point=entry_point,
                )
                self._last_generation_diagnostics = {
                    "provider_chain": ["claude"],
                    "model": model,
                    "entry_point": entry_point,
                    "ollama_placeholder_files": 0,
                }

        except Exception as e:
            logging.getLogger(__name__).warning(f"Claude generation failed: {e}")
            self._last_generation_diagnostics = {
                "provider_chain": ["claude"],
                "model": model,
                "entry_point": entry_point,
                "error": str(e),
                "ollama_placeholder_files": 0,
            }

        return output_path, model, tokens_used * 0.00001, None, AIProviderType.CLAUDE

    def _generate_with_openai(
        self, name: str, template: BaseProjectTemplate, description: str
    ) -> tuple:
        """Generate using OpenAI GPT-4.

        Requires OPENAI_API_KEY environment variable.
        """
        output_path = Path(self.output_root / name)
        output_path.mkdir(parents=True, exist_ok=True)

        model = "gpt-4-turbo-preview"
        tokens_used = 0
        profile = self._language_profile((template.language or "python").lower())
        file_structure = getattr(template, "file_structure", {}) or {
            profile["fallback_entry"]: "Main entry point"
        }
        entry_point = self._detect_entry_point(template, file_structure)

        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            if requests is None:
                raise RuntimeError("requests library not available")

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""Create a {template.language} project: {name}
Description: {description}
Type: {template.type}
Entry point: {entry_point}

Generate ONLY the contents of {entry_point}. Output only file content.""",
                        }
                    ],
                    "max_tokens": 4096,
                },
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                code = (
                    result.get(
                        "choices",
                        [{}],
                    )[0]
                    .get("message", {})
                    .get("content", "")
                )
                tokens_used = result.get("usage", {}).get("completion_tokens", 0)

                entry_path = output_path / entry_point
                entry_path.parent.mkdir(parents=True, exist_ok=True)
                entry_path.write_text(
                    self._clean_code_output(code, entry_path.suffix.lower()),
                    encoding="utf-8",
                )
                self._write_support_files(
                    output_path=output_path,
                    name=name,
                    description=description,
                    template=template,
                    file_structure=file_structure,
                    entry_point=entry_point,
                )
                self._last_generation_diagnostics = {
                    "provider_chain": ["openai"],
                    "model": model,
                    "entry_point": entry_point,
                    "ollama_placeholder_files": 0,
                }

        except Exception as e:
            logging.getLogger(__name__).warning(f"OpenAI generation failed: {e}")
            self._last_generation_diagnostics = {
                "provider_chain": ["openai"],
                "model": model,
                "entry_point": entry_point,
                "error": str(e),
                "ollama_placeholder_files": 0,
            }

        return output_path, model, tokens_used * 0.00003, None, AIProviderType.OPENAI

    def _build_chatdev_task(
        self, name: str, template: BaseProjectTemplate, description: str
    ) -> str:
        """Build ChatDev task description from template."""
        task_lines = [
            f"Create a {template.type}: {name}",
            description,
        ]

        if isinstance(template, BaseGame):
            task_lines.append(
                f"Game engine: {template.engine or 'generic'}, "
                f"Genre: {template.genre or 'general'}, "
                f"Platforms: {', '.join(template.target_platforms)}"
            )
            if template.godot_translate:
                task_lines.append("Generate Python code suitable for translation to GDScript.")

        task_lines.extend(
            [
                f"Language: {template.language}",
                f"Dependencies: {', '.join(template.dependencies)}",
                "Include tests and documentation.",
            ]
        )

        if template.file_structure:
            files = ", ".join(list(template.file_structure.keys())[:12])
            task_lines.append(f"Target file structure: {files}")

        if getattr(template, "generation_hints", None):
            hints = "\n".join(f"- {hint}" for hint in template.generation_hints[:10])
            task_lines.append(f"Generation hints:\n{hints}")

        return "\n".join(task_lines)

    def run_health_check(self, include_packaging: bool = True) -> dict[str, Any]:
        """Run smoke probes for factory resilience and runtime wiring."""
        checks = [
            self._probe_provider_fallback(),
            self._probe_runtime_bootstrap(),
        ]
        if include_packaging:
            checks.append(self._probe_packaging_adapters(validate_hook_contracts=True))

        healthy = all(bool(check.get("passed")) for check in checks)
        return {
            "healthy": healthy,
            "checks": checks,
        }

    def run_doctor(
        self,
        strict_hooks: bool = False,
        include_examples: bool = True,
        include_health: bool = True,
        include_workspace: bool = False,
        recent_limit: int = 25,
    ) -> dict[str, Any]:
        """Run fail-fast factory diagnostics for degraded generation and packaging."""
        issues: list[dict[str, Any]] = []

        health_report: dict[str, Any] = {"healthy": True, "checks": []}
        if include_health:
            health_report = self.run_health_check(include_packaging=True)
            for check in health_report.get("checks", []):
                if not check.get("passed"):
                    issues.append(
                        {
                            "code": f"health_{check.get('name', 'unknown')}",
                            "message": f"Health check failed: {check.get('name')}",
                            "details": check.get("details", {}),
                        }
                    )

            if strict_hooks:
                packaging_check = next(
                    (
                        item
                        for item in health_report.get("checks", [])
                        if item.get("name") == "packaging_adapters"
                    ),
                    None,
                )
                hook_validation = (
                    (packaging_check or {}).get("details", {}).get("hook_validation", {})
                )
                for profile, report in hook_validation.items():
                    skipped = int(report.get("skipped", 0))
                    if skipped > 0:
                        issues.append(
                            {
                                "code": "hook_runtime_skipped",
                                "message": f"Hook runtime validation skipped for {profile} in strict mode",
                                "details": {
                                    "runtime_profile": profile,
                                    "skipped": skipped,
                                },
                            }
                        )

        quality_report = self._analyze_recent_generation_quality(limit=recent_limit)
        for quality_issue in quality_report.get("issues", []):
            issues.append(quality_issue)

        runtime_integrity = self._analyze_recent_runtime_integrity(
            strict_hooks=strict_hooks,
            limit=recent_limit,
        )
        for runtime_issue in runtime_integrity.get("issues", []):
            issues.append(runtime_issue)

        workspace_integrity: dict[str, Any] | None = None
        if include_workspace:
            workspace_integrity = self._probe_workspace_contention()
            if not workspace_integrity.get("passed"):
                issues.append(
                    {
                        "code": "workspace_extension_contention",
                        "message": "Workspace extension-host contention detected in IDE logs",
                        "details": workspace_integrity.get("details", {}),
                    }
                )

        examples_report: dict[str, Any] | None = None
        if include_examples:
            examples_report = self.inspect_reference_games()

        healthy = not issues
        recommendations = [
            "Keep fallback ratio below threshold by restoring preferred providers (ChatDev/Ollama).",
            "Treat placeholder output as a release blocker in production templates.",
            "Require executable hook contracts to pass before package/export.",
            "Use reference-game runtime signals to tune profile defaults per template family.",
        ]

        return {
            "healthy": healthy,
            "status": "healthy" if healthy else "degraded",
            "issues": issues,
            "health": health_report,
            "generation_quality": quality_report,
            "runtime_integrity": runtime_integrity,
            "workspace_integrity": workspace_integrity,
            "examples": examples_report,
            "recommendations": recommendations,
        }

    def run_doctor_fix(
        self,
        strict_hooks: bool = False,
        include_examples: bool = True,
        include_health: bool = True,
        include_workspace: bool = False,
        recent_limit: int = 25,
    ) -> dict[str, Any]:
        """Apply safe auto-remediation steps for doctor findings."""
        pre_fix = self.run_doctor(
            strict_hooks=strict_hooks,
            include_examples=include_examples,
            include_health=include_health,
            include_workspace=include_workspace,
            recent_limit=recent_limit,
        )
        issue_codes = {str(issue.get("code")) for issue in pre_fix.get("issues", [])}
        pre_examples = pre_fix.get("examples")
        examples_payload = pre_examples if isinstance(pre_examples, dict) else {"profiles": {}}
        patch_plan = self._build_autopilot_patch_plan(pre_fix, examples_payload)
        planned_actions = {str(item.get("action")) for item in patch_plan}
        actions: list[dict[str, Any]] = []

        if {
            "repeated_fallback",
            "high_placeholder_ratio",
        } & issue_codes or "provider_policy_hardening" in planned_actions:
            policy_action = self._apply_provider_policy_hardening()
            actions.append(policy_action)

        template_action = self._correct_template_runtime_profiles()
        actions.append(template_action)

        if "missing_runtime_bootstrap" in issue_codes:
            runtime_action = self._repair_runtime_bootstrap_for_recent_projects(limit=recent_limit)
            actions.append(runtime_action)

        packaging_action = self._regenerate_packaging_for_recent_projects(limit=recent_limit)
        actions.append(packaging_action)

        if "electron_release_hardening" in planned_actions:
            actions.append(self._apply_electron_release_hardening(limit=recent_limit))
        if "native_ops_hardening" in planned_actions:
            actions.append(self._apply_native_ops_hardening(limit=recent_limit))
        if "godot_export_hardening" in planned_actions:
            actions.append(self._apply_godot_export_hardening(limit=recent_limit))

        post_fix = self.run_doctor(
            strict_hooks=strict_hooks,
            include_examples=include_examples,
            include_health=include_health,
            include_workspace=include_workspace,
            recent_limit=recent_limit,
        )
        return {
            "healthy": post_fix.get("healthy", False),
            "status": ("healthy" if post_fix.get("healthy") else "degraded"),
            "pre_fix": pre_fix,
            "patch_plan": patch_plan,
            "actions": actions,
            "post_fix": post_fix,
        }

    def run_autopilot(
        self,
        fix: bool = False,
        strict_hooks: bool = False,
        include_examples: bool = True,
        include_workspace: bool = False,
        recent_limit: int = 25,
        example_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run doctor + example inspection + targeted patch plan as one loop."""
        doctor = self.run_doctor(
            strict_hooks=strict_hooks,
            include_examples=False,
            include_health=True,
            include_workspace=include_workspace,
            recent_limit=recent_limit,
        )
        examples = (
            self.inspect_reference_games(paths=example_paths)
            if include_examples
            else {"profiles": {}, "reports": [], "recommendations": []}
        )
        patch_plan = self._build_autopilot_patch_plan(doctor, examples)

        fix_report: dict[str, Any] | None = None
        if fix:
            fix_report = self.run_doctor_fix(
                strict_hooks=strict_hooks,
                include_examples=include_examples,
                include_health=True,
                include_workspace=include_workspace,
                recent_limit=recent_limit,
            )

        final_healthy = (
            fix_report.get("post_fix", {}).get("healthy")
            if isinstance(fix_report, dict)
            else doctor.get("healthy")
        )
        return {
            "healthy": bool(final_healthy),
            "status": "healthy" if final_healthy else "degraded",
            "doctor": doctor,
            "examples": examples,
            "patch_plan": patch_plan,
            "fix_applied": fix_report,
        }

    @staticmethod
    def _resolve_host_path(path_text: str) -> Path:
        """Resolve Windows-style path text on non-Windows hosts."""
        candidate = Path(path_text)
        if candidate.exists() or os.name == "nt":
            return candidate
        match = re.match(r"^([A-Za-z]):[\\/](.*)$", path_text)
        if not match:
            return candidate
        drive = match.group(1).lower()
        rest = match.group(2).replace("\\", "/")
        return Path(f"/mnt/{drive}/{rest}")

    def _candidate_vscode_logs_roots(self) -> list[Path]:
        """Return likely VS Code logs roots for current host/user."""
        candidates: list[Path] = []
        logs_parts = (
            "AppData",
            "Roaming",
            "Code",
            "logs",
        )
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            candidates.append(self._resolve_host_path(userprofile).joinpath(*logs_parts))
        candidates.append(Path.home().joinpath(*logs_parts))
        candidates.append(Path.home() / ".config" / "Code" / "logs")

        deduped: list[Path] = []
        seen: set[str] = set()
        for item in candidates:
            key = str(item)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def _candidate_vscode_settings_paths(self) -> list[Path]:
        """Return likely VS Code settings files used by the current user/session."""
        candidates: list[Path] = []
        settings_parts = (
            "AppData",
            "Roaming",
            "Code",
            "User",
            "settings.json",
        )
        xdg_settings_parts = (
            ".config",
            "Code",
            "User",
            "settings.json",
        )
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            base = self._resolve_host_path(userprofile)
            candidates.append(base.joinpath(*settings_parts))
        candidates.append(Path.home().joinpath(*settings_parts))
        candidates.append(Path.home().joinpath(*xdg_settings_parts))
        candidates.append(Path(__file__).resolve().parents[2] / ".vscode" / "settings.json")

        deduped: list[Path] = []
        seen: set[str] = set()
        for item in candidates:
            key = str(item)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def _latest_exthost_logs_root(self) -> Path | None:
        """Locate latest VS Code exthost logs root."""
        for logs_root in self._candidate_vscode_logs_roots():
            if not logs_root.exists():
                continue
            sessions = sorted(
                [item for item in logs_root.iterdir() if item.is_dir()],
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
            for session in sessions:
                window_roots = sorted(
                    [item for item in session.glob("window*/exthost") if item.is_dir()],
                    key=lambda item: item.stat().st_mtime,
                    reverse=True,
                )
                if window_roots:
                    return window_roots[0]
        return None

    @staticmethod
    def _read_log_tail(path: Path, max_lines: int = 2500) -> str:
        """Read bounded tail from a log file."""
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return ""
        if len(lines) > max_lines:
            lines = lines[-max_lines:]
        return "\n".join(lines)

    def _probe_workspace_contention(self) -> dict[str, Any]:
        """Detect extension-host contention signals from latest VS Code logs."""
        stale_threshold_seconds = 60 * 60
        details: dict[str, Any] = {
            "status": "ok",
            "exthost_root": None,
            "foreign_workspaces": [],
            "signals": [],
            "log_files": {},
            "stale": False,
            "latest_log_mtime_utc": None,
            "log_age_seconds": None,
        }
        exthost_root = self._latest_exthost_logs_root()
        if exthost_root is None:
            details["status"] = "no_logs"
            return {
                "name": "workspace_contention",
                "passed": True,
                "details": details,
            }

        details["exthost_root"] = str(exthost_root)
        output_roots = sorted(
            [item for item in exthost_root.glob("output_logging_*") if item.is_dir()],
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        latest_output = output_roots[0] if output_roots else None

        ruff_log: Path | None = None
        semgrep_log: Path | None = None
        if latest_output is not None:
            ruff_candidates = sorted(latest_output.glob("*Ruff Language Server.log"))
            semgrep_candidates = sorted(latest_output.glob("*Semgrep (Server).log"))
            if ruff_candidates:
                ruff_log = ruff_candidates[-1]
            if semgrep_candidates:
                semgrep_log = semgrep_candidates[-1]
        isort_log = exthost_root / "ms-python.isort" / "isort.log"

        for label, log_path in (
            ("ruff", ruff_log),
            ("isort", isort_log if isort_log.exists() else None),
            ("semgrep", semgrep_log),
        ):
            if log_path is not None and log_path.exists():
                details["log_files"][label] = str(log_path)

        latest_log_mtime: float | None = None
        for log_path in (ruff_log, isort_log if isort_log.exists() else None, semgrep_log):
            if log_path is None or not log_path.exists():
                continue
            try:
                mtime = log_path.stat().st_mtime
            except OSError:
                continue
            latest_log_mtime = max(latest_log_mtime or mtime, mtime)

        if latest_log_mtime is not None:
            now_ts = datetime.now(UTC).timestamp()
            age_seconds = max(0.0, now_ts - latest_log_mtime)
            details["latest_log_mtime_utc"] = datetime.fromtimestamp(
                latest_log_mtime, tz=UTC
            ).isoformat()
            details["log_age_seconds"] = int(age_seconds)

            latest_settings_mtime: float | None = None
            for settings_path in self._candidate_vscode_settings_paths():
                if not settings_path.exists():
                    continue
                try:
                    settings_mtime = settings_path.stat().st_mtime
                except OSError:
                    continue
                latest_settings_mtime = max(latest_settings_mtime or settings_mtime, settings_mtime)
            if latest_settings_mtime is not None:
                details["latest_settings_mtime_utc"] = datetime.fromtimestamp(
                    latest_settings_mtime, tz=UTC
                ).isoformat()
                if latest_log_mtime < latest_settings_mtime:
                    details["stale"] = True
                    details["status"] = "stale_logs_after_settings_change"
                    return {
                        "name": "workspace_contention",
                        "passed": True,
                        "details": details,
                    }

            if age_seconds > stale_threshold_seconds:
                details["stale"] = True
                details["status"] = "stale_logs"
                return {
                    "name": "workspace_contention",
                    "passed": True,
                    "details": details,
                }

        signals: list[str] = []
        foreign_workspaces: list[str] = []

        if ruff_log is not None and ruff_log.exists():
            ruff_text = self._read_log_tail(ruff_log)
            if "Cannot call write after a stream was destroyed" in ruff_text:
                signals.append("ruff_stream_destroyed")
            if "Stopping server timed out" in ruff_text:
                signals.append("ruff_server_timeout")
            foreign_workspaces.extend(re.findall(r"Registering workspace:\s*(.+)", ruff_text))

        if isort_log.exists():
            isort_text = self._read_log_tail(isort_log)
            if "Stopping server timed out" in isort_text:
                signals.append("isort_server_timeout")
            if "Client isort: connection to server is erroring" in isort_text:
                signals.append("isort_transport_error")
            foreign_workspaces.extend(
                re.findall(r"workspace\s+([^\r\n]+)", isort_text, flags=re.IGNORECASE)
            )

        if semgrep_log is not None and semgrep_log.exists():
            semgrep_text = self._read_log_tail(semgrep_log)
            if "positionEncoding" in semgrep_text:
                signals.append("semgrep_position_encoding_crash")
            if ".coverage" in semgrep_text and "No such file or directory open" in semgrep_text:
                signals.append("semgrep_missing_coverage_file")

        foreign_hits = sorted(
            {
                entry.strip()
                for entry in foreign_workspaces
                if any(marker in entry.lower() for marker in FOREIGN_WORKSPACE_MARKERS)
            }
        )
        details["foreign_workspaces"] = foreign_hits
        details["signals"] = sorted(set(signals))

        passed = not details["signals"] and not foreign_hits
        if not passed:
            details["status"] = "contention_detected"

        return {
            "name": "workspace_contention",
            "passed": passed,
            "details": details,
        }

    def _apply_provider_policy_hardening(self) -> dict[str, Any]:
        """Write provider policy that reduces avoidable ChatDev->Ollama churn."""
        policy = self._load_provider_policy()
        updated = dict(policy)
        updated.update(
            {
                "version": 1,
                "updated_at": datetime.now(UTC).isoformat(),
                "prefer_ollama_for_multifile": True,
                "fallback_guard": {
                    "max_placeholder_ratio": 0.25,
                    "max_consecutive_fallbacks": 1,
                },
            }
        )
        self._provider_policy_path.parent.mkdir(parents=True, exist_ok=True)
        self._provider_policy_path.write_text(
            f"{json.dumps(updated, indent=2)}\n", encoding="utf-8"
        )
        return {
            "action": "provider_policy_hardening",
            "applied": True,
            "path": str(self._provider_policy_path),
        }

    def _correct_template_runtime_profiles(self) -> dict[str, Any]:
        """Normalize template runtime_profile + game feature flags when missing/invalid."""
        try:
            import yaml  # type: ignore[import]
        except Exception as exc:
            return {
                "action": "template_runtime_profile_corrections",
                "applied": False,
                "error": f"yaml unavailable: {exc}",
                "updated_templates": [],
            }

        updated_templates: list[str] = []
        for template_path in sorted(self.template_dir.glob("*.yaml")):
            try:
                raw = yaml.safe_load(template_path.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            if not isinstance(raw, dict):
                continue

            changed = False
            runtime_profile = str(raw.get("runtime_profile", "") or "").strip().lower()
            inferred_runtime = self._infer_runtime_profile_from_dict(raw)
            if runtime_profile not in RUNTIME_PROFILES:
                raw["runtime_profile"] = inferred_runtime
                changed = True

            if str(raw.get("type", "")).lower() == "game":
                flags = raw.get("feature_flags")
                if not isinstance(flags, dict):
                    raw["feature_flags"] = dict(DEFAULT_GAME_FEATURE_FLAGS)
                    changed = True
                else:
                    for key, value in DEFAULT_GAME_FEATURE_FLAGS.items():
                        if key not in flags:
                            flags[key] = value
                            changed = True

            if changed:
                template_path.write_text(
                    yaml.safe_dump(raw, sort_keys=False, allow_unicode=False),
                    encoding="utf-8",
                )
                updated_templates.append(str(template_path))

        return {
            "action": "template_runtime_profile_corrections",
            "applied": bool(updated_templates),
            "updated_templates": updated_templates,
            "updated_count": len(updated_templates),
        }

    def _infer_runtime_profile_from_dict(self, template_data: dict[str, Any]) -> str:
        """Infer runtime profile from raw template mapping."""
        language = str(template_data.get("language", "")).lower()
        template_type = str(template_data.get("type", "")).lower()
        metadata = template_data.get("metadata", {}) or {}
        if language == "gdscript" or metadata.get("engine") == "godot":
            return "godot_export"
        if template_type == "game" and language in {"javascript", "typescript"}:
            return "electron_local"
        return "native_terminal"

    def _discover_recent_project_roots(self, limit: int = 25) -> list[Path]:
        """Find recent generated project roots based on generation diagnostics files."""
        diagnostics_paths = list(self.output_root.rglob("factory/generation_diagnostics.json"))
        diagnostics_paths.sort(
            key=lambda path: path.stat().st_mtime if path.exists() else 0,
            reverse=True,
        )
        roots: list[Path] = []
        seen: set[str] = set()
        for diag in diagnostics_paths:
            root = diag.parent.parent
            key = str(root)
            if key in seen:
                continue
            seen.add(key)
            roots.append(root)
            if len(roots) >= max(1, limit):
                break

        if roots:
            return roots

        # Fallback discovery for projects created before diagnostics were introduced.
        for runtime_profile_file in self.output_root.rglob("packaging/runtime_profile.json"):
            root = runtime_profile_file.parent.parent
            key = str(root)
            if key in seen:
                continue
            seen.add(key)
            roots.append(root)
            if len(roots) >= max(1, limit):
                break
        return roots

    def _regenerate_packaging_for_recent_projects(self, limit: int = 25) -> dict[str, Any]:
        """Regenerate packaging adapter artifacts + hook health for recent projects."""
        updated_projects: list[str] = []
        failures: list[dict[str, str]] = []

        for root in self._discover_recent_project_roots(limit=limit):
            runtime_profile_file = root / "packaging" / "runtime_profile.json"
            if not runtime_profile_file.exists():
                continue
            try:
                runtime_data = json.loads(runtime_profile_file.read_text(encoding="utf-8"))
            except Exception as exc:
                failures.append(
                    {"project": str(root), "error": f"invalid runtime_profile.json: {exc}"}
                )
                continue

            profile = str(runtime_data.get("runtime_profile", "native_terminal"))
            entry_point = str(runtime_data.get("entry_point", "main.py"))
            language = str(runtime_data.get("language", "python"))
            project_type = str(runtime_data.get("project_type", "game"))
            context = PackagingContext(
                name=root.name,
                runtime_profile=profile,
                entry_point=entry_point,
                language=language,
                project_type=project_type,
                metadata={},
            )
            try:
                adapter = build_runtime_packaging_adapter(profile)
                for relpath, content in adapter.build_file_map(context).items():
                    target = root / relpath
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")

                preflight = adapter.validate_layout(root, context)
                preflight_path = root / "packaging" / "health" / "preflight.json"
                preflight_path.parent.mkdir(parents=True, exist_ok=True)
                preflight_path.write_text(f"{json.dumps(preflight, indent=2)}\n", encoding="utf-8")

                hook_report = adapter.validate_executable_hooks(root, context)
                hook_path = root / "packaging" / "health" / "hook_validation.json"
                hook_path.parent.mkdir(parents=True, exist_ok=True)
                hook_path.write_text(f"{json.dumps(hook_report, indent=2)}\n", encoding="utf-8")
                updated_projects.append(str(root))
            except Exception as exc:
                failures.append({"project": str(root), "error": str(exc)})

        return {
            "action": "packaging_hook_regeneration",
            "applied": bool(updated_projects),
            "updated_projects": updated_projects,
            "updated_count": len(updated_projects),
            "failures": failures,
        }

    def _build_autopilot_patch_plan(
        self, doctor_report: dict[str, Any], examples_report: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Build targeted patch plan from doctor+example diagnostics."""
        issues = doctor_report.get("issues", [])
        issue_codes = {str(issue.get("code")) for issue in issues}
        profiles = examples_report.get("profiles", {}) if isinstance(examples_report, dict) else {}

        plan: list[dict[str, Any]] = []
        if {"repeated_fallback", "high_placeholder_ratio"} & issue_codes:
            plan.append(
                {
                    "priority": "high",
                    "action": "provider_policy_hardening",
                    "why": "Fallback churn or placeholder ratio indicates degraded generation reliability.",
                    "auto_fix": True,
                }
            )
        packaging_codes = {
            "hook_runtime_skipped",
            "health_packaging_adapters",
            "missing_packaging_preflight",
            "failed_packaging_preflight",
            "missing_hook_validation_report",
            "failed_hook_validation_report",
            "skipped_hook_runtime_validation",
        }
        if issue_codes & packaging_codes:
            plan.append(
                {
                    "priority": "high",
                    "action": "packaging_hook_regeneration",
                    "why": "Packaging hook contracts need deterministic regeneration and validation.",
                    "auto_fix": True,
                }
            )
        if "missing_runtime_bootstrap" in issue_codes:
            plan.append(
                {
                    "priority": "high",
                    "action": "runtime_bootstrap_repair",
                    "why": "Recent generated projects are missing active runtime scaffold wiring.",
                    "auto_fix": True,
                }
            )
        if "workspace_extension_contention" in issue_codes:
            plan.append(
                {
                    "priority": "high",
                    "action": "workspace_window_isolation",
                    "why": "Active IDE workspace includes heavy foreign roots or crash-loop extension signals.",
                    "auto_fix": False,
                }
            )
        if int(profiles.get("electron_local", 0) or 0) > 0:
            plan.append(
                {
                    "priority": "medium",
                    "action": "electron_release_hardening",
                    "why": "Reference installs show Electron asar/updater/Steam integration norms.",
                    "auto_fix": False,
                }
            )
        if int(profiles.get("native_terminal", 0) or 0) > 0:
            plan.append(
                {
                    "priority": "medium",
                    "action": "native_ops_hardening",
                    "why": "Reference installs emphasize versioned save slots, manuals, and runtime logs.",
                    "auto_fix": False,
                }
            )
        if int(profiles.get("godot_export", 0) or 0) > 0:
            plan.append(
                {
                    "priority": "medium",
                    "action": "godot_export_hardening",
                    "why": "Reference installs confirm pck/plugin export expectations for Steam packaging.",
                    "auto_fix": False,
                }
            )
        if not plan:
            plan.append(
                {
                    "priority": "low",
                    "action": "monitor",
                    "why": "No critical degradation found; keep doctor/autopilot in CI cadence.",
                    "auto_fix": False,
                }
            )
        return plan

    def _recent_project_contexts(
        self,
        *,
        limit: int = 25,
        runtime_profiles: set[str] | None = None,
    ) -> list[tuple[Path, dict[str, Any]]]:
        """Return recent project roots plus parsed runtime profile metadata."""
        allowed_profiles = {item.lower() for item in (runtime_profiles or set())}
        contexts: list[tuple[Path, dict[str, Any]]] = []
        for root in self._discover_recent_project_roots(limit=limit):
            runtime_profile_file = root / "packaging" / "runtime_profile.json"
            if not runtime_profile_file.exists():
                continue
            try:
                runtime_data = json.loads(runtime_profile_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(runtime_data, dict):
                continue
            profile = str(runtime_data.get("runtime_profile", "")).strip().lower()
            if allowed_profiles and profile not in allowed_profiles:
                continue
            contexts.append((root, runtime_data))
        return contexts

    def _apply_electron_release_hardening(self, limit: int = 25) -> dict[str, Any]:
        """Apply release/update hardening scaffolds for Electron runtime profiles."""
        profiles = {"electron_local", "electron_web_wrapper"}
        updated_projects: list[str] = []
        failures: list[dict[str, str]] = []

        for root, runtime_data in self._recent_project_contexts(
            limit=limit, runtime_profiles=profiles
        ):
            try:
                profile = str(runtime_data.get("runtime_profile", "electron_local"))
                steam_adapter_path = root / "packaging" / "electron" / "steam_adapter.json"
                steam_adapter_path.parent.mkdir(parents=True, exist_ok=True)
                if steam_adapter_path.exists():
                    adapter_data = json.loads(steam_adapter_path.read_text(encoding="utf-8"))
                    if not isinstance(adapter_data, dict):
                        adapter_data = {}
                else:
                    adapter_data = {}
                adapter_data.update(
                    {
                        "steamworks_required": True,
                        "runtime_profile": profile,
                        "asar_aware": True,
                        "updater": {
                            "provider": "squirrel",
                            "channels": [
                                "stable",
                                "beta",
                                "canary",
                            ],
                            "rollback_safe": True,
                        },
                    }
                )
                steam_adapter_path.write_text(
                    f"{json.dumps(adapter_data, indent=2)}\n",
                    encoding="utf-8",
                )

                asar_manifest = {
                    "asar": True,
                    "unpack_patterns": ["**/*.node", "**/steam_api*.dll"],
                    "runtime_profile": profile,
                }
                (root / "packaging" / "electron" / "asar_manifest.json").write_text(
                    f"{json.dumps(asar_manifest, indent=2)}\n",
                    encoding="utf-8",
                )
                release_channels = {
                    "default": "stable",
                    "channels": [
                        "stable",
                        "beta",
                        "canary",
                    ],
                    "rollback_safe": True,
                }
                (root / "packaging" / "electron" / "release_channels.json").write_text(
                    f"{json.dumps(release_channels, indent=2)}\n",
                    encoding="utf-8",
                )
                updated_projects.append(str(root))
            except Exception as exc:
                failures.append({"project": str(root), "error": str(exc)})

        return {
            "action": "electron_release_hardening",
            "applied": bool(updated_projects),
            "updated_projects": updated_projects,
            "updated_count": len(updated_projects),
            "failures": failures,
        }

    def _apply_native_ops_hardening(self, limit: int = 25) -> dict[str, Any]:
        """Apply operational maturity scaffolds for native terminal projects."""
        updated_projects: list[str] = []
        failures: list[dict[str, str]] = []

        for root, _runtime_data in self._recent_project_contexts(
            limit=limit, runtime_profiles={"native_terminal"}
        ):
            try:
                ops_root = root / "packaging" / "native" / "ops"
                ops_root.mkdir(parents=True, exist_ok=True)
                save_policy = {
                    "slot_pattern": "save_v{schema}_slot{index}.sav",
                    "schema_version_key": "save_schema_version",
                    "migration_required": True,
                }
                (ops_root / "save_policy.json").write_text(
                    f"{json.dumps(save_policy, indent=2)}\n",
                    encoding="utf-8",
                )
                logging_policy = {
                    "log_file": "run.log",
                    "rotation": {"max_files": 5, "max_mb": 10},
                    "include_runtime_profile": True,
                }
                (ops_root / "logging_policy.json").write_text(
                    f"{json.dumps(logging_policy, indent=2)}\n",
                    encoding="utf-8",
                )
                (root / "packaging" / "native" / "OPERATIONS.md").write_text(
                    (
                        "# Native Operations Playbook\n\n"
                        "- Save files should be versioned and migrated before load.\n"
                        "- Keep runtime logs enabled in release builds for supportability.\n"
                        "- Validate packaging/native/hooks contracts before each release.\n"
                    ),
                    encoding="utf-8",
                )
                updated_projects.append(str(root))
            except Exception as exc:
                failures.append({"project": str(root), "error": str(exc)})

        return {
            "action": "native_ops_hardening",
            "applied": bool(updated_projects),
            "updated_projects": updated_projects,
            "updated_count": len(updated_projects),
            "failures": failures,
        }

    def _apply_godot_export_hardening(self, limit: int = 25) -> dict[str, Any]:
        """Apply export/plugin hardening scaffolds for Godot runtime profile."""
        updated_projects: list[str] = []
        failures: list[dict[str, str]] = []

        for root, _runtime_data in self._recent_project_contexts(
            limit=limit, runtime_profiles={"godot_export"}
        ):
            try:
                godot_root = root / "packaging" / "godot"
                godot_root.mkdir(parents=True, exist_ok=True)
                export_contract = {
                    "runtime_profile": "godot_export",
                    "required_artifacts": ["*.pck", "packaging/godot/export_presets.cfg"],
                    "steam_plugin_required": True,
                }
                (godot_root / "export_contract.json").write_text(
                    f"{json.dumps(export_contract, indent=2)}\n",
                    encoding="utf-8",
                )
                plugin_hooks = {
                    "plugin": "godot_steam_plugin",
                    "hooks": ["overlay.enable", "achievement.unlock"],
                    "validation": "static_and_runtime",
                }
                (godot_root / "plugin_hooks.json").write_text(
                    f"{json.dumps(plugin_hooks, indent=2)}\n",
                    encoding="utf-8",
                )
                updated_projects.append(str(root))
            except Exception as exc:
                failures.append({"project": str(root), "error": str(exc)})

        return {
            "action": "godot_export_hardening",
            "applied": bool(updated_projects),
            "updated_projects": updated_projects,
            "updated_count": len(updated_projects),
            "failures": failures,
        }

    def _probe_provider_fallback(self) -> dict[str, Any]:
        """Verify ChatDev generation failure falls back to Ollama output."""
        import tempfile
        from unittest.mock import patch

        from src.factories.generators.chatdev_generator import \
            ChatDevGenerationResult

        class _FakeResponse:
            status_code = 200

            def json(self) -> dict[str, Any]:
                return {"response": "print('fallback-ok')\n", "eval_count": 16}

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_root = Path(temp_dir)
                chatdev_dir = temp_root / "ChatDev"
                chatdev_dir.mkdir(parents=True, exist_ok=True)
                (chatdev_dir / "run.py").write_text("print('runner')\n", encoding="utf-8")
                (chatdev_dir / "WareHouse").mkdir(parents=True, exist_ok=True)

                factory = ProjectFactory(template_dir=self.template_dir)
                factory.output_root = temp_root / "generated"
                factory.output_root.mkdir(parents=True, exist_ok=True)
                factory.orchestrator.chatdev_path = chatdev_dir
                factory.orchestrator.ollama_available = True

                template = {
                    "name": "HealthFallbackGame",
                    "type": "game",
                    "language": "python",
                    "description": "health probe provider fallback",
                    "dependencies": [],
                    "file_structure": {"main.py": "Entry point"},
                    "complexity": 8,
                    "requires_multifile": True,
                    "runtime_profile": "native_terminal",
                    "feature_flags": {
                        "data_pipeline": False,
                        "event_router": False,
                        "save_migration": False,
                        "modding_api": False,
                    },
                }

                def _fake_generate(self, *_args, **_kwargs):
                    return ChatDevGenerationResult(
                        project_name="HealthFallbackGame",
                        warehouse_path=chatdev_dir / "WareHouse",
                        model_used="qwen2.5-coder:14b",
                        token_cost=0.0,
                        created_at="2026-02-07T00:00:00",
                        task_description="health",
                        success=False,
                        error_message="forced health fallback",
                    )

                with (
                    patch(
                        "src.factories.generators.chatdev_generator.ChatDevGenerator.generate",
                        _fake_generate,
                    ),
                    patch("requests.post", lambda *args, **kwargs: _FakeResponse()),
                    patch("time.sleep", lambda *args, **kwargs: None),
                ):
                    result = factory.create(
                        name="HealthFallbackGame",
                        custom_template=template,
                        ai_provider="chatdev",
                        auto_register=False,
                    )

                main_exists = (result.output_path / "main.py").exists()
                passed = result.ai_provider == "ollama" and main_exists
                return {
                    "name": "provider_fallback",
                    "passed": passed,
                    "details": {
                        "provider": result.ai_provider,
                        "main_exists": main_exists,
                    },
                }
        except Exception as exc:
            return {
                "name": "provider_fallback",
                "passed": False,
                "details": {"error": str(exc)},
            }

    def _probe_runtime_bootstrap(self) -> dict[str, Any]:
        """Verify runtime scaffolds are actively wired into generated entrypoints."""
        import subprocess
        import sys
        import tempfile
        from unittest.mock import patch

        class _FakeResponse:
            status_code = 200

            def json(self) -> dict[str, Any]:
                return {
                    "response": "def run():\n    return 0\n\nif __name__ == '__main__':\n    run()\n",
                    "eval_count": 16,
                }

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_root = Path(temp_dir)
                factory = ProjectFactory(template_dir=self.template_dir)
                factory.output_root = temp_root / "generated"
                factory.output_root.mkdir(parents=True, exist_ok=True)
                factory.orchestrator.chatdev_path = None
                factory.orchestrator.ollama_available = True

                template = {
                    "name": "HealthRuntimeBootstrap",
                    "type": "game",
                    "language": "python",
                    "description": "health probe runtime bootstrap",
                    "dependencies": [],
                    "file_structure": {"main.py": "Entry point"},
                    "complexity": 2,
                    "requires_multifile": False,
                    "runtime_profile": "native_terminal",
                    "feature_flags": {
                        "data_pipeline": True,
                        "event_router": True,
                        "save_migration": True,
                        "modding_api": True,
                    },
                }

                with (
                    patch("requests.post", lambda *args, **kwargs: _FakeResponse()),
                    patch("time.sleep", lambda *args, **kwargs: None),
                ):
                    result = factory.create(
                        name="HealthRuntimeBootstrap",
                        custom_template=template,
                        ai_provider="ollama",
                        auto_register=False,
                    )

                main_path = result.output_path / "main.py"
                runtime_module = result.output_path / "game" / "runtime_services.py"
                marker_present = (
                    "# NuSyQ runtime bootstrap (auto-generated)"
                    in main_path.read_text(encoding="utf-8")
                )
                runtime_ok = runtime_module.exists() and marker_present

                run_result = subprocess.run(
                    [sys.executable, "main.py"],
                    cwd=result.output_path,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                passed = runtime_ok and run_result.returncode == 0
                return {
                    "name": "runtime_bootstrap",
                    "passed": passed,
                    "details": {
                        "runtime_module": runtime_module.exists(),
                        "marker_present": marker_present,
                        "returncode": run_result.returncode,
                    },
                }
        except Exception as exc:
            return {
                "name": "runtime_bootstrap",
                "passed": False,
                "details": {"error": str(exc)},
            }

    def _probe_packaging_adapters(self, validate_hook_contracts: bool = True) -> dict[str, Any]:
        """Verify each runtime profile emits executable adapter outputs."""
        import tempfile
        from unittest.mock import patch

        class _FakeResponse:
            status_code = 200

            def json(self) -> dict[str, Any]:
                return {"response": "print('packaging-ok')\n", "eval_count": 8}

        expected_paths = {
            "electron_local": "packaging/electron/hooks/steam_overlay_hook.js",
            "electron_web_wrapper": "packaging/electron/hooks/web_wrapper_launcher.js",
            "godot_export": "packaging/godot/hooks/steam_overlay_hook.gd",
            "native_terminal": "packaging/native/hooks/steam_overlay_hook.py",
        }
        failures: list[dict[str, Any]] = []
        hook_validation: dict[str, dict[str, Any]] = {}

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_root = Path(temp_dir)
                factory = ProjectFactory(template_dir=self.template_dir)
                factory.output_root = temp_root / "generated"
                factory.output_root.mkdir(parents=True, exist_ok=True)
                factory.orchestrator.chatdev_path = None
                factory.orchestrator.ollama_available = True

                with (
                    patch("requests.post", lambda *args, **kwargs: _FakeResponse()),
                    patch("time.sleep", lambda *args, **kwargs: None),
                ):
                    for profile, expected in expected_paths.items():
                        template = {
                            "name": f"HealthPackaging{profile}",
                            "type": "game",
                            "language": "python",
                            "description": "health probe packaging adapters",
                            "dependencies": [],
                            "file_structure": {"main.py": "Entry point"},
                            "complexity": 2,
                            "requires_multifile": False,
                            "runtime_profile": profile,
                            "feature_flags": {
                                "data_pipeline": False,
                                "event_router": False,
                                "save_migration": False,
                                "modding_api": False,
                            },
                        }
                        result = factory.create(
                            name=f"HealthPackaging{profile}",
                            custom_template=template,
                            ai_provider="ollama",
                            auto_register=False,
                        )
                        expected_exists = (result.output_path / expected).exists()
                        preflight_path = (
                            result.output_path / "packaging" / "health" / "preflight.json"
                        )
                        preflight_healthy = False
                        if preflight_path.exists():
                            try:
                                preflight_data = json.loads(
                                    preflight_path.read_text(encoding="utf-8")
                                )
                                preflight_healthy = bool(preflight_data.get("healthy"))
                            except Exception:
                                preflight_healthy = False

                        hook_healthy = True
                        if validate_hook_contracts:
                            adapter = build_runtime_packaging_adapter(profile)
                            context = PackagingContext(
                                name=f"HealthPackaging{profile}",
                                runtime_profile=profile,
                                entry_point="main.py",
                                language="python",
                                project_type="game",
                                metadata={},
                            )
                            hook_report = adapter.validate_executable_hooks(
                                result.output_path, context
                            )
                            hook_validation[profile] = hook_report
                            hook_healthy = bool(hook_report.get("healthy"))

                        if not expected_exists or not preflight_healthy or not hook_healthy:
                            failures.append(
                                {
                                    "runtime_profile": profile,
                                    "expected_exists": expected_exists,
                                    "preflight_healthy": preflight_healthy,
                                    "hook_healthy": hook_healthy,
                                }
                            )
            return {
                "name": "packaging_adapters",
                "passed": not failures,
                "details": {
                    "profiles_checked": list(expected_paths.keys()),
                    "failures": failures,
                    "hook_validation": hook_validation,
                },
            }
        except Exception as exc:
            return {
                "name": "packaging_adapters",
                "passed": False,
                "details": {"error": str(exc)},
            }

    def _analyze_recent_generation_quality(self, limit: int = 25) -> dict[str, Any]:
        """Analyze recent generation diagnostics for fallback/placeholder degradation."""
        diagnostics_paths = list(self.output_root.rglob("factory/generation_diagnostics.json"))
        diagnostics_paths.sort(
            key=lambda path: path.stat().st_mtime if path.exists() else 0,
            reverse=True,
        )
        recent_paths = diagnostics_paths[: max(0, int(limit))]

        runs: list[dict[str, Any]] = []
        for path in recent_paths:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            data["_path"] = str(path)
            runs.append(data)

        fallback_runs = 0
        placeholder_runs = 0
        max_placeholder_ratio = 0.0
        issues: list[dict[str, Any]] = []

        for run in runs:
            provider_chain = run.get("provider_chain", [])
            if isinstance(provider_chain, list) and len(provider_chain) > 1:
                fallback_runs += 1

            targeted = int(run.get("ollama_files_targeted", 0) or 0)
            placeholders = int(run.get("ollama_placeholder_files", 0) or 0)
            ratio = float(placeholders / targeted) if targeted > 0 else 0.0
            if ratio > 0:
                placeholder_runs += 1
            max_placeholder_ratio = max(max_placeholder_ratio, ratio)

        if fallback_runs >= 2:
            issues.append(
                {
                    "code": "repeated_fallback",
                    "message": "Repeated provider fallback detected in recent generations",
                    "details": {
                        "fallback_runs": fallback_runs,
                        "sample_size": len(runs),
                    },
                }
            )

        if max_placeholder_ratio >= 0.4:
            issues.append(
                {
                    "code": "high_placeholder_ratio",
                    "message": "High placeholder ratio detected in generated outputs",
                    "details": {
                        "max_placeholder_ratio": round(max_placeholder_ratio, 3),
                        "placeholder_runs": placeholder_runs,
                        "sample_size": len(runs),
                    },
                }
            )

        return {
            "sample_size": len(runs),
            "fallback_runs": fallback_runs,
            "placeholder_runs": placeholder_runs,
            "max_placeholder_ratio": round(max_placeholder_ratio, 3),
            "degraded": bool(issues),
            "issues": issues,
        }

    def _analyze_recent_runtime_integrity(
        self,
        *,
        strict_hooks: bool = False,
        limit: int = 25,
    ) -> dict[str, Any]:
        """Analyze runtime bootstrap + packaging health for recent generated projects."""
        issues: list[dict[str, Any]] = []
        inspected = 0

        for root, runtime_data in self._recent_project_contexts(limit=limit):
            inspected += 1
            profile = str(runtime_data.get("runtime_profile", "native_terminal"))
            language = str(runtime_data.get("language", "python")).lower()
            entry_point = str(runtime_data.get("entry_point", "main.py"))
            project_ref = str(root)

            diagnostics: dict[str, Any] = {}
            diagnostics_path = root / "factory" / "generation_diagnostics.json"
            if diagnostics_path.exists():
                try:
                    parsed = json.loads(diagnostics_path.read_text(encoding="utf-8"))
                    diagnostics = parsed if isinstance(parsed, dict) else {}
                except Exception:
                    diagnostics = {}

            active_features = diagnostics.get("feature_flags", [])
            if not isinstance(active_features, list):
                active_features = []
            expects_runtime_bootstrap = language == "python" and bool(active_features)

            if expects_runtime_bootstrap:
                marker_ok = self._python_entrypoint_has_runtime_marker(root, entry_point)
                runtime_module_ok = (root / "game" / "runtime_services.py").exists()
                if not marker_ok or not runtime_module_ok:
                    issues.append(
                        {
                            "code": "missing_runtime_bootstrap",
                            "message": "Runtime scaffolds are not actively wired into generated entrypoint",
                            "details": {
                                "project": project_ref,
                                "runtime_profile": profile,
                                "entry_point": entry_point,
                                "marker_present": marker_ok,
                                "runtime_module_present": runtime_module_ok,
                            },
                        }
                    )

            preflight_path = root / "packaging" / "health" / "preflight.json"
            if not preflight_path.exists():
                issues.append(
                    {
                        "code": "missing_packaging_preflight",
                        "message": "Packaging preflight report is missing",
                        "details": {"project": project_ref, "runtime_profile": profile},
                    }
                )
            else:
                try:
                    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
                    if not bool(preflight.get("healthy")):
                        issues.append(
                            {
                                "code": "failed_packaging_preflight",
                                "message": "Packaging preflight report is unhealthy",
                                "details": {
                                    "project": project_ref,
                                    "runtime_profile": profile,
                                    "missing_paths": preflight.get("missing_paths", []),
                                },
                            }
                        )
                except Exception as exc:
                    issues.append(
                        {
                            "code": "failed_packaging_preflight",
                            "message": "Packaging preflight report is unreadable",
                            "details": {
                                "project": project_ref,
                                "runtime_profile": profile,
                                "error": str(exc),
                            },
                        }
                    )

            if strict_hooks:
                hook_path = root / "packaging" / "health" / "hook_validation.json"
                if not hook_path.exists():
                    issues.append(
                        {
                            "code": "missing_hook_validation_report",
                            "message": "Hook validation report is missing in strict mode",
                            "details": {"project": project_ref, "runtime_profile": profile},
                        }
                    )
                else:
                    try:
                        hook_report = json.loads(hook_path.read_text(encoding="utf-8"))
                        failed = int(hook_report.get("failed", 0) or 0)
                        skipped = int(hook_report.get("skipped", 0) or 0)
                        if failed > 0:
                            issues.append(
                                {
                                    "code": "failed_hook_validation_report",
                                    "message": "Hook validation report contains failed checks",
                                    "details": {
                                        "project": project_ref,
                                        "runtime_profile": profile,
                                        "failed": failed,
                                    },
                                }
                            )
                        if skipped > 0:
                            issues.append(
                                {
                                    "code": "skipped_hook_runtime_validation",
                                    "message": "Hook runtime checks were skipped in strict mode",
                                    "details": {
                                        "project": project_ref,
                                        "runtime_profile": profile,
                                        "skipped": skipped,
                                    },
                                }
                            )
                    except Exception as exc:
                        issues.append(
                            {
                                "code": "failed_hook_validation_report",
                                "message": "Hook validation report is unreadable",
                                "details": {
                                    "project": project_ref,
                                    "runtime_profile": profile,
                                    "error": str(exc),
                                },
                            }
                        )

        return {
            "inspected_projects": inspected,
            "degraded": bool(issues),
            "issues": issues,
        }

    def _repair_runtime_bootstrap_for_recent_projects(self, limit: int = 25) -> dict[str, Any]:
        """Repair missing runtime bootstrap wiring for recent Python project outputs."""
        updated_projects: list[str] = []
        failures: list[dict[str, str]] = []

        for root, runtime_data in self._recent_project_contexts(limit=limit):
            language = str(runtime_data.get("language", "python")).lower()
            if language != "python":
                continue

            entry_point = str(runtime_data.get("entry_point", "main.py"))
            entry_path = root / entry_point
            if not entry_path.exists():
                failures.append(
                    {"project": str(root), "error": f"entrypoint missing: {entry_point}"}
                )
                continue

            before_marker = self._python_entrypoint_has_runtime_marker(root, entry_point)
            before_runtime_module = (root / "game" / "runtime_services.py").exists()
            try:
                self._write_if_missing(
                    root,
                    "game/runtime_services.py",
                    self._runtime_services_module_content(),
                )
                self._patch_python_entrypoint_for_runtime(root, entry_point)
            except Exception as exc:
                failures.append({"project": str(root), "error": str(exc)})
                continue

            after_marker = self._python_entrypoint_has_runtime_marker(root, entry_point)
            after_runtime_module = (root / "game" / "runtime_services.py").exists()
            changed = (not before_marker and after_marker) or (
                not before_runtime_module and after_runtime_module
            )
            if changed:
                updated_projects.append(str(root))

        return {
            "action": "runtime_bootstrap_repair",
            "applied": bool(updated_projects),
            "updated_projects": updated_projects,
            "updated_count": len(updated_projects),
            "failures": failures,
        }

    def _python_entrypoint_has_runtime_marker(self, root: Path, entry_point: str) -> bool:
        """Check whether Python entrypoint contains runtime bootstrap marker."""
        entry_path = root / entry_point
        if not entry_path.exists() or entry_path.suffix.lower() != ".py":
            return False
        try:
            text = entry_path.read_text(encoding="utf-8")
        except Exception:
            return False
        return "# NuSyQ runtime bootstrap (auto-generated)" in text

    def inspect_reference_games(self, paths: list[str] | None = None) -> dict[str, Any]:
        """Inspect reference game installations for runtime/packaging patterns."""
        default_paths = [
            "/mnt/c/Program Files (x86)/Steam/steamapps/common/Bitburner",
            "/mnt/c/Program Files (x86)/Steam/steamapps/common/Dungeon Team",
            "/mnt/c/Program Files (x86)/Steam/steamapps/common/Cogmind",
            "/mnt/c/Program Files (x86)/Steam/steamapps/common/Path of Achra",
        ]
        target_paths = [Path(p) for p in (paths or default_paths)]

        profiles: dict[str, int] = {
            "electron_local": 0,
            "electron_web_wrapper": 0,
            "godot_export": 0,
            "native_terminal": 0,
            "unknown": 0,
        }
        reports: list[dict[str, Any]] = []

        for candidate in target_paths:
            report = self._inspect_reference_game_path(candidate)
            reports.append(report)
            profile = str(report.get("runtime_profile", "unknown"))
            profiles[profile] = profiles.get(profile, 0) + 1

        recommendations = [
            "Use runtime_profile-driven packaging adapters as mandatory generation step.",
            "Preserve save compatibility via version migrations and schema validation.",
            "Keep data-driven content pipeline (json/yaml) as first-class source of truth.",
            "Treat Steam overlay and hook shims as executable runtime contracts.",
        ]

        return {
            "inspected_paths": [str(p) for p in target_paths],
            "profiles": profiles,
            "reports": reports,
            "recommendations": recommendations,
        }

    def _inspect_reference_game_path(self, path: Path) -> dict[str, Any]:
        """Inspect one reference game install path and infer platform signals."""
        report: dict[str, Any] = {
            "path": str(path),
            "exists": path.exists(),
            "runtime_profile": "unknown",
            "signals": [],
            "recommendations": [],
        }
        if not path.exists():
            report["recommendations"] = ["Install path not found; skip or provide explicit path."]
            return report

        signals: list[str] = []
        runtime_profile = "unknown"

        # Electron signatures (Bitburner / Dungeon Team pattern)
        if (path / "resources" / "app" / "package.json").exists():
            signals.append("electron_app_package_json")
            runtime_profile = "electron_local"
        if (path / "resources" / "app.asar").exists():
            signals.append("electron_app_asar")
            runtime_profile = "electron_local"
        if (path / "Squirrel.exe").exists():
            signals.append("electron_squirrel_updater")
        if any(path.glob("steamworks*.node")) or any(path.glob("**/steamworks*.node")):
            signals.append("steamworks_node_binary")
        if any(path.glob("locales/*.pak")):
            signals.append("chromium_locales_pack")
        if (path / "steam_api64.dll").exists() or (path / "steam_api.dll").exists():
            signals.append("steam_api_runtime")

        # Godot signatures (Path of Achra pattern)
        if any(path.glob("*.pck")):
            signals.append("godot_pck_bundle")
            runtime_profile = "godot_export"
        if any(path.glob("**/project.godot")):
            signals.append("godot_project_manifest")
            runtime_profile = "godot_export"
        if any(path.glob("**/*godot*.dll")):
            signals.append("godot_runtime_plugin")

        # Native executable + mature operations signatures (Cogmind pattern)
        exe_files = list(path.glob("*.exe"))
        if exe_files and runtime_profile == "unknown":
            runtime_profile = "native_terminal"
            signals.append("native_executable")
        if (path / "manual.txt").exists() or (path / "COGMIND-README.txt").exists():
            signals.append("operational_manual_present")
            if runtime_profile == "unknown":
                runtime_profile = "native_terminal"
        if (path / "user").exists() and any((path / "user").glob("save_v*.sav")):
            signals.append("versioned_save_slots")
        if (path / "run.log").exists():
            signals.append("runtime_log_file")
        if (path / "data").exists() and any((path / "data").glob("*.bin")):
            signals.append("compiled_data_catalogs")

        report["runtime_profile"] = runtime_profile
        report["signals"] = signals
        report["recommendations"] = self._recommendations_for_reference(runtime_profile, signals)
        return report

    def _recommendations_for_reference(self, runtime_profile: str, signals: list[str]) -> list[str]:
        """Map detected signals to concrete platform upgrade recommendations."""
        recs: list[str] = []
        if runtime_profile == "electron_local":
            recs.append("Enable preload IPC boundary and Steam overlay hook shims by default.")
            if "electron_app_asar" in signals:
                recs.append("Emit asar-aware packaging manifests for production bundles.")
        elif runtime_profile == "godot_export":
            recs.append("Emit Godot export presets and plugin hook scripts in packaging adapter.")
        elif runtime_profile == "native_terminal":
            recs.append("Prioritize save migration + config schema hardening for native builds.")
        else:
            recs.append(
                "Runtime unknown: default to native_terminal and require explicit profile override."
            )

        if "steamworks_node_binary" in signals or "godot_runtime_plugin" in signals:
            recs.append(
                "Treat Steamworks integration as first-class adapter concern, not optional metadata."
            )
        if "electron_squirrel_updater" in signals:
            recs.append(
                "Add updater channel metadata and rollback-safe release hooks for Electron packaging."
            )
        if "versioned_save_slots" in signals:
            recs.append(
                "Adopt versioned save-slot naming with migration gates and rollback support."
            )
        if "runtime_log_file" in signals:
            recs.append("Emit runtime logs and attach log rotation defaults in package templates.")
        if "compiled_data_catalogs" in signals:
            recs.append(
                "Support compiled/binary data catalogs as optional optimized build outputs."
            )
        if "operational_manual_present" in signals:
            recs.append("Generate operations/playbook docs alongside build artifacts.")

        return recs

    def _list_templates(self) -> list:
        """List available templates."""
        templates = []
        for f in self.template_dir.glob("*.yaml"):
            templates.append(f.stem)
        return templates


UTC = getattr(__import__("datetime"), "UTC", UTC)
