#!/usr/bin/env python3
"""⚡ UNIFIED ECOSYSTEM STARTUP
=============================
Single command to start everything:
- Check/start Docker
- Check/start Ollama
- Verify all services
- Report status
- Ready for development

Usage:
    python startup_ecosystem.py          # Check all services
    python startup_ecosystem.py --start  # Auto-start what's possible
    python startup_ecosystem.py --wait   # Wait for services (blocking)
"""

import argparse
import socket
import subprocess
import sys
import time
from pathlib import Path


def check_port(host: str, port: int, timeout: int = 2) -> bool:
    """Check if a service is listening on a port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (TimeoutError, ConnectionRefusedError, OSError):
        return False


def run_command(cmd: list, check: bool = False) -> bool:
    """Run a command silently."""
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def get_service_status() -> dict:
    """Get status of all critical services."""
    status = {
        "docker": False,
        "ollama": False,
        "observability": False,
        "precommit": False,
        "quest_system": False,
    }

    # Check Docker
    if run_command(["docker", "ps"], check=False):
        if check_port("localhost", 2375):
            status["docker"] = True

    # Check Ollama
    if run_command(["ollama", "--version"], check=False):
        if check_port("localhost", 11434):
            status["ollama"] = True

    # Check Observability (Jaeger)
    if check_port("localhost", 16686):
        status["observability"] = True

    # Check Pre-commit
    if run_command(["pre-commit", "--version"], check=False):
        status["precommit"] = True

    # Check Quest System
    quest_log = Path("src/Rosetta_Quest_System/quest_log.jsonl")
    if quest_log.exists():
        status["quest_system"] = True

    return status


def print_status(status: dict, verbose: bool = True) -> None:
    """Print service status."""
    print("\n" + "=" * 60)
    print("📊 ECOSYSTEM SERVICE STATUS")
    print("=" * 60)

    services = [
        ("Docker Daemon", status["docker"], "localhost:2375"),
        ("Ollama LLM", status["ollama"], "localhost:11434"),
        ("Observability", status["observability"], "localhost:16686"),
        ("Pre-commit", status["precommit"], "git hooks"),
        ("Quest System", status["quest_system"], "quest_log.jsonl"),
    ]

    for service, running, endpoint in services:
        emoji = "✅" if running else "❌"
        status_text = "RUNNING" if running else "STOPPED"
        print(f"{emoji} {service:20s} {status_text:10s} ({endpoint})")

    running_count = sum(1 for s in status.values() if s)
    print(f"\n📈 {running_count}/5 services active")

    if verbose:
        print("\n" + "=" * 60)
        print("📝 WHAT TO DO")
        print("=" * 60)

        if not status["docker"]:
            print("\n❌ Docker not running:")
            print("   1. Start Docker Desktop")
            print("   2. Wait for daemon to start (~30 seconds)")
            print("   3. Re-run this script")

        if not status["ollama"]:
            print("\n❌ Ollama not running:")
            print("   1. Open a terminal")
            print("   2. Run: ollama serve")
            print("   3. Keep terminal open while working")

        if status["docker"] and status["ollama"] and not status["observability"]:
            print("\n⚠️  Observability not active:")
            print("   Docker + Ollama running but Jaeger not ready")
            print("   This is OK - traces will still work")

        if status["precommit"]:
            print("\n✅ Pre-commit ready:")
            print("   - Auto-runs on every git commit")
            print("   - Checks: Black, Ruff, Mypy, Secrets")

        if status["quest_system"]:
            print("\n✅ Quest system ready:")
            print("   - Logging agent actions")
            print("   - Preserving context across sessions")


def get_startup_instructions() -> str:
    """Get instructions for starting services."""
    instructions = """

╔════════════════════════════════════════════════════════════╗
║            🚀 ECOSYSTEM STARTUP INSTRUCTIONS               ║
╚════════════════════════════════════════════════════════════╝

OPTION 1: MANUAL START (Recommended First Time)
═════════════════════════════════════════════════

1. START DOCKER DESKTOP
   ├─ Windows: Click Start menu → Docker Desktop
   ├─ Mac: Applications → Docker.app
   ├─ Linux: systemctl start docker
   └─ Wait 30 seconds for daemon to start

2. START OLLAMA SERVICE
   ├─ Open a terminal
   ├─ Run: ollama serve
   ├─ Keep terminal open while developing
   └─ (Press Ctrl+C to stop)

3. DONE! Your ecosystem is running
   ├─ Python code can use local LLM
   ├─ OpenTelemetry tracing ready
   ├─ Pre-commit auto-runs on commits
   └─ Quest system logging actions


