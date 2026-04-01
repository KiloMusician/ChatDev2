#!/usr/bin/env python3
"""
Terminal Depths Universal Launcher
Starts Terminal Depths from anywhere on the system.
Works from: cmd.exe, PowerShell, Git Bash, Docker, VSCode, TouchDesigner, Godot, etc.

Usage:
    python -m scripts.terminal_depths_launcher [--mode] [--agent] [--surface]
    
    Modes:
        cli         - Direct CLI game loop (default)
        web         - Web interface via http://localhost:7777
        repl        - Interactive Python REPL with game context
        agent       - Agent-delegated mode (via orchestrator)
        daemon      - Background daemon with API
        
    Surfaces:
        terminal    - Native terminal
        web         - Web browser
        vscode      - VS Code embedded terminal
        godot       - Godot in-game console
        touchdesigner - TouchDesigner operator context
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

# Add NuSyQ paths
NUSYQ_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(NUSYQ_ROOT))

from src.cyber_terminal.engine import CyberTerminal, build_world

logger = logging.getLogger(__name__)


@dataclass
class LauncherConfig:
    """Configuration for Terminal Depths launcher."""
    mode: Literal["cli", "web", "repl", "agent", "daemon"] = "cli"
    surface: Literal["terminal", "web", "vscode", "godot", "touchdesigner"] = "terminal"
    enable_colors: bool = True
    port: int = 7777
    agent_name: str | None = None
    context_tags: list[str] = None
    orchestrator_endpoint: str = "http://localhost:8000"

    def __post_init__(self):
        if self.context_tags is None:
            self.context_tags = []


class TerminalDepthsLauncher:
    """Universal launcher for Terminal Depths game."""

    def __init__(self, config: LauncherConfig):
        self.config = config
        self.game = CyberTerminal(
            world=build_world(),
            state_path=Path.home() / ".nusyq" / "terminal_depths.json",
            enable_colors=config.enable_colors and config.surface == "terminal"
        )
        self.session_id = self._generate_session_id()

    def _generate_session_id(self) -> str:
        import uuid
        return str(uuid.uuid4())[:8]

    async def launch_cli(self) -> None:
        """Launch classic CLI mode."""
        self._print_banner()
        self._print_help()

        while True:
            try:
                line = input(self.game.prompt())
            except (EOFError, KeyboardInterrupt):
                self._print(f"\n👋 Session {self.session_id} terminated.")
                break

            if line.strip() == "help":
                self._print_help()
                continue

            if line.strip() in ("quit", "exit"):
                self._print("👋 See you in the datastream.")
                break

            out = self.game.execute(line)
            notice = self.game._after_command(line.strip())

            if out:
                self._print(out)
            if notice:
                self._print(f"✨ {notice}")

    async def launch_web(self) -> None:
        """Launch web interface."""
        try:
            from aiohttp import web
        except ImportError:
            self._print("❌ aiohttp not installed. Install with: pip install aiohttp")
            return

        self._print("🌐 Terminal Depths Web Interface")
        self._print(f"📡 Starting on http://localhost:{self.config.port}")

        app = web.Application()
        app.router.add_get("/", self._web_home)
        app.router.add_post("/api/execute", self._web_execute)
        app.router.add_get("/api/state", self._web_state)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self.config.port)
        await site.start()

        self._print(f"✅ Web server running. Open http://localhost:{self.config.port}")

        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await runner.cleanup()

    async def _web_home(self, request) -> "web.Response":
        """Serve web UI."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Terminal Depths</title>
            <style>
                body { font-family: 'Courier New', monospace; background: #0a0e27; color: #00ff00; }
                #terminal { width: 100%; height: 600px; background: #000; overflow-y: auto; padding: 10px; }
                .line { margin: 2px 0; }
                input { width: 100%; padding: 10px; background: #1a1a2e; color: #00ff00; border: 1px solid #00ff00; }
            </style>
        </head>
        <body>
            <h1>Terminal Depths</h1>
            <div id="terminal"></div>
            <input type="text" id="input" placeholder="Enter command..." autofocus>
            <script>
                const terminal = document.getElementById('terminal');
                const input = document.getElementById('input');
                
                async function execute(cmd) {
                    const res = await fetch('/api/execute', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({command: cmd})
                    });
                    const data = await res.json();
                    const line = document.createElement('div');
                    line.className = 'line';
                    line.innerHTML = `<strong>${cmd}</strong><br/>${data.output}`;
                    terminal.appendChild(line);
                    terminal.scrollTop = terminal.scrollHeight;
                }
                
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        execute(input.value);
                        input.value = '';
                    }
                });
            </script>
        </body>
        </html>
        """
        from aiohttp import web
        return web.Response(text=html, content_type="text/html")

    async def _web_execute(self, request) -> "web.Response":
        """Execute command via API."""
        data = await request.json()
        cmd = data.get("command", "")
        output = self.game.execute(cmd)
        notice = self.game._after_command(cmd)
        from aiohttp import web
        return web.json_response({
            "output": output,
            "notice": notice,
            "score": self.game.score
        })

    async def _web_state(self, request) -> "web.Response":
        """Get game state."""
        from aiohttp import web
        return web.json_response({
            "cwd": "/".join(self.game.cwd),
            "score": self.game.score,
            "tasks_completed": sum(1 for _, done, _ in self.game.tasks if done),
            "tasks_total": len(self.game.tasks),
            "session_id": self.session_id
        })

    async def launch_repl(self) -> None:
        """Launch interactive Python REPL with game context."""
        import code

        banner = f"""
