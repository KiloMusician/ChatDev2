"""Resource Cleanup Utilities.

===========================

Purpose:
    Utilities for cleaning up hung processes, temporary files,
    and other resources that may be left behind by failed workflows.

Features:
    - Process termination (graceful and forced)
    - Temporary file cleanup
    - Stale lock file removal
    - Port release utilities
    - Memory cleanup

Usage:
    # Clean up hung Python processes
    cleanup = ResourceCleanup()
    cleanup.kill_hung_processes(pattern="pytest", timeout=60)

    # Clean temporary files
    cleanup.clean_temp_files(older_than_days=7)

    # Release specific port
    cleanup.release_port(5000)
"""

import logging
import re
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)


class ResourceCleanup:
    """Utilities for cleaning up system resources."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        """Initialize resource cleanup.

        Args:
            workspace_root: Root directory of workspace
        """
        self.workspace_root = workspace_root or Path.cwd()
        logger.info("🧹 ResourceCleanup initialized")
        logger.info(f"   Workspace: {self.workspace_root}")

    def find_hung_processes(
        self,
        pattern: str | None = None,
        timeout_seconds: int | None = None,
    ) -> list[psutil.Process]:
        """Find processes matching pattern that may be hung.

        Args:
            pattern: Regex pattern to match against process name or cmdline
            timeout_seconds: Consider processes running longer than this hung

        Returns:
            List of potentially hung processes
        """
        hung_processes = []
        pattern_re = re.compile(pattern, re.IGNORECASE) if pattern else None

        for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
            try:
                # Check pattern match
                if pattern_re:
                    name_match = pattern_re.search(proc.info["name"])
                    cmdline_match = (
                        pattern_re.search(" ".join(proc.info["cmdline"]))
                        if proc.info["cmdline"]
                        else None
                    )
                    if not (name_match or cmdline_match):
                        continue

                # Check timeout
                if timeout_seconds:
                    runtime = time.time() - proc.info["create_time"]
                    if runtime > timeout_seconds:
                        hung_processes.append(proc)
                else:
                    hung_processes.append(proc)

            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                continue

        return hung_processes

    def kill_hung_processes(
        self,
        pattern: str,
        timeout_seconds: int | None = None,
        force: bool = False,
    ) -> int:
        """Kill processes matching pattern.

        Args:
            pattern: Regex pattern to match processes
            timeout_seconds: Only kill processes running longer than this
            force: Use SIGKILL (True) vs SIGTERM (False)

        Returns:
            Number of processes killed
        """
        hung_procs = self.find_hung_processes(pattern, timeout_seconds)

        if not hung_procs:
            logger.info(f"No hung processes found matching '{pattern}'")
            return 0

        logger.warning(f"Found {len(hung_procs)} hung processes matching '{pattern}'")

        killed_count = 0
        for proc in hung_procs:
            try:
                logger.info(f"Killing process {proc.pid}: {proc.name()}")
                if force:
                    proc.kill()  # SIGKILL
                else:
                    proc.terminate()  # SIGTERM

                # Wait for process to die
                proc.wait(timeout=5)
                killed_count += 1
                logger.info(f"✅ Process {proc.pid} terminated")

            except psutil.NoSuchProcess:
                logger.info(f"Process {proc.pid} already terminated")
                killed_count += 1
            except psutil.TimeoutExpired:
                logger.warning(f"Process {proc.pid} did not terminate, forcing...")
                try:
                    proc.kill()
                    killed_count += 1
                except Exception as e:
                    logger.error(f"Failed to kill process {proc.pid}: {e}")
            except Exception as e:
                logger.error(f"Error killing process {proc.pid}: {e}")

        logger.info(f"✅ Killed {killed_count}/{len(hung_procs)} processes")
        return killed_count

    def release_port(self, port: int, force: bool = True) -> bool:
        """Release a port by killing processes using it.

        Args:
            port: Port number to release
            force: Force kill processes

        Returns:
            True if port released, False otherwise
        """
        logger.info(f"Attempting to release port {port}")

        # Find processes using the port
        using_port = []
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == port:
                try:
                    proc = psutil.Process(conn.pid)
                    using_port.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    logger.debug("Suppressed psutil", exc_info=True)

        if not using_port:
            logger.info(f"Port {port} is already free")
            return True

        logger.warning(f"Port {port} is used by {len(using_port)} process(es)")

        # Kill processes
        for proc in using_port:
            try:
                logger.info(f"Killing process {proc.pid} ({proc.name()}) using port {port}")
                if force:
                    proc.kill()
                else:
                    proc.terminate()
                proc.wait(timeout=5)
            except Exception as e:
                logger.error(f"Failed to kill process {proc.pid}: {e}")
                return False

        logger.info(f"✅ Port {port} released")
        return True

    def clean_temp_files(self, older_than_days: int = 7, patterns: list[str] | None = None) -> int:
        """Clean temporary files from workspace.

        Args:
            older_than_days: Delete files older than this many days
            patterns: Glob patterns for files to clean (default: common temp patterns)

        Returns:
            Number of files deleted
        """
        if patterns is None:
            patterns = [
                "**/__pycache__",
                "**/*.pyc",
                "**/*.pyo",
                "**/.pytest_cache",
                "**/.mypy_cache",
                "**/.ruff_cache",
                "**/tmp_*",
                "**/*.tmp",
                "**/*.log",  # Be careful with this one
            ]

        cutoff_time = datetime.now() - timedelta(days=older_than_days)
        deleted_count = 0

        logger.info(f"Cleaning temporary files (older than {older_than_days} days)")

        for pattern in patterns:
            for path in self.workspace_root.glob(pattern):
                try:
                    # Check file age
                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                    if mtime < cutoff_time:
                        if path.is_file():
                            path.unlink()
                            deleted_count += 1
                            logger.debug(f"Deleted file: {path}")
                        elif path.is_dir():
                            shutil.rmtree(path)
                            deleted_count += 1
                            logger.debug(f"Deleted directory: {path}")
                except Exception as e:
                    logger.warning(f"Failed to delete {path}: {e}")

        logger.info(f"✅ Deleted {deleted_count} temporary files/directories")
        return deleted_count

    def clean_stale_locks(self, lock_dir: Path | None = None) -> int:
        """Remove stale lock files.

        Args:
            lock_dir: Directory containing lock files (default: workspace/.locks)

        Returns:
            Number of lock files removed
        """
        lock_dir = lock_dir or (self.workspace_root / ".locks")

        if not lock_dir.exists():
            logger.info("No lock directory found")
            return 0

        removed_count = 0
        for lock_file in lock_dir.glob("*.lock"):
            try:
                # Check if process owning lock still exists
                # Lock file format: <process_name>_<pid>.lock
                if match := re.match(r".*_(\d+)\.lock$", lock_file.name):
                    pid = int(match.group(1))
                    if not psutil.pid_exists(pid):
                        lock_file.unlink()
                        removed_count += 1
                        logger.info(f"Removed stale lock: {lock_file.name}")
                else:
                    # Unknown format, check age
                    age_hours = (time.time() - lock_file.stat().st_mtime) / 3600
                    if age_hours > 24:
                        lock_file.unlink()
                        removed_count += 1
                        logger.info(f"Removed old lock: {lock_file.name}")

            except Exception as e:
                logger.warning(f"Failed to remove lock {lock_file}: {e}")

        logger.info(f"✅ Removed {removed_count} stale locks")
        return removed_count

    def cleanup_all(
        self,
        kill_hung: bool = True,
        clean_temp: bool = True,
        clean_locks: bool = True,
        process_pattern: str | None = None,
        process_timeout: int = 300,
    ) -> dict:
        """Run comprehensive cleanup.

        Args:
            kill_hung: Kill hung processes
            clean_temp: Clean temporary files
            clean_locks: Clean stale locks
            process_pattern: Pattern for hung processes (default: Python/Node)
            process_timeout: Consider processes hung after this many seconds

        Returns:
            Dictionary with cleanup statistics
        """
        logger.info("🧹 Running comprehensive cleanup...")
        results = {"processes_killed": 0, "temp_files_deleted": 0, "locks_removed": 0}

        if kill_hung:
            # Kill hung Python processes
            pattern = process_pattern or r"(python|node|npm|pytest)"
            results["processes_killed"] = self.kill_hung_processes(
                pattern, timeout_seconds=process_timeout
            )

        if clean_temp:
            results["temp_files_deleted"] = self.clean_temp_files(older_than_days=7)

        if clean_locks:
            results["locks_removed"] = self.clean_stale_locks()

        logger.info("✅ Comprehensive cleanup complete")
        logger.info(f"   Processes killed: {results['processes_killed']}")
        logger.info(f"   Temp files deleted: {results['temp_files_deleted']}")
        logger.info(f"   Locks removed: {results['locks_removed']}")

        return results


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Resource cleanup utilities")
    parser.add_argument("--kill-hung", action="store_true", help="Kill hung processes")
    parser.add_argument(
        "--pattern", type=str, default=r"(python|node|pytest)", help="Process pattern"
    )
    parser.add_argument("--timeout", type=int, default=300, help="Hung process timeout (seconds)")
    parser.add_argument("--clean-temp", action="store_true", help="Clean temporary files")
    parser.add_argument("--clean-locks", action="store_true", help="Clean stale locks")
    parser.add_argument("--release-port", type=int, metavar="PORT", help="Release specific port")
    parser.add_argument("--all", action="store_true", help="Run all cleanup tasks")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    cleanup = ResourceCleanup()

    if args.release_port:
        cleanup.release_port(args.release_port)
    elif args.all:
        cleanup.cleanup_all(
            kill_hung=True,
            clean_temp=True,
            clean_locks=True,
            process_pattern=args.pattern,
            process_timeout=args.timeout,
        )
    else:
        if args.kill_hung:
            cleanup.kill_hung_processes(args.pattern, timeout_seconds=args.timeout)
        if args.clean_temp:
            cleanup.clean_temp_files()
        if args.clean_locks:
            cleanup.clean_stale_locks()
