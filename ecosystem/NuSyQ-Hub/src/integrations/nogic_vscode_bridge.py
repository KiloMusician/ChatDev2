"""Nogic VS Code Extension Integration.

This module provides integration points for controlling Nogic from
Python code and quest systems. It includes:
- Task runners for common Nogic operations
- Webview message handlers
- Command routing
"""

import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import quote

logger = logging.getLogger(__name__)


def _command_uri(command_id: str) -> str:
    """Build a VS Code command URI."""
    return f"vscode://command/{quote(command_id, safe='.')}"


def _task_for_command(label: str, description: str, command_id: str) -> dict[str, Any]:
    """Create a shell task that dispatches a VS Code command URI."""
    return {
        "label": label,
        "description": description,
        "type": "shell",
        "command": "code",
        "args": ["--open-url", _command_uri(command_id)],
    }


class NogicVSCodeBridge:
    """Bridge between NuSyQ-Hub and Nogic VS Code extension.

    Handles communication patterns, command routing, and state management.
    """

    # Known Nogic commands in VS Code
    _COMMANDS: ClassVar[dict] = {
        "open": "nogic.openVisualizer",
        "add_to_board": "nogic.addToBoard",
        "create_board": "nogic.createBoard",
        "init": "nogic.cliInit",
        "sync": "nogic.cliSync",
        "watch": "nogic.cliWatch",
        "watch_stop": "nogic.cliWatchStop",
        "watch_toggle": "nogic.cliWatchToggle",
        "reindex": "nogic.cliReindex",
        "status": "nogic.cliStatus",
        "login": "nogic.cliLogin",
        "onboard": "nogic.cliOnboard",
    }

    def __init__(self):
        """Initialize the bridge."""
        self.command_history = []
        self.message_handlers: dict[str, Callable] = {}
        logger.info("✅ Nogic VS Code Bridge initialized")

    def get_command(self, operation: str) -> str | None:
        """Get the VS Code command ID for an operation.

        Args:
            operation: Operation name (e.g., 'open', 'create_board')

        Returns:
            VS Code command ID or None
        """
        return self._COMMANDS.get(operation)

    def register_message_handler(
        self, message_type: str, handler: Callable[[dict[str, Any]], Any]
    ) -> None:
        """Register a handler for Nogic webview messages.

        Args:
            message_type: Type of message to handle
            handler: Callback function
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type: {message_type}")

    def handle_message(self, message: dict[str, Any]) -> Any:
        """Handle a message from Nogic webview.

        Args:
            message: Message dictionary with 'type' and 'payload'

        Returns:
            Response to send back to webview
        """
        msg_type = message.get("type", "unknown")
        payload = message.get("payload", {})

        logger.debug(f"Handling message: {msg_type}")

        if msg_type in self.message_handlers:
            try:
                return self.message_handlers[msg_type](payload)
            except Exception as e:
                logger.error(f"Error handling message {msg_type}: {e}")
                return {"error": str(e)}
        else:
            logger.warning(f"No handler for message type: {msg_type}")
            return {"error": f"Unknown message type: {msg_type}"}

    def record_command(self, operation: str, args: dict | None = None) -> None:
        """Record a command for audit/replay purposes."""
        self.command_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "args": args or {},
            }
        )


class NogicTaskRunner:
    """Run Nogic operations as VS Code tasks.

    This enables task-based workflow integration (e.g., "Analyze Architecture").
    """

    def __init__(self, workspace_root: Path | None = None):
        """Initialize task runner."""
        self.workspace_root = workspace_root or Path.cwd()
        self.tasks_dir = self.workspace_root / ".vscode" / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Nogic Task Runner initialized at {self.tasks_dir}")

    def create_visualization_task(
        self,
        name: str = "Visualize Workspace with Nogic",
        description: str = "Open Nogic visualizer and index workspace",
    ) -> dict[str, Any]:
        """Create a task that opens Nogic visualizer.

        Args:
            name: Task name
            description: Task description

        Returns:
            Task definition
        """
        return {
            **_task_for_command(name, description, "nogic.openVisualizer"),
            "group": {
                "kind": "build",
                "isDefault": False,
            },
            "presentation": {
                "reveal": "silent",
            },
        }

    def create_reindex_task(
        self,
        name: str = "Reindex Workspace (Nogic)",
        description: str = "Reindex entire workspace in Nogic",
    ) -> dict[str, Any]:
        """Create a task that reindexes the workspace.

        Args:
            name: Task name
            description: Task description

        Returns:
            Task definition
        """
        return {
            **_task_for_command(name, description, "nogic.cliReindex"),
            "group": {
                "kind": "test",
                "isDefault": False,
            },
            "presentation": {
                "reveal": "always",
                "panel": "shared",
            },
            "problemMatcher": [],
        }

    def create_analysis_task(
        self,
        name: str = "Analyze Architecture (Nogic)",
        description: str = "Run architecture analysis with Nogic",
    ) -> dict[str, Any]:
        """Create a task that runs architecture analysis.

        Args:
            name: Task name
            description: Task description

        Returns:
            Task definition
        """
        return {
            "label": name,
            "description": description,
            "type": "shell",
            "command": "${workspaceFolder}/.venv/Scripts/python.exe",
            "args": [
                "-m",
                "src.integrations.nogic_quest_integration",
            ],
            "group": {
                "kind": "test",
                "isDefault": False,
            },
            "presentation": {
                "reveal": "always",
                "panel": "new",
            },
            "problemMatcher": [],
        }

    def create_watch_task(
        self,
        name: str = "Watch Nogic Changes",
        description: str = "Start Nogic watch mode for live updates",
    ) -> dict[str, Any]:
        """Create a task that starts Nogic watch mode.

        Args:
            name: Task name
            description: Task description

        Returns:
            Task definition
        """
        return {
            **_task_for_command(name, description, "nogic.cliWatchToggle"),
            "isBackground": True,
            "problemMatcher": {
                "pattern": {
                    "regexp": "^.*$",
                    "file": 1,
                    "location": 2,
                    "message": 3,
                },
                "background": {
                    "activeOnStart": True,
                    "beginsPattern": "^.*Watch mode started.*",
                    "endsPattern": "^.*Watch mode stopped.*",
                },
            },
        }


class NogicWebviewMessenger:
    """Handle bidirectional communication with Nogic webview.

    Enables Python ↔ React webview messaging for advanced integration.
    """

    def __init__(self):
        """Initialize messenger."""
        self.pending_messages = []
        logger.info("✅ Nogic Webview Messenger initialized")

    def send_message(
        self,
        message_type: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a message to Nogic webview.

        Args:
            message_type: Type of message
            payload: Message payload

        Returns:
            Message envelope
        """
        message = {
            "type": message_type,
            "payload": payload or {},
            "timestamp": datetime.now().isoformat(),
        }

        self.pending_messages.append(message)
        logger.debug(f"Queued message: {message_type}")

        return message

    def request_graph_update(self, file_path: str | None = None) -> dict[str, Any]:
        """Request Nogic to update the graph for a file.

        Args:
            file_path: Optional file path to focus

        Returns:
            Message envelope
        """
        return self.send_message(
            "refresh",
            {"filePath": file_path},
        )

    def request_source_code(self, node_id: str) -> dict[str, Any]:
        """Request source code for a node.

        Args:
            node_id: Node identifier

        Returns:
            Message envelope
        """
        return self.send_message(
            "getSourceCode",
            {"nodeId": node_id},
        )

    def add_nodes_to_board(self, board_id: str, node_ids: list) -> dict[str, Any]:
        """Add nodes to a board.

        Args:
            board_id: Board identifier
            node_ids: List of node IDs

        Returns:
            Message envelope
        """
        return self.send_message(
            "boardOperation",
            {
                "operation": "addNodes",
                "boardId": board_id,
                "nodeIds": node_ids,
            },
        )

    def flush_messages(self) -> list:
        """Get and clear pending messages.

        Returns:
            List of pending messages
        """
        messages = self.pending_messages[:]
        self.pending_messages.clear()
        logger.info(f"Flushed {len(messages)} messages")
        return messages


