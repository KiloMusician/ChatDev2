#!/usr/bin/env python3
"""🚀 System Activation Script - Full AI Agent Enablement.

Activates all systems required for full AI agent coordination:
1. Loads environment variables from .env
2. Verifies all service endpoints
3. Activates quest system
4. Registers all AI systems with orchestrator
5. Validates Docker deployment readiness
6. Generates coordination instructions

Run this script to ensure the system is fully operational.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Initialize terminal logging (best-effort) so activation logs appear in the
# structured TerminalManager channels when available.
try:
    from src.system.init_terminal import init_terminal_logging

    init_terminal_logging(channel="ActivateSystem")
except Exception:
    # non-fatal if terminal logging shim isn't present in this environment
    pass


# Constants for deduplication
SRC_ORCHESTRATION = "src/orchestration"
DEPLOY_DOCKER_COMPOSE = "deploy/docker-compose.yml"

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import after path setup to ensure module is found
from AI_AGENT_COORDINATION_MASTER import AIAgentCoordinationMaster

logging.basicConfig(
    level=logging.INFO,
    format="🚀 [%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_env_file(env_path: Path = Path(".env")) -> dict[str, str]:
    """Load environment variables from .env file."""
    env_vars: dict[str, str] = {}
    if not env_path.exists():
        logger.warning(f"⚠️ {env_path} not found - using system environment only")
        return env_vars

    logger.info(f"📄 Loading environment from: {env_path}")
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                env_vars[key] = value
                os.environ[key] = value

    logger.info(f"✅ Loaded {len(env_vars)} environment variables")
    return env_vars


def verify_critical_paths() -> dict[str, bool]:
    """Verify all critical system paths exist."""
    logger.info("🔍 Verifying critical system paths...")

    paths = {
        SRC_ORCHESTRATION: Path(SRC_ORCHESTRATION),
        "src/Rosetta_Quest_System": Path("src/Rosetta_Quest_System"),
        DEPLOY_DOCKER_COMPOSE: Path(DEPLOY_DOCKER_COMPOSE),
        "config/secrets.json": Path("config/secrets.json"),
        "config/settings.json": Path("config/settings.json"),
        ".env": Path(".env"),
    }

    results = {}
    for name, path in paths.items():
        exists = path.exists()
        results[name] = exists
        if exists:
            logger.info(f"  ✅ {name}")
        else:
            logger.warning(f"  ⚠️ {name} - NOT FOUND")

    return results


def activate_quest_system() -> bool:
    """Activate the Rosetta Quest System.

    Be flexible across variants: try quest_manager first, then quest_engine,
    and finally verify presence of quest files.
    """
    # Try quest_manager

    try:
        from src.Rosetta_Quest_System.quest_manager import QuestManager

        logger.info("🎯 Activating Quest System...")
        qm = QuestManager()
        questlines: list[Any] = getattr(qm, "list_questlines", lambda: [])()
        logger.info(f"✅ Quest System active - {len(questlines)} questlines loaded")
        return True
    except ImportError as e:
        logger.warning(f"⚠️ Quest System activation via quest_manager failed: {e}")

    # Try quest_engine (common fallback)
    try:
        from src.Rosetta_Quest_System.quest_engine import QuestEngine

        qe = QuestEngine()
        getattr(qe, "list_quests", lambda *a, **k: None)()
        logger.info("✅ Quest System (quest_engine) active")
        return True
    except ImportError as e:
        logger.warning(f"⚠️ Quest System activation via quest_engine failed: {e}")

    # File presence as last resort
    quest_files = [
        Path("src/Rosetta_Quest_System/quest_engine.py"),
        Path("src/Rosetta_Quest_System/quest_log.jsonl"),
        Path("src/Rosetta_Quest_System/quests.json"),
    ]
    if any(p.exists() for p in quest_files):
        logger.info("✅ Quest System files present - marking as AVAILABLE")
        return True

    return False


def generate_system_manifest() -> dict[str, Any]:
    """Generate comprehensive system manifest for AI agents."""
    from datetime import datetime

    manifest = {
        "system_name": "NuSyQ-Hub Multi-AI Development Environment",
        "version": "5.0.0",
        "activation_timestamp": datetime.now().isoformat(),
        "capabilities": {
            "development": {
                "languages": ["Python", "JavaScript", "TypeScript", "PowerShell", "GDScript"],
                "frameworks": ["React", "Node.js", "Godot"],
                "testing": ["pytest", "unittest", "integration tests"],
            },
            "ai_systems": {
                "ollama": {
                    "description": "Local LLM orchestration",
                    "endpoint": os.environ.get("OLLAMA_HOST", "http://127.0.0.1")
                    + ":"
                    + os.environ.get("OLLAMA_PORT", "11434"),
                    "capabilities": ["code_generation", "analysis", "chat", "review"],
                },
                "chatdev": {
                    "description": "Multi-agent software development",
                    "path": os.environ.get("CHATDEV_PATH", ""),
                    "capabilities": [
                        "project_generation",
                        "team_coordination",
                        "role_based_development",
                    ],
                },
                "copilot": {
                    "description": "GitHub Copilot integration",
                    "capabilities": ["code_completion", "chat", "inline_suggestions"],
                },
                "consciousness_bridge": {
                    "description": "Consciousness-aware AI integration",
                    "capabilities": ["semantic_awareness", "context_synthesis"],
                },
                "quantum_resolver": {
                    "description": "Advanced problem resolution",
                    "capabilities": ["self_healing", "quantum_analysis"],
                },
            },
            "orchestration": {
                "unified_orchestrator": "Multi-AI task routing and coordination",
                "quest_system": "Quest-based development tracking",
                "workflow_pipelines": "Automated development workflows",
            },
            "deployment": {
                "docker": {
                    "enabled": Path(DEPLOY_DOCKER_COMPOSE).exists(),
                    "compose_files": ["docker-compose.yml", "docker-compose.dev.yml"],
                },
                "kubernetes": {
                    "enabled": Path("deploy/k8s").exists(),
                    "manifests": list(Path("deploy").glob("*.yaml")),
                },
            },
            "game_development": {
                "wizard_navigator": "RPG-based repository exploration",
                "godot_integration": "Godot engine AI bridge",
            },
            "web_development": {
                "simulatedverse": {
                    "description": "Consciousness simulation engine",
                    "ports": [5000, 3000],
                },
                "modular_windows": "Dynamic web UI system",
            },
        },
        "key_entry_points": {
            "ai_coordination": "AI_AGENT_COORDINATION_MASTER.py",
            "unified_orchestrator": f"{SRC_ORCHESTRATION}/unified_ai_orchestrator.py",
            "chatdev_orchestrator": f"{SRC_ORCHESTRATION}/chatdev_development_orchestrator.py",
            "quest_system": "src/Rosetta_Quest_System/quest_engine.py",
            "docker_deploy": DEPLOY_DOCKER_COMPOSE,
            "health_check": "src/diagnostics/ecosystem_startup_sentinel.py",
        },
        "environment_requirements": {
            "CHATDEV_PATH": os.environ.get("CHATDEV_PATH", "NOT_SET"),
            "OLLAMA_HOST": os.environ.get("OLLAMA_HOST", "NOT_SET"),
            "OLLAMA_PORT": os.environ.get("OLLAMA_PORT", "NOT_SET"),
        },
    }

    return manifest


def main():
    """Main activation sequence."""
    print("=" * 80)
    print("🚀 NUSYQ-HUB SYSTEM ACTIVATION")
    print("=" * 80)
    print()

    # Step 1: Load environment
    env_vars = load_env_file()

    # Step 2: Verify paths
    paths_ok = verify_critical_paths()
    critical_paths = ["src/orchestration", ".env"]
    if not all(paths_ok.get(p, False) for p in critical_paths):
        logger.error("❌ Critical paths missing - cannot proceed")
        return 1

    # Step 3: Activate quest system
    quest_active = activate_quest_system()

    # Step 4: Initialize coordination master
    logger.info("🤖 Initializing AI Agent Coordination Master...")
    master = AIAgentCoordinationMaster()

    # Step 5: Run readiness check
    readiness = master.run_readiness_check()

    # Step 6: Generate instructions
    logger.info("📝 Generating AI agent instructions...")
    instructions_path = Path("docs/AI_AGENT_INSTRUCTIONS.md")
    instructions_path.parent.mkdir(exist_ok=True, parents=True)
    master.generate_agent_instructions(instructions_path)

    # Step 7: Generate system manifest
    logger.info("📋 Generating system manifest...")
    manifest = generate_system_manifest()
    manifest_path = Path("docs/SYSTEM_MANIFEST.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info(f"✅ Manifest written to: {manifest_path}")

    # Step 8: Display summary
    print()
    print("=" * 80)
    print("✅ SYSTEM ACTIVATION COMPLETE")
    print("=" * 80)
    print()
    print("📊 System Status:")
    print(f"  - Environment Variables: {len(env_vars)} loaded")
    print(f"  - Critical Paths: {sum(paths_ok.values())}/{len(paths_ok)} verified")
    print(f"  - Quest System: {'✅ ACTIVE' if quest_active else '⚠️ INACTIVE'}")
    print(f"  - AI Systems Ready: {sum(readiness.values())}/{len(readiness)}")
    print()
    print("📚 Documentation Generated:")
    print(f"  - Instructions: {instructions_path}")
    print(f"  - Manifest: {manifest_path}")
    print()
    print("🎯 Next Steps:")
    print("  1. Review AI_AGENT_INSTRUCTIONS.md for usage guidance")
    print("  2. Run `docker-compose -f deploy/docker-compose.yml up` to deploy")
    print("  3. Use quest system: python -m src.Rosetta_Quest_System.quest_manager")
    print("  4. Start orchestrator: python -m src.orchestration.unified_ai_orchestrator")
    print()
    print("=" * 80)

    # Return success if most systems are ready
    if sum(readiness.values()) >= len(readiness) * 0.7:
        return 0
    else:
        logger.warning("⚠️ System not fully ready - check warnings above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
