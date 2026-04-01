"""
NuSyQ Configuration Manager
============================

Purpose:
    Centralized configuration management system for the NuSyQ AI
    ecosystem. Loads, validates, caches, and provides unified access to
    YAML configuration files across the entire project.

Architecture:
    - YAML-based configuration with JSON export support
    - Validation system with specific rules per config type
    - Caching mechanism to avoid repeated file I/O
    - Unified settings view across all configurations

Key Features:
     1. Multi-file configuration loading (manifest, knowledge-base,
         ai-ecosystem, tasks)
    2. Schema validation with custom rules per configuration type
    3. Configuration caching with timestamp tracking
    4. Export to YAML or JSON formats
    5. Unified settings aggregation

Configuration Files:
    - nusyq.manifest.yaml: System manifest (packages, models, folders)
    - knowledge-base.yaml: Learning log and session tracking
    - 1/ai-ecosystem.yaml: AI model configurations (archived from AI_Hub)
    - config/tasks.yaml: Task definitions and workflows
"""

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml  # type: ignore[import-untyped]

# Windows UTF-8 encoding fix - use safer reconfigure method
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        # Already configured or running in non-standard environment
        pass


@dataclass
class ValidationResult:
    """
    Result of configuration validation

    Attributes:
        is_valid (bool): Whether configuration passed all validation checks
        errors (List[str]): Critical errors that prevent usage
        warnings (List[str]): Non-critical issues or suggestions
    """

    is_valid: bool
    errors: List[str]
    warnings: List[str]