OPTION 2: AUTOMATIC START (Windows PowerShell)
═══════════════════════════════════════════════

Run this PowerShell command (elevated/admin):

    # Start Docker
    Start-Process "C:\\Program Files\\Docker\\Docker\\Docker.exe"
    Start-Sleep -Seconds 10  # Wait for Docker

    # Start Ollama
    Start-Process "ollama" -ArgumentList "serve"

    Write-Host "✅ Services starting... give them 30 seconds"


OPTION 3: TASK SCHEDULER (Windows - Auto-Launch on Boot)
═════════════════════════════════════════════════════════

1. Task Scheduler: Create Basic Task
2. Name: "Start Docker & Ollama"
3. Trigger: At log on
4. Action:
   Program: PowerShell
   Args: -NoProfile -Command "Start-Process 'C:\\Program Files\\Docker\\Docker\\Docker.exe'; Start-Sleep 30; Start-Process 'ollama' -ArgumentList 'serve'"
5. Create


VERIFY EVERYTHING IS RUNNING
═════════════════════════════

Run this command to check:
    python startup_ecosystem.py

All 5 services should show ✅


DAILY USAGE
═══════════

1. Morning: Services are running (from Task Scheduler or manual start)

2. During work: Just code and commit
   git commit -m "my changes"
   # Pre-commit auto-runs

3. Weekly check:
   python scripts/start_nusyq.py brief
   python scripts/start_nusyq.py error_report

4. Evening: (Optional) Stop services to free resources
   - Docker Desktop: Click quit
   - Ollama terminal: Press Ctrl+C


TROUBLESHOOTING
═══════════════

Q: Docker not starting?
A:
  • Check Docker Desktop is installed
  • Try: docker --version
  • Reinstall if needed: https://docker.com/products/docker-desktop

Q: Ollama not responding?
A:
  • Check Ollama is installed: ollama --version
  • Try: ollama serve (in terminal)
  • Wait 10 seconds for it to load models
  • Check: http://localhost:11434/api/tags

Q: Pre-commit not running?
A:
  • Reinstall: pip install pre-commit
  • Setup hooks: pre-commit install
  • Test: pre-commit run --all-files

Q: Observability not working?
A:
  • This is optional
  • Requires Docker running
  • Access: http://localhost:16686 (Jaeger)
  • Not critical for development


WHAT EACH SERVICE DOES
══════════════════════

✅ Docker Daemon (Port 2375)
   └─ Runs containers (observability, future deployments)

✅ Ollama LLM (Port 11434)
   └─ Local language model (agents generate code, analyze files)

✅ Observability (Port 16686 - Jaeger)
   └─ Traces agent coordination (if Docker running)

✅ Pre-commit (Git hooks)
   └─ Auto-checks code on every commit

✅ Quest System (quest_log.jsonl)
   └─ Logs all agent actions (preserves context)


RECOMMENDED WORKFLOW
════════════════════

1. Boot computer
2. Docker + Ollama auto-launch (if Task Scheduler configured)
3. Wait 30-60 seconds for both to be ready
4. Open IDE
5. Code normally
6. Pre-commit auto-checks each commit
7. Sleep well knowing your system is healthy 😴
    """
    return instructions


def main():
    parser = argparse.ArgumentParser(description="Unified ecosystem startup and status check")
    parser.add_argument(
        "--start",
        action="store_true",
        help="Auto-start services if possible",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for services to be ready (blocking)",
    )
    parser.add_argument(
        "--instructions",
        action="store_true",
        help="Show detailed startup instructions",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show errors",
    )

    args = parser.parse_args()

    # Print instructions if requested
    if args.instructions:
        print(get_startup_instructions())
        return 0

    # Get current status
    if not args.quiet:
        print("\n🔍 Checking ecosystem services...")

    status = get_service_status()

    # Print status
    if not args.quiet:
        print_status(status, verbose=not args.quiet)

    # Wait for services if requested
    if args.wait:
        print("\n⏳ Waiting for all services to be ready...")
        max_wait = 120  # 2 minutes
        elapsed = 0
        while not all(status.values()) and elapsed < max_wait:
            time.sleep(5)
            elapsed += 5
            status = get_service_status()
            ready = sum(1 for s in status.values() if s)
            print(f"   {ready}/5 services ready ({elapsed}s elapsed)")

        if all(status.values()):
            print("✅ All services ready!")
            return 0
        else:
            print("⏱️  Timeout waiting for services")
            print_status(status, verbose=True)
            return 1

    # Return status code
    running_count = sum(1 for s in status.values() if s)
    if running_count >= 3:  # At least Docker, Ollama, or Precommit + Quest
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
