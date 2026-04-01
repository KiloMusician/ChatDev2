#!/usr/bin/env python3
"""NuSyQ-Hub Master Launcher - The "Master Clock" for your modular system.

This is the unified entry point that connects all the scattered UI/API components.
Think of it like a modular synthesizer's master clock - it syncs everything.

    python start.py              # Interactive menu
    python start.py --api        # Start FastAPI backend only
    python start.py --ui         # Start Streamlit UI only
    python start.py --all        # Start everything
    python start.py --cli        # CLI menu mode

Components Available:
    - FastAPI Backend (port 8000) - REST API for agents
    - Streamlit UI (port 8501)    - Interactive Context Browser
    - CLI Tools (nq commands)     - Terminal interface
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Ensure we're in the right directory
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


class Colors:
    """ANSI colors for terminal output."""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"


def colored(text, color):
    """Apply color to text."""
    return f"{color}{text}{Colors.END}"


PLACEHOLDER_MODULES = [
    ("scripts/comprehensive_modernization_audit.py", "Audit placeholder"),
    ("start.py", "Master launcher placeholder"),
    ("test_system_connections.py", "System connection placeholder"),
]


def show_placeholder_status():
    """Display which series of placeholders reconcile the incomplete backlog."""
    print()
    print(colored("Placeholder Module Status", Colors.CYAN))
    print(colored("-" * 40, Colors.BLUE))
    for index, (path, desc) in enumerate(PLACEHOLDER_MODULES, start=1):
        print(f"  {index}. {path} → {desc}")
    print(colored("-" * 40, Colors.BLUE))
    print()


def check_service(name, url, timeout=2):
    """Check if a service is running."""
    try:
        import requests

        r = requests.get(url, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def check_ollama():
    """Check Ollama status."""
    try:
        import requests

        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code == 200:
            models = r.json().get("models", [])
            return True, models
        return False, []
    except Exception:
        return False, []


def start_fastapi(background=True):
    """Start the FastAPI backend."""
    print(colored("\n🚀 Starting FastAPI Backend...", Colors.CYAN))
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.api.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]

    if background:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT)
        time.sleep(2)
        if check_service("FastAPI", "http://localhost:8000/api/health"):
            print(colored("   ✅ FastAPI running at http://localhost:8000", Colors.GREEN))
            print(colored("   📚 Docs at http://localhost:8000/docs", Colors.BLUE))
        else:
            print(colored("   ⏳ Starting... check http://localhost:8000", Colors.YELLOW))
        return process
    else:
        subprocess.run(cmd, cwd=ROOT)
        return None


def start_streamlit(background=True):
    """Start the Streamlit UI."""
    print(colored("\n🖥️  Starting Streamlit UI...", Colors.CYAN))

    # Find the best UI file
    ui_candidates = [
        ROOT / "src" / "interface" / "Enhanced-Interactive-Context-Browser-Fixed.py",
        ROOT / "src" / "interface" / "Enhanced-Interactive-Context-Browser-v2.py",
        ROOT / "src" / "interface" / "ContextBrowser_DesktopApp.py",
    ]

    ui_file = None
    for candidate in ui_candidates:
        if candidate.exists():
            ui_file = candidate
            break

    if not ui_file:
        print(colored("   ❌ No Streamlit UI found!", Colors.RED))
        return None

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ui_file),
        "--server.port=8501",
        "--server.headless=true",
        "--theme.base=dark",
        "--browser.gatherUsageStats=false",
    ]

    if background:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT)
        time.sleep(3)
        print(colored("   ✅ Streamlit running at http://localhost:8501", Colors.GREEN))
        return process
    else:
        subprocess.run(cmd, cwd=ROOT)
        return None


def show_status():
    """Show current system status."""
    print()
    print(colored("=" * 60, Colors.BOLD))
    print(colored("           NuSyQ-Hub System Status", Colors.BOLD))
    print(colored("=" * 60, Colors.BOLD))
    print()

    # Ollama
    ollama_ok, models = check_ollama()
    if ollama_ok:
        print(f"  🦙 Ollama:    {colored('✅ Running', Colors.GREEN)} ({len(models)} models)")
    else:
        print(f"  🦙 Ollama:    {colored('❌ NOT RUNNING', Colors.RED)}")
        print(f"              → Run: {colored('ollama serve', Colors.YELLOW)}")

    # FastAPI
    if check_service("API", "http://localhost:8000/api/health"):
        print(f"  🔌 FastAPI:   {colored('✅ Running', Colors.GREEN)} → http://localhost:8000")
    else:
        print(f"  🔌 FastAPI:   {colored('○ Stopped', Colors.YELLOW)}")

    # Streamlit
    if check_service("UI", "http://localhost:8501"):
        print(f"  🖥️  Streamlit: {colored('✅ Running', Colors.GREEN)} → http://localhost:8501")
    else:
        print(f"  🖥️  Streamlit: {colored('○ Stopped', Colors.YELLOW)}")

    # Core system
    try:
        from src.core import nusyq

        result = nusyq.status()
        if result.success:
            print(f"  🧠 Core:      {colored('✅ Healthy', Colors.GREEN)}")
        else:
            print(f"  🧠 Core:      {colored('⚠️ Degraded', Colors.YELLOW)}")
    except Exception as e:
        print(f"  🧠 Core:      {colored(f'❌ Error: {e}', Colors.RED)}")

    print()


def show_menu():
    """Show interactive menu."""
    show_status()

    print(colored("-" * 60, Colors.BLUE))
    print("  Commands:")
    print(colored("-" * 60, Colors.BLUE))
    print("  1. Start API         - FastAPI backend (port 8000)")
    print("  2. Start UI          - Streamlit browser (port 8501)")
    print("  3. Start Both        - API + UI together")
    print("  4. Boot Core         - Initialize NuSyQ core systems")
    print("  5. Run AI Cycle      - Execute one autonomous cycle")
    print("  6. Process Tasks     - Process queued LLM tasks")
    print("  7. Run Tests         - Execute test suite")
    print("  8. Protocol Status   - Check Agent Protocol health")
    print("  9. Placeholder Status   - Show placeholder reconciliation report")
    print("  s. Status            - Refresh status display")
    print("  q. Quit")
    print(colored("-" * 60, Colors.BLUE))
    print()

    return input("  Choose: ").strip().lower()


def run_nq(cmd_args):
    """Run nq command."""
    cmd = [sys.executable, str(ROOT / "nq")] + cmd_args
    print()
    subprocess.run(cmd, cwd=ROOT)
    print()
    input("  Press Enter to continue...")


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # Handle command-line arguments
    if "--api" in args:
        start_fastapi(background=False)
        return

    if "--ui" in args:
        start_streamlit(background=False)
        return

    if "--all" in args:
        print(colored("\n🚀 Starting All Services...\n", Colors.BOLD))
        api_proc = start_fastapi(background=True)
        ui_proc = start_streamlit(background=True)

        print()
        print(colored("=" * 60, Colors.GREEN))
        print(colored("  All services started!", Colors.GREEN))
        print(colored("=" * 60, Colors.GREEN))
        print()
        print("  📡 API:  http://localhost:8000")
        print("  📚 Docs: http://localhost:8000/docs")
        print("  🖥️  UI:   http://localhost:8501")
        print()
        print("  Press Ctrl+C to stop all services...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(colored("\n\n  Stopping services...", Colors.YELLOW))
            if api_proc:
                api_proc.terminate()
            if ui_proc:
                ui_proc.terminate()
            print(colored("  👋 Goodbye!\n", Colors.CYAN))
        return

    if "--status" in args:
        show_status()
        return

    if "--placeholders" in args or "--placeholder-status" in args:
        show_placeholder_status()
        return

    if "--help" in args or "-h" in args:
        print(__doc__)
        return

    # Interactive menu mode
    processes = []
    try:
        while True:
            choice = show_menu()

            if choice == "1":
                proc = start_fastapi(background=True)
                if proc:
                    processes.append(proc)
            elif choice == "2":
                proc = start_streamlit(background=True)
                if proc:
                    processes.append(proc)
            elif choice == "3":
                api_proc = start_fastapi(background=True)
                ui_proc = start_streamlit(background=True)
                if api_proc:
                    processes.append(api_proc)
                if ui_proc:
                    processes.append(ui_proc)
                print(colored("\n  🎉 Both services started!", Colors.GREEN))
                print("     API:  http://localhost:8000")
                print("     UI:   http://localhost:8501")
                input("\n  Press Enter to continue...")
            elif choice == "4":
                run_nq(["boot"])
            elif choice == "5":
                run_nq(["cycle"])
            elif choice == "6":
                count = input("  How many tasks? [5]: ").strip() or "5"
                run_nq(["bg", "process", count])
            elif choice == "7":
                run_nq(["health"])
            elif choice == "8":
                run_nq(["protocol", "status"])
            elif choice == "9":
                show_placeholder_status()
            elif choice == "s":
                continue  # Just refresh
            elif choice in ("q", "quit", "exit"):
                break
            else:
                print(colored("\n  ❓ Unknown option\n", Colors.YELLOW))

    except KeyboardInterrupt:
        pass

    # Cleanup
    print(colored("\n  Cleaning up...", Colors.YELLOW))
    for proc in processes:
        try:
            proc.terminate()
        except Exception:
            pass
    print(colored("  👋 Goodbye!\n", Colors.CYAN))


if __name__ == "__main__":
    main()
