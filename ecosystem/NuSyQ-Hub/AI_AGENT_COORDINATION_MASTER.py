#!/usr/bin/env python3
"""🤖 AI Agent Coordination Master - Full System Enablement.

This module ensures all AI agents (GitHub Copilot, Ollama, ChatDev, etc.)
can fully utilize the NuSyQ-Hub system for:
- Development & debugging
- Game development
- Web application generation
- Package creation
- Quest-based development
- Docker deployment
- Multi-agent harmonious collaboration

OmniTag: {
    "purpose": "ai_agent_coordination_master",
    "tags": ["orchestration", "multi-agent", "system-enablement"],
    "category": "infrastructure",
    "evolution_stage": "production_ready"
}
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Initialize terminal logging (best-effort) so coordination master logs appear
# in the structured TerminalManager channels when available.
try:
    from src.system.init_terminal import init_terminal_logging

    init_terminal_logging(channel="AI-Agent-Coordinator")
except Exception:
    pass

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import after path setup
from src.config.service_config import ServiceConfig
from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator
from src.utils.timeout_config import get_timeout

logging.basicConfig(
    level=logging.INFO,
    format="🤖 [%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class AIAgentCoordinationMaster:
    """Master coordination system for all AI agents in the ecosystem."""

    def __init__(self, project_root: str | Path = "."):
        """Initialize the AI Agent Coordination Master.

        Args:
            project_root: Root directory of the NuSyQ-Hub project
        """
        self.project_root = Path(project_root).resolve()
        self.orchestrator = UnifiedAIOrchestrator()
        self.config = self._load_system_config()
        self.capabilities_map = self._build_capabilities_map()

        logger.info("🚀 AI Agent Coordination Master initialized")
        logger.info(f"📂 Project Root: {self.project_root}")
        logger.info(f"🎯 Capabilities: {len(self.capabilities_map)} systems registered")

    def _load_system_config(self) -> dict[str, Any]:
        """Load comprehensive system configuration."""
        config = {
            "project_root": str(self.project_root),
            "ollama": {
                "enabled": True,
                "url": ServiceConfig.get_ollama_url(),
                "models": self._get_ollama_models(),
            },
            "chatdev": {
                "enabled": bool(os.environ.get("CHATDEV_PATH")),
                "path": os.environ.get("CHATDEV_PATH", ""),
            },
            "docker": {
                "enabled": self._check_docker_available(),
                "compose_files": list(self.project_root.glob("deploy/docker-compose*.yml")),
            },
            "quest_system": {
                "enabled": (self.project_root / "src/Rosetta_Quest_System").exists(),
                "quest_log": str(self.project_root / "src/Rosetta_Quest_System/quest_log.jsonl"),
            },
            "game_dev": {
                "wizard_navigator": (self.project_root / "src/tools/wizard_navigator.py").exists(),
                "godot_integration": (
                    self.project_root / "src/integration/godot_bridge.py"
                ).exists(),
            },
            "web_dev": {
                "simulatedverse": {
                    "enabled": True,
                    "url": ServiceConfig.get_simulatedverse_url(),
                },
                "react_ui": {
                    "enabled": True,
                    "url": f"{ServiceConfig.REACT_UI_HOST}:{ServiceConfig.REACT_UI_PORT}",
                },
            },
        }
        return config

    def _get_ollama_models(self) -> list[str]:
        """Get list of available Ollama models."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=get_timeout("TOOL_CHECK_TIMEOUT_SECONDS", 10),
                check=False,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                return [line.split()[0] for line in lines if line.strip()]
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("⚠️ Ollama not available")
        return []

    def _check_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                timeout=get_timeout("TOOL_CHECK_TIMEOUT_SECONDS", 10),
                check=False,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _build_capabilities_map(self) -> dict[str, dict[str, Any]]:
        """Build comprehensive capabilities map for AI agents."""
        return {
            "development": {
                "python": ["coding", "testing", "debugging", "refactoring"],
                "javascript": ["web_dev", "react", "node"],
                "typescript": ["web_dev", "type_checking"],
                "powershell": ["automation", "scripting", "windows"],
                "gdscript": ["game_dev", "godot"],
            },
            "ai_systems": {
                "ollama": {
                    "enabled": self.config["ollama"]["enabled"],
                    "models": self.config["ollama"]["models"],
                    "capabilities": [
                        "code_generation",
                        "code_review",
                        "documentation",
                        "analysis",
                        "chat",
                    ],
                },
                "chatdev": {
                    "enabled": self.config["chatdev"]["enabled"],
                    "capabilities": [
                        "multi_agent_development",
                        "project_generation",
                        "team_coordination",
                        "code_review",
                    ],
                },
                "copilot": {
                    "enabled": True,  # GitHub Copilot assumed available
                    "capabilities": [
                        "code_completion",
                        "chat",
                        "inline_suggestions",
                        "test_generation",
                    ],
                },
            },
            "orchestration": {
                "quest_system": {
                    "enabled": self.config["quest_system"]["enabled"],
                    "features": ["task_tracking", "quest_chains", "zeta_integration"],
                },
                "unified_orchestrator": {
                    "enabled": True,
                    "features": [
                        "multi_ai_coordination",
                        "task_routing",
                        "workflow_management",
                    ],
                },
            },
            "deployment": {
                "docker": {
                    "enabled": self.config["docker"]["enabled"],
                    "compose_files": len(self.config["docker"]["compose_files"]),
                },
                "kubernetes": {
                    "enabled": (self.project_root / "deploy/k8s").exists(),
                },
            },
            "game_development": {
                "wizard_navigator": {
                    "enabled": self.config["game_dev"]["wizard_navigator"],
                    "features": ["rpg_system", "repository_exploration"],
                },
                "godot": {
                    "enabled": self.config["game_dev"]["godot_integration"],
                    "features": ["scene_generation", "ai_integration"],
                },
            },
            "web_development": {
                "simulatedverse": {
                    "enabled": self.config["web_dev"]["simulatedverse"]["enabled"],
                    "url": self.config["web_dev"]["simulatedverse"]["url"],
                },
                "react_ui": {
                    "enabled": self.config["web_dev"]["react_ui"]["enabled"],
                    "url": self.config["web_dev"]["react_ui"]["url"],
                },
            },
        }

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status for AI agents."""
        from datetime import datetime

        status = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "config": self.config,
            "capabilities": self.capabilities_map,
            "orchestrator_status": {
                "active_systems": len(self.orchestrator.ai_systems),
                "registered_workflows": len(self.orchestrator.pipelines),
            },
            "environment": {
                "CHATDEV_PATH": os.environ.get("CHATDEV_PATH", "NOT_SET"),
                "OLLAMA_PORT": os.environ.get("OLLAMA_PORT", "NOT_SET"),
                "OLLAMA_HOST": os.environ.get("OLLAMA_HOST", "NOT_SET"),
            },
            "readiness_check": {
                "ollama": self.config["ollama"]["enabled"],
                "chatdev": self.config["chatdev"]["enabled"],
                "docker": self.config["docker"]["enabled"],
                "quest_system": self.config["quest_system"]["enabled"],
                "game_dev": any(self.config["game_dev"].values()),
                "web_dev": any(
                    self.config["web_dev"][k]["enabled"] for k in ["simulatedverse", "react_ui"]
                ),
            },
        }
        return status

    def generate_agent_instructions(self, output_file: str | Path | None = None) -> str:
        """Generate comprehensive instructions for AI agents.

        Args:
            output_file: Optional file to write instructions to

        Returns:
            Formatted instruction text
        """
        status = self.get_system_status()

        instructions = f"""
