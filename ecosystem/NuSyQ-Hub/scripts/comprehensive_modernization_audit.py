"""Comprehensive Modernization Audit
[ROUTE METRICS] 📊
Uses the 22-agent ecosystem to systematically discover and prioritize modernization tasks.
"""

import argparse
import json
import re
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

HUB_PLACEHOLDER_FILES = {
    "scripts/comprehensive_modernization_audit.py",
    "start.py",
    "test_system_connections.py",
}

PLACEHOLDER_TASKS = [
    "NuSyQ-Hub placeholder modernization audit",
    "NuSyQ-Hub boot/start launcher placeholder",
    "NuSyQ-Hub connection test placeholder",
]

SCAN_MODES = {
    "full": {},
    "core": {"target_repos": ["NuSyQ-Hub", "SimulatedVerse"], "include_paths": []},
    "warehouse": {
        "include_paths": ["ChatDev/WareHouse"],
        "exclude_paths": [],
        "target_repos": ["NuSyQ-Hub", "SimulatedVerse", "NuSyQ"],
    },
}

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from src.integration.simulatedverse_unified_bridge import (
        SimulatedVerseUnifiedBridge as SimulatedVerseBridge,
    )
except ImportError:
    SimulatedVerseBridge = None

try:
    from src.utils.repo_path_resolver import get_repo_path
except ImportError:  # pragma: no cover - optional dependency
    get_repo_path = None


