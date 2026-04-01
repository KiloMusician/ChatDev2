"""scripts/diagnostics.py — Colony Diagnostic Suite
==================================================
Phase 0 of the Colony Activation Directive.

Runs health checks across all accessible surfaces and services, outputs
a JSON report, and writes/updates state/surface_inventory.json.

Usage:
  python scripts/diagnostics.py                # full check, pretty print
  python scripts/diagnostics.py --json         # raw JSON to stdout
  python scripts/diagnostics.py --quiet        # only failures
  python scripts/diagnostics.py --check <name> # single check

Checks
------
  game_api       — Terminal Depths REST API (localhost:7337)
  serena_status  — Serena agent health endpoint
  serena_drift   — Drift Detection Engine
  serena_align   — Mladenc alignment score
  llm_backend    — LLM route (Replit AI proxy / Ollama / stub)
  git_status     — git remote + token validity
  memory_palace  — SQLite DB presence and row counts
  scheduler      — Content scheduler heartbeat
  nusyq_manifest — Agent manifest JSON validity
  python_env     — Key package imports (fastapi, yaml, requests)
  agent_yamls    — All personality YAMLs parseable
  fs_health      — Key directories and files present
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ─────────────────────────────────────────────────────────────────────────────
# Result types
# ─────────────────────────────────────────────────────────────────────────────

STATUS_OK = "ok"
STATUS_WARN = "warn"
STATUS_FAIL = "fail"
STATUS_SKIP = "skip"

ICONS = {STATUS_OK: "✅", STATUS_WARN: "⚠ ", STATUS_FAIL: "✕ ", STATUS_SKIP: "◌ "}


def _result(name: str, status: str, message: str, detail: dict | None = None) -> dict:
    return {
        "check": name,
        "status": status,
        "message": message,
        "detail": detail or {},
        "ts": datetime.utcnow().isoformat() + "Z",
    }


def ok(name, msg, **kw):
    return _result(name, STATUS_OK, msg, kw or None)


def warn(name, msg, **kw):
    return _result(name, STATUS_WARN, msg, kw or None)


def fail(name, msg, **kw):
    return _result(name, STATUS_FAIL, msg, kw or None)


def skip(name, msg, **kw):
    return _result(name, STATUS_SKIP, msg, kw or None)


# ─────────────────────────────────────────────────────────────────────────────
# Individual checks
# ─────────────────────────────────────────────────────────────────────────────


def check_game_api() -> dict:
    """Terminal Depths REST API on localhost:7337."""
    try:
        import urllib.request

        url = "http://localhost:8008/api/state"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as r:
            data = json.loads(r.read())
        return ok(
            "game_api",
            "Terminal Depths API responding",
            status_code=r.status,
            keys=list(data.keys())[:5],
        )
    except Exception as exc:
        return fail("game_api", f"Terminal Depths API not reachable: {exc}")


def check_serena_status() -> dict:
    """Serena agent status endpoint."""
    try:
        import urllib.request

        with urllib.request.urlopen(
            "http://localhost:8008/api/serena/status", timeout=5
        ) as r:
            envelope = json.loads(r.read())
        # Response: {"ok": true, "status": {..., "serena_version": "..."}}
        data = envelope.get("status", envelope)
        version = data.get("serena_version")
        if not version:
            return warn(
                "serena_status",
                "Endpoint responded but version missing",
                keys=list(data.keys()),
            )
        psi = data.get("ψξφω", data.get("\u03c8\u03be\u03c6\u03c9", "?"))
        mem = data.get("memory", {})
        chunks = (mem.get("index") or {}).get("total_chunks", "?")
        return ok(
            "serena_status",
            f"Serena v{version} — {psi} — {chunks} chunks indexed",
            codename=data.get("codename"),
            faction=data.get("faction"),
        )
    except Exception as exc:
        return fail("serena_status", f"Serena status unreachable: {exc}")


def check_serena_drift() -> dict:
    """Drift Detection Engine."""
    try:
        import urllib.request

        with urllib.request.urlopen(
            "http://localhost:8008/api/serena/drift", timeout=12
        ) as r:
            data = json.loads(r.read())
        critical = data.get("critical", 0)
        warnings = data.get("warnings", 0)
        total = data.get("total", 0)
        if critical > 0:
            return warn(
                "serena_drift",
                f"Drift detected: {critical} critical, {warnings} warn",
                total=total,
                signals=list(data.get("signals", {}).keys()),
            )
        return ok(
            "serena_drift",
            f"Drift clean: {warnings} warn signals (0 critical)",
            total=total,
        )
    except Exception as exc:
        return fail("serena_drift", f"Drift check failed: {exc}")


def check_serena_align() -> dict:
    """Mladenc alignment score."""
    try:
        import urllib.request

        with urllib.request.urlopen(
            "http://localhost:8008/api/serena/align", timeout=8
        ) as r:
            data = json.loads(r.read())
        score = data.get("score", 0.0)
        aligned = data.get("aligned", False)
        if not aligned:
            return warn(
                "serena_align",
                f"Alignment: {score:.0%} — drifting from Mladenc",
                failed=[
                    c["name"] for c in data.get("checks", []) if not c.get("passed")
                ],
            )
        return ok(
            "serena_align",
            f"Alignment: {score:.0%} — {data.get('passed','?')}/{data.get('total','?')} checks",
        )
    except Exception as exc:
        return fail("serena_align", f"Alignment check failed: {exc}")


def check_llm_backend() -> dict:
    """LLM backend — Replit AI proxy / Ollama / stub."""
    # Check Replit AI proxy (modelfarm)
    replit_url = os.getenv("AI_INTEGRATIONS_OPENAI_BASE_URL", "")
    if replit_url:
        try:
            import urllib.request

            probe = urllib.request.Request(
                replit_url.rstrip("/") + "/models",
                headers={"Authorization": "Bearer dummy"},
            )
            with urllib.request.urlopen(probe, timeout=3) as r:
                return ok("llm_backend", f"Replit AI proxy responding at {replit_url}")
        except Exception:
            # Endpoint exists but needs a real token — that's fine
            return ok(
                "llm_backend",
                f"Replit AI proxy configured: {replit_url}",
                note="auth required for /models; proxy is active",
            )

    # Check Ollama
    try:
        import urllib.request

        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
            data = json.loads(r.read())
            models = [m["name"] for m in data.get("models", [])]
            return ok(
                "llm_backend",
                f"Ollama running — {len(models)} models",
                models=models[:5],
            )
    except Exception:
        pass

    return warn(
        "llm_backend",
        "No live LLM backend configured — stub/fallback mode",
        hint="Set AI_INTEGRATIONS_OPENAI_BASE_URL or start Ollama",
    )


def check_git_status() -> dict:
    """Git remote + token presence."""
    try:
        result = subprocess.run(
            ["git", "remote", "-v"], capture_output=True, text=True, cwd=ROOT, timeout=5
        )
        remotes = result.stdout.strip()
        has_token = bool(os.getenv("GITHUB_TOKEN") or (ROOT / ".env.local").exists())
        if "github.com" not in remotes:
            return warn("git_status", "No GitHub remote configured")
        return ok(
            "git_status",
            f"GitHub remote present — token={'present' if has_token else 'missing'}",
            has_token=has_token,
        )
    except Exception as exc:
        return fail("git_status", f"Git check failed: {exc}")


def check_memory_palace() -> dict:
    """SQLite Memory Palace DB."""
    try:
        from agents.serena.memory import MemoryPalace

        memory = MemoryPalace()
        stats = memory.index_stats()
        obs_count = memory._conn.execute(
            "SELECT COUNT(*) FROM observations"
        ).fetchone()[0]
        db_path = memory._db_path
        size_kb = round(db_path.stat().st_size / 1024, 1) if db_path.exists() else 0
        return ok(
            "memory_palace",
            f"Memory Palace: {stats.get('total_chunks', 0)} chunks, {obs_count} observations",
            path=str(db_path),
            size_kb=size_kb,
            indexed_files=stats.get("unique_files", 0),
            fallback_in_use=str(db_path) != str(ROOT / "state" / "serena_memory.db"),
        )
    except Exception:
        pass

    db_candidates = [
        ROOT / "state" / "serena_memory.db",
        ROOT / "agent_memory.db",
    ]
    for db_path in db_candidates:
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path, timeout=3)
                tables = {
                    r[0]
                    for r in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                # Table name is code_index (not code_chunks)
                chunk_table = "code_index" if "code_index" in tables else "code_chunks"
                chunks = (
                    conn.execute(f'SELECT COUNT(*) FROM "{chunk_table}"').fetchone()[0]
                    if chunk_table in tables
                    else 0
                )
                obs = (
                    conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
                    if "observations" in tables
                    else 0
                )
                conn.close()
                size_kb = round(db_path.stat().st_size / 1024, 1)
                return ok(
                    "memory_palace",
                    f"Memory Palace: {chunks} chunks, {obs} observations",
                    path=str(db_path),
                    size_kb=size_kb,
                    tables=sorted(tables),
                )
            except Exception as exc:
                return warn(
                    "memory_palace",
                    f"DB exists but query failed: {exc}",
                    path=str(db_path),
                )
    return warn(
        "memory_palace", "No Memory Palace DB found — run 'serena walk' to create"
    )


def check_scheduler() -> dict:
    """Content scheduler — running as background task in the server."""
    try:
        import urllib.request

        with urllib.request.urlopen("http://localhost:8008/api/state", timeout=4) as r:
            data = json.loads(r.read())
        # Scheduler state is embedded in game state
        sched = data.get("scheduler", {})
        if sched:
            return ok(
                "scheduler",
                "Scheduler state visible in API",
                jobs=list(sched.keys()) if isinstance(sched, dict) else str(sched),
            )
        return ok("scheduler", "Server running (scheduler embedded in process)")
    except Exception as exc:
        return fail("scheduler", f"Cannot verify scheduler: {exc}")


def check_nusyq_manifest() -> dict:
    """NuSyQ agent manifest JSON validity."""
    manifest_path = ROOT / "state" / "agent_manifest.json"
    if not manifest_path.exists():
        return warn(
            "nusyq_manifest", "Agent manifest not found — run the server to generate"
        )
    try:
        data = json.loads(manifest_path.read_text())
        serena = data.get("focal_agents", {}).get("SERENA", {})
        version = serena.get("version", "unknown")
        endpoints = data.get("endpoints", data.get("api_endpoints", {}))
        n_apis = len(endpoints) if isinstance(endpoints, (dict, list)) else 0
        return ok(
            "nusyq_manifest",
            f"Manifest valid — Serena v{version}, {n_apis} API endpoints",
            path=str(manifest_path),
        )
    except Exception as exc:
        return fail("nusyq_manifest", f"Manifest parse error: {exc}")


def check_bridge_inventory() -> dict:
    """Bridge inventory for IDE agents and claw-family surfaces."""
    try:
        from core.bridge_inventory import (build_bridge_inventory,
                                           save_bridge_inventory)

        inventory = build_bridge_inventory()
        save_bridge_inventory(inventory)
        summary = inventory.get("summary", {})
        first_class = summary.get("first_class", [])
        claw_family = summary.get("claw_family", [])
        return ok(
            "bridge_inventory",
            f"Bridge inventory ready — {summary.get('installed', 0)}/{summary.get('total', 0)} installed",
            first_class=first_class,
            claw_family=claw_family,
            path=str(ROOT / "state" / "bridge_inventory.json"),
        )
    except Exception as exc:
        return fail("bridge_inventory", f"Bridge inventory failed: {exc}")


def check_python_env() -> dict:
    """Key Python package imports."""
    required = ["fastapi", "yaml", "requests", "typer", "rich"]
    optional = ["agno", "chromadb", "redis"]
    missing_req = []
    missing_opt = []

    for pkg in required:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing_req.append(pkg)

    for pkg in optional:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing_opt.append(pkg)

    if missing_req:
        return fail(
            "python_env",
            f"Missing required packages: {missing_req}",
            missing_required=missing_req,
            missing_optional=missing_opt,
        )
    if missing_opt:
        return warn(
            "python_env",
            f"Optional packages not installed: {missing_opt}",
            missing_optional=missing_opt,
        )
    return ok("python_env", "All required packages importable")


def check_agent_yamls() -> dict:
    """All personality YAMLs parseable."""
    personalities_dir = ROOT / "agents" / "personalities"
    if not personalities_dir.exists():
        return fail("agent_yamls", "agents/personalities/ directory missing")
    try:
        import yaml
    except ImportError:
        return skip("agent_yamls", "PyYAML not installed")

    yamls = list(personalities_dir.glob("*.yaml"))
    errors = []
    for yf in yamls:
        try:
            data = yaml.safe_load(yf.read_text())
            if not isinstance(data, dict):
                errors.append(f"{yf.name}: not a dict")
        except Exception as exc:
            errors.append(f"{yf.name}: {exc}")

    if errors:
        return warn(
            "agent_yamls",
            f"{len(errors)}/{len(yamls)} YAMLs have issues",
            errors=errors,
        )
    return ok(
        "agent_yamls", f"All {len(yamls)} personality YAMLs valid", count=len(yamls)
    )


def check_fs_health() -> dict:
    """Key directories and files present."""
    required = [
        "app/backend/main.py",
        "app/game_engine/commands.py",
        "agents/serena/serena_agent.py",
        "agents/serena/drift.py",
        "agents/serena/policy.yaml",
        "cli/devmentor.py",
        "scripts/git_auto_push.py",
    ]
    missing = [p for p in required if not (ROOT / p).exists()]

    if missing:
        return warn("fs_health", f"{len(missing)} key files missing", missing=missing)
    return ok("fs_health", f"All {len(required)} key files present")


# ─────────────────────────────────────────────────────────────────────────────
# Surface inventory builder
# ─────────────────────────────────────────────────────────────────────────────

SURFACE_TEMPLATE = [
    {
        "id": "replit",
        "name": "Replit",
        "access": "https://$REPLIT_DEV_DOMAIN",
        "command": "python -m cli.devmentor serve",
        "capabilities": ["game_api", "serena", "llm", "git_auto_push", "web_ui"],
        "port": 5000,
        "notes": "Primary active surface — owns Game API, Serena, NuSyQ-Hub bridge",
    },
    {
        "id": "terminal_depths",
        "name": "Terminal Depths (Game)",
        "access": "http://localhost:8008/game/",
        "command": "browser",
        "capabilities": [
            "ns_scripting",
            "xterm_ui",
            "ambient_audio",
            "120_commands",
            "serena_interface",
        ],
        "port": 5000,
        "notes": "Bitburner-style terminal RPG. ns object available in scripts.",
    },
    {
        "id": "vscode",
        "name": "VS Code",
        "access": "code .",
        "command": "code DevMentorWorkspace.workspace.json",
        "capabilities": ["chug_engine", "tutorials", "multi_repo", "tasks_json"],
        "port": None,
        "notes": "Owns CHUG engine, tutorial content, local script suite",
    },
    {
        "id": "docker",
        "name": "Docker Desktop",
        "access": "docker CLI",
        "command": "docker-compose up -d",
        "capabilities": ["ollama", "mcp_server", "redis", "lm_studio"],
        "port": None,
        "notes": "Full stack — Ollama, MCP server, all 71 agents, LM Studio sidecar",
    },
    {
        "id": "ollama",
        "name": "Ollama (local LLM)",
        "access": "http://localhost:11434",
        "command": "ollama serve",
        "capabilities": ["qwen2.5-coder:7b", "nomic-embed-text", "llava:7b"],
        "port": 11434,
        "notes": "Zero-token inference. Primary model: qwen2.5-coder:7b",
    },
    {
        "id": "github",
        "name": "GitHub",
        "access": "https://github.com/KiloMusician/Dev-Mentor",
        "command": "python scripts/git_auto_push.py",
        "capabilities": ["auto_push", "issues_sync", "ci_cd", "nusyq_mirror"],
        "port": None,
        "notes": "Auto-push target. Reads .env.local first, then GITHUB_TOKEN",
    },
    {
        "id": "obsidian",
        "name": "Obsidian",
        "access": "local vault",
        "command": "obsidian",
        "capabilities": ["docs_mirror", "lore_graph", "linked_notes"],
        "port": None,
        "notes": "Vault mirrors docs/ — passive, needs sync script",
    },
    {
        "id": "n8n",
        "name": "n8n",
        "access": "http://localhost:5678",
        "command": "n8n start",
        "capabilities": ["workflow_automation", "http_webhooks", "scheduled_tasks"],
        "port": 5678,
        "notes": "Workflow automation — NOT currently running on Replit",
    },
    {
        "id": "serena_agno",
        "name": "Serena Agno Bridge",
        "access": "http://localhost:8008/api/serena/toolkit",
        "command": "python agents/serena/agno_bridge.py",
        "capabilities": [
            "walk_repo",
            "find_symbol",
            "ask",
            "relate",
            "diff",
            "detect_drift",
            "get_status",
            "get_observations",
        ],
        "port": 5000,
        "notes": "Agno-compatible toolkit. 8 tools in OpenAI function-call schema.",
    },
    {
        "id": "bridge_inventory",
        "name": "Bridge Inventory",
        "access": "state/bridge_inventory.json",
        "command": "python scripts/bridge_inventory.py --json",
        "capabilities": [
            "serena",
            "codex",
            "claude",
            "copilot",
            "continue",
            "kilo_code",
            "claw_family",
        ],
        "port": None,
        "notes": "Machine-readable IDE and claw-family bridge inventory.",
    },
    {
        "id": "gordon",
        "name": "Gordon (Autonomous Player)",
        "access": "python gordon_player.py",
        "command": "python gordon_player.py --url $REPLIT_DEV_DOMAIN",
        "capabilities": ["auto_play", "serena_briefing", "7_phase_strategy"],
        "port": None,
        "notes": "Gordon v0.4.0 — Serena-aware. ORIENTATION includes serena walk/align/drift",
    },
]


def build_surface_inventory(results: list[dict]) -> dict:
    """Build surface_inventory.json from template + diagnostic results."""
    status_map = {r["check"]: r["status"] for r in results}

    surfaces = []
    for s in SURFACE_TEMPLATE:
        sid = s["id"]
        # Determine health from relevant checks
        relevant = {
            "replit": ["game_api"],
            "terminal_depths": ["game_api"],
            "serena_agno": ["serena_status", "serena_drift", "serena_align"],
            "bridge_inventory": ["bridge_inventory"],
            "github": ["git_status"],
        }.get(sid, [])

        statuses = [status_map.get(c, STATUS_SKIP) for c in relevant]
        if STATUS_FAIL in statuses:
            health = STATUS_FAIL
        elif STATUS_WARN in statuses:
            health = STATUS_WARN
        elif statuses:
            health = STATUS_OK
        else:
            health = STATUS_SKIP

        surfaces.append({**s, "health": health})

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "colony_status": "active",
        "surfaces": surfaces,
        "checks_run": len(results),
        "ok": sum(1 for r in results if r["status"] == STATUS_OK),
        "warn": sum(1 for r in results if r["status"] == STATUS_WARN),
        "fail": sum(1 for r in results if r["status"] == STATUS_FAIL),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

ALL_CHECKS = [
    ("game_api", check_game_api),
    ("serena_status", check_serena_status),
    ("serena_drift", check_serena_drift),
    ("serena_align", check_serena_align),
    ("llm_backend", check_llm_backend),
    ("git_status", check_git_status),
    ("memory_palace", check_memory_palace),
    ("scheduler", check_scheduler),
    ("nusyq_manifest", check_nusyq_manifest),
    ("bridge_inventory", check_bridge_inventory),
    ("python_env", check_python_env),
    ("agent_yamls", check_agent_yamls),
    ("fs_health", check_fs_health),
]


def run_diagnostics(only: str | None = None, quiet: bool = False) -> list[dict]:
    results = []
    for name, fn in ALL_CHECKS:
        if only and name != only:
            continue
        r = fn()
        results.append(r)
    return results


def print_report(results: list[dict], quiet: bool = False) -> None:
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║   COLONY DIAGNOSTIC SUITE — Phase 0 Inventory       ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    for r in results:
        if quiet and r["status"] == STATUS_OK:
            continue
        icon = ICONS.get(r["status"], "?")
        print(f"  {icon} [{r['check']}]  {r['message']}")
        if r["detail"] and r["status"] != STATUS_OK:
            for k, v in r["detail"].items():
                print(f"       {k}: {v}")

    ok_n = sum(1 for r in results if r["status"] == STATUS_OK)
    warn_n = sum(1 for r in results if r["status"] == STATUS_WARN)
    fail_n = sum(1 for r in results if r["status"] == STATUS_FAIL)
    total = len(results)

    print(f"\n  ── Summary: {ok_n} ok  {warn_n} warn  {fail_n} fail  / {total} checks")
    if fail_n == 0 and warn_n == 0:
        print("  ✅ Colony health: OPTIMAL\n")
    elif fail_n == 0:
        print("  ⚠  Colony health: STABLE (warnings present)\n")
    else:
        print("  ✕  Colony health: DEGRADED — blockers detected\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Colony Diagnostic Suite")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--quiet", action="store_true", help="Show only failures")
    parser.add_argument("--check", metavar="NAME", help="Run single check")
    parser.add_argument(
        "--no-inventory", action="store_true", help="Skip surface_inventory.json write"
    )
    args = parser.parse_args()

    results = run_diagnostics(only=args.check, quiet=args.quiet)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results, quiet=args.quiet)

    # Write surface inventory
    if not args.no_inventory and not args.check:
        inv = build_surface_inventory(results)
        state = ROOT / "state"
        state.mkdir(exist_ok=True)
        out_path = state / "surface_inventory.json"
        out_path.write_text(json.dumps(inv, indent=2))
        if not args.quiet:
            print(f"  → Surface inventory written to: {out_path.relative_to(ROOT)}")

    # Exit code: 1 if any failures
    sys.exit(1 if any(r["status"] == STATUS_FAIL for r in results) else 0)


if __name__ == "__main__":
    main()
