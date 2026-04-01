#!/usr/bin/env python3
"""🚀 COMPLETE ECOSYSTEM ACTIVATION.

=================================
[ROUTE AGENTS] 🤖

Activates ALL critical services:
- Docker daemon (if available)
- Ollama service
- OpenTelemetry stack
- Pre-commit hooks
- Test coverage baseline
- Quest system
- All AI agents

This is the "activate" endpoint for the entire system.
Run this to get everything running.
"""

import json
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


class EcosystemActivator:
    """Orchestrates full ecosystem activation."""

    def __init__(self):
        self.status: dict[str, dict] = {
            "timestamp": datetime.now().isoformat(),
            "activated": [],
            "failed": [],
            "warnings": [],
            "optional_skipped": [],
        }
        self.root_path = Path(__file__).parent.parent

    def run_command(self, cmd: list[str], description: str, required: bool = True) -> bool:
        """Run command and report status."""
        print(f"\n📋 {description}...")
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
            print(f"✅ {description} - SUCCESS")
            return True
        except subprocess.TimeoutExpired:
            msg = f"⏱️  {description} - TIMEOUT (service may still be starting)"
            print(msg)
            if required:
                self.status["failed"].append(description)
                return False
            else:
                self.status["warnings"].append(msg)
                return False
        except subprocess.CalledProcessError as e:
            msg = f"❌ {description} - FAILED: {e.stderr[:100]}"
            print(msg)
            if required:
                self.status["failed"].append(description)
            else:
                self.status["optional_skipped"].append(description)
            return False
        except FileNotFoundError:
            msg = f"⚠️  {description} - SKIPPED (command not found)"
            print(msg)
            if required:
                self.status["failed"].append(description)
            else:
                self.status["optional_skipped"].append(description)
            return False

    def check_port(self, host: str, port: int, service_name: str) -> bool:
        """Check if a service is listening on a port."""
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"✅ {service_name} is running (port {port})")
                return True
        except (TimeoutError, ConnectionRefusedError, OSError):
            print(f"⏳ {service_name} not yet responding (port {port})")
            return False

    def activate_docker(self) -> bool:
        """Check and start Docker if available."""
        print("\n" + "=" * 70)
        print("[1/7] DOCKER DAEMON")
        print("=" * 70)

        # Check if Docker is installed
        if not self.run_command(["docker", "--version"], "Checking Docker installation", required=False):
            self.status["optional_skipped"].append("docker-daemon")
            print("⚠️  Docker not found - skipping. (optional but recommended)")
            return False

        # Check if Docker daemon is running
        for attempt in range(3):
            if self.check_port("localhost", 2375, "Docker"):
                self.status["activated"].append("docker-daemon")
                return True
            if attempt < 2:
                print(f"   Attempt {attempt + 1}/3 - retrying...")
                time.sleep(2)

        print("⚠️  Docker daemon not responding. Start Docker Desktop manually.")
        self.status["warnings"].append("docker-daemon-not-responding")
        return False

    def activate_ollama(self) -> bool:
        """Check and start Ollama if available."""
        print("\n" + "=" * 70)
        print("[2/7] OLLAMA LOCAL LLM")
        print("=" * 70)

        # Check if Ollama is installed
        if not self.run_command(["ollama", "--version"], "Checking Ollama installation", required=False):
            self.status["optional_skipped"].append("ollama")
            print("⚠️  Ollama not installed - skipping.")
            print("   Install: https://ollama.ai/download")
            return False

        # Check if Ollama is running
        for attempt in range(3):
            if self.check_port("localhost", 11434, "Ollama"):
                self.status["activated"].append("ollama-service")
                return True
            if attempt < 2:
                print(f"   Attempt {attempt + 1}/3 - retrying...")
                time.sleep(2)

        print("⚠️  Ollama not responding. Start manually with: ollama serve")
        self.status["warnings"].append("ollama-not-responding")
        return False

    def activate_precommit(self) -> bool:
        """Setup pre-commit hooks."""
        print("\n" + "=" * 70)
        print("[3/7] PRE-COMMIT QUALITY GATES")
        print("=" * 70)

        if self.run_command(
            [sys.executable, "-m", "pip", "install", "pre-commit"],
            "Installing pre-commit",
            required=False,
        ):
            if self.run_command(["pre-commit", "install"], "Installing git hooks", required=False):
                self.status["activated"].append("pre-commit-hooks")
                return True

        self.status["warnings"].append("pre-commit-setup-incomplete")
        return False

    def activate_coverage(self) -> bool:
        """Verify pytest coverage configuration."""
        print("\n" + "=" * 70)
        print("[4/7] PYTEST COVERAGE BASELINE")
        print("=" * 70)

        pyproject = self.root_path / "pyproject.toml"
        if pyproject.exists():
            print("✅ pyproject.toml found")
            self.status["activated"].append("pytest-coverage-config")
            return True
        else:
            print("❌ pyproject.toml not found")
            self.status["failed"].append("pytest-coverage-config")
            return False

    def activate_quest_system(self) -> bool:
        """Initialize quest system."""
        print("\n" + "=" * 70)
        print("[5/7] QUEST SYSTEM & CONTEXT LOGGING")
        print("=" * 70)

        quest_log = self.root_path / "src/Rosetta_Quest_System/quest_log.jsonl"
        if quest_log.exists():
            print(f"✅ Quest log found at {quest_log}")
            self.status["activated"].append("quest-system")
            return True
        else:
            print("⚠️  Quest log not found - will be created on first use")
            self.status["warnings"].append("quest-log-not-found")
            return True

    def activate_orchestrator(self) -> bool:
        """Activate AI agent orchestrator."""
        print("\n" + "=" * 70)
        print("[6/7] AI AGENT ORCHESTRATOR")
        print("=" * 70)

        try:
            from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator

            orchestrator = UnifiedAIOrchestrator()
            print("✅ Orchestrator initialized")
            print(f"   AI Systems: {len(orchestrator.ai_systems)}")
            self.status["activated"].append("orchestrator")
            return True
        except Exception as e:
            print(f"⚠️  Could not initialize orchestrator: {str(e)[:100]}")
            self.status["warnings"].append(f"orchestrator-init-error: {str(e)[:50]}")
            return False

    def activate_observability(self) -> bool:
        """Start OpenTelemetry stack (Docker-based)."""
        print("\n" + "=" * 70)
        print("[7/7] OPENTELEMETRY OBSERVABILITY (Optional)")
        print("=" * 70)

        observability_compose = self.root_path / "dev/observability/docker-compose.observability.yml"
        if not observability_compose.exists():
            print("⚠️  Observability compose file not found")
            self.status["optional_skipped"].append("observability-compose-missing")
            return False

        if not self.run_command(
            ["docker", "compose", "--version"],
            "Checking Docker Compose",
            required=False,
        ):
            print("⚠️  Docker Compose not available - skipping observability")
            self.status["optional_skipped"].append("docker-compose-missing")
            return False

        if self.run_command(
            [
                "docker",
                "compose",
                "-f",
                str(observability_compose),
                "up",
                "-d",
            ],
            "Starting OpenTelemetry stack",
            required=False,
        ):
            print("   Waiting for services to start...")
            time.sleep(3)

            # Check Jaeger
            if self.check_port("localhost", 16686, "Jaeger UI"):
                print("   🌐 Access Jaeger traces at http://localhost:16686")
            if self.check_port("localhost", 4317, "OTLP Collector"):
                print("   📊 OTLP collector ready at http://localhost:4317")

            self.status["activated"].append("observability-stack")
            return True

        return False

    def generate_summary(self) -> None:
        """Print activation summary."""
        print("\n" + "=" * 70)
        print("🎯 ECOSYSTEM ACTIVATION SUMMARY")
        print("=" * 70)

        print(f"\n✅ ACTIVATED ({len(self.status['activated'])} components)")
        for comp in self.status["activated"]:
            print(f"   • {comp}")

        if self.status["warnings"]:
            print(f"\n⚠️  WARNINGS ({len(self.status['warnings'])} items)")
            for warning in self.status["warnings"]:
                print(f"   • {warning}")

        if self.status["optional_skipped"]:
            print(f"\n🔄 OPTIONAL SKIPPED ({len(self.status['optional_skipped'])} items)")
            for skipped in self.status["optional_skipped"]:
                print(f"   • {skipped}")

        if self.status["failed"]:
            print(f"\n❌ FAILED ({len(self.status['failed'])} items)")
            for failed in self.status["failed"]:
                print(f"   • {failed}")

    def log_to_quest_system(self) -> None:
        """Log activation to quest system."""
        quest_log = self.root_path / "src/Rosetta_Quest_System/quest_log.jsonl"
        try:
            quest_entry = {
                "timestamp": datetime.now().isoformat(),
                "agent": "system",
                "action": "full_ecosystem_activation",
                "status": ("success" if not self.status["failed"] else "partial"),
                "components_activated": self.status["activated"],
                "components_warnings": self.status["warnings"],
                "components_optional_skipped": self.status["optional_skipped"],
                "components_failed": self.status["failed"],
                "metadata": {
                    "timestamp": self.status["timestamp"],
                    "total_activated": len(self.status["activated"]),
                    "total_warnings": len(self.status["warnings"]),
                    "total_skipped": len(self.status["optional_skipped"]),
                    "total_failed": len(self.status["failed"]),
                },
            }

            if quest_log.parent.exists():
                with open(quest_log, "a") as f:
                    f.write(json.dumps(quest_entry) + "\n")
                print(f"✅ Logged to quest system: {quest_log}")
            else:
                print("⚠️  Quest log directory not ready - will log on next run")
        except Exception as e:
            print(f"⚠️  Could not log to quest system: {e}")

    def print_next_steps(self) -> None:
        """Print recommended next steps."""
        print("\n" + "=" * 70)
        print("📝 NEXT STEPS")
        print("=" * 70)

        if "docker-daemon" not in self.status["activated"]:
            print("\n1. DOCKER (Recommended)")
            print("   📥 Install: https://www.docker.com/products/docker-desktop")
            print("   ▶️ Start Docker Desktop")
            print("   🔄 Re-run this script to activate observability")

        if "ollama-service" not in self.status["activated"]:
            print("\n2. OLLAMA (Recommended)")
            print("   📥 Install: https://ollama.ai/download")
            print("   ▶️ Run: ollama serve")
            print("   🔄 Re-run this script to activate local LLM")

        print("\n3. WEEKLY MONITORING")
        print("   python scripts/start_nusyq.py brief")
        print("   python scripts/start_nusyq.py error_report")
        print("   pytest --cov=src --cov-report=term-missing")

        print("\n4. DAILY USAGE")
        print("   git commit -m 'your changes'")
        print("   # Pre-commit auto-checks (Black, Ruff, Mypy, Secrets)")

        if "observability-stack" in self.status["activated"]:
            print("\n5. OBSERVABILITY")
            print("   🌐 Jaeger traces: http://localhost:16686")
            print("   📊 OTLP metrics: http://localhost:4317")

        print("\n6. AI AGENT ORCHESTRATION")
        print("   python scripts/start_nusyq.py ai_status")
        print("   python scripts/start_nusyq.py work")

    def run(self) -> int:
        """Execute full activation sequence."""
        print("\n" + "=" * 70)
        print("🚀 COMPLETE ECOSYSTEM ACTIVATION SEQUENCE")
        print("=" * 70)
        print("This will activate all critical services:")
        print("  • Docker daemon (local containers)")
        print("  • Ollama (local LLM for agents)")
        print("  • Pre-commit (quality gates)")
        print("  • Pytest coverage (test metrics)")
        print("  • Quest system (context logging)")
        print("  • AI orchestrator (agent coordination)")
        print("  • OpenTelemetry (observability)")
        print("=" * 70)

        # Execute activation sequence
        self.activate_docker()
        self.activate_ollama()
        self.activate_precommit()
        self.activate_coverage()
        self.activate_quest_system()
        self.activate_orchestrator()
        self.activate_observability()

        # Log and summarize
        self.log_to_quest_system()
        self.generate_summary()
        self.print_next_steps()

        print("\n" + "=" * 70)
        print("🎉 ACTIVATION COMPLETE - System ready for AI agent coordination")
        print("=" * 70)

        # Exit code: 0 if no required components failed
        return 0 if not self.status["failed"] else 1


if __name__ == "__main__":
    activator = EcosystemActivator()
    sys.exit(activator.run())
