#!/usr/bin/env python3
"""NuSyQ-Hub Launcher - Simple entry point to run the system.

This provides a unified way to start NuSyQ-Hub with different modes:

    python run.py              # Interactive menu
    python run.py --boot       # Boot all systems
    python run.py --cycle      # Run one AI development cycle
    python run.py --web        # Start web interface (if available)
    python run.py --watch      # Watch mode with auto-rebuild

Double-click this file on Windows to launch!
"""

import subprocess
import sys
from pathlib import Path

# Ensure we're in the right directory
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


def check_ollama():
    """Check if Ollama is running."""
    try:
        import requests

        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code == 200:
            models = r.json().get("models", [])
            return True, len(models)
        return False, 0
    except Exception:
        return False, 0


def check_system_health():
    """Quick health check."""
    try:
        from src.core import nusyq

        result = nusyq.status()
        return result.success
    except Exception:
        return False


def show_menu():
    """Show interactive menu."""
    print()
    print("=" * 50)
    print("       🚀 NuSyQ-Hub Development System 🚀")
    print("=" * 50)
    print()

    # Check Ollama
    ollama_ok, model_count = check_ollama()
    if ollama_ok:
        print(f"  🦙 Ollama: ✅ Running ({model_count} models)")
    else:
        print("  🦙 Ollama: ❌ NOT RUNNING")
        print("     → Run 'ollama serve' in another terminal!")
        print()

    # Check system
    if check_system_health():
        print("  🧠 System: ✅ Healthy")
    else:
        print("  🧠 System: ⚠️  Needs boot")

    print()
    print("-" * 50)
    print("  Commands:")
    print("-" * 50)
    print("  1. Boot System        - Initialize all components")
    print("  2. Health Check       - Check system status")
    print("  3. Run AI Cycle       - One autonomous dev cycle")
    print("  4. Process AI Tasks   - Process queued LLM tasks")
    print("  5. Watch Mode         - Auto-rebuild on file changes")
    print("  6. Protocol Status    - Check Agent Protocol")
    print("  7. List Workflows     - Show available workflows")
    print("  8. Run Tests          - Execute test suite")
    print("  q. Quit")
    print("-" * 50)
    print()

    return input("  Choose [1-8, q]: ").strip().lower()


def run_command(cmd_args):
    """Run a nq command."""
    cmd = [sys.executable, str(ROOT / "nq")] + cmd_args
    print()
    print(f"  Running: python nq {' '.join(cmd_args)}")
    print("-" * 50)
    subprocess.run(cmd, cwd=ROOT)
    print("-" * 50)
    input("\n  Press Enter to continue...")


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # Handle command-line args
    if "--boot" in args:
        run_command(["boot"])
        return

    if "--cycle" in args:
        run_command(["cycle"])
        return

    if "--health" in args:
        run_command(["health"])
        return

    if "--watch" in args:
        run_command(["watch"])
        return

    if "--help" in args or "-h" in args:
        print(__doc__)
        return

    # Interactive mode
    while True:
        try:
            choice = show_menu()

            if choice == "1":
                run_command(["boot"])
            elif choice == "2":
                run_command(["health"])
            elif choice == "3":
                run_command(["cycle"])
            elif choice == "4":
                count = input("  How many tasks? [5]: ").strip() or "5"
                run_command(["bg", "process", count])
            elif choice == "5":
                run_command(["watch"])
            elif choice == "6":
                run_command(["protocol", "status"])
            elif choice == "7":
                run_command(["workflow", "list"])
            elif choice == "8":
                run_command(["health"])  # Basic test
                print("\n  Running pytest...")
                subprocess.run(
                    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-x"], cwd=ROOT
                )
                input("\n  Press Enter to continue...")
            elif choice in ("q", "quit", "exit"):
                print("\n  👋 Goodbye!\n")
                break
            else:
                print("\n  ❓ Unknown option. Try 1-8 or q.\n")

        except KeyboardInterrupt:
            print("\n\n  👋 Interrupted. Goodbye!\n")
            break


if __name__ == "__main__":
    main()
