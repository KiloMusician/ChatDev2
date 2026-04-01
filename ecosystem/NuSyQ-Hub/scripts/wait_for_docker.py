#!/usr/bin/env python3
"""Wait for Docker Desktop to be fully initialized.

Polls the Docker daemon until it responds successfully or times out.

Usage:
    python scripts/wait_for_docker.py [--timeout SECONDS]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time


def is_docker_ready() -> bool:
    """Check if Docker daemon is ready."""
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def wait_for_docker(timeout: int = 60) -> bool:
    """Wait for Docker to be ready.

    Args:
        timeout: Maximum seconds to wait

    Returns:
        True if Docker became ready, False if timed out
    """
    print("🐳 Waiting for Docker Desktop to initialize...")

    start_time = time.time()
    last_message_time = start_time

    while time.time() - start_time < timeout:
        if is_docker_ready():
            elapsed = time.time() - start_time
            print(f"✅ Docker is ready! (took {elapsed:.1f}s)")
            return True

        # Print status every 5 seconds
        if time.time() - last_message_time >= 5:
            elapsed = time.time() - start_time
            print(f"⏳ Still waiting... ({elapsed:.0f}s / {timeout}s)")
            last_message_time = time.time()

        time.sleep(2)

    print(f"❌ Timeout after {timeout}s. Docker may not be running.")
    print("\nTroubleshooting:")
    print("1. Check if Docker Desktop is running:")
    print("   Get-Process 'Docker Desktop'")
    print("2. Check if named pipe exists:")
    print("   Test-Path '\\\\.\\pipe\\dockerDesktopLinuxEngine'")
    print("3. Try restarting Docker Desktop")

    return False


def main():
    """Parse arguments and wait for Docker."""
    parser = argparse.ArgumentParser(description="Wait for Docker to be ready")
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Maximum seconds to wait (default: 60)",
    )

    args = parser.parse_args()

    success = wait_for_docker(timeout=args.timeout)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
