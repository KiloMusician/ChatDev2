#!/usr/bin/env python3
"""ChatDev Task Delegator - Delegates code generation tasks to ChatDev with Ollama.

This script bridges the task queue with ChatDev's multi-agent code generation,
using local Ollama models instead of OpenAI API.
"""

import asyncio
import json
import logging
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ChatDevDelegator")


class ChatDevDelegator:
    """Delegates tasks to ChatDev with Ollama backend."""

    def __init__(self):
        self.chatdev_path = Path("C:/Users/keath/NuSyQ/ChatDev")
        self.output_path = Path(__file__).parent.parent / "data/chatdev_outputs"
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.log_path = Path(__file__).parent.parent / "data/terminal_logs"

    def log_to_terminal(self, message: str, level: str = "INFO"):
        """Write to ChatDev terminal log."""
        log_file = self.log_path / "chatdev.log"
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "channel": "ChatDev",
            "level": level,
            "message": message,
            "meta": {"source": "chatdev_delegator"},
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def create_chatdev_task(self, task_description: str, project_name: str | None = None) -> dict:
        """Create a ChatDev task specification."""
        if not project_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = f"AutoGen_{timestamp}"

        return {
            "task": task_description,
            "name": project_name,
            "model": "qwen2.5-coder:14b",
            "config": "Default",
            "org": "DefaultOrganization",
        }

    def run_chatdev(self, task_spec: dict) -> dict:
        """Execute ChatDev with Ollama backend."""
        logger.info(f"Starting ChatDev: {task_spec['name']}")
        self.log_to_terminal(f"Starting project: {task_spec['name']}")

        # Build command
        cmd = [
            sys.executable,
            str(self.chatdev_path / "run_ollama.py"),
            "--task",
            task_spec["task"],
            "--name",
            task_spec["name"],
            "--model",
            task_spec["model"],
            "--config",
            task_spec["config"],
            "--org",
            task_spec["org"],
        ]

        try:
            # Run ChatDev
            result = subprocess.run(
                cmd,
                cwd=str(self.chatdev_path),
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                env={
                    **dict(__import__("os").environ),
                    "OLLAMA_BASE_URL": "http://localhost:11434",
                    "PYTHONUTF8": "1",
                },
            )

            # Check output directory
            project_output = self.chatdev_path / "WareHouse" / task_spec["name"]

            output = {
                "success": result.returncode == 0,
                "project_name": task_spec["name"],
                "output_path": str(project_output) if project_output.exists() else None,
                "stdout": result.stdout[-2000:] if result.stdout else "",
                "stderr": result.stderr[-1000:] if result.stderr else "",
                "return_code": result.returncode,
            }

            if output["success"]:
                logger.info(f"ChatDev completed: {task_spec['name']}")
                self.log_to_terminal(f"Project completed: {task_spec['name']}", "INFO")
            else:
                logger.error(f"ChatDev failed: {result.stderr[:500]}")
                self.log_to_terminal(f"Project failed: {task_spec['name']}", "ERROR")

            return output

        except subprocess.TimeoutExpired:
            logger.error("ChatDev timed out")
            self.log_to_terminal("Project timed out", "ERROR")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error(f"ChatDev error: {e}")
            self.log_to_terminal(f"Error: {e}", "ERROR")
            return {"success": False, "error": str(e)}

    async def process_chatdev_tasks(self, limit: int = 1):
        """Process ChatDev-targeted tasks from the queue."""
        from src.orchestration.background_task_orchestrator import (
            BackgroundTaskOrchestrator,
            TaskStatus,
        )

        bg = BackgroundTaskOrchestrator()

        # Find ChatDev tasks
        chatdev_tasks = [t for t in bg.tasks.values() if t.target.name == "CHATDEV" and t.status.name == "QUEUED"]

        logger.info(f"Found {len(chatdev_tasks)} ChatDev tasks")

        processed = 0
        for task in chatdev_tasks[:limit]:
            logger.info(f"Processing: {task.task_id}")

            # Create ChatDev spec
            spec = self.create_chatdev_task(task.prompt)

            # Run ChatDev
            result = self.run_chatdev(spec)

            # Update task status
            if result.get("success"):
                task.status = TaskStatus.COMPLETED
                task.result = json.dumps(result)
                task.completed_at = datetime.now(UTC)
            else:
                task.status = TaskStatus.FAILED
                task.error = result.get("error", "unknown error")

            bg._save_tasks()
            processed += 1

        return processed


async def main():
    """Run ChatDev delegator."""
    delegator = ChatDevDelegator()

    # Check if ChatDev is available
    if not delegator.chatdev_path.exists():
        logger.error(f"ChatDev not found at {delegator.chatdev_path}")
        return

    # Process ChatDev tasks
    processed = await delegator.process_chatdev_tasks(limit=1)
    logger.info(f"Processed {processed} ChatDev tasks")


if __name__ == "__main__":
    asyncio.run(main())
