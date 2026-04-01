#!/usr/bin/env python3
"""Stop All Critical Services - Unified shutdown for NuSyQ-Hub ecosystem

This script stops all critical services started by start_all_critical_services.py.
It reads the state file and attempts to gracefully terminate all running processes/threads.
"""

import json
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
STATE_FILE = ROOT / "state" / "services" / "critical_services.json"


def stop_process(pid):
    try:
        import psutil

        proc = psutil.Process(pid)
        print(f"Stopping PID {pid} ({proc.name()}) ...", end=" ")
        proc.terminate()
        try:
            proc.wait(timeout=10)
            print("✅ Terminated.")
        except psutil.TimeoutExpired:
            print("⚠️ Not responding, killing...")
            proc.kill()
            proc.wait(timeout=5)
            print("💀 Killed.")
    except Exception as e:
        print(f"❌ Could not stop PID {pid}: {e}")


def main():
    if not STATE_FILE.exists():
        print(f"No state file found at {STATE_FILE}. Nothing to stop.")
        return

    state = json.loads(STATE_FILE.read_text())
    services = state.get("services", {})
    if not services:
        print("No running services found in state file.")
        return

    print("=" * 70)
    print("🛑 STOPPING ALL CRITICAL SERVICES")
    print("=" * 70)

    for name, info in services.items():
        print(f"\n{name.replace('_', ' ').title()}:")
        if info.get("type") == "process" and "pid" in info:
            stop_process(info["pid"])
        elif info.get("type") == "thread":
            print("(Thread-based service, will stop with main process or on restart.)")
        else:
            print("Unknown service type or missing PID.")

    print("\nAll stop signals sent. Some services may take a few seconds to exit.")
    print("You may need to manually check for orphaned processes if any remain running.")

    # Optionally, clear the state file
    STATE_FILE.write_text(json.dumps({"services": {}, "last_update": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=2))
    print(f"\nState file cleared: {STATE_FILE}")


if __name__ == "__main__":
    main()
