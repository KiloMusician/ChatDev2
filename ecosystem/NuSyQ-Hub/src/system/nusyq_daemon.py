#!/usr/bin/env python3
"""ΞNuSyQ Conversational CLI Daemon.

================================
Provides a "system voice" that users can interact with directly.

This daemon allows users to say:
    "ΞNuSyQ, build a game"
    "ΞNuSyQ, fix the errors in src/main.py"
    "ΞNuSyQ, what's the system status?"

Instead of having to know:
    python src/main.py --mode=orchestration --task="build a game"

Usage:
    python -m src.system.nusyq_daemon       # Start interactive REPL
    python -m src.system.nusyq_daemon cmd "build a game"  # One-shot command
"""

import argparse
import contextlib
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# readline is not available on Windows by default
try:
    import readline  # Enables arrow keys, history on Unix
except ImportError:
    readline = None  # type: ignore[assignment]

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))


class NuSyQDaemon:
    """Conversational interface to the ΞNuSyQ system.

    This daemon acts as a unified entry point for all system capabilities:
    - Build/develop projects
    - Fix errors
    - Check system status
    - Coordinate agents
    - Manage lifecycle
    """

    def __init__(self):
        """Initialize NuSyQDaemon."""
        self.repo_root = REPO_ROOT
        self.history_file = self.repo_root / "data" / "nusyq_daemon_history.txt"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # Load command history (if readline available)
        if readline and self.history_file.exists():
            try:
                readline.read_history_file(str(self.history_file))
                readline.set_history_length(1000)
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)

    def save_history(self) -> None:
        """Save command history to disk."""
        if readline:
            with contextlib.suppress(Exception):  # Ignore history save errors
                readline.write_history_file(str(self.history_file))

    def parse_command(self, user_input: str) -> tuple[str, list[str]]:
        """Parse user input into command and arguments.

        Examples:
            "build a game" → ("build", ["a", "game"])
            "status" → ("status", [])
            "fix errors in src/main.py" → ("fix", ["errors", "in", "src/main.py"])
        """
        user_input = user_input.strip()

        # Remove common prefixes
        for prefix in ["nusyq,", "ξnusyq,", "system,"]:
            if user_input.lower().startswith(prefix):
                user_input = user_input[len(prefix) :].strip()

        # Split into words
        parts = user_input.split()
        if not parts:
            return ("", [])

        command = parts[0].lower()
        args = parts[1:]

        return (command, args)

    def execute_command(self, command: str, args: list[str]) -> bool:
        """Execute a command.

        Returns:
            True if command succeeded, False otherwise
        """
        full_input = f"{command} {' '.join(args)}".strip()

        # =====================================================================
        # LIFECYCLE COMMANDS
        # =====================================================================
        if command in ["start", "startup", "boot"]:
            logger.info("🚀 Starting ΞNuSyQ ecosystem...")
            from src.system.lifecycle_manager import LifecycleManager

            manager = LifecycleManager(self.repo_root)
            return manager.start_all_services()

        elif command in ["stop", "shutdown", "halt"]:
            logger.info("🛑 Stopping ΞNuSyQ ecosystem...")
            from src.system.lifecycle_manager import LifecycleManager

            manager = LifecycleManager(self.repo_root)
            return manager.stop_all_services()

        elif command in ["restart", "reboot"]:
            logger.info("🔄 Restarting ΞNuSyQ ecosystem...")
            from src.system.lifecycle_manager import LifecycleManager

            manager = LifecycleManager(self.repo_root)
            manager.stop_all_services()
            return manager.start_all_services()

        # =====================================================================
        # STATUS COMMANDS
        # =====================================================================
        elif command in ["status", "health", "check"]:
            logger.info("📊 Checking ΞNuSyQ system status...")
            from src.system.lifecycle_manager import LifecycleManager

            manager = LifecycleManager(self.repo_root)
            manager.print_status()
            return True

        elif command in ["terminals", "term"]:
            logger.info("🖥️  Checking terminal status...")
            from src.system.terminal_manager import TerminalManager

            tm = TerminalManager(self.repo_root)
            tm.print_status()
            return True

        # =====================================================================
        # BUILD COMMANDS
        # =====================================================================
        elif command in ["build", "create", "develop", "make"]:
            task_description = " ".join(args)
            if not task_description:
                logger.error("❌ Usage: build <what to build>")
                logger.info("   Example: build a snake game")
                return False

            logger.info(f"🛠️  Building: {task_description}")
            logger.info("   Routing to orchestration system...")

            # Route to orchestrator
            from src.orchestration.multi_ai_orchestrator import (
                MultiAIOrchestrator, TaskPriority)

            orchestrator = MultiAIOrchestrator()
            result = orchestrator.orchestrate_task(
                task_type="general",
                content=task_description,
                context={"mode": "daemon", "source": "nusyq_cli"},
                priority=TaskPriority.NORMAL,
            )
            logger.info(f"✅ Task submitted: {result}")
            return True

        # =====================================================================
        # FIX/DEBUG COMMANDS
        # =====================================================================
        elif command in ["fix", "debug", "repair", "heal"]:
            target = " ".join(args) if args else "system"
            logger.info(f"🔧 Fixing: {target}")

            # Route to error resolution
            from src.healing.comprehensive_error_resolver import \
                ComprehensiveErrorResolver

            resolver = ComprehensiveErrorResolver(self.repo_root)
            resolver.resolve_all_errors()
            return True

        # =====================================================================
        # HELP COMMANDS
        # =====================================================================
        elif command in ["help", "?", "commands"]:
            self.print_help()
            return True

        elif command in ["orient", "brief"]:
            logger.info("📖 Loading system brief...")
            from src.system.agent_orientation import orient_agent

            orient_agent(silent=False)
            return True

        # =====================================================================
        # EXIT COMMANDS
        # =====================================================================
        elif command in ["exit", "quit", "bye", "goodbye"]:
            logger.info("👋 Goodbye!")
            return False

        # =====================================================================
        # UNKNOWN COMMAND
        # =====================================================================
        else:
            logger.info(f"❓ Unknown command: '{command}'")
            logger.info("   Type 'help' for available commands")
            logger.info(f"   Or try: build {full_input}")
            return True

    def print_help(self) -> None:
        """Print help message."""
        help_text = """
╔════════════════════════════════════════════════════════════════════════╗
║                    ΞNuSyQ CONVERSATIONAL CLI                           ║
╚════════════════════════════════════════════════════════════════════════╝

Available Commands:

🚀 LIFECYCLE
  start, startup, boot       Start all ecosystem services
  stop, shutdown, halt       Stop all services
  restart, reboot            Restart all services

📊 STATUS
  status, health, check      Show system status
  terminals, term            Show terminal status
  orient, brief              Display system brief

🛠️  BUILD
  build <description>        Build a project/game/app
  create <description>       Alias for 'build'
  develop <description>      Alias for 'build'

  Examples:
    build a snake game
    create a TODO app with FastAPI backend
    develop a poker simulator

🔧 FIX/DEBUG
  fix [target]              Fix errors in target (or entire system)
  debug [target]            Alias for 'fix'
  heal [target]             Alias for 'fix'

  Examples:
    fix src/main.py
    fix
    heal errors

INFO HELP
  help, ?, commands         Show this help message

🚪 EXIT
  exit, quit, bye           Exit the daemon

╔════════════════════════════════════════════════════════════════════════╗
║  TIP: You can omit "ΞNuSyQ," prefix                                    ║
║       "build a game" works the same as "ΞNuSyQ, build a game"          ║
╚════════════════════════════════════════════════════════════════════════╝
""".strip()

        logger.info(help_text)

    def repl(self) -> None:
        """Run interactive REPL."""
        logger.info("\n" + "═" * 60)
        logger.info("ΞNuSyQ CONVERSATIONAL CLI")
        logger.info("Type 'help' for commands, 'exit' to quit")
        logger.info("═" * 60 + "\n")

        while True:
            try:
                # Get user input
                user_input = input("ΞNuSyQ> ").strip()

                if not user_input:
                    continue

                # Parse and execute
                command, args = self.parse_command(user_input)
                if not command:
                    continue

                # Execute (returns False to exit)
                if not self.execute_command(command, args):
                    break

            except KeyboardInterrupt:
                logger.info("\n👋 Interrupted. Type 'exit' to quit.")
                continue
            except EOFError:
                logger.info("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                import traceback

                traceback.print_exc()

        # Save history on exit
        self.save_history()

    def one_shot(self, command_string: str) -> int:
        """Execute a single command and exit."""
        command, args = self.parse_command(command_string)
        if not command:
            logger.error("❌ No command provided")
            return 1

        success = self.execute_command(command, args)
        return 0 if success else 1


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="ΞNuSyQ Conversational CLI Daemon")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["repl", "cmd"],
        default="repl",
        help="Mode: repl (interactive) or cmd (one-shot)",
    )
    parser.add_argument(
        "command",
        nargs="*",
        help="Command to execute (for cmd mode)",
    )

    args = parser.parse_args()

    daemon = NuSyQDaemon()

    if args.mode == "repl":
        daemon.repl()
        return 0
    elif args.mode == "cmd":
        if not args.command:
            logger.error("❌ Usage: nusyq_daemon cmd <command>")
            return 1
        command_string = " ".join(args.command)
        return daemon.one_shot(command_string)

    return 1


if __name__ == "__main__":
    sys.exit(main())
