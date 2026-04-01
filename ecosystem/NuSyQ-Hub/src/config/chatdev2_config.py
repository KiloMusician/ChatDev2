"""ChatDev2 Fork Integration Configuration.

This module provides configuration and utility functions for integrating
with the canonical KiloMusician/ChatDev2 fork.

OmniTag: {
    "purpose": "ChatDev2 fork integration configuration",
    "dependencies": ["chatdev2_fork", "ollama", "nusyq_framework"],
    "context": "Multi-agent AI development with ΞNuSyQ protocol",
    "evolution_stage": "v1.0"
}
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Canonical ChatDev2 Fork Information
CHATDEV2_REPO = "https://github.com/KiloMusician/ChatDev2.git"
CHATDEV2_BRANCH = "main"
CHATDEV2_COMMIT = "670c805"  # Latest commit as of 2025-02-11

# Default installation paths
DEFAULT_CHATDEV_PATH = Path("C:/Users/keath/NuSyQ/ChatDev")
CHATDEV_WORKSPACE = DEFAULT_CHATDEV_PATH / "WareHouse"


class ChatDev2Config:
    """Configuration helper for ChatDev2 fork integration."""

    def __init__(self, custom_path: Path | None = None):
        """Initialize ChatDev2 configuration.

        Args:
            custom_path: Optional custom path to ChatDev installation.
                        Falls back to CHATDEV_PATH env var, then default.
        """
        self.chatdev_path = self._resolve_chatdev_path(custom_path)
        self.workspace_path = self.chatdev_path / "WareHouse"
        self.config_path = self.chatdev_path / "CompanyConfig"

    def _resolve_chatdev_path(self, custom_path: Path | None) -> Path:
        """Resolve ChatDev installation path from multiple sources."""
        # Priority: custom_path > env var > default
        if custom_path:
            return Path(custom_path)

        env_path = os.getenv("CHATDEV_PATH")
        if env_path:
            return Path(env_path)

        return DEFAULT_CHATDEV_PATH

    def verify_installation(self) -> bool:
        """Verify ChatDev2 fork is properly installed."""
        required_paths = [
            self.chatdev_path / "run.py",
            self.chatdev_path / "chatdev",
            self.workspace_path,
            self.config_path,
        ]

        return all(p.exists() for p in required_paths)

    def get_fork_info(self) -> dict:
        """Get information about the ChatDev2 fork."""
        return {
            "repository": CHATDEV2_REPO,
            "branch": CHATDEV2_BRANCH,
            "latest_verified_commit": CHATDEV2_COMMIT,
            "installation_path": str(self.chatdev_path),
            "workspace_path": str(self.workspace_path),
            "verified": self.verify_installation(),
        }

    def get_run_command(self, task: str, model: str = "qwen2.5-coder:7b") -> list[str]:
        """Generate run command for ChatDev2.

        Args:
            task: Task description for ChatDev
            model: Ollama model to use (default: qwen2.5-coder:7b)

        Returns:
            List of command arguments
        """
        return [
            "python",
            str(self.chatdev_path / "run.py"),
            "--task",
            task,
            "--name",
            f"nusyq_task_{task[:30].replace(' ', '_')}",
            "--model",
            model,
            "--path",
            str(self.workspace_path),
        ]


def get_chatdev2_config(custom_path: Path | None = None) -> ChatDev2Config:
    """Get ChatDev2 configuration instance.

    Args:
        custom_path: Optional custom path to ChatDev installation

    Returns:
        ChatDev2Config instance
    """
    return ChatDev2Config(custom_path)


def verify_chatdev2_fork() -> bool:
    """Quick verification that ChatDev2 fork is available.

    Returns:
        True if ChatDev2 is properly installed, False otherwise
    """
    config = get_chatdev2_config()
    return config.verify_installation()


# Example usage
if __name__ == "__main__":
    config = get_chatdev2_config()
    info = config.get_fork_info()

    logger.info("ChatDev2 Fork Information:")
    logger.info("=" * 60)
    for key, value in info.items():
        logger.info(f"{key}: {value}")

    if info["verified"]:
        logger.info("\n✅ ChatDev2 installation verified!")

        # Example command
        cmd = config.get_run_command("Create a simple calculator")
        logger.info(f"\nExample command:\n{' '.join(cmd)}")
    else:
        logger.error("\n❌ ChatDev2 installation not found!")
        logger.info(f"Expected path: {config.chatdev_path}")
        logger.info(f"Repository: {CHATDEV2_REPO}")
