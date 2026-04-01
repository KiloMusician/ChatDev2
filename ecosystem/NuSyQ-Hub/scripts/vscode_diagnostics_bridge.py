#!/usr/bin/env python3
"""VSCode Diagnostics Bridge - Agent-Accessible Error Truth

This script provides a bridge between VSCode's diagnostic system and all
agents in the ecosystem. It queries the active language servers and extension
diagnostics to provide the same error counts that the human sees in VSCode.

IMPORTANT: This is the SINGLE SOURCE OF TRUTH for error counts.
All agents (Claude Code, Copilot, Ollama, ChatDev, etc.) should read the
output from this script rather than running their own linters.

Output:
- docs/Reports/diagnostics/vscode_problem_counts_tooling.json - Tool-derived counts
- docs/Reports/diagnostics/vscode_diagnostics_bridge.json - Full snapshot

Usage:
    # For agents to get current error counts
    python scripts/vscode_diagnostics_bridge.py

    # To export diagnostics for debugging
    python scripts/vscode_diagnostics_bridge.py --export diagnostics.json
"""

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from src.utils.repo_path_resolver import get_repo_path
except Exception:
    get_repo_path = None

# Add repo root to path for proper imports
_script_dir = Path(__file__).parent.resolve()
_repo_root = _script_dir.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

try:
    from src.system.output_source_intelligence import OutputSourceIntelligence
except Exception:
    OutputSourceIntelligence = None  # type: ignore[misc, assignment]


@dataclass
class DiagnosticItem:
    """Single diagnostic item from VSCode."""

    file: str
    line: int
    column: int
    severity: str  # "error", "warning", "info", "hint"
    source: str  # "Pylance", "Ruff", "mypy", etc.
    code: str | None
    message: str


@dataclass
class DiagnosticSummary:
    """Summary of diagnostics by source and severity."""

    timestamp: str
    errors: int
    warnings: int
    infos: int
    hints: int
    total: int
    by_source: dict[str, dict[str, int]]
    by_file: dict[str, dict[str, int]]
    items: list[dict[str, Any]] | None = None
    exthost_issues: list[dict[str, Any]] | None = None
    pytest_failures: list[dict[str, Any]] | None = None
    log_session: str | None = None


