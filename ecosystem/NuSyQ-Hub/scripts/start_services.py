#!/usr/bin/env python3
"""Start/stop/status for all NuSyQ ecosystem services.

Manages:
- Orchestrator (from Hub)
- PU Queue (from Hub)
- SimulatedVerse Dev Server (npm)
- Quest Log Sync (continuous mode)

Usage:
    python scripts/start_services.py start [--service SERVICE]
    python scripts/start_services.py stop [--service SERVICE]
    python scripts/start_services.py status
    python scripts/start_services.py restart [--service SERVICE]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Literal

# Add Hub to path
HUB_ROOT = Path(__file__).resolve().parents[1]
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

from src.system.ecosystem_paths import get_repo_roots

SERVICE_REGISTRY = HUB_ROOT / "state" / "services" / "registry.json"
SERVICE_REGISTRY.parent.mkdir(parents=True, exist_ok=True)

ServiceName = Literal["orchestrator", "pu_queue", "simverse", "quest_sync", "all"]


def load_registry() -> dict:
    """Load service registry from disk."""
    if SERVICE_REGISTRY.exists():
        try:
            return json.loads(SERVICE_REGISTRY.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_registry(registry: dict) -> None:
    """Save service registry to disk."""
    try:
        SERVICE_REGISTRY.write_text(json.dumps(registry, indent=2))
    except OSError as e:
        print(f"⚠️  Failed to save registry: {e}")


def is_process_running(pid: int) -> bool:
    """Check if process with given PID is running."""
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return str(pid) in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    else:
        try:
            import os

            os.kill(pid, 0)  # Doesn't actually kill, just checks if process exists
            return True
        except (OSError, ProcessLookupError):
            return False


def start_orchestrator() -> dict:
    """Start the unified AI orchestrator."""
    print("🚀 Starting Orchestrator...")

    try:
        # Import and initialize orchestrator
        from src.orchestration.unified_ai_orchestrator import UnifiedAIOrchestrator

        orchestrator = UnifiedAIOrchestrator()

        # Orchestrator is now initialized and ready to handle tasks
        # It doesn't need a continuous loop - it's event-driven
        print(f"   ✅ Initialized with {len(orchestrator.ai_systems)} AI systems")
        print(f"   ✅ {len(orchestrator.pipelines)} pipelines registered")

        return {
            "pid": "initialized",  # Orchestrator is ready, not a background process
            "status": "running",
            "method": "singleton",
        }
    except ImportError as e:
        print(f"❌ Failed to import orchestrator: {e}")
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        print(f"❌ Failed to start orchestrator: {e}")
        return {"status": "failed", "error": str(e)}


def start_pu_queue() -> dict:
    """Start PU queue processor in background."""
    print("🔄 Starting PU Queue...")

    try:
        # PU queue runs once and exits - that's normal behavior
        # Run it in simulated mode (no --real flag = simulated by default)
        cmd = [sys.executable, str(HUB_ROOT / "scripts" / "pu_queue_runner.py")]

        result = subprocess.run(
            cmd,
            cwd=HUB_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("   ✅ PU queue processing complete")
            return {"pid": "one-shot", "status": "completed", "method": "one-shot"}
        else:
            return {"status": "failed", "error": result.stderr or "Non-zero exit"}

    except subprocess.TimeoutExpired:
        return {"status": "failed", "error": "PU queue timed out after 30s"}
    except Exception as e:
        print(f"❌ Failed to start PU queue: {e}")
        return {"status": "failed", "error": str(e)}


def start_simverse() -> dict:
    """Start SimulatedVerse dev server."""
    print("🌌 Starting SimulatedVerse...")

    repos = get_repo_roots()
    simverse_root = repos["simverse"]

    if not simverse_root.exists():
        return {"status": "failed", "error": "SimulatedVerse repo not found"}

    package_json = simverse_root / "package.json"
    if not package_json.exists():
        return {"status": "failed", "error": "package.json not found"}

    simverse_port = str(os.environ.get("SIMULATEDVERSE_PORT", "5002")).strip() or "5002"
    use_minimal = not bool(str(os.environ.get("DATABASE_URL", "")).strip())
    npm_script = "dev:minimal" if use_minimal else "dev"

    try:
        env = os.environ.copy()
        env["PORT"] = simverse_port
        env["SIMULATEDVERSE_PORT"] = simverse_port
        env.setdefault("NUSYQ_SIMULATEDVERSE_START_PROFILE", "minimal" if use_minimal else "full")

        # Canonicalize startup path on Windows to avoid duplicate launcher logic drift.
        if sys.platform == "win32":
            canonical_launcher = HUB_ROOT / "scripts" / "Start-SimulatedVerse.ps1"
            powershell = shutil.which("powershell.exe")
            if canonical_launcher.exists() and powershell:
                cmd = [
                    powershell,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(canonical_launcher),
                ]
                result = subprocess.run(
                    cmd,
                    cwd=HUB_ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                if result.returncode == 0:
                    base_url = f"http://127.0.0.1:{simverse_port}"
                    mode_note = "minimal" if use_minimal else "full"
                    print(f"   ✅ SimulatedVerse ({mode_note}) started via canonical launcher")
                    return {
                        "pid": "launcher",
                        "status": "running",
                        "method": "canonical_launcher",
                        "base_url": base_url,
                        "script": npm_script,
                    }
                stderr_tail = "\n".join((result.stderr or "").splitlines()[-12:])
                stdout_tail = "\n".join((result.stdout or "").splitlines()[-12:])
                return {
                    "status": "failed",
                    "error": (
                        f"canonical_launcher_failed rc={result.returncode}; "
                        f"stdout_tail={stdout_tail!r}; stderr_tail={stderr_tail!r}"
                    ),
                }

        if sys.platform == "win32":
            cmd = ["cmd.exe", "/c", f"npm run {npm_script}"]
        else:
            cmd = ["npm", "run", npm_script]

        if sys.platform == "win32":
            proc = subprocess.Popen(
                cmd,
                cwd=simverse_root,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            )
        else:
            proc = subprocess.Popen(
                cmd,
                cwd=simverse_root,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        time.sleep(2)

        if proc.poll() is None:
            base_url = f"http://127.0.0.1:{simverse_port}"
            mode_note = "minimal" if use_minimal else "full"
            print(f"   ✅ SimulatedVerse ({mode_note}) starting on {base_url}")
            return {
                "pid": proc.pid,
                "status": "running",
                "method": "subprocess",
                "base_url": base_url,
                "script": npm_script,
            }
        else:
            return {"status": "failed", "error": "npm process exited immediately"}

    except FileNotFoundError:
        return {"status": "failed", "error": "npm not found - install Node.js"}
    except Exception as e:
        print(f"❌ Failed to start SimulatedVerse: {e}")
        return {"status": "failed", "error": str(e)}


def start_quest_sync() -> dict:
    """Start quest log sync in continuous mode."""
    print("📡 Starting Quest Log Sync...")

    try:
        # Run sync once (no continuous mode yet)
        cmd = [sys.executable, "-m", "src.tools.cross_ecosystem_sync"]

        result = subprocess.run(
            cmd,
            cwd=HUB_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return {"pid": "one-shot", "status": "completed", "method": "one-shot"}
        else:
            return {"status": "failed", "error": result.stderr or "Non-zero exit"}

    except subprocess.TimeoutExpired:
        return {"status": "failed", "error": "Sync timed out after 60s"}
    except Exception as e:
        print(f"❌ Failed to start quest sync: {e}")
        return {"status": "failed", "error": str(e)}


def stop_service(service_name: str, service_info: dict) -> bool:
    """Stop a running service."""
    if service_info.get("status") != "running":
        return True  # Already stopped

    pid = service_info.get("pid")
    if pid == "thread":
        print(f"⚠️  {service_name}: Cannot stop thread-based service (restart process)")
        return False

    if pid == "one-shot":
        return True  # One-shot services don't need stopping

    if not isinstance(pid, int):
        return True

    if not is_process_running(pid):
        return True  # Already dead

    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], timeout=5)
        else:
            import os
            import signal

            os.kill(pid, signal.SIGTERM)

        print(f"✅ Stopped {service_name} (PID {pid})")
        return True

    except Exception as e:
        print(f"❌ Failed to stop {service_name}: {e}")
        return False


def get_status() -> dict:
    """Get status of all services."""
    registry = load_registry()
    status = {}

    for service_name, service_info in registry.items():
        if service_info.get("method") == "thread":
            status[service_name] = "⚠️  thread (restart process to stop)"
        elif service_info.get("method") == "one-shot":
            status[service_name] = "✅ completed (one-shot)"
        elif service_info.get("status") == "failed":
            status[service_name] = f"❌ failed: {service_info.get('error', 'unknown')}"
        else:
            pid = service_info.get("pid")
            if isinstance(pid, int) and is_process_running(pid):
                status[service_name] = f"✅ running (PID {pid})"
            else:
                status[service_name] = "❌ stopped"

    return status


def main():
    parser = argparse.ArgumentParser(description="Manage NuSyQ ecosystem services")
    parser.add_argument(
        "action",
        choices=["start", "stop", "status", "restart"],
        help="Action to perform",
    )
    parser.add_argument(
        "--service",
        choices=["orchestrator", "pu_queue", "simverse", "quest_sync", "all"],
        default="all",
        help="Specific service to manage (default: all)",
    )

    args = parser.parse_args()

    if args.action == "status":
        print("\n🏥 Service Status:\n")
        status = get_status()
        if not status:
            print("No services registered yet")
        for name, state in status.items():
            print(f"  {name:20s} {state}")
        print()
        return

    registry = load_registry()

    if args.action == "start":
        services_to_start = (
            ["orchestrator", "pu_queue", "simverse", "quest_sync"] if args.service == "all" else [args.service]
        )

        for service in services_to_start:
            if service == "orchestrator":
                result = start_orchestrator()
            elif service == "pu_queue":
                result = start_pu_queue()
            elif service == "simverse":
                result = start_simverse()
            elif service == "quest_sync":
                result = start_quest_sync()
            else:
                continue

            registry[service] = result

            if result.get("status") == "running" or result.get("status") == "completed":
                print(f"✅ {service} started")
            else:
                print(f"❌ {service} failed: {result.get('error', 'unknown')}")

        save_registry(registry)

    elif args.action == "stop":
        services_to_stop = list(registry.keys()) if args.service == "all" else [args.service]

        for service in services_to_stop:
            if service in registry:
                if stop_service(service, registry[service]):
                    registry[service]["status"] = "stopped"

        save_registry(registry)

    elif args.action == "restart":
        # Stop then start
        if args.service in registry:
            stop_service(args.service, registry[args.service])
        time.sleep(1)
        # Re-run start logic
        subprocess.run([sys.executable, __file__, "start", "--service", args.service])


if __name__ == "__main__":
    main()
