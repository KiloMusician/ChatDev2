"""terminal_abstraction.py — Cross-surface shell & environment detection.

Detects which terminal/surface the process is running inside and exposes
a unified adapter so the rest of DevMentor can issue shell commands,
format output, and route instructions appropriately regardless of whether
the host is:
  • PowerShell 7 (pwsh)      — Windows / Linux / macOS
  • Windows PowerShell 5.1   — Windows built-in
  • CMD / Command Prompt      — Windows legacy
  • Git Bash / MINGW64        — MSYS2 on Windows
  • WSL Bash                  — Windows Subsystem for Linux
  • Bash / Zsh                — Linux / macOS native
  • Replit Container          — Cloud dev environment
  • Docker container          — CI / local stack
  • VS Code Integrated Term.  — any of the above, inside VS Code
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

# ──────────────────────────────────────────────────────────────────────────────
# Surface / Shell enumerations
# ──────────────────────────────────────────────────────────────────────────────


class Surface(str, Enum):
    REPLIT = "replit"
    VSCODE = "vscode"
    DOCKER = "docker"
    OBSIDIAN = "obsidian"
    GITHUB_CI = "github_ci"
    LOCAL = "local"


class ShellKind(str, Enum):
    POWERSHELL_7 = "pwsh"  # pwsh.exe / pwsh
    POWERSHELL_5 = "powershell"  # Windows PowerShell 5.1
    CMD = "cmd"  # Command Prompt
    GIT_BASH = "git_bash"  # MSYS2 / MINGW64
    WSL = "wsl"  # Windows Subsystem for Linux
    BASH = "bash"  # GNU Bash (Linux/macOS)
    ZSH = "zsh"  # Zsh (macOS default, Linux optional)
    FISH = "fish"  # Fish shell
    UNKNOWN = "unknown"


# ──────────────────────────────────────────────────────────────────────────────
# Detected environment dataclass
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class TerminalEnv:
    surface: Surface
    shell: ShellKind
    platform: str  # "Windows", "Linux", "Darwin"
    in_vscode: bool = False
    in_docker: bool = False
    in_wsl: bool = False
    conda_env: str | None = None
    venv_path: str | None = None
    path_sep: str = os.pathsep
    line_end: str = "\n"
    clear_cmd: str = "clear"
    which_cmd: str = "which"
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def is_windows_native(self) -> bool:
        return self.platform == "Windows" and not self.in_wsl

    @property
    def is_unix(self) -> bool:
        return self.platform in ("Linux", "Darwin") or self.in_wsl

    @property
    def label(self) -> str:
        parts = [self.shell.value]
        if self.in_vscode:
            parts.append("vscode")
        if self.in_docker:
            parts.append("docker")
        parts.append(f"({self.surface.value})")
        return "/".join(parts)


# ──────────────────────────────────────────────────────────────────────────────
# Detection logic
# ──────────────────────────────────────────────────────────────────────────────


def _detect_surface() -> Surface:
    if os.getenv("REPL_ID") or os.getenv("REPLIT_DB_URL"):
        return Surface.REPLIT
    if os.getenv("GITHUB_ACTIONS"):
        return Surface.GITHUB_CI
    if Path("/.dockerenv").exists() or os.getenv("DOCKER_CONTAINER"):
        return Surface.DOCKER
    if os.getenv("TERM_PROGRAM") == "vscode" or os.getenv("VSCODE_PID"):
        return Surface.VSCODE
    return Surface.LOCAL


def _detect_shell() -> ShellKind:
    # On Windows, COMSPEC + PSModulePath fingerprinting
    comspec = os.getenv("COMSPEC", "").lower()
    psmod = os.getenv("PSModulePath", "")

    # Inside Git Bash / MINGW64
    msystem = os.getenv("MSYSTEM", "")
    if msystem in ("MINGW64", "MINGW32", "MSYS", "CLANG64"):
        return ShellKind.GIT_BASH

    # Check parent process name via /proc (Linux/WSL) or psutil fallback
    parent_name = _parent_process_name()

    if parent_name:
        pn = parent_name.lower()
        if "pwsh" in pn:
            return ShellKind.POWERSHELL_7
        if "powershell" in pn:
            return ShellKind.POWERSHELL_5
        if "cmd" in pn:
            return ShellKind.CMD
        if "bash" in pn:
            # Distinguish WSL Bash from native Bash — checked below
            pass
        if "zsh" in pn:
            return ShellKind.ZSH
        if "fish" in pn:
            return ShellKind.FISH

    # Fall back to SHELL env var (present in Unix-like shells)
    shell_var = os.getenv("SHELL", "")
    if "zsh" in shell_var:
        return ShellKind.ZSH
    if "fish" in shell_var:
        return ShellKind.FISH
    if "bash" in shell_var:
        return ShellKind.BASH

    # Windows PowerShell detection via PSModulePath
    if psmod and platform.system() == "Windows":
        if shutil.which("pwsh"):
            return ShellKind.POWERSHELL_7
        return ShellKind.POWERSHELL_5

    # CMD fallback on Windows
    if platform.system() == "Windows" and "cmd.exe" in comspec:
        return ShellKind.CMD

    return ShellKind.UNKNOWN


def _parent_process_name() -> str | None:
    try:
        ppid = os.getppid()
        comm_path = Path(f"/proc/{ppid}/comm")
        if comm_path.exists():
            return comm_path.read_text().strip()
    except (AttributeError, PermissionError, FileNotFoundError):
        pass
    try:
        import psutil  # type: ignore

        return psutil.Process(os.getppid()).name()
    except Exception:
        pass
    return None


def _detect_wsl() -> bool:
    if platform.system() != "Linux":
        return False
    try:
        osrelease = Path("/proc/sys/kernel/osrelease").read_text().lower()
        return "microsoft" in osrelease or "wsl" in osrelease
    except Exception:
        return False


def detect() -> TerminalEnv:
    """Run detection and return a fully-populated TerminalEnv."""
    sys_platform = platform.system()  # "Windows", "Linux", "Darwin"
    surface = _detect_surface()
    shell = _detect_shell()
    in_wsl = _detect_wsl()
    in_vscode = bool(os.getenv("TERM_PROGRAM") == "vscode" or os.getenv("VSCODE_PID"))
    in_docker = bool(Path("/.dockerenv").exists() or os.getenv("DOCKER_CONTAINER"))
    conda_env = os.getenv("CONDA_DEFAULT_ENV")
    venv_path = os.getenv("VIRTUAL_ENV")

    # WSL overrides platform for downstream callers
    if in_wsl:
        shell = ShellKind.BASH  # WSL always has Bash as the base shell

    # Windows-native overrides
    if sys_platform == "Windows":
        line_end = "\r\n"
        clear_cmd = "cls"
        which_cmd = "where"
    else:
        line_end = "\n"
        clear_cmd = "clear"
        which_cmd = "which"

    return TerminalEnv(
        surface=surface,
        shell=shell,
        platform=sys_platform,
        in_vscode=in_vscode,
        in_docker=in_docker,
        in_wsl=in_wsl,
        conda_env=conda_env,
        venv_path=venv_path,
        line_end=line_end,
        clear_cmd=clear_cmd,
        which_cmd=which_cmd,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Shell command adapter
# ──────────────────────────────────────────────────────────────────────────────


class ShellAdapter:
    """Run shell commands in a surface-appropriate way.
    Always returns (stdout: str, stderr: str, returncode: int).
    """

    def __init__(self, env: TerminalEnv | None = None):
        self.env = env or detect()

    def run(self, cmd: str, capture: bool = True) -> tuple[str, str, int]:
        """Execute cmd in the appropriate shell.
        On Windows-native: uses PowerShell or CMD.
        On Unix (Bash/Zsh/WSL): uses /bin/bash or $SHELL.
        """
        if self.env.is_windows_native:
            if self.env.shell in (ShellKind.POWERSHELL_7, ShellKind.POWERSHELL_5):
                exe = (
                    "pwsh" if self.env.shell == ShellKind.POWERSHELL_7 else "powershell"
                )
                full = [exe, "-NoProfile", "-Command", cmd]
            else:
                full = ["cmd", "/C", cmd]
        else:
            shell_exe = os.getenv("SHELL", "/bin/bash")
            full = [shell_exe, "-c", cmd]

        result = subprocess.run(
            full,
            capture_output=capture,
            text=True,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        return stdout, stderr, result.returncode

    def which(self, program: str) -> str | None:
        """Return path to program or None."""
        path = shutil.which(program)
        return path

    def env_var(self, name: str, default: str = "") -> str:
        return os.getenv(name, default)


# ──────────────────────────────────────────────────────────────────────────────
# Human-readable report
# ──────────────────────────────────────────────────────────────────────────────

SHELL_EDUCATION: dict[ShellKind, dict] = {
    ShellKind.POWERSHELL_7: {
        "name": "PowerShell 7 (pwsh)",
        "tagline": "Cross-platform, object-pipeline, modern Windows/Linux/macOS",
        "prompt": "PS C:\\> ",
        "tips": [
            "Objects flow through pipes, not text strings",
            "Cmdlets use Verb-Noun convention (Get-ChildItem, Set-Location)",
            "Scripts are .ps1 files; execution policy may block unsigned scripts",
            "Env vars: $env:PATH, $env:HOME",
            "$PSVersionTable shows version info",
        ],
        "gotchas": [
            "Pipeline output is objects — pipe to | Out-String for text",
            "String escaping uses backtick ` not backslash",
            "Tab completion is context-aware but slow on first run",
        ],
    },
    ShellKind.POWERSHELL_5: {
        "name": "Windows PowerShell 5.1",
        "tagline": "Built-in Windows shell — stable but Windows-only",
        "prompt": "PS C:\\> ",
        "tips": [
            "Same Verb-Noun syntax as PowerShell 7 but Windows-only modules",
            "Comes pre-installed — no download needed",
            "ISE (Integrated Scripting Environment) is its native IDE",
            "Upgrade to pwsh for cross-platform parity",
        ],
        "gotchas": [
            "No cross-platform support — scripts break on Linux",
            "Missing newer cmdlets added in pwsh 7+",
            "Different default encoding than pwsh (use UTF-8 BOM carefully)",
        ],
    },
    ShellKind.CMD: {
        "name": "Command Prompt (cmd.exe)",
        "tagline": "Windows legacy — minimal, DOS-heritage, still ubiquitous",
        "prompt": "C:\\> ",
        "tips": [
            "Batch scripts are .bat / .cmd files",
            "Use %VAR% for environment variables",
            "dir = ls, copy = cp, del = rm, move = mv",
            "Still the fastest shell to launch on Windows",
        ],
        "gotchas": [
            "No pipes between native Unix tools — use Git Bash or WSL instead",
            "Line endings are CRLF (\\r\\n) — Git may warn about this",
            "No tab completion for file paths by default",
            "echo off at the top of batch files to suppress command echoing",
        ],
    },
    ShellKind.GIT_BASH: {
        "name": "Git Bash (MINGW64/MSYS2)",
        "tagline": "Unix-like shell on Windows via MSYS2 — git users' first stop",
        "prompt": "user@HOST MINGW64 ~/repo $ ",
        "tips": [
            "Ships with Git for Windows — already installed if you use git",
            "Supports most Bash syntax and common Unix tools (grep, awk, sed)",
            "Windows paths translated: /c/Users/... = C:\\Users\\...",
            "Use winpty for interactive programs (winpty python, winpty node)",
        ],
        "gotchas": [
            "Not a full Linux env — some tools missing or behave differently",
            "Path translation can surprise: /c/ vs C:\\ in mixed scripts",
            "winpty required for readline-based REPLs (Python, Node)",
            "Slower than PowerShell for large file operations",
        ],
    },
    ShellKind.WSL: {
        "name": "WSL — Windows Subsystem for Linux",
        "tagline": "Real Linux kernel on Windows — best of both worlds",
        "prompt": "user@HOSTNAME:~$ ",
        "tips": [
            "Full Linux userspace — apt, systemd (WSL2), native binaries",
            "Access Windows files at /mnt/c/, /mnt/d/ etc.",
            "Run Windows .exe from Linux: explorer.exe ., code .",
            "WSL2 uses a real VM — faster I/O inside /home/ than /mnt/",
            "Set default distro: wsl --set-default Ubuntu",
        ],
        "gotchas": [
            "File I/O across /mnt/ boundary is slow — keep projects in ~ ",
            "Networking is NATed in WSL2 — different IP from Windows",
            "GUI apps need WSLg (Windows 11) or an X server (Windows 10)",
            "systemd disabled by default in some older WSL2 setups",
        ],
    },
    ShellKind.BASH: {
        "name": "Bash (GNU Bourne Again Shell)",
        "tagline": "The universal Unix shell — default on most Linux distros",
        "prompt": "user@host:~$ ",
        "tips": [
            "POSIX-compliant — scripts run nearly everywhere",
            "~/.bashrc for interactive config, ~/.bash_profile for login shells",
            "Use set -euo pipefail at script top for safety",
            "Ctrl+R for reverse history search",
        ],
        "gotchas": [
            "Arrays are 0-indexed but syntax is quirky: ${arr[@]}",
            "Word splitting on unquoted variables is a common bug source",
            "No async/await — background with & and wait",
            "macOS ships /bin/bash 3.2 (ancient) — install Homebrew bash",
        ],
    },
    ShellKind.ZSH: {
        "name": "Zsh (Z Shell)",
        "tagline": "macOS default since Catalina — powerful, Oh My Zsh ecosystem",
        "prompt": "user@host ~ % ",
        "tips": [
            "Oh My Zsh / Prezto for plugins and themes",
            "Better tab completion and globbing than Bash",
            "~/.zshrc for config; separate ~/.zprofile for login",
            "Backwards compatible with most Bash scripts",
        ],
        "gotchas": [
            "Arrays are 1-indexed (unlike Bash!) — major footgun",
            "setopt KSH_ARRAYS to get 0-indexed behavior",
            "Slower startup than Bash if plugins are heavy",
        ],
    },
}


def print_report(env: TerminalEnv | None = None) -> None:
    env = env or detect()
    edu = SHELL_EDUCATION.get(env.shell, {})
    print(f"\n{'═'*60}")
    print("  TERMINAL ABSTRACTION REPORT")
    print(f"{'═'*60}")
    print(f"  Surface   : {env.surface.value}")
    print(f"  Shell     : {env.shell.value}  ({edu.get('name', '?')})")
    print(f"  Platform  : {env.platform}")
    print(f"  In VS Code: {env.in_vscode}")
    print(f"  In Docker : {env.in_docker}")
    print(f"  In WSL    : {env.in_wsl}")
    if env.conda_env:
        print(f"  Conda env : {env.conda_env}")
    if env.venv_path:
        print(f"  Venv      : {env.venv_path}")
    print()
    if edu:
        print(f"  TAGLINE : {edu['tagline']}")
        print(f"  PROMPT  : {edu.get('prompt','')}")
        print()
        print("  TIPS:")
        for t in edu.get("tips", []):
            print(f"    • {t}")
        print()
        print("  GOTCHAS:")
        for g in edu.get("gotchas", []):
            print(f"    ⚠ {g}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    env = detect()
    print_report(env)
