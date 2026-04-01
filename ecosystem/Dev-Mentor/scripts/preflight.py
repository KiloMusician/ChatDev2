#!/usr/bin/env python3
"""scripts/preflight.py — Terminal Depths System Preflight

Runs at server startup (called from main.py) to:
  1. Check all required Python packages and install missing ones
  2. Initialize all SQLite databases
  3. Verify Replit AI / LLM connectivity
  4. Warm up Serena index if under-populated
  5. Create required directory structure

Safe to run multiple times — fully idempotent.

Usage:
    python3 scripts/preflight.py               # print report
    python3 scripts/preflight.py --silent      # exit 0/1 only
    python3 scripts/preflight.py --auto-fix    # pip install missing pkgs
"""
from __future__ import annotations

import importlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ── Required packages (import_name, pip_name, critical) ─────────────────────
PACKAGES = [
    ("fastapi", "fastapi", True),
    ("uvicorn", "uvicorn[standard]", True),
    ("pydantic", "pydantic", True),
    ("yaml", "pyyaml", True),
    ("rich", "rich", True),
    ("typer", "typer", True),
    ("aiofiles", "aiofiles", True),
    ("websockets", "websockets", True),
    ("jwt", "PyJWT", True),
    ("openai", "openai", False),
    ("requests", "requests", False),
    ("httpx", "httpx", False),
    ("redis", "redis", False),
    ("aiohttp", "aiohttp", False),
]

# ── SQLite databases to initialise ──────────────────────────────────────────
DATABASES: dict[str, str] = {
    "state/agents.db": """
        CREATE TABLE IF NOT EXISTS agent_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            session_id TEXT,
            role TEXT DEFAULT 'assistant',
            content TEXT NOT NULL,
            ts REAL DEFAULT (unixepoch('now')),
            tags TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_agent_memory_agent ON agent_memory(agent_id);
    """,
    "state/lattice.db": """
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT UNIQUE NOT NULL,
            label TEXT,
            kind TEXT DEFAULT 'generic',
            properties TEXT DEFAULT '{}',
            created_at REAL DEFAULT (unixepoch('now'))
        );
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            src TEXT NOT NULL,
            dst TEXT NOT NULL,
            relation TEXT DEFAULT 'related',
            weight REAL DEFAULT 1.0
        );
    """,
    "state/economy.db": """
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            delta INTEGER NOT NULL,
            reason TEXT,
            ts REAL DEFAULT (unixepoch('now'))
        );
    """,
    "state/gordon_memory.db": """
        CREATE TABLE IF NOT EXISTS gordon_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phase TEXT,
            action TEXT,
            result TEXT,
            ts REAL DEFAULT (unixepoch('now'))
        );
    """,
    "state/model_registry.db": """
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            backend TEXT DEFAULT 'replit',
            status TEXT DEFAULT 'registered',
            metadata TEXT DEFAULT '{}'
        );
    """,
    "state/llm_cache.db": """
        CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_hash TEXT UNIQUE NOT NULL,
            response TEXT NOT NULL,
            model TEXT,
            ts REAL DEFAULT (unixepoch('now'))
        );
    """,
}

# ── Required directories ─────────────────────────────────────────────────────
REQUIRED_DIRS = [
    "state",
    "sessions",
    "logs",
    "var",
    "var/devlog",
]


def _check_packages(auto_fix: bool = False) -> list[dict]:
    results = []
    for imp, pip_name, critical in PACKAGES:
        try:
            importlib.import_module(imp)
            results.append({"name": pip_name, "status": "ok", "critical": critical})
        except ImportError:
            if auto_fix:
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", "-q", pip_name],
                        timeout=120,
                    )
                    importlib.import_module(imp)
                    results.append(
                        {"name": pip_name, "status": "installed", "critical": critical}
                    )
                except Exception as e:
                    results.append(
                        {
                            "name": pip_name,
                            "status": f"install_failed: {e}",
                            "critical": critical,
                        }
                    )
            else:
                results.append(
                    {"name": pip_name, "status": "missing", "critical": critical}
                )
    return results


