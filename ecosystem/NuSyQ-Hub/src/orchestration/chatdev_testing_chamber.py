#!/usr/bin/env python3
"""🧪 KILO-FOOLISH ChatDev Testing Chamber.

Enhanced ChatDev launcher for testing Ollama integration development.

OmniTag: {
    "purpose": "ChatDev testing environment with Ollama integration",
    "dependencies": ["chatdev_launcher.py", "ollama", "testing_chamber"],
    "context": "Recursive AI development, testing chamber operations",
    "evolution_stage": "v4.0"
}
MegaTag: {
    "type": "TestingChamber",
    "integration_points": ["chatdev", "ollama", "testing_environment"],
    "related_tags": ["RecursiveDevelopment", "AIIntegration", "TestChamber"]
}
RSHTS: ΞΨΩ∞⟨RECURSIVE-DEV⟩→ΦΣΣ⟨CHAMBER⟩
"""

import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from src.config.service_config import ServiceConfig
from src.integration.chatdev_launcher import ChatDevLauncher

logger = logging.getLogger(__name__)


class ChatDevTestingChamber:
    """Testing chamber for ChatDev projects with isolated environments.

    Focuses on Ollama integration development with API fallback.
    """

    def __init__(self) -> None:
        """Initialize ChatDevTestingChamber."""
        repo_root = Path(__file__).resolve().parents[2]
        default_chamber = repo_root / "testing_chamber"
        chamber_env = os.getenv("CHATDEV_TESTING_CHAMBER", str(default_chamber))
        self.chamber_root = Path(chamber_env).expanduser()
        self.chatdev_launcher = ChatDevLauncher()

        # Create testing chamber structure
        self.setup_testing_chamber()

    def setup_testing_chamber(self) -> None:
        """Create isolated testing environment."""
        # Create main chamber directory
        self.chamber_root.mkdir(exist_ok=True)

        # Create subdirectories
        subdirs = [
            "ollama_integration",  # Ollama-ChatDev bridge development
            "api_fallback",  # API fallback mechanisms
            "modules",  # Generated modules
            "tests",  # Test scripts
            "configs",  # Configuration files
            "logs",  # Execution logs
            "artifacts",  # Generated artifacts
        ]

        for subdir in subdirs:
            (self.chamber_root / subdir).mkdir(exist_ok=True)

    def create_ollama_chatdev_project(self) -> None:
        """Create ChatDev project for Ollama integration."""
        project_task = """
        Develop a comprehensive Ollama-ChatDev Integration System with the following requirements:

        CORE FEATURES:
        1. OllamaChatDevBridge - Main integration class that:
              - Connects to configured Ollama server (see ServiceConfig)
           - Intercepts ChatDev's OpenAI API calls
           - Routes them through Ollama instead
           - Falls back to OpenAI API if Ollama is unavailable

        2. ChatDevOllamaAdapter - Adapter class that:
           - Translates ChatDev prompts to Ollama format
           - Handles different Ollama models (llama2, codellama, mistral, etc.)
           - Manages conversation context and memory
           - Provides model selection based on task type

        3. ApiFallbackManager - Fallback system that:
           - Monitors Ollama availability
           - Automatically switches to OpenAI when needed
           - Logs all fallback events
           - Provides health checking and recovery

        4. TestingChamberIntegration - Testing utilities that:
           - Creates isolated test environments
           - Validates integration functionality
           - Provides comprehensive logging
           - Generates test reports

        TECHNICAL REQUIREMENTS:
        - Python 3.8+ compatibility
        - Async/await support for concurrent operations
        - Comprehensive error handling and logging
        - Configuration file support (JSON/YAML)
        - Unit tests with pytest
        - Documentation with examples

        INTEGRATION POINTS:
        - Must work with existing ChatDev architecture
        - Should integrate with KILO-FOOLISH secrets management
        - Must support multiple Ollama models
        - Should provide graceful degradation

        The system should be production-ready with proper error handling,
        logging, and configuration management. Include example usage scripts
        and comprehensive documentation.
        """

        project_name = f"OllamaChatDevBridge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Launch ChatDev with our specific task
            process = self.chatdev_launcher.launch_chatdev(
                task=project_task,
                name=project_name,
                model="GPT_3_5_TURBO",  # Use cost-effective model for development
                organization="KiloFoolishChamber",
                config="Default",
            )

            # set up monitoring and post-processing
            # Prepare warehouse path for later post-processing (computed again where needed)

            # Monitor the process
            self.monitor_development_process(process, project_name)

            return process

        except (OSError, subprocess.SubprocessError, AttributeError) as exc:
            logger.error("ChatDev launch failed: %s", exc)
            return None

    def monitor_development_process(self, process, project_name) -> None:
        """Monitor ChatDev development and handle outputs."""
        if process.stdout is None:
            logger.warning("ChatDev process has no stdout; skipping monitoring")
            return

        saw_post_processing = False

        try:
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    # Log important events
                    if "phase" in output.lower():
                        self.log_development_phase(output.strip())

                    # Check for completion
                    if "post processing" in output.lower():
                        saw_post_processing = True
                        self.log_development_phase(f"post-processing: {output.strip()}")

            # Process completed
            process_return_code = process.poll()
            if process_return_code == 0:
                self.post_process_project(project_name)
            else:
                logger.error(
                    "ChatDev process failed for %s (exit=%s)",
                    project_name,
                    process_return_code,
                )

            if saw_post_processing:
                logger.info("Post-processing detected for %s", project_name)

        except KeyboardInterrupt:
            logger.warning("Monitoring interrupted; attempting to terminate ChatDev")
            try:
                process.terminate()
            except Exception as exc:
                logger.debug("Failed to terminate ChatDev process: %s", exc)

    def log_development_phase(self, phase_info) -> None:
        """Log development phases to chamber logs."""
        log_file = self.chamber_root / "logs" / "development.log"
        timestamp = datetime.now().isoformat()

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {phase_info}\n")

    def post_process_project(self, project_name) -> None:
        """Post-process the completed ChatDev project."""
        # Find the generated project
        warehouse_path = self.chatdev_launcher.chatdev_path / "WareHouse"
        project_dirs = list(warehouse_path.glob(f"{project_name}_KiloFoolishChamber_*"))

        if not project_dirs:
            logger.warning("No ChatDev projects found for %s", project_name)
            return

        latest_project = max(project_dirs, key=lambda p: p.stat().st_mtime)

        # Copy to testing chamber
        chamber_project_path = self.chamber_root / "ollama_integration" / latest_project.name

        try:
            shutil.copytree(latest_project, chamber_project_path, dirs_exist_ok=True)

            # Analyze the generated code
            self.analyze_generated_code(chamber_project_path)

            # Create integration scripts
            self.create_integration_scripts(chamber_project_path)

            # Generate test configuration
            self.generate_test_config(chamber_project_path)

        except (OSError, AttributeError) as exc:
            logger.error("Post-processing failed for %s: %s", project_name, exc)

    def analyze_generated_code(self, project_path) -> None:
        """Analyze the generated code structure."""
        python_files = list(project_path.glob("*.py"))

        analysis = {
            "project_path": str(project_path),
            "python_files": [str(f.name) for f in python_files],
            "file_count": len(python_files),
            "analysis_timestamp": datetime.now().isoformat(),
        }

        file_summaries = []
        for py_file in python_files:
            try:
                lines = py_file.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                lines = []
            file_summaries.append({"name": py_file.name, "lines": len(lines)})

        analysis["files"] = file_summaries

        # Save analysis
        analysis_file = self.chamber_root / "artifacts" / f"code_analysis_{project_path.name}.json"

        import json

        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)

        if not python_files:
            logger.info("No Python files found in %s", project_path)

    def create_integration_scripts(self, project_path) -> None:
        """Create integration scripts for the generated project."""
        # Integration script template
        integration_script = f'''#!/usr/bin/env python3
"""
🔗 KILO-FOOLISH Ollama-ChatDev Integration Test Script
Generated integration script for {project_path.name}

This script integrates the ChatDev-generated Ollama bridge with the KILO-FOOLISH system
"""

import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, "{self.chamber_root.parent / "src"!s}")

def test_ollama_integration():
    """Test the generated Ollama integration"""
    print("🧪 Testing Ollama-ChatDev Integration")
    print("=" * 40)

    try:
        # Import generated modules (will be customized based on actual generation)
        # This is a template - actual imports will be determined after code analysis

        print("✅ Integration test template created")
        print("💡 Customize this script based on the generated code structure")

    except Exception as e:
        print(f"❌ Integration test failed: {{e}}")

if __name__ == "__main__":
    test_ollama_integration()
'''

        script_path = project_path / "kilo_integration_test.py"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(integration_script)

    def generate_test_config(self, project_path) -> None:
        """Generate test configuration for the project."""
        config = {
            "project_name": project_path.name,
            "testing_chamber": str(self.chamber_root),
            "ollama_config": {
                "host": ServiceConfig.get_ollama_url(),
                "models": ["llama2", "codellama", "mistral"],
                "fallback_enabled": True,
            },
            "api_fallback": {
                "enabled": True,
                "provider": "openai",
                "model": "gpt-3.5-turbo",
            },
            "logging": {
                "level": "INFO",
                "file": str(self.chamber_root / "logs" / f"{project_path.name}.log"),
            },
        }

        import json

        config_path = project_path / "kilo_test_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)


def main() -> None:
    """Main entry point for ChatDev Testing Chamber."""
    chamber = ChatDevTestingChamber()

    # Support non-interactive mode via environment variable
    auto_launch = os.getenv("CHATDEV_AUTO_LAUNCH", "false").lower() in [
        "true",
        "1",
        "yes",
    ]

    if auto_launch:
        confirm = "y"
    else:
        confirm = (
            input("\n🚀 Launch ChatDev for Ollama integration development? (y/n): ").strip().lower()
            if sys.stdin.isatty()
            else "n"
        )

    if confirm == "y":
        chamber.create_ollama_chatdev_project()
    else:
        logger.info("[INFO] Skipping ChatDev launch. Set CHATDEV_AUTO_LAUNCH=true to auto-launch.")


if __name__ == "__main__":
    main()