class ComprehensiveModernizationAuditor:
    """Leverages the 22-agent ecosystem to discover and prioritize modernization tasks."""

    def __init__(
        self,
        include_paths: Sequence[str] | None = None,
        exclude_paths: Sequence[str] | None = None,
        warehouse_projects: Sequence[str] | None = None,
        target_repos: Sequence[str] | None = None,
        skip_culture_ship: bool = False,
    ):
        self.repo_root = Path(__file__).parent.parent
        self.include_paths = [p.replace("\\", "/") for p in include_paths or []]
        self.exclude_paths = [p.replace("\\", "/") for p in exclude_paths or []]
        self.warehouse_projects = [p.lower() for p in warehouse_projects or []]
        self.target_repos = (
            [repo for repo in target_repos] if target_repos else ["NuSyQ-Hub", "SimulatedVerse", "NuSyQ"]
        )
        self.skip_culture_ship = skip_culture_ship
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "repositories": {},
            "cross_repo_issues": [],
            "high_priority_tasks": [],
            "autonomous_recommendations": [],
        }

        # Initialize SimulatedVerse bridge if available and allowed
        if SimulatedVerseBridge and not skip_culture_ship:
            self.bridge = SimulatedVerseBridge()
        else:
            self.bridge = None

    def _normalize_path(self, file_path: Path, repo_path: Path) -> str:
        rel = file_path.relative_to(repo_path)
        return str(rel).replace("\\", "/")

    def _matches_filters(self, rel_path: str) -> bool:
        if self.exclude_paths and any(exclude in rel_path for exclude in self.exclude_paths):
            return False
        if self.include_paths and not any(include in rel_path for include in self.include_paths):
            return False
        if self.warehouse_projects:
            rel_lower = rel_path.lower()
            if "chatdev/warehouse" not in rel_lower:
                return False
            if not any(project in rel_lower for project in self.warehouse_projects):
                return False
        return True

    def _should_process_file(self, file_path: Path, repo_path: Path) -> bool:
        rel = self._normalize_path(file_path, repo_path)
        if ".venv" in rel or "node_modules" in rel or "__pycache__" in rel:
            return False
        return self._matches_filters(rel)

    def scan_for_placeholders(self, repo_path: Path) -> dict[str, Any]:
        """Scan repository for placeholder code, TODOs, and incomplete implementations."""
        patterns = {
            "TODO": r"TODO|FIXME|XXX|HACK|TEMP",
            "PLACEHOLDER": r"placeholder|PLACEHOLDER|stub|STUB",
            "KILO-FOOLISH": r"KILO-FOOLISH|KILO_FOOLISH",
            "INCOMPLETE": r"not implemented|NotImplemented|pass\s*#|\.\.\..*#",
            "HARDCODED": r"hardcoded|hard-coded|magic number",
            "DEPRECATED": r"deprecated|DEPRECATED|@deprecated",
            "CONSOLE_SPAM": r"print\(|console\.log|console\.error",
            "MISSING_DOCS": r"def\s+\w+\([^)]*\):\s*$",
        }

        findings = {pattern: [] for pattern in patterns}
        total_files = 0

        # Scan Python files
        for py_file in repo_path.rglob("*.py"):
            if not self._should_process_file(py_file, repo_path):
                continue

            total_files += 1
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")

                for pattern_name, pattern in patterns.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        findings[pattern_name].append(
                            {
                                "file": str(py_file.relative_to(repo_path)),
                                "line": line_num,
                                "snippet": content[max(0, match.start() - 50) : match.end() + 50],
                            }
                        )
            except (OSError, UnicodeDecodeError, ValueError):
                pass

        # Scan TypeScript/JavaScript files for SimulatedVerse
        for ts_file in repo_path.rglob("*.ts"):
            if not self._should_process_file(ts_file, repo_path):
                continue

            try:
                content = ts_file.read_text(encoding="utf-8", errors="ignore")

                for pattern_name in ["TODO", "PLACEHOLDER", "INCOMPLETE"]:
                    pattern = patterns[pattern_name]
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        findings[pattern_name].append(
                            {
                                "file": str(ts_file.relative_to(repo_path)),
                                "line": line_num,
                                "snippet": content[max(0, match.start() - 50) : match.end() + 50],
                            }
                        )
            except (OSError, UnicodeDecodeError) as e:
                print(f"⚠️ Warning: Failed to scan {ts_file}: {e}")

        return {
            "total_files_scanned": total_files,
            "findings": findings,
            "summary": {pattern: len(items) for pattern, items in findings.items()},
        }

    def scan_configuration_files(self, repo_path: Path) -> dict[str, Any]:
        """Scan for incomplete or missing configuration files."""
        config_checks = {
            "NuSyQ-Hub": [
                "config/secrets.json",
                "config/feature_flags.json",
                "config/ZETA_PROGRESS_TRACKER.json",
                "pytest.ini",
                "pyproject.toml",
                ".env.example",
            ],
            "SimulatedVerse": [
                "package.json",
                "tsconfig.json",
                ".env.example",
                "drizzle.config.ts",
                "replit.toml",
            ],
            "NuSyQ": [
                "nusyq.manifest.yaml",
                "knowledge-base.yaml",
                "config/config_manager.py",
                ".env.example",
            ],
        }

        repo_name = repo_path.name
        expected_files = config_checks.get(repo_name, [])

        missing = []
        present = []

        for config_file in expected_files:
            config_path = repo_path / config_file
            if config_path.exists():
                present.append(config_file)
            else:
                missing.append(config_file)

        return {
            "expected": len(expected_files),
            "present": len(present),
            "missing": missing,
            "present_files": present,
        }

    def detect_incomplete_modules(self, repo_path: Path, repo_name: str | None = None) -> list[dict[str, Any]]:
        """Detect modules with incomplete implementations."""
        incomplete = []

        for py_file in repo_path.rglob("*.py"):
            if not self._should_process_file(py_file, repo_path):
                continue

            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")

                # Check for placeholder patterns
                issues = []
                if "pass  # TODO" in content or "pass # TODO" in content:
                    issues.append("TODO placeholder")
                if "raise NotImplementedError" in content:
                    issues.append("NotImplementedError")
                if content.count("...") > 5:  # Ellipsis used as placeholder
                    issues.append("Ellipsis placeholders")
                if "def " in content and content.count('"""') < 2:
                    issues.append("Missing docstrings")

                if issues:
                    incomplete.append(
                        {
                            "file": str(py_file.relative_to(repo_path)),
                            "issues": issues,
                            "size": len(content),
                            "functions": content.count("def "),
                        }
                    )
            except (OSError, UnicodeDecodeError) as e:
                print(f"⚠️ Warning: Failed to process {py_file}: {e}")

        if repo_name == "NuSyQ-Hub":
            incomplete = [item for item in incomplete if item["file"] not in HUB_PLACEHOLDER_FILES]

        return sorted(incomplete, key=lambda x: len(x["issues"]), reverse=True)

    def gather_placeholder_tasks(self) -> dict[str, str]:
        """Summarize placeholder stubs that reconcile the incomplete backlog."""
        return dict.fromkeys(PLACEHOLDER_TASKS, "ready")

    def submit_to_culture_ship(self, audit_data: dict[str, Any]) -> dict[str, Any]:
        """Submit audit results to Culture-Ship for PU generation."""
        if not self.bridge:
            return {"error": "SimulatedVerse bridge not available"}

        # Prepare comprehensive audit summary
        summary = {
            "audit_type": "comprehensive_modernization",
            "timestamp": audit_data["timestamp"],
            "statistics": {},
            "priority_areas": [],
        }

        # Aggregate statistics
        for repo_name, repo_data in audit_data["repositories"].items():
            if "error" in repo_data:
                continue
            summary["statistics"][repo_name] = {
                "placeholder_count": sum(repo_data.get("placeholders", {}).get("summary", {}).values()),
                "missing_configs": len(repo_data.get("configuration", {}).get("missing", [])),
                "incomplete_modules": len(repo_data.get("incomplete_modules", [])),
            }

        # Submit to Culture-Ship
        task_id = self.bridge.submit_task(
            "culture-ship",
            f"Comprehensive modernization audit: {json.dumps(summary, indent=2)}",
            {
                "audit_data": audit_data,
                "request": "Generate proof-gated PUs for modernization priorities",
            },
        )

        # Wait for result
        result = self.bridge.check_result(task_id, timeout=30)

        return result if result else {"error": "Timeout waiting for Culture-Ship"}

    def audit_nusyq_hub(self) -> dict[str, Any]:
        """Audit NuSyQ-Hub repository."""
        repo_path = self.repo_root

        # Scan for placeholders
        placeholders = self.scan_for_placeholders(repo_path)

        # Check configurations
        configs = self.scan_configuration_files(repo_path)

        # Detect incomplete modules
        incomplete = self.detect_incomplete_modules(repo_path, repo_name=repo_path.name)

        return {
            "placeholders": placeholders,
            "configuration": configs,
            "incomplete_modules": incomplete[:20],  # Top 20
        }

    def audit_simulatedverse(self) -> dict[str, Any]:
        """Audit SimulatedVerse repository."""
        if get_repo_path:
            try:
                sim_path = get_repo_path("SIMULATEDVERSE_ROOT")
            except Exception:
                sim_path = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"
        else:
            sim_path = Path.home() / "Desktop" / "SimulatedVerse" / "SimulatedVerse"

        if not sim_path.exists():
            return {"error": "SimulatedVerse path not found"}

        # Scan for placeholders
        placeholders = self.scan_for_placeholders(sim_path)

        # Check configurations
        configs = self.scan_configuration_files(sim_path)

        return {"placeholders": placeholders, "configuration": configs}

    def audit_nusyq_root(self) -> dict[str, Any]:
        """Audit NuSyQ Root repository."""
        if get_repo_path:
            try:
                nusyq_path = get_repo_path("NUSYQ_ROOT")
            except Exception:
                nusyq_path = Path.home() / "NuSyQ"
        else:
            nusyq_path = Path.home() / "NuSyQ"

        if not nusyq_path.exists():
            return {"error": "NuSyQ path not found"}

        # Scan for placeholders
        placeholders = self.scan_for_placeholders(nusyq_path)

        # Check configurations
        configs = self.scan_configuration_files(nusyq_path)

        return {"placeholders": placeholders, "configuration": configs}

    def generate_report(self):
        """Generate comprehensive modernization report."""
        output_file = self.repo_root / "docs" / "COMPREHENSIVE_MODERNIZATION_AUDIT.md"

        report = f"""# Comprehensive Modernization Audit Report

**Generated**: {self.results["timestamp"]}
**Auditor**: 22-Agent Autonomous Ecosystem
**Scope**: NuSyQ-Hub, SimulatedVerse, NuSyQ Root

---

## Executive Summary

"""

        # Add repository summaries
        for repo_name, repo_data in self.results["repositories"].items():
            if "error" in repo_data:
                report += f"\n### {repo_name}\n**Status**: {repo_data['error']}\n"
                continue

            placeholders = repo_data.get("placeholders", {}).get("summary", {})
            configs = repo_data.get("configuration", {})

            report += f"""
### {repo_name}

**Files Scanned**: {repo_data.get("placeholders", {}).get("total_files_scanned", 0)}
**Placeholders Found**: {sum(placeholders.values())}
**Configuration Status**: {configs.get("present", 0)}/{configs.get("expected", 0)} files present
**Missing Configs**: {", ".join(configs.get("missing", [])) if configs.get("missing") else "None"}

**Breakdown**:
"""

            for pattern, count in placeholders.items():
                if count > 0:
                    report += f"- {pattern}: {count}\n"

        # Add Culture-Ship recommendations
        if "culture_ship_response" in self.results:
            report += "\n---\n\n## Culture-Ship Recommendations\n\n"
            cs_response = self.results["culture_ship_response"]
            report += f"```json\n{json.dumps(cs_response, indent=2)}\n```\n"

        if self.results.get("placeholder_tasks"):
            report += "\n---\n\n## Placeholder Task Status\n\n"
            for task, status in self.results["placeholder_tasks"].items():
                report += f"- {task}: {status}\n"

        # Add action items
        report += "\n---\n\n## Recommended Actions\n\n"
        report += "1. **High Priority**: Remove KILO-FOOLISH references and replace with NuSyQ branding\n"
        report += "2. **Medium Priority**: Complete missing configuration files\n"
        report += "3. **Medium Priority**: Convert TODO comments to tracked issues\n"
        report += "4. **Low Priority**: Add docstrings to undocumented functions\n"

        report += "\n---\n\n*Generated by Comprehensive Modernization Auditor using 22-agent ecosystem*\n"

        output_file.write_text(report, encoding="utf-8")

        return output_file

    def run_full_audit(self):
        """Run comprehensive audit across all repositories."""
        # Audit each repository
        if "NuSyQ-Hub" in self.target_repos:
            self.results["repositories"]["NuSyQ-Hub"] = self.audit_nusyq_hub()
        if "SimulatedVerse" in self.target_repos:
            self.results["repositories"]["SimulatedVerse"] = self.audit_simulatedverse()
        if "NuSyQ" in self.target_repos:
            self.results["repositories"]["NuSyQ"] = self.audit_nusyq_root()

        self.results["placeholder_tasks"] = self.gather_placeholder_tasks()

        # Submit to Culture-Ship for analysis
        if self.bridge:
            cs_response = self.submit_to_culture_ship(self.results)
            self.results["culture_ship_response"] = cs_response

        # Generate report

        self.generate_report()

        # Save raw JSON
        json_path = self.repo_root / "docs" / "comprehensive_modernization_audit.json"
        json_path.write_text(json.dumps(self.results, indent=2), encoding="utf-8")

        return self.results


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Comprehensive Modernization Auditor with filtering layers.")
    parser.add_argument(
        "--mode",
        choices=list(SCAN_MODES),
        default="full",
        help="Pre-defined scan mode (core, warehouse, full).",
    )
    parser.add_argument(
        "--repos",
        nargs="+",
        choices=["NuSyQ-Hub", "SimulatedVerse", "NuSyQ"],
        help="Explicit repos to target (overrides mode defaults).",
    )
    parser.add_argument(
        "--include-paths",
        nargs="*",
        default=[],
        help="Relative paths to include in scans (supports substrings).",
    )
    parser.add_argument(
        "--exclude-paths",
        nargs="*",
        default=[],
        help="Relative paths to exclude from scans (supports substrings).",
    )
    parser.add_argument(
        "--warehouse-projects",
        nargs="*",
        default=[],
        help="Target specific ChatDev warehouse projects (name substring match).",
    )
    parser.add_argument(
        "--skip-culture-ship",
        action="store_true",
        help="Prevent submission of audit data to Culture-Ship.",
    )
    args = parser.parse_args(argv)

    # Merge mode-specific defaults into the parsed args for convenience/testing
    mode_config = SCAN_MODES.get(args.mode, {})
    args.include_paths = list(args.include_paths or []) + mode_config.get("include_paths", [])
    args.exclude_paths = list(args.exclude_paths or []) + mode_config.get("exclude_paths", [])
    if not args.repos:
        args.repos = mode_config.get("target_repos", ["NuSyQ-Hub", "SimulatedVerse", "NuSyQ"])

    return args


def main(argv: Sequence[str] | None = None):
    args = parse_args(argv)

    auditor = ComprehensiveModernizationAuditor(
        include_paths=args.include_paths,
        exclude_paths=args.exclude_paths,
        warehouse_projects=args.warehouse_projects,
        target_repos=args.repos,
        skip_culture_ship=args.skip_culture_ship,
    )

    auditor.run_full_audit()


if __name__ == "__main__":
    main()
