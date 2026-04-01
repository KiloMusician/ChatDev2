"""VS Code Integration - Extension Commands.

Provides command palette integration for NuSyQ operations.
Commands can be invoked from VS Code command palette or keybindings.

Usage:
  - python -m src.vscode_integration.extension_commands <command>
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class VSCodeCommand:
    """Represents a VS Code command."""

    id: str
    title: str
    category: str
    description: str


class VSCodeIntegration:
    """VS Code integration for NuSyQ."""

    def __init__(self, workspace_root: Path | None = None):
        """Initialize VS Code integration."""
        self.workspace_root = workspace_root or Path.cwd()
        self.hub_root = self._find_hub_root()

    def _find_hub_root(self) -> Path:
        """Find NuSyQ-Hub root directory."""
        current = self.workspace_root
        while current != current.parent:
            if (current / "scripts" / "start_nusyq.py").exists():
                return current
            current = current.parent
        return self.workspace_root

    def get_commands(self) -> list[VSCodeCommand]:
        """Get all available VS Code commands."""
        return [
            VSCodeCommand(
                id="nusyq.task.list",
                title="NuSyQ: List Tasks",
                category="NuSyQ",
                description="Show all open tasks",
            ),
            VSCodeCommand(
                id="nusyq.task.add",
                title="NuSyQ: Add Task",
                category="NuSyQ",
                description="Create a new task",
            ),
            VSCodeCommand(
                id="nusyq.snapshot",
                title="NuSyQ: System Snapshot",
                category="NuSyQ",
                description="Generate system state snapshot",
            ),
            VSCodeCommand(
                id="nusyq.test",
                title="NuSyQ: Run Tests",
                category="NuSyQ",
                description="Run test suite",
            ),
            VSCodeCommand(
                id="nusyq.analyze",
                title="NuSyQ: Analyze Current File",
                category="NuSyQ",
                description="Analyze current file with AI",
            ),
            VSCodeCommand(
                id="nusyq.quest.list",
                title="NuSyQ: List Active Quests",
                category="NuSyQ",
                description="Show active guild quests",
            ),
            VSCodeCommand(
                id="nusyq.suggest",
                title="NuSyQ: Get Suggestions",
                category="NuSyQ",
                description="Get system improvement suggestions",
            ),
            VSCodeCommand(
                id="nusyq.heal",
                title="NuSyQ: Heal System",
                category="NuSyQ",
                description="Run system healing and diagnostics",
            ),
        ]

    def execute_command(self, command_id: str, args: dict | None = None) -> int:
        """Execute a VS Code command."""
        args = args or {}

        # Map command IDs to start_nusyq.py actions
        command_map = {
            "nusyq.task.list": ("task", ["list"]),
            "nusyq.task.add": ("task", ["add", args.get("title", "New Task")]),
            "nusyq.snapshot": ("snapshot", []),
            "nusyq.test": ("test", []),
            "nusyq.analyze": ("analyze", [args.get("file", "${file}")]),
            "nusyq.quest.list": ("guild_available", []),
            "nusyq.suggest": ("suggest", []),
            "nusyq.heal": ("heal", []),
        }

        if command_id not in command_map:
            logger.info(f"Unknown command: {command_id}")
            return 1

        action, action_args = command_map[command_id]

        # Execute start_nusyq.py with the action
        cmd = [
            sys.executable,
            str(self.hub_root / "scripts" / "start_nusyq.py"),
            action,
            *action_args,
        ]

        try:
            result = subprocess.run(cmd, cwd=self.hub_root, capture_output=False)
            return result.returncode
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return 1

    def generate_keybindings(self) -> dict:
        """Generate VS Code keybindings configuration."""
        return {
            "keybindings": [
                {
                    "key": "ctrl+shift+t",
                    "command": "nusyq.task.list",
                    "when": "editorFocus",
                },
                {
                    "key": "ctrl+shift+s",
                    "command": "nusyq.snapshot",
                    "when": "editorFocus",
                },
                {
                    "key": "ctrl+shift+l",
                    "command": "nusyq.quest.list",
                    "when": "editorFocus",
                },
            ]
        }

    def generate_package_json_contrib(self) -> dict:
        """Generate package.json contribution point configuration."""
        return {
            "commands": [
                {
                    "command": cmd.id,
                    "title": f"{cmd.category}: {cmd.title}",
                    "description": cmd.description,
                }
                for cmd in self.get_commands()
            ]
        }

    def export_config(self, output_path: Path | None = None) -> dict:
        """Export configuration for VS Code extension."""
        config = {
            "extension": {
                "name": "nusyq-commands",
                "displayName": "NuSyQ Commands",
                "description": "Quick access to NuSyQ development commands",
                "version": "1.0.0",
                "engines": {"vscode": "^1.60.0"},
            },
            "contributes": self.generate_package_json_contrib(),
            "keybindings": self.generate_keybindings()["keybindings"],
        }

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(config, indent=2))

        return config


def main() -> int:
    """Main entry point for command-line usage."""
    if len(sys.argv) < 2:
        logger.info(
            "Usage: python -m src.vscode_integration.extension_commands <command> [args...]"
        )
        logger.info("\nAvailable commands:")
        vscode = VSCodeIntegration()
        for cmd in vscode.get_commands():
            logger.info(f"  {cmd.id:30} - {cmd.description}")
        return 1

    command_id = sys.argv[1]
    args_dict = {}

    # Parse simple args
    for arg in sys.argv[2:]:
        if "=" in arg:
            key, val = arg.split("=", 1)
            args_dict[key] = val

    vscode = VSCodeIntegration()

    # Handle special commands
    if command_id == "export":
        output = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        config = vscode.export_config(output)
        logger.info(json.dumps(config, indent=2))
        if output:
            logger.info(f"\n✅ Configuration exported to {output}")
        return 0

    # Execute normal command
    return vscode.execute_command(command_id, args_dict)


if __name__ == "__main__":
    sys.exit(main())
