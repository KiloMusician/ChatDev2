#!/usr/bin/env python3
"""Direct ChatDev launcher for debugging - bypasses MCP server.

This script tests ChatDev directly to isolate integration issues.
It captures and logs all stdout/stderr from the ChatDev process.
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

# Setup environment
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.integration.chatdev_launcher import ChatDevLauncher


def stream_output(pipe, prefix, log_file):
    """Read from pipe and log to console and file."""
    try:
        for line in iter(pipe.readline, ""):
            if line:
                msg = f"{prefix}: {line.rstrip()}"
                print(msg)
                if log_file:
                    log_file.write(msg + "\n")
                    log_file.flush()
    except Exception as e:
        print(f"Error reading {prefix}: {e}")
    finally:
        pipe.close()


def setup_logger(log_dir: Path) -> Path:
    """Create log file and return path."""
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return log_dir / f"chatdev_direct_test_{timestamp}.log"


def initialize_and_configure_launcher() -> ChatDevLauncher:
    """Initialize ChatDev launcher and configure environment."""
    print("\n1️⃣ Initializing ChatDevLauncher...")
    launcher = ChatDevLauncher()
    print(f"   {launcher}")
    print(f"   ChatDev path: {launcher.chatdev_path}")
    print(f"   Use Ollama: {launcher.use_ollama}")

    # Setup API key
    print("\n2️⃣ Setting up API key...")
    if launcher.setup_api_key():
        print("   ✅ API key configured")
    else:
        print("   ❌ API key setup failed")
        raise RuntimeError("API key setup failed")

    # Setup environment
    print("\n3️⃣ Setting up environment...")
    launcher.setup_environment()
    print("   ✅ Environment configured")

    # Display environment variables
    print("\n📋 Environment variables:")
    env_vars = ["OPENAI_API_KEY", "CHATDEV_USE_OLLAMA", "BASE_URL", "CHATDEV_ROOT"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if "KEY" in var:
                display = value[:8] + "..." if len(value) > 8 else value
            else:
                display = value
            print(f"   {var}: {display}")

    return launcher


def launch_and_monitor(launcher: ChatDevLauncher, log_file_path: Path) -> int:
    """Launch ChatDev and monitor output."""
    print("\n4️⃣ Launching ChatDev process...")
    print("   Task: Create a simple Python function to add two numbers")
    print("   Name: debug_test_adder")
    print("   Model: gpt-4o-mini")

    process = launcher.launch_chatdev(
        task="Create a Python function called add_numbers(a, b) that returns the sum. Include docstring.",
        name="debug_test_adder",
        model="gpt-4o-mini",
        organization="NuSyQ",
        config="Default",
    )

    print(f"   ✅ Process launched with PID: {process.pid}")

    # Open log file and capture output
    with open(log_file_path, "w", encoding="utf-8") as log_file:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file.write(f"ChatDev Direct Test - {timestamp}\n")
        log_file.write("=" * 70 + "\n\n")

        # Start threads to capture stdout and stderr
        print("\n5️⃣ Capturing process output...")
        print("   (Live output streaming to console and log file)\n")
        print("-" * 70)

        stdout_thread = threading.Thread(target=stream_output, args=(process.stdout, "STDOUT", log_file), daemon=True)
        stderr_thread = threading.Thread(target=stream_output, args=(process.stderr, "STDERR", log_file), daemon=True)

        stdout_thread.start()
        stderr_thread.start()

        # Wait for process to complete with timeout
        print("\n⏳ Waiting for ChatDev (max 5 minutes)...")
        try:
            return_code = process.wait(timeout=300)
            print(f"\n✅ Process completed with return code: {return_code}")
        except subprocess.TimeoutExpired:
            print("\n⚠️ Process timed out after 5 minutes")
            process.kill()
            return_code = -1

        # Wait for threads to finish reading
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)

    return return_code


def check_and_report_results(launcher: ChatDevLauncher, log_file_path: Path, return_code: int) -> int:
    """Check generated project and report results."""
    print("-" * 70)
    print("\n6️⃣ Checking results...")

    # Check if project was created
    warehouse = Path(launcher.chatdev_path) / "WareHouse"
    project_dirs = list(warehouse.glob("debug_test_adder*"))

    if project_dirs:
        print(f"   ✅ Project created: {project_dirs[0].name}")

        # List generated files
        py_files = list(project_dirs[0].glob("*.py"))
        if py_files:
            print(f"   ✅ Generated {len(py_files)} Python file(s):")
            for f in py_files:
                print(f"      - {f.name}")
        else:
            print("   ⚠️ No Python files found in project")
    else:
        print("   ❌ No project directory created")
        print(f"   Searched in: {warehouse}")

    print(f"\n📄 Full log saved to: {log_file_path}")

    if return_code == 0 and project_dirs:
        print("\n🎉 SUCCESS: ChatDev completed successfully!")
        return 0
    else:
        print("\n⚠️ PARTIAL SUCCESS: Process completed but check logs for issues")
        return 1


def main():
    """Run direct ChatDev test with full logging."""
    print("=" * 70)
    print("🔍 DIRECT CHATDEV LAUNCHER TEST")
    print("=" * 70)

    # Create log directory and file
    log_dir = REPO_ROOT / "logs" / "chatdev"
    log_file_path = setup_logger(log_dir)
    print(f"\n📝 Logging to: {log_file_path}")

    try:
        # Initialize and configure
        launcher = initialize_and_configure_launcher()

        # Launch and monitor
        return_code = launch_and_monitor(launcher, log_file_path)

        # Check results
        return check_and_report_results(launcher, log_file_path, return_code)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