class ConfigManager:
    """
    Centralized Configuration Management for NuSyQ Ecosystem

    Responsibilities:
        - Load and parse YAML configuration files
        - Cache configurations to minimize file I/O
        - Validate configurations against schemas
        - Provide unified access to all settings
        - Export configurations in multiple formats

    Usage:
        manager = ConfigManager()
        manager.reload_all()  # Load all configs
        config = manager.get_config("manifest")
        validation = manager.validate_config("manifest")
    """

    def __init__(self, base_path: str = "."):
        """
        Initialize ConfigManager

        Args:
            base_path (str): Base directory for relative config paths
                            Defaults to current directory
        """
        self.base_path = Path(base_path)
        self.configs: Dict[str, Any] = {}
        self.last_loaded: Dict[str, datetime] = {}

    def load_config(self, config_name: str, file_path: str) -> Dict[str, Any]:
        """
        Load and cache a YAML configuration file

        Reads YAML file, parses content, stores in cache with timestamp.

        Args:
            config_name (str): Identifier for this config (e.g.,
                "manifest")
            file_path (str): Relative path from base_path

        Returns:
            Dict[str, Any]: Parsed configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If YAML parsing fails
        """
        full_path = self.base_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {full_path}")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Cache configuration and track load time
            self.configs[config_name] = config
            self.last_loaded[config_name] = datetime.now()
            return config

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}") from e

    def _load_if_missing(self, config_name: str, file_path: str) -> Dict[str, Any]:
        """Load config if not cached, otherwise return cached value."""
        config = self.get_config(config_name)
        if config is not None:
            return config
        return self.load_config(config_name, file_path)

    def load_manifest(self) -> Dict[str, Any]:
        """Load nusyq.manifest.yaml."""
        return self._load_if_missing("manifest", "nusyq.manifest.yaml")

    def load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge-base.yaml."""
        config = self._load_if_missing("knowledge_base", "knowledge-base.yaml")
        if "completions" not in config:
            config["completions"] = []
        return config

    def load_ai_ecosystem(self) -> Dict[str, Any]:
        """Load ai-ecosystem.yaml."""
        return self._load_if_missing("ai_ecosystem", "1/ai-ecosystem.yaml")

    def load_tasks(self) -> Dict[str, Any]:
        """Load config/tasks.yaml."""
        return self._load_if_missing("tasks", "config/tasks.yaml")

    def validate_all(self) -> Dict[str, Any]:
        """Load and validate all known configs."""
        load_results = self.reload_all()
        errors: List[str] = []
        warnings: List[str] = []
        validations: Dict[str, ValidationResult] = {}

        for name, loaded in load_results.items():
            if not loaded:
                errors.append(f"Config {name} failed to load")
                continue
            validation = self.validate_config(name)
            validations[name] = validation
            errors.extend(validation.errors)
            warnings.extend(validation.warnings)

        all_valid = all(load_results.values()) and not errors
        return {
            "all_valid": all_valid,
            "errors": errors,
            "warnings": warnings,
            "load_results": load_results,
            "validations": validations,
        }

    def get_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached configuration by name

        Args:
            config_name (str): Configuration identifier

        Returns:
            Optional[Dict[str, Any]]: Cached config dict, or None if not loaded
        """
        return self.configs.get(config_name)

    def reload_all(self) -> Dict[str, bool]:
        """
        Reload all NuSyQ configuration files

        Attempts to load all known configuration files. Failures are
        logged but don't prevent other configs from loading.

        Loaded Configurations:
            - manifest: System manifest (packages, models, folders)
            - knowledge_base: Learning log and session data
            - ai_ecosystem: AI model definitions and settings
            - tasks: VS Code task definitions and workflows

        Returns:
            Dict[str, bool]: Load success status for each config
        """
        load_results: Dict[str, bool] = {}
        config_files = {
            "manifest": "nusyq.manifest.yaml",
            "knowledge_base": "knowledge-base.yaml",
            "ai_ecosystem": "1/ai-ecosystem.yaml",
            # Updated: AI_Hub archived to 1/
            "tasks": "config/tasks.yaml",
        }

        for config_key, path in config_files.items():
            try:
                self.load_config(config_key, path)
                load_results[config_key] = True
            except (
                FileNotFoundError,
                ValueError,
                OSError,
                yaml.YAMLError,
            ) as exc:
                print(f"Failed to load {config_key}: {exc}")
                load_results[config_key] = False

        return load_results

    def validate_config(self, config_name: str) -> ValidationResult:
        """
        Validate configuration against schema rules

        Performs two-tier validation:
        1. Common validation (meta section requirements)
        2. Config-specific validation (custom rules per type)

        Args:
            config_name (str): Name of config to validate

        Returns:
            ValidationResult: Validation outcome with errors and warnings
        """
        config = self.get_config(config_name)
        if not config:
            return ValidationResult(
                False,
                [f"Config {config_name} not loaded"],
                [],
            )

        errors: List[str] = []
        warnings: List[str] = []

        # === Common Validation: Meta Section ===
        # All configs should have meta section with name and version
        if "meta" not in config:
            errors.append("Missing 'meta' section")
        elif not isinstance(config["meta"], dict):
            errors.append("'meta' section must be a dictionary")
        else:
            meta = config["meta"]
            required_meta = ["name", "version"]
            for field in required_meta:
                if field not in meta:
                    errors.append(f"Missing required meta field: {field}")

        # === Config-Specific Validation ===
        if config_name == "manifest":
            errors.extend(self._validate_manifest(config))
        elif config_name == "ai_ecosystem":
            errors.extend(self._validate_ai_ecosystem(config))
        elif config_name == "tasks":
            errors.extend(self._validate_tasks(config))

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_manifest(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate nusyq.manifest.yaml structure

        Checks:
            - Required sections: folders, packages, extensions
            - Ollama models list format

        Args:
            config: Manifest configuration dictionary

        Returns:
            List of validation error messages
        """
        errors = []

        # Required sections for orchestrator operation
        required_sections = [
            "folders",
            "winget_packages",
            "pip_packages",
            "vscode_extensions",
        ]
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")

        # Validate ollama_models if present
        if "ollama_models" in config:
            if not isinstance(config["ollama_models"], list):
                errors.append("ollama_models must be a list")

        return errors

    def _validate_ai_ecosystem(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate AI_Hub/ai-ecosystem.yaml structure

        Checks:
            - Ollama configuration (base_url, models list)
            - Model definitions structure

        Args:
            config: AI ecosystem configuration dictionary

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate Ollama configuration
        if "local_models" in config and "ollama" in config["local_models"]:
            ollama_config = config["local_models"]["ollama"]
            if "base_url" not in ollama_config:
                errors.append("Missing ollama base_url")
            if "models" not in ollama_config:
                errors.append("Missing ollama models list")

        return errors

    def _validate_tasks(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate config/tasks.yaml structure

        Checks:
            - Task groups are lists
            - Each task has id and command fields

        Args:
            config: Tasks configuration dictionary

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate task groups structure
        if "task_groups" in config:
            for group_name, tasks in config["task_groups"].items():
                if not isinstance(tasks, list):
                    errors.append(f"Task group {group_name} must be a list")
                else:
                    for task in tasks:
                        task_id = task.get("id", "unknown")
                        if "id" not in task:
                            errors.append(f"Task in {group_name} missing id")
                        if "command" not in task:
                            errors.append(f"Task {task_id} missing command")

        return errors

    def export_config(self, config_name: str, output_format: str = "yaml") -> str:
        """
        Export configuration in specified format

        Supports YAML and JSON export for backup, documentation, or
        integration with other tools.

        Args:
            config_name (str): Configuration to export
            format (str): Output format ("yaml" or "json")

        Returns:
            str: Serialized configuration

        Raises:
            ValueError: If config not found or format unsupported
        """
        config = self.get_config(config_name)
        if not config:
            raise ValueError(f"Config {config_name} not found")

        if output_format.lower() == "yaml":
            # Preserve order and structure
            return yaml.dump(config, default_flow_style=False, sort_keys=False)
        if output_format.lower() == "json":
            # Pretty-print with 2-space indent
            return json.dumps(config, indent=2)
        raise ValueError(f"Unsupported export format: {output_format}")

    def get_unified_settings(self) -> Dict[str, Any]:
        """
        Aggregate settings from all configurations into unified view

        Combines data from multiple configs into single structure for
        easy consumption by applications that need ecosystem-wide settings.

        Returns:
            Dict[str, Any]: Unified settings with sections:
                - system: Base paths and metadata
                - ai_models: Available AI models and configurations
                - tools: Installed development tools
                - workflows: Defined task workflows
        """
        unified = {
            "system": {
                "base_path": str(self.base_path),
                "last_updated": (
                    max(self.last_loaded.values()) if self.last_loaded else None
                ),
            },
            "ai_models": {},
            "tools": {},
            "workflows": {},
        }

        # Extract AI models info from ecosystem config
        ai_config = self.get_config("ai_ecosystem")
        if ai_config and "local_models" in ai_config:
            unified["ai_models"] = ai_config["local_models"]

        # Extract tools info from manifest
        manifest = self.get_config("manifest")
        if manifest:
            unified["tools"] = {
                "vscode_extensions": manifest.get("vscode_extensions", []),
                "pip_packages": manifest.get("pip_packages", []),
                "winget_packages": manifest.get("winget_packages", []),
            }

        # Extract workflows from tasks config
        tasks_config = self.get_config("tasks")
        if tasks_config and "workflows" in tasks_config:
            unified["workflows"] = tasks_config["workflows"]

        return unified


def main() -> int:
    """Run standalone configuration validation."""

    manager = ConfigManager()

    print("=" * 50)
    print("NuSyQ Configuration Manager - Validation Report")
    print("=" * 50)

    # Load all configurations
    print("\n[1/2] Loading configurations...")
    results = manager.reload_all()

    print("\nLoad Results:")
    for name, success in results.items():
        status_icon = "✅" if success else "❌"
        print(f"  {status_icon} {name}")

    # Validate loaded configurations
    print("\n[2/2] Validating configurations...")
    has_errors = False

    for name, success in results.items():
        if not success:
            continue

        validation = manager.validate_config(name)
        status_icon = "✅" if validation.is_valid else "❌"
        print(f"  {status_icon} {name}")

        if validation.errors:
            has_errors = True
            for error in validation.errors:
                print(f"    ❌ Error: {error}")

        if validation.warnings:
            for warning in validation.warnings:
                print(f"    ⚠️  Warning: {warning}")

    # Summary
    print("\n" + "=" * 50)
    if not has_errors and all(results.values()):
        print("✅ All configurations valid!")
        return 0

    print("❌ Configuration issues detected. Review errors above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
