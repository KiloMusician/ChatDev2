"""Start/stop helper for MultiAIOrchestrator.

Features:
- Ensures the NuSyQ-Hub `src` directory is importable as `src` by adding it to sys.path.
- Writes logs to `logs/orchestrator.log` with rotation.
- Provides CLI: start (daemon), run (foreground), status, stop.
"""

import argparse
import logging
import logging.handlers
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "orchestrator.log"

# Configure logging with rotation
logger = logging.getLogger("start_orchestrator")
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    str(LOG_FILE), maxBytes=5_000_000, backupCount=3, encoding="utf-8"
)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

# Initialize terminal logging (best-effort) for orchestrator logs
try:
    from src.system.init_terminal import init_terminal_logging

    init_terminal_logging(channel="Orchestrator")
except (ImportError, OSError, RuntimeError):
    logger.debug("Terminal logging shim not available for orchestrator")


# Helper to ensure NuSyQ-Hub src path is present
def ensure_paths():
    # Use centralized path resolver if available
    try:
        # Bootstrap: add NuSyQ-Hub first
        hub_bootstrap = Path(
            os.getenv("NUSYQ_HUB_ROOT", "/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub")
        ).resolve()
        if str(hub_bootstrap) not in sys.path:
            sys.path.insert(0, str(hub_bootstrap))

        # Try to import path resolver
        try:
            # Don't add src to sys.path here, we'll handle it in run_foreground
            from utils.repo_path_resolver import get_repo_path

            repo_root = get_repo_path("NUSYQ_HUB_ROOT") or hub_bootstrap
        except ImportError:
            repo_root = hub_bootstrap
    except (OSError, AttributeError, RuntimeError):
        repo_root = Path(
            os.getenv("NUSYQ_HUB_ROOT", "/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub")
        ).resolve()

    if repo_root.exists():
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

    # Also add local NuSyQ repo root
    local_root = Path(__file__).parent.resolve()
    if str(local_root) not in sys.path:
        sys.path.insert(0, str(local_root))


def run_foreground(max_runtime: int | None = None):
    ensure_paths()
    logger.info("Starting MultiAIOrchestrator in foreground")
    try:
        # Import from NuSyQ-Hub orchestration system
        import sys

        hub_path = Path(
            os.getenv("NUSYQ_HUB_ROOT", "/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub")
        ).resolve()
        # Ensure the hub root is at the beginning of sys.path for src.* imports
        if str(hub_path) not in sys.path:
            sys.path.insert(0, str(hub_path))
        elif sys.path[0] != str(hub_path):
            # Move it to the front if it's already there but not at the front
            sys.path.remove(str(hub_path))
            sys.path.insert(0, str(hub_path))
        logger.info("sys.path[0] for import: %s", sys.path[0])

        logger.info("sys.path[0]: %s", sys.path[0])
        logger.info("Importing from src.orchestration.multi_ai_orchestrator")

        from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator

        orchestrator = MultiAIOrchestrator()
        orchestrator.start_orchestration()
        # keep alive
        max_runtime = max_runtime or int(os.getenv("NUSYQ_ORCH_MAX_SECONDS", "0") or 0)
        deadline = time.time() + max_runtime if max_runtime else None
        while True:
            time.sleep(60)
            if deadline and time.time() >= deadline:
                logger.info("Max runtime reached; stopping orchestrator")
                break
    except (ImportError, OSError, RuntimeError, ValueError, AttributeError) as e:
        logger.exception("Orchestrator failed: %s", e)
        raise


def start_background(max_runtime: int | None = None):
    # Use subprocess to start a detached background process that runs this module in 'run' mode
    python = sys.executable
    cmd = [python, str(__file__), "run"]
    if max_runtime:
        cmd.extend(["--max-runtime", str(max_runtime)])
    logger.info("Launching background process: %s", cmd)
    # Ensure log file is used for stdout/stderr of the child process so we capture logs
    pid_file = LOG_DIR / "orchestrator.pid"
    with open(LOG_FILE, "ab") as lf:
        # Start the process detached; on Windows creationflags can be used but we'll keep it simple
        p = subprocess.Popen(cmd, stdout=lf, stderr=lf, cwd=str(ROOT))
    try:
        pid = p.pid
        pid_file.write_text(str(pid), encoding="utf-8")
        logger.info("Background process started (pid=%s)", pid)
    except (OSError, AttributeError, PermissionError):
        logger.exception("Failed to write pid file")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "run", "status", "stop"], help="Action")
    parser.add_argument(
        "--max-runtime", type=int, default=0, help="Max runtime seconds (0=unlimited)"
    )
    args = parser.parse_args()
    if args.action == "run":
        run_foreground(max_runtime=args.max_runtime or None)
    elif args.action == "start":
        start_background(max_runtime=args.max_runtime or None)
    elif args.action == "status":
        pid_file = LOG_DIR / "orchestrator.pid"
        print("Log file:", LOG_FILE)
        if pid_file.exists():
            print("PID file:", pid_file)
            try:
                print("PID:", pid_file.read_text(encoding="utf-8").strip())
            except (OSError, UnicodeDecodeError):
                pass
        print("\nLast lines:")
        if LOG_FILE.exists():
            # show last ~200 lines without reading whole file
            try:
                with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                for line in lines[-200:]:
                    print(line.rstrip("\n"))
            except (OSError, IOError, UnicodeDecodeError):
                print("Unable to read log file")
        else:
            print("No log yet")
    elif args.action == "stop":
        pid_file = LOG_DIR / "orchestrator.pid"
        if not pid_file.exists():
            print("No pid file found; nothing to stop")
            return
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
        except (ValueError, OSError, UnicodeDecodeError):
            print("Could not read pid file")
            return
        # Try graceful termination
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False)
            else:
                import os
                import signal

                os.kill(pid, signal.SIGTERM)
            print("Stop signal sent to pid", pid)
            pid_file.unlink(missing_ok=True)
        except (OSError, PermissionError, ProcessLookupError, ValueError) as e:
            print("Failed to stop process:", e)


if __name__ == "__main__":
    main()
