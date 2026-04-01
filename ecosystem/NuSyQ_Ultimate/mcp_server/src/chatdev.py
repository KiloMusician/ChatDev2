"""
ChatDev Service - Multi-agent software creation
"""

import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

try:
    from .models import ChatDevRequest
except ImportError:
    from models import ChatDevRequest

logger = logging.getLogger(__name__)


class ChatDevService:
    """Service for ChatDev multi-agent framework integration"""

    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.chatdev_path = Path("ChatDev")

    async def create_software(self, request: ChatDevRequest) -> Dict[str, Any]:
        """
        Create software using ChatDev multi-agent framework

        Args:
            request: Validated ChatDev request with task, model, config

        Returns:
            Dictionary with success status, project details, and logs
        """
        task = request.task
        model = request.model
        config = request.config
        timeout = request.timeout

        # Validate ChatDev availability
        if not self.chatdev_path.exists():
            return {
                "success": False,
                "error": "ChatDev not found in workspace",
                "suggestion": "Clone ChatDev repository to workspace",
            }

        try:
            # Generate project name from task
            project_name = self._generate_project_name(task)

            # Prepare command
            cmd = [
                sys.executable,
                str(self.chatdev_path / "run.py"),
                "--task",
                task,
                "--config",
                config,
                "--name",
                project_name,
                "--org",
                "NuSyQ",
            ]

            # Set environment to use Ollama (mock OpenAI key)
            env = os.environ.copy()
            env["OPENAI_API_KEY"] = "ollama-local-model"
            env["NUSYQ_OLLAMA_MODEL"] = model

            logger.info(f"Starting ChatDev: task='{task}', model={model}, config={config}")

            # Execute ChatDev
            result = self._run_subprocess(cmd, env, timeout)

            # Determine output path
            warehouse_path = self.chatdev_path / "WareHouse" / project_name

            if result["returncode"] == 0:
                # Success - parse output and provide summary
                summary = f"Created software project: {project_name}"
                if warehouse_path.exists():
                    files = list(warehouse_path.glob("*"))
                    summary += f" ({len(files)} files generated)"

                return {
                    "success": True,
                    "project_name": project_name,
                    "output_path": str(warehouse_path),
                    "summary": summary,
                    "logs": result["stdout"][-1000:],  # Last 1000 chars
                    "model_used": model,
                    "config_used": config,
                }
            else:
                # Failure - return error information
                error_msg = result["stderr"] if result["stderr"] else "ChatDev execution failed"
                return {
                    "success": False,
                    "error": error_msg,
                    "logs": result["stdout"][-1000:] if result["stdout"] else "",
                    "command": " ".join(cmd),
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"ChatDev timed out after {timeout} seconds",
                "suggestion": "Try a simpler task or increase timeout",
            }
        except Exception as e:
            logger.error(f"ChatDev execution failed: {e}")
            return {"success": False, "error": f"ChatDev execution failed: {str(e)}"}

    def _generate_project_name(self, task: str) -> str:
        """Generate valid project name from task description"""
        # Remove special characters and truncate
        clean_task = re.sub(r"\W", "_", task[:30])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"NuSyQ_{clean_task}_{timestamp}"

    def _run_subprocess(self, command: list, env: dict, timeout: int) -> Dict[str, Any]:
        """Run subprocess command synchronously"""
        try:
            result = subprocess.run(
                command, env=env, capture_output=True, text=True, timeout=timeout
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            raise
        except Exception as e:
            logger.error(f"Subprocess execution failed: {e}")
            return {"stdout": "", "stderr": str(e), "returncode": 1}
