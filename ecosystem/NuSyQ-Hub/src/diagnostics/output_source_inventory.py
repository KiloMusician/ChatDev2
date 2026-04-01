"""Output source inventory for VS Code and NuSyQ terminal channels.

This module scans known output surfaces and provides a consolidated view of:
- VS Code output channel logs (output_logging_* and extension logs)
- VS Code core logs (main, terminal, pty host, window logs)
- NuSyQ terminal logs (data/terminal_logs/*.log)
- Terminal watcher scripts and VS Code watcher tasks
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from difflib import get_close_matches
from pathlib import Path
from typing import Any

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    UTC = timezone.utc  # noqa: UP017

logger = logging.getLogger(__name__)


LOCAL_TZ = datetime.now().astimezone().tzinfo or UTC


DEFAULT_EXPECTED_CHANNELS = [
    ".NET Install Tool",
    ".NET Test Log",
    "AI Toolkit",
    "AI Toolkit Tracing",
    "Auto Rename Tag",
    "autoDocstring",
    "Biome",
    "Biome (NuSyQ-Hub)",
    "Biome (NuSyQ)",
    "Biome (Prime_anchor)",
    "Biome (SimulatedVerse)",
    "Black Formatter",
    "C#",
    "C# LSP Trace Logs",
    "Claude VSCode",
    "Code",
    "Code Spell Checker",
    "Codex",
    "Cody by SourceGraph",
    "Cody: Network",
    "coverage-gutters",
    "database Client",
    "Docker Labs AI",
    "Docker LSP (Markdown)",
    "EditorConfig",
    "ESLint",
    "Even Better TOML",
    "Even Better TOML LSP",
    "Flake8",
    "Git",
    "Git Graph",
    "GitHub",
    "GitHub Actions",
    "GitHub Authentication",
    "GitHub Copilot chat",
    "GitHub Copilot Log (Code References)",
    "GitLens",
    "GitLens (Git)",
    "GritQL Token Provider",
    "Helm",
    "ILSpy Backend",
    "ILSpy Extension",
    "isort",
    "JSON Language Server",
    "Jupyter",
    "Jupyter Server Console",
    "Kilo-Code",
    "Kubernetes",
    "Makefile Tools",
    "Markdown",
    "Microsoft Authentication",
    "MSBuild Project Tools",
    "Mypy Type Checker",
    "OpenAPI Swagger Editor",
    "OpenCtx",
    "Peacock",
    "PowerShell",
    "Prettier",
    "PyHover",
    "Pylint",
    "Python",
    "Python Debugger",
    "Python Language Service",
    "Python Locator",
    "Python Test Adapter Log",
    "rainbow_csv_debug+channel",
    "Razor Log",
    "REST",
    "Roo-Code",
    "Ruff",
    "Ruff Language Server",
    "Semgrep (Client)",
    "Semgrep (Server)",
    "Sixth",
    "SonarQube for IDE",
    "SQLTools",
    "Tailwind CSS IntelliSense",
    "Test Explorer",
    "Todohighlight",
    "TypeScript",
    "VersionLens",
    "ViTest",
    "vscode-shiki-bridge",
    "Windsurf",
    "YAML Support",
    "Agent Sessions",
    "Extension Host",
    "Extension Host (Worker)",
    "Main",
    "Pty Host",
    "Remote Tunnel Service",
    "Settings Sync",
    "Shared",
    "Tasks",
    "Terminal",
    "Text Model Changes Reason",
    "Window",
]


CHANNEL_ALIASES: dict[str, list[str]] = {
    # VS Code labels -> NuSyQ canonical channels.
    "githubcopilotchat": ["copilot"],
    "githubcopilotlogcodereferences": ["copilot"],
    "terminal": ["cli", "main", "tasks"],
    "main": ["main", "cli"],
    "errors": ["errors", "anomalies"],
}


def _canonical(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


def _iso_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()
    except OSError:
        return ""


def _size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _safe_tail(path: Path, lines: int = 40) -> list[str]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            raw = handle.readlines()[-lines:]
        return [line.rstrip("\n") for line in raw]
    except OSError:
        return []


def _safe_recent_lines(path: Path, max_lines: int = 2000) -> list[str]:
    """Read a bounded suffix of lines from a text file."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            raw = handle.readlines()
        if max_lines <= 0:
            return [line.rstrip("\n") for line in raw]
        return [line.rstrip("\n") for line in raw[-max_lines:]]
    except OSError:
        return []