# 🤖 AI Agent Coordination Instructions - NuSyQ-Hub
**Generated**: {status["timestamp"]}
**Project Root**: {status["project_root"]}

## System Configuration

### AI Systems Available
"""

        # Ollama
        if status["readiness_check"]["ollama"]:
            instructions += f"""
#### Ollama (Local LLMs)
- **Status**: ✅ ENABLED
- **URL**: {status["config"]["ollama"]["url"]}
- **Models Available**: {len(status["config"]["ollama"]["models"])}
  {chr(10).join(f"  - {m}" for m in status["config"]["ollama"]["models"][:10])}
"""
        else:
            instructions += "\n#### Ollama\n- **Status**: ❌ NOT AVAILABLE\n"

        # ChatDev
        if status["readiness_check"]["chatdev"]:
            instructions += f"""
#### ChatDev (Multi-Agent Development)
- **Status**: ✅ ENABLED
- **Path**: {status["config"]["chatdev"]["path"]}
- **Capabilities**: Multi-agent development, project generation, team coordination
"""
        else:
            instructions += "\n#### ChatDev\n- **Status**: ❌ NOT CONFIGURED (Set CHATDEV_PATH)\n"

        # Docker
        if status["readiness_check"]["docker"]:
            instructions += f"""
#### Docker Deployment
- **Status**: ✅ ENABLED
- **Compose Files**: {status["config"]["docker"]["compose_files"]}
"""
        else:
            instructions += "\n#### Docker\n- **Status**: ❌ NOT AVAILABLE\n"

        # Capabilities
        instructions += """
