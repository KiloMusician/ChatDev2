#!/usr/bin/env python3
"""🔍 KILO-FOOLISH Systematic SRC Directory Audit.

PRESERVATION FIX: 2025-08-03 - Comprehensive file analysis and consolidation detector.

Following ZETA Progress methodology and File Preservation Mandate.
Uses our existing documentation and infrastructure to guide systematic review.
"""

import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any


class KILOSystematicAuditor:
    """Systematic auditor following KILO-FOOLISH principles."""

    def __init__(self, repo_root=".") -> None:
        """Initialize KILOSystematicAuditor with repo_root."""
        self.repo_root = Path(repo_root)
        self.src_root = self.repo_root / "src"

        # Results storage
        self.compilation_results: dict[str, list[Any]] = {"working": [], "broken": []}
        self.duplicate_candidates: list[Any] = []
        self.consolidation_opportunities: list[Any] = []
        self.directory_health: dict[str, Any] = {}

    def run_comprehensive_audit(self) -> None:
        """Run full systematic audit."""
        self.check_compilation_status()
        self.identify_duplicates()
        self.check_directory_health()
        self.identify_consolidation_opportunities()
        self.generate_report()

    def check_compilation_status(self) -> None:
        """Check compilation status of all Python files."""
        py_files = list(self.src_root.rglob("*.py"))
        len(py_files)

        for i, file_path in enumerate(py_files):
            if i % 30 == 0:
                pass

            try:
                result = subprocess.run(
                    ["python", "-m", "py_compile", str(file_path)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=3,
                )

                if result.returncode == 0:
                    self.compilation_results["working"].append(str(file_path))
                else:
                    error_info = {
                        "file": str(file_path),
                        "error": (
                            result.stderr.split("\n")[0] if result.stderr else "Unknown error"
                        ),
                    }
                    self.compilation_results["broken"].append(error_info)

            except Exception as e:
                error_info = {
                    "file": str(file_path),
                    "error": f"Exception: {e!s}",
                }
                self.compilation_results["broken"].append(error_info)

        working_count = len(self.compilation_results["working"])
        broken_count = len(self.compilation_results["broken"])
        (working_count / (working_count + broken_count)) * 100

        if broken_count > 0:
            for _error_info in self.compilation_results["broken"][:5]:
                pass

    def identify_duplicates(self) -> None:
        """Identify potential duplicate files by name similarity."""
        py_files = list(self.src_root.rglob("*.py"))
        file_names = defaultdict(list)

        # Group files by similar names
        for file_path in py_files:
            name = file_path.name
            file_names[name].append(str(file_path))

        # Find exact duplicates
        exact_duplicates = {name: paths for name, paths in file_names.items() if len(paths) > 1}

        if exact_duplicates:
            for name, paths in exact_duplicates.items():
                for _path in paths:
                    pass
                self.duplicate_candidates.append(
                    {
                        "name": name,
                        "paths": paths,
                        "type": "exact_duplicate",
                    }
                )
        else:
            pass

    def check_directory_health(self) -> None:
        """Check health status of each directory."""
        # Get all directories in src
        directories = set()
        for file_path in self.src_root.rglob("*.py"):
            directories.add(file_path.parent)

        for directory in sorted(directories):
            py_files = list(directory.glob("*.py"))
            working_files = [f for f in py_files if str(f) in self.compilation_results["working"]]
            broken_files = [
                f
                for f in py_files
                if any(str(f) == e["file"] for e in self.compilation_results["broken"])
            ]

            total_files = len(py_files)
            working_count = len(working_files)
            health_percentage = (working_count / total_files * 100) if total_files > 0 else 0

            rel_dir = directory.relative_to(self.repo_root)

            self.directory_health[str(rel_dir)] = {
                "total_files": total_files,
                "working_files": working_count,
                "broken_files": len(broken_files),
                "health_percentage": health_percentage,
            }

    def identify_consolidation_opportunities(self) -> None:
        """Identify consolidation opportunities based on existing documentation."""
        # Check for known consolidation patterns from our documentation
        consolidation_patterns = [
            (
                "ai_coordinator",
                ["src/core/ai_coordinator.py", "src/ai/ai_coordinator.py"],
            ),
            ("chatdev", ["integration", "orchestration"]),
            ("ollama", ["integration", "ai"]),
            ("quantum", ["quantum", "core"]),
        ]

        for pattern_name, _pattern_info in consolidation_patterns:
            # Find files matching pattern
            matching_files: list[Any] = []
            for file_path in self.src_root.rglob("*.py"):
                if pattern_name.lower() in file_path.name.lower():
                    matching_files.append(str(file_path))

            if len(matching_files) > 1:
                for _file_path in matching_files:
                    pass

                self.consolidation_opportunities.append(
                    {
                        "pattern": pattern_name,
                        "files": matching_files,
                        "action": "consolidation_candidate",
                    }
                )

    def generate_report(self) -> None:
        """Generate comprehensive audit report."""
        report = {
            "audit_timestamp": "2025-08-03",
            "audit_type": "systematic_src_review",
            "compilation_results": self.compilation_results,
            "duplicate_candidates": self.duplicate_candidates,
            "consolidation_opportunities": self.consolidation_opportunities,
            "directory_health": self.directory_health,
            "recommendations": self.generate_recommendations(),
        }

        # Save report
        report_file = self.repo_root / "SYSTEMATIC_SRC_AUDIT_REPORT.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Print summary

        total_files = len(self.compilation_results["working"]) + len(
            self.compilation_results["broken"]
        )
        working_files = len(self.compilation_results["working"])
        (working_files / total_files * 100) if total_files > 0 else 0

        unhealthy_dirs = sum(
            1 for h in self.directory_health.values() if h["health_percentage"] < 100
        )

        if len(self.compilation_results["broken"]) > 0:
            pass
        if len(self.duplicate_candidates) > 0:
            pass
        if len(self.consolidation_opportunities) > 0:
            pass
        if unhealthy_dirs > 0:
            pass

    def generate_recommendations(self) -> list[dict[str, Any]]:
        """Generate specific recommendations based on audit results."""
        recommendations: list[dict[str, Any]] = []
        # Broken files recommendations
        if len(self.compilation_results["broken"]) > 0:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "file_repair",
                    "action": "Apply surgical precision fixes to broken files",
                    "count": len(self.compilation_results["broken"]),
                    "method": "File Preservation Mandate methodology",
                }
            )

        # Duplicate files recommendations
        if len(self.duplicate_candidates) > 0:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "consolidation",
                    "action": "Consolidate duplicate files maintaining all functionality",
                    "count": len(self.duplicate_candidates),
                    "method": "Infrastructure-first consolidation approach",
                }
            )

        # Directory health recommendations
        unhealthy_dirs = [
            d for d, h in self.directory_health.items() if h["health_percentage"] < 100
        ]
        if unhealthy_dirs:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "directory_health",
                    "action": f"Improve health of {len(unhealthy_dirs)} directories",
                    "directories": unhealthy_dirs,
                    "method": "Directory-by-directory systematic approach",
                }
            )

        return recommendations


if __name__ == "__main__":
    auditor = KILOSystematicAuditor()
    auditor.run_comprehensive_audit()