def _to_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=LOCAL_TZ).astimezone(UTC)
    return value.astimezone(UTC)


def _parse_isoish_datetime(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    try:
        return _to_aware_utc(datetime.fromisoformat(text.replace("Z", "+00:00")))
    except ValueError:
        return None


def _parse_line_timestamp(line: str) -> datetime | None:
    """Extract a best-effort timestamp from common log line formats."""
    stripped = line.strip()
    if not stripped:
        return None

    if stripped.startswith("{") and '"ts"' in stripped:
        try:
            payload = json.loads(stripped)
            ts = payload.get("ts") or payload.get("timestamp")
            if isinstance(ts, str):
                parsed = _parse_isoish_datetime(ts)
                if parsed is not None:
                    return parsed
        except json.JSONDecodeError:
            logger.debug("Suppressed JSONDecodeError", exc_info=True)

    patterns = [
        r"\b(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:?\d{2})?)\b",
        r"\b(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:[.,]\d+)?\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, stripped)
        if not match:
            continue
        candidate = match.group(1)
        parsed = _parse_isoish_datetime(candidate)
        if parsed is not None:
            return parsed
        try:
            return _to_aware_utc(datetime.strptime(candidate, "%Y-%m-%d %H:%M:%S"))
        except ValueError:
            continue

    return None


def _dedupe_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


@dataclass(frozen=True)
class SourceRecord:
    channel: str
    source_type: str
    path: str
    last_modified: str
    size_bytes: int


class OutputSourceInventory:
    """Build a consolidated inventory over output-producing sources."""

    def __init__(self, repo_root: Path | None = None):
        """Initialize OutputSourceInventory with repo_root."""
        self.repo_root = repo_root or Path(__file__).resolve().parents[2]
        self.terminal_logs_dir = self.repo_root / "data" / "terminal_logs"
        self.watcher_dir = self.repo_root / "data" / "terminal_watchers"
        self.watcher_tasks_path = self.repo_root / ".vscode" / "terminal_watcher_tasks.json"

    @staticmethod
    def _parse_iso(value: str | None) -> datetime | None:
        if not value:
            return None
        return _parse_isoish_datetime(value)

    def _discover_vscode_logs_root(self) -> Path | None:
        candidates: list[Path] = []

        appdata = os.getenv("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / "Code" / "logs")

        user_profile = os.getenv("USERPROFILE")
        if user_profile:
            candidates.append(Path(user_profile) / "AppData" / "Roaming" / "Code" / "logs")

        candidates.extend(Path("/mnt/c/Users").glob("*/AppData/Roaming/Code/logs"))

        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate
        return None

    def _latest_vscode_session(self, logs_root: Path | None) -> Path | None:
        if not logs_root or not logs_root.exists():
            return None
        sessions = [p for p in logs_root.iterdir() if p.is_dir()]
        if not sessions:
            return None
        return max(sessions, key=lambda p: p.name)

    def _collect_vscode_output_logging(self, session_dir: Path) -> list[SourceRecord]:
        records: list[SourceRecord] = []
        pattern = re.compile(r"^\d+\-")
        for path in session_dir.glob("window*/exthost/output_logging_*/*.log"):
            stem = path.stem
            channel = pattern.sub("", stem).strip()
            records.append(
                SourceRecord(
                    channel=channel or stem,
                    source_type="vscode_output_channel",
                    path=str(path),
                    last_modified=_iso_mtime(path),
                    size_bytes=_size(path),
                )
            )
        return records

    def _collect_vscode_extension_logs(self, session_dir: Path) -> list[SourceRecord]:
        records: list[SourceRecord] = []
        for path in session_dir.glob("window*/exthost/*/*.log"):
            if "output_logging_" in str(path):
                continue
            records.append(
                SourceRecord(
                    channel=path.stem,
                    source_type="vscode_extension_log",
                    path=str(path),
                    last_modified=_iso_mtime(path),
                    size_bytes=_size(path),
                )
            )
        return records

    def _collect_vscode_core_logs(self, session_dir: Path) -> list[SourceRecord]:
        records: list[SourceRecord] = []
        for path in session_dir.glob("*.log"):
            records.append(
                SourceRecord(
                    channel=path.stem,
                    source_type="vscode_core_log",
                    path=str(path),
                    last_modified=_iso_mtime(path),
                    size_bytes=_size(path),
                )
            )
        for path in session_dir.glob("window*/*.log"):
            records.append(
                SourceRecord(
                    channel=path.stem,
                    source_type="vscode_window_log",
                    path=str(path),
                    last_modified=_iso_mtime(path),
                    size_bytes=_size(path),
                )
            )
        return records

    def _collect_terminal_logs(self) -> list[SourceRecord]:
        records: list[SourceRecord] = []
        if not self.terminal_logs_dir.exists():
            return records
        for path in self.terminal_logs_dir.glob("*.log"):
            records.append(
                SourceRecord(
                    channel=path.stem,
                    source_type="nusyq_terminal_log",
                    path=str(path),
                    last_modified=_iso_mtime(path),
                    size_bytes=_size(path),
                )
            )
        return records

    def _collect_watchers(self) -> list[SourceRecord]:
        records: list[SourceRecord] = []
        if not self.watcher_dir.exists():
            return records
        for path in self.watcher_dir.glob("watch_*_terminal.ps1"):
            name = path.stem.replace("watch_", "").replace("_terminal", "")
            records.append(
                SourceRecord(
                    channel=name,
                    source_type="terminal_watcher_script",
                    path=str(path),
                    last_modified=_iso_mtime(path),
                    size_bytes=_size(path),
                )
            )
        return records

    def _collect_watcher_tasks(self) -> list[SourceRecord]:
        records: list[SourceRecord] = []
        if not self.watcher_tasks_path.exists():
            return records
        try:
            payload = json.loads(self.watcher_tasks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return records

        for task in payload.get("tasks", []):
            label = str(task.get("label", ""))
            match = re.match(r"Watch (.+) Terminal$", label)
            if not match:
                continue
            channel = match.group(1)
            records.append(
                SourceRecord(
                    channel=channel,
                    source_type="terminal_watcher_task",
                    path=str(self.watcher_tasks_path),
                    last_modified=_iso_mtime(self.watcher_tasks_path),
                    size_bytes=_size(self.watcher_tasks_path),
                )
            )
        return records

    def scan(self, expected_channels: list[str] | None = None) -> dict[str, Any]:
        logs_root = self._discover_vscode_logs_root()
        latest_session = self._latest_vscode_session(logs_root)

        records: list[SourceRecord] = []
        records.extend(self._collect_terminal_logs())
        records.extend(self._collect_watchers())
        records.extend(self._collect_watcher_tasks())

        if latest_session:
            records.extend(self._collect_vscode_output_logging(latest_session))
            records.extend(self._collect_vscode_extension_logs(latest_session))
            records.extend(self._collect_vscode_core_logs(latest_session))

        channels: dict[str, dict[str, Any]] = {}
        source_type_counts: dict[str, int] = {}

        for rec in records:
            source_type_counts[rec.source_type] = source_type_counts.get(rec.source_type, 0) + 1
            key = rec.channel
            entry = channels.setdefault(
                key,
                {
                    "channel": rec.channel,
                    "canonical": _canonical(rec.channel),
                    "source_types": set(),
                    "paths": [],
                    "latest_path": "",
                    "latest_modified": "",
                    "total_bytes": 0,
                },
            )
            entry["source_types"].add(rec.source_type)
            entry["paths"].append(rec.path)
            entry["total_bytes"] += rec.size_bytes
            if rec.last_modified > entry["latest_modified"]:
                entry["latest_modified"] = rec.last_modified
                entry["latest_path"] = rec.path

        for value in channels.values():
            value["source_types"] = sorted(value["source_types"])
            value["paths"] = sorted(set(value["paths"]))

        expected = expected_channels or DEFAULT_EXPECTED_CHANNELS
        by_canonical = {_canonical(name): name for name in channels}
        found_expected: list[str] = []
        missing_expected: list[str] = []
        for channel in expected:
            if _canonical(channel) in by_canonical:
                found_expected.append(channel)
            else:
                missing_expected.append(channel)

        return {
            "timestamp": datetime.now().isoformat(),
            "repo_root": str(self.repo_root),
            "vscode_logs_root": str(logs_root) if logs_root else None,
            "latest_vscode_session": str(latest_session) if latest_session else None,
            "summary": {
                "total_records": len(records),
                "total_channels": len(channels),
                "source_type_counts": source_type_counts,
                "expected_count": len(expected),
                "expected_found": len(found_expected),
                "expected_missing": len(missing_expected),
            },
            "channels": dict(sorted(channels.items(), key=lambda kv: kv[0].lower())),
            "expected": {
                "found": sorted(found_expected),
                "missing": sorted(missing_expected),
            },
        }

    def _find_channel_candidates(
        self, channels: dict[str, dict[str, Any]], requested: str
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Resolve channel candidates using canonical, alias, and fuzzy matching."""
        canon = _canonical(requested)
        entries = list(channels.values())

        direct = [entry for entry in entries if entry.get("canonical") == canon]
        if direct:
            return direct, []

        alias_values = CHANNEL_ALIASES.get(canon, [])
        alias_canonical = {_canonical(value) for value in alias_values}
        alias_matches = [entry for entry in entries if entry.get("canonical") in alias_canonical]
        if alias_matches:
            return alias_matches, []

        by_canonical = {
            str(entry.get("canonical", "")): str(entry.get("channel", ""))
            for entry in entries
            if entry.get("canonical")
        }
        fuzzy_canonical = get_close_matches(canon, list(by_canonical.keys()), n=5, cutoff=0.4)
        suggestions = [by_canonical[item] for item in fuzzy_canonical if by_canonical.get(item)]
        return [], suggestions

    def tail(self, channel: str, lines: int = 40) -> dict[str, Any]:
        report = self.scan()
        channels = report.get("channels", {})
        candidates, suggestions = self._find_channel_candidates(channels, channel)
        if not candidates:
            return {
                "channel": channel,
                "found": False,
                "matches": [],
                "lines": [],
                "suggestions": suggestions,
            }

        source_priority = {
            "nusyq_terminal_log": 100,
            "vscode_output_channel": 90,
            "vscode_extension_log": 80,
            "vscode_core_log": 70,
            "vscode_window_log": 60,
            "terminal_watcher_script": 20,
            "terminal_watcher_task": 10,
        }

        def _candidate_score(item: dict[str, Any]) -> int:
            score = 0
            for source_type in item.get("source_types", []):
                score += source_priority.get(source_type, 1)
            if item.get("channel") == channel:
                score += 50
            return score

        selected = max(
            candidates,
            key=lambda item: (_candidate_score(item), item.get("latest_modified", "")),
        )

        paths = [Path(path) for path in selected.get("paths", [])]
        existing_paths = [path for path in paths if path.exists()]
        existing_paths = [
            path for path in existing_paths if path.suffix.lower() in {".log", ".txt"}
        ]
        existing_paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        tail_lines: list[str] = []
        for path in existing_paths[:2]:
            tail_lines.extend([f"--- {path} ---"])
            tail_lines.extend(_safe_tail(path, lines=lines))

        return {
            "channel": selected.get("channel"),
            "found": True,
            "matches": [str(path) for path in existing_paths],
            "lines": tail_lines[-(lines * 2 + 4) :],
        }

    def _channel_entries(
        self, report: dict[str, Any], channel: str | None = None
    ) -> list[dict[str, Any]]:
        channels = list(report.get("channels", {}).values())
        if not channel:
            return channels
        canon = _canonical(channel)
        return [entry for entry in channels if entry.get("canonical") == canon]

    def tail_since(
        self, channel: str, lines: int = 40, since_minutes: int | None = None
    ) -> dict[str, Any]:
        """Tail output with optional time filtering based on parsed line timestamps."""
        base = self.tail(channel, lines=max(lines * 5, 200))
        if not base.get("found") or since_minutes is None or since_minutes <= 0:
            if len(base.get("lines", [])) > (lines * 2 + 4):
                base["lines"] = base["lines"][-(lines * 2 + 4) :]
            return base

        cutoff = datetime.now(UTC) - timedelta(minutes=since_minutes)
        filtered: list[str] = []
        for line in base.get("lines", []):
            if line.startswith("--- "):
                filtered.append(line)
                continue
            parsed = _parse_line_timestamp(line)
            if parsed is not None and parsed >= cutoff:
                filtered.append(line)

        # Keep only the most recent slice if filtering still returns many lines.
        if len(filtered) > (lines * 2 + 4):
            filtered = filtered[-(lines * 2 + 4) :]

        base["since_minutes"] = since_minutes
        base["cutoff_utc"] = cutoff.isoformat()
        base["lines"] = filtered
        return base

    def load_report(self, report_path: str | Path) -> dict[str, Any]:
        path = Path(report_path)
        if not path.is_absolute():
            path = self.repo_root / path
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_loaded_from"] = str(path)
        return payload

    def diff_reports(
        self, old_report: dict[str, Any], new_report: dict[str, Any]
    ) -> dict[str, Any]:
        old_channels = old_report.get("channels", {})
        new_channels = new_report.get("channels", {})

        old_keys = set(old_channels.keys())
        new_keys = set(new_channels.keys())
        added = sorted(new_keys - old_keys)
        removed = sorted(old_keys - new_keys)

        changed: list[dict[str, Any]] = []
        for key in sorted(old_keys & new_keys):
            old_item = old_channels.get(key, {})
            new_item = new_channels.get(key, {})
            old_modified = old_item.get("latest_modified")
            new_modified = new_item.get("latest_modified")
            old_bytes = int(old_item.get("total_bytes", 0))
            new_bytes = int(new_item.get("total_bytes", 0))
            if old_modified != new_modified or old_bytes != new_bytes:
                changed.append(
                    {
                        "channel": key,
                        "old_latest_modified": old_modified,
                        "new_latest_modified": new_modified,
                        "old_total_bytes": old_bytes,
                        "new_total_bytes": new_bytes,
                        "delta_bytes": new_bytes - old_bytes,
                    }
                )

        old_missing = set(old_report.get("expected", {}).get("missing", []))
        new_missing = set(new_report.get("expected", {}).get("missing", []))
        missing_resolved = sorted(old_missing - new_missing)
        missing_new = sorted(new_missing - old_missing)

        old_types = old_report.get("summary", {}).get("source_type_counts", {})
        new_types = new_report.get("summary", {}).get("source_type_counts", {})
        source_type_delta: dict[str, int] = {}
        for key in sorted(set(old_types) | set(new_types)):
            source_type_delta[key] = int(new_types.get(key, 0)) - int(old_types.get(key, 0))

        return {
            "timestamp": datetime.now().isoformat(),
            "old_source": old_report.get("_loaded_from", "in-memory"),
            "new_source": new_report.get("_loaded_from", "in-memory"),
            "old_timestamp": old_report.get("timestamp"),
            "new_timestamp": new_report.get("timestamp"),
            "summary": {
                "old_total_channels": int(old_report.get("summary", {}).get("total_channels", 0)),
                "new_total_channels": int(new_report.get("summary", {}).get("total_channels", 0)),
                "added_channels": len(added),
                "removed_channels": len(removed),
                "changed_channels": len(changed),
                "missing_resolved": len(missing_resolved),
                "missing_new": len(missing_new),
            },
            "added_channels": added,
            "removed_channels": removed,
            "changed_channels": changed,
            "expected_missing": {
                "resolved": missing_resolved,
                "new": missing_new,
            },
            "source_type_delta": source_type_delta,
        }

    def _channel_log_paths(self, channel_entry: dict[str, Any]) -> list[Path]:
        paths = [Path(p) for p in channel_entry.get("paths", [])]
        existing = [p for p in paths if p.exists()]
        return [p for p in existing if p.suffix.lower() in {".log", ".txt"}]

    def _analyze_channel_noise(
        self, channel_entry: dict[str, Any], sample_lines: int = 400
    ) -> dict[str, Any] | None:
        log_paths = self._channel_log_paths(channel_entry)
        if not log_paths:
            return None
        log_paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        path = log_paths[0]
        lines = _safe_recent_lines(path, max_lines=sample_lines)
        if not lines:
            return None

        total = len(lines)
        error_count = 0
        warning_count = 0
        normalized: dict[str, int] = {}
        for line in lines:
            lowered = line.lower()
            if any(
                token in lowered for token in ("error", "exception", "traceback", "failed", "fatal")
            ):
                error_count += 1
            elif "warning" in lowered:
                warning_count += 1

            compact = re.sub(r"\s+", " ", line.strip())
            if compact:
                normalized[compact] = normalized.get(compact, 0) + 1

        top_repeat = max(normalized.values()) if normalized else 0
        noisy = (error_count >= 10) or (
            (error_count + warning_count) / max(total, 1) >= 0.25 and total >= 20
        )
        if top_repeat >= 8:
            noisy = True

        return {
            "channel": channel_entry.get("channel"),
            "path": str(path),
            "sample_lines": total,
            "error_lines": error_count,
            "warning_lines": warning_count,
            "top_repeat_count": top_repeat,
            "noisy": noisy,
        }

    def _detect_idle_shells(self, idle_minutes: int = 30) -> list[dict[str, Any]]:
        """Detect likely idle VS Code-integrated pwsh shells on Windows hosts."""
        command = (
            "$procs = Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -eq 'pwsh.exe' -and $_.CommandLine -match 'shellIntegration.ps1' }; "
            "$out = @(); "
            "foreach ($proc in $procs) { "
            "  $start = [Management.ManagementDateTimeConverter]::ToDateTime($proc.CreationDate); "
            "  $cpu = $null; "
            "  try { $cpu = (Get-Process -Id $proc.ProcessId -ErrorAction Stop).CPU } catch {} "
            "  $out += [PSCustomObject]@{ pid=$proc.ProcessId; start_time=([DateTimeOffset]$start).ToUniversalTime().ToString('o'); cpu=$cpu; command=$proc.CommandLine }; "
            "} "
            "$out | ConvertTo-Json -Compress"
        )
        try:
            completed = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return []

        if completed.returncode != 0 or not completed.stdout.strip():
            return []

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return []

        items = payload if isinstance(payload, list) else [payload]
        now = datetime.now(UTC)
        idle: list[dict[str, Any]] = []
        for item in items:
            start = self._parse_iso(item.get("start_time"))
            if start is None:
                continue
            age_minutes = (now - start).total_seconds() / 60.0
            cpu = item.get("cpu")
            is_low_cpu = cpu is None or (isinstance(cpu, (int, float)) and cpu <= 0.05)
            if age_minutes >= idle_minutes and is_low_cpu:
                idle.append(
                    {
                        "pid": item.get("pid"),
                        "age_minutes": round(age_minutes, 1),
                        "cpu_seconds": cpu,
                        "start_time": item.get("start_time"),
                        "command": item.get("command"),
                    }
                )
        idle.sort(key=lambda x: float(x.get("age_minutes", 0)), reverse=True)
        return idle

    def stale_report(
        self,
        stale_minutes: int = 240,
        idle_shell_minutes: int = 30,
        noise_sample_lines: int = 400,
        include_static_channels: bool = False,
    ) -> dict[str, Any]:
        report = self.scan()
        channels = list(report.get("channels", {}).values())
        now = datetime.now(UTC)

        stale_channels: list[dict[str, Any]] = []
        noisy_channels: list[dict[str, Any]] = []

        for item in channels:
            source_types = set(item.get("source_types", []))
            static_only = source_types and source_types.issubset(
                {"terminal_watcher_script", "terminal_watcher_task"}
            )
            if static_only and not include_static_channels:
                continue

            latest_modified = self._parse_iso(item.get("latest_modified"))
            if latest_modified is not None:
                age_minutes = (now - latest_modified).total_seconds() / 60.0
                if age_minutes >= stale_minutes:
                    stale_channels.append(
                        {
                            "channel": item.get("channel"),
                            "age_minutes": round(age_minutes, 1),
                            "latest_modified": item.get("latest_modified"),
                            "source_types": item.get("source_types", []),
                            "latest_path": item.get("latest_path"),
                        }
                    )

            noise = self._analyze_channel_noise(item, sample_lines=noise_sample_lines)
            if noise and noise.get("noisy"):
                noisy_channels.append(noise)

        stale_channels.sort(key=lambda x: float(x.get("age_minutes", 0)), reverse=True)
        noisy_channels.sort(
            key=lambda x: (
                int(x.get("error_lines", 0)),
                int(x.get("warning_lines", 0)),
                int(x.get("top_repeat_count", 0)),
            ),
            reverse=True,
        )
        idle_shells = self._detect_idle_shells(idle_minutes=idle_shell_minutes)

        return {
            "timestamp": datetime.now().isoformat(),
            "thresholds": {
                "stale_minutes": stale_minutes,
                "idle_shell_minutes": idle_shell_minutes,
                "noise_sample_lines": noise_sample_lines,
                "include_static_channels": include_static_channels,
            },
            "summary": {
                "total_channels": int(report.get("summary", {}).get("total_channels", 0)),
                "stale_channels": len(stale_channels),
                "noisy_channels": len(noisy_channels),
                "idle_shells": len(idle_shells),
            },
            "stale_channels": stale_channels,
            "noisy_channels": noisy_channels,
            "idle_shells": idle_shells,
        }

    def hints_report(
        self,
        channel: str | None = None,
        since_minutes: int = 60,
        sample_lines: int = 2000,
    ) -> dict[str, Any]:
        """Convert noisy log patterns into practical hints and next steps."""
        report = self.scan()
        entries = self._channel_entries(report, channel=channel)
        cutoff = datetime.now(UTC) - timedelta(minutes=max(1, since_minutes))

        rules = [
            {
                "id": "codex_open_in_target_unsupported",
                "title": "Codex open-in-target unsupported",
                "severity": "high",
                "pattern": re.compile(r"open-in-target.*not supported in extension", re.I),
                "min_hits": 2,
                "guidance": [
                    "Guard the open-in-target call and fallback to plain file open when unsupported.",
                    "Reduce retrial frequency for unsupported capability checks.",
                ],
                "next_steps": [
                    "Add a capability probe cache for open-in-target support per session.",
                    "Route unsupported target operations to a no-op with single warning emission.",
                ],
            },
            {
                "id": "workspace_path_mismatch",
                "title": "Workspace path mismatch (Git worktree ENOENT)",
                "severity": "high",
                "pattern": re.compile(r"failed to list worktrees.*enoent", re.I),
                "min_hits": 2,
                "guidance": [
                    "Workspace path translation is inconsistent between host/runtime contexts.",
                    "Normalize all workspace roots before git-origin/worktree discovery.",
                ],
                "next_steps": [
                    "Prefer one canonical root format per environment (WSL or Windows).",
                    "Add preflight existence checks before worktree listing and downgrade repeated errors to debug after first warning.",
                ],
            },
            {
                "id": "skills_list_hot_loop",
                "title": "Skills/list polling loop is too aggressive",
                "severity": "medium",
                "pattern": re.compile(r"Skills/list request", re.I),
                "min_hits": 120,
                "guidance": [
                    "Frequent skills polling is creating high log volume with low signal.",
                    "Use debounce or TTL caching for unchanged skill manifests.",
                ],
                "next_steps": [
                    "Increase cache TTL for skills listing to reduce repeated calls.",
                    "Gate forceReload=false refreshes behind UI focus or explicit trigger.",
                ],
            },
            {
                "id": "mcp_connection_cli_errors",
                "title": "Codex MCP connection reports CLI errors",
                "severity": "medium",
                "pattern": re.compile(r"CodexMcpConnection.*CLI", re.I),
                "min_hits": 2,
                "guidance": [
                    "MCP transport is active but occasionally failing at CLI boundary.",
                    "Treat transient MCP CLI failures as retryable with backoff.",
                ],
                "next_steps": [
                    "Capture and surface the first full CLI error payload per minute.",
                    "Add exponential backoff and circuit-breaker for repetitive MCP CLI failures.",
                ],
            },
            {
                "id": "shell_integration_capability_delay",
                "title": "Shell integration capability negotiation delays",
                "severity": "low",
                "pattern": re.compile(r"Shell integration failed to add capabilities", re.I),
                "min_hits": 1,
                "guidance": [
                    "Terminal shell integration occasionally misses capability handshake SLA.",
                    "Delay-sensitive automation should verify shell readiness before dispatch.",
                ],
                "next_steps": [
                    "Add a readiness wait with timeout fallback before bulk terminal commands.",
                    "Emit one summarized warning instead of repeated per-terminal warnings.",
                ],
            },
            {
                "id": "terminal_autoapprove_gaps",
                "title": "Terminal auto-approve rules are missing for common safe commands",
                "severity": "low",
                "pattern": re.compile(r"no matching auto approve entries", re.I),
                "min_hits": 1,
                "guidance": [
                    "Safe recurring commands are not whitelisted for auto-approval.",
                    "This increases manual friction and noisy warning output.",
                ],
                "next_steps": [
                    "Add command prefix rules for known-safe terminal tasks.",
                    "Keep non-safe commands interactive and audited.",
                ],
            },
            {
                "id": "copilot_invalid_terminal_id",
                "title": "Copilot terminal output requests are using stale terminal IDs",
                "severity": "high",
                "pattern": re.compile(r"Invalid terminal ID", re.I),
                "min_hits": 2,
                "guidance": [
                    "Terminal IDs are ephemeral and should be resolved from the active VS Code session before each request.",
                    "Do not replay cached terminal IDs across restarts or window reloads.",
                ],
                "next_steps": [
                    "Use channel-based lookup via `nq outputs tail <channel>` instead of PID/terminal ID lookups.",
                    "Invalidate terminal ID caches on VS Code session change and fall back to fresh discovery.",
                ],
            },
            {
                "id": "semgrep_single_file_scan_pressure",
                "title": "Semgrep is repeatedly rescanning single files",
                "severity": "medium",
                "pattern": re.compile(r"Scanning single file", re.I),
                "min_hits": 3,
                "guidance": [
                    "Semgrep is active but being asked to re-scan single files frequently.",
                    "In large workspaces this usually comes from repeated code-action or focus-change requests rather than a crash loop.",
                ],
                "next_steps": [
                    "Set `editor.codeActions.triggerOnFocusChange=false` in workspace settings.",
                    "Keep `semgrep.useExperimentalLS=true`, `semgrep.doHover=false`, and dirty-only scanning enabled.",
                ],
            },
            {
                "id": "vscode_orphaned_extension_dir",
                "title": "VS Code is scanning orphaned extension directories",
                "severity": "medium",
                "pattern": re.compile(
                    r"Unable to read file .*\.vscode[\\/]+extensions[\\/]+.*package\.json",
                    re.I,
                ),
                "min_hits": 1,
                "guidance": [
                    "At least one extension directory exists without a valid `package.json`.",
                    "This adds startup noise and slows extension scans.",
                ],
                "next_steps": [
                    "Run extension integrity cleanup: remove orphaned extension folders and reinstall if needed.",
                    "Re-scan outputs after cleanup to verify the warning is gone from `cli` channel.",
                ],
            },
            {
                "id": "router_fallback_noise",
                "title": "Agent router fallback warnings are dominating error channels",
                "severity": "medium",
                "pattern": re.compile(
                    r"(ChatDev launcher unavailable|Consciousness Bridge routing failed|Analysis failed)",
                    re.I,
                ),
                "min_hits": 8,
                "guidance": [
                    "Expected fallback paths are being logged repeatedly and obscuring real failures.",
                    "Treat these as degraded-mode events with rate-limited summaries.",
                ],
                "next_steps": [
                    "Emit one warning per fallback type per cooldown window, then downgrade repeats to debug.",
                    "Route repeated fallback messages to a dedicated health/degraded channel instead of `errors`.",
                ],
            },
        ]

        evidence_by_rule: dict[str, dict[str, Any]] = {}
        scanned_files: list[str] = []
        analyzed_lines = 0

        for entry in entries:
            paths = self._channel_log_paths(entry)
            if not paths:
                continue
            paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            for path in paths[:2]:
                scanned_files.append(str(path))
                lines = _safe_recent_lines(path, max_lines=sample_lines)
                if not lines:
                    continue

                for line in lines:
                    parsed = _parse_line_timestamp(line)
                    if parsed is not None and parsed < cutoff:
                        continue
                    analyzed_lines += 1
                    for rule in rules:
                        if not rule["pattern"].search(line):
                            continue
                        bucket = evidence_by_rule.setdefault(
                            rule["id"],
                            {
                                "rule": rule,
                                "count": 0,
                                "channels": set(),
                                "examples": [],
                            },
                        )
                        bucket["count"] += 1
                        bucket["channels"].add(entry.get("channel"))
                        if len(bucket["examples"]) < 5:
                            bucket["examples"].append(line[:300])

        issues: list[dict[str, Any]] = []
        for bucket in evidence_by_rule.values():
            rule = bucket["rule"]
            count = int(bucket["count"])
            if count < int(rule["min_hits"]):
                continue
            issues.append(
                {
                    "id": rule["id"],
                    "title": rule["title"],
                    "severity": rule["severity"],
                    "evidence_count": count,
                    "channels": sorted(bucket["channels"]),
                    "examples": bucket["examples"],
                    "guidance": rule["guidance"],
                    "next_steps": rule["next_steps"],
                }
            )

        severity_order = {"high": 0, "medium": 1, "low": 2}
        issues.sort(
            key=lambda item: (severity_order.get(item["severity"], 9), -item["evidence_count"])
        )

        summary = {
            "issue_count": len(issues),
            "high": sum(1 for issue in issues if issue["severity"] == "high"),
            "medium": sum(1 for issue in issues if issue["severity"] == "medium"),
            "low": sum(1 for issue in issues if issue["severity"] == "low"),
        }

        global_guidance: list[str] = []
        if issues:
            global_guidance.extend(
                [
                    "Promote repeated capability errors to one warning + cached decision.",
                    "Convert hot loops to event-driven refresh with debounce and TTL cache.",
                    "Normalize cross-environment paths once at boundary adapters.",
                ]
            )

        return {
            "timestamp": datetime.now().isoformat(),
            "channel_filter": channel,
            "since_minutes": since_minutes,
            "cutoff_utc": cutoff.isoformat(),
            "scanned_channels": sorted(
                _dedupe_preserve(
                    [entry.get("channel", "") for entry in entries if entry.get("channel")]
                )
            ),
            "scanned_files": sorted(_dedupe_preserve(scanned_files)),
            "analyzed_lines": analyzed_lines,
            "summary": summary,
            "issues": issues,
            "global_guidance": global_guidance,
        }
