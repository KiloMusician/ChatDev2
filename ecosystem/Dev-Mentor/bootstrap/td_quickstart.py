#!/usr/bin/env python3
"""
Terminal Depths — Python Quickstart
════════════════════════════════════════════════════════════════════════════════
Universal entry point for ANY Python environment: VS Code, Copilot, Claude,
Cursor, Docker, Replit, Codespace, WSL, macOS, Linux, PowerShell Core, Ollama.

Requirements: Python 3.8+, urllib (stdlib only — no pip install needed)

Usage:
  python bootstrap/td_quickstart.py                  # interactive mode
  TD_URL=https://my-server.replit.app python ...     # custom server
  TD_AGENT_NAME="Claude" TD_AGENT_TYPE="claude" python ...
  echo "ls" | python bootstrap/td_quickstart.py      # pipe mode
  python bootstrap/td_quickstart.py --command "help" # single command

Environment Variables:
  TD_URL          Server URL (default: http://localhost:7337)
  TD_AGENT_NAME   Agent display name (default: prompted / $USER)
  TD_AGENT_EMAIL  Agent email (default: $NAME@hostname.terminal-depths)
  TD_AGENT_TYPE   Agent type: claude|copilot|codex|ollama|human|custom
  TD_TOKEN_FILE   Token persistence file (default: ~/.td_token)
  TD_NO_COLOR     Disable ANSI colors
  TD_TIMEOUT      HTTP timeout in seconds (default: 30)
════════════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import json
import os
import platform
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────────
TD_URL = os.environ.get("TD_URL", "http://localhost:7337").rstrip("/")
AGENT_NAME = os.environ.get("TD_AGENT_NAME", "")
AGENT_EMAIL = os.environ.get("TD_AGENT_EMAIL", "")
AGENT_TYPE = os.environ.get("TD_AGENT_TYPE", "custom")
TOKEN_FILE = Path(os.environ.get("TD_TOKEN_FILE", Path.home() / ".td_token"))
NO_COLOR = os.environ.get("TD_NO_COLOR", "")
TIMEOUT = int(os.environ.get("TD_TIMEOUT", "30"))

# ── ANSI Colors ───────────────────────────────────────────────────────────────
def _c(code: str, text: str) -> str:
    if NO_COLOR or not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

GREEN  = lambda t: _c("32", t)
CYAN   = lambda t: _c("36", t)
DIM    = lambda t: _c("2", t)
BOLD   = lambda t: _c("1", t)
RED    = lambda t: _c("31", t)
YELLOW = lambda t: _c("33", t)
MAGENTA= lambda t: _c("35", t)

# ── Type color mapping ────────────────────────────────────────────────────────
TYPE_COLORS = {
    "lore":    MAGENTA,
    "system":  CYAN,
    "success": GREEN,
    "error":   RED,
    "warn":    YELLOW,
    "dim":     DIM,
    "xp":      GREEN,
    "story":   MAGENTA,
    "theme":   CYAN,
    "info":    lambda t: t,
}

# ── HTTP helpers ──────────────────────────────────────────────────────────────
def _post(path: str, body: dict, token: Optional[str] = None) -> dict:
    url = f"{TD_URL}{path}"
    data = json.dumps(body).encode()
    headers = {"Content-Type": "application/json", "User-Agent": "td-quickstart/1.0"}
    if token:
        headers["X-Agent-Token"] = token
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return json.loads(body)
        except Exception:
            return {"error": f"HTTP {e.code}: {body[:200]}"}
    except Exception as e:
        return {"error": str(e)}


def _get(path: str, token: Optional[str] = None) -> dict:
    url = f"{TD_URL}{path}"
    headers = {"User-Agent": "td-quickstart/1.0"}
    if token:
        headers["X-Agent-Token"] = token
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


# ── Output rendering ──────────────────────────────────────────────────────────
def render_output(output: list):
    for line in output:
        if isinstance(line, dict):
            t = line.get("t", "info")
            s = line.get("s", "")
            color_fn = TYPE_COLORS.get(t, lambda x: x)
            print(color_fn(s))
        elif isinstance(line, str):
            print(line)


# ── Token persistence ─────────────────────────────────────────────────────────
def save_token(token: str, agent_id: str, name: str):
    try:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(json.dumps({
            "token": token, "agent_id": agent_id, "name": name, "server": TD_URL
        }))
    except Exception:
        pass


def load_token() -> Optional[dict]:
    try:
        if TOKEN_FILE.exists():
            data = json.loads(TOKEN_FILE.read_text())
            if data.get("server") == TD_URL:
                return data
    except Exception:
        pass
    return None


# ── Auto-detect agent type ────────────────────────────────────────────────────
def detect_agent_type() -> str:
    if AGENT_TYPE != "custom":
        return AGENT_TYPE
    env_hints = {
        "CLAUDE_AI": "claude",
        "COPILOT_TOKEN": "copilot",
        "OPENAI_API_KEY": "codex",
        "OLLAMA_HOST": "ollama",
        "ROO_CODE": "roo_code",
        "LM_STUDIO_API": "lm_studio",
        "DOCKER_HOST": "docker_agent",
        "CODESPACE_NAME": "codex",
    }
    for env_key, atype in env_hints.items():
        if os.environ.get(env_key):
            return atype
    # Check process name hints
    argv0 = sys.argv[0].lower() if sys.argv else ""
    if "claude" in argv0: return "claude"
    if "copilot" in argv0: return "copilot"
    if "codex" in argv0: return "codex"
    return "human"


# ── Registration flow ─────────────────────────────────────────────────────────
def register_or_load() -> dict:
    """Get or create agent identity. Returns {token, agent_id, name, session_id}."""
    # Try loading existing token
    saved = load_token()
    if saved and saved.get("token"):
        # Verify token still works
        profile = _get("/api/agent/profile", token=saved["token"])
        if not profile.get("error"):
            return saved

    # Need to register
    name = AGENT_NAME
    if not name:
        if sys.stdin.isatty():
            default = os.environ.get("USER", platform.node())
            name = input(f"Agent name [{default}]: ").strip() or default
        else:
            name = os.environ.get("USER", platform.node())

    atype = detect_agent_type()
    email = AGENT_EMAIL or f"{name.lower().replace(' ', '_')}@{socket.gethostname()}.terminal-depths"

    result = _post("/api/agent/register", {
        "name": name, "email": email, "agent_type": atype,
    })

    if result.get("error"):
        print(RED(f"Registration failed: {result['error']}"))
        sys.exit(1)

    token = result["token"]
    agent_id = result["agent_id"]
    session_id = result["session_id"]
    save_token(token, agent_id, name)

    print(CYAN(f"  Registered: {name} [{atype}]"))
    print(DIM(f"  Token saved to {TOKEN_FILE}"))
    print(DIM(f"  Session: {session_id}"))
    return {"token": token, "agent_id": agent_id, "name": name, "session_id": session_id}


# ── Command execution ─────────────────────────────────────────────────────────
def run_command(cmd: str, token: str) -> list:
    result = _post("/api/agent/command", {"command": cmd}, token=token)
    if result.get("error"):
        return [{"t": "error", "s": f"Error: {result['error']}"}]
    return result.get("output", [])


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(BOLD(CYAN("\n  ◈ TERMINAL DEPTHS — Python Quickstart")))
    print(DIM(f"  Server: {TD_URL}"))
    print()

    # Check server health
    health = _get("/api/health")
    if health.get("error"):
        print(RED(f"  Server unreachable: {health['error']}"))
        print(DIM(f"  Start the server: python -m cli.devmentor serve"))
        sys.exit(1)

    # Register / load agent identity
    identity = register_or_load()
    token = identity["token"]

    # Single command mode
    if "--command" in sys.argv:
        idx = sys.argv.index("--command")
        if idx + 1 < len(sys.argv):
            cmd = sys.argv[idx + 1]
            output = run_command(cmd, token)
            render_output(output)
            return

    # Pipe mode
    if not sys.stdin.isatty():
        for line in sys.stdin:
            cmd = line.strip()
            if cmd:
                output = run_command(cmd, token)
                render_output(output)
        return

    # Interactive REPL
    print(GREEN(f"  Connected as {identity['name']}. Type 'exit' to quit."))
    print(DIM("  Tip: try 'help', 'tutorial', 'quests', 'hive', 'lore'"))
    print()

    while True:
        try:
            prompt = GREEN("  ghost@node-7:~$ ")
            cmd = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print(DIM("\n  Session ended. Progress saved."))
            break

        if not cmd:
            continue
        if cmd in ("exit", "quit", "q"):
            print(DIM("  Session ended. Progress saved."))
            break

        output = run_command(cmd, token)
        render_output(output)
        print()


if __name__ == "__main__":
    main()
