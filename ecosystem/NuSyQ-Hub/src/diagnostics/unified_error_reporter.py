"""Unified Error Reporter - Ground Truth Error Reporting System.

=============================================================

This module provides a consistent, authoritative error reporting system
that all agents (Copilot, Claude, Ollama, etc.) can use to get the same
signal about code quality across all three repositories (NuSyQ-Hub,
SimulatedVerse, NuSyQ).

Purpose:
--------
- Single source of truth for error counts and types
- Consistent reporting across all agents
- Ground truth derived from tool scan results (VS Code counts shown separately)
- Categorization by severity and type
- Support for multi-repo scanning

Architecture:
--------------
ErrorDiagnostic
    ├── ID: Unique error identifier
    ├── Severity: error/warning/info
    ├── Type: linting/type/syntax/logic
    ├── File: Full path
    ├── Line: Line number
    ├── Message: Description
    └── Repo: Which repo (nusyq-hub, simverse, nusyq)

RepoScan
    ├── Repo name
    ├── Total errors/warnings/infos
    ├── Categorized diagnostics
    └── Timestamp

UnifiedErrorReporter
    ├── Scan all three repos
    ├── Collect from pylint, mypy, ruff
    ├── Generate consistent reports
    └── Log to quest system for persistence
"""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

SCAN_TARGET_DIRS = (
    "src",
    "tests",
    "scripts",
    "core",
    "ml",
    "tools",
)
SKIP_DIRECTORY_NAMES = {
    ".git",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "env",
    "venv",
    ".venv",
}
SCAN_PATH_PRIORITY = {
    "src": 0,
    "core": 1,
    "ml": 2,
    "scripts": 3,
    "tests": 4,
    "tools": 5,
}
MAX_MYPY_FILES = int(os.getenv("NUSYQ_ERROR_SCAN_MAX_MYPY_FILES", "24"))
MAX_QUICK_RUFF_FILES = int(os.getenv("NUSYQ_ERROR_SCAN_MAX_QUICK_RUFF_FILES", "30"))
QUICK_RUFF_TIMEOUT_SECONDS = int(os.getenv("NUSYQ_ERROR_SCAN_RUFF_QUICK_TIMEOUT", "90"))
QUICK_RUFF_RETRY_MAX_FILES = int(os.getenv("NUSYQ_ERROR_SCAN_RUFF_QUICK_RETRY_MAX_FILES", "12"))
QUICK_RUFF_RETRY_TIMEOUT_SECONDS = int(os.getenv("NUSYQ_ERROR_SCAN_RUFF_QUICK_RETRY_TIMEOUT", "30"))
FULL_RUFF_TIMEOUT_SECONDS = int(os.getenv("NUSYQ_ERROR_SCAN_RUFF_FULL_TIMEOUT", "300"))
FULL_RUFF_RETRY_MAX_FILES = int(os.getenv("NUSYQ_ERROR_SCAN_RUFF_FULL_RETRY_MAX_FILES", "40"))
FULL_RUFF_RETRY_TIMEOUT_SECONDS = int(os.getenv("NUSYQ_ERROR_SCAN_RUFF_FULL_RETRY_TIMEOUT", "60"))
MAX_PYLINT_FILES = int(os.getenv("NUSYQ_ERROR_SCAN_MAX_PYLINT_FILES", "250"))
PYLINT_TIMEOUT_SECONDS = int(os.getenv("NUSYQ_ERROR_SCAN_PYLINT_TIMEOUT", "240"))
PYLINT_BATCH_FILES = int(os.getenv("NUSYQ_ERROR_SCAN_PYLINT_BATCH_FILES", "80"))
PYLINT_RETRY_MAX_FILES = int(os.getenv("NUSYQ_ERROR_SCAN_PYLINT_RETRY_MAX_FILES", "20"))
PYLINT_RETRY_TIMEOUT_SECONDS = int(os.getenv("NUSYQ_ERROR_SCAN_PYLINT_RETRY_TIMEOUT", "90"))
MYPY_TIMEOUT_SECONDS = int(os.getenv("NUSYQ_ERROR_SCAN_MYPY_TIMEOUT", "180"))
MYPY_RETRY_MAX_FILES = int(os.getenv("NUSYQ_ERROR_SCAN_MYPY_RETRY_MAX_FILES", "8"))
MYPY_RETRY_TIMEOUT_SECONDS = int(os.getenv("NUSYQ_ERROR_SCAN_MYPY_RETRY_TIMEOUT", "120"))

logger = logging.getLogger(__name__)

try:
    from src.utils.repo_path_resolver import get_repo_path
except ImportError:
    get_repo_path = None  # type: ignore[assignment]


