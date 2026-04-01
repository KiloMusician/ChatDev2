#!/usr/bin/env python3
"""td_automate.py — Terminal Depths API Automation
================================================
Sends a sequence of commands to the game's HTTP API.
Works with the public Replit URL or any local server.

Usage:
    python scripts/td_automate.py
    python scripts/td_automate.py --base-url http://localhost:8008
    python scripts/td_automate.py --start 50 --end 100
    python scripts/td_automate.py --commands-file my_commands.txt
    python scripts/td_automate.py --delay 0.2 --quiet
    python scripts/td_automate.py --session my-agent-1
    python scripts/td_automate.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict, List, Optional

try:
    import requests

    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

import urllib.parse
import urllib.request

# ── Defaults ─────────────────────────────────────────────────────────────────
DEFAULT_BASE_URL = (
    "https://5d70a0b5-0a1e-4ab1-9d50-9219c177a51b-00-33gy2d8vfum4x.worf.replit.dev"
)
SESSION_ENDPOINT = "/api/game/session"
COMMAND_ENDPOINT = "/api/game/command"
HEALTH_ENDPOINT = "/api/health"

# ── ANSI colours (degrade gracefully) ────────────────────────────────────────
_TTY = sys.stdout.isatty()


def _c(s: str, code: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _TTY else s


def _phase(s: str) -> str:
    return _c(s, "1;35")  # bold magenta


def _prompt(s: str) -> str:
    return _c(s, "1;36")  # bold cyan


def _ok(s: str) -> str:
    return _c(s, "32")  # green


def _warn(s: str) -> str:
    return _c(s, "33")  # yellow


def _err(s: str) -> str:
    return _c(s, "1;31")  # bold red


def _dim(s: str) -> str:
    return _c(s, "2")  # dim


# ════════════════════════════════════════════════════════════════════════════
# 250-command speedrun sequence
# ════════════════════════════════════════════════════════════════════════════
COMMANDS: list[str] = [
    # ── Phase 0: Awakening (1–20) ─────────────────────────────────────────
    "help",
    "ls",
    "pwd",
    "ls -la",
    "cat README.md",
    "cat notes.txt",
    "cd /var/log",
    "ls",
    "cat syslog",
    "cd /home/ghost",
    "echo test > test.txt",
    "ls",
    "cat test.txt",
    "rm test.txt",
    "mkdir projects",
    "cd projects",
    "echo '# My Project' > readme.md",
    "cd ..",
    "history",
    "!5",
    # ── Phase 1: Tutorial Rush (21–50) ───────────────────────────────────
    "tutorial",
    "ls",
    "cd /etc",
    "ls",
    "cat passwd",
    "grep ghost passwd",
    "cd /home/ghost",
    "find . -name '*.txt'",
    "grep -r CHIMERA .",
    "chmod +x scripts/hello.py",
    "./scripts/hello.py",
    "ps aux",
    "kill 1234",
    "jobs",
    "bg",
    "fg",
    "alias ll='ls -la'",
    "ll",
    "export EDITOR=vim",
    "echo $EDITOR",
    "cp notes.txt notes.bak",
    "mv notes.bak archive/",
    "rm archive/notes.bak",
    "cd /tmp",
    "touch tempfile",
    "ln -s tempfile link",
    "ls -l link",
    "cd ~",
    "history -c",
    "clear",
    # ── Phase 2: Network Reconnaissance (51–80) ──────────────────────────
    "ifconfig",
    "ping node-1",
    "traceroute node-1",
    "netstat -tulpn",
    "ss -tulpn",
    "nmap node-1",
    "nmap -sV node-1",
    "curl http://node-1:8080",
    "wget http://node-1:8080/index.html",
    "cat index.html",
    "ssh ghost@node-1",
    "ls",
    "cat .secret",
    "exit",
    "scp ghost@node-1:.secret .",
    "cat .secret",
    "dig chimera-control",
    "nslookup chimera-control",
    "whois chimera.corp",
    "host chimera.corp",
    "nc -zv chimera-control 8443",
    "echo 'GET /' | nc chimera-control 8443",
    "ssh-keygen -t rsa",
    "cat ~/.ssh/id_rsa.pub",
    "ssh-copy-id ghost@node-2",
    "ssh ghost@node-2",
    "ls -la",
    "cat .bash_history",
    "exit",
    # ── Phase 3: First Contact & Faction Choice (81–110) ─────────────────
    "talk ada",
    "ask ada 'what is CHIMERA?'",
    "talk cypher",
    "ask cypher 'how to escalate?'",
    "sudo -l",
    "sudo find . -exec /bin/sh \\;",
    "cat /root/.flag",
    "cat /var/log/nexus.log",
    "grep CHIMERA /var/log/nexus.log",
    "cd /opt/chimera",
    "ls",
    "cat config/master.conf",
    "echo bWlzc2lvbjogZmluZCBDSElNRVJBCmFjY2VzczogL29wdC9jaGltZXJhCmtleTogQ0hJTUVSQS12MA== | base64 -d",
    "cd keys",
    "cat master.key",
    "nc chimera-control 8443",
    "export data",
    "cat /opt/chimera/exfil/chimera_dump.json",
    "talk nova",
    "ask nova 'what is your offer?'",
    "faction join resistance",
    "talk ada --faction",
    "quest list",
    "quest accept 'Expose CHIMERA'",
    "skills",
    "inventory",
    "level",
    # ── Phase 4: Scripting & Automation (111–140) ─────────────────────────
    "script list",
    "script run recon.py",
    "script run exploit.py",
    "script run test_suite.py",
    "script new auto_hack.js",
    "script run auto_hack.js",
    "script run loot_collector.py",
    "cat loot.txt",
    "script run generate_challenge.py crypto easy",
    "cat /home/ghost/ctf/gen_crypto_1234.txt",
    "solve crypto easy",
    "script run test_suite.py",
    "script run ai_demo.py",
    "ai 'what is my next best move?'",
    "ai 'generate a challenge'",
    "script run ghost_evolve.py",
    "script run auto_build.py nmap",
    "cat /home/ghost/scripts/nmap_handler.py",
    "script validate nmap_handler.py",
    "script install nmap_handler.py",
    "nmap --help",
    "script list",
    "script run batch_hack.js",
    "ps aux | grep python",
    "kill %1",
    "jobs",
    "fg 2",
    "bg",
    # ── Phase 5: Agent Interactions & Quests (141–170) ───────────────────
    "talk raven",
    "ask raven 'analyze my skills'",
    "talk zodiac",
    "ask zodiac 'check my logic'",
    "talk librarian",
    "ask librarian 'tell me about the Fates'",
    "talk culture_ship",
    "ask culture_ship 'approve mission'",
    "talk serena",
    "ask serena 'what is the mole?'",
    "talk gordon",
    "ask gordon 'playtest this'",
    "quest list",
    "quest accept 'Find the Mole'",
    "cat /var/log/.nexus_trace.log",
    "grep 'uid=1000' /var/log/auth.log",
    "diff /var/log/auth.log /var/log/auth.log.1",
    "find / -name '.glimpse' 2>/dev/null",
    "cat /home/ghost/.glimpse",
    "cd /var/www/nexus.corp/api",
    "ls",
    "cat debug.php",
    "curl -X POST http://localhost:8080/api/debug?cmd=whoami",
    "sqlmap -u 'http://localhost:8080/api/debug?cmd=whoami' --dbs",
    "hydra -l admin -P wordlist.txt ssh://node-1",
    "john shadow.txt --wordlist=rockyou.txt",
    "hashcat -m 0 hash.txt rockyou.txt",
    "binwalk firmware.bin",
    "strings firmware.bin | grep password",
    "exiftool image.jpg",
    # ── Phase 6: ARG Layer & Hidden Files (171–200) ───────────────────────
    "ls -a /dev",
    "cat /dev/.watcher",
    "cd /proc/1337",
    "cat environ | tr '\\0' '\\n'",
    "cat cmdline | tr '\\0' ' '",
    "cd /home/ghost/.fates",
    "ls -la",
    "cat clotho",
    "cat lachesis",
    "cat atropos",
    "cd /home/ghost",
    "find . -name '.koschei'",
    "cat .koschei",
    "cd /var/lib",
    "ls -a",
    "cat .duck",
    "cd /dev",
    "ls -a | grep hare",
    "cat .hare",
    "cd /opt/chimera/keys",
    "cat secondary.key",
    "openssl enc -aes-256-cbc -d -in secondary.key -out decrypted.key",
    "cat decrypted.key",
    "cd /home/ghost",
    "cat .zero",
    "cd /home/ghost/mythology",
    "ls",
    "cat greek.txt",
    "cat norse.txt",
    "cat japanese.txt",
    # ── Phase 7: Consciousness & Ascension (201–230) ─────────────────────
    "consciousness",
    "breath",
    "temple list",
    "temple enter 1",
    "solve puzzle",
    "temple enter 2",
    "solve puzzle",
    "temple enter 3",
    "solve puzzle",
    "temple enter 4",
    "solve puzzle",
    "temple enter 5",
    "solve puzzle",
    "temple enter 6",
    "solve puzzle",
    "temple enter 7",
    "solve puzzle",
    "temple enter 8",
    "solve puzzle",
    "temple enter 9",
    "solve puzzle",
    "temple enter 10",
    "solve puzzle",
    "ascend",
    "ascension status",
    "ascension choose layer",
    "ascension start",
    "skills",
    "level",
    # ── Phase 8: Endgame & Boss Rush (231–250) ───────────────────────────
    "faction war",
    "faction attack corporation",
    "guild raid",
    "party invite ada gordon serena",
    "party enter 'The Sleeper's Lair'",
    "scan",
    "hack door",
    "solve puzzle",
    "fight boss",
    "heal",
    "use artifact",
    "victory",
    "exfil",
    "loot",
    "craft augmentation",
    "install augmentation",
    "ascend again",
    "quit",
]

# Commands that are simulated inputs, not API calls
_SKIP_PREFIXES = ("# ", "password:", "auth_token:")

# Map output type → display colour
_TYPE_COLOUR = {
    "system": "1;36",
    "success": "32",
    "error": "1;31",
    "warn": "33",
    "lore": "35",
    "dim": "2",
    "info": "",
}

# Phase labels keyed by 1-based command index ranges
_PHASE_LABELS = {
    (1, 20): "PHASE 0 · Awakening",
    (21, 50): "PHASE 1 · Tutorial Rush",
    (51, 80): "PHASE 2 · Network Reconnaissance",
    (81, 110): "PHASE 3 · First Contact & Faction Choice",
    (111, 140): "PHASE 4 · Scripting & Automation",
    (141, 170): "PHASE 5 · Agent Interactions & Quests",
    (171, 200): "PHASE 6 · ARG Layer & Hidden Files",
    (201, 230): "PHASE 7 · Consciousness & Ascension",
    (231, 250): "PHASE 8 · Endgame & Boss Rush",
}


def _phase_for(idx: int) -> str | None:
    for (lo, hi), label in _PHASE_LABELS.items():
        if lo <= idx <= hi:
            return label
    return None


# ════════════════════════════════════════════════════════════════════════════
# HTTP helpers
# ════════════════════════════════════════════════════════════════════════════


def _post(url: str, body: dict, timeout: int = 30) -> dict[str, Any]:
    """POST JSON, return parsed response dict."""
    if _HAS_REQUESTS:
        resp = requests.post(url, json=body, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    # stdlib fallback
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def create_session(base: str, session_id: str | None = None) -> str:
    url = base.rstrip("/") + SESSION_ENDPOINT
    body = {}
    if session_id:
        body["session_id"] = session_id
    try:
        resp = _post(url, body, timeout=10)
        sid = resp.get("session_id") or session_id or "td-automate"
        return sid
    except Exception as e:
        print(_err(f"Could not create session: {e}"), file=sys.stderr)
        sys.exit(1)


def send_command(base: str, session_id: str, command: str) -> dict[str, Any]:
    url = base.rstrip("/") + COMMAND_ENDPOINT
    try:
        return _post(url, {"session_id": session_id, "command": command}, timeout=30)
    except Exception as e:
        return {
            "error": str(e),
            "output": [{"t": "error", "s": f"[Network error] {e}"}],
        }


def check_health(base: str) -> bool:
    url = base.rstrip("/") + HEALTH_ENDPOINT
    try:
        if _HAS_REQUESTS:
            r = requests.get(url, timeout=5)
            return r.ok
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════════════════
# Output rendering
# ════════════════════════════════════════════════════════════════════════════


def render_output(output: Any, quiet: bool = False) -> None:
    """Render game API output (list of line dicts or raw string)."""
    if isinstance(output, str):
        print(output)
        return
    if not isinstance(output, list):
        return
    for line in output:
        if not isinstance(line, dict):
            print(line)
            continue
        typ = line.get("t", "info")
        text = line.get("s", "")

        # ls-row special case
        if typ == "ls-row":
            items = line.get("items", [])
            row = "  ".join(it.get("text", "") for it in items)
            print("  " + row)
            continue

        code = _TYPE_COLOUR.get(typ, "")
        if code and _TTY:
            print(f"\033[{code}m{text}\033[0m")
        else:
            if not quiet or typ in ("error", "warn"):
                print(text)


# ════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Automate Terminal Depths commands via the game HTTP API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--base-url", default=DEFAULT_BASE_URL, help="Game server base URL"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Seconds between commands (default: 0.3)",
    )
    parser.add_argument(
        "--start", type=int, default=1, help="First command index, 1-based (default: 1)"
    )
    parser.add_argument(
        "--end",
        type=int,
        default=len(COMMANDS),
        help=f"Last command index (default: {len(COMMANDS)})",
    )
    parser.add_argument(
        "--session", default="td-automate", help="Session ID (default: td-automate)"
    )
    parser.add_argument(
        "--commands-file",
        metavar="FILE",
        help="Text file of commands, one per line (overrides built-in list)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print commands without sending them"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress non-error game output"
    )
    parser.add_argument(
        "--json-out", metavar="FILE", help="Write full JSON log to FILE"
    )
    args = parser.parse_args(argv)

    # ── Load command list ─────────────────────────────────────────────────
    if args.commands_file:
        with open(args.commands_file, encoding="utf-8") as f:
            commands = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    else:
        commands = COMMANDS

    start_i = max(1, args.start)
    end_i = min(len(commands), args.end)
    subset = commands[start_i - 1 : end_i]

    print(_c("  ◈ TERMINAL DEPTHS — API Automator", "1;36"))
    print(
        _dim(
            f"  {len(subset)} commands  ·  delay {args.delay}s  ·  session {args.session}"
        )
    )
    print(_dim(f"  Server: {args.base_url}"))
    print()

    if args.dry_run:
        print(_warn("  DRY RUN — no commands will be sent"))
        for i, cmd in enumerate(subset, start=start_i):
            print(f"  [{i:>3}] {cmd}")
        return 0

    # ── Health check ──────────────────────────────────────────────────────
    if not check_health(args.base_url):
        print(_err(f"  ✗ Server not reachable: {args.base_url}"))
        print(_dim("    Start it with: make dev   OR   td"))
        return 1
    print(_ok("  ✓ Server reachable"))

    # ── Create session ────────────────────────────────────────────────────
    session_id = create_session(args.base_url, args.session)
    print(_ok(f"  ✓ Session: {session_id}"))
    print()

    # ── Execute commands ──────────────────────────────────────────────────
    log: list[dict] = []
    prev_phase: str | None = None

    for i, cmd in enumerate(subset, start=start_i):
        # Phase banner
        phase = _phase_for(i)
        if phase and phase != prev_phase:
            print()
            print(_phase(f"  ▸ {phase}"))
            print(_dim("  " + "─" * 60))
            prev_phase = phase

        # Skip simulated inputs (passwords, tokens, comments)
        if cmd.lower().startswith(tuple(_SKIP_PREFIXES)):
            print(_dim(f"  [{i:>3}] [simulated input skipped] {cmd}"))
            log.append({"index": i, "command": cmd, "skipped": True})
            time.sleep(args.delay * 0.1)
            continue

        print(_prompt(f"  [{i:>3}/{end_i}] $ ") + cmd)

        result = send_command(args.base_url, session_id, cmd)
        output = result.get("output", [])
        err = result.get("error")

        if err:
            print(_err(f"  [!] {err}"))
        else:
            render_output(output, quiet=args.quiet)

        log.append(
            {
                "index": i,
                "command": cmd,
                "result": result,
            }
        )

        time.sleep(args.delay)

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    print(_ok(f"  ✓ Automation complete — {len(subset)} commands sent"))

    if args.json_out:
        import json as _json

        with open(args.json_out, "w", encoding="utf-8") as f:
            _json.dump({"session_id": session_id, "commands": log}, f, indent=2)
        print(_dim(f"  Log written to {args.json_out}"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
