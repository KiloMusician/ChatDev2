"""
System Information Service - NuSyQ ecosystem status
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict

try:
    from .models import SystemInfoRequest
except ImportError:
    from models import SystemInfoRequest

logger = logging.getLogger(__name__)


class SystemInfoService:
    """Service for retrieving system and AI ecosystem information"""

    def __init__(self, config_manager=None):
        self.config_manager = config_manager

    async def get_info(self, request: SystemInfoRequest) -> Dict[str, Any]:
        """
        Retrieve NuSyQ ecosystem system information

        Args:
            request: Validated system info request with component filter

        Returns:
            Dictionary with requested system information
        """
        component = request.component

        try:
            info = {}

            # Configuration status
            if component in ["all", "config"]:
                info["configurations"] = await self._get_config_status()

            # Ollama service status
            if component in ["all", "ollama"]:
                info["ollama_status"] = await self._get_ollama_status()

            # Available model definitions
            if component in ["all", "models"]:
                info["available_models"] = await self._get_available_models()

            return {"success": True, "info": info}

        except Exception as e:
            logger.error(f"System info query failed: {e}")
            return {"success": False, "error": str(e)}

    async def _get_config_status(self) -> Dict[str, bool]:
        """Get configuration loading status"""
        config_files = {
            "manifest": Path("nusyq.manifest.yaml"),
            "knowledge_base": Path("knowledge-base.yaml"),
            "ai_ecosystem": Path("AI_Hub/ai-ecosystem.yaml"),
            "tasks": Path("config/tasks.yaml"),
        }

        status = {}
        for name, path in config_files.items():
            status[name] = path.exists()

        return status

    async def _get_ollama_status(self) -> Dict[str, Any]:
        """Check Ollama service status"""
        try:
            # Check Ollama via CLI command
            # Increased from 10s to 20s - model list can be slow on first call
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=20)

            if result.returncode == 0:
                # Parse model list (skip header row)
                models = result.stdout.strip().split("\n")[1:] if result.returncode == 0 else []

                return {"running": True, "models": models, "model_count": len(models)}
            else:
                return {"running": False, "error": "Ollama not responding"}

        except subprocess.TimeoutExpired:
            return {"running": False, "error": "Ollama command timed out"}
        except FileNotFoundError:
            return {"running": False, "error": "Ollama not installed"}
        except Exception as e:
            return {"running": False, "error": str(e)}

    async def _get_available_models(self) -> list:
        """Get available model definitions from configuration"""
        if not self.config_manager:
            return []

        try:
            ollama_config = self.config_manager.get_ollama_config()
            if ollama_config and ollama_config.models:
                return [
                    {"name": name, "description": desc}
                    for name, desc in ollama_config.models.items()
                ]
            return []

        except Exception as e:
            logger.error(f"Failed to get model definitions: {e}")
            return []

    async def check_component_health(self) -> Dict[str, bool]:
        """Check health of all components"""
        health = {}

        # Check Ollama
        ollama_status = await self._get_ollama_status()
        health["ollama"] = ollama_status.get("running", False)

        # Check ChatDev
        health["chatdev"] = Path("ChatDev").exists()

        # Check configurations
        config_status = await self._get_config_status()
        health["configuration"] = any(config_status.values())

        return health
