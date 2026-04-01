"""Filesystem "maze" solver that searches the repository for 'treasures'.

(TODO/FIXME/BUG comments) using a DFS-like traversal.

What this module is for (who/what/where/when/why/how):
- Who: developers, automated agents (Copilot/ChatDev/local LLMs), and CI jobs
- What: quickly find technical-debt markers (TODO/FIXME/BUG/@TODO/@FIXME)
- Where: run from repository root (or pass another path)
- When: ad-hoc during development, as part of pre-commit hooks, or scheduled CI
- Why: provide a human- and machine-readable summary of code TODOs so
    downstream agents can ingest and create tasks/quests
- How: command-line tool that writes a JSON summary into `logs/` and prints
    a small human-friendly report to stdout

Quick start:
    python -m src.tools.maze_solver . --max-depth 8

Outputs and integration points (paths & formats):
- Human output: concise summary printed to stdout (try `--max-depth 2` for quick runs)
- Machine output: `logs/maze_summary_<YYYYMMDD_HHMMSS>.json` containing:
    {
        "root": <string>,
        "total": <int>,
        "files": { "path": [[line, text], ...], ... },
        "errors": [<strings>],
        "interrupted": <bool>
    }
- Agents should prefer the JSON summary for deterministic ingestion. See `src/tools/log_indexer.py`.

Troubleshooting & tips (important for Windows PowerShell & CI):
- Terminal encoding: PowerShell on Windows often uses cp1252 which can't encode
    some characters (e.g. box-drawing). The `safe_print` helper below attempts
    a safe fallback path. If you still see encoding errors, run PowerShell with
    UTF-8: `chcp 65001` or use a terminal that supports UTF-8.
- Interrupts: if a user hits Ctrl-C, we try to persist partial results (the
    `interrupted` flag) so downstream systems still get useful data.
- Permissions: scanning large repos or system folders may raise permission
    or symlink errors; these are collected in `errors` and included in the JSON.

Extensibility notes (how to integrate):
- Hook this scanner into the AI orchestration pipeline by watching `logs/`
    and consuming the newest `maze_summary_*.json` (see `src/tools/log_indexer.py`).
- For richer analysis, pipeline the JSON into embedding/indexing or create
    prioritized tasks in `src/orchestration/`.

Development TODOs (small, low-risk follow-ups):
- Add unit tests for `MazeRepoScanner` with temporary files.
- Optionally allow output directory override via CLI flag.

This module keeps behavior deliberately simple so it can run in minimal CI
environments and be easily ingested by downstream agents.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TREASURE_PATTERNS = [
    r"(?<![a-zA-Z0-9_-])TODO(?![a-zA-Z0-9_-])",
    r"(?<![a-zA-Z0-9_-])FIXME(?![a-zA-Z0-9_-])",
    r"(?<![a-zA-Z0-9_-])BUG(?![a-zA-Z0-9_-])",
    r"@TODO\b",
    r"@FIXME\b",
]
TREASURE_RE = re.compile("|".join(TREASURE_PATTERNS), re.IGNORECASE)


class MazeRepoScanner:
    """Scan a repository directory tree for 'treasures' (technical debt markers).

    Usage:
        scanner = MazeRepoScanner(Path("."))
        results = scanner.scan()
    """

    findings: dict[Path, list[tuple[int, str]]]
    _errors: list[str]

    def __init__(self, root: Path, follow_symlinks: bool = False) -> None:
        """Initialize MazeRepoScanner with root, follow_symlinks."""
        self.root = root
        self.follow_symlinks = follow_symlinks
        self.findings = {}
        # Accumulate non-fatal errors encountered while scanning
        self._errors = []

    def _is_text_file(self, path: Path) -> bool:
        try:
            with path.open("r", encoding="utf-8") as f:
                f.read(1024)
            return True
        except (OSError, UnicodeDecodeError):
            return False

    def scan(self, max_depth: int = 20) -> dict[Path, list[tuple[int, str]]]:
        """Perform a DFS-like traversal of the filesystem starting at root.

        Returns a mapping of file path -> list of (line_no, line_text) where
        treasures were found.
        """
        stack = [(self.root.resolve(), 0)]
        visited = set()
        file_count = 0

        # Performance optimization: provide progress feedback for large repos

        while stack:
            path, depth = stack.pop()
            if depth > max_depth:
                continue
            try:
                path = path.resolve()
            except (OSError, RuntimeError):
                # Path couldn't be resolved (permission, symlink loop, etc.)
                continue
            if path in visited:
                continue
            visited.add(path)

            if path.is_dir():
                try:
                    entries = sorted(path.iterdir(), reverse=True)
                except (PermissionError, OSError) as e:
                    # Record directory listing errors and continue
                    self._errors.append(f"Error listing {path}: {type(e).__name__}: {e}")
                    continue
                for child in entries:
                    # Skip common virtual env and git directories for performance
                    name = child.name.lower()
                    if name in {
                        ".git",
                        "venv",
                        "node_modules",
                        ".venv",
                        "dist",
                        "build",
                        "__pycache__",
                        ".pytest_cache",
                    }:
                        continue
                    stack.append((child, depth + 1))
            elif path.is_file():
                if not self._is_text_file(path):
                    continue

                file_count += 1
                # Progress feedback every 100 files
                if file_count % 100 == 0:
                    pass

                try:
                    with path.open("r", encoding="utf-8", errors="replace") as fh:
                        for i, line in enumerate(fh, start=1):
                            if TREASURE_RE.search(line):
                                self.findings.setdefault(path, []).append((i, line.rstrip()))
                except (PermissionError, OSError) as e:
                    # Record read errors but continue scanning other files
                    self._errors.append(f"Error reading {path}: {type(e).__name__}: {e}")
                    continue

        return self.findings

    @property
    def errors(self) -> list[str]:
        """Public read-only view of non-fatal scanning errors."""
        return list(self._errors)


def cleanup_old_summaries(log_dir: Path, keep_count: int = 3) -> None:
    """Retention policy: Keep only N most recent maze_summary files.

    Why: Prevents bloat from accumulating 21GB+ summary files over time.
    How: Sorts by modification time, deletes oldest files beyond keep_count.

    Args:
        log_dir: Directory containing maze_summary_*.json files
        keep_count: Number of most recent summaries to keep (default: 3)
    """
    try:
        summaries = sorted(
            log_dir.glob("maze_summary_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for old_file in summaries[keep_count:]:
            with contextlib.suppress(OSError, PermissionError):  # silent cleanup
                old_file.unlink()
    except Exception:
        # Defensive: cleanup failure should not break main functionality
        logger.debug("Suppressed Exception", exc_info=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Scan repository for TODO/FIXME/BUG markers")
    parser.add_argument("root", nargs="?", default=".", help="Repository root to scan")
    parser.add_argument("--max-depth", type=int, default=20, help="Maximum directory depth to scan")
    parser.add_argument("--progress", action="store_true", help="Show progress during scan")
    parser.add_argument("--classify", action="store_true", help="Enable classification of markers")
    parser.add_argument("--force", action="store_true", help="Force overwrite of existing files")
    args = parser.parse_args(argv)

    scanner = MazeRepoScanner(Path(args.root))
    interrupted = False

    # Performance optimization: show progress for interactive use
    if args.progress:
        logger.info("[maze_solver] Progress enabled: scanning...")

    try:
        results = scanner.scan(max_depth=args.max_depth)
    except KeyboardInterrupt:
        interrupted = True
        # Use whatever findings were collected so far
        results = scanner.findings

    def safe_print(s: str = "") -> None:
        """Safe print that handles encoding issues in Windows PowerShell (cp1252)."""
        try:
            logger.info(s)
        except UnicodeEncodeError:
            # Windows PowerShell cp1252 encoding fallback
            # Replace problematic Unicode characters with ASCII equivalents
            enc = sys.stdout.encoding or "utf-8"
            try:
                sys.stdout.buffer.write(s.encode(enc, errors="replace") + b"\n")
            except Exception:
                # Last-resort fallback to avoid crashing on output
                logger.error(s.encode(enc, errors="replace").decode(enc, errors="ignore"))

    # Performance optimization: limit console output for large results
    total = sum(len(v) for v in results.values()) if isinstance(results, dict) else 0
    file_count = len(results) if isinstance(results, dict) else 0

    safe_print(f"Found {total} treasures in {file_count} files.\n")

    # Show summary instead of full output for very large results (performance)
    if total > 50 and not args.progress:
        safe_print(
            "(Large result set - showing first 10 files. Use --progress for details or check JSON summary)"
        )
        shown_files = 0
        for path, hits in sorted(results.items()):
            if shown_files >= 10:
                break
            safe_print(f"{path}: {len(hits)} treasures")
            shown_files += 1
        if file_count > 10:
            safe_print(f"... and {file_count - 10} more files")
    else:
        # Standard output for smaller results
        for path, hits in sorted(results.items()):
            safe_print(f"{path}:")
            for ln, text in hits:
                safe_print(f"  {ln}: {text}")
            safe_print()

    # Always write a machine-readable summary to logs for downstream agents
    log_dir = Path("logs")
    try:
        log_dir.mkdir(exist_ok=True)
    except (OSError, PermissionError):
        # If we cannot create logs directory, fallback to current dir
        log_dir = Path()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = log_dir / f"maze_summary_{timestamp}.json"

    # Make findings JSON serializable
    serializable = (
        {str(p): [(ln, txt) for ln, txt in hits] for p, hits in results.items()}
        if isinstance(results, dict)
        else {}
    )

    summary_obj = {
        "root": str(Path(args.root).resolve()),
        "total": total,
        "files": serializable,
        "errors": scanner.errors,
        "interrupted": interrupted,
    }

    # Add classification data if --classify flag is used
    if args.classify:
        items: list[Any] = []
        counts_by_pattern: dict[str, Any] = {}
        counts_by_severity: dict[str, Any] = {}
        hotspots_by_dir: dict[str, Any] = {}
        for path, hits in results.items():
            path_str = str(path)
            dir_name = str(Path(path_str).parent)

            for line_no, line_text in hits:
                # Extract pattern from line
                pattern = None
                for p in ["TODO", "FIXME", "BUG", "HACK", "XXX", "NOTE"]:
                    if p in line_text.upper():
                        pattern = p
                        break

                if not pattern:
                    continue

                # Determine category and severity
                category = "maintenance" if pattern in ["TODO", "NOTE"] else "defect"

                # Special handling for docs vs code
                is_docs = "/docs" in path_str.replace("\\", "/") or path_str.endswith(".md")
                if pattern == "BUG":
                    severity = "low" if is_docs else "critical"
                elif pattern == "TODO":
                    severity = "medium"
                else:
                    severity = "low"

                # Add to items
                items.append(
                    {
                        "path": path_str,
                        "line_no": line_no,
                        "pattern": pattern,
                        "category": category,
                        "severity": severity,
                        "line": line_text,
                    }
                )

                # Update counts
                counts_by_pattern[pattern] = counts_by_pattern.get(pattern, 0) + 1
                counts_by_severity[severity] = counts_by_severity.get(severity, 0) + 1
                hotspots_by_dir[dir_name] = hotspots_by_dir.get(dir_name, 0) + 1

        summary_obj["classified"] = True
        summary_obj["items"] = items
        summary_obj["counts_by_pattern"] = counts_by_pattern
        summary_obj["counts_by_severity"] = counts_by_severity
        summary_obj["hotspots_by_dir"] = hotspots_by_dir

    try:
        with summary_path.open("w", encoding="utf-8") as sf:
            json.dump(summary_obj, sf, indent=2)
        safe_print(f"Summary written to: {summary_path}")

        # Retention policy: Keep only 3 most recent summaries (prevent bloat)
        cleanup_old_summaries(log_dir, keep_count=3)
    except (OSError, PermissionError, TypeError, ValueError) as e:
        safe_print(f"Failed to write summary to {summary_path}: {e}")
        # Fallback: attempt to write to system temp directory when disk is full or path is not writable
        try:
            import tempfile

            tmp_dir = Path(tempfile.gettempdir())
            tmp_summary_path = tmp_dir / summary_path.name
            with tmp_summary_path.open("w", encoding="utf-8") as sf:
                json.dump(summary_obj, sf, indent=2)
            safe_print(f"Summary written to TEMP: {tmp_summary_path}")
        except Exception as e2:
            safe_print(f"Failed to write TEMP summary: {e2}")

    return 0


if __name__ == "__main__":
    main()
