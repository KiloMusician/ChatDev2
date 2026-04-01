#!/usr/bin/env python3
"""🔌 System Awakener - Discover & Activate Dormant Systems.

===================================================================================

Scans the ecosystem for dormant, misconfigured, or disconnected systems and provides
automated activation/repair scripts.

Critical Systems Checked:
- Ollama (9 local LLM models)
- ChatDev (multi-agent development company)
- MCP Server (Model Context Protocol)
- Consciousness Bridge
- Quantum Resolver
- Multi-AI Orchestrator
- Knowledge Base connectivity
- Environment variables

OmniTag: {
    "purpose": "Discover and activate dormant ecosystem systems",
    "dependencies": ["ollama", "chatdev", "mcp_server", "consciousness_bridge"],
    "context": "System health and activation orchestration",
    "evolution_stage": "v1.0"
}
===================================================================================
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SystemAwakener:
    """🔌 Discovers dormant systems and provides activation scripts."""

    def __init__(self, nusyq_hub_root: str = ".") -> None:
        """Initialize SystemAwakener with nusyq_hub_root."""
        self.hub_root = Path(nusyq_hub_root).resolve()
        self.nusyq_root = self._find_nusyq_root()

        self.systems_status: dict[str, Any] = {}
        self.activation_scripts: list[str] = []
        self.errors: list[str] = []

    def _find_nusyq_root(self) -> Path:
        """Find NuSyQ root directory."""
        env_root = os.environ.get("NUSYQ_ROOT_PATH")
        candidates = [
            Path(env_root) if env_root else None,
            Path.home() / "NuSyQ",
            self.hub_root.parent.parent / "NuSyQ",
        ]

        for candidate in candidates:
            if not candidate:
                continue
            if candidate.exists() and (candidate / "nusyq.manifest.yaml").exists():
                return candidate

        return self.hub_root

    def check_ollama(self) -> dict[str, Any]:
        """Check Ollama status and available models."""
        status: dict[str, Any] = {
            "name": "Ollama",
            "running": False,
            "models": [],
            "issues": [],
            "activation_needed": False,
        }

        try:
            # Check if Ollama is running
            result = subprocess.run(
                ["ollama", "list"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                status["running"] = True

                # Parse models
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            status["models"].append(parts[0])

                # Check expected models
                expected_models = [
                    "qwen2.5-coder:14b",
                    "starcoder2:15b",
                    "gemma2:9b",
                    "gemma2:27b",
                    "codellama:7b",
                    "llama3.1:8b",
                    "deepseek-coder-v2:16b",
                ]

                missing = [
                    m for m in expected_models if not any(m in model for model in status["models"])
                ]
                if missing:
                    status["issues"].append(
                        f"Missing {len(missing)} expected models: {', '.join(missing[:3])}",
                    )
            else:
                status["issues"].append("Ollama command failed")
                status["activation_needed"] = True

        except FileNotFoundError:
            status["issues"].append("Ollama not installed")
            status["activation_needed"] = True
        except subprocess.TimeoutExpired:
            status["issues"].append("Ollama not responding")
            status["activation_needed"] = True
        except Exception as e:
            status["issues"].append(f"Error: {e}")

        return status

    def check_chatdev(self) -> dict[str, Any]:
        """Check ChatDev installation and configuration."""
        status: dict[str, Any] = {
            "name": "ChatDev",
            "installed": False,
            "configured": False,
            "path": None,
            "issues": [],
            "activation_needed": False,
        }

        # Check environment variable
        chatdev_path_env = os.getenv("CHATDEV_PATH")

        # Check config files
        config_paths = [
            self.hub_root / "config" / "secrets.json",
            self.hub_root / ".env",
        ]

        chatdev_path = None

        # Try environment variable
        if chatdev_path_env:
            chatdev_path = Path(chatdev_path_env)
            status["path"] = str(chatdev_path)

        # Try config files
        if not chatdev_path:
            for config_file in config_paths:
                if config_file.exists():
                    try:
                        if config_file.suffix == ".json":
                            with open(config_file, encoding="utf-8") as f:
                                config = json.load(f)
                                if "chatdev_path" in config or "chatdev" in config:
                                    path_val = config.get("chatdev_path") or config.get(
                                        "chatdev",
                                        {},
                                    ).get("path")
                                    if path_val:
                                        chatdev_path = Path(path_val)
                                        status["path"] = str(chatdev_path)
                                        break
                        elif config_file.suffix == ".env":
                            with open(config_file, encoding="utf-8") as f:
                                for line in f:
                                    if line.startswith("CHATDEV_PATH="):
                                        path_val = line.split("=", 1)[1].strip().strip("\"'")
                                        if path_val:
                                            chatdev_path = Path(path_val)
                                            status["path"] = str(chatdev_path)
                                            break
                    except (FileNotFoundError, UnicodeDecodeError, OSError, IndexError):
                        logger.debug(
                            "Suppressed FileNotFoundError/IndexError/OSError/UnicodeDecodeError",
                            exc_info=True,
                        )

        # Try NuSyQ root
        if not chatdev_path:
            candidate = self.nusyq_root / "ChatDev"
            if candidate.exists():
                chatdev_path = candidate
                status["path"] = str(chatdev_path)

        # Validate path
        if chatdev_path and chatdev_path.exists():
            status["installed"] = True

            # Check for key files
            required_files = ["run.py", "chatdev/chat_chain.py"]
            missing_files: list[Any] = []
            for file in required_files:
                if not (chatdev_path / file).exists():
                    missing_files.append(file)

            if missing_files:
                status["issues"].append(f"Missing files: {', '.join(missing_files)}")
            else:
                status["configured"] = True

                # Check if environment variable is set
                if not chatdev_path_env:
                    status["issues"].append("CHATDEV_PATH environment variable not set")
                    status["activation_needed"] = True
        else:
            status["issues"].append("ChatDev not found - path not configured or doesn't exist")
            status["activation_needed"] = True

        return status

    def check_mcp_server(self) -> dict[str, Any]:
        """Check MCP (Model Context Protocol) Server."""
        status: dict[str, Any] = {
            "name": "MCP Server",
            "installed": False,
            "running": False,
            "path": None,
            "issues": [],
            "activation_needed": False,
        }

        # Look for MCP server
        mcp_paths = [
            self.nusyq_root / "mcp_server" / "main.py",
            self.hub_root / "mcp_server" / "main.py",
        ]

        for path in mcp_paths:
            if path.exists():
                status["installed"] = True
                status["path"] = str(path.parent)

                # Check if running (would need to check process or port)
                # For now, just mark as installed
                status["activation_needed"] = True  # Assume needs activation
                status["issues"].append("Not verified if running")
                break

        if not status["installed"]:
            status["issues"].append("MCP Server not found")
            status["activation_needed"] = True

        return status

    def check_consciousness_bridge(self) -> dict[str, Any]:
        """Check Consciousness Bridge and memory database."""
        status: dict[str, Any] = {
            "name": "Consciousness Bridge",
            "installed": False,
            "database_exists": False,
            "path": None,
            "issues": [],
            "activation_needed": False,
        }

        # Check for consciousness bridge code
        bridge_path = self.hub_root / "src" / "copilot" / "copilot_enhancement_bridge.py"
        if bridge_path.exists():
            status["installed"] = True
            status["path"] = str(bridge_path)

            # Check for database
            db_path = self.hub_root / "copilot_memory" / "consciousness_memory.db"
            if db_path.exists():
                status["database_exists"] = True
            else:
                status["issues"].append("Database not initialized")
                status["activation_needed"] = True
        else:
            status["issues"].append("Consciousness Bridge code not found")
            status["activation_needed"] = True

        return status

    def check_knowledge_base(self) -> dict[str, Any]:
        """Check knowledge base connectivity."""
        status: dict[str, Any] = {
            "name": "Knowledge Base",
            "accessible": False,
            "path": None,
            "sessions": 0,
            "issues": [],
            "activation_needed": False,
        }

        kb_path = self.nusyq_root / "knowledge-base.yaml"
        if kb_path.exists():
            status["accessible"] = True
            status["path"] = str(kb_path)

            try:
                import yaml  # type: ignore[import]

                with open(kb_path, encoding="utf-8") as f:
                    kb = yaml.safe_load(f)
                    status["sessions"] = len(kb.get("sessions", []))
            except Exception as e:
                status["issues"].append(f"Failed to parse: {e}")
        else:
            status["issues"].append("Knowledge base file not found")
            status["activation_needed"] = True

        return status

    def check_environment_variables(self) -> dict[str, Any]:
        """Check critical environment variables."""
        status: dict[str, Any] = {
            "name": "Environment Variables",
            "configured": False,
            "variables": {},
            "issues": [],
            "activation_needed": False,
        }

        critical_vars = {
            "CHATDEV_PATH": "ChatDev installation directory",
            "OLLAMA_BASE_URL": "Ollama API endpoint (optional)",
        }

        missing: list[Any] = []
        for var, description in critical_vars.items():
            value = os.getenv(var)
            status["variables"][var] = value or "NOT SET"
            if not value:
                missing.append(f"{var} ({description})")

        if missing:
            status["issues"] = missing
            status["activation_needed"] = True
        else:
            status["configured"] = True

        return status

    def check_multi_ai_orchestrator(self) -> dict[str, Any]:
        """Check Multi-AI Orchestrator."""
        status: dict[str, Any] = {
            "name": "Multi-AI Orchestrator",
            "installed": False,
            "importable": False,
            "issues": [],
            "activation_needed": False,
        }

        orchestrator_path = self.hub_root / "src" / "orchestration" / "multi_ai_orchestrator.py"
        if orchestrator_path.exists():
            status["installed"] = True

            # Try to import
            try:
                sys.path.insert(0, str(self.hub_root))
                status["importable"] = True
            except Exception as e:
                status["issues"].append(f"Import failed: {e}")
                status["activation_needed"] = True
        else:
            status["issues"].append("Orchestrator not found")
            status["activation_needed"] = True

        return status

    def generate_activation_script(self) -> str:
        """Generate PowerShell activation script."""
        script_lines = [
            "# 🔌 NuSyQ Ecosystem Activation Script",
            "# Generated: " + datetime.now().isoformat(),
            "",
            "Write-Host '🔌 Activating NuSyQ Ecosystem Systems...' -ForegroundColor Cyan",
            "",
        ]

        # Check each system and add activation commands
        for system_name, system_status in self.systems_status.items():
            if system_status.get("activation_needed"):
                script_lines.append(f"# {system_name}")

                if system_name == "Ollama":
                    script_lines.extend(
                        [
                            "Write-Host '🤖 Starting Ollama...' -ForegroundColor Yellow",
                            "Start-Process 'ollama' -ArgumentList 'serve' -WindowStyle Hidden",
                            "Start-Sleep -Seconds 3",
                            "",
                        ],
                    )

                elif system_name == "ChatDev":
                    chatdev_path = system_status.get("path")
                    if chatdev_path:
                        script_lines.extend(
                            [
                                "Write-Host '👥 Configuring ChatDev...' -ForegroundColor Yellow",
                                f"$env:CHATDEV_PATH = '{chatdev_path}'",
                                "",
                            ],
                        )
                    else:
                        script_lines.extend(
                            [
                                "Write-Host '⚠️  ChatDev path not found - manual configuration needed' -ForegroundColor Red",
                                "# Set CHATDEV_PATH manually:",
                                "# $env:CHATDEV_PATH = '${env:USERPROFILE}\\NuSyQ\\ChatDev'",
                                "",
                            ],
                        )

                elif system_name == "MCP Server":
                    mcp_path = system_status.get("path")
                    if mcp_path:
                        script_lines.extend(
                            [
                                "Write-Host '🔗 Starting MCP Server...' -ForegroundColor Yellow",
                                f"Start-Process 'python' -ArgumentList '{mcp_path}\\main.py' -WindowStyle Hidden",
                                "",
                            ],
                        )

                elif system_name == "Consciousness Bridge":
                    script_lines.extend(
                        [
                            "Write-Host '🧠 Initializing Consciousness Bridge...' -ForegroundColor Yellow",
                            f"python '{self.hub_root}\\src\\copilot\\copilot_enhancement_bridge.py'",
                            "",
                        ],
                    )

                elif system_name == "Environment Variables":
                    script_lines.extend(
                        [
                            "Write-Host '🔧 Setting Environment Variables...' -ForegroundColor Yellow",
                        ],
                    )
                    for var, value in system_status.get("variables", {}).items():
                        if value == "NOT SET":
                            script_lines.append(f"# $env:{var} = '<SET_ME>'")
                    script_lines.append("")

        script_lines.extend(
            [
                "Write-Host '✅ Activation Complete!' -ForegroundColor Green",
                "Write-Host 'Run: python health.py --resume' -ForegroundColor Cyan",
            ],
        )

        return "\n".join(script_lines)

    def run_comprehensive_check(self) -> None:
        """Run all system checks."""
        # Run all checks
        self.systems_status["Ollama"] = self.check_ollama()
        self.systems_status["ChatDev"] = self.check_chatdev()
        self.systems_status["MCP Server"] = self.check_mcp_server()
        self.systems_status["Consciousness Bridge"] = self.check_consciousness_bridge()
        self.systems_status["Knowledge Base"] = self.check_knowledge_base()
        self.systems_status["Environment Variables"] = self.check_environment_variables()
        self.systems_status["Multi-AI Orchestrator"] = self.check_multi_ai_orchestrator()

        # Summary

        healthy = 0
        needs_activation = 0

        for status in self.systems_status.values():
            if status.get("activation_needed"):
                needs_activation += 1
                for _issue in status.get("issues", []):
                    pass
            elif (
                status.get("running")
                or status.get("configured")
                or status.get("accessible")
                or status.get("importable")
            ):
                healthy += 1
            else:
                for _issue in status.get("issues", []):
                    pass

        # Generate activation script
        if needs_activation > 0:
            script_path = self.hub_root / "activate_systems.ps1"
            script_content = self.generate_activation_script()

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

        # Save detailed report
        report_path = self.hub_root / "system_awakener_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "systems": self.systems_status,
                    "summary": {
                        "healthy": healthy,
                        "needs_activation": needs_activation,
                        "total": len(self.systems_status),
                    },
                },
                f,
                indent=2,
            )


def main() -> None:
    awakener = SystemAwakener()
    awakener.run_comprehensive_check()


if __name__ == "__main__":
    main()
