"""Culture Ship plugin — mypy type-checking with structured error output."""

from __future__ import annotations

import re
import subprocess
from typing import Any

# Regex to parse mypy output lines: file.py:line: severity: message  [code]
_MYPY_LINE_RE = re.compile(
    r"^(?P<file>[^:]+):(?P<line>\d+)(?::\d+)?: (?P<severity>error|warning|note): (?P<message>.+?)(?:\s+\[(?P<code>[^\]]+)\])?$"
)


class MypyCheckerPlugin:
    """Run mypy and surface type errors for Culture Ship triage."""

    def __init__(self) -> None:
        """Initialize MypyCheckerPlugin."""
        self.name = "mypy_checker"
        self.description = "Type-check Python sources via mypy and report errors"

    def analyze(self, targets: list[str], dry_run: bool = False) -> dict[str, Any]:
        """Run mypy in check-only mode and parse structured output."""
        cmd = [
            "python",
            "-m",
            "mypy",
            *targets,
            "--no-error-summary",
            "--show-column-numbers",
            "--follow-imports=skip",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
            errors, warnings, notes = self._parse_output(result.stdout)
            return {
                "plugin": self.name,
                "errors": len(errors),
                "warnings": len(warnings),
                "notes": len(notes),
                "error_details": errors[:100],  # cap payload
                "exit_code": result.returncode,
                "dry_run": dry_run,
                "targets": targets,
            }
        except subprocess.TimeoutExpired as exc:
            return {"plugin": self.name, "error": str(exc), "errors": 0, "targets": targets}

    def fix(self, analysis: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
        """Mypy has no auto-fix — return a report of files needing attention."""
        if dry_run:
            return {"plugin": self.name, "fixes_applied": 0, "files_modified": []}

        error_details: list[dict[str, Any]] = analysis.get("error_details", [])
        affected_files = sorted({e["file"] for e in error_details if e.get("file")})
        # Group errors by file so callers know where to focus
        by_file: dict[str, list[dict[str, Any]]] = {}
        for entry in error_details:
            f = entry.get("file", "unknown")
            by_file.setdefault(f, []).append(entry)

        return {
            "plugin": self.name,
            "fixes_applied": 0,  # mypy is report-only; fixes require manual edits
            "files_modified": [],
            "files_with_errors": affected_files,
            "errors_by_file": {f: len(errs) for f, errs in by_file.items()},
            "top_error_codes": self._top_codes(error_details),
            "note": (
                f"mypy found {analysis.get('errors', 0)} type errors across "
                f"{len(affected_files)} file(s). Review 'errors_by_file' for triage priority."
            ),
        }

    # ── helpers ──────────────────────────────────────────────────────────────

    def _parse_output(
        self, output: str
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        notes: list[dict[str, Any]] = []
        for line in output.splitlines():
            m = _MYPY_LINE_RE.match(line.strip())
            if not m:
                continue
            entry: dict[str, Any] = {
                "file": m.group("file"),
                "line": int(m.group("line")),
                "severity": m.group("severity"),
                "message": m.group("message"),
                "code": m.group("code") or "",
            }
            if m.group("severity") == "error":
                errors.append(entry)
            elif m.group("severity") == "warning":
                warnings.append(entry)
            else:
                notes.append(entry)
        return errors, warnings, notes

    def _top_codes(self, errors: list[dict[str, Any]], top_n: int = 10) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for e in errors:
            code = e.get("code") or "unknown"
            counts[code] = counts.get(code, 0) + 1
        return [
            {"code": c, "count": n} for c, n in sorted(counts.items(), key=lambda x: -x[1])[:top_n]
        ]