# ========== TASK DEFINITIONS FOR tasks.json ==========

NOGIC_TASKS = {
    "version": "2.0.0",
    "tasks": [
        {
            **_task_for_command(
                "🎨 Nogic: Open Visualizer",
                "Open Nogic code visualization panel",
                "nogic.openVisualizer",
            ),
            "group": {
                "kind": "build",
                "isDefault": False,
            },
            "presentation": {
                "reveal": "silent",
                "panel": "shared",
            },
        },
        {
            **_task_for_command(
                "🎨 Nogic: Reindex Workspace",
                "Reindex entire workspace for visualization",
                "nogic.cliReindex",
            ),
            "group": {
                "kind": "test",
            },
            "presentation": {
                "reveal": "always",
            },
        },
        {
            "label": "🎨 Nogic: Architecture Analysis",
            "description": "Run architecture analysis (Nogic + NuSyQ-Hub)",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/Scripts/python.exe",
            "args": [
                "-m",
                "src.integrations.nogic_quest_integration",
            ],
            "group": {
                "kind": "test",
            },
            "presentation": {
                "reveal": "always",
                "panel": "new",
            },
        },
        {
            **_task_for_command(
                "🎨 Nogic: Toggle Watch",
                "Start/stop watch mode for live visualization updates",
                "nogic.cliWatchToggle",
            ),
            "isBackground": True,
            "problemMatcher": {
                "pattern": {
                    "regexp": "^.*$",
                },
            },
        },
    ],
}


if __name__ == "__main__":
    # Demo output
    logging.basicConfig(level=logging.INFO)

    logger.info("🎨 Nogic VS Code Integration Demo")
    logger.info("=" * 60)

    bridge = NogicVSCodeBridge()
    runner = NogicTaskRunner()
    messenger = NogicWebviewMessenger()

    # Show available commands
    logger.info("\nAvailable Commands:")
    for op, cmd in bridge._COMMANDS.items():
        logger.info(f"  {op:20} → {cmd}")

    # Create sample tasks
    logger.info("\nSample Tasks:")
    viz_task = runner.create_visualization_task()
    logger.info(f"  ✓ {viz_task['label']}")

    reindex_task = runner.create_reindex_task()
    logger.info(f"  ✓ {reindex_task['label']}")

    analysis_task = runner.create_analysis_task()
    logger.info(f"  ✓ {analysis_task['label']}")

    # Demonstrate messaging
    logger.info("\nMessaging Examples:")
    msg1 = messenger.send_message("refresh", {"filePath": "src/main.py"})
    logger.info(f"  ✓ Sent: {msg1['type']}")

    msg2 = messenger.request_source_code("node-123")
    logger.info(f"  ✓ Sent: {msg2['type']}")

    pending = messenger.flush_messages()
    logger.info(f"\n  Pending messages: {len(pending)}")

    logger.info("\n✅ Integration demo complete!")