def _init_directories() -> list[str]:
    created = []
    for d in REQUIRED_DIRS:
        p = ROOT / d
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(str(p))
    return created


def _init_databases() -> dict[str, str]:
    results = {}
    for db_rel, schema in DATABASES.items():
        db_path = ROOT / db_rel
        db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            conn = sqlite3.connect(str(db_path))
            conn.executescript(schema)
            conn.commit()
            conn.close()
            results[db_rel] = "ok"
        except Exception as e:
            results[db_rel] = f"error: {e}"
    return results


def _check_llm() -> dict:
    replit_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "")
    if not replit_url:
        return {"status": "no_url", "backend": "none"}

    try:
        sys.path.insert(0, str(ROOT))
        from llm_client import get_client

        st = get_client().status()
        return {
            "status": "ok",
            "backend": st.get("active_backend", "?"),
            "replit_ai": st.get("replit_ai", False),
        }
    except Exception as e:
        return {"status": f"error: {e}", "backend": "unknown"}


def _check_serena() -> dict:
    db_path = ROOT / "state" / "serena_memory.db"
    if not db_path.exists():
        return {"status": "not_indexed", "chunks": 0, "symbols": 0}
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            count = conn.execute("SELECT COUNT(*) FROM code_index").fetchone()[0]
            conn.close()
            return {"status": "ok", "chunks": count, "symbols": count}
        except Exception:
            conn.close()
            return {"status": "empty_db", "chunks": 0, "symbols": 0}
    except Exception as e:
        return {"status": f"error: {e}", "chunks": 0, "symbols": 0}


def run_preflight(auto_fix: bool = False, silent: bool = False) -> dict:
    """Run full preflight. Returns summary dict."""
    dirs_created = _init_directories()
    pkg_results = _check_packages(auto_fix=auto_fix)
    db_results = _init_databases()
    llm_status = _check_llm()
    serena_status = _check_serena()

    failures = [
        p
        for p in pkg_results
        if p["status"] not in ("ok", "installed") and p["critical"]
    ]
    db_errors = {k: v for k, v in db_results.items() if v.startswith("error")}

    summary = {
        "ok": not failures and not db_errors,
        "packages": pkg_results,
        "databases": db_results,
        "llm": llm_status,
        "serena": serena_status,
        "dirs_created": dirs_created,
        "critical_failures": [p["name"] for p in failures],
        "db_errors": db_errors,
    }

    if not silent:
        _print_report(summary)

    return summary


def _print_report(s: dict) -> None:
    icon = "✓" if s["ok"] else "✗"
    print(f"\n{'='*60}")
    print(f"  Terminal Depths Preflight  {icon}")
    print(f"{'='*60}")

    print("\n  PACKAGES")
    for p in s["packages"]:
        status = p["status"]
        sym = (
            "✓"
            if status in ("ok", "installed")
            else ("!" if not p["critical"] else "✗")
        )
        print(f"    {sym}  {p['name']:<20} {status}")

    print("\n  DATABASES")
    for db, st in s["databases"].items():
        sym = "✓" if st == "ok" else "✗"
        name = db.replace("state/", "").replace(".db", "")
        print(f"    {sym}  {name:<18} {st}")

    print(f"\n  LLM       {s['llm']}")
    print(f"  SERENA    {s['serena']}")

    if s["dirs_created"]:
        print(f"\n  Created: {s['dirs_created']}")

    if not s["ok"]:
        print(f"\n  CRITICAL: {s['critical_failures']}")
    print()


if __name__ == "__main__":
    auto_fix = "--auto-fix" in sys.argv
    silent = "--silent" in sys.argv
    result = run_preflight(auto_fix=auto_fix, silent=silent)
    sys.exit(0 if result["ok"] else 1)
