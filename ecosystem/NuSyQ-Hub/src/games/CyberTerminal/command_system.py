"""Command System for CyberTerminal.

Handles parsing, validation, and execution of terminal commands.
Implements a subset of Linux commands for the educational game.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.games.CyberTerminal.virtual_filesystem import VirtualFilesystem


class CommandStatus(Enum):
    """Command execution status."""

    SUCCESS = "success"
    ERROR = "error"
    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"
    INVALID_ARGS = "invalid_args"


@dataclass
class CommandResult:
    """Result of a command execution."""

    status: CommandStatus
    output: str
    error: str = ""
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


class CommandSystem:
    """Central command parsing and execution system."""

    def __init__(self, filesystem: "VirtualFilesystem"):
        """Initialize command system with filesystem reference."""
        self.filesystem = filesystem
        self.commands: dict[str, Callable] = {}
        self.command_history: list[str] = []
        self.max_history = 100

        # Register built-in commands
        self._register_builtin_commands()

    def _register_builtin_commands(self) -> None:
        """Register all built-in terminal commands."""
        self.register("ls", self._cmd_ls)
        self.register("cd", self._cmd_cd)
        self.register("pwd", self._cmd_pwd)
        self.register("cat", self._cmd_cat)
        self.register("echo", self._cmd_echo)
        self.register("mkdir", self._cmd_mkdir)
        self.register("touch", self._cmd_touch)
        self.register("chmod", self._cmd_chmod)
        self.register("clear", self._cmd_clear)
        self.register("help", self._cmd_help)
        self.register("man", self._cmd_man)
        self.register("whoami", self._cmd_whoami)
        self.register("pwd", self._cmd_pwd)
        self.register("history", self._cmd_history)

    def register(self, command: str, handler: Callable[[list[str]], CommandResult]) -> None:
        """Register a new command handler."""
        self.commands[command.lower()] = handler

    def execute(self, input_str: str) -> CommandResult:
        """Parse and execute a command."""
        input_str = input_str.strip()

        if not input_str:
            return CommandResult(CommandStatus.SUCCESS, "", "")

        # Add to history
        if len(self.command_history) >= self.max_history:
            self.command_history.pop(0)
        self.command_history.append(input_str)

        # Parse command
        parts = input_str.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        # Check if command exists
        if cmd not in self.commands:
            return CommandResult(CommandStatus.NOT_FOUND, "", f"command not found: {cmd}")

        # Execute command
        try:
            result = self.commands[cmd](args)
            if not isinstance(result, CommandResult):
                return CommandResult(CommandStatus.ERROR, "", "Invalid handler")
            return result
        except (OSError, ValueError, KeyError) as e:
            return CommandResult(CommandStatus.ERROR, "", f"error: {e!s}")

    # Built-in command implementations

    def _cmd_ls(self, args: list[str]) -> CommandResult:
        """List directory contents: ls [path]."""
        show_hidden = "-a" in args or "--all" in args
        show_long = "-l" in args or "--long" in args

        path = None
        for arg in args:
            if not arg.startswith("-"):
                path = arg
                break

        contents = self.filesystem.list_directory(path, show_hidden)

        if show_long:
            output = "\n".join(f"  {item}" for item in contents)
        else:
            output = "  ".join(contents) if contents else "  (empty)"

        return CommandResult(CommandStatus.SUCCESS, output)

    def _cmd_cd(self, args: list[str]) -> CommandResult:
        """Change directory: cd [path]."""
        path = "/home" if not args else args[0]  # no args → home directory

        if self.filesystem.navigate_to(path):
            return CommandResult(CommandStatus.SUCCESS, "")
        else:
            return CommandResult(CommandStatus.NOT_FOUND, "", f"directory not found: {path}")

    def _cmd_pwd(self, _args: list[str]) -> CommandResult:
        """Print working directory: pwd."""
        return CommandResult(CommandStatus.SUCCESS, self.filesystem.get_current_path())

    def _cmd_cat(self, args: list[str]) -> CommandResult:
        """Concatenate and display file: cat [file]."""
        if not args:
            return CommandResult(CommandStatus.INVALID_ARGS, "", "cat: missing filename")

        filename = args[0]
        file = self.filesystem.get_file(filename)

        if not file:
            return CommandResult(
                CommandStatus.NOT_FOUND, "", f"cat: {filename}: No such file or directory"
            )

        return CommandResult(CommandStatus.SUCCESS, file.content)

    def _cmd_echo(self, args: list[str]) -> CommandResult:
        """Echo text: echo [text]."""
        output = " ".join(args) if args else ""
        return CommandResult(CommandStatus.SUCCESS, output)

    def _cmd_mkdir(self, args: list[str]) -> CommandResult:
        """Make directory: mkdir [dirname]."""
        if not args:
            return CommandResult(CommandStatus.INVALID_ARGS, "", "mkdir: missing directory name")

        dirname = args[0]
        from src.games.CyberTerminal.virtual_filesystem import VirtualDirectory

        new_dir = VirtualDirectory(name=dirname, owner=self.filesystem.current_user)
        self.filesystem.current_directory.add_directory(new_dir)

        return CommandResult(CommandStatus.SUCCESS, "")

    def _cmd_touch(self, args: list[str]) -> CommandResult:
        """Create empty file: touch [filename]."""
        if not args:
            return CommandResult(CommandStatus.INVALID_ARGS, "", "touch: missing filename")

        filename = args[0]
        if self.filesystem.create_file(filename, ""):
            return CommandResult(CommandStatus.SUCCESS, "")
        else:
            return CommandResult(
                CommandStatus.ERROR, "", f"touch: cannot create {filename}: File exists"
            )

    def _cmd_chmod(self, args: list[str]) -> CommandResult:
        """Change permissions: chmod [octal] [file]."""
        if len(args) < 2:
            return CommandResult(CommandStatus.INVALID_ARGS, "", "chmod: missing arguments")

        # For now, simplified implementation
        return CommandResult(CommandStatus.SUCCESS, "")

    def _cmd_clear(self, _args: list[str]) -> CommandResult:
        """Clear screen."""
        return CommandResult(CommandStatus.SUCCESS, "\n" * 50)

    def _cmd_help(self, _args: list[str]) -> CommandResult:
        """Show available commands: help."""
        commands = sorted(self.commands.keys())
        output = "Available commands:\n  " + "\n  ".join(commands)
        return CommandResult(CommandStatus.SUCCESS, output)

    def _cmd_man(self, args: list[str]) -> CommandResult:
        """Show manual page: man [command]."""
        if not args:
            return CommandResult(CommandStatus.INVALID_ARGS, "", "man: missing command")

        cmd = args[0].lower()
        manpages = {
            "ls": "List directory contents\nUsage: ls [options] [path]",
            "cd": "Change directory\nUsage: cd [path]",
            "pwd": "Print working directory\nUsage: pwd",
            "cat": "Display file contents\nUsage: cat [file]",
            "echo": "Print text\nUsage: echo [text]",
        }

        if cmd in manpages:
            return CommandResult(CommandStatus.SUCCESS, manpages[cmd])
        else:
            return CommandResult(CommandStatus.NOT_FOUND, "", f"No manual entry for {cmd}")

    def _cmd_whoami(self, _args: list[str]) -> CommandResult:
        """Show current user: whoami."""
        return CommandResult(CommandStatus.SUCCESS, self.filesystem.current_user)

    def _cmd_history(self, _args: list[str]) -> CommandResult:
        """Show command history: history."""
        output = "\n".join(f"  {i + 1}  {cmd}" for i, cmd in enumerate(self.command_history[-20:]))
        return CommandResult(CommandStatus.SUCCESS, output)
