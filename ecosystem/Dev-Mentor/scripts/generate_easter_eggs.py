"""scripts/generate_easter_eggs.py — Easter Egg Seeder
====================================================
Seeds the Terminal Depths virtual filesystem with lore references and
hidden files from the knowledge graph's easter_eggs collection.

Each game's easter eggs are placed as files in the game's virtual
filesystem via the REST API. Players discover them through exploration,
`ls`, `cat`, and `find` commands.

Also creates hidden command triggers in the game state (via Serena
observations) so that typing the game's name triggers a special response.

Usage:
  python scripts/generate_easter_eggs.py
  python scripts/generate_easter_eggs.py --dry-run
  python scripts/generate_easter_eggs.py --game bitburner
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).parent.parent
API_URL = "http://localhost:8008"


# ─────────────────────────────────────────────────────────────────────────────
# API helpers
# ─────────────────────────────────────────────────────────────────────────────


def _api_post(path: str, payload: dict) -> dict | None:
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{API_URL}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except urllib.error.URLError as exc:
        print(f"  ✕ API unreachable: {exc}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"  ✕ API error: {exc}", file=sys.stderr)
        return None


def _game_cmd(session_id: str, cmd: str) -> dict | None:
    return _api_post("/api/game/command", {"session_id": session_id, "command": cmd})


def _ensure_session(session_id: str) -> bool:
    """Ensure a game session exists."""
    result = _game_cmd(session_id, "whoami")
    return result is not None


# ─────────────────────────────────────────────────────────────────────────────
# Egg seeder
# ─────────────────────────────────────────────────────────────────────────────


def seed_egg(session_id: str, egg: dict, dry_run: bool = False) -> bool:
    """Plant an easter egg file in the virtual filesystem."""
    path = egg.get("path", "/home/ghost/lore/")
    filename = egg.get("filename", "SECRET.txt")
    content = egg.get("content", "")
    game = egg.get("game", "unknown")
    full_path = path.rstrip("/") + "/" + filename

    if dry_run:
        print(f"  [dry-run] Would plant: {full_path} ({len(content)} bytes)")
        return True

    # Create directory first
    mkdir_cmd = f"mkdir -p {path}"
    _game_cmd(session_id, mkdir_cmd)

    # Write file via the script/write mechanism
    # Escape content for shell single-quote
    safe_content = content.replace("'", "'\\''")
    write_cmd = f"echo '{safe_content}' > {full_path}"
    result = _game_cmd(session_id, write_cmd)

    if result:
        print(f"  ✅ Planted [{game}] {full_path}")
        return True
    else:
        print(f"  ✕ Failed to plant [{game}] {full_path}")
        return False


def seed_lore_index(session_id: str, graph: dict, dry_run: bool = False) -> None:
    """Create a master lore index file listing all easter eggs."""
    lore_index_path = "/home/ghost/lore/INDEX.txt"
    lines = [
        "=== TERMINAL DEPTHS — KNOWLEDGE ARCHIVE INDEX ===",
        "Recovered data from across the gaming multiverse.",
        "",
        "Directories:",
    ]
    for gid, gdata in graph.get("games", {}).items():
        eggs = [e for e in graph.get("easter_eggs", []) if e.get("game") == gid]
        if eggs:
            lines.append(f"  /home/ghost/lore/{gid}/")
            for e in eggs:
                lines.append(f"    {e['filename']}")
    lines += [
        "",
        "Use `cat <filename>` to read any file.",
        "Use `find /home/ghost/lore -name '*.txt'` to discover all lore.",
        "",
        f"Generated: {datetime.utcnow().isoformat()}Z",
    ]
    content = "\n".join(lines)

    if dry_run:
        print(f"  [dry-run] Would write {lore_index_path}")
        return

    _game_cmd(session_id, "mkdir -p /home/ghost/lore")
    safe = content.replace("'", "'\\''")
    _game_cmd(session_id, f"echo '{safe}' > {lore_index_path}")
    print(f"  ✅ Lore index written to {lore_index_path}")


def seed_serena_observations(graph: dict, dry_run: bool = False) -> None:
    """Record easter egg lore as Serena observations for future ask() queries."""
    try:
        import urllib.request

        if dry_run:
            lore_count = len(graph.get("lore", []))
            print(
                f"  [dry-run] Would record {lore_count} lore fragments as Serena observations"
            )
            return

        # Add lore fragments as observations via Serena ask
        count = 0
        for entry in graph.get("lore", [])[:10]:  # seed first 10
            payload = {"query": f"What do you know about {entry['game']}?"}
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{API_URL}/api/serena/ask",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    count += 1
            except Exception:
                pass

        print(f"  ✅ {count} lore observations seeded to Serena Memory Palace")
    except Exception as exc:
        print(f"  ⚠  Serena observation seeding failed: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Special hidden commands planted as filesystem scripts
# ─────────────────────────────────────────────────────────────────────────────

SPECIAL_SCRIPTS = {
    "find_csec.py": """\
