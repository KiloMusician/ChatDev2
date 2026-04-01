"""Session Checkpoint & Restore System.

====================================

Purpose:
    Automatic workflow state persistence and recovery for AI agent sessions.
    Prevents loss of progress due to crashes, interruptions, or softlocks.

Features:
    - Automatic checkpoint creation at key workflow points
    - State serialization (TODO list, progress, context)
    - Graceful restoration from last checkpoint
    - Session history tracking
    - Cleanup of old checkpoints

Usage:
    # Save checkpoint
    checkpoint = SessionCheckpoint()
    checkpoint.save(state_data, description="Completed test suite")

    # Restore from latest
    state = checkpoint.restore()

    # List available checkpoints
    checkpoints = checkpoint.list_checkpoints()
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CheckpointMetadata:
    """Metadata for a saved checkpoint."""

    checkpoint_id: str
    timestamp: str
    description: str
    session_id: str
    agent_name: str
    file_path: str
    size_bytes: int


class SessionCheckpoint:
    """Manages session state checkpoints for workflow recovery.

    Automatically saves and restores agent workflow state including:
    - TODO list progress
    - File modifications
    - Terminal command history
    - Active tasks
    - Session context
    """

    def __init__(
        self,
        checkpoint_dir: Path | None = None,
        agent_name: str = "copilot",
        max_checkpoints: int = 10,
    ) -> None:
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoint storage
            agent_name: Name of the agent (for multi-agent scenarios)
            max_checkpoints: Maximum number of checkpoints to retain
        """
        self.checkpoint_dir = checkpoint_dir or Path.cwd() / ".checkpoints"
        self.agent_name = agent_name
        self.max_checkpoints = max_checkpoints
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        logger.info("📌 SessionCheckpoint initialized")
        logger.info(f"   Directory: {self.checkpoint_dir}")
        logger.info(f"   Session: {self.session_id}")

    def _generate_checkpoint_id(self) -> str:
        """Generate unique checkpoint identifier."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"{self.agent_name}_{self.session_id}_{timestamp}"

    def save(self, state: dict[str, Any], description: str = "Auto-checkpoint") -> str:
        """Save current session state to checkpoint.

        Args:
            state: Dictionary containing session state
            description: Human-readable checkpoint description

        Returns:
            Checkpoint ID

        State dictionary should contain:
            - todo_list: Current TODO items and status
            - modified_files: List of files changed
            - terminal_history: Commands executed
            - active_tasks: Running background tasks
            - context: Additional session context
        """
        checkpoint_id = self._generate_checkpoint_id()
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        # Build full checkpoint data
        checkpoint_data = {
            "metadata": {
                "checkpoint_id": checkpoint_id,
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "session_id": self.session_id,
                "agent_name": self.agent_name,
            },
            "state": state,
        }

        # Save to file
        try:
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

            file_size = checkpoint_path.stat().st_size
            logger.info(f"✅ Checkpoint saved: {checkpoint_id}")
            logger.info(f"   Description: {description}")
            logger.info(f"   Size: {file_size:,} bytes")
            logger.info(f"   Path: {checkpoint_path}")

            # Cleanup old checkpoints
            self._cleanup_old_checkpoints()

            return checkpoint_id

        except Exception as e:
            logger.error(f"❌ Failed to save checkpoint: {e}")
            raise

    def restore(self, checkpoint_id: str | None = None) -> dict[str, Any] | None:
        """Restore session state from checkpoint.

        Args:
            checkpoint_id: Specific checkpoint to restore (latest if None)

        Returns:
            Restored state dictionary or None if no checkpoint found
        """
        if checkpoint_id:
            checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
            if not checkpoint_path.exists():
                logger.error(f"❌ Checkpoint not found: {checkpoint_id}")
                return None
        else:
            # Find latest checkpoint for this session
            checkpoints = self.list_checkpoints()
            if not checkpoints:
                logger.warning("⚠️  No checkpoints found to restore")
                return None
            checkpoint_id = checkpoints[0].checkpoint_id
            checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        try:
            with open(checkpoint_path, encoding="utf-8") as f:
                checkpoint_data = json.load(f)

            metadata = checkpoint_data["metadata"]
            state: dict[str, Any] = checkpoint_data["state"]

            logger.info(f"✅ Checkpoint restored: {checkpoint_id}")
            logger.info(f"   Created: {metadata['timestamp']}")
            logger.info(f"   Description: {metadata['description']}")

            return state

        except Exception as e:
            logger.error(f"❌ Failed to restore checkpoint: {e}")
            return None

    def list_checkpoints(self) -> list[CheckpointMetadata]:
        """List all available checkpoints.

        Returns:
            List of checkpoint metadata, sorted by timestamp (newest first)
        """
        checkpoints = []

        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, encoding="utf-8") as f:
                    data = json.load(f)

                metadata = data["metadata"]
                checkpoints.append(
                    CheckpointMetadata(
                        checkpoint_id=metadata["checkpoint_id"],
                        timestamp=metadata["timestamp"],
                        description=metadata["description"],
                        session_id=metadata["session_id"],
                        agent_name=metadata["agent_name"],
                        file_path=str(checkpoint_file),
                        size_bytes=checkpoint_file.stat().st_size,
                    )
                )
            except Exception as e:
                logger.warning(f"⚠️  Skipping invalid checkpoint: {checkpoint_file} ({e})")

        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x.timestamp, reverse=True)
        return checkpoints

    def _cleanup_old_checkpoints(self) -> None:
        """Remove old checkpoints beyond max_checkpoints limit."""
        checkpoints = self.list_checkpoints()

        if len(checkpoints) > self.max_checkpoints:
            to_delete = checkpoints[self.max_checkpoints :]
            logger.info(f"🧹 Cleaning up {len(to_delete)} old checkpoints")

            for checkpoint in to_delete:
                try:
                    Path(checkpoint.file_path).unlink()
                    logger.debug(f"   Deleted: {checkpoint.checkpoint_id}")
                except Exception as e:
                    logger.warning(f"   Failed to delete {checkpoint.checkpoint_id}: {e}")

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete specific checkpoint.

        Args:
            checkpoint_id: Checkpoint to delete

        Returns:
            True if deleted, False otherwise
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_path.exists():
            logger.warning(f"⚠️  Checkpoint not found: {checkpoint_id}")
            return False

        try:
            checkpoint_path.unlink()
            logger.info(f"🗑️  Deleted checkpoint: {checkpoint_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete checkpoint: {e}")
            return False

    def clear_all(self) -> None:
        """Delete all checkpoints (use with caution)."""
        checkpoints = self.list_checkpoints()
        logger.warning(f"⚠️  Clearing {len(checkpoints)} checkpoints")

        for checkpoint in checkpoints:
            self.delete_checkpoint(checkpoint.checkpoint_id)


# Convenience function for quick checkpointing
def auto_checkpoint(
    state: dict[str, Any],
    description: str = "Auto-checkpoint",
    checkpoint_dir: Path | None = None,
) -> str:
    """Quick checkpoint creation without explicit manager.

    Args:
        state: Session state to save
        description: Checkpoint description
        checkpoint_dir: Custom checkpoint directory

    Returns:
        Checkpoint ID
    """
    manager = SessionCheckpoint(checkpoint_dir=checkpoint_dir)
    return manager.save(state, description)


def restore_latest(checkpoint_dir: Path | None = None) -> dict[str, Any] | None:
    """Quick restore from latest checkpoint.

    Args:
        checkpoint_dir: Custom checkpoint directory

    Returns:
        Restored state or None
    """
    manager = SessionCheckpoint(checkpoint_dir=checkpoint_dir)
    return manager.restore()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create checkpoint manager
    checkpoint = SessionCheckpoint()

    # Example state
    example_state = {
        "todo_list": [
            {"id": 1, "title": "Fix type errors", "status": "completed"},
            {"id": 2, "title": "Run tests", "status": "in-progress"},
        ],
        "modified_files": ["src/utils/async_task_wrapper.py"],
        "terminal_history": ["pytest tests/", "python scripts/lint_check.py"],
        "context": {"last_action": "running tests", "errors_found": 0},
    }

    # Save checkpoint
    checkpoint_id = checkpoint.save(example_state, "After fixing type errors")

    # List checkpoints
    logger.info("\n📋 Available checkpoints:")
    for cp in checkpoint.list_checkpoints():
        logger.info(f"   {cp.checkpoint_id}: {cp.description}")

    # Restore from latest
    restored_state = checkpoint.restore()
    if restored_state:
        logger.info("\n✅ Restored state:")
        logger.info(f"   TODO items: {len(restored_state['todo_list'])}")
        logger.info(f"   Modified files: {restored_state['modified_files']}")
