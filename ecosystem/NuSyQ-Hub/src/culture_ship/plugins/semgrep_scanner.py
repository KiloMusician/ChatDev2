"""Culture Ship plugin — semgrep SAST scanner with auto-fix support."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

# Default ruleset — covers common security + correctness patterns across languages
_DEFAULT_CONFIG = "auto"


class SemgrepScannerPlugin:
    """Run semgrep and surface security/correctness findings for Culture Ship triage."""

    def __init__(self, config: str = _DEFAULT_CONFIG) -> None:
        """Initialize SemgrepScannerPlugin with config."""
        self.name = "semgrep_scanner"
        self.description = "Scan source code via semgrep for security and correctness issues"
        self._config = config

    def analyze(self, targets: list[str], dry_run: bool = False) -> dict[str, Any]:
        """Run semgrep in scan mode and parse structured JSON output."""
        if not shutil.which("semgrep"):
            return {
                "plugin": self.name,
                "error": "semgrep not found in PATH (install: pip install semgrep)",
                "findings": 0,
                "targets": targets,
                "dry_run": dry_run,
            }

        cmd = [
            "semgrep",
            "--config",
            self._config,
            "--json",
            "--quiet",
            "--no-git-ignore",  # respect repo, not git
            *targets,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False)
            data = self._parse_json(result.stdout)
            findings = data.get("results", [])
            errors = data.get("errors", [])

            return {
                "plugin": self.name,
                "findings": len(findings),
                "finding_details": self._summarize(findings)[:50],  # cap payload
                "scan_errors": len(errors),
                "exit_code": result.returncode,
                "dry_run": dry_run,
                "targets": targets,
                "config": self._config,
            }
        except subprocess.TimeoutExpired as exc:
            return {"plugin": self.name, "error": str(exc), "findings": 0, "targets": targets}

    def fix(self, analysis: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
        """Apply semgrep --autofix where rules support it."""
        if dry_run or not shutil.which("semgrep"):
            return {"plugin": self.name, "fixes_applied": 0, "files_modified": []}

        targets = analysis.get("targets", ["."])
        cmd = [
            "semgrep",
            "--config",
            self._config,
            "--autofix",
            "--quiet",
            "--json",
            *targets,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=False)
            data = self._parse_json(result.stdout)
            fixed = data.get("results", [])
            fixed_files = sorted(
                {
                    r.get("path", "")
                    for r in fixed
                    if r.get("extra", {}).get("fixed_lines") is not None
                }
                - {""}
            )

            return {
                "plugin": self.name,
                "fixes_applied": len(fixed_files),
                "files_modified": fixed_files,
                "findings_remaining": analysis.get("findings", 0) - len(fixed_files),
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "plugin": self.name,
                "error": str(exc),
                "fixes_applied": 0,
                "files_modified": [],
            }

    # ── helpers ──────────────────────────────────────────────────────────────

    def _parse_json(self, text: str) -> dict[str, Any]:
        try:
            return json.loads(text) if text.strip() else {}
        except (ValueError, json.JSONDecodeError):
            return {}

    def _summarize(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract the fields most useful for triage."""
        out: list[dict[str, Any]] = []
        for f in findings:
            extra = f.get("extra", {})
            out.append(
                {
                    "rule_id": f.get("check_id", ""),
                    "path": f.get("path", ""),
                    "line": f.get("start", {}).get("line"),
                    "severity": extra.get("severity", ""),
                    "message": extra.get("message", "")[:200],
                    "fixable": extra.get("fix") is not None or extra.get("fixed_lines") is not None,
                }
            )
        return out
