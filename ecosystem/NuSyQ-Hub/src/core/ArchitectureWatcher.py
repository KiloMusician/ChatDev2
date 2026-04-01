#!/usr/bin/env python3
"""Architecture Watcher - Monitors and validates system architecture.

Tracks:
- File structure changes
- Module dependencies
- Architecture violations
- Pattern compliance
- Integration health
"""

import argparse
import contextlib
import logging
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # pragma: no cover - optional dependency
    FileSystemEventHandler = None
    Observer = None

try:
    from src.core.ArchitectureScanner import KILOArchitectureScanner
except ImportError:  # pragma: no cover - optional integration
    KILOArchitectureScanner = None


class ArchitectureWatcher:
    """Watches and validates system architecture."""

    def __init__(self, root_path: Path | None = None) -> None:
        """Initialize architecture watcher.

        Args:
            root_path: Root path of the repository
        """
        self.root_path = root_path or Path.cwd()
        self.monitored_paths = [
            self.root_path / "src",
            self.root_path / "tests",
            self.root_path / "deploy",
        ]

        # Architecture rules
        self.rules = {
            "max_module_depth": 5,
            "required_tests": True,
            "required_docs": True,
            "forbidden_circular_imports": True,
        }

        logger.info("Architecture Watcher initialized")

    def health_check(self) -> dict[str, Any]:
        """Check architecture health.

        Returns:
            Health status report
        """
        health: dict[str, Any] = {
            "healthy": True,
            "issues": [],
            "stats": {},
        }

        # Check if monitored paths exist
        for path in self.monitored_paths:
            if not path.exists():
                health["healthy"] = False
                health["issues"].append(f"Missing path: {path}")

        # Count Python files
        src_path = self.root_path / "src"
        if src_path.exists():
            py_files = list(src_path.rglob("*.py"))
            health["stats"]["python_files"] = len(py_files)

            # Check for __init__.py in packages
            packages = [p for p in src_path.rglob("*") if p.is_dir()]
            init_files = [p / "__init__.py" for p in packages]
            missing_init = [p for p in init_files if not p.exists()]

            if missing_init:
                health["issues"].append(f"{len(missing_init)} packages missing __init__.py")

        # Check tests
        tests_path = self.root_path / "tests"
        if tests_path.exists():
            test_files = list(tests_path.rglob("test_*.py"))
            health["stats"]["test_files"] = len(test_files)
        elif self.rules["required_tests"]:
            health["healthy"] = False
            health["issues"].append("No tests directory found")

        return health

    def scan_violations(self) -> list[dict[str, Any]]:
        """Scan for architecture violations.

        Returns:
            List of violations found
        """
        violations: list[dict[str, Any]] = []

        # Check module depth
        src_path = self.root_path / "src"
        if src_path.exists():
            for py_file in src_path.rglob("*.py"):
                relative = py_file.relative_to(src_path)
                depth = len(relative.parts) - 1  # Exclude filename

                if depth > self.rules["max_module_depth"]:
                    violations.append(
                        {
                            "type": "excessive_depth",
                            "file": str(relative),
                            "depth": depth,
                            "max_allowed": self.rules["max_module_depth"],
                        }
                    )

        return violations

    def generate_report(self) -> dict[str, Any]:
        """Generate architecture health report.

        Returns:
            Comprehensive health report
        """
        health = self.health_check()
        violations = self.scan_violations()

        report = {
            "timestamp": Path.cwd(),
            "health": health,
            "violations": violations,
            "summary": {
                "healthy": health["healthy"] and len(violations) == 0,
                "issue_count": len(health["issues"]) + len(violations),
            },
        }

        try:
            from src.system.agent_awareness import emit as _emit

            _issue_count = report["summary"]["issue_count"]
            _lvl = "WARNING" if _issue_count > 0 else "INFO"
            _emit(
                "system",
                f"Architecture report: healthy={report['summary']['healthy']}"
                f" issues={_issue_count} violations={len(violations)}",
                level=_lvl,
                source="architecture_watcher",
            )
        except Exception:
            pass

        return report