## Development Capabilities

### Programming Languages
- Python (coding, testing, debugging, refactoring)
- JavaScript/TypeScript (web dev, React, Node.js)
- PowerShell (automation, scripting)
- GDScript (game development, Godot)

### AI-Powered Development
"""

        for system, details in status["capabilities"]["ai_systems"].items():
            if details["enabled"]:
                instructions += f"- **{system.title()}**: {', '.join(details['capabilities'])}\n"

        # Quest System
        if status["readiness_check"]["quest_system"]:
            instructions += f"""
### Quest-Based Development
- **Status**: ✅ ENABLED
- **Quest Log**: {status["config"]["quest_system"]["quest_log"]}
- **Features**: Task tracking, quest chains, ZETA integration
"""

        # Game Dev
        if status["readiness_check"]["game_dev"]:
            instructions += """
### Game Development
- Wizard Navigator (RPG system for repository exploration)
- Godot integration (scene generation, AI integration)
"""

        # Web Dev
        if status["readiness_check"]["web_dev"]:
            instructions += f"""
### Web Development
- SimulatedVerse: {status["config"]["web_dev"]["simulatedverse"]["url"]}
- React UI: {status["config"]["web_dev"]["react_ui"]["url"]}
"""

        # Usage Guide
        instructions += """
## Usage Guide for AI Agents

### 1. Development Tasks
```python
from AI_AGENT_COORDINATION_MASTER import AIAgentCoordinationMaster

master = AIAgentCoordinationMaster()
status = master.get_system_status()
print(json.dumps(status, indent=2))
```

### 2. Multi-Agent Orchestration
```python
from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator

orchestrator = UnifiedAIOrchestrator()
orchestrator.register_ai_system(name="ollama", system_type="ollama_local")
result = orchestrator.submit_task(task_type="code_generation", content="...")
```

### 3. Quest-Based Development
```python
from src.Rosetta_Quest_System.quest_manager import QuestManager

qm = QuestManager()
quests = qm.list_quests()
qm.update_quest_status(quest_id, "in_progress")
```

### 4. Docker Deployment
```bash
cd deploy
docker-compose up --build
```

### 5. ChatDev Multi-Agent Development
```bash
python -m src.orchestration.chatdev_development_orchestrator \\
    --project "MyProject" \\
    --description "Build a web app"
```

## Environment Variables Required

```dotenv
CHATDEV_PATH=C:\\Users\\keath\\NuSyQ\\ChatDev
OLLAMA_HOST=http://127.0.0.1
OLLAMA_PORT=11434
```

## Key Integration Points

1. **Unified Orchestrator**: `src/orchestration/unified_ai_orchestrator.py`
2. **ChatDev Development**: `src/orchestration/chatdev_development_orchestrator.py`
3. **Quest System**: `src/Rosetta_Quest_System/`
4. **Docker Deployment**: `deploy/docker-compose.yml`
5. **Service Config**: `src/config/service_config.py`

## Next Steps for Full System Utilization

1. ✅ Verify Ollama models: `ollama list`
2. ✅ Test ChatDev integration: Set CHATDEV_PATH
3. ✅ Run quest system: Check quest_log.jsonl
4. ✅ Deploy with Docker: `docker-compose up`
5. ✅ Coordinate multi-agent tasks via UnifiedAIOrchestrator

