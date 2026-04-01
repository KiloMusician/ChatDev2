#!/usr/bin/env python3
"""Run a fast semgrep scan across tripartite repos using a local ruleset."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES = ROOT / "config" / "semgrep_local.yaml"
DEFAULT_OUTPUT_DIR = ROOT / "state" / "reports" / "semgrep"
VENV_DIR = ".venv"


def _first_existing(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


default_simverse = _first_existing(
    [
        Path("C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"),
        ROOT.parent / "SimulatedVerse" / "SimulatedVerse",
        Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse",
    ]
)
default_root = _first_existing(
    [
        Path("C:/Users/keath/NuSyQ"),
        ROOT.parent / "NuSyQ",
        Path.home() / "NuSyQ",
    ]
)

REPOS: list[Path] = [
    Path(os.environ.get("NUSYQ_HUB_PATH", ROOT)),
    Path(os.environ.get("SIMULATEDVERSE_ROOT", str(default_simverse))),
    Path(os.environ.get("NUSYQ_ROOT_PATH", str(default_root))),
]


def _get_nusyq_root(env: dict[str, str]) -> Path:
    """Get NuSyQ root path from environment or default."""
    nusyq_root_env = env.get("NUSYQ_ROOT_PATH", "").strip()
    if nusyq_root_env and Path(nusyq_root_env).exists():
        return Path(nusyq_root_env)
    return default_root


def _resolve_semgrep(env: dict[str, str]) -> list[str]:
    """Resolve semgrep executable, prioritizing Windows-native binaries."""
    configured = env.get("SEMGREP")
    if configured:
        return [configured]

    if os.name == "nt":
        # On Windows, prefer NuSyQ venv semgrep.exe (native binary)
        nusyq_root = _get_nusyq_root(env)
        semgrep_exe = nusyq_root / VENV_DIR / "Scripts" / "semgrep.exe"
        if semgrep_exe.exists():
            return [str(semgrep_exe)]

        # Try system semgrep.exe or semgrep
        for cmd in ["semgrep.exe", "semgrep"]:
            from_path = shutil.which(cmd)
            if from_path:
                return [from_path]
    else:
        # Non-Windows: try system semgrep
        from_path = shutil.which("semgrep")
        if from_path:
            return [from_path]

        # Fall back to NuSyQ venv via python -m
        nusyq_root = _get_nusyq_root(env)
        nusyq_python = nusyq_root / VENV_DIR / "bin" / "python"
        if nusyq_python.exists():
            return [str(nusyq_python), "-m", "semgrep"]

    # Final fallback: try current interpreter's module
    return [sys.executable, "-m", "semgrep"]


def run_semgrep(repo: Path, rules: Path, output_dir: Path, timeout: int = 600) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    name = repo.name
    out_json = output_dir / f"{name}.json"
    env = os.environ.copy()
    env.pop("HTTP_PROXY", None)
    env.pop("HTTPS_PROXY", None)
    env.pop("NO_PROXY", None)
    semgrep_cmd = _resolve_semgrep(env)
    cmd = [
        *semgrep_cmd,
        "--config",
        str(rules),
        "--timeout",
        str(timeout),
        "--jobs",
        "1",
        "--max-target-bytes",
        "500000",
        "--include",
        "src",
        "--include",
        "scripts",
        "--include",
        "tests",
        "--exclude",
        "node_modules",
        "--exclude",
        ".git",
        "--exclude",
        VENV_DIR,
        "--exclude",
        "venv_kilo",
        "--exclude",
        "ChatDev",
        "--exclude",
        "WareHouse",
        "--exclude",
        "tmpclaude-*",
        "--json",
        "--output",
        str(out_json),
        str(repo),
    ]
    print(f"\n==> Semgrep minimal: {repo}")
    try:
        result = subprocess.run(
            cmd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout + 30,
        )
        if result.returncode != 0:
            print(f"[WARN] Semgrep exited {result.returncode} for {repo}\n{result.stderr.strip()}")
        else:
            print(f"[OK] {repo} -> {out_json}")
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Semgrep timed out after {timeout + 30}s for {repo}")
        return 124
    except FileNotFoundError:
        print("[ERROR] semgrep not found; install it or set SEMGREP env")
        return 1


def main() -> int:
    rules = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RULES
    out_dir = DEFAULT_OUTPUT_DIR
    rc = 0
    for repo in REPOS:
        if not repo.exists() or not (repo / ".git").exists():
            print(f"Skipping {repo} (missing or not a git repo)")
            continue
        rc |= run_semgrep(repo, rules, out_dir)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