if FileSystemEventHandler is not None:

    class ArchitectureUpdateHandler(FileSystemEventHandler):
        """Watchdog handler that debounces architecture scans."""

        def __init__(
            self,
            scanner: "KILOArchitectureScanner",
            debounce_time: float = 2.0,
        ) -> None:
            """Initialize ArchitectureUpdateHandler with scanner, debounce_time."""
            self.scanner = scanner
            self.debounce_time = debounce_time
            self.last_update: float = 0.0
            self.update_timer: threading.Timer | None = None

        def on_any_event(self, event) -> None:
            if getattr(event, "is_directory", False):
                return
            if any(skip in event.src_path for skip in (".git", "__pycache__", ".tmp", "~")):
                return

            self.last_update = time.time()
            if self.update_timer:
                self.update_timer.cancel()

            self.update_timer = threading.Timer(self.debounce_time, self._perform_update)
            self.update_timer.start()

        def _perform_update(self) -> None:
            with contextlib.suppress(OSError, FileNotFoundError, PermissionError, ValueError):
                self.scanner.run_full_scan()

else:
    ArchitectureUpdateHandler = None


class KILOArchitectureWatcher:
    """Real-time architecture watcher using watchdog (optional dependency)."""

    def __init__(self, repo_root: str | None = None) -> None:
        """Initialize KILOArchitectureWatcher with repo_root."""
        if Observer is None or FileSystemEventHandler is None:
            raise RuntimeError(
                "watchdog is required for KILOArchitectureWatcher. Install with: pip install watchdog"
            )
        if KILOArchitectureScanner is None:
            raise RuntimeError("KILOArchitectureScanner unavailable for watcher.")
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).parent.parent.parent
        self.scanner = KILOArchitectureScanner(str(self.repo_root))
        self.observer: Observer | None = None

    def start_watching(self) -> None:
        """Start real-time architecture monitoring."""
        self.scanner.run_full_scan()
        if ArchitectureUpdateHandler is None:
            raise RuntimeError(
                "ArchitectureUpdateHandler unavailable because watchdog is not installed."
            )

        event_handler = ArchitectureUpdateHandler(self.scanner)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.repo_root), recursive=True)
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_watching()

    def stop_watching(self) -> None:
        """Stop the watcher."""
        if self.observer:
            self.observer.stop()
            self.observer.join()


# Singleton instance
_watcher: ArchitectureWatcher | None = None


def get_architecture_watcher(root_path: Path | None = None) -> ArchitectureWatcher:
    """Get or create architecture watcher singleton.

    Args:
        root_path: Root path of the repository

    Returns:
        Architecture watcher instance
    """
    global _watcher
    if _watcher is None:
        _watcher = ArchitectureWatcher(root_path=root_path)
    return _watcher


def _print_report(report: dict[str, Any]) -> None:
    logger.info("\n" + "=" * 60)
    logger.info("ARCHITECTURE HEALTH REPORT")
    logger.info("=" * 60)

    logger.info(
        f"\nOverall Health: {'HEALTHY' if report['summary']['healthy'] else 'ISSUES FOUND'}"
    )
    logger.info(f"Total Issues: {report['summary']['issue_count']}")

    if report["health"]["stats"]:
        logger.info("\nStatistics:")
        for key, value in report["health"]["stats"].items():
            logger.info(f"  {key}: {value}")

    if report["health"]["issues"]:
        logger.info("\nIssues:")
        for issue in report["health"]["issues"]:
            logger.info(f"  - {issue}")

    if report["violations"]:
        logger.info("\nViolations:")
        for violation in report["violations"]:
            logger.info(f"  - {violation['type']}: {violation['file']}")

    logger.info("\n" + "=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Architecture watcher")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run continuously instead of a single report.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Seconds between reports when running in watch mode.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    watcher = get_architecture_watcher()

    if args.watch:
        logger.info("ARCHITECTURE WATCHER READY")
        try:
            while True:
                _print_report(watcher.generate_report())
                time.sleep(max(10, args.interval))
        except KeyboardInterrupt:
            logger.info("Architecture watcher stopped.")
    else:
        _print_report(watcher.generate_report())
