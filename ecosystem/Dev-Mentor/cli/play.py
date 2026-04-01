"""
Terminal Depths — CLI Player
Usage: python -m cli.devmentor play [--server URL]

Connects to the Terminal Depths game engine running on a server
and provides a full readline-capable terminal REPL.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    import readline  # type: ignore
    _HAVE_READLINE = True
except Exception:
    readline = None  # type: ignore
    _HAVE_READLINE = False

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# ANSI colors
C = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
    "cyan":    "\033[36m",
    "green":   "\033[32m",
    "yellow":  "\033[33m",
    "red":     "\033[31m",
    "magenta": "\033[35m",
    "blue":    "\033[34m",
    "orange":  "\033[38;5;208m",
    "white":   "\033[37m",
}

TYPE_COLOR = {
    "info":    "",
    "error":   C["red"],
    "warn":    C["yellow"],
    "success": C["green"],
    "system":  C["cyan"],
    "story":   C["magenta"],
    "npc":     C["orange"],
    "dim":     C["dim"],
    "xp":      C["yellow"],
    "cmd":     C["green"],
    "root":    C["red"] + C["bold"],
}

STATE_FILE = Path.home() / ".terminal_depths" / "session.json"


def _color(t: str, text: str) -> str:
    c = TYPE_COLOR.get(t, "")
    if t == "story":
        return f"{c}│ {text}{C['reset']}"
    if t == "root":
        return f"{c}{text}{C['reset']}"
    return c + text + (C["reset"] if c else "")


def _iter_output_items(items: list):
    for item in items:
        if isinstance(item, list):
            yield from _iter_output_items(item)
            continue
        if isinstance(item, dict):
            yield item
            continue
        if item is None:
            continue
        yield {"t": "info", "s": str(item)}


def _print_output(items: list):
    for item in _iter_output_items(items):
        t = item.get("t", "info")
        if t == "ls-row":
            row_parts = []
            for i in item.get("items", []):
                col = C.get(i.get("color", ""), "")
                row_parts.append(col + i["text"] + C["reset"])
            print("".join(row_parts))
        elif t == "npc":
            npc = item.get("npc", "NPC")
            text = item.get("text", "")
            print(f"{C['orange']}[{npc}]{C['reset']}")
            print(text)
        elif t == "clear":
            os.system("clear" if os.name != "nt" else "cls")
        else:
            s = item.get("s", "")
            if s or t == "info":
                print(_color(t, s))


def _load_session() -> dict:
    """Load saved session from disk."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_session(data: dict):
    """Persist session to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def _get_prompt(name: str, cwd: str, is_root: bool) -> str:
    user = "root" if is_root else "ghost"
    sym = "#" if is_root else "$"
    user_color = C["red"] + C["bold"] if is_root else C["green"]
    cwd_short = cwd.replace("/home/ghost", "~")
    return f"{user_color}{user}{C['reset']}@node-7:{C['blue']}{cwd_short}{C['reset']}{sym} "


class GameClient:
    def __init__(self, server: str = "http://localhost:7337"):
        self.server = server.rstrip("/")
        saved = _load_session()
        self.session_id: Optional[str] = saved.get("session_id")
        self.cwd: str = saved.get("cwd", "~")
        self.is_root: bool = saved.get("is_root", False)
        self.state: dict = saved.get("state", {})
        self._cmds: list = []

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.session_id:
            h["X-Session-Id"] = self.session_id
        return h

    def connect(self) -> bool:
        """Create or resume a session."""
        if not _HAS_REQUESTS:
            print(f"{C['red']}Error: 'requests' package not installed.{C['reset']}")
            print("Install with: pip install requests")
            return False
        try:
            r = requests.post(
                f"{self.server}/api/game/session",
                json={"session_id": self.session_id},
                headers=self._headers(),
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.ConnectionError:
            print(f"{C['red']}Cannot connect to server at {self.server}{C['reset']}")
            print(f"{C['dim']}Make sure the DevMentor server is running.{C['reset']}")
            return False
        except Exception as e:
            print(f"{C['red']}Connection error: {e}{C['reset']}")
            return False

        self.session_id = data["session_id"]
        self.state = data.get("state", {})
        self.cwd = data.get("cwd", "/home/ghost").replace("/home/ghost", "~")
        self.is_root = data.get("is_root", False)
        _save_session({"session_id": self.session_id, "cwd": self.cwd,
                        "is_root": self.is_root, "state": self.state})

        # Boot message
        boot = data.get("boot_output", [])
        if boot:
            _print_output(boot)
            print()

        # Fetch command list for tab completion
        try:
            cr = requests.get(f"{self.server}/api/game/commands", headers=self._headers(), timeout=5)
            self._cmds = cr.json().get("commands", [])
        except Exception:
            pass

        return True

    def send_command(self, cmd: str) -> bool:
        """Send command to server and print output. Returns False on fatal error."""
        try:
            r = requests.post(
                f"{self.server}/api/game/command",
                json={"command": cmd, "session_id": self.session_id},
                headers=self._headers(),
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.ConnectionError:
            print(f"{C['red']}Lost connection to server.{C['reset']}")
            return False
        except Exception as e:
            print(f"{C['red']}Error: {e}{C['reset']}")
            return True

        self.session_id = data.get("session_id", self.session_id)
        self.state = data.get("state", self.state)
        self.cwd = data.get("cwd", self.cwd).replace("/home/ghost", "~")
        self.is_root = data.get("is_root", self.is_root)

        _print_output(data.get("output", []))

        if tut := data.get("tutorial_notification"):
            print(f"\n{C['yellow']}✓ {tut}{C['reset']}")

        if lvl := data.get("level_up"):
            print(f"\n{C['magenta']}▲ LEVEL UP: {lvl}{C['reset']}")

        _save_session({"session_id": self.session_id, "cwd": self.cwd,
                       "is_root": self.is_root, "state": self.state})
        return True

    def setup_readline(self):
        """Configure readline with history + tab completion (if available)."""
        if not _HAVE_READLINE or readline is None:
            return

        hist_file = Path.home() / ".terminal_depths" / "history"
        hist_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            readline.read_history_file(str(hist_file))
        except FileNotFoundError:
            pass
        readline.set_history_length(500)

        cmds = self._cmds

        def completer(text, state):
            options = [c for c in cmds if c.startswith(text)]
            return options[state] if state < len(options) else None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")

        import atexit
        atexit.register(readline.write_history_file, str(hist_file))

    def run(self):
        """Main REPL loop."""
        name = self.state.get("name", "GHOST")
        level = self.state.get("level", 1)
        print(f"\n{C['cyan']}╔══════════════════════════════════════╗{C['reset']}")
        print(f"{C['cyan']}║  TERMINAL DEPTHS — CLI Interface     ║{C['reset']}")
        print(f"{C['cyan']}╚══════════════════════════════════════╝{C['reset']}")
        print(f"  {C['dim']}Operative:{C['reset']} {name}  {C['dim']}Level:{C['reset']} {level}")
        print(f"  {C['dim']}Server:{C['reset']} {self.server}")
        print(f"  {C['dim']}Session:{C['reset']} {(self.session_id or '')[:16]}...")
        print(f"\n  {C['dim']}Type{C['reset']} help  {C['dim']}for commands.{C['reset']}")
        print(f"  {C['dim']}Type{C['reset']} exit  {C['dim']}to quit.\n{C['reset']}")

        self.setup_readline()

        while True:
            try:
                prompt = _get_prompt(name, self.cwd, self.is_root)
                try:
                    cmd = input(prompt).strip()
                except EOFError:
                    print()
                    break

                if not cmd:
                    continue
                if cmd.lower() in ("exit", "quit", "logout"):
                    print(f"{C['dim']}logout{C['reset']}")
                    break

                if not self.send_command(cmd):
                    break

                # Update name/level from state
                if self.state:
                    name = self.state.get("name", name)

            except KeyboardInterrupt:
                print("^C")

        print(f"\n{C['dim']}Session saved. Run again to resume.{C['reset']}")


def run_cli(server: str = "http://localhost:7337"):
    """Entry point called from cli/devmentor.py."""
    client = GameClient(server)
    if client.connect():
        client.run()
    else:
        sys.exit(1)
