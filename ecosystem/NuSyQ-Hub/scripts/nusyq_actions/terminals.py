"""terminals — Terminal awareness CLI action.

Usage (via start_nusyq.py):
    python scripts/start_nusyq.py terminals            # show status
    python scripts/start_nusyq.py terminals assign     # auto-assign PIDs to roles
    python scripts/start_nusyq.py terminals emit       # send test messages
    python scripts/start_nusyq.py terminals channels   # show output channels

Direct usage:
    python scripts/nusyq_actions/terminals.py [command]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))


def _get_registry():
    from src.system.terminal_pid_registry import get_registry

    return get_registry()


def cmd_status(args: list[str]) -> int:
    """Show current terminal registry and output channel status."""
    from src.system.agent_awareness import awareness_report, get_snapshot

    print(awareness_report())
    snap = get_snapshot(refresh=True)
    print(f"\nRegistry path: {_REPO_ROOT / 'state' / 'terminal_pid_registry.json'}")
    print(f"Log directory: {_REPO_ROOT / 'data' / 'terminal_logs'}")
    active = snap["active_terminal_count"]
    total = len(snap["terminals"])
    print(f"\nActive terminals: {active}/{total}")
    return 0


def cmd_assign(args: list[str]) -> int:
    """Auto-assign live pwsh.exe PIDs to terminal roles in order."""
    reg = _get_registry()
    entries = reg.auto_assign()
    print(f"✓ Assigned {len(entries)} terminal roles")
    print()
    print(reg.status_table())
    print()
    print("Next step: run the startup command in each terminal:")
    print()
    for role, cmd in reg.get_startup_commands().items():
        print(f"  [{role}]  {cmd}")
    return 0


def cmd_emit(args: list[str]) -> int:
    """Send a test message to every agent terminal to verify wiring."""
    from src.system.agent_awareness import emit
    from src.system.terminal_pid_registry import TERMINAL_ROLES

    msg = " ".join(args) if args else "NuSyQ terminal awareness test — agents can reach you!"
    count = 0
    for role in TERMINAL_ROLES:
        ok = emit(role, msg, level="INFO", source="terminal_test")
        if ok:
            count += 1
    print(f"✓ Test message written to {count}/{len(TERMINAL_ROLES)} terminal log files")
    print("  If watchers are running, you should see output appear in each terminal.")
    return 0


def cmd_channels(args: list[str]) -> int:
    """Show all output channels (OpenClaw, SkyClaw, guild events, etc.)."""
    from src.system.agent_awareness import _probe_output_channels

    channels = _probe_output_channels()
    print("OUTPUT CHANNELS\n" + "=" * 60)
    for name, info in channels.items():
        status_icon = "●" if info.get("status") == "online" else "○"
        url_or_path = info.get("url") or info.get("path", "")
        print(f"  {status_icon}  {name:<20}  [{info['type']:<12}]  {info.get('status', '?')}")
        print(f"       {url_or_path}")
        print(f"       {info.get('description', '')}")
        print()
    return 0


def cmd_startup_scripts(args: list[str]) -> int:
    """Print the PowerShell startup command for each registered terminal."""
    reg = _get_registry()
    if not reg.entries:
        print("No terminals registered. Run: python scripts/start_nusyq.py terminals assign")
        return 1
    print("TERMINAL STARTUP COMMANDS\n" + "=" * 60)
    for role, cmd in reg.get_startup_commands().items():
        entry = reg.entries.get(role)
        pid = entry.pid if entry else "?"
        print(f"\n[{role}]  (pid={pid})")
        print(f"  {cmd}")
    return 0


def cmd_map(args: list[str]) -> int:
    """Show the full agent → terminal channel mapping."""
    reg = _get_registry()
    channel_map = reg.get_channel_map()
    print("AGENT → TERMINAL CHANNEL MAP\n" + "=" * 70)
    seen_roles: set[str] = set()
    for _agent, info in sorted(channel_map.items()):
        role = info["role"]
        if role in seen_roles:
            continue
        seen_roles.add(role)
        status = info["status"]
        pid = str(info["pid"]) if info["pid"] else "——"
        icon = "●" if status == "active" else "○"
        agents_in_role = [a for a, i in channel_map.items() if i["role"] == role]
        agents_str = ", ".join(sorted(agents_in_role)[:4])
        if len(agents_in_role) > 4:
            agents_str += f" +{len(agents_in_role) - 4}"
        print(f"  {icon} {role:<22} pid={pid:<7} {status:<12}  → {agents_str}")
    return 0


_COMMANDS = {
    "status": cmd_status,
    "assign": cmd_assign,
    "emit": cmd_emit,
    "channels": cmd_channels,
    "startup": cmd_startup_scripts,
    "map": cmd_map,
}


def handle_terminals(args: list[str]) -> int:
    """Entry point called from start_nusyq.py."""
    sub = args[0] if args else "status"
    remaining = args[1:]
    fn = _COMMANDS.get(sub)
    if fn is None:
        print(f"Unknown subcommand '{sub}'. Available: {', '.join(_COMMANDS)}")
        return 1
    return fn(remaining)


if __name__ == "__main__":
    sys.exit(handle_terminals(sys.argv[1:]))
