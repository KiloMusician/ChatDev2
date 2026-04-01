#!/usr/bin/env python3
"""Terminal Integration Module - Actually Use the Terminals!

This module integrates our beautiful terminal setup with actual Python output,
routing prints, logs, and agent output to the correct themed terminals.
"""

import logging
import sys
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TextIO, cast

from src.utils import terminal_output

logger = logging.getLogger(__name__)


_TERMINAL_ENUM_BY_NAME = {member.value: member for member in terminal_output.TerminalType}


class TerminalRouter:
    """Routes output to appropriate VSCode terminal based on content."""

    def __init__(self, _root_dir: Path | None = None):
        """Initialize TerminalRouter with _root_dir."""
        self._router = terminal_output.get_router()
        self.root = self._router.root
        self.output_dir = self.root / "data" / "terminal_logs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        terminals = self._router.routing_config.get("terminals", {})
        terminal_ids = (
            terminals.keys()
            if isinstance(terminals, dict) and terminals
            else _TERMINAL_ENUM_BY_NAME
        )
        self.terminal_files = {
            terminal_name: self.output_dir / f"{terminal_name}.log"
            for terminal_name in terminal_ids
        }

    def route_message(self, message: str, default: str = "main") -> str:
        """Determine which terminal should receive this message."""
        message_lower = message.lower()
        routed: str | None = None

        # Prefer public/explicit API when present.
        route_by_content = cast(
            Callable[[str], str | None] | None,
            getattr(self._router, "route_by_content", None),
        )
        if callable(route_by_content):
            routed = route_by_content(message_lower)  # pylint: disable=not-callable
        else:
            # Backward-compat with src.utils.terminal_output.TerminalRouter,
            # where routing is implemented as a private helper.
            private_router = cast(
                Callable[[str], str | None] | None,
                getattr(self._router, "_route_by_content", None),
            )
            if callable(private_router):
                routed = private_router(message_lower)  # pylint: disable=not-callable

        return routed or default

    def write_to_terminal(
        self,
        message: str,
        terminal: str | None = None,
        level: str = "INFO",
        _metadata: dict[str, Any] | None = None,
        emit_stdout: bool = True,
    ) -> None:
        """Write message to appropriate terminal output file."""
        # Auto-route if terminal not specified
        if terminal is None:
            terminal = self.route_message(message)

        if terminal not in self.terminal_files:
            terminal = "main"

        enum_terminal = _TERMINAL_ENUM_BY_NAME.get(terminal)
        self._router.route(message, agent=enum_terminal, level=level)

        if emit_stdout:
            logger.info(f"[{terminal.upper()}] {message}")


class TerminalStreamWrapper:
    """Wraps stdout/stderr to route to terminals."""

    def __init__(
        self, router: TerminalRouter, original_stream: TextIO, terminal: str, level: str = "INFO"
    ):
        """Initialize TerminalStreamWrapper with router, original_stream, terminal, ...."""
        self.router = router
        self.original_stream = original_stream
        self.terminal = terminal
        self.level = level
        self.buffer = ""
        self._in_write = False  # Prevent recursion

    def write(self, text: str) -> int:
        """Intercept write and route to terminal."""
        # Prevent recursion when write_to_terminal calls print
        if self._in_write:
            return self.original_stream.write(text)

        try:
            self._in_write = True

            # Write to original stream
            result = self.original_stream.write(text)

            # Buffer and route complete lines
            self.buffer += text
            if "\n" in self.buffer:
                lines = self.buffer.split("\n")
                self.buffer = lines[-1]  # Keep incomplete line in buffer

                for line in lines[:-1]:
                    if line.strip():  # Skip empty lines
                        self.router.write_to_terminal(
                            message=line,
                            terminal=self.terminal,
                            level=self.level,
                            emit_stdout=False,
                        )

            return result
        finally:
            self._in_write = False

    def flush(self) -> None:
        """Flush buffer and original stream."""
        if not self._in_write and self.buffer.strip():
            try:
                self._in_write = True
                self.router.write_to_terminal(
                    message=self.buffer,
                    terminal=self.terminal,
                    level=self.level,
                    emit_stdout=False,
                )
                self.buffer = ""
            finally:
                self._in_write = False
        self.original_stream.flush()


class TerminalLogHandler(logging.Handler):
    """Logging handler that routes to terminals."""

    def __init__(self, router: TerminalRouter):
        """Initialize TerminalLogHandler with router."""
        super().__init__()
        self.router = router

    def emit(self, record: logging.LogRecord) -> None:
        """Route log record to appropriate terminal."""
        try:
            message = self.format(record)
            level = record.levelname

            # Route errors to error terminal
            terminal = (
                "errors" if record.levelno >= logging.ERROR else self.router.route_message(message)
            )

            self.router.write_to_terminal(
                message=message,
                terminal=terminal,
                level=level,
                metadata={
                    "logger": record.name,
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                },
                emit_stdout=False,
            )
        except Exception:
            self.handleError(record)


