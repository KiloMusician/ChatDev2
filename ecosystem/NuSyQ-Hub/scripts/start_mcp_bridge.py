#!/usr/bin/env python3
"""Auto-start MCP bridge for Claude Code CLI integration.

Starts the Python MCP bridge that exposes NuSyQ ecosystem capabilities
to the Kilo Code VS Code extension via MCP protocol.

Usage:
    python scripts/start_mcp_bridge.py [--port PORT] [--host HOST]

Options:
    --port PORT    Port to run on (default: 8000)
    --host HOST    Host to bind to (default: 127.0.0.1)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


def start_mcp_bridge(port: int = 8000, host: str = "127.0.0.1") -> None:
    """Start MCP bridge in background.

    Args:
        port: Port to run on (default: 8000)
        host: Host to bind to (default: 127.0.0.1)
    """
    repo_root = Path(__file__).resolve().parents[1]

    # Check if already running
    if is_port_in_use(port):
        print(f"⚠️  Port {port} is already in use. MCP bridge may already be running.")
        return

    print(f"🔗 Starting MCP Bridge on {host}:{port}...")

    # Start in background
    env = {
        "MCP_BRIDGE_HOST": host,
        "MCP_BRIDGE_PORT": str(port),
    }

    if sys.platform == "win32":
        # Windows: Use CREATE_NEW_PROCESS_GROUP to detach
        process = subprocess.Popen(
            [sys.executable, "-m", "src.integration.mcp_server"],
            cwd=repo_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            env={**subprocess.os.environ, **env},
        )
    else:
        # Unix: Use start_new_session
        process = subprocess.Popen(
            [sys.executable, "-m", "src.integration.mcp_server"],
            cwd=repo_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env={**subprocess.os.environ, **env},
        )

    # Give it time to start
    time.sleep(2)

    # Verify it started
    if is_port_in_use(port):
        print(f"✅ MCP Bridge started (PID: {process.pid})")

        # Write PID for later cleanup
        pid_file = repo_root / "data" / "mcp_bridge.pid"
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(process.pid))

        print(f"📍 PID saved to {pid_file}")
        print("\n🔍 Test endpoints:")
        print(f"   curl http://{host}:{port}/health")
        print(f"   curl http://{host}:{port}/mcp/tools")
    else:
        print("❌ MCP Bridge failed to start. Check logs for details.")
        print("\nTry running manually to see errors:")
        print("   python -m src.integration.mcp_server")


def main():
    """Parse arguments and start MCP bridge."""
    parser = argparse.ArgumentParser(description="Start MCP Bridge")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")

    args = parser.parse_args()

    start_mcp_bridge(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