class VSCodeDiagnosticsBridge:
    """Bridge to VSCode diagnostics for cross-agent consistency."""

    def __init__(self):
        if get_repo_path:
            try:
                self.repo_root = get_repo_path("NUSYQ_HUB_ROOT")
            except Exception:
                self.repo_root = Path(__file__).parent.parent
        else:
            self.repo_root = Path(__file__).parent.parent
        self.output_dir = self.repo_root / "docs" / "Reports" / "diagnostics"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_ruff_diagnostics(self) -> list[DiagnosticItem]:
        """Get diagnostics from Ruff (VSCode's primary Python linter)."""
        items = []

        try:
            # Run ruff with JSON output
            result = subprocess.run(
                ["python", "-m", "ruff", "check", "src", "--output-format=json"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout.strip():
                ruff_results = json.loads(result.stdout)

                for item in ruff_results:
                    # Ruff severity mapping
                    severity = "error" if item.get("code", "").startswith("E") else "warning"

                    items.append(
                        DiagnosticItem(
                            file=item["filename"],
                            line=item["location"]["row"],
                            column=item["location"]["column"],
                            severity=severity,
                            source="Ruff",
                            code=item.get("code"),
                            message=item.get("message", ""),
                        )
                    )
        except Exception as e:
            print(f"Warning: Could not get Ruff diagnostics: {e}", file=sys.stderr)

        return items

    def get_pylance_diagnostics(self) -> list[DiagnosticItem]:
        """Get type checking diagnostics from Pylance/Pyright.

        This runs pyright (Pylance's engine) with the workspace configuration
        to match VSCode's Python extension behavior.
        """
        items = []

        try:
            # Run pyright with JSON output
            result = subprocess.run(
                ["python", "-m", "pyright", "src", "--outputjson"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.stdout.strip():
                pyright_output = json.loads(result.stdout)

                for diagnostic in pyright_output.get("generalDiagnostics", []):
                    severity_map = {"error": "error", "warning": "warning", "information": "info"}

                    items.append(
                        DiagnosticItem(
                            file=diagnostic["file"],
                            line=diagnostic["range"]["start"]["line"] + 1,
                            column=diagnostic["range"]["start"]["character"] + 1,
                            severity=severity_map.get(diagnostic["severity"], "info"),
                            source="Pylance",
                            code=diagnostic.get("rule"),
                            message=diagnostic["message"],
                        )
                    )
        except FileNotFoundError:
            # Pyright not available, skip
            print("Info: Pyright not installed - install with: pip install pyright", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse Pyright output: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not get Pylance diagnostics: {e}", file=sys.stderr)

        return items

    def get_log_diagnostics(self) -> dict[str, Any]:
        """Get diagnostics from VS Code logs via OutputSourceIntelligence.

        Returns:
            dict containing:
                - exthost_issues: list of extension host errors/warnings
                - pytest_failures: list of recent pytest failures
                - session: path to current VS Code log session
        """
        result: dict[str, Any] = {
            "exthost_issues": [],
            "pytest_failures": [],
            "session": None,
        }

        if OutputSourceIntelligence is None:
            print(
                "Info: OutputSourceIntelligence not available for log parsing",
                file=sys.stderr,
            )
            return result

        try:
            intel = OutputSourceIntelligence()
            aggregated = intel.aggregate_all_diagnostics()

            result["session"] = aggregated.get("session")
            result["exthost_issues"] = aggregated.get("exthost_issues", [])
            result["pytest_failures"] = aggregated.get("pytest_failures", [])

        except Exception as e:
            print(f"Warning: Could not get log diagnostics: {e}", file=sys.stderr)

        return result

    def get_active_diagnostics(self) -> DiagnosticSummary:
        """Get diagnostics from all active VSCode language servers."""
        all_items = []

        # Get Ruff diagnostics (primary linter in VSCode)
        print("📋 Fetching Ruff diagnostics...", file=sys.stderr)
        all_items.extend(self.get_ruff_diagnostics())

        # Get Pylance diagnostics (type checking)
        print("📋 Fetching Pylance diagnostics...", file=sys.stderr)
        all_items.extend(self.get_pylance_diagnostics())

        # Get VS Code log diagnostics (exthost errors, pytest failures)
        print("📋 Fetching VS Code log diagnostics...", file=sys.stderr)
        log_diags = self.get_log_diagnostics()

        # Calculate summary
        errors = sum(1 for item in all_items if item.severity == "error")
        warnings = sum(1 for item in all_items if item.severity == "warning")
        infos = sum(1 for item in all_items if item.severity == "info")
        hints = sum(1 for item in all_items if item.severity == "hint")

        # Group by source
        by_source: dict[str, dict[str, int]] = {}
        for item in all_items:
            if item.source not in by_source:
                by_source[item.source] = {"errors": 0, "warnings": 0, "infos": 0, "hints": 0}
            by_source[item.source][f"{item.severity}s"] = by_source[item.source].get(f"{item.severity}s", 0) + 1

        # Group by file
        by_file: dict[str, dict[str, int]] = {}
        for item in all_items:
            if item.file not in by_file:
                by_file[item.file] = {"errors": 0, "warnings": 0, "infos": 0, "hints": 0}
            by_file[item.file][f"{item.severity}s"] = by_file[item.file].get(f"{item.severity}s", 0) + 1

        # Add log-based diagnostic counts to by_source
        exthost_errors = sum(
            1 for i in log_diags["exthost_issues"] if str(i.get("level", "")).lower() in ("error", "err")
        )
        exthost_warnings = sum(
            1 for i in log_diags["exthost_issues"] if str(i.get("level", "")).lower() in ("warning", "warn")
        )
        if log_diags["exthost_issues"]:
            by_source["VSCode-ExtHost"] = {
                "errors": exthost_errors,
                "warnings": exthost_warnings,
                "infos": 0,
                "hints": 0,
            }

        pytest_count = len(log_diags["pytest_failures"])
        if pytest_count > 0:
            by_source["Pytest-Log"] = {
                "errors": pytest_count,
                "warnings": 0,
                "infos": 0,
                "hints": 0,
            }

        return DiagnosticSummary(
            timestamp=datetime.now().isoformat(),
            errors=errors,
            warnings=warnings,
            infos=infos,
            hints=hints,
            total=errors + warnings + infos + hints,
            by_source=by_source,
            by_file=by_file,
            items=[asdict(item) for item in all_items],
            exthost_issues=log_diags["exthost_issues"] or None,
            pytest_failures=log_diags["pytest_failures"] or None,
            log_session=str(log_diags["session"]) if log_diags["session"] else None,
        )

    def save_diagnostics(
        self,
        summary: DiagnosticSummary,
        include_items: bool = False,
        override_truth: bool = False,
    ):
        """Save diagnostics snapshot under docs/Reports/diagnostics."""
        detail_path = self.output_dir / "vscode_diagnostics_bridge.json"
        counts_path = self.output_dir / "vscode_problem_counts_tooling.json"
        diagnostics_export_path = self.output_dir / "vscode_diagnostics_export.json"
        legacy_export_path = self.repo_root / "data" / "diagnostics" / "vscode_diagnostics_export.json"
        legacy_export_path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(summary)
        if not include_items:
            data.pop("items", None)

        with open(detail_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        counts_payload = {
            "source": "vscode_diagnostics_bridge",
            "timestamp": summary.timestamp,
            "counts": {
                "errors": summary.errors,
                "warnings": summary.warnings,
                "infos": summary.infos,
                "total": summary.total,
            },
        }
        with open(counts_path, "w", encoding="utf-8") as f:
            json.dump(counts_payload, f, indent=2)

        items = summary.items or []
        by_category = {
            "errors": sum(1 for item in items if item.get("severity") == "error"),
            "warnings": sum(1 for item in items if item.get("severity") == "warning"),
            "infos": sum(1 for item in items if item.get("severity") == "info"),
            "hints": sum(1 for item in items if item.get("severity") == "hint"),
        }
        export_payload = {
            "total_issues": len(items),
            "by_category": by_category,
            "issues": [
                {
                    "tool": item.get("source"),
                    "file": item.get("file"),
                    "line": item.get("line"),
                    "severity": item.get("severity"),
                    "message": item.get("message"),
                    "code": item.get("code"),
                }
                for item in items
            ],
        }
        for export_path in (diagnostics_export_path, legacy_export_path):
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(export_payload, f, indent=2)

        if override_truth:
            truth_path = self.output_dir / "vscode_problem_counts.json"
            with open(truth_path, "w", encoding="utf-8") as f:
                json.dump(counts_payload, f, indent=2)
            print(f"💾 VSCode truth counts saved to: {truth_path}", file=sys.stderr)

        print(f"💾 VSCode diagnostics saved to: {detail_path}", file=sys.stderr)
        print(f"💾 VSCode counts saved to: {counts_path}", file=sys.stderr)
        print(f"💾 VSCode export saved to: {diagnostics_export_path}", file=sys.stderr)
        print(f"💾 VSCode export saved to: {legacy_export_path}", file=sys.stderr)

    def display_summary(self, summary: DiagnosticSummary):
        """Display diagnostics summary to console."""
        print("\n" + "=" * 70)
        print("🔍 VSCODE DIAGNOSTICS SUMMARY")
        print("=" * 70)
        print(f"  Errors:   {summary.errors}")
        print(f"  Warnings: {summary.warnings}")
        print(f"  Infos:    {summary.infos}")
        print(f"  Hints:    {summary.hints}")
        print(f"  Total:    {summary.total}")

        if summary.by_source:
            print("\n📊 By Source:")
            for source, counts in summary.by_source.items():
                total = sum(counts.values())
                print(f"  {source}: {total} total")
                for severity, count in counts.items():
                    if count > 0:
                        print(f"    - {severity}: {count}")

        # Display log-based diagnostics
        if summary.log_session:
            print(f"\n📁 VS Code Log Session: {summary.log_session}")

        if summary.exthost_issues:
            print(f"\n🔌 Extension Host Issues: {len(summary.exthost_issues)}")
            for issue in summary.exthost_issues[:5]:
                level = issue.get("level", "?")
                msg = issue.get("message", "")[:60]
                print(f"  [{level}] {msg}...")
            if len(summary.exthost_issues) > 5:
                print(f"  ... and {len(summary.exthost_issues) - 5} more")

        if summary.pytest_failures:
            print(f"\n🧪 Pytest Failures from Log: {len(summary.pytest_failures)}")
            for fail in summary.pytest_failures[:5]:
                test = fail.get("test", "?")
                print(f"  ❌ {test}")
            if len(summary.pytest_failures) > 5:
                print(f"  ... and {len(summary.pytest_failures) - 5} more")

        print("\n" + "=" * 70)


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="VSCode Diagnostics Bridge - Single Source of Truth for Errors")
    parser.add_argument("--export", metavar="PATH", help="Export full diagnostics with items to specified path")
    parser.add_argument(
        "--override-truth",
        action="store_true",
        help="Overwrite vscode_problem_counts.json with tooling-derived counts",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress console output")

    args = parser.parse_args(argv)

    bridge = VSCodeDiagnosticsBridge()
    summary = bridge.get_active_diagnostics()

    # Save to state directory
    bridge.save_diagnostics(
        summary,
        include_items=bool(args.export),
        override_truth=bool(args.override_truth),
    )

    # Export if requested
    if args.export:
        export_path = Path(args.export)
        with open(export_path, "w") as f:
            json.dump(asdict(summary), f, indent=2)
        print(f"📤 Full diagnostics exported to: {export_path}", file=sys.stderr)

    # Display summary
    if not args.quiet:
        bridge.display_summary(summary)

    # Exit code: 0 if no errors, 1 if errors
    return 1 if summary.errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
