#!/usr/bin/env python3
"""td — Terminal Depths Universal Launcher
========================================
Type `td` from ANY terminal to enter Terminal Depths.

Works in: Bash · Zsh · Fish · PowerShell 5/7 · CMD · Git Bash · WSL ·
          VS Code integrated terminal · Docker exec · Replit shell ·
          Godot console (via Python) · TouchDesigner Python REPL ·
          ChatDev · any environment with Python 3.8+

Usage:
  td                   — auto-detect best interface and enter
  td play              — rich terminal REPL (no browser required)
  td open              — open in browser only
  td status            — show server + colony health
  td surfaces          — inventory all detected surfaces
  td install           — install 'td' command system-wide
  td help              — this message

Environment variables:
  TD_SERVER_URL        — override server URL (default: http://localhost:7337)
  TD_SESSION_ID        — reuse a specific session ID
  TD_NO_BROWSER        — set to 1 to skip browser, use terminal REPL
  TD_REPLIT_URL        — Replit Dev URL for browser launch
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import textwrap
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Repo root resolution ────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = _SCRIPT_DIR.parent

# Add repo root to path for terminal_abstraction import
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(_SCRIPT_DIR))

try:
    from terminal_abstraction import ShellKind, Surface, TerminalEnv
    from terminal_abstraction import detect as _detect_env

    _HAS_ABSTRACTION = True
except ImportError:
    _HAS_ABSTRACTION = False

# ── Rich detection (optional — graceful degradation) ────────────────────────
try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    _HAS_RICH = True
    _con = Console()
except ImportError:
    _HAS_RICH = False
    _con = None

# ── Color codes for non-rich terminals ──────────────────────────────────────
_ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "magenta": "\033[35m",
    "white": "\033[37m",
}


def _c(text: str, style: str) -> str:
    """Apply ANSI color if stdout is a TTY."""
    if not sys.stdout.isatty():
        return text
    code = _ANSI.get(style, "")
    return f"{code}{text}{_ANSI['reset']}"


def _print(text: str, style: str = "white") -> None:
    if _HAS_RICH and _con:
        style_map = {
            "system": "bold cyan",
            "info": "white",
            "success": "bold green",
            "error": "bold red",
            "warn": "yellow",
            "dim": "dim",
            "white": "white",
            "cyan": "cyan",
            "magenta": "magenta",
            "bold": "bold white",
        }
        _con.print(text, style=style_map.get(style, "white"))
    else:
        print(_c(text, style))


def _hr(char: str = "─", width: int = 72) -> None:
    _print(char * width, "dim")


# ── Server configuration ─────────────────────────────────────────────────────
DEFAULT_PORTS = [5000, 8008, 7337, 8000]
TD_SERVER_URL = os.getenv("TD_SERVER_URL", "")
TD_SESSION_ID = os.getenv("TD_SESSION_ID", "td-launcher")
TD_NO_BROWSER = os.getenv("TD_NO_BROWSER", "0") == "1"
TD_REPLIT_URL = os.getenv("TD_REPLIT_URL", "")
REPLIT_DOMAIN = os.getenv("REPLIT_DEV_DOMAIN", "") or os.getenv("REPL_SLUG", "")

# ── Boot banner ──────────────────────────────────────────────────────────────
BANNER = r"""
  ╔══════════════════════════════════════════════════════════════════╗
  ║  ████████╗██████╗     ██╗      █████╗ ██╗   ██╗███╗   ██╗      ║
  ║     ██╔══╝██╔══██╗    ██║     ██╔══██╗██║   ██║████╗  ██║      ║
  ║     ██║   ██║  ██║    ██║     ███████║██║   ██║██╔██╗ ██║      ║
  ║     ██║   ██║  ██║    ██║     ██╔══██║██║   ██║██║╚██╗██║      ║
  ║     ██║   ██████╔╝    ███████╗██║  ██║╚██████╔╝██║ ╚████║      ║
  ║     ╚═╝   ╚═════╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝     ║
  ║               ██████╗ ███████╗██████╗ ████████╗██╗  ██╗███████╗║
  ║               ██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║  ██║██╔════╝║
  ║               ██║  ██║█████╗  ██████╔╝   ██║   ███████║███████╗║
  ║               ██║  ██║██╔══╝  ██╔═══╝    ██║   ██╔══██║╚════██║║
  ║               ██████╔╝███████╗██║        ██║   ██║  ██║███████║║
  ║               ╚═════╝ ╚══════╝╚═╝        ╚═╝   ╚═╝  ╚═╝╚══════╝║
  ╠══════════════════════════════════════════════════════════════════╣
  ║  ΨΞΦΩ  NuSyQ-Hub · Colony Active · Serena Online               ║
  ╚══════════════════════════════════════════════════════════════════╝
