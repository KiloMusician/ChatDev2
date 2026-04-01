#!/usr/bin/env python3
"""NuSyQ-Hub Environment Validator.
================================

Validates and reports on the environment setup.
Non-destructive analysis of configuration state.

Usage:
    python scripts/validate_environment.py
    python scripts/validate_environment.py --fix
"""

import os
import sys
from importlib.util import find_spec
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


class EnvironmentValidator:
    """Validate NuSyQ-Hub environment configuration."""

    def __init__(self):
        self.repo_root = REPO_ROOT
        self.issues = []
        self.warnings = []
        self.successes = []

    def validate_python_version(self) -> bool:
        """Check Python version compatibility."""
        version = sys.version_info

        if version.major != 3:
            self.issues.append(f"Python {version.major}.x not supported (need Python 3.x)")
            return False

        if version.minor < 11:
            self.issues.append(f"Python 3.{version.minor} detected - Python 3.11+ required")
            return False

        if version.minor >= 13:
            self.warnings.append(f"Python 3.{version.minor} detected - tested on 3.11-3.13")
            return True

        self.successes.append(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True

    def validate_venv(self) -> bool:
        """Check if virtual environment is properly configured."""
        venv_path = self.repo_root / ".venv"

        if not venv_path.exists():
            self.issues.append("❌ Virtual environment (.venv) not found")
            return False

        # Check pyvenv.cfg for correct paths
        pyvenv_cfg = venv_path / "pyvenv.cfg"
        if pyvenv_cfg.exists():
            content = pyvenv_cfg.read_text()

            # Check for old user paths
            if "malik" in content.lower():
                self.warnings.append("⚠️  Virtual environment contains old user paths (may still work)")

            current_user = Path.home().name
            if current_user.lower() in content.lower():
                self.successes.append(f"✅ Virtual environment configured for user: {current_user}")
                return True
            else:
                self.warnings.append("⚠️  Virtual environment may be from different user")
                return True

        self.successes.append("✅ Virtual environment exists")
        return True

    def validate_dependencies(self) -> tuple[bool, dict[str, bool]]:
        """Check if required packages are installed."""
        required = {
            "pandas": "Data manipulation",
            "numpy": "Numerical computing",
            "torch": "Machine learning (optional)",
            "transformers": "AI models (optional)",
            "flask": "Web framework (optional)",
            "fastapi": "API framework (optional)",
        }

        results = {}
        all_critical = True

        for package, description in required.items():
            if find_spec(package) is not None:
                results[package] = True

                if package in ["pandas", "numpy"]:
                    self.successes.append(f"✅ {package} installed ({description})")
            else:
                results[package] = False

                if package in ["pandas", "numpy"]:
                    self.issues.append(f"❌ {package} missing ({description}) - CRITICAL")
                    all_critical = False
                else:
                    self.warnings.append(f"⚠️  {package} not installed ({description}) - Optional")

        return all_critical, results

    def validate_paths(self) -> bool:
        """Check if critical paths exist."""
        critical_paths = [
            ("src", "Source code directory"),
            ("config", "Configuration directory"),
            ("docs", "Documentation"),
            ("tests", "Test suite"),
        ]

        all_exist = True
        for path_name, description in critical_paths:
            path = self.repo_root / path_name
            if path.exists():
                self.successes.append(f"✅ {path_name}/ exists ({description})")
            else:
                self.warnings.append(f"⚠️  {path_name}/ not found ({description})")
                all_exist = False

        return all_exist

    def validate_chatdev_path(self) -> bool:
        """Check ChatDev configuration."""
        # Check environment variable
        chatdev_path = os.getenv("CHATDEV_PATH")

        if chatdev_path:
            path = Path(chatdev_path)
            if path.exists():
                self.successes.append(f"✅ CHATDEV_PATH configured: {chatdev_path}")
                return True
            else:
                self.warnings.append(f"⚠️  CHATDEV_PATH set but path doesn't exist: {chatdev_path}")
                return False

        # Check config file
        config_file = self.repo_root / "config" / "secrets.json"
        if config_file.exists():
            try:
                import json

                with open(config_file, encoding="utf-8") as f:
                    config = json.load(f)
                    if "chatdev" in config and "path" in config["chatdev"]:
                        self.successes.append("✅ ChatDev path in config/secrets.json")
                        return True
            except (OSError, json.JSONDecodeError, KeyError):
                pass

        self.warnings.append("⚠️  CHATDEV_PATH not configured (optional)")
        return True

    def analyze_caches(self) -> dict[str, dict]:
        """Analyze cache directories (non-destructive)."""
        cache_dirs = [
            ".pytest_cache",
            ".mypy_cache",
            "__pycache__",
            ".kilo_cache",
            ".tmp_audit",
            ".snapshots",
        ]

        cache_info = {}
        total_size = 0

        for cache_name in cache_dirs:
            cache_path = self.repo_root / cache_name

            if cache_path.exists():
                try:
                    top_level_entries = 0
                    direct_file_bytes = 0
                    for child in cache_path.iterdir():
                        top_level_entries += 1
                        if child.is_file():
                            direct_file_bytes += child.stat().st_size

                    cache_info[cache_name] = {
                        "size_mb": direct_file_bytes / (1024 * 1024),
                        "top_level_entries": top_level_entries,
                        "scan_mode": "shallow",
                    }
                    total_size += direct_file_bytes
                except Exception as e:
                    cache_info[cache_name] = {"error": str(e)}

        if cache_info:
            total_mb = total_size / (1024 * 1024)
            self.warnings.append(f"📁 {len(cache_info)} cache directories found ({total_mb:.2f} MB total)")

        return cache_info

    def run_validation(self):
        """Run all validation checks."""
        # Python version
        self.validate_python_version()

        # Virtual environment
        self.validate_venv()

        # Dependencies
        _critical_ok, _deps = self.validate_dependencies()

        # Paths
        self.validate_paths()

        # ChatDev
        self.validate_chatdev_path()

        # Caches
        caches = self.analyze_caches()

        # Summary

        if self.successes:
            for _success in self.successes:
                pass

        if self.warnings:
            for _warning in self.warnings:
                pass

        if self.issues:
            for _issue in self.issues:
                pass

        if caches:
            for _cache_name, info in caches.items():
                if "error" in info:
                    pass
                else:
                    pass

        if self.issues:
            return False
        elif self.warnings:
            return True
        else:
            return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate NuSyQ-Hub environment")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt automatic fixes (not implemented yet)",
    )
    args = parser.parse_args()

    validator = EnvironmentValidator()
    success = validator.run_validation()

    if args.fix:
        pass

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
