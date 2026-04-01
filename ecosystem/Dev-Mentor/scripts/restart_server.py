#!/usr/bin/env python3
"""scripts/restart_server.py — Graceful game server restart
Kills the uvicorn process on port 7337, restarts it, waits for health.

Activates on restart:
  - Ollama LLM backend (qwen2.5-coder:14b at localhost:11434)
  - nomic-embed-text embeddings (768-dim)
  - 48 consciousness hooks + Project Emergence trigger
  - /api/agent/rl/status numpy fix (numpy present in restarted process env)

Usage: python scripts/restart_server.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

PORT = 7337
SERVER_CMD = [
    sys.executable,
    "-m",
    "cli.devmentor",
    "serve",
    "--host",
    "0.0.0.0",
    "--port",
    str(PORT),
]


def _health():
    try:
        with urllib.request.urlopen(
            f"http://localhost:{PORT}/api/health", timeout=3
        ) as r:
            return json.loads(r.read()).get("ok", False)
    except Exception:
        return False


def kill_server():
    """Kill the process currently listening on PORT. Tries psutil first, falls
    back to Windows netstat + taskkill if psutil is not installed.
    """
    try:
        import psutil  # type: ignore

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info["cmdline"] or []
                if any(str(PORT) in str(c) for c in cmdline):
                    print(
                        f"  [psutil] Killing PID {proc.info['pid']} ({proc.info['name']})"
                    )
                    proc.kill()
                    proc.wait(timeout=5)
                    return True
            except Exception:
                pass
        print("  [psutil] No matching process found on port", PORT)
    except ImportError:
        # Fallback: Windows netstat-based kill
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if f":{PORT}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                print(f"  [netstat] Killing PID {pid}")
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                return True
        print("  [netstat] No LISTENING process found on port", PORT)
    return False


def start_server():
    """Launch the game server as a detached background process."""
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    # PREFER_LOCAL=1 routes LLM calls to Ollama/LM Studio first
    env["PREFER_LOCAL"] = "1"

    kwargs = {}
    if sys.platform == "win32":
        # Detach from parent console on Windows so the process survives terminal close
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )

    subprocess.Popen(
        SERVER_CMD,
        env=env,
        cwd=os.getcwd(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )
    print(f"  Server process launched: {' '.join(SERVER_CMD)}")


def wait_healthy(timeout=30):
    """Poll /api/health until the server responds ok=True or timeout expires."""
    print(f"  Waiting up to {timeout}s for server to become healthy...")
    for i in range(timeout):
        if _health():
            print(f"  Server healthy after {i + 1}s")
            return True
        time.sleep(1)
        if i % 5 == 4:
            print(f"  ...still waiting ({i + 1}s elapsed)")
    return False


def main():
    print(f"\n=== Dev-Mentor Server Restart (port {PORT}) ===\n")

    was_up = _health()
    if not was_up:
        print("Server was already down — skipping kill step.")
    else:
        print("Step 1: Stopping current server...")
        kill_server()
        print("  Waiting 2s for port to clear...")
        time.sleep(2)

    print("\nStep 2: Starting server...")
    start_server()

    print("\nStep 3: Health check...")
    if wait_healthy():
        print("\nRestart complete.")
        print(f"  Game server: http://localhost:{PORT}/api/health")
        print(f"  Terminal Depths: http://localhost:{PORT}/game/")
        print(f"  API docs: http://localhost:{PORT}/api/docs")
    else:
        print(
            "\nServer did not come up within 30s.\n"
            "  -> Check the 'DM: Game Server' terminal for errors.\n"
            "  -> Manually run: python -m cli.devmentor serve --port 7337"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