"""

MINI_BANNER = "  ◈ TERMINAL DEPTHS — ΨΞΦΩ · NuSyQ-Hub · Colony Active"


# ════════════════════════════════════════════════════════════════════════════
# Server discovery
# ════════════════════════════════════════════════════════════════════════════


def _probe_port(host: str, port: int, timeout: float = 0.5) -> bool:
    """Return True if something is listening on host:port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _api_get(url: str, timeout: float = 3.0) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def _api_post(url: str, body: dict, timeout: float = 5.0) -> dict | None:
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def discover_server() -> str | None:
    """Return the first responding Terminal Depths server URL."""
    if TD_SERVER_URL:
        parsed = urllib.parse.urlparse(TD_SERVER_URL)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5000
        if _probe_port(host, port):
            return TD_SERVER_URL
        return None

    # Auto-discovery across known ports
    for port in DEFAULT_PORTS:
        if _probe_port("localhost", port):
            result = _api_get(f"http://localhost:{port}/api/health", timeout=1.5)
            if result and result.get("ok"):
                return f"http://localhost:{port}"
    return None


def start_server_background(port: int = 5000) -> subprocess.Popen | None:
    """Start the game server in the background. Returns the process."""
    cmd = [
        sys.executable,
        "-m",
        "cli.devmentor",
        "serve",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return proc
    except Exception as e:
        _print(f"  [!] Could not start server: {e}", "error")
        return None


def wait_for_server(port: int = 5000, timeout: float = 12.0) -> bool:
    """Poll until server is responsive or timeout."""
    deadline = time.time() + timeout
    dots = 0
    while time.time() < deadline:
        if _probe_port("localhost", port, 0.3):
            result = _api_get(f"http://localhost:{port}/api/health", timeout=1.0)
            if result and result.get("ok"):
                return True
        sys.stdout.write(f"\r  Starting server{'.' * (dots % 4 + 1)}    ")
        sys.stdout.flush()
        dots += 1
        time.sleep(0.5)
    sys.stdout.write("\r" + " " * 40 + "\r")
    return False


# ════════════════════════════════════════════════════════════════════════════
# Environment / Surface inventory
# ════════════════════════════════════════════════════════════════════════════


@dataclass
class SurfaceInventory:
    shell: str
    surface: str
    platform: str
    in_vscode: bool
    in_docker: bool
    in_wsl: bool
    in_replit: bool
    has_browser: bool
    has_python: bool
    has_node: bool
    has_git: bool
    godot_present: bool
    td_present: bool
    simverse_port: int | None
    extra_notes: list[str]


def map_surfaces() -> SurfaceInventory:
    """Detect and catalogue all surfaces."""
    # Use the full abstraction if available
    env = None
    if _HAS_ABSTRACTION:
        try:
            env = _detect_env()
        except Exception:
            pass

    shell = env.shell.value if env else os.getenv("SHELL", "unknown").split("/")[-1]
    surface = env.surface.value if env else "local"
    plat = platform.system()
    in_vscode = bool(os.getenv("TERM_PROGRAM") == "vscode" or os.getenv("VSCODE_PID"))
    in_docker = Path("/.dockerenv").exists() or bool(os.getenv("DOCKER_CONTAINER"))
    in_wsl = False
    in_replit = bool(os.getenv("REPL_ID") or os.getenv("REPLIT_DB_URL"))
    if plat == "Linux":
        try:
            osrel = Path("/proc/sys/kernel/osrelease").read_text().lower()
            in_wsl = "microsoft" in osrel or "wsl" in osrel
        except Exception:
            pass

    has_browser = (
        bool(
            shutil.which("xdg-open")
            or shutil.which("open")
            or shutil.which("start")
            or os.getenv("BROWSER")
        )
        or plat == "Windows"
    )
    has_python = bool(shutil.which("python3") or shutil.which("python"))
    has_node = bool(shutil.which("node"))
    has_git = bool(shutil.which("git"))

    # Godot — check for Godot binary or project
    godot_present = bool(
        shutil.which("godot")
        or shutil.which("godot4")
        or list(REPO_ROOT.glob("*.godot"))
        or list(REPO_ROOT.glob("**/*.tscn"))
    )

    # TouchDesigner / ChatDev detection via env hints
    extra_notes = []
    if os.getenv("TD_PROCESS") or os.getenv("TOUCHDESIGNER"):
        extra_notes.append("TouchDesigner environment detected")
    if shutil.which("chatdev"):
        extra_notes.append("ChatDev CLI available")
    if in_wsl:
        extra_notes.append("WSL — Windows files at /mnt/c/")

    # SimulatedVerse — check if running
    simverse_port = None
    for sv_port in [5001, 3000, 4000]:
        if _probe_port("localhost", sv_port, 0.3):
            result = _api_get(f"http://localhost:{sv_port}/api/health", 0.5)
            if result:
                simverse_port = sv_port
                break

    # td present in PATH
    td_present = bool(shutil.which("td"))

    return SurfaceInventory(
        shell=shell,
        surface=surface,
        platform=plat,
        in_vscode=in_vscode,
        in_docker=in_docker,
        in_wsl=in_wsl,
        in_replit=in_replit,
        has_browser=has_browser,
        has_python=has_python,
        has_node=has_node,
        has_git=has_git,
        godot_present=godot_present,
        td_present=td_present,
        simverse_port=simverse_port,
        extra_notes=extra_notes,
    )


def print_surfaces(inv: SurfaceInventory) -> None:
    _print("\n  SURFACE INVENTORY", "system")
    _hr()
    rows = [
        ("Shell", inv.shell),
        ("Surface", inv.surface),
        ("Platform", inv.platform),
        ("VS Code", "✓ integrated terminal" if inv.in_vscode else "—"),
        ("Docker", "✓ container" if inv.in_docker else "—"),
        ("WSL", "✓ Windows Subsystem for Linux" if inv.in_wsl else "—"),
        ("Replit", "✓ cloud container" if inv.in_replit else "—"),
        ("Browser", "✓ available" if inv.has_browser else "— no browser"),
        ("Git", "✓" if inv.has_git else "— not found"),
        ("Node.js", "✓" if inv.has_node else "— not found"),
        ("Godot", "✓ detected" if inv.godot_present else "—"),
        (
            "SimVerse",
            f"✓ port {inv.simverse_port}" if inv.simverse_port else "— not running",
        ),
        (
            "td in PATH",
            (
                "✓ global command"
                if inv.td_present
                else "— not installed (run: td install)"
            ),
        ),
    ]
    for label, value in rows:
        check = "✓" if value.startswith("✓") else " "
        style = "success" if check == "✓" else "dim"
        _print(f"  {label:<14} {value}", style)
    for note in inv.extra_notes:
        _print(f"  [NOTE] {note}", "warn")
    _hr()


# ════════════════════════════════════════════════════════════════════════════
# Browser launch
# ════════════════════════════════════════════════════════════════════════════


def _game_url(server_url: str, inv: SurfaceInventory) -> str:
    """Derive the browser-accessible game URL."""
    # Prefer explicit Replit Dev URL
    if TD_REPLIT_URL:
        return TD_REPLIT_URL
    # Derive from REPLIT_DEV_DOMAIN env (set by Replit automatically)
    domain = os.getenv("REPLIT_DEV_DOMAIN", "")
    if domain:
        return f"https://{domain}/"
    # If we're inside a Replit container, tell the user to use the Dev URL
    if inv.in_replit:
        return f"[Check your Replit Dev URL — {server_url} (proxied)]"
    return server_url.rstrip("/") + "/"


def open_browser(url: str) -> bool:
    """Open URL in the default system browser. Returns True on success."""
    if not url.startswith("http"):
        return False
    plat = platform.system()
    try:
        if plat == "Darwin":
            subprocess.Popen(["open", url])
        elif plat == "Windows":
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            # Linux / WSL / Git Bash
            for opener in [
                "xdg-open",
                "sensible-browser",
                "x-www-browser",
                "firefox",
                "chromium-browser",
            ]:
                if shutil.which(opener):
                    subprocess.Popen([opener, url])
                    return True
            # WSL: call Windows' start command
            if Path("/proc/sys/kernel/osrelease").exists():
                osrel = Path("/proc/sys/kernel/osrelease").read_text().lower()
                if "microsoft" in osrel:
                    subprocess.Popen(["cmd.exe", "/c", "start", url])
                    return True
            return False
        return True
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════════════════
# Terminal REPL (Rich-backed, no browser required)
# ════════════════════════════════════════════════════════════════════════════

_TYPE_STYLE = {
    "system": "bold cyan",
    "info": "white",
    "success": "bold green",
    "error": "bold red",
    "warn": "yellow",
    "dim": "dim",
    "lore": "italic magenta",
    "default": "white",
}

_ANSI_TYPE = {
    "system": "\033[1;36m",
    "info": "\033[0m",
    "success": "\033[1;32m",
    "error": "\033[1;31m",
    "warn": "\033[33m",
    "dim": "\033[2m",
    "lore": "\033[35m",
    "default": "\033[0m",
}


def _render_line(line: dict) -> None:
    """Print a single game output line with correct styling."""
    text = line.get("s", "")
    typ = line.get("t", "info")

    if line.get("t") == "ls-row":
        items = line.get("items", [])
        row_text = "  " + "  ".join(
            _c(it.get("text", ""), "cyan" if "dir" in it.get("color", "") else "white")
            for it in items
        )
        print(row_text)
        return

    if _HAS_RICH and _con:
        style = _TYPE_STYLE.get(typ, "white")
        _con.print(text, style=style, highlight=False)
    else:
        code = _ANSI_TYPE.get(typ, "\033[0m")
        print(f"{code}{text}\033[0m")


def _render_output(output: list[dict]) -> None:
    for line in output:
        _render_line(line)


def _get_prompt(server_url: str, session_id: str) -> str:
    """Fetch the player's name + cwd for the prompt."""
    state = _api_get(f"{server_url}/api/game/state?session_id={session_id}", 1.0)
    name = "GHOST"
    cwd = "~"
    if state:
        s = state.get("state", {})
        name = s.get("name", "GHOST")
        cwd = state.get("cwd", "~")
    if _HAS_RICH and _con:
        return f"[bold red]{name}@colony[/bold red]:[bold cyan]{cwd}[/bold cyan]$ "
    return _c(f"{name}@colony", "red") + ":" + _c(cwd, "cyan") + "$ "


def run_terminal_repl(server_url: str, session_id: str) -> None:
    """Interactive terminal REPL — send commands to game API, render output."""
    _print(
        "\n  Connected to Terminal Depths. Type 'exit' or Ctrl+C to leave.", "system"
    )
    _print("  Commands: help · tutorial · skills · ls · map · faction · lore", "dim")
    _hr()

    # Initial greeting
    result = _api_post(
        f"{server_url}/api/game/command",
        {
            "command": "help --brief",
            "session_id": session_id,
        },
    )
    if result:
        _render_output(result.get("output", []))

    while True:
        try:
            # Build prompt
            prompt_str = _get_prompt(server_url, session_id)
            if _HAS_RICH and _con:
                cmd = _con.input(prompt_str)
            else:
                sys.stdout.write(prompt_str)
                sys.stdout.flush()
                cmd = input()

            cmd = cmd.strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit", "logout", "disconnect", ":q"):
                _print(
                    "\n  [∞] Session preserved. Colony continues. Re-enter with: td",
                    "dim",
                )
                break

            # Send to API
            result = _api_post(
                f"{server_url}/api/game/command",
                {
                    "command": cmd,
                    "session_id": session_id,
                },
            )
            if result is None:
                _print("  [!] Lost connection to Terminal Depths server.", "error")
                _print(f"      Server: {server_url}", "dim")
                break
            _render_output(result.get("output", []))

        except KeyboardInterrupt:
            _print("\n\n  [∞] Ctrl+C — session preserved. Colony continues.", "dim")
            break
        except EOFError:
            break


# ════════════════════════════════════════════════════════════════════════════
# Colony activation sequence
# ════════════════════════════════════════════════════════════════════════════


def activate_colony(server_url: str, session_id: str, inv: SurfaceInventory) -> None:
    """POST session create + run a silent surface-mapping init command."""
    # Create or resume session
    _api_post(f"{server_url}/api/game/session", {"session_id": session_id})

    # Surface annotation command (silent — just triggers story beat)
    surface_tag = inv.shell
    if inv.in_vscode:
        surface_tag += "+vscode"
    if inv.in_docker:
        surface_tag += "+docker"
    if inv.in_wsl:
        surface_tag += "+wsl"
    if inv.in_replit:
        surface_tag += "+replit"

    # Fire a lightweight status check via game command to register presence
    _api_post(
        f"{server_url}/api/game/command",
        {
            "command": "manifest",
            "session_id": session_id,
        },
    )


# ════════════════════════════════════════════════════════════════════════════
# Server status command
# ════════════════════════════════════════════════════════════════════════════


def cmd_status() -> None:
    _print(MINI_BANNER + "\n", "cyan")
    inv = map_surfaces()
    server_url = discover_server()

    print_surfaces(inv)

    _print("\n  SERVER HEALTH", "system")
    _hr()
    if server_url:
        health = _api_get(f"{server_url}/api/health", 2.0)
        if health:
            _print(f"  ✓ Online        {server_url}", "success")
            _print(f"  ✓ Uptime        {health.get('uptime_s', '?')}s", "success")
            _print(f"  ✓ Game engine   {health.get('game_engine', '?')}", "success")
            _print(
                f"  ✓ Sessions      {health.get('active_game_sessions', '?')}",
                "success",
            )
        else:
            _print(f"  ✓ Port open   {server_url}", "success")
            _print("  ? Health API not responding", "warn")
    else:
        _print("  ✗ No Terminal Depths server found", "error")
        _print("  Start with: make dev    or    td (will auto-start)", "dim")
        for port in DEFAULT_PORTS:
            _print(f"    Tried: localhost:{port}", "dim")

    if inv.simverse_port:
        _print(f"  ✓ SimulatedVerse  localhost:{inv.simverse_port}", "success")
    else:
        _print("  — SimulatedVerse  not running", "dim")
    _hr()


# ════════════════════════════════════════════════════════════════════════════
# Installer
# ════════════════════════════════════════════════════════════════════════════

INSTALLER_BASH = """\
#!/usr/bin/env bash
# td — Terminal Depths Launcher (auto-generated by td install)
# Place in any directory on your PATH: ~/.local/bin/td  OR  ~/bin/td
TD_REPO="{repo_root}"
exec python3 "$TD_REPO/scripts/td.py" "$@"
"""

INSTALLER_PS1 = """\
# td.ps1 — Terminal Depths Launcher (auto-generated by td install)
# Auto-detected repo root
$TDRepo = "{repo_root}"
& python "$TDRepo\\scripts\\td.py" @Args
"""

INSTALLER_CMD = """\
@echo off
REM td.cmd — Terminal Depths Launcher (auto-generated by td install)
set TD_REPO={repo_root_win}
python "%TD_REPO%\\scripts\\td.py" %*
"""


def cmd_install() -> None:
    """Install the `td` command system-wide."""
    _print(MINI_BANNER + "\n", "cyan")
    _print("  TD INSTALLER", "system")
    _hr()

    plat = platform.system()
    repo_str = str(REPO_ROOT)
    repo_win = str(REPO_ROOT).replace("/", "\\")

    installed: list[tuple[str, str]] = []
    errors: list[tuple[str, str]] = []

    def _write(path: Path, content: str, executable: bool = False) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            if executable and plat != "Windows":
                path.chmod(0o755)
            installed.append((str(path), "✓"))
            _print(f"  ✓ Written: {path}", "success")
        except Exception as e:
            errors.append((str(path), str(e)))
            _print(f"  ✗ Failed:  {path}  ({e})", "error")

    if plat != "Windows":
        # Unix: write to ~/.local/bin/td  (usually on PATH)
        local_bin = Path.home() / ".local" / "bin"
        td_path = local_bin / "td"
        _write(td_path, INSTALLER_BASH.format(repo_root=repo_str), executable=True)

        # Also write ~/bin/td if that directory exists
        bin_home = Path.home() / "bin"
        if bin_home.exists():
            _write(
                bin_home / "td",
                INSTALLER_BASH.format(repo_root=repo_str),
                executable=True,
            )

        # PowerShell Core on Linux/Mac
        if shutil.which("pwsh"):
            ps_dir = Path.home() / ".config" / "powershell"
            _write(ps_dir / "td.ps1", INSTALLER_PS1.format(repo_root=repo_str))

        _print("\n  Add to PATH if needed (paste into ~/.bashrc / ~/.zshrc):", "dim")
        _print('  export PATH="$HOME/.local/bin:$PATH"', "dim")

    else:
        # Windows: write to %USERPROFILE%\bin and PowerShell profile dir
        user_bin = Path.home() / "bin"
        _write(user_bin / "td.cmd", INSTALLER_CMD.format(repo_root_win=repo_win))
        _write(user_bin / "td.ps1", INSTALLER_PS1.format(repo_root=repo_str))

        # PowerShell Documents\WindowsPowerShell\Scripts
        ps_scripts = Path.home() / "Documents" / "WindowsPowerShell" / "Scripts"
        _write(ps_scripts / "td.ps1", INSTALLER_PS1.format(repo_root=repo_str))

        _print("\n  Add to PATH (run in PowerShell as Admin):", "dim")
        _print(f'  $env:PATH += ";{user_bin}"', "dim")
        _print(
            '  [Environment]::SetEnvironmentVariable("PATH", $env:PATH, "User")', "dim"
        )

    # Write repo-local scripts (always — works without PATH)
    _write(REPO_ROOT / "td", INSTALLER_BASH.format(repo_root=repo_str), executable=True)
    _write(REPO_ROOT / "td.ps1", INSTALLER_PS1.format(repo_root=repo_str))
    _write(REPO_ROOT / "td.cmd", INSTALLER_CMD.format(repo_root_win=repo_win))

    _hr()
    _print(
        f"  {len(installed)} files written, {len(errors)} errors",
        "success" if not errors else "warn",
    )
    _print("\n  IMMEDIATE USE (no PATH needed):", "system")
    _print("  bash/zsh/git-bash   ./td", "dim")
    _print("  PowerShell          .\\td.ps1", "dim")
    _print("  CMD                 td.cmd", "dim")
    _print("  Python anywhere     python scripts/td.py", "dim")
    _hr()


# ════════════════════════════════════════════════════════════════════════════
# Main entry point
# ════════════════════════════════════════════════════════════════════════════


def _boot_header(inv: SurfaceInventory) -> None:
    """Print the boot sequence header."""
    if sys.stdout.isatty() and (_HAS_RICH or True):
        print(_c(BANNER, "cyan"))
    else:
        _print(MINI_BANNER, "cyan")

    env_tag = inv.shell
    if inv.in_vscode:
        env_tag += " · VS Code"
    if inv.in_docker:
        env_tag += " · Docker"
    if inv.in_wsl:
        env_tag += " · WSL"
    if inv.in_replit:
        env_tag += " · Replit"
    if inv.godot_present:
        env_tag += " · Godot"
    _print(f"  Surface detected: {env_tag}", "dim")


def main(argv: list[str] = None) -> int:
    args = argv or sys.argv[1:]
    subcmd = args[0].lower() if args else "auto"
    rest = args[1:]

    # ── Quick commands that don't need a server ───────────────────────────
    if subcmd in ("install",):
        cmd_install()
        return 0

    if subcmd in ("surfaces", "surface", "map", "scan"):
        inv = map_surfaces()
        print_surfaces(inv)
        return 0

    if subcmd in ("status", "health", "check"):
        cmd_status()
        return 0

    if subcmd in ("help", "--help", "-h"):
        print(__doc__)
        return 0

    # ── Commands that need a running server ───────────────────────────────
    inv = map_surfaces()
    _boot_header(inv)

    # 1. Discover server
    _print("\n  Scanning for Terminal Depths server...", "dim")
    server_url = discover_server()

    if not server_url:
        _print("  Server not found — starting Terminal Depths...", "system")
        proc = start_server_background(5000)
        if proc:
            ok = wait_for_server(5000, timeout=15.0)
            if ok:
                server_url = "http://localhost:7337"
                _print("  ✓ Server started", "success")
            else:
                _print("  ✗ Server failed to start within 15s", "error")
                _print(
                    "  Try manually: make dev  OR  python -m cli.devmentor serve", "dim"
                )
                return 1
        else:
            return 1
    else:
        _print(f"  ✓ Server: {server_url}", "success")

    # 2. Activate colony
    session_id = TD_SESSION_ID or f"td-{int(time.time())}"
    activate_colony(server_url, session_id, inv)

    # 3. SimulatedVerse note
    if inv.simverse_port:
        sv_url = f"http://localhost:{inv.simverse_port}"
        _print(f"  ✓ SimulatedVerse: {sv_url}", "success")

    # 4. Determine game URL
    game_url = _game_url(server_url, inv)
    _print(f"  ✓ Game URL:  {game_url}", "system")
    if inv.simverse_port:
        _print(f"  ✓ SimVerse:  http://localhost:{inv.simverse_port}/", "dim")

    # 5. Choose interface based on subcommand + env
    force_play = subcmd in ("play", "repl", "terminal", "tty")
    force_open = subcmd in ("open", "browser", "web")
    no_browser = TD_NO_BROWSER or inv.in_replit or force_play or not inv.has_browser

    if force_open or (not no_browser and inv.has_browser):
        _print("\n  Opening Terminal Depths in browser...", "system")
        if inv.in_replit:
            _print(f"  [Replit] Open your Dev URL: {game_url}", "warn")
            _print("  Launching terminal REPL instead...", "dim")
            run_terminal_repl(server_url, session_id)
        else:
            opened = open_browser(game_url)
            if inv.simverse_port:
                sv_url = f"http://localhost:{inv.simverse_port}/"
                _print("  Opening SimulatedVerse in separate tab...", "dim")
                open_browser(sv_url)
            if opened:
                _print("  ✓ Browser launched. Terminal Depths is loading.", "success")
                _print("  [The terminal REPL is also available: td play]", "dim")
            else:
                _print("  Could not open browser — launching terminal REPL", "warn")
                run_terminal_repl(server_url, session_id)
    else:
        # Terminal REPL fallback
        _print("\n  Entering terminal REPL mode...", "system")
        if inv.in_replit:
            _print(f"  [Browser] {game_url}", "dim")
        run_terminal_repl(server_url, session_id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
