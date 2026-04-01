#!/usr/bin/env python3
"""scripts/requirements_check.py — Startup dependency validator (stdlib-only)

Checks that all required Python packages are importable and that critical
environment variables and files are present.  Runs at startup if invoked
directly, or imported by bootstrap scripts.

Usage:
    python3 scripts/requirements_check.py
    python3 scripts/requirements_check.py --strict   # exit 1 on any failure
    python3 scripts/requirements_check.py --json     # JSON output

Integrations:
    - VS Code task: "🧰 TD: Requirements Check"
    - Makefile: make install / make install-dev
    - Bootstrap: scripts/bootstrap_local.sh calls this
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ── Package checks ────────────────────────────────────────────────────────────
# (import_name, pip_name, required)
PACKAGES: list[tuple[str, str, bool]] = [
    ("fastapi", "fastapi", True),
    ("uvicorn", "uvicorn[standard]", True),
    ("pydantic", "pydantic", True),
    ("rich", "rich", True),
    ("typer", "typer", True),
    ("aiofiles", "aiofiles", True),
    ("websockets", "websockets", True),
    ("yaml", "pyyaml", True),
    ("jwt", "PyJWT", True),
    ("httpx", "httpx", False),
    ("aiohttp", "aiohttp", False),
    ("requests", "requests", False),
    ("redis", "redis", False),
    ("openai", "openai", False),
]

# ── File checks ───────────────────────────────────────────────────────────────
REQUIRED_FILES: list[tuple[str, str]] = [
    ("app/backend/main.py", "Main FastAPI application"),
    ("app/game_engine/commands.py", "Game engine command registry"),
    ("app/game_engine/gamestate.py", "Game state management"),
    ("config/port_map.json", "Port registry (offline-first)"),
    ("config/ecosystem_state.yaml", "Desired ecosystem state"),
    ("core/environment.py", "Meta-awareness layer"),
    ("core/suggest.py", "Suggestion engine"),
    ("scripts/bootstrap_local.sh", "Linux/macOS bootstrap"),
    ("scripts/bootstrap_windows.ps1", "Windows bootstrap"),
    ("scripts/validate_all.py", "CI validation suite"),
    ("MASTER_ZETA_TODO.md", "Task queue"),
    ("requirements.txt", "Pip dependencies"),
    (".env.example", "Environment variable template"),
]

# ── Env var checks ────────────────────────────────────────────────────────────
# (var, required, description)
ENV_VARS: list[tuple[str, bool, str]] = [
    ("SESSION_SECRET", True, "Session signing key (set in Replit Secrets)"),
    ("REPL_ID", False, "Replit environment ID (auto-set in Replit)"),
    ("GITHUB_TOKEN", False, "GitHub push / Issues automation"),
    ("OPENAI_API_KEY", False, "OpenAI LLM backend"),
    ("OLLAMA_URL", False, "Ollama local LLM backend"),
    ("TD_BASE_URL", False, "Terminal Depths API URL override"),
]


def check_packages() -> list[dict]:
    results = []
    for import_name, pip_name, required in PACKAGES:
        try:
            importlib.import_module(import_name)
            results.append({"name": pip_name, "status": "OK", "required": required})
        except ImportError:
            status = "MISSING" if required else "OPTIONAL"
            results.append(
                {
                    "name": pip_name,
                    "status": status,
                    "required": required,
                    "fix": f"pip install {pip_name}",
                }
            )
    return results


def check_files() -> list[dict]:
    results = []
    for rel_path, desc in REQUIRED_FILES:
        full = ROOT / rel_path
        ok = full.exists()
        results.append(
            {"path": rel_path, "desc": desc, "status": "OK" if ok else "MISSING"}
        )
    return results


def check_env() -> list[dict]:
    results = []
    for var, required, desc in ENV_VARS:
        present = bool(os.environ.get(var))
        if present:
            status = "SET"
        elif required:
            status = "MISSING"
        else:
            status = "UNSET"
        results.append(
            {"var": var, "status": status, "required": required, "desc": desc}
        )
    return results


def run(strict: bool = False, as_json: bool = False) -> int:
    pkg_results = check_packages()
    file_results = check_files()
    env_results = check_env()

    if as_json:
        print(
            json.dumps(
                {
                    "packages": pkg_results,
                    "files": file_results,
                    "env": env_results,
                },
                indent=2,
            )
        )
        return 0

    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    DIM = "\033[90m"
    RESET = "\033[0m"

    failures = 0

    print(f"\n  {GREEN}DevMentor / Terminal Depths — Requirements Check{RESET}")
    print("  ════════════════════════════════════════════════\n")

    # Packages
    print("  📦 Packages:")
    for r in pkg_results:
        s = r["status"]
        icon = (
            f"{GREEN}✓{RESET}"
            if s == "OK"
            else (f"{RED}✗{RESET}" if s == "MISSING" else f"{DIM}○{RESET}")
        )
        fix = f"  {DIM}→ {r.get('fix','')}{RESET}" if s == "MISSING" else ""
        print(f"    {icon}  {r['name']:<28} {s}{fix}")
        if s == "MISSING" and r["required"]:
            failures += 1
    print()

    # Files
    print("  📁 Files:")
    for r in file_results:
        s = r["status"]
        icon = f"{GREEN}✓{RESET}" if s == "OK" else f"{RED}✗{RESET}"
        print(f"    {icon}  {r['path']:<40} {DIM}{r['desc'][:40]}{RESET}")
        if s == "MISSING":
            failures += 1
    print()

    # Env vars
    print("  🔑 Environment:")
    for r in env_results:
        s = r["status"]
        if s == "SET":
            icon = f"{GREEN}✓{RESET}"
        elif s == "MISSING":
            icon = f"{RED}✗{RESET}"
            failures += 1
        else:
            icon = f"{DIM}○{RESET}"
        print(f"    {icon}  {r['var']:<28} {s:<8} {DIM}{r['desc'][:40]}{RESET}")
    print()

    # Summary
    if failures == 0:
        print(f"  {GREEN}✓ All checks passed — system ready{RESET}\n")
    else:
        print(f"  {RED}✗ {failures} issue(s) found — see above{RESET}")
        print(f"    Run: {DIM}pip install -r requirements.txt{RESET}")
        print("    Set secrets in Replit Secrets panel or .env file\n")

    return 1 if (failures > 0 and strict) else 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Check DevMentor runtime requirements")
    ap.add_argument(
        "--strict", action="store_true", help="Exit 1 if any required check fails"
    )
    ap.add_argument("--json", action="store_true", help="JSON output")
    a = ap.parse_args()
    sys.exit(run(strict=a.strict, as_json=a.json))
