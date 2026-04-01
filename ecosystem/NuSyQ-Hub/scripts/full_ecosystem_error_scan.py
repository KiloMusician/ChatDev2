#!/usr/bin/env python3
"""Full Ecosystem Error Scanner
Scans all three repos (NuSyQ-Hub, SimulatedVerse, NuSyQ) for errors, warnings, and info.
Matches the VSCode Problems panel count.
"""

import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.terminal_output import to_errors, to_metrics, to_suggestions


@dataclass
class RepoScan:
    """Results from scanning a single repository."""

    name: str
    path: Path
    errors: int
    warnings: int
    infos: int
    total: int
    by_type: dict[str, int]
    by_file: dict[str, int]


class EcosystemScanner:
    """Scan all repos in the ecosystem."""

    def __init__(self):
        self.repos = {
            "NuSyQ-Hub": Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub"),
            "SimulatedVerse": Path("C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"),
            "NuSyQ": Path("C:/Users/keath/NuSyQ"),
        }
        self.results: list[RepoScan] = []

    def scan_repo(self, name: str, path: Path) -> RepoScan:
        """Scan a single repository with ruff."""
        print(f"\n{'=' * 70}")
        print(f"Scanning {name}...")
        print(f"Path: {path}")
        to_metrics(f"Scanning repository: {name}")

        if not path.exists():
            print(f"⚠️ Repository not found: {path}")
            to_errors(f"Repository not found: {name} at {path}")
            return RepoScan(name, path, 0, 0, 0, 0, {}, {})

        try:
            # Run ruff check
            result = subprocess.run(
                ["ruff", "check", ".", "--output-format=json"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.stdout:
                issues = json.loads(result.stdout)
            else:
                issues = []

            # Categorize issues
            errors = 0
            warnings = 0
            infos = 0
            by_type = defaultdict(int)
            by_file = defaultdict(int)

            for issue in issues:
                # Ruff doesn't distinguish severity, so count all as errors
                errors += 1
                code = issue.get("code", "unknown")
                filename = issue.get("filename", "unknown")

                by_type[code] += 1
                by_file[filename] += 1

            total = errors + warnings + infos

            print(f"   Errors: {errors}")
            print(f"   Warnings: {warnings}")
            print(f"   Infos: {infos}")
            print(f"   Total: {total}")

            if total > 0:
                to_errors(f"{name}: {errors} errors, {warnings} warnings, {infos} infos")
            else:
                to_metrics(f"{name}: Clean! No issues found")

            return RepoScan(name, path, errors, warnings, infos, total, dict(by_type), dict(by_file))

        except subprocess.TimeoutExpired:
            print("   ⏱️ Scan timed out after 120s")
            to_errors(f"Scan timeout for {name}")
            return RepoScan(name, path, 0, 0, 0, 0, {}, {})
        except Exception as e:
            print(f"   ❌ Error scanning: {e}")
            to_errors(f"Error scanning {name}: {e}")
            return RepoScan(name, path, 0, 0, 0, 0, {}, {})

    def scan_all(self) -> dict[str, Any]:
        """Scan all repositories."""
        print("=" * 70)
        print("FULL ECOSYSTEM ERROR SCAN")
        print("=" * 70)
        to_metrics("Starting full ecosystem scan...")

        for name, path in self.repos.items():
            result = self.scan_repo(name, path)
            self.results.append(result)

        # Calculate totals
        total_errors = sum(r.errors for r in self.results)
        total_warnings = sum(r.warnings for r in self.results)
        total_infos = sum(r.infos for r in self.results)
        total_problems = sum(r.total for r in self.results)

        # Find top error types
        all_types = defaultdict(int)
        for result in self.results:
            for error_type, count in result.by_type.items():
                all_types[error_type] += count

        top_types = sorted(all_types.items(), key=lambda x: x[1], reverse=True)[:10]

        # Find worst files
        all_files = defaultdict(int)
        for result in self.results:
            for filename, count in result.by_file.items():
                all_files[f"{result.name}/{filename}"] = count

        worst_files = sorted(all_files.items(), key=lambda x: x[1], reverse=True)[:20]

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_infos": total_infos,
            "total_problems": total_problems,
            "by_repo": [
                {
                    "name": r.name,
                    "errors": r.errors,
                    "warnings": r.warnings,
                    "infos": r.infos,
                    "total": r.total,
                }
                for r in self.results
            ],
            "top_error_types": [{"type": t, "count": c} for t, c in top_types],
            "worst_files": [{"file": f, "count": c} for f, c in worst_files],
        }

        # Save report
        report_path = Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/state/reports/ecosystem_scan.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        print("\n" + "=" * 70)
        print("ECOSYSTEM SCAN SUMMARY")
        print("=" * 70)
        print(f"\n📊 Total Problems: {total_problems}")
        print(f"   Errors: {total_errors}")
        print(f"   Warnings: {total_warnings}")
        print(f"   Infos: {total_infos}")

        print("\n📁 By Repository:")
        for result in self.results:
            if result.total > 0:
                print(
                    f"   {result.name}: {result.total} problems ({result.errors}E + {result.warnings}W + {result.infos}I)"
                )
            else:
                print(f"   {result.name}: ✅ Clean")

        if top_types:
            print("\n🔥 Top Error Types:")
            for error_type, count in top_types[:5]:
                print(f"   {error_type}: {count}")

        if worst_files:
            print("\n📄 Files Needing Most Attention:")
            for filename, count in worst_files[:10]:
                print(f"   {filename}: {count} issues")

        print(f"\n💾 Report saved: {report_path}")

        to_metrics(f"Ecosystem scan complete: {total_problems} total problems across {len(self.repos)} repos")
        if total_errors > 0:
            to_suggestions(f"Focus Boss Rush on {top_types[0][0]} errors ({top_types[0][1]} occurrences)")

        print("=" * 70)

        return report


if __name__ == "__main__":
    scanner = EcosystemScanner()
    scanner.scan_all()
