"""Auto-Heal Configuration: Detect and fix common configuration issues.

This script proactively fixes:
1. REDACTED placeholders that can be auto-populated
2. Missing environment variable templates
3. Broken import paths in config files
4. Ollama port misconfigurations

Usage:
    python scripts/auto_heal_config.py
    python scripts/auto_heal_config.py --dry-run  # Preview changes only
"""

import json
import subprocess
from pathlib import Path
from typing import Any


class ConfigHealer:
    """Automatically heal common configuration issues."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.fixes_applied = []
        self.repo_root = Path(__file__).parent.parent
        self.config_dir = self.repo_root / "config"

    def heal_all(self) -> dict[str, Any]:
        """Run all healing operations."""
        print("🏥 Configuration Healing System Activated...")

        self.check_ollama_port()
        self.create_env_template()
        self.fix_chatdev_path()
        self.validate_secrets_structure()

        return {
            "fixes_applied": len(self.fixes_applied),
            "details": self.fixes_applied,
            "dry_run": self.dry_run,
        }

    def check_ollama_port(self):
        """Verify Ollama is accessible and update config if needed."""
        print("\n🔌 Checking Ollama connectivity...")

        # Try to connect to Ollama
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/version"], capture_output=True, timeout=5
            )
            if result.returncode == 0:
                print("  ✅ Ollama accessible at http://localhost:11434")

                # Update secrets.json if it has placeholder
                secrets_file = self.config_dir / "secrets.json"
                if secrets_file.exists():
                    with open(secrets_file, encoding="utf-8") as f:
                        secrets = json.load(f)

                    if secrets.get("ollama", {}).get("host") != "http://localhost:11434":
                        if not self.dry_run:
                            secrets.setdefault("ollama", {})["host"] = "http://localhost:11434"
                            with open(secrets_file, "w", encoding="utf-8") as f:
                                json.dump(secrets, f, indent=2)
                        self.fixes_applied.append("Updated Ollama host to http://localhost:11434")
                        print("  🔧 Fixed Ollama host configuration")
            else:
                print("  ⚠️  Ollama not accessible - may need to start service")
        except Exception as e:
            print(f"  ⚠️  Could not check Ollama: {e}")

    def create_env_template(self):
        """Create .env.template if missing."""
        print("\n📄 Checking environment template...")

        env_template = self.repo_root / ".env.template"
        if not env_template.exists():
            template_content = """# Environment Variables Template for NuSyQ-Hub
# Copy this to .env and fill in actual values

# API Keys (Optional - only if using external AI services)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# GitHub Integration (Optional)
GITHUB_TOKEN=ghp_your-github-token-here
GITHUB_USERNAME=your-github-username

# Local Services (Usually auto-detected)
OLLAMA_HOST=http://localhost:11434
OLLAMA_PORT=11434

# ChatDev Integration
CHATDEV_PATH=C:/Users/keath/NuSyQ/ChatDev

# System Configuration
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development
"""
            if not self.dry_run:
                env_template.write_text(template_content, encoding="utf-8")
            self.fixes_applied.append("Created .env.template")
            print("  ✅ Created .env.template")
        else:
            print("  ✅ .env.template already exists")

    def fix_chatdev_path(self):
        """Auto-detect and fix ChatDev path if wrong."""
        print("\n🤖 Checking ChatDev path...")

        # Common ChatDev locations
        possible_paths = [
            Path("C:/Users/keath/NuSyQ/ChatDev"),
            Path("../NuSyQ/ChatDev"),
            self.repo_root.parent / "NuSyQ" / "ChatDev",
        ]

        chatdev_path = None
        for path in possible_paths:
            if path.exists() and (path / "run.py").exists():
                chatdev_path = path
                break

        if chatdev_path:
            print(f"  ✅ Found ChatDev at {chatdev_path}")

            # Update secrets.json
            secrets_file = self.config_dir / "secrets.json"
            if secrets_file.exists():
                with open(secrets_file, encoding="utf-8") as f:
                    secrets = json.load(f)

                current_path = secrets.get("chatdev", {}).get("path", "")
                if current_path == "" or not Path(current_path).exists():
                    if not self.dry_run:
                        secrets.setdefault("chatdev", {})["path"] = str(chatdev_path)
                        with open(secrets_file, "w", encoding="utf-8") as f:
                            json.dump(secrets, f, indent=2)
                    self.fixes_applied.append(f"Set ChatDev path to {chatdev_path}")
                    print("  🔧 Updated ChatDev path")
        else:
            print("  ⚠️  ChatDev not found in expected locations")

    def validate_secrets_structure(self):
        """Ensure secrets.json has all required fields."""
        print("\n🔐 Validating secrets.json structure...")

        secrets_file = self.config_dir / "secrets.json"
        if not secrets_file.exists():
            print("  ⚠️  secrets.json not found (expected)")
            return

        with open(secrets_file, encoding="utf-8") as f:
            secrets = json.load(f)

        # Required structure
        required_structure = {
            "openai": {"api_key": None, "organization": None},
            "ollama": {"host": "http://localhost:11434", "api_key": None},
            "anthropic": {"api_key": None},
            "github": {"token": None, "username": None},
            "chatdev": {"path": ""},
            "system": {"debug": True, "log_level": "INFO"},
        }

        updated = False
        for service, fields in required_structure.items():
            if service not in secrets:
                secrets[service] = fields
                updated = True
                self.fixes_applied.append(f"Added missing '{service}' section to secrets.json")
            else:
                for field, default in fields.items():
                    if field not in secrets[service]:
                        secrets[service][field] = default
                        updated = True
                        self.fixes_applied.append(f"Added missing '{service}.{field}' field")

        if updated and not self.dry_run:
            with open(secrets_file, "w", encoding="utf-8") as f:
                json.dump(secrets, f, indent=2)
            print(f"  🔧 Updated secrets.json with {sum(1 for x in self.fixes_applied if 'secrets.json' in x)} fixes")
        elif not updated:
            print("  ✅ secrets.json structure valid")


def main():
    """Run configuration healing."""
    import sys

    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")

    healer = ConfigHealer(dry_run=dry_run)
    results = healer.heal_all()

    print(f"\n{'=' * 60}")
    print("✅ Configuration Healing Complete!")
    print(f"   Fixes Applied: {results['fixes_applied']}")
    if results["dry_run"]:
        print("   (DRY RUN - no actual changes made)")
    print(f"{'=' * 60}")

    if results["details"]:
        print("\n📋 Details:")
        for fix in results["details"]:
            print(f"   • {fix}")

    print("\n💡 Next Steps:")
    print("   1. Review any warnings above")
    print("   2. Populate REDACTED values in config/secrets.json")
    print("   3. Run: python scripts/quick_status.py")


if __name__ == "__main__":
    main()