---
**System Ready**: All AI agents can now fully utilize NuSyQ-Hub capabilities.
"""

        if output_file:
            output_path = Path(output_file)
            output_path.write_text(instructions, encoding="utf-8")
            logger.info(f"📄 Instructions written to: {output_path}")

        return instructions

    def run_readiness_check(self) -> dict[str, bool]:
        """Run comprehensive readiness check for AI agent coordination."""
        logger.info("🔍 Running AI Agent Readiness Check...")

        checks = {
            "ollama_service": False,
            "chatdev_path": False,
            "docker_available": False,
            "quest_system": False,
            "orchestrator": False,
            "environment_vars": False,
        }

        # Check Ollama
        if self.config["ollama"]["enabled"] and len(self.config["ollama"]["models"]) > 0:
            checks["ollama_service"] = True
            logger.info("✅ Ollama service: READY")
        else:
            logger.warning("⚠️ Ollama service: NOT READY")

        # Check ChatDev
        if self.config["chatdev"]["enabled"]:
            checks["chatdev_path"] = True
            logger.info(f"✅ ChatDev path: {self.config['chatdev']['path']}")
        else:
            logger.warning("⚠️ ChatDev: NOT CONFIGURED (Set CHATDEV_PATH)")

        # Check Docker
        if self.config["docker"]["enabled"]:
            checks["docker_available"] = True
            logger.info("✅ Docker: AVAILABLE")
        else:
            logger.warning("⚠️ Docker: NOT AVAILABLE")

        # Check Quest System (be tolerant: consider engine or log presence)
        try:
            from importlib.util import find_spec as _find_spec
        except ImportError:
            _find_spec = None  # type: ignore[assignment]

        quest_enabled = False
        # Config flag
        if self.config["quest_system"].get("enabled"):
            quest_enabled = True
        # Module available under any known name
        module_candidates = [
            "src.Rosetta_Quest_System.quest_manager",
            "src.Rosetta_Quest_System.quest_engine",
            "Rosetta_Quest_System.quest_engine",
        ]
        if not quest_enabled and _find_spec is not None:
            for mod in module_candidates:
                try:
                    if _find_spec(mod) is not None:
                        quest_enabled = True
                        break
                except (ImportError, ModuleNotFoundError, ValueError):
                    continue
        # Files present
        if not quest_enabled:
            quest_files = [
                Path("src/Rosetta_Quest_System/quest_engine.py"),
                Path("src/Rosetta_Quest_System/quest_log.jsonl"),
                Path("src/Rosetta_Quest_System/quests.json"),
            ]
            if any(p.exists() for p in quest_files):
                quest_enabled = True

        checks["quest_system"] = bool(quest_enabled)
        if quest_enabled:
            logger.info("✅ Quest System: ENABLED")
        else:
            logger.warning("⚠️ Quest System: NOT FOUND")

        # Check Orchestrator
        if self.orchestrator:
            checks["orchestrator"] = True
            logger.info("✅ Unified Orchestrator: READY")

        # Check Environment Variables (consider .env values as well)
        required_vars = ["CHATDEV_PATH", "OLLAMA_PORT", "OLLAMA_HOST"]
        missing = [v for v in required_vars if not os.environ.get(v)]
        if missing:
            # Try loading from .env without exporting globally
            env_file = self.project_root / ".env"
            env_map: dict[str, str] = {}
            if env_file.exists():
                try:
                    for line in env_file.read_text(encoding="utf-8").splitlines():
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, val = line.split("=", 1)
                            env_map[k.strip()] = val.strip()
                except (OSError, UnicodeDecodeError):
                    pass
            missing = [v for v in required_vars if not (os.environ.get(v) or env_map.get(v))]
            env_ready = len(missing) == 0
        else:
            env_ready = True

        if env_ready:
            checks["environment_vars"] = True
            logger.info("✅ Environment Variables: CONFIGURED (env or .env)")
        else:
            logger.warning(f"⚠️ Missing environment variables: {missing}")

        # Overall Status
        ready_count = sum(checks.values())
        total_count = len(checks)
        logger.info(f"\n🎯 Readiness: {ready_count}/{total_count} systems ready")

        if ready_count == total_count:
            logger.info("🚀 SYSTEM FULLY OPERATIONAL - All AI agents ready")
        elif ready_count >= total_count * 0.7:
            logger.info("⚡ SYSTEM MOSTLY READY - Core capabilities operational")
        else:
            logger.warning("⚠️ SYSTEM NEEDS CONFIGURATION - Check warnings above")

        return checks


def main():
    """Main entry point for AI Agent Coordination Master."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Agent Coordination Master")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run readiness check",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status",
    )
    parser.add_argument(
        "--instructions",
        type=str,
        help="Generate agent instructions to file",
    )
    args = parser.parse_args()

    master = AIAgentCoordinationMaster()

    if args.check:
        master.run_readiness_check()

    if args.status:
        status = master.get_system_status()
        print(json.dumps(status, indent=2))

    if args.instructions:
        master.generate_agent_instructions(args.instructions)

    # Default: run readiness check
    if not any([args.check, args.status, args.instructions]):
        master.run_readiness_check()
        separator = "=" * 80
        print(f"\n{separator}")
        print("💡 Tip: Run with --instructions AI_INSTRUCTIONS.md to generate full guide")
        print(separator)


if __name__ == "__main__":
    main()
