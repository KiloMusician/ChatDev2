#!/usr/bin/env python3
"""Workspace Folder Mapping Validator & Auto-Setup
Ensures all variables are tied to their correct folders (Feb 2, 2026)

Usage:
    python validate_and_setup_workspace.py
    python validate_and_setup_workspace.py --setup
    python validate_and_setup_workspace.py --check-only
    python validate_and_setup_workspace.py --mode overnight
"""

import json
import os
import sys
from pathlib import Path, PureWindowsPath

# Constants
WORKSPACE_LOADER_SCRIPT = "workspace_loader.ps1"


class WorkspaceValidator:
    def __init__(self):
        self.hub = r"C:\Users\keath\Desktop\Legacy\NuSyQ-Hub"
        self.root = r"C:\Users\keath\NuSyQ"
        self.verse = r"C:\Users\keath\Desktop\SimulatedVerse"
        self.prime = r"C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\.vscode\prime_anchor"

        self.folders = {
            "hub": self.hub,
            "root": self.root,
            "verse": self.verse,
            "anchor": self.prime,
        }

        self.native_paths = {key: self._resolve_to_native_path(path) for key, path in self.folders.items()}

        self.errors = []
        self.warnings = []
        self.successes = []

    def log_success(self, msg):
        self.successes.append(f"✓ {msg}")
        print(f"✓ {msg}")

    def log_warning(self, msg):
        self.warnings.append(f"⚠ {msg}")
        print(f"⚠ {msg}")

    def log_error(self, msg):
        self.errors.append(f"✗ {msg}")
        print(f"✗ {msg}")

    def _resolve_to_native_path(self, raw_path: str) -> Path:
        """Normalize Windows-style paths so they resolve from WSL."""
        win_path = PureWindowsPath(raw_path)
        if win_path.drive:
            drive_letter = win_path.drive.rstrip(":").lower()
            components = win_path.parts[1:]
            native = Path("/mnt") / drive_letter
            if components:
                native = native.joinpath(*components)
            return native
        return Path(raw_path)

    def check_folder_exists(self, name: str, key: str) -> bool:
        """Check if a folder exists."""
        raw_path = self.folders[key]
        native_path = self.native_paths[key]
        if native_path.exists():
            self.log_success(f"{name} folder exists: {raw_path}")
            return True
        else:
            self.log_error(f"{name} folder NOT FOUND: {raw_path}")
            return False

    def check_python_venv(self, name: str, key: str) -> bool:
        """Check if Python venv exists."""
        native_path = self.native_paths[key]
        venv_path = native_path / ".venv"
        if venv_path.exists():
            self.log_success(f"{name} Python venv exists")
            return True
        else:
            self.log_warning(f"{name} Python venv not found (optional for verse)")
            return True if name == "SimulatedVerse" else False

    def check_env_file_exists(self) -> bool:
        """Check if .env.workspace exists."""
        env_file = self.native_paths["hub"] / ".env.workspace"
        if env_file.exists():
            self.log_success(".env.workspace file exists")
            return True
        else:
            self.log_error(".env.workspace NOT FOUND")
            return False

    def check_loader_exists(self) -> bool:
        """Check if workspace_loader.ps1 exists."""
        loader = self.native_paths["hub"] / ".vscode" / WORKSPACE_LOADER_SCRIPT
        if loader.exists():
            self.log_success(f"{WORKSPACE_LOADER_SCRIPT} exists")
            return True
        else:
            self.log_error(f"{WORKSPACE_LOADER_SCRIPT} NOT FOUND")
            return False

    def check_mapping_yaml(self) -> bool:
        """Check if workspace_mapping.yaml exists."""
        mapping = self.native_paths["hub"] / "config" / "workspace_mapping.yaml"
        if mapping.exists():
            self.log_success("workspace_mapping.yaml exists")
            return True
        else:
            self.log_error("workspace_mapping.yaml NOT FOUND")
            return False

    def generate_env_file(self):
        """Generate .env.workspace if missing."""
        env_file = self.native_paths["hub"] / ".env.workspace"
        if not env_file.exists():
            self.log_warning("Generating .env.workspace...")
            content = f"""# Auto-generated {Path(__file__).stem}
NUSYQ_HUB={self.hub}
NUSYQ_HUB_SRC={self.hub}\\src
NUSYQ_HUB_SCRIPTS={self.hub}\\scripts
NUSYQ_HUB_TESTS={self.hub}\\tests
NUSYQ_ROOT={self.root}
NUSYQ_ROOT_CHATDEV={self.root}\\ChatDev
SIMULATEDVERSE={self.verse}
PRIME_ANCHOR={self.prime}
PYTHON_HUB={self.hub}\\.venv\\Scripts\\python.exe
PYTHON_ROOT={self.root}\\.venv\\Scripts\\python.exe
"""
            env_file.write_text(content)
            self.log_success(f"Generated {env_file}")

    def get_powershell_profile(self) -> tuple[Path, bool]:
        """Get or create PowerShell profile."""
        user_home = os.environ.get("USERPROFILE")
        if user_home:
            profile_dir = self._resolve_to_native_path(user_home) / "Documents" / "PowerShell"
        else:
            profile_dir = Path.home() / "Documents" / "PowerShell"
        profile_path = profile_dir / "profile.ps1"

        if not profile_dir.exists():
            profile_dir.mkdir(parents=True, exist_ok=True)
            self.log_success(f"Created PowerShell profile directory: {profile_dir}")

        exists = profile_path.exists()
        return profile_path, exists

    def setup_powershell_profile(self, profile_path: Path) -> bool:
        """Add workspace loader to PowerShell profile."""
        loader_path = self.native_paths["hub"] / ".vscode" / WORKSPACE_LOADER_SCRIPT
        loader_line = f'& "{loader_path}"\n'

        # Check if already sourced
        if profile_path.exists():
            content = profile_path.read_text()
            if WORKSPACE_LOADER_SCRIPT in content:
                self.log_warning("PowerShell profile already sources workspace_loader")
                return True
            else:
                profile_path.write_text(content + f"\n# NuSyQ Workspace Loader\n{loader_line}")
                self.log_success("Added workspace_loader to PowerShell profile")
                return True
        else:
            profile_path.write_text(f"# NuSyQ Workspace Loader\n{loader_line}")
            self.log_success("Created PowerShell profile with workspace_loader")
            return True

    def generate_validation_report(self) -> dict:
        """Generate a JSON report of validation results."""
        report = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "folders_checked": len(self.folders),
            "successes": len(self.successes),
            "warnings": len(self.warnings),
            "errors": len(self.errors),
            "details": {
                "successes": self.successes,
                "warnings": self.warnings,
                "errors": self.errors,
            },
            "workspace_mapping": {
                "nusyq_hub": self.hub,
                "nusyq_root": self.root,
                "simulatedverse": self.verse,
                "prime_anchor": self.prime,
            },
        }
        return report

    def run_full_check(self, setup: bool = False) -> int:
        """Run full validation suite."""
        print("\n" + "=" * 60)
        print("NuSyQ WORKSPACE FOLDER MAPPING VALIDATOR")
        print("=" * 60 + "\n")

        # Check all folders
        print("📂 CHECKING FOLDERS:")
        self.check_folder_exists("NuSyQ-Hub", "hub")
        self.check_folder_exists("NuSyQ-Root", "root")
        self.check_folder_exists("SimulatedVerse", "verse")
        self.check_folder_exists("Prime Anchor", "anchor")

        # Check Python venvs
        print("\n🐍 CHECKING PYTHON ENVIRONMENTS:")
        self.check_python_venv("NuSyQ-Hub", "hub")
        self.check_python_venv("NuSyQ-Root", "root")
        self.check_python_venv("SimulatedVerse", "verse")

        # Check mapping files
        print("\n📋 CHECKING MAPPING FILES:")
        all_config = all(
            [
                self.check_env_file_exists(),
                self.check_loader_exists(),
                self.check_mapping_yaml(),
            ]
        )

        # Setup if requested
        if setup:
            print("\n⚙️  SETUP MODE:")
            if not all_config:
                self.generate_env_file()

            profile_path, _ = self.get_powershell_profile()
            self.setup_powershell_profile(profile_path)

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY:")
        print(f"  ✓ Successes: {len(self.successes)}")
        print(f"  ⚠ Warnings:  {len(self.warnings)}")
        print(f"  ✗ Errors:    {len(self.errors)}")
        print("=" * 60)

        # Generate report
        report = self.generate_validation_report()
        report_file = self.native_paths["hub"] / "state" / "reports" / "workspace_validation.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2))
        print(f"\n📊 Report saved: {report_file}")

        return 0 if len(self.errors) == 0 else 1


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate and setup workspace folder mapping")
    parser.add_argument("--setup", action="store_true", help="Run setup mode (auto-generate missing files)")
    parser.add_argument("--check-only", action="store_true", help="Check only, don't setup")
    parser.add_argument("--mode", default="normal", help="Operating mode (normal, overnight, analysis)")

    args = parser.parse_args()

    validator = WorkspaceValidator()
    exit_code = validator.run_full_check(setup=args.setup and not args.check_only)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
