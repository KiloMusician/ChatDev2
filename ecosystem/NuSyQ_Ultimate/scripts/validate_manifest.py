"""
NuSyQ Manifest Validator
=========================

Validates nusyq.manifest.yaml for common issues and misconfigurations.

Usage:
    python scripts/validate_manifest.py

Returns:
    Exit code 0 if valid
    Exit code 1 if errors found
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML not installed")
    print("Install with: pip install pyyaml")
    sys.exit(1)


class ManifestValidator:
    """Validates NuSyQ manifest structure and content"""

    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.manifest: Dict[str, Any] = {}

    def validate(self) -> bool:
        """Run all validation checks"""
        print("=" * 70)
        print("NuSyQ Manifest Validator")
        print("=" * 70)
        print()

        # Load manifest
        if not self._load_manifest():
            return False

        # Run checks
        self._check_structure()
        self._check_meta()
        self._check_folders()
        self._check_packages()
        self._check_models()
        self._check_extensions()
        self._check_health_checks()

        # Report results
        self._print_report()

        return len(self.errors) == 0

    def _load_manifest(self) -> bool:
        """Load and parse YAML manifest"""
        if not self.manifest_path.exists():
            self.errors.append(f"Manifest not found: {self.manifest_path}")
            return False

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                self.manifest = yaml.safe_load(f)
            print(f"[OK] Loaded manifest: {self.manifest_path.name}")
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"YAML syntax error: {e}")
            return False
        except (OSError, UnicodeDecodeError, ValueError, TypeError) as e:
            self.errors.append(f"Failed to load manifest: {e}")
            return False

    def _check_structure(self) -> None:
        """Check required top-level sections"""
        required_sections = ["meta", "folders", "ollama_models", "vscode_extensions"]
        for section in required_sections:
            if section not in self.manifest:
                self.errors.append(f"Missing required section: {section}")

    def _check_meta(self) -> None:
        """Validate meta section"""
        if "meta" not in self.manifest:
            return

        meta = self.manifest["meta"]

        # Check required meta fields
        required_fields = ["name", "version", "root_dir"]
        for field in required_fields:
            if field not in meta:
                self.errors.append(f"Missing meta.{field}")

        # Validate version format
        if "version" in meta:
            version = str(meta["version"])
            if not self._is_valid_date_version(version):
                self.warnings.append(f"Version '{version}' not in YYYY-MM-DD format")

    def _check_folders(self) -> None:
        """Validate folders section"""
        if "folders" not in self.manifest:
            return

        folders = self.manifest["folders"]
        if not isinstance(folders, list):
            self.errors.append("'folders' must be a list")
            return

        # Check for path variables
        for folder in folders:
            if not isinstance(folder, str):
                self.errors.append(f"Folder path must be string: {folder}")
                continue

            if "%" in folder or "$" in folder:
                # Has environment variable - this is OK
                pass
            elif not folder.startswith(("/", "C:", "D:")):
                self.warnings.append(f"Relative folder path: {folder}")

    def _check_packages(self) -> None:
        """Validate package sections"""
        # Check winget packages
        if "winget_packages" in self.manifest:
            packages = self.manifest["winget_packages"]
            if not isinstance(packages, list):
                self.errors.append("'winget_packages' must be a list")
            else:
                for pkg in packages:
                    if isinstance(pkg, dict):
                        if "id" not in pkg:
                            self.errors.append(f"Package missing 'id': {pkg}")
                    elif not isinstance(pkg, str):
                        self.errors.append(f"Package must be string or dict: {pkg}")

        # Check pip packages
        if "pip_packages" in self.manifest:
            packages = self.manifest["pip_packages"]
            if not isinstance(packages, list):
                self.errors.append("'pip_packages' must be a list")

    def _check_models(self) -> None:
        """Validate Ollama models"""
        if "ollama_models" not in self.manifest:
            return

        models = self.manifest["ollama_models"]
        if not isinstance(models, list):
            self.errors.append("'ollama_models' must be a list")
            return

        # Check model name format
        for model in models:
            if not isinstance(model, str):
                self.errors.append(f"Model name must be string: {model}")
                continue

            # Check for size tag
            if ":" not in model:
                self.warnings.append(f"Model missing size tag: {model} (should be model:size)")

            # Check for valid characters
            if not all(c.isalnum() or c in ":-_." for c in model):
                self.warnings.append(f"Model name has unusual characters: {model}")

        # Recommend essential models
        essential_models = ["qwen2.5-coder:7b", "qwen2.5-coder:14b"]
        has_essential = any(model in models for model in essential_models)
        if not has_essential:
            self.warnings.append("No qwen2.5-coder models found (recommended for coding)")

    def _check_extensions(self) -> None:
        """Validate VS Code extensions"""
        if "vscode_extensions" not in self.manifest:
            return

        extensions = self.manifest["vscode_extensions"]
        if not isinstance(extensions, list):
            self.errors.append("'vscode_extensions' must be a list")
            return

        # Check extension ID format
        for ext in extensions:
            if not isinstance(ext, str):
                self.errors.append(f"Extension ID must be string: {ext}")
                continue

            if "." not in ext:
                self.warnings.append(f"Extension ID missing dot: {ext}")

            # Check for known invalid extensions
            if ext == "ollama.ollama":
                self.warnings.append("Extension 'ollama.ollama' doesn't exist in marketplace")

        # Recommend essential extensions
        essential_exts = ["ms-python.python", "Continue.continue"]
        for ext in essential_exts:
            if ext not in extensions:
                self.warnings.append(f"Recommended extension missing: {ext}")

    def _check_health_checks(self) -> None:
        """Validate health checks"""
        if "health_checks" not in self.manifest:
            self.warnings.append("No health_checks defined")
            return

        checks = self.manifest["health_checks"]
        if not isinstance(checks, list):
            self.errors.append("'health_checks' must be a list")
            return

        for check in checks:
            if not isinstance(check, dict):
                self.errors.append(f"Health check must be dict: {check}")
                continue

            if "cmd" not in check:
                self.errors.append(f"Health check missing 'cmd': {check}")

            if "expect" not in check:
                self.warnings.append(f"Health check missing 'expect': {check.get('cmd')}")

    def _is_valid_date_version(self, version: str) -> bool:
        """Check if version is in YYYY-MM-DD format"""
        try:
            parts = version.split("-")
            if len(parts) != 3:
                return False
            year, month, day = parts
            return (
                len(year) == 4
                and len(month) == 2
                and len(day) == 2
                and year.isdigit()
                and month.isdigit()
                and day.isdigit()
            )
        except (ValueError, AttributeError):
            return False

    def _print_report(self) -> None:
        """Print validation report"""
        print()
        print("=" * 70)
        print("Validation Report")
        print("=" * 70)
        print()

        # Errors
        if self.errors:
            print(f"[ERROR] Found {len(self.errors)} error(s):")
            for error in self.errors:
                print(f"  X {error}")
            print()

        # Warnings
        if self.warnings:
            print(f"[WARNING] Found {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"  ! {warning}")
            print()

        # Summary
        if not self.errors and not self.warnings:
            print("[OK] Manifest is valid!")
        elif not self.errors:
            print("[OK] Manifest is valid (with warnings)")
        else:
            print("[FAIL] Manifest has errors and must be fixed")

        print()
        print("=" * 70)


def main() -> int:
    """Main entry point"""
    # Find manifest
    manifest_path = Path("nusyq.manifest.yaml")
    if not manifest_path.exists():
        # Try parent directory
        manifest_path = Path("..") / "nusyq.manifest.yaml"

    if not manifest_path.exists():
        print("[ERROR] Cannot find nusyq.manifest.yaml")
        print("Run this script from NuSyQ root directory")
        return 1

    # Validate
    validator = ManifestValidator(manifest_path)
    valid = validator.validate()

    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
