#!/usr/bin/env python3
"""Unified Orchestrator CLI

Subcommands:
- queue: Show unified quest queue summary
- todo: Print current sprint/todo status
- zeta: Summarize ZETA progress tracker
- guild: Render board-style summary from quest log
- culture-ship: Run Culture Ship commands (health-only|dry-run|apply)
- away: Put system in overnight safe mode + generate unified receipts

All subcommands emit a JSON receipt to state/receipts/cli/<cmd>_YYYYMMDD_HHMMSS.json
"""

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

# Use script location to resolve repo root (parent of scripts/)
REPO_ROOT = Path(__file__).resolve().parent.parent
RECEIPTS_DIR = REPO_ROOT / "state" / "receipts" / "cli"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIARY_LOG = REPO_ROOT / "data" / "terminal_logs" / "intermediary.log"


def _write_receipt(cmd: str, payload: dict[str, Any]) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = RECEIPTS_DIR / f"{cmd}_{ts}.json"
    payload.setdefault("timestamp", datetime.now().isoformat())
    payload.setdefault("command", cmd)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"✓ CLI receipt: {out}")
    return out


def cmd_queue(args: argparse.Namespace) -> None:
    """Show unified quest queue summary."""
    # Reuse unified quest viewer logic via script
    quest_file = REPO_ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    total = 0
    types: dict[str, int] = {}
    statuses: dict[str, int] = {}
    recent: list[dict[str, Any]] = []
    if quest_file.exists():
        with open(quest_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    q = json.loads(line)
                    total += 1
                    t = q.get("type", "unknown")
                    s = q.get("status", "unknown")
                    types[t] = types.get(t, 0) + 1
                    statuses[s] = statuses.get(s, 0) + 1
                    recent.append(q)
                except json.JSONDecodeError:
                    continue
    recent = sorted(recent, key=lambda q: q.get("timestamp", ""), reverse=True)[: args.limit]

    payload = {
        "summary": {
            "total_quests": total,
            "by_type": types,
            "by_status": statuses,
        },
        "recent": recent,
    }
    _write_receipt("queue", payload)

    print(f"Total quests: {total}")
    for k, v in sorted(types.items(), key=lambda x: -x[1]):
        print(f"  type {k}: {v}")
    for k, v in sorted(statuses.items(), key=lambda x: -x[1]):
        print(f"  status {k}: {v}")


def cmd_todo(_args: argparse.Namespace) -> None:
    """Print current sprint/todo status from sprint_log.jsonl."""
    sprint_log = REPO_ROOT / "state" / "sprint_log.jsonl"
    sprints: list[dict[str, Any]] = []
    if sprint_log.exists():
        with open(sprint_log, encoding="utf-8") as f:
            for line in f:
                try:
                    sprints.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    payload = {"sprints": sprints[-10:], "count": len(sprints)}
    _write_receipt("todo", payload)
    print(f"Sprints recorded: {len(sprints)}")


def cmd_zeta(_args: argparse.Namespace) -> None:
    """Summarize ZETA progress tracker."""
    zeta_path = REPO_ROOT / "config" / "ZETA_PROGRESS_TRACKER.json"
    if not zeta_path.exists():
        print("❌ ZETA tracker not found")
        _write_receipt("zeta", {"status": "missing"})
        return
    with open(zeta_path, encoding="utf-8") as f:
        data = json.load(f)
    phases = data.get("phases", {})
    counts: dict[str, int] = {}
    for _ph_key, ph_val in phases.items():
        tasks = ph_val.get("tasks", [])
        for t in tasks:
            status = t.get("status", "unknown")
            counts[status] = counts.get(status, 0) + 1
    payload = {"project": data.get("project"), "phase_counts": counts}
    _write_receipt("zeta", payload)
    print(f"Project: {data.get('project')} | Status counts: {counts}")


def cmd_guild(args: argparse.Namespace) -> None:
    """Render a simple board summary from quests (columns by status).

    Optional: --snapshot to write markdown file to docs/Agent-Sessions/
    """
    quest_file = REPO_ROOT / "src" / "Rosetta_Quest_System" / "quest_log.jsonl"
    board: dict[str, int] = {
        "pending": 0,
        "in_progress": 0,
        "suggested": 0,
        "completed": 0,
        "unknown": 0,
    }
    quests_by_status: dict[str, list[dict[str, Any]]] = {
        "pending": [],
        "in_progress": [],
        "suggested": [],
        "completed": [],
        "unknown": [],
    }

    if quest_file.exists():
        with open(quest_file, encoding="utf-8") as f:
            for line in f:
                try:
                    q = json.loads(line)
                    s = q.get("status", "unknown")
                    if s not in board:
                        s = "unknown"
                    board[s] += 1
                    quests_by_status[s].append(q)
                except json.JSONDecodeError:
                    pass

    payload = {"board": board}
    _write_receipt("guild", payload)

    print("Guild Board:")
    for col, cnt in board.items():
        print(f"  {col}: {cnt}")

    # Optional: Write markdown snapshot
    write_snapshot = getattr(args, "guild_snapshot", False)
    if write_snapshot:
        snapshot_path = (
            REPO_ROOT
            / "docs"
            / "Agent-Sessions"
            / f"GUILD_BOARD_SNAPSHOT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)

        # Build markdown content
        lines = [
            "# Guild Board Snapshot",
            f"\nGenerated: {datetime.now().isoformat()}",
            "\n## Summary",
            "\n| Status | Count |",
            "|--------|-------|",
        ]

        for col in ["pending", "in_progress", "suggested", "completed", "unknown"]:
            cnt = board[col]
            lines.append(f"| {col} | {cnt} |")

        # Add recent completions if any
        if quests_by_status["completed"]:
            lines.append("\n## Recent Completions")
            recent_completed = sorted(
                quests_by_status["completed"], key=lambda q: q.get("timestamp", ""), reverse=True
            )[:5]
            for q in recent_completed:
                title = q.get("title", "Untitled")
                ts = q.get("timestamp", "")
                lines.append(f"- **{title}** ({ts})")

        # Add in-progress items
        if quests_by_status["in_progress"]:
            lines.append("\n## Currently In Progress")
            for q in quests_by_status["in_progress"][:10]:
                title = q.get("title", "Untitled")
                lines.append(f"- {title}")

        content = "\n".join(lines)
        with open(snapshot_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"\n✓ Guild Board snapshot: {snapshot_path}")


def cmd_intermediary(args: argparse.Namespace) -> None:
    """High-level call into AI Intermediary.handle().

    Examples:
      python scripts/orchestrator_cli.py intermediary --text "Route to module" --module dummy
      python scripts/orchestrator_cli.py intermediary --text "Ask Ollama" --ollama
    """
    import asyncio
    import sys

    sys.path.insert(0, str(REPO_ROOT))  # ensure src import works when launched from elsewhere
    from src.ai.ai_intermediary import AIIntermediary, AISecurityError, CognitiveParadigm

    async def run() -> dict[str, Any]:
        interm = AIIntermediary()
        await interm.initialize()

        # Optional ad-hoc module registration
        if args.module:

            class Passthrough:
                async def process(self, payload):
                    return f"{args.module}:{payload}"

            await interm.register_module(args.module, Passthrough(), CognitiveParadigm.CODE_ANALYSIS)

        target_paradigm = CognitiveParadigm[args.target_paradigm.upper()] if args.target_paradigm else None
        event = await interm.handle(
            input_data=args.text,
            context={"conversation_id": args.conversation or "cli_intermediary"},
            source="cli",
            paradigm=CognitiveParadigm[args.paradigm.upper()],
            target_module=args.module,
            target_paradigm=target_paradigm,
            use_ollama=args.ollama,
        )
        return {
            "event_id": event.event_id,
            "payload": event.payload,
            "paradigm": event.paradigm.value,
            "tags": event.tags,
            "context": event.context,
        }

    try:
        result = asyncio.run(run())
        _write_receipt("intermediary", {"status": "ok", "result": result})
        print(json.dumps(result, indent=2, default=str))

        # Emit to intermediary terminal for visibility
        INTERMEDIARY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with INTERMEDIARY_LOG.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "ts": datetime.now().isoformat(),
                        "channel": "intermediary",
                        "level": "info",
                        "message": f"CLI intermediary call payload={result.get('payload')}",
                        "meta": {"tags": result.get("tags")},
                    }
                )
                + "\n"
            )
    except AISecurityError as e:
        _write_receipt("intermediary", {"status": "security_error", "detail": str(e)})
        print(f"❌ Security error: {e}")
    except Exception as e:
        _write_receipt("intermediary", {"status": "error", "detail": str(e)})
        print(f"❌ Error: {e}")


