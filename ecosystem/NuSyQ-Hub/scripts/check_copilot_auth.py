#!/usr/bin/env python3
"""Check Copilot CLI authentication state.

This helper is intended to quickly show whether the current environment is sufficient
for Copilot CLI authentication (token presence + config). It is not intended to
replace a full interactive `copilot login`, but it highlights the most common
failure modes observed while running NuSyQ-Hub agent dispatch.

Usage:
    python scripts/check_copilot_auth.py

Outputs a summary of:
 - relevant environment variables (present/empty)
 - secrets.json github.token contents (masked)
 - whether `copilot` is available on PATH
 - whether `copilot status` / `copilot --help` runs successfully or fails due to auth
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _mask(value: str | None) -> str:
    if value is None:
        return "<missing>"
    if value == "":
        return "<empty>"
    if len(value) <= 8:
        return value
    return value[:4] + "…" + value[-4:]


def _load_secrets_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        return {"__error": f"invalid json ({e})"}


def _run_command(cmd: list[str], timeout: int = 10) -> dict[str, Any]:
    # Resolve executable via PATH on Windows to avoid rare FileNotFound errors
    if cmd:
        executable = cmd[0]
        resolved = shutil.which(executable)
        if resolved:
            cmd = [resolved, *cmd[1:]]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "cmd": " ".join(cmd),
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError:
        return {"cmd": " ".join(cmd), "error": "not found"}
    except subprocess.TimeoutExpired:
        return {"cmd": " ".join(cmd), "error": f"timeout ({timeout}s)"}


def main() -> int:
    print("=== Copilot CLI Auth Checker ===\n")

    env_keys = [
        "GITHUB_COPILOT_API_KEY",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "COPILOT_GITHUB_TOKEN",
    ]

    print("[1] Environment Variables")
    for k in env_keys:
        print(f"  {k} = {_mask(os.environ.get(k))}")

    # Check secrets file for github.token
    config_dir = Path(__file__).resolve().parents[1] / "config"
    secrets_path = config_dir / "secrets.json"
    secrets = _load_secrets_json(secrets_path)

    print("\n[2] config/secrets.json")
    print(f"  path: {secrets_path}")
    if "__error" in secrets:
        print(f"  error: {secrets['__error']}")
    else:
        github = secrets.get("github") or {}
        token = github.get("token")
        username = github.get("username")
        print(f"  github.token = {_mask(token)}")
        print(f"  github.username = {username or '<missing>'}")

    # Try to use src/setup/secrets.py if available for structured info
    print("\n[3] SecureConfig (src/setup/secrets.py)")
    try:
        from src.setup.secrets import get_config
    except Exception:
        print("  (unable to import src.setup.secrets)")
    else:
        try:
            cfg = get_config()
            github_token = cfg.get_secret("github", "token")
            print(f"  secure config github.token = {_mask(github_token)}")
        except Exception as e:
            print(f"  error reading secure config: {e}")

    # Check Copilot binary
    print("\n[4] Copilot CLI availability")
    which = _run_command(["where" if os.name == "nt" else "which", "copilot"])
    if which.get("error"):
        print(f"  copilot not found in PATH ({which.get('error')})")
    else:
        paths = which.get("stdout") or ""
        print(f"  copilot found: {paths}")

    # Try running a non-interactive Copilot command to exercise auth check
    print("\n[5] Copilot CLI auth check")
    copilot_exe = shutil.which("copilot")
    if not copilot_exe:
        print("  copilot executable not found via PATH (shutil.which returned None)")
        health = {"error": "not found"}
    else:
        print(f"  copilot executable: {copilot_exe}")
        health = _run_command(
            [
                copilot_exe,
                "-p",
                "Hello",
                "--allow-all",
                "--output-format",
                "json",
            ],
            timeout=15,
        )

    if "error" in health:
        print(f"  health check error: {health['error']}")
    else:
        print(f"  returncode: {health['returncode']}")
        if health.get("stderr"):
            print(f"  stderr: {health['stderr']}")
        if health.get("stdout"):
            print(f"  stdout: {health['stdout']}")

    # Scan Copilot logs for known auth failure patterns
    print("\n[6] Copilot CLI log audit")
    home = Path.home()
    log_dir = home / ".copilot" / "logs"
    if not log_dir.exists():
        print("  log directory not found: ~/.copilot/logs")
    else:
        log_files = sorted(log_dir.glob("process-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not log_files:
            print("  no Copilot log files found in ~/.copilot/logs")
        else:
            latest = log_files[0]
            print(f"  latest log: {latest}")
            try:
                with latest.open("r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(20_000)
            except Exception as e:
                print(f"  failed to read log: {e}")
                content = ""

            if "Copilot Requests" in content and "permission" in content:
                print("  detected: token is missing 'Copilot Requests' permission.")
                print(
                    "  -> Create a fine-grained PAT in GitHub with 'Copilot Requests' and set it in GITHUB_COPILOT_API_KEY."
                )
                print("  -> GitHub docs: https://github.com/settings/tokens/new?scopes=repo&description=Copilot+CLI")
            elif "Personal Access Token" in content and "does not have" in content:
                print("  detected: invalid/insufficient PAT permissions.")
            elif "401" in content or "unauthorized" in content.lower():
                print("  detected: unauthorized (invalid or expired token).")
            else:
                print("  no obvious auth failure strings found in the latest log.")

    print(
        "\n---\nNext step: set GITHUB_COPILOT_API_KEY (or GITHUB_TOKEN/GH_TOKEN) and rerun, or run `copilot login` interactively."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