# Global router instance
_router: TerminalRouter | None = None


def get_router() -> TerminalRouter:
    """Get or create global terminal router."""
    global _router
    if _router is None:
        _router = TerminalRouter()
    return _router


@contextmanager
def route_agent_output(agent_name: str):
    """Context manager to route agent output to its terminal."""
    router = get_router()
    terminal = agent_name.lower()

    # Redirect stdout/stderr to terminal
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    sys.stdout = TerminalStreamWrapper(router, original_stdout, terminal, "INFO")
    sys.stderr = TerminalStreamWrapper(router, original_stderr, terminal, "ERROR")

    try:
        router.write_to_terminal(
            message=f"=== {agent_name} Session Started ===",
            terminal=terminal,
            level="INFO",
        )
        yield router
    finally:
        router.write_to_terminal(
            message=f"=== {agent_name} Session Ended ===",
            terminal=terminal,
            level="INFO",
        )
        # Restore original streams
        sys.stdout = original_stdout
        sys.stderr = original_stderr


def route_to_terminal(terminal: str, message: str, level: str = "INFO", **metadata: Any) -> None:
    """Convenience function to route message to specific terminal."""
    router = get_router()
    router.write_to_terminal(message=message, terminal=terminal, level=level, metadata=metadata)


def setup_terminal_logging(logger: logging.Logger | None = None) -> None:
    """Set up logging to route through terminal router."""
    router = get_router()
    handler = TerminalLogHandler(router)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )

    if logger is None:
        # Configure root logger
        logging.basicConfig(level=logging.INFO, handlers=[handler])
    else:
        # Configure specific logger
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


# Convenience functions for each terminal
def to_claude(message: str, **metadata: Any) -> None:
    """Send message to Claude terminal."""
    route_to_terminal("claude", message, **metadata)


def to_copilot(message: str, **metadata: Any) -> None:
    """Send message to Copilot terminal."""
    route_to_terminal("copilot", message, **metadata)


def to_codex(message: str, **metadata: Any) -> None:
    """Send message to Codex terminal."""
    route_to_terminal("codex", message, **metadata)


def to_chatdev(message: str, **metadata: Any) -> None:
    """Send message to ChatDev terminal."""
    route_to_terminal("chatdev", message, **metadata)


def to_council(message: str, **metadata: Any) -> None:
    """Send message to AI Council terminal."""
    route_to_terminal("ai_council", message, **metadata)


def to_errors(message: str, **metadata: Any) -> None:
    """Send message to Errors terminal."""
    route_to_terminal("errors", message, level="ERROR", **metadata)


def to_tasks(message: str, **metadata: Any) -> None:
    """Send message to Tasks terminal."""
    route_to_terminal("tasks", message, **metadata)


def to_metrics(message: str, **metadata: Any) -> None:
    """Send message to Metrics terminal."""
    route_to_terminal("metrics", message, **metadata)


def to_suggestions(message: str, **metadata: Any) -> None:
    """Send message to Suggestions terminal."""
    route_to_terminal("suggestions", message, **metadata)


def to_zeta(message: str, **metadata: Any) -> None:
    """Send message to Zeta terminal."""
    route_to_terminal("zeta", message, **metadata)


# Example usage demonstration
def demo_terminal_routing():
    """Demonstrate terminal routing in action."""
    # Create logger for demo (must be defined before first use)
    demo_logger = logging.getLogger("terminal_demo")

    demo_logger.info("=" * 70)
    demo_logger.info("TERMINAL ROUTING DEMONSTRATION")
    demo_logger.info("=" * 70)

    # Set up terminal logging
    setup_terminal_logging()

    # Route different types of messages
    to_claude("Claude agent analyzing code structure...")
    to_copilot("Copilot suggesting completion for function...")
    to_codex("Codex transforming legacy code to modern patterns...")
    to_chatdev("ChatDev CEO: Let's implement the authentication system")
    to_council("AI Council: Voting on architectural decision...")
    to_errors("ERROR: Failed to connect to database")
    to_tasks("Processing task: Update configuration files")
    to_metrics("System health: CPU 45%, Memory 62%, Disk 78%")
    to_suggestions("💡 Suggestion: Consider refactoring duplicated code")
    to_zeta("Zeta: Autonomous cycle 42 completed successfully")

    # Test auto-routing with logger
    demo_logger.info("This is an agent coordination message")
    demo_logger.error("This is an error that should go to error terminal")

    # Test context manager for agent session
    with route_agent_output("Claude"):
        demo_logger.info("Claude is now working...")
        demo_logger.info("Analyzing file structure...")
        demo_logger.info("Found 3 optimization opportunities")

    with route_agent_output("Copilot"):
        demo_logger.info("Copilot providing suggestions...")
        demo_logger.info("Suggested 5 code completions")

    demo_logger.info("\n✅ Terminal routing demonstration complete!")
    demo_logger.info(f"Check {get_router().output_dir} for terminal output files")


if __name__ == "__main__":
    demo_terminal_routing()