def _quick_e501_debt_scan_enabled() -> bool:
    """Return True when quick-mode E501 debt scanning is explicitly enabled."""
    raw = os.getenv("NUSYQ_ERROR_SCAN_INCLUDE_QUICK_E501_DEBT", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class ErrorSeverity(str, Enum):
    """Error severity levels matching VS Code conventions."""

    ERROR = "error"  # Code won't run
    WARNING = "warning"  # Code runs but problematic
    INFO = "info"  # Code quality, style
    HINT = "hint"  # Minor suggestions


class ErrorType(str, Enum):
    """Error type categories."""

    LINTING = "linting"  # Style, conventions (pylint, ruff)
    TYPE = "type"  # Type checking (mypy)
    SYNTAX = "syntax"  # Syntax errors (py_compile)
    IMPORT = "import"  # Import issues
    LOGIC = "logic"  # Potential bugs
    ASYNC = "async"  # Async/await issues
    EXCEPTION = "exception"  # Exception handling
    COMPLEXITY = "complexity"  # Cognitive/cyclomatic complexity


class RepoName(str, Enum):
    """The three repos in the ecosystem."""

    NUSYQ_HUB = "nusyq-hub"
    SIMULATED_VERSE = "simulated-verse"
    NUSYQ = "nusyq"


@dataclass
class ErrorDiagnostic:
    """A single error/warning/info diagnostic."""

    error_id: str  # Unique identifier
    severity: ErrorSeverity  # error/warning/info
    error_type: ErrorType  # Category of error
    repo: RepoName  # Which repository
    file_path: Path  # Full path to file
    line_num: int  # Line number (1-indexed)
    column_num: int = 0  # Column number (0-indexed)
    message: str = ""  # Error description
    source: str = ""  # Tool that detected it (pylint, mypy, ruff)
    suggestion: str = ""  # How to fix it (if known)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def __hash__(self) -> int:
        """Make diagnostics hashable for deduplication."""
        return hash((str(self.file_path), self.line_num, self.message))


@dataclass
class RepoScan:
    """Results from scanning one repository."""

    repo: RepoName
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    diagnostics: list[ErrorDiagnostic] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        """Get error summary for this repo."""
        by_severity: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_source: dict[str, int] = {}

        for diag in self.diagnostics:
            # Count by severity
            sev = diag.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

            # Count by type
            etype = diag.error_type.value
            by_type[etype] = by_type.get(etype, 0) + 1

            # Count by source
            src = diag.source
            by_source[src] = by_source.get(src, 0) + 1

        summary = {
            "repo": self.repo.value,
            "total": len(self.diagnostics),
            "by_severity": by_severity,
            "by_type": by_type,
            "by_source": by_source,
        }
        if self.stats:
            summary["path"] = self.stats.get("path")
            summary["python_targets"] = self.stats.get("python_targets")
            summary["python_target_names"] = self.stats.get("python_target_names")
        return summary


class UnifiedErrorReporter:
    """Ground-truth error reporting system for the entire ecosystem."""

    def __init__(
        self,
        hub_path: Path | None = None,
        include_repos: Sequence[RepoName] | None = None,
        exclude_repos: Sequence[RepoName] | None = None,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        """Initialize UnifiedErrorReporter with hub_path, include_repos, exclude_repos."""
        # Default paths
        if hub_path is None:
            hub_path = Path(__file__).parent.parent.parent

        include_list = list(dict.fromkeys(include_repos)) if include_repos else []
        exclude_set = set(exclude_repos or [])

        repo_map: dict[RepoName, Path] = {RepoName.NUSYQ_HUB: hub_path}

        simulated_verse = self._resolve_repo_path(
            "SIMULATEDVERSE_ROOT",
            [
                hub_path.parent / "SimulatedVerse" / "SimulatedVerse",
                hub_path.parent / "SimulatedVerse",
                hub_path.parent.parent / "SimulatedVerse" / "SimulatedVerse",
                hub_path.parent.parent / "SimulatedVerse",
            ],
        )
        if simulated_verse:
            repo_map[RepoName.SIMULATED_VERSE] = simulated_verse

        nusyq_root = self._resolve_repo_path(
            "NUSYQ_ROOT",
            [
                hub_path.parent / "NuSyQ",
                hub_path.parent / "NuSyQ-Root",
                hub_path.parent.parent / "NuSyQ",
                hub_path.parent.parent / "NuSyQ-Root",
            ],
        )
        if nusyq_root:
            repo_map[RepoName.NUSYQ] = nusyq_root

        filtered: dict[RepoName, Path] = {}
        for repo_name, repo_path in repo_map.items():
            if include_list and repo_name not in include_list:
                continue
            if repo_name in exclude_set:
                continue
            filtered[repo_name] = repo_path
        self.include_filters = include_list
        self.exclude_filters = list(exclude_repos or [])
        self._target_repo_values = tuple(repo.value for repo in filtered)
        self.repos = filtered
        self.all_diagnostics: list[ErrorDiagnostic] = []
        self.scans: dict[RepoName, RepoScan] = {}
        self.vscode_counts_path = (
            hub_path / "docs" / "Reports" / "diagnostics" / "vscode_problem_counts.json"
        )
        self.export_paths: tuple[Path, ...] = (
            hub_path / "docs" / "Reports" / "diagnostics" / "vscode_problem_counts_tooling.json",
            hub_path / "docs" / "Reports" / "diagnostics" / "vscode_problem_counts.json",
            hub_path / "docs" / "Reports" / "diagnostics" / "vscode_diagnostics_export.json",
            hub_path / "data" / "diagnostics" / "vscode_diagnostics_export.json",
        )
        self.progress_callback = progress_callback
        self.reports_dir = hub_path / "docs" / "Reports" / "diagnostics"
        self.scan_mode = "full"
        self.scan_warnings: list[str] = []
        self.scan_deadline_ts: float | None = None
        self.quick_e501_debt_scan = _quick_e501_debt_scan_enabled()

    @property
    def target_repo_values(self) -> tuple[str, ...]:
        return self._target_repo_values

    def _emit_progress(self, event: str, **payload: Any) -> None:
        """Emit progress updates to an optional observer and the errors terminal."""
        if self.progress_callback is not None:
            try:
                self.progress_callback({"event": event, **payload})
            except Exception:
                logger.debug("Progress callback failed", exc_info=True)
        # Mirror scan events to the errors terminal for live watcher visibility
        try:
            from src.system.agent_awareness import emit as _emit

            if event in {"repo_complete", "tool_complete"}:
                repo = payload.get("repo", "?")
                tool = payload.get("tool", event)
                diag_count = payload.get("diagnostics", 0)
                level = "WARNING" if diag_count > 0 else "INFO"
                _emit(
                    "errors",
                    f"[{event}] {repo} {tool} diagnostics={diag_count}",
                    level=level,
                    source="error_reporter",
                )
        except Exception:
            pass

    def _resolve_repo_path(self, env_key: str, fallbacks: Sequence[Path]) -> Path | None:
        """Resolve a repo path, preferring valid Python targets over empty placeholders."""
        if get_repo_path:
            try:
                resolved = get_repo_path(env_key)
                if resolved.exists():
                    if self._python_targets(resolved):
                        return resolved
                    logger.warning(
                        "Resolved %s path %s has no Python targets; trying fallbacks.",
                        env_key,
                        resolved,
                    )
                else:
                    logger.warning(
                        "Resolved %s path %s does not exist; trying fallbacks.",
                        env_key,
                        resolved,
                    )
            except Exception:
                logger.debug("Suppressed Exception", exc_info=True)

        for candidate in fallbacks:
            if candidate.exists() and self._python_targets(candidate):
                return candidate
        for candidate in fallbacks:
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def _python_cmd() -> list[str]:
        """Return the active interpreter command for tool subprocesses."""
        return [sys.executable]

    @staticmethod
    def _ruff_cmd() -> list[str]:
        """Prefer the Ruff binary when available; otherwise use the active interpreter."""
        ruff_bin = shutil.which("ruff")
        if ruff_bin:
            return [ruff_bin]
        return [sys.executable, "-m", "ruff"]

    def _count_python_files(self, targets: Sequence[Path]) -> int:
        """Count Python files in targets for progress display."""
        rg_files = self._list_python_files_with_rg(targets)
        if rg_files is not None:
            return len(rg_files)

        count = 0
        for target in targets:
            if not target.exists():
                continue
            if target.is_file() and target.suffix == ".py":
                count += 1
                continue
            if not target.is_dir():
                continue
            for _root, dirs, files in os.walk(target):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRECTORY_NAMES]
                count += sum(1 for f in files if f.endswith(".py"))
        return count

    def _path_priority(self, path: Path) -> tuple[int, str]:
        """Prefer runtime code before tests and tools when sampling scan candidates."""
        for part in path.parts:
            if part in SCAN_PATH_PRIORITY:
                return (SCAN_PATH_PRIORITY[part], str(path))
        return (len(SCAN_PATH_PRIORITY) + 1, str(path))

    def _collect_python_files(self, targets: Sequence[Path], limit: int) -> list[Path]:
        """Collect up to ``limit`` Python files from scan targets."""
        collected: list[Path] = []
        if limit <= 0:
            return collected

        rg_files = self._list_python_files_with_rg(targets, limit=limit)
        if rg_files is not None:
            return sorted(rg_files, key=self._path_priority)[:limit]

        for target in targets:
            if not target.exists():
                continue
            if target.is_file():
                if target.suffix == ".py":
                    collected.append(target)
                if len(collected) >= limit:
                    break
                continue
            for path in target.rglob("*.py"):
                collected.append(path)
                if len(collected) >= limit:
                    break
            if len(collected) >= limit:
                break
        return sorted(collected, key=self._path_priority)[:limit]

    def _list_python_files_with_rg(
        self,
        targets: Sequence[Path],
        limit: int | None = None,
    ) -> list[Path] | None:
        """Use ripgrep for fast Python file discovery when available."""
        rg_bin = shutil.which("rg")
        if not rg_bin:
            return None

        file_targets = [target for target in targets if target.exists() and target.is_file()]
        dir_targets = [target for target in targets if target.exists() and target.is_dir()]

        collected: list[Path] = [target for target in file_targets if target.suffix == ".py"]
        if limit is not None and len(collected) >= limit:
            return collected[:limit]

        if not dir_targets:
            return collected

        cmd = [rg_bin, "--files", *[str(target) for target in dir_targets], "-g", "*.py"]
        try:
            result = self._run_with_heartbeat(cmd, label="python-file-discovery", timeout=30)
        except (subprocess.TimeoutExpired, OSError):
            return None
        if result.returncode not in {0, 1}:
            return None

        seen = {path.resolve() for path in collected}
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            path = Path(line)
            if not path.is_absolute():
                path = Path.cwd() / path
            try:
                resolved = path.resolve()
            except OSError:
                resolved = path
            if resolved in seen:
                continue
            collected.append(path)
            seen.add(resolved)
            if limit is not None and len(collected) >= limit:
                break
        return collected

    def _run_with_heartbeat(
        self,
        cmd: list[str],
        label: str,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        """Run command with bounded timeout and safe output capture."""
        _ = label
        effective_timeout = timeout
        if self.scan_deadline_ts is not None:
            remaining = max(1, int(self.scan_deadline_ts - time.time()))
            effective_timeout = min(timeout, remaining) if timeout else remaining

        if effective_timeout and effective_timeout <= 0:
            raise subprocess.TimeoutExpired(cmd, timeout)

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=effective_timeout if effective_timeout > 0 else None,
            check=False,
        )

    def scan_all_repos(self, quick: bool = False) -> dict[str, Any]:
        """Scan all three repos and return unified report.

        Args:
            quick: If True, only run fast scanners (ruff).
        """
        logger.info("🔍 Starting unified error scan across all repos...")
        self.scan_mode = "quick" if quick else "full"
        self.all_diagnostics = []
        self.scans = {}
        self.scan_warnings = []
        self.quick_e501_debt_scan = _quick_e501_debt_scan_enabled()

        for repo_name, repo_path in self.repos.items():
            if repo_path.exists():
                targets = self._python_targets(repo_path)
                if not targets:
                    logger.warning(
                        "  ⚠️  %s has no Python targets under %s",
                        repo_name.value,
                        repo_path,
                    )
                logger.info(f"  Scanning {repo_name.value}...")
                self._emit_progress("repo_start", repo=repo_name.value, repo_path=str(repo_path))
                # quick=True runs only ruff (fast) while skipping pylint/mypy
                scan = self._scan_repo(repo_name, repo_path, quick=quick)
                scan.stats["path"] = str(repo_path)
                scan.stats["python_targets"] = len(targets)
                scan.stats["python_target_names"] = [p.name for p in targets]
                self.scans[repo_name] = scan
                self.all_diagnostics.extend(scan.diagnostics)
                self._emit_progress(
                    "repo_complete",
                    repo=repo_name.value,
                    repo_path=str(repo_path),
                    diagnostics=len(scan.diagnostics),
                )
            else:
                logger.warning(f"  ⚠️  {repo_name.value} not found at {repo_path}")

        return self.generate_unified_report()

    def _scan_repo(self, repo_name: RepoName, repo_path: Path, quick: bool = False) -> RepoScan:
        """Scan a single repository using available tools."""
        scan = RepoScan(repo=repo_name)

        targets = self._python_targets(repo_path)
        file_count = None if quick else self._count_python_files(targets)
        total_stages = 1 if quick else 3

        def _stage_banner(stage_name: str, stage_index: int) -> None:
            percent = int(stage_index / total_stages * 100)
            target_note = (
                f"{file_count} files"
                if file_count is not None and file_count > 0
                else ("sampled scan" if quick else "file count n/a")
            )
            logger.info(
                f"    ▶ {stage_name} [{stage_index}/{total_stages} | {percent}%] ({target_note})"
            )
            self._emit_progress(
                "tool_start",
                repo=repo_name.value,
                tool=stage_name,
                stage_index=stage_index,
                total_stages=total_stages,
                percent=percent,
                target_note=target_note,
                quick=quick,
            )

        # Scan with ruff (fast)
        _stage_banner("ruff", 1)
        ruff_diags = self._scan_with_ruff(repo_name, repo_path, quick=quick)
        scan.diagnostics.extend(ruff_diags)
        logger.info(f"    ✅ ruff complete: {len(ruff_diags)} diagnostics")
        self._emit_progress(
            "tool_complete", repo=repo_name.value, tool="ruff", diagnostics=len(ruff_diags)
        )

        # Quick mode: stop after ruff to avoid long-running tools
        if quick:
            unique_quick_diags = list(set(scan.diagnostics))
            scan.diagnostics = unique_quick_diags
            logger.info(f"    Found {len(scan.diagnostics)} diagnostics (quick)")
            self._emit_progress(
                "repo_summary",
                repo=repo_name.value,
                diagnostics=len(scan.diagnostics),
                quick=True,
            )
            return scan

        # Scan with pylint
        _stage_banner("pylint", 2)
        pylint_diags = self._scan_with_pylint(repo_name, repo_path)
        scan.diagnostics.extend(pylint_diags)
        logger.info(f"    ✅ pylint complete: {len(pylint_diags)} diagnostics")
        self._emit_progress(
            "tool_complete",
            repo=repo_name.value,
            tool="pylint",
            diagnostics=len(pylint_diags),
        )

        # Scan with mypy
        _stage_banner("mypy", 3)
        mypy_diags = self._scan_with_mypy(repo_name, repo_path)
        scan.diagnostics.extend(mypy_diags)
        logger.info(f"    ✅ mypy complete: {len(mypy_diags)} diagnostics")
        self._emit_progress(
            "tool_complete", repo=repo_name.value, tool="mypy", diagnostics=len(mypy_diags)
        )

        # Deduplicate
        unique_diags = list(set(scan.diagnostics))
        scan.diagnostics = unique_diags

        logger.info(f"    Found {len(scan.diagnostics)} diagnostics")
        self._emit_progress(
            "repo_summary",
            repo=repo_name.value,
            diagnostics=len(scan.diagnostics),
            quick=False,
        )
        return scan

    def _python_targets(self, repo_path: Path) -> list[Path]:
        """Pick a small set of reliable Python code directories."""
        targets: list[Path] = []
        for candidate_name in SCAN_TARGET_DIRS:
            candidate = repo_path / candidate_name
            if candidate.exists():
                targets.append(candidate)

        if not targets:
            for candidate in repo_path.iterdir():
                if candidate.name in SKIP_DIRECTORY_NAMES or not candidate.is_dir():
                    continue
                if any(candidate.glob("*.py")):
                    targets.append(candidate)
                if len(targets) >= 3:
                    break

        if not targets and any(repo_path.glob("*.py")):
            targets.append(repo_path)

        return targets

    def _scan_with_pylint(self, repo_name: RepoName, repo_path: Path) -> list[ErrorDiagnostic]:
        """Scan repository with pylint."""
        diags: list[ErrorDiagnostic] = []
        targets = self._python_targets(repo_path)
        if not targets:
            return diags
        py_files = self._collect_python_files(targets, limit=MAX_PYLINT_FILES)
        if not py_files:
            return diags

        def _parse_pylint_stdout(stdout: str) -> None:
            if not stdout:
                return
            messages = json.loads(stdout)
            for msg in messages:
                diag = ErrorDiagnostic(
                    error_id=f"pylint-{msg.get('symbol', 'unknown')}",
                    severity=self._pylint_to_severity(msg.get("type", "error")),
                    error_type=self._pylint_to_error_type(msg.get("symbol", "error")),
                    repo=repo_name,
                    file_path=Path(msg.get("path", "")),
                    line_num=msg.get("line", 0),
                    column_num=msg.get("column", 0),
                    message=msg.get("message", ""),
                    source="pylint",
                    suggestion=msg.get("message-id", ""),
                )
                diags.append(diag)

        def _run_pylint_files(
            files: list[Path],
            *,
            label: str,
            timeout: int,
        ) -> None:
            cmd = (
                self._python_cmd()
                + ["-m", "pylint", "--exit-zero", "-f", "json"]
                + [str(path) for path in files]
            )
            result = self._run_with_heartbeat(cmd, label=label, timeout=timeout)
            _parse_pylint_stdout(result.stdout)

        batch_size = max(1, min(PYLINT_BATCH_FILES, len(py_files)))
        total_batches = (len(py_files) + batch_size - 1) // batch_size
        chunk_timeout_hit = False

        try:
            for batch_index, start in enumerate(range(0, len(py_files), batch_size), start=1):
                batch = py_files[start : start + batch_size]
                self._emit_progress(
                    "tool_progress",
                    repo=repo_name.value,
                    tool="pylint",
                    batch_index=batch_index,
                    total_batches=total_batches,
                    batch_files=len(batch),
                    retry=False,
                )
                try:
                    _run_pylint_files(
                        batch,
                        label=f"{repo_name.value} pylint batch {batch_index}/{total_batches}",
                        timeout=PYLINT_TIMEOUT_SECONDS,
                    )
                except subprocess.TimeoutExpired:
                    retry_limit = min(PYLINT_RETRY_MAX_FILES, max(1, len(batch) // 2))
                    if retry_limit >= len(batch):
                        retry_limit = max(1, len(batch) - 1)
                    if retry_limit < len(batch):
                        logger.warning(
                            "  ⚠️  pylint batch %s timed out for %s; retrying in chunks of %s files",
                            batch_index,
                            repo_name.value,
                            retry_limit,
                        )
                        for retry_index, retry_start in enumerate(
                            range(0, len(batch), retry_limit),
                            start=1,
                        ):
                            retry_batch = batch[retry_start : retry_start + retry_limit]
                            self._emit_progress(
                                "tool_progress",
                                repo=repo_name.value,
                                tool="pylint",
                                batch_index=batch_index,
                                total_batches=total_batches,
                                batch_files=len(retry_batch),
                                retry=True,
                                retry_index=retry_index,
                            )
                            try:
                                _run_pylint_files(
                                    retry_batch,
                                    label=(
                                        f"{repo_name.value} pylint retry {batch_index}.{retry_index}/{total_batches}"
                                    ),
                                    timeout=PYLINT_RETRY_TIMEOUT_SECONDS,
                                )
                            except subprocess.TimeoutExpired:
                                chunk_timeout_hit = True
                                logger.warning(
                                    "  ⚠️  pylint retry chunk %s.%s timed out for %s",
                                    batch_index,
                                    retry_index,
                                    repo_name.value,
                                )
                    else:
                        chunk_timeout_hit = True
                        logger.warning(
                            "  ⚠️  pylint batch %s timed out for %s",
                            batch_index,
                            repo_name.value,
                        )
        except json.JSONDecodeError as e:
            logger.warning(f"  ⚠️  pylint error for {repo_name.value}: {e}")
        if chunk_timeout_hit:
            warning = f"pylint timed out for {repo_name.value}"
            self.scan_warnings.append(warning)
            logger.warning(f"  ⚠️  {warning}")

        return diags

    def _scan_with_mypy(self, repo_name: RepoName, repo_path: Path) -> list[ErrorDiagnostic]:
        """Scan repository with mypy."""
        diags: list[ErrorDiagnostic] = []
        try:
            targets = self._python_targets(repo_path)
            if not targets:
                return diags

            py_files: list[Path] = []
            for target in targets:
                for file_path in sorted(target.rglob("*.py")):
                    py_files.append(file_path)
                    if len(py_files) >= MAX_MYPY_FILES:
                        break
                if len(py_files) >= MAX_MYPY_FILES:
                    break

            if not py_files:
                return diags

            def _parse_mypy_stdout(stdout: str) -> None:
                if not stdout:
                    return
                for line in stdout.split("\n"):
                    if "error:" in line or "warning:" in line:
                        # Parse mypy output: file.py:line: error: message
                        parts = line.split(":")
                        if len(parts) >= 3:
                            try:
                                file_path = Path(parts[0].strip())
                                line_num = int(parts[1].strip())
                                msg = ":".join(parts[3:]).strip()

                                diag = ErrorDiagnostic(
                                    error_id="mypy-type-check",
                                    severity=(
                                        ErrorSeverity.ERROR
                                        if "error:" in line
                                        else ErrorSeverity.WARNING
                                    ),
                                    error_type=ErrorType.TYPE,
                                    repo=repo_name,
                                    file_path=file_path,
                                    line_num=line_num,
                                    message=msg,
                                    source="mypy",
                                )
                                diags.append(diag)
                            except (ValueError, IndexError):
                                continue

            def _run_mypy_files(
                files: list[Path],
                *,
                label: str,
                timeout: int,
            ) -> None:
                if not files:
                    return
                cmd = self._python_cmd() + ["-m", "mypy"] + [str(f) for f in files]
                result = self._run_with_heartbeat(cmd, label=label, timeout=timeout)
                _parse_mypy_stdout(result.stdout)

            primary_limit = min(len(py_files), MAX_MYPY_FILES)
            primary_files = py_files[:primary_limit]
            try:
                _run_mypy_files(
                    primary_files,
                    label=f"{repo_name.value} mypy",
                    timeout=MYPY_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired:
                retry_limit = min(MYPY_RETRY_MAX_FILES, max(1, primary_limit // 3))
                if retry_limit >= primary_limit:
                    retry_limit = max(1, primary_limit - 1)

                if retry_limit < primary_limit:
                    logger.warning(
                        "  ⚠️  mypy timed out for %s; retrying in chunks of %s files",
                        repo_name.value,
                        retry_limit,
                    )
                    chunk_timeout_hit = False
                    for chunk_index in range(0, primary_limit, retry_limit):
                        chunk = primary_files[chunk_index : chunk_index + retry_limit]
                        try:
                            _run_mypy_files(
                                chunk,
                                label=f"{repo_name.value} mypy retry {chunk_index // retry_limit + 1}",
                                timeout=MYPY_RETRY_TIMEOUT_SECONDS,
                            )
                        except subprocess.TimeoutExpired:
                            chunk_timeout_hit = True
                            logger.warning(
                                "  ⚠️  mypy retry chunk %s timed out for %s",
                                chunk_index // retry_limit + 1,
                                repo_name.value,
                            )
                    if chunk_timeout_hit:
                        warning = f"mypy timed out for {repo_name.value}"
                        self.scan_warnings.append(warning)
                        logger.warning(f"  ⚠️  {warning}")
                    else:
                        logger.info("  ✅ mypy retry succeeded for %s", repo_name.value)
                else:
                    warning = f"mypy timed out for {repo_name.value}"
                    self.scan_warnings.append(warning)
                    logger.warning(f"  ⚠️  {warning}")
        except subprocess.TimeoutExpired:
            warning = f"mypy timed out for {repo_name.value}"
            self.scan_warnings.append(warning)
            logger.warning(f"  ⚠️  {warning}")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"  ⚠️  mypy error for {repo_name.value}: {e}")

        return diags

    def _scan_with_ruff(
        self,
        repo_name: RepoName,
        repo_path: Path,
        quick: bool = False,
    ) -> list[ErrorDiagnostic]:
        """Scan repository with ruff."""
        diags: list[ErrorDiagnostic] = []
        targets = self._python_targets(repo_path)
        if not targets:
            return diags

        config_file = repo_path / "pyproject.toml"

        def _run_ruff_scan(
            target_list: list[str],
            timeout_seconds: int,
            label: str,
            isolated: bool = False,
            select_codes: list[str] | None = None,
        ) -> subprocess.CompletedProcess[str]:
            cmd = [
                *self._ruff_cmd(),
                "check",
                *target_list,
                "--output-format",
                "json",
            ]
            if isolated:
                cmd.append("--isolated")
            if select_codes:
                cmd.extend(["--select", ",".join(select_codes)])
            if config_file.exists() and not isolated:
                cmd.extend(["--config", str(config_file)])
            return self._run_with_heartbeat(cmd, label=label, timeout=timeout_seconds)

        def _parse_ruff_output(stdout: str) -> list[ErrorDiagnostic]:
            parsed: list[ErrorDiagnostic] = []
            if not stdout:
                return parsed
            try:
                data = json.loads(stdout)
            except json.JSONDecodeError:
                return parsed
            for item in data if isinstance(data, list) else []:
                parsed.append(
                    ErrorDiagnostic(
                        error_id=f"ruff-{item.get('code', 'unknown')}",
                        severity=self._ruff_to_severity(item.get("code", "E999")),
                        error_type=self._ruff_to_error_type(item.get("code", "E999")),
                        repo=repo_name,
                        file_path=Path(item.get("filename", "")),
                        line_num=item.get("location", {}).get("row", 0),
                        column_num=item.get("location", {}).get("column", 0),
                        message=item.get("message", ""),
                        source="ruff",
                    )
                )
            return parsed

        try:
            if quick:
                sampled_files = self._collect_python_files(targets, limit=MAX_QUICK_RUFF_FILES)
                scan_targets = (
                    [str(path) for path in sampled_files]
                    if sampled_files
                    else [str(target) for target in targets]
                )
                result = _run_ruff_scan(
                    scan_targets,
                    timeout_seconds=QUICK_RUFF_TIMEOUT_SECONDS,
                    label=f"{repo_name.value} ruff",
                )
                diags.extend(_parse_ruff_output(result.stdout))
                if self.quick_e501_debt_scan:
                    try:
                        debt_result = _run_ruff_scan(
                            scan_targets,
                            timeout_seconds=QUICK_RUFF_TIMEOUT_SECONDS,
                            label=f"{repo_name.value} ruff-e501",
                            select_codes=["E501"],
                        )
                        diags.extend(_parse_ruff_output(debt_result.stdout))
                    except subprocess.TimeoutExpired:
                        logger.warning("  ⚠️  ruff E501 debt scan timed out for %s", repo_name.value)
                    except Exception as debt_exc:
                        logger.warning(
                            "  ⚠️  ruff E501 debt scan error for %s: %s",
                            repo_name.value,
                            debt_exc,
                        )
                return diags

            full_targets = [str(target) for target in targets]
            result = _run_ruff_scan(
                full_targets,
                timeout_seconds=FULL_RUFF_TIMEOUT_SECONDS,
                label=f"{repo_name.value} ruff",
            )
            diags.extend(_parse_ruff_output(result.stdout))
        except subprocess.TimeoutExpired:
            if quick:
                retry_limit = max(1, min(QUICK_RUFF_RETRY_MAX_FILES, MAX_QUICK_RUFF_FILES))
                retry_files = self._collect_python_files(targets, limit=retry_limit)
                if retry_files:
                    logger.warning(
                        "  ⚠️  ruff quick scan timed out for %s; retrying with %s files",
                        repo_name.value,
                        len(retry_files),
                    )
                    try:
                        retry_result = _run_ruff_scan(
                            [str(path) for path in retry_files],
                            timeout_seconds=QUICK_RUFF_RETRY_TIMEOUT_SECONDS,
                            label=f"{repo_name.value} ruff retry",
                        )
                        diags.extend(_parse_ruff_output(retry_result.stdout))
                        logger.info("  ✅ ruff quick retry succeeded for %s", repo_name.value)
                        return diags
                    except subprocess.TimeoutExpired:
                        logger.debug("Suppressed TimeoutExpired", exc_info=True)
                    except Exception as retry_exc:
                        logger.warning(
                            "  ⚠️  ruff retry error for %s: %s", repo_name.value, retry_exc
                        )
            else:
                retry_limit = max(1, FULL_RUFF_RETRY_MAX_FILES)
                retry_files = self._collect_python_files(targets, limit=retry_limit)
                if retry_files:
                    warning = f"ruff full scan timed out for {repo_name.value}; sampled retry on {len(retry_files)} files"
                    self.scan_warnings.append(warning)
                    logger.warning("  ⚠️  %s", warning)
                    try:
                        retry_result = _run_ruff_scan(
                            [str(path) for path in retry_files],
                            timeout_seconds=FULL_RUFF_RETRY_TIMEOUT_SECONDS,
                            label=f"{repo_name.value} ruff sampled-retry",
                        )
                        diags.extend(_parse_ruff_output(retry_result.stdout))
                        logger.info(
                            "  ✅ ruff full-timeout sampled retry succeeded for %s", repo_name.value
                        )
                        return diags
                    except subprocess.TimeoutExpired:
                        logger.debug("Suppressed TimeoutExpired", exc_info=True)
                    except Exception as retry_exc:
                        logger.warning(
                            "  ⚠️  ruff full sampled retry error for %s: %s",
                            repo_name.value,
                            retry_exc,
                        )

            warning = f"ruff timed out for {repo_name.value}"
            self.scan_warnings.append(warning)
            logger.warning(f"  ⚠️  {warning}")
        except Exception as e:
            logger.warning(f"  ⚠️  ruff error for {repo_name.value}: {e}")

        return diags

    @staticmethod
    def _pylint_to_severity(pylint_type: str) -> ErrorSeverity:
        """Convert pylint type to ErrorSeverity."""
        mapping = {
            "error": ErrorSeverity.ERROR,
            "fatal": ErrorSeverity.ERROR,
            "warning": ErrorSeverity.WARNING,
            "convention": ErrorSeverity.INFO,
            "refactor": ErrorSeverity.INFO,
            "information": ErrorSeverity.HINT,
        }
        return mapping.get(pylint_type.lower(), ErrorSeverity.INFO)

    @staticmethod
    def _pylint_to_error_type(symbol: str) -> ErrorType:
        """Convert pylint symbol to ErrorType."""
        symbol_lower = symbol.lower()
        if "import" in symbol_lower:
            return ErrorType.IMPORT
        elif "complexity" in symbol_lower or "too-many" in symbol_lower:
            return ErrorType.COMPLEXITY
        elif "async" in symbol_lower:
            return ErrorType.ASYNC
        elif "exception" in symbol_lower or "broad-except" in symbol_lower:
            return ErrorType.EXCEPTION
        else:
            return ErrorType.LINTING

    @staticmethod
    def _ruff_to_severity(code: str) -> ErrorSeverity:
        """Convert ruff code to ErrorSeverity."""
        if code.startswith("E") or code.startswith("F"):
            return ErrorSeverity.ERROR
        elif code.startswith("W"):
            return ErrorSeverity.WARNING
        else:
            return ErrorSeverity.INFO

    @staticmethod
    def _ruff_to_error_type(code: str) -> ErrorType:
        """Convert ruff code to ErrorType."""
        if code.startswith("E"):
            return ErrorType.SYNTAX
        elif code == "F401" or code == "F841":
            return ErrorType.LINTING
        else:
            return ErrorType.LINTING

    def generate_unified_report(self) -> dict[str, Any]:
        """Generate unified report of all errors."""
        total_errors = sum(1 for d in self.all_diagnostics if d.severity == ErrorSeverity.ERROR)
        total_warnings = sum(1 for d in self.all_diagnostics if d.severity == ErrorSeverity.WARNING)
        total_infos = sum(
            1
            for d in self.all_diagnostics
            if d.severity in (ErrorSeverity.INFO, ErrorSeverity.HINT)
        )

        vscode_counts = self._load_counts_file(self.vscode_counts_path)
        export_counts = self._load_export_counts_from_candidates(self.export_paths)

        # Ground truth is now the actual tool scan results (canonical source)
        partial_scan = bool(self.scan_warnings)
        target_list = list(self._target_repo_values)
        target_phrase = ", ".join(target_list) if target_list else "no targets"
        note = f"Tool scan ({self.scan_mode} mode) using ruff, mypy, pylint across targeted repos: {target_phrase}"
        if partial_scan:
            note = f"{note}; partial due to tool timeouts/errors"
        elif self.scan_mode == "quick":
            if self.quick_e501_debt_scan:
                note = f"{note}; includes quick E501 debt scan"
            else:
                note = f"{note}; excludes quick E501 debt scan (set NUSYQ_ERROR_SCAN_INCLUDE_QUICK_E501_DEBT=1 to include)"
        confidence = "high"
        if partial_scan:
            confidence = "low"
        elif self.scan_mode == "quick":
            confidence = "medium"
        ground_truth = {
            "errors": total_errors,
            "warnings": total_warnings,
            "infos": total_infos,
            "total": len(self.all_diagnostics),
            "source": "tool_scan",
            "note": note,
            "scope": {
                "targets": target_list,
                "scan_mode": self.scan_mode,
                "partial_scan": partial_scan,
            },
            "confidence": confidence,
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "scan_mode": self.scan_mode,
            "total_diagnostics": len(self.all_diagnostics),
            "by_severity": {
                "errors": total_errors,
                "warnings": total_warnings,
                "infos_hints": total_infos,
            },
            "by_repo": {repo.value: scan.summary() for repo, scan in self.scans.items()},
            "targets": list(self._target_repo_values),
            "filters": {
                "include": [repo.value for repo in self.include_filters],
                "exclude": [repo.value for repo in self.exclude_filters],
            },
            "partial_scan": partial_scan,
            "scan_warnings": self.scan_warnings,
            "vscode_counts": vscode_counts,
            "ground_truth": ground_truth,
            "diagnostics_export_counts": export_counts,
            "diagnostic_details": [asdict(d) for d in self.all_diagnostics[:50]],  # First 50
        }

    def print_summary(self, report: dict[str, Any] | None = None) -> None:
        """Print a human-readable summary."""
        if report is None:
            report = self.generate_unified_report()

        logger.info("\n" + "=" * 70)
        logger.error("🔍 UNIFIED ERROR REPORT - GROUND TRUTH")
        logger.info("=" * 70)
        logger.info(f"Generated: {report['timestamp']}")
        logger.info(f"Scan Mode: {report.get('scan_mode', 'unknown')}")
        if report.get("partial_scan"):
            logger.warning("⚠️  Partial scan detected (see warnings below)")

        ground_truth = report.get("ground_truth")
        if ground_truth:
            logger.info(f"\n📊 CANONICAL GROUND TRUTH ({ground_truth.get('source', 'unknown')}):")
            logger.info(f"  • Total:    {ground_truth['total']}")
            logger.error(f"  • Errors:   {ground_truth['errors']}")
            logger.warning(f"  • Warnings: {ground_truth['warnings']}")
            logger.info(f"  • Infos:    {ground_truth['infos']}")
            if ground_truth.get("note"):
                logger.info(f"  • Note:     {ground_truth['note']}")

        vscode_counts = report.get("vscode_counts")
        if vscode_counts and isinstance(vscode_counts, dict):
            counts = vscode_counts.get("counts", {})
            logger.warning("\n⚠️  VS Code Problems Panel (filtered view):")
            logger.error(f"  • Errors:   {counts.get('errors', 0)}")
            logger.warning(f"  • Warnings: {counts.get('warnings', 0)}")
            logger.info(f"  • Infos:    {counts.get('infos', 0)}")
            logger.info(f"  • Total:    {counts.get('total', 0)}")
            logger.error("  • Note:     VS Code shows filtered subset of actual errors")

        warnings = report.get("scan_warnings") or []
        if warnings:
            logger.warning("\nScan Warnings:")
            for warning in warnings:
                logger.warning(f"  • {warning}")

        logger.info("\nBy Repository:")
        for repo_name, repo_summary in report["by_repo"].items():
            if repo_summary["total"] > 0:
                logger.info(f"\n  {repo_name} ({repo_summary['total']} diagnostics)")
                logger.info(f"    Severity: {repo_summary['by_severity']}")
                logger.info(f"    Types: {repo_summary['by_type']}")
                logger.info(f"    Sources: {repo_summary['by_source']}")

        logger.info("\n" + "=" * 70)

    def write_report(
        self,
        output_dir: Path | None = None,
        label: str | None = None,
    ) -> dict[str, str]:
        """Write unified report to JSON + Markdown files."""
        if output_dir is None:
            output_dir = self.reports_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        report = self.generate_unified_report()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_label = ""
        if label:
            safe_label = label.strip().lower().replace(" ", "-").replace("_", "-")
            safe_label = f"{safe_label}_"
        stamped_json_path = output_dir / f"unified_error_report_{safe_label}{stamp}.json"
        stamped_md_path = output_dir / f"unified_error_report_{safe_label}{stamp}.md"
        json_path = stamped_json_path
        md_path = stamped_md_path
        rendered_markdown = self._render_markdown(report)
        serialized_report = json.dumps(report, indent=2, default=str)
        latest_json = output_dir / f"unified_error_report_{safe_label}latest.json"
        latest_md = output_dir / f"unified_error_report_{safe_label}latest.md"
        targets = report.get("targets", [])
        target_count = len(targets) if isinstance(targets, list) else 0
        scan_mode = str(report.get("scan_mode", "")).lower()
        partial_scan = bool(report.get("partial_scan"))

        allow_scoped_latest = str(
            os.getenv("NUSYQ_ERROR_REPORT_ALLOW_SCOPED_LATEST", "0")
        ).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        preserve_partial_latest = str(
            os.getenv("NUSYQ_ERROR_REPORT_PRESERVE_LATEST_ON_PARTIAL", "0")
        ).strip().lower() in {"1", "true", "yes", "on"}
        write_history = str(os.getenv("NUSYQ_ERROR_REPORT_WRITE_HISTORY", "1")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        skip_unchanged_history = str(
            os.getenv("NUSYQ_ERROR_REPORT_SKIP_UNCHANGED_HISTORY", "1")
        ).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        should_skip_latest = False
        if (
            scan_mode == "quick"
            and target_count < 3
            and not safe_label
            and not allow_scoped_latest
            and latest_json.exists()
            and latest_md.exists()
        ):
            should_skip_latest = True
            logger.info(
                "Scoped quick scan detected; preserving canonical latest report at %s",
                latest_json,
            )

        if (
            partial_scan
            and preserve_partial_latest
            and latest_json.exists()
            and latest_md.exists()
            and not should_skip_latest
        ):
            should_skip_latest = True
            logger.warning(
                "Partial scan detected; preserving previous latest report at %s",
                latest_json,
            )

        unchanged_vs_latest = False
        latest_report: dict[str, Any] | None = None
        if latest_json.exists():
            try:
                latest_candidate = json.loads(latest_json.read_text(encoding="utf-8"))
                if isinstance(latest_candidate, dict):
                    latest_report = latest_candidate
            except (json.JSONDecodeError, OSError):
                latest_report = None
        if latest_report is not None:
            unchanged_vs_latest = self._report_fingerprint(
                latest_report
            ) == self._report_fingerprint(report)

        should_write_history = write_history
        if skip_unchanged_history and unchanged_vs_latest:
            should_write_history = False
        if not latest_json.exists():
            # Ensure first run persists at least one timestamped artifact.
            should_write_history = True

        if should_write_history:
            stamped_json_path.write_text(serialized_report, encoding="utf-8")
            stamped_md_path.write_text(rendered_markdown, encoding="utf-8")
            json_path = stamped_json_path
            md_path = stamped_md_path
        elif latest_json.exists() and latest_md.exists():
            json_path = latest_json
            md_path = latest_md

        if not should_skip_latest:
            latest_json.write_text(serialized_report, encoding="utf-8")
            latest_md.write_text(rendered_markdown, encoding="utf-8")
            if not should_write_history:
                json_path = latest_json
                md_path = latest_md

        try:
            retention_count = int(os.getenv("NUSYQ_ERROR_REPORT_HISTORY_KEEP", "20"))
        except ValueError:
            retention_count = 20
        self._prune_report_history(
            output_dir, safe_label=safe_label, keep_count=max(0, retention_count)
        )

        return {
            "json": str(json_path),
            "md": str(md_path),
            "latest_json": str(latest_json),
            "latest_md": str(latest_md),
        }

    @staticmethod
    def _report_fingerprint(report: dict[str, Any]) -> str:
        """Generate a stable fingerprint to detect meaningful report changes."""
        by_repo = report.get("by_repo")
        repo_totals: dict[str, int] = {}
        if isinstance(by_repo, dict):
            for repo_name, summary in by_repo.items():
                if isinstance(summary, dict):
                    try:
                        repo_totals[str(repo_name)] = int(summary.get("total", 0))
                    except (TypeError, ValueError):
                        repo_totals[str(repo_name)] = 0
        payload = {
            "scan_mode": str(report.get("scan_mode", "")),
            "targets": sorted(str(t) for t in report.get("targets", []) if t),
            "partial_scan": bool(report.get("partial_scan", False)),
            "total_diagnostics": int(report.get("total_diagnostics", 0) or 0),
            "by_severity": report.get("by_severity", {}),
            "repo_totals": repo_totals,
            "ground_truth": report.get("ground_truth", {}),
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def _prune_report_history(output_dir: Path, safe_label: str, keep_count: int) -> None:
        """Retain only the newest N timestamped report pairs per label."""
        if keep_count <= 0:
            return

        if safe_label:
            prefix = f"unified_error_report_{safe_label}"
            candidates = [
                path
                for path in output_dir.glob(f"{prefix}*.json")
                if not path.name.endswith("_latest.json") and not path.name.endswith("latest.json")
            ]
        else:
            candidates = [
                path
                for path in output_dir.glob("unified_error_report_*.json")
                if (
                    not path.name.endswith("_latest.json")
                    and not path.name.endswith("latest.json")
                    and path.name.removeprefix("unified_error_report_")[:8].isdigit()
                )
            ]
        timestamped_json = sorted(
            candidates,
            key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
            reverse=True,
        )
        stale_json = timestamped_json[keep_count:]
        for stale in stale_json:
            sibling_md = stale.with_suffix(".md")
            try:
                stale.unlink()
            except OSError:
                continue
            try:
                if sibling_md.exists():
                    sibling_md.unlink()
            except OSError:
                continue

    @staticmethod
    def _load_counts_file(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            counts_data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            return counts_data
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def _load_export_counts(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        if isinstance(data.get("counts"), dict):
            counts_obj = data["counts"]
            return {
                "errors": int(counts_obj.get("errors", 0)),
                "warnings": int(counts_obj.get("warnings", 0)),
                "infos": int(counts_obj.get("infos", 0)),
                "total": int(counts_obj.get("total", 0)),
                "source": str(data.get("source", "diagnostics_counts")),
                "path": str(path),
            }
        by_category = data.get("by_category", {})
        if not isinstance(by_category, dict):
            return None
        return {
            "errors": int(by_category.get("errors", 0)),
            "warnings": int(by_category.get("warnings", 0)),
            "infos": int(by_category.get("info", 0)),
            "total": int(data.get("total_issues", 0)),
            "source": "diagnostics_export",
            "path": str(path),
        }

    @classmethod
    def _load_export_counts_from_candidates(cls, paths: Sequence[Path]) -> dict[str, Any] | None:
        for path in paths:
            counts = cls._load_export_counts(path)
            if counts:
                return counts
        return None

    @staticmethod
    def _render_markdown(report: dict[str, Any]) -> str:
        lines: list[str] = []
        lines.append("# Unified Error Report\n\n")
        lines.append(f"- Timestamp: {report.get('timestamp')}\n")
        lines.append(f"- Scan mode: {report.get('scan_mode', 'unknown')}\n")
        if report.get("partial_scan"):
            lines.append("- Partial scan: yes (one or more scanners timed out or failed)\n")
        targets = report.get("targets")
        if targets:
            lines.append(f"- Targets: {', '.join(targets)}\n")
        filters = report.get("filters", {})
        include_filters = filters.get("include", [])
        exclude_filters = filters.get("exclude", [])
        if include_filters or exclude_filters:
            lines.append("\n## Filters\n")
            if include_filters:
                lines.append(f"- Include: {', '.join(include_filters)}\n")
            if exclude_filters:
                lines.append(f"- Exclude: {', '.join(exclude_filters)}\n")
        totals = report.get("by_severity", {})
        lines.append(
            f"- Tool Errors: {totals.get('errors', 0)}, "
            f"Tool Warnings: {totals.get('warnings', 0)}, "
            f"Tool Infos: {totals.get('infos_hints', 0)}\n"
        )
        ground_truth = report.get("ground_truth")
        if ground_truth:
            lines.append("\n## Tool Scan Ground Truth\n")
            lines.append(
                f"- Errors: {ground_truth.get('errors', 0)}, "
                f"Warnings: {ground_truth.get('warnings', 0)}, "
                f"Infos: {ground_truth.get('infos', 0)}, "
                f"Total: {ground_truth.get('total', 0)}\n"
            )
            if ground_truth.get("note"):
                lines.append(f"- Note: {ground_truth.get('note')}\n")
        scan_warnings = report.get("scan_warnings") or []
        if scan_warnings:
            lines.append("\n## Scan Warnings\n")
            for warning in scan_warnings:
                lines.append(f"- {warning}\n")
        vscode_counts = report.get("vscode_counts")
        if vscode_counts:
            counts = vscode_counts.get("counts", {})
            lines.append("\n## VS Code Counts\n")
            lines.append(
                f"- Errors: {counts.get('errors', 0)}, "
                f"Warnings: {counts.get('warnings', 0)}, "
                f"Infos: {counts.get('infos', 0)}, "
                f"Total: {counts.get('total', 0)}\n"
            )
        export_counts = report.get("diagnostics_export_counts")
        if export_counts:
            lines.append("\n## Diagnostics Export Counts\n")
            lines.append(
                f"- Errors: {export_counts.get('errors', 0)}, "
                f"Warnings: {export_counts.get('warnings', 0)}, "
                f"Infos: {export_counts.get('infos', 0)}, "
                f"Total: {export_counts.get('total', 0)}\n"
            )
        lines.append("\n## Repository Summary\n")
        for repo_name, repo_summary in report.get("by_repo", {}).items():
            lines.append(f"### {repo_name}\n")
            repo_path = repo_summary.get("path")
            if repo_path:
                lines.append(f"- Path: {repo_path}\n")
            python_targets = repo_summary.get("python_targets")
            if python_targets is not None:
                lines.append(f"- Python targets: {python_targets}\n")
            target_names = repo_summary.get("python_target_names") or []
            if target_names:
                lines.append(f"- Target names: {', '.join(target_names)}\n")
            lines.append(f"- Total: {repo_summary.get('total', 0)}\n")
            lines.append(f"- Severity: {repo_summary.get('by_severity', {})}\n")
            lines.append(f"- Types: {repo_summary.get('by_type', {})}\n")
            lines.append(f"- Sources: {repo_summary.get('by_source', {})}\n")
        return "".join(lines)

    def load_cached_report(self, max_age_seconds: int | None = None) -> dict[str, Any] | None:
        """Load the best cached report if it exists and is fresh enough.

        Args:
            max_age_seconds: If provided, return the cache only when newer than this age.
        """
        latest_json = self.reports_dir / "unified_error_report_latest.json"
        candidates: list[Path] = []
        if latest_json.exists():
            candidates.append(latest_json)
        candidates.extend(
            sorted(
                [
                    path
                    for path in self.reports_dir.glob("unified_error_report_*.json")
                    if (
                        not path.name.endswith("_latest.json")
                        and path.name.removeprefix("unified_error_report_")[:8].isdigit()
                    )
                ],
                key=lambda p: p.stat().st_mtime if p.exists() else 0.0,
                reverse=True,
            )[:25]
        )

        best: tuple[float, dict[str, Any], Path] | None = None
        for candidate_path in candidates:
            try:
                payload = json.loads(candidate_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(payload, dict):
                continue

            cache_age_seconds: float | None = None
            timestamp_raw = payload.get("timestamp")
            if isinstance(timestamp_raw, str) and timestamp_raw.strip():
                try:
                    cache_dt = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
                    cache_age_seconds = max((datetime.now() - cache_dt).total_seconds(), 0.0)
                except Exception:
                    cache_age_seconds = None
            if cache_age_seconds is None:
                try:
                    cache_age_seconds = max(time.time() - candidate_path.stat().st_mtime, 0.0)
                except OSError:
                    cache_age_seconds = None

            if (
                max_age_seconds is not None
                and cache_age_seconds is not None
                and cache_age_seconds > max_age_seconds
            ):
                continue

            score = float("inf") if cache_age_seconds is None else cache_age_seconds

            best_score = best[0] if best is not None else None
            if best_score is None or score < best_score:
                best = (score, payload, candidate_path)

        if best is None:
            return None

        _, cached, chosen_path = best
        cached.setdefault("cache_info", {})
        cache_info = cached["cache_info"]
        if isinstance(cache_info, dict):
            cache_info.setdefault("path", str(chosen_path))
            age_seconds = None
            try:
                age_seconds = max(time.time() - chosen_path.stat().st_mtime, 0.0)
            except OSError:
                age_seconds = None
            cache_info.setdefault("age_seconds", age_seconds)
            cache_info.setdefault("max_age_seconds", max_age_seconds)

        return cached


def create_unified_report() -> dict[str, Any]:
    """Entry point: Create and return unified error report."""
    reporter = UnifiedErrorReporter()
    return reporter.scan_all_repos()


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Unified error reporter")
    parser.add_argument("--quick", action="store_true", help="Run fast scan only (ruff)")
    args = parser.parse_args()

    reporter = UnifiedErrorReporter()
    reporter.scan_all_repos(quick=args.quick)
    reporter.print_summary()
    default_out = Path(__file__).parent.parent.parent / "docs" / "Reports" / "diagnostics"
    reporter.write_report(default_out)