def cmd_culture_ship(args: argparse.Namespace) -> None:
    """Run Culture Ship CLI with chosen mode (health-only|dry-run|apply).

    Maps friendly mode names to start_nusyq.py culture_ship flags:
    - health-only → --health-only (lightweight dependency probe)
    - dry-run → --dry-run (audit/fix analysis without applying)
    - apply → --apply (run fix pipeline)
    """
    mode = getattr(args, "cs_mode", None) or "dry-run"

    # Map friendly mode names to start_nusyq.py flags
    mode_map = {
        "health": "--health-only",
        "health-only": "--health-only",
        "dry": "--dry-run",
        "dry-run": "--dry-run",
        "apply": "--apply",
    }
    flag = mode_map.get(mode.lower())
    if not flag:
        print(f"❌ Unknown Culture Ship mode: {mode}")
        print("   Valid modes: health-only, dry-run, apply")
        _write_receipt(
            "culture_ship",
            {
                "mode": mode,
                "status": "error",
                "error": f"Unknown mode: {mode}",
            },
        )
        return

    cmd = ["python", "scripts/start_nusyq.py", "culture_ship", flag]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(REPO_ROOT),
            check=False,
        )
        status = "success" if result.returncode == 0 else "error"
        payload = {
            "mode": mode,
            "flag": flag,
            "status": status,
            "stdout": result.stdout[-1500:],
            "stderr": result.stderr[-1500:],
            "exit_code": result.returncode,
        }
        _write_receipt("culture_ship", payload)
        print(f"✓ Culture Ship run ({mode}): {status}")
        if result.returncode != 0:
            print(f"  Exit code: {result.returncode}")
            if result.stderr:
                print(f"  Error output:\n{result.stderr[-500:]}")
    except subprocess.TimeoutExpired:
        _write_receipt(
            "culture_ship",
            {
                "mode": mode,
                "status": "timeout",
                "error": "Culture Ship run exceeded 300s timeout",
            },
        )
        print(f"❌ Culture Ship timeout (300s) on mode: {mode}")
    except OSError as e:
        _write_receipt(
            "culture_ship",
            {
                "mode": mode,
                "status": "os_error",
                "error": str(e),
            },
        )
        print(f"❌ Culture Ship OS error: {e}")