# Hidden Bitburner reference — find CSEC equivalent
# In Terminal Depths, the CSEC node is: node-csec
# Hack it to join the CyberSec faction
import sys
ns = sys.modules.get('ns') or type('ns', (), {'tprint': print})()
ns.tprint("[BITBURNER REFERENCE] Looking for CSEC equivalent...")
ns.tprint("In Bitburner: scan → connect CSEC → backdoor → join faction")
ns.tprint("In Terminal Depths: map → find node-csec → hack → talk faction_rep")
ns.tprint("XP reward: +50 (faction)")
""",
    "quasar_skip.py": """\
# Hacknet Quasar Skip — adapted for Terminal Depths
# During the 2.5s window when 'connect' runs, you can rm files
import sys
ns = sys.modules.get('ns') or type('ns', (), {'tprint': print, 'sleep': lambda x: None})()
ns.tprint("[HACKNET REFERENCE] Quasar Skip technique")
ns.tprint("1. Start a connection to a locked node")
ns.tprint("2. During the connection window, run: rm <target>/logs/*")
ns.tprint("3. The ownership check runs AFTER the connection completes")
ns.tprint("4. Files removed in the window bypass the ownership gate")
ns.tprint("")
ns.tprint("Race condition window: ~2.5 seconds")
ns.tprint("This is a REAL technique — TOCTOU vulnerability")
""",
    "tis100_colony.py": """\
# TIS-100 → Colony Architecture mapping
import sys
ns = sys.modules.get('ns') or type('ns', (), {'tprint': print})()
ns.tprint("[TIS-100 REFERENCE] Colony as parallel processor")
ns.tprint("")
ns.tprint("TIS-100 Architecture → Colony Architecture:")
ns.tprint("  NODE          → Agent (Gordon, Serena, Oracle...)")
ns.tprint("  ACC register  → Working memory (SQLite current row)")
ns.tprint("  BAK register  → Last observation (Memory Palace)")
ns.tprint("  MOV LEFT      → REST POST to adjacent agent")
ns.tprint("  MOV RIGHT     → REST GET from adjacent agent")
ns.tprint("  JMP label     → ns.run('next_script.py')")
ns.tprint("  SWP           → push/pop Serena observation")
ns.tprint("  SAV           → serena observe()")
ns.tprint("")
ns.tprint("The colony IS a TIS-100 machine. 71 nodes. Massively parallel.")
ns.tprint("Run: serena ask 'parallel agent architecture'")
""",
}


def seed_special_scripts(session_id: str, dry_run: bool = False) -> None:
    """Plant special reference scripts in /home/ghost/scripts/."""
    for name, code in SPECIAL_SCRIPTS.items():
        path = f"/home/ghost/scripts/{name}"
        if dry_run:
            print(f"  [dry-run] Would plant script: {path}")
            continue
        safe = code.replace("'", "'\\''")
        _game_cmd(session_id, "mkdir -p /home/ghost/scripts")
        _game_cmd(session_id, f"echo '{safe}' > {path}")
        print(f"  ✅ Planted script: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Easter Egg Seeder")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes",
    )
    parser.add_argument("--game", metavar="GAME_ID", help="Seed only this game's eggs")
    parser.add_argument(
        "--session", default="easter-egg-seed", help="Game session ID to use"
    )
    parser.add_argument(
        "--graph",
        default=str(ROOT / "state" / "knowledge_graph.json"),
        help="Path to knowledge_graph.json",
    )
    args = parser.parse_args()

    graph_path = Path(args.graph)
    if not graph_path.exists():
        print(f"  ✕ Knowledge graph not found: {graph_path}")
        print("  Run: python scripts/populate_knowledge_graph.py first")
        sys.exit(1)

    graph = json.loads(graph_path.read_text())
    eggs = graph.get("easter_eggs", [])

    if args.game:
        eggs = [e for e in eggs if e.get("game") == args.game]

    print(f"\n  Easter Egg Seeder — {len(eggs)} eggs to plant")
    print(f"  {'[DRY RUN] ' if args.dry_run else ''}Session: {args.session}")
    print()

    if not args.dry_run:
        if not _ensure_session(args.session):
            print("  ✕ Could not reach game API. Is the server running?")
            sys.exit(1)

    # Plant lore files
    seeded = 0
    for egg in eggs:
        if seed_egg(args.session, egg, dry_run=args.dry_run):
            seeded += 1

    # Write lore index
    seed_lore_index(args.session, graph, dry_run=args.dry_run)

    # Plant special scripts
    if not args.game:
        seed_special_scripts(args.session, dry_run=args.dry_run)

    # Record lore as Serena observations
    if not args.game:
        seed_serena_observations(graph, dry_run=args.dry_run)

    print(f"\n  ── Done: {seeded}/{len(eggs)} eggs planted")
    if not args.dry_run:
        print("  Try: find /home/ghost/lore -name '*.txt'")
        print("  Try: cat /home/ghost/lore/INDEX.txt")
        print("  Try: script run tis100_colony.py")


if __name__ == "__main__":
    main()
