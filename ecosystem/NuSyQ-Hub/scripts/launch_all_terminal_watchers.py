#!/usr/bin/env python3
"""
Master Terminal Launcher - Starts all terminal watchers

Run this to see live output from all agents and operational terminals!
"""

import os
import shutil
import subprocess
import time
from pathlib import Path

WATCHERS = [
    "watch_claude_terminal.ps1",
    "watch_copilot_terminal.ps1",
    "watch_codex_terminal.ps1",
    "watch_chatdev_terminal.ps1",
    "watch_ai_council_terminal.ps1",
    "watch_intermediary_terminal.ps1",
    "watch_errors_terminal.ps1",
    "watch_suggestions_terminal.ps1",
    "watch_tasks_terminal.ps1",
    "watch_tests_terminal.ps1",
    "watch_zeta_terminal.ps1",
    "watch_agents_terminal.ps1",
    "watch_metrics_terminal.ps1",
    "watch_anomalies_terminal.ps1",
    "watch_future_terminal.ps1",
    "watch_main_terminal.ps1",
    "watch_culture_ship_terminal.ps1",
    "watch_moderator_terminal.ps1",
    "watch_system_terminal.ps1",
    "watch_chatgpt_bridge_terminal.ps1",
    "watch_simulatedverse_terminal.ps1",
    "watch_ollama_terminal.ps1",
    "watch_lmstudio_terminal.ps1",
    "watch_powershell_extension_terminal.ps1",
    "watch_pwsh_terminal.ps1",
]


def _to_windows_path(path: Path) -> str:
    path_str = str(path)
    if path_str.startswith("/mnt/") and len(path_str) > 6:
        drive = path_str[5].upper()
        tail = path_str[7:].replace("/", "\\")
        return f"{drive}:\\{tail}"
    return path_str


def main():
    root = Path(__file__).parent.parent
    watcher_dir = root / "data" / "terminal_watchers"
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        print("❌ PowerShell executable not found (pwsh/powershell).")
        return 1

    print("🚀 Launching Terminal Watchers...")
    print("=" * 70)
    print(f"Watcher Dir: {watcher_dir}")
    print(f"Shell: {shell}")

    processes = []
    for watcher in WATCHERS:
        watcher_path = watcher_dir / watcher
        if not watcher_path.exists():
            print(f"⚠️  Watcher not found: {watcher}")
            continue

        terminal_name = watcher.replace("watch_", "").replace("_terminal.ps1", "")
        print(f"   Launching {terminal_name} watcher...")

        # Launch in new PowerShell window
        args = [shell, "-NoExit"]
        if os.path.basename(shell).lower().startswith("powershell"):
            args.extend(["-ExecutionPolicy", "Bypass"])
        args.extend(["-File", _to_windows_path(watcher_path)])
        creation_flags = 0
        if os.name == "nt" and hasattr(subprocess, "CREATE_NEW_CONSOLE"):
            creation_flags = subprocess.CREATE_NEW_CONSOLE
        proc = subprocess.Popen(args, creationflags=creation_flags)
        processes.append(proc)
        time.sleep(0.5)  # Stagger launches

    print(f"\n✅ Launched {len(processes)} terminal watchers!")
    print("   Each terminal is now showing live output")
    print("   Press Ctrl+C to stop monitoring")

    try:
        # Keep script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping terminal watchers...")
        for proc in processes:
            proc.terminate()
        print("✅ All watchers stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
