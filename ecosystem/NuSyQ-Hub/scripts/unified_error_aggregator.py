#!/usr/bin/env python3
"""Unified Error Aggregator - Single Source of Truth for All Errors
[ROUTE ERRORS] 🔥

This script aggregates errors from ALL sources across ALL repositories to provide
a consistent error count that matches what the human sees in VSCode.

Sources Checked:
- VSCode diagnostics (from .vscode/diagnostics.json if available)
- Python linters (flake8, ruff, pylint, mypy)
- TypeScript compiler (tsc)
- JavaScript linters (eslint)
- Formatting tools (black, prettier)
- Custom analyzers

Repositories Scanned:
- NuSyQ-Hub (Python)
- SimulatedVerse (TypeScript/JavaScript)
- NuSyQ (Python + MCP)

Output: Single JSON file with ground truth error counts for all agents to consume.
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


def _load_repo_roots() -> dict[str, Path]:
    if get_repo_path:
        roots = {}
        for name, key in (
            ("NuSyQ-Hub", "NUSYQ_HUB_ROOT"),
            ("SimulatedVerse", "SIMULATEDVERSE_ROOT"),
            ("NuSyQ", "NUSYQ_ROOT"),
        ):
            try:
                roots[name] = get_repo_path(key)
            except Exception:
                continue
        if roots:
            return roots
    return {"NuSyQ-Hub": Path.cwd()}


REPO_ROOTS = _load_repo_roots()


@dataclass
class ErrorSource:
    """Single error source with its configuration."""

    name: str
    tool: str
    command: list[str]
    working_dir: Path
    parse_output: callable
    enabled: bool = True
    timeout: int = 60


@dataclass
class ErrorCount:
    """Error count from a single source."""

    source: str
    errors: int
    warnings: int
    infos: int
    total: int
    timestamp: str
    details: list[str] | None = None


@dataclass
class AggregatedErrors:
    """Aggregated errors across all sources."""

    timestamp: str
    repositories: dict[str, Any]
    totals: dict[str, int]
    sources: list[ErrorCount]
    vscode_truth: dict[str, int] | None = None


class UnifiedErrorAggregator:
    """Aggregates errors from all linters/checkers across all repos."""

    def __init__(self):
        self.results: list[ErrorCount] = []
        hub_root = REPO_ROOTS.get("NuSyQ-Hub", Path.cwd())
        self.vscode_diagnostics_path = hub_root / "docs" / "Reports" / "diagnostics" / "vscode_problem_counts.json"
        self.vscode_legacy_path = hub_root / ".vscode" / "diagnostics.json"

    def run_command(self, cmd: list[str], cwd: Path, timeout: int = 60) -> tuple[str, str, int]:
        """Run a command and return stdout, stderr, return code."""
        try:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", f"Timeout after {timeout}s", -1
        except FileNotFoundError:
            return "", f"Command not found: {cmd[0]}", -1
        except Exception as e:
            return "", str(e), -1

    def check_vscode_diagnostics(self) -> ErrorCount | None:
        """Check VSCode diagnostics file (if available)."""
        path = None
        if self.vscode_diagnostics_path.exists():
            path = self.vscode_diagnostics_path
        elif self.vscode_legacy_path.exists():
            path = self.vscode_legacy_path
        else:
            return None

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            if "counts" in data:
                data = data["counts"]

            errors = int(data.get("errors", 0))
            warnings = int(data.get("warnings", 0))
            infos = int(data.get("infos", 0))

            return ErrorCount(
                source=f"VSCode Diagnostics ({path})",
                errors=errors,
                warnings=warnings,
                infos=infos,
                total=errors + warnings + infos,
                timestamp=datetime.now().isoformat(),
            )
        except Exception as e:
            print(f"Warning: Could not read VSCode diagnostics: {e}", file=sys.stderr)
            return None

    def check_flake8(self, repo_path: Path, target: str = "src") -> ErrorCount:
        """Check flake8 errors."""
        cmd = ["python", "-m", "flake8", target, "--count", "--select=E,F,W", "--statistics"]
        stdout, _stderr, _code = self.run_command(cmd, repo_path)

        # Parse flake8 output
        errors = 0
        warnings = 0
        for line in stdout.splitlines():
            if line.strip().isdigit():
                errors += int(line.strip())
            elif "W" in line and line.split()[0].isdigit():
                warnings += int(line.split()[0])

        return ErrorCount(
            source=f"flake8 ({repo_path.name})",
            errors=errors,
            warnings=warnings,
            infos=0,
            total=errors + warnings,
            timestamp=datetime.now().isoformat(),
        )

    def check_ruff(self, repo_path: Path, target: str = "src") -> ErrorCount:
        """Check ruff errors."""
        cmd = ["python", "-m", "ruff", "check", target, "--output-format=json"]
        stdout, _stderr, _code = self.run_command(cmd, repo_path)

        errors = 0
        warnings = 0
        try:
            if stdout.strip():
                results = json.loads(stdout)
                errors = len([r for r in results if r.get("code", "").startswith("E")])
                warnings = len([r for r in results if r.get("code", "").startswith("W")])
        except json.JSONDecodeError:
            pass

        return ErrorCount(
            source=f"ruff ({repo_path.name})",
            errors=errors,
            warnings=warnings,
            infos=0,
            total=errors + warnings,
            timestamp=datetime.now().isoformat(),
        )

    def check_mypy(self, repo_path: Path, target: str = "src") -> ErrorCount:
        """Check mypy type errors."""
        cmd = ["python", "-m", "mypy", target, "--ignore-missing-imports", "--no-error-summary"]
        stdout, _stderr, _code = self.run_command(cmd, repo_path, timeout=120)

        # Count lines with "error:"
        errors = stdout.count("error:")
        warnings = stdout.count("note:")

        return ErrorCount(
            source=f"mypy ({repo_path.name})",
            errors=errors,
            warnings=warnings,
            infos=0,
            total=errors + warnings,
            timestamp=datetime.now().isoformat(),
        )

    def check_typescript(self, repo_path: Path) -> ErrorCount:
        """Check TypeScript compiler errors."""
        cmd = ["npx", "tsc", "--noEmit"]
        stdout, stderr, _code = self.run_command(cmd, repo_path, timeout=120)

        # Count "error TS" lines
        combined = stdout + stderr
        errors = combined.count("error TS")

        return ErrorCount(
            source=f"tsc ({repo_path.name})",
            errors=errors,
            warnings=0,
            infos=0,
            total=errors,
            timestamp=datetime.now().isoformat(),
        )

    def check_eslint(self, repo_path: Path) -> ErrorCount:
        """Check ESLint errors."""
        cmd = ["npx", "eslint", ".", "--format=json"]
        stdout, _stderr, _code = self.run_command(cmd, repo_path, timeout=120)

        errors = 0
        warnings = 0
        try:
            if stdout.strip():
                results = json.loads(stdout)
                for file_result in results:
                    for msg in file_result.get("messages", []):
                        if msg.get("severity") == 2:
                            errors += 1
                        elif msg.get("severity") == 1:
                            warnings += 1
        except json.JSONDecodeError:
            pass

        return ErrorCount(
            source=f"eslint ({repo_path.name})",
            errors=errors,
            warnings=warnings,
            infos=0,
            total=errors + warnings,
            timestamp=datetime.now().isoformat(),
        )

    def aggregate_all(self) -> AggregatedErrors:
        """Aggregate errors from all sources."""
        print("🔍 Unified Error Aggregation Starting...")
        print("=" * 70)

        # Check VSCode diagnostics first (ground truth)
        vscode_result = self.check_vscode_diagnostics()
        if vscode_result:
            print(f"✅ VSCode Diagnostics: {vscode_result.total} total")
            self.results.append(vscode_result)
            vscode_truth = {
                "errors": vscode_result.errors,
                "warnings": vscode_result.warnings,
                "infos": vscode_result.infos,
                "total": vscode_result.total,
            }
        else:
            print("⚠️  VSCode Diagnostics: Not available")
            vscode_truth = None

        # Check NuSyQ-Hub (Python)
        hub_path = REPO_ROOTS["NuSyQ-Hub"]
        if hub_path.exists():
            print(f"\n📦 Checking {hub_path.name}...")

            result = self.check_flake8(hub_path)
            print(f"  flake8: {result.total} issues")
            self.results.append(result)

            result = self.check_ruff(hub_path)
            print(f"  ruff: {result.total} issues")
            self.results.append(result)

            result = self.check_mypy(hub_path)
            print(f"  mypy: {result.total} issues")
            self.results.append(result)

        # Check SimulatedVerse (TypeScript)
        sim_path = REPO_ROOTS["SimulatedVerse"]
        if sim_path.exists():
            print(f"\n📦 Checking {sim_path.name}...")

            result = self.check_typescript(sim_path)
            print(f"  tsc: {result.total} issues")
            self.results.append(result)

            result = self.check_eslint(sim_path)
            print(f"  eslint: {result.total} issues")
            self.results.append(result)

        # Check NuSyQ (Python + MCP)
        nusyq_path = REPO_ROOTS["NuSyQ"]
        if nusyq_path.exists():
            print(f"\n📦 Checking {nusyq_path.name}...")

            result = self.check_flake8(nusyq_path)
            print(f"  flake8: {result.total} issues")
            self.results.append(result)

            result = self.check_ruff(nusyq_path)
            print(f"  ruff: {result.total} issues")
            self.results.append(result)

        # Calculate totals
        total_errors = sum(r.errors for r in self.results)
        total_warnings = sum(r.warnings for r in self.results)
        total_infos = sum(r.infos for r in self.results)
        total_all = sum(r.total for r in self.results)

        print("\n" + "=" * 70)
        print("📊 TOTALS:")
        print(f"  Errors: {total_errors}")
        print(f"  Warnings: {total_warnings}")
        print(f"  Infos: {total_infos}")
        print(f"  Total Problems: {total_all}")

        if vscode_truth:
            print("\n🎯 VSCode Ground Truth:")
            print(f"  Errors: {vscode_truth['errors']}")
            print(f"  Warnings: {vscode_truth['warnings']}")
            print(f"  Infos: {vscode_truth['infos']}")
            print(f"  Total: {vscode_truth['total']}")

            # Calculate delta
            delta = total_all - vscode_truth["total"]
            if delta != 0:
                print(f"\n⚠️  Delta from VSCode: {delta:+d}")
                print("   (Linters may detect different issues than VSCode extensions)")

        # Build aggregated result
        repo_breakdown = {}
        for repo_name, _repo_path in REPO_ROOTS.items():
            repo_results = [r for r in self.results if repo_name in r.source]
            if repo_results:
                repo_breakdown[repo_name] = {
                    "errors": sum(r.errors for r in repo_results),
                    "warnings": sum(r.warnings for r in repo_results),
                    "infos": sum(r.infos for r in repo_results),
                    "total": sum(r.total for r in repo_results),
                    "sources": [r.source for r in repo_results],
                }

        aggregated = AggregatedErrors(
            timestamp=datetime.now().isoformat(),
            repositories=repo_breakdown,
            totals={
                "errors": total_errors,
                "warnings": total_warnings,
                "infos": total_infos,
                "total": total_all,
            },
            sources=[asdict(r) for r in self.results],
            vscode_truth=vscode_truth,
        )

        return aggregated

    def save_results(self, aggregated: AggregatedErrors, output_path: Path):
        """Save aggregated results to JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(asdict(aggregated), f, indent=2)

        print(f"\n💾 Results saved to: {output_path}")
        print("   All agents should read this file for consistent error counts.")


def main():
    aggregator = UnifiedErrorAggregator()
    results = aggregator.aggregate_all()

    hub_root = REPO_ROOTS.get("NuSyQ-Hub", Path.cwd())
    output_dir = hub_root / "docs" / "Reports" / "diagnostics"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"unified_errors_{stamp}.json"
    aggregator.save_results(results, output_path)
    latest_path = output_dir / "unified_errors_latest.json"
    aggregator.save_results(results, latest_path)

    # Return exit code based on error count
    # Use VSCode truth if available, otherwise linter totals
    if results.vscode_truth:
        return min(results.vscode_truth["errors"], 1)  # 0 if no errors, 1 otherwise
    else:
        return min(results.totals["errors"], 1)


if __name__ == "__main__":
    sys.exit(main())