Terminal Depths Interactive REPL
Session: {self.session_id}
Game object: 'game'
Commands: game.execute(cmd), game.cmd_ls(), etc.
        """

        locals_dict = {
            "game": self.game,
            "execute": self.game.execute,
            "ls": self.game.cmd_ls,
            "pwd": self.game.cmd_pwd,
            "cd": self.game.cmd_cd,
            "cat": self.game.cmd_cat,
        }

        code.InteractiveConsole(locals=locals_dict).interact(banner=banner)

    async def launch_agent_delegated(self) -> None:
        """Launch via agent orchestrator."""
        self._print("🤖 Terminal Depths Agent-Delegated Mode")
        self._print(f"📡 Orchestrator: {self.config.orchestrator_endpoint}")

        try:
            from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator
            orchestrator = MultiAIOrchestrator()
        except ImportError:
            self._print("❌ Orchestrator not available. Falling back to CLI mode.")
            await self.launch_cli()
            return

        # Register game as a service
        service_def = {
            "name": f"terminal_depths_{self.session_id}",
            "type": "game_engine",
            "capabilities": ["execute", "get_state", "get_tasks"],
            "agent_name": self.config.agent_name or "System",
            "tags": self.config.context_tags
        }

        self._print(f"✅ Game service registered: {service_def['name']}")
        self._print(f"📋 Available agents: {self.config.agent_name}")

        # Fallback to CLI if no agent delegation
        await self.launch_cli()

    async def launch_daemon(self) -> None:
        """Launch as background daemon with REST API."""
        self._print("⚙️  Terminal Depths Daemon Mode")
        self._print(f"📡 API: http://localhost:{self.config.port}/api")

        await self.launch_web()

    def _print_banner(self) -> None:
        """Print startup banner."""
        banner = f"""
╔════════════════════════════════════╗
║   TERMINAL DEPTHS                  ║
║   Chrome Dusk / Neon Glyphs       ║
║   Session: {self.session_id:<13}          ║
╚════════════════════════════════════╝

Mode: {self.config.mode:<15} Surface: {self.config.surface}
Type 'help' for commands, 'exit' to quit.
        """
        self._print(banner)

    def _print_help(self) -> None:
        """Print help text."""
        help_text = """
Commands:
  pwd               - Print working directory
  ls                - List directory contents
  cd <path>         - Change directory
  cat <file>        - Read file
  tasks             - Show task status
  missions          - List available missions
  mission <id>      - Start a mission
  hack              - Initiate hack sequence
  scan              - Scan target
  connect <target>  - Connect to target
  download <target> - Download from target
  help              - Show this help
  exit              - Quit the game
        """
        self._print(help_text)

    def _print(self, msg: str = "") -> None:
        """Print to output."""
        if self.config.surface == "terminal":
            print(msg)
        elif self.config.surface == "vscode":
            # VS Code will capture stdout
            print(msg)
        elif self.config.surface == "godot":
            # Would use Godot's print_debug()
            print(f"[GODOT] {msg}")
        elif self.config.surface == "touchdesigner":
            # Would use TouchDesigner's op() logging
            print(f"[TD] {msg}")
        else:
            print(msg)

    async def run(self) -> None:
        """Run launcher with configured mode."""
        if self.config.mode == "cli":
            await self.launch_cli()
        elif self.config.mode == "web":
            await self.launch_web()
        elif self.config.mode == "repl":
            await self.launch_repl()
        elif self.config.mode == "agent":
            await self.launch_agent_delegated()
        elif self.config.mode == "daemon":
            await self.launch_daemon()
        else:
            raise ValueError(f"Unknown mode: {self.config.mode}")


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Terminal Depths - Universal Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # CLI mode (default)
  python -m scripts.terminal_depths_launcher
  
  # Web interface
  python -m scripts.terminal_depths_launcher --mode web --port 7777
  
  # Agent-delegated mode
  python -m scripts.terminal_depths_launcher --mode agent --agent Ada
  
  # REPL mode
  python -m scripts.terminal_depths_launcher --mode repl
  
  # VS Code integration
  python -m scripts.terminal_depths_launcher --surface vscode
        """
    )

    parser.add_argument(
        "--mode",
        choices=["cli", "web", "repl", "agent", "daemon"],
        default="cli",
        help="Launch mode (default: cli)"
    )
    parser.add_argument(
        "--surface",
        choices=["terminal", "web", "vscode", "godot", "touchdesigner"],
        default="terminal",
        help="Output surface (default: terminal)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7777,
        help="Port for web/daemon modes (default: 7777)"
    )
    parser.add_argument(
        "--agent",
        help="Agent name for delegation"
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        default=[],
        help="Context tags for agent dispatch"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colors"
    )

    args = parser.parse_args()

    config = LauncherConfig(
        mode=args.mode,
        surface=args.surface,
        enable_colors=not args.no_color,
        port=args.port,
        agent_name=args.agent,
        context_tags=args.tags or []
    )

    launcher = TerminalDepthsLauncher(config)

    try:
        asyncio.run(launcher.run())
    except KeyboardInterrupt:
        print("\n👋 Terminal Depths session ended.")
        sys.exit(0)


if __name__ == "__main__":
    main()