def cmd_sessions(_args: argparse.Namespace) -> None:
    """Show aggregated session logs across all repos."""
    try:
        result = subprocess.run(
            ["python", "scripts/unified_session_aggregator.py"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(REPO_ROOT),
            check=False,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"❌ Session aggregator error: {e}")


def cmd_diff_viewer(args: argparse.Namespace) -> None:
    """Show uncommitted changes across all repos."""
    since_commit = getattr(args, "diff_since_commit", None)

    cmd = ["python", "scripts/multi_repo_diff.py"]
    if since_commit:
        cmd.append(f"--since-commit={since_commit}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT), check=False)
        payload = {
            "status": "success" if result.returncode == 0 else "error",
            "since_commit": since_commit,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
        _write_receipt("diff_viewer", payload)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except (subprocess.TimeoutExpired, OSError) as e:
        _write_receipt("diff_viewer", {"status": "error", "error": str(e)})
        print(f"❌ Diff viewer error: {e}")


def cmd_next_actions(_args: argparse.Namespace) -> None:
    """Show suggested next actions from the roadmap."""
    try:
        result = subprocess.run(
            ["python", "scripts/start_nusyq.py", "next_action"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(REPO_ROOT),
            check=False,
        )
        status = "success" if result.returncode == 0 else "error"
        payload = {
            "status": status,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-500:],
            "exit_code": result.returncode,
        }
        _write_receipt("next_actions", payload)
        print("🎯 Next Actions from Roadmap:")
        print(result.stdout)
        if result.returncode != 0 and result.stderr:
            print(f"Warning: {result.stderr[-200:]}")
    except subprocess.TimeoutExpired:
        _write_receipt("next_actions", {"status": "timeout", "error": "next_action exceeded 30s"})
        print("❌ Next actions lookup timed out (30s)")
    except OSError as e:
        _write_receipt("next_actions", {"status": "error", "error": str(e)})
        print(f"❌ Next actions error: {e}")


def cmd_nav(args: argparse.Namespace) -> None:
    """Navigate between repos or list repo paths."""
    repo = getattr(args, "nav_repo", None)
    pwd_only = getattr(args, "nav_pwd", False)

    cmd = ["python", "scripts/cross_repo_navigator.py"]
    if repo:
        cmd.append(repo)
        if pwd_only:
            cmd.append("--pwd")
    else:
        cmd.append("list")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=str(REPO_ROOT), check=False)
        payload = {
            "repo": repo or "list",
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
        if not pwd_only:
            _write_receipt("nav", payload)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except (subprocess.TimeoutExpired, OSError) as e:
        payload = {
            "repo": repo or "list",
            "status": "error",
            "error": str(e),
        }
        _write_receipt("nav", payload)
        print(f"❌ Navigation error: {e}")


def cmd_away(_args: argparse.Namespace) -> None:
    """Overnight safe mode snapshot + unified health + knowledge sync."""
    actions: list[dict[str, Any]] = []
    # 1) Overnight snapshot
    try:
        r = subprocess.run(
            ["python", "scripts/start_nusyq.py", "--mode", "overnight"],
            capture_output=True,
            text=True,
            timeout=90,
            cwd=str(REPO_ROOT),
            check=False,
        )
        actions.append(
            {
                "overnight_snapshot": "ok" if r.returncode == 0 else "error",
                "stdout": r.stdout[-500:],
                "stderr": r.stderr[-500:],
            }
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        actions.append({"overnight_snapshot": "exception", "error": str(e)})
    # 2) Unified health check
    try:
        r = subprocess.run(
            ["python", "scripts/unified_health_check.py"],
            capture_output=True,
            text=True,
            timeout=90,
            cwd=str(REPO_ROOT),
            check=False,
        )
        actions.append(
            {
                "unified_health": "ok" if r.returncode == 0 else "error",
                "stdout": r.stdout[-500:],
                "stderr": r.stderr[-500:],
            }
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        actions.append({"unified_health": "exception", "error": str(e)})
    # 3) Knowledge sync
    try:
        r = subprocess.run(
            ["python", "scripts/sync_knowledge_base.py"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(REPO_ROOT),
            check=False,
        )
        actions.append(
            {
                "knowledge_sync": "ok" if r.returncode == 0 else "error",
                "stdout": r.stdout[-500:],
                "stderr": r.stderr[-500:],
            }
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        actions.append({"knowledge_sync": "exception", "error": str(e)})

    payload = {"status": "completed", "actions": actions}
    _write_receipt("away", payload)
    print("✓ Away mode complete: overnight snapshot + unified health + knowledge sync")


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified Orchestrator CLI")
    sub = parser.add_subparsers(dest="cmd")

    p_queue = sub.add_parser("queue", help="Show unified quest queue summary")
    p_queue.add_argument("--limit", type=int, default=10)
    p_queue.set_defaults(func=cmd_queue)

    p_todo = sub.add_parser("todo", help="Print current sprint/todo status")
    p_todo.set_defaults(func=cmd_todo)

    p_zeta = sub.add_parser("zeta", help="Summarize ZETA progress tracker")
    p_zeta.set_defaults(func=cmd_zeta)

    p_guild = sub.add_parser("guild", help="Render guild board summary")
    p_guild.add_argument(
        "--snapshot",
        dest="guild_snapshot",
        action="store_true",
        help="Write markdown snapshot to docs/Agent-Sessions/",
    )
    p_guild.set_defaults(func=cmd_guild)

    p_cs = sub.add_parser("culture-ship", help="Run Culture Ship CLI (health-only|dry-run|apply)")
    p_cs.add_argument(
        "cs_mode",
        nargs="?",
        default="dry-run",
        help="Mode: health-only, dry-run, apply (default: dry-run)",
    )
    p_cs.set_defaults(func=cmd_culture_ship)

    p_away = sub.add_parser("away", help="Overnight safe mode + receipts")
    p_away.set_defaults(func=cmd_away)

    p_nav = sub.add_parser("nav", help="Navigate between repos (hub|simverse|root)")
    p_nav.add_argument("nav_repo", nargs="?", help="Repo to navigate to (hub, simverse, root) or 'list' for all")
    p_nav.add_argument("--pwd", dest="nav_pwd", action="store_true", help="Print path only (suitable for eval)")
    p_nav.set_defaults(func=cmd_nav)

    p_next = sub.add_parser("next-actions", help="Show suggested next actions from roadmap")
    p_next.set_defaults(func=cmd_next_actions)

    p_sessions = sub.add_parser("sessions", help="Show aggregated session logs from all repos")
    p_sessions.set_defaults(func=cmd_sessions)

    p_intermediary = sub.add_parser("intermediary", help="Call AI Intermediary.handle()")
    p_intermediary.add_argument("--text", required=True, help="Input text/payload")
    p_intermediary.add_argument(
        "--paradigm",
        default="natural_language",
        help="Input paradigm (matches CognitiveParadigm enum name)",
    )
    p_intermediary.add_argument(
        "--target-paradigm",
        help="Translate output to this paradigm (enum name)",
    )
    p_intermediary.add_argument("--module", help="Target module name (auto-registered passthrough if provided)")
    p_intermediary.add_argument("--ollama", action="store_true", help="Process via Ollama instead of module")
    p_intermediary.add_argument("--conversation", help="Conversation ID for context memory (default: cli_intermediary)")
    p_intermediary.set_defaults(func=cmd_intermediary)

    p_diff = sub.add_parser("diff-viewer", help="Show uncommitted changes across all repos")
    p_diff.add_argument("--since-commit", dest="diff_since_commit", help="Show changes since specific commit")
    p_diff.set_defaults(func=cmd_diff_viewer)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
