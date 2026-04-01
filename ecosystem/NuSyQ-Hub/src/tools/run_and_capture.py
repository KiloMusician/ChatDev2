"""Run a Python module or command, stream stdout/stderr to the console,.

and capture the full output into a timestamped log file.

This utility helps ensure real-time visibility in editors/terminals while
preserving the complete output for downstream agents (Copilot, ChatDev, Ollama).

Additional guidance and tips (short):
- Use this wrapper when you need both live terminal output and a persistent
    log for agent ingestion. It writes `logs/run_capture_<timestamp>.log`.
- On Windows, the runner creates a new process group and attempts to forward
    CTRL events so Ctrl-C in the parent can be relayed to the child process.
    This helps child processes handle cleanup and write partial summaries.
- Encoding: output is captured with UTF-8 encoding; where consoles don't
    support UTF-8, characters may be replaced. Use `chcp 65001` on Windows
    or run the terminal with UTF-8 support.

Integration notes:
- Agents should read the generated log file for the authoritative output
    and prefer structured summaries (e.g., `logs/maze_summary_*.json`) when
    available.
- Consider integrating the writer with `src/tools/log_indexer.py` to
    automatically surface recent run artifacts to orchestrators.

Security & safety:
- This runner executes arbitrary commands; avoid running untrusted code.
"""

from __future__ import annotations

# mypy: disable-error-code=attr-defined
import argparse
import contextlib
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_and_capture(cmd: list[str], cwd: Path | None = None, log_dir: Path | None = None) -> Path:
    if log_dir is None:
        log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"run_capture_{timestamp}.log"

    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write(
            f"# Command: {' '.join(cmd)}\n# Cwd: {cwd or Path.cwd()}\n# Started: {timestamp}\n\n"
        )
        # Start subprocess and stream output; set encoding/errors to be robust
        # On Windows, create a new process group so we can send CTRL_BREAK_EVENT
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        proc = subprocess.Popen(  # nosemgrep
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",  # nosemgrep
            errors="replace",  # nosemgrep
            bufsize=1,
            creationflags=creationflags,
        )
        assert proc.stdout is not None
        try:
            # Read line-by-line to allow responsive KeyboardInterrupt handling
            while True:
                line = proc.stdout.readline()
                if line:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    fh.write(line)
                elif proc.poll() is not None:
                    # Process ended and no more output
                    break
        except KeyboardInterrupt:
            # Forward interrupt to subprocess so it can handle and write summaries.
            try:
                if os.name == "nt":
                    # Send CTRL_BREAK_EVENT to the process group
                    proc.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    # POSIX: send SIGINT
                    proc.send_signal(signal.SIGINT)
            except (OSError, ValueError):
                # If forwarding fails, fall back to terminate
                with contextlib.suppress(OSError):  # termination failed; OS will clean up
                    proc.terminate()
            fh.write("\n# INTERRUPTED by user (KeyboardInterrupt) - forwarded to child\n")
            # Re-raise to propagate to caller if desired
            raise
        finally:
            try:
                rc = proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                rc = proc.poll() or -1
            fh.write(f"\n# Return code: {rc}\n")

    return log_path


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Run a module/command and capture full output to a log while streaming it"
    )
    parser.add_argument(
        "cmd",
        nargs=argparse.REMAINDER,
        help="Command to run (e.g. python -m src.tools.maze_solver . --max-depth 6)",
    )
    parser.add_argument("--log-dir", default="logs", help="Directory to write logs into")
    parser.add_argument("--cwd", default=".", help="Working directory for the command")
    args = parser.parse_args(argv)

    if not args.cmd:
        parser.error("Specify a command to run")

    cmd = args.cmd
    run_and_capture(cmd, cwd=Path(args.cwd), log_dir=Path(args.log_dir))


if __name__ == "__main__":
    main()
