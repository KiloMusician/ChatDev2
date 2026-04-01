#!/usr/bin/env python3
"""NuSyQ-Hub Theater Audit.

Scans repository for "sophisticated theater" patterns:
- Placeholders (TODO, FIXME, XXX, HACK, etc.)
- Hardcoded errors and NotImplementedError
- Console/print spam
- Stub implementations
- Fake progress logging

Theater Score: 0.0 (perfect) to 1.0 (maximum theater)
Target: < 0.2 (acceptable)

Based on SimulatedVerse Culture Ship auditor
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


class TheaterAuditor:
    """Audit repository for theater patterns.

    Theater = code that looks operational but does nothing real
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.patterns = {
            "placeholder": [
                r"#\s*TODO",
                r"#\s*FIXME",
                r"#\s*XXX",
                r"#\s*HACK",
                r"#\s*KLUDGE",
                r"#\s*BUG",
                r"#\s*REFACTOR",
                r"#\s*OPTIMIZE",
                r"@todo",
                r"@fixme",
            ],
            "hardcoded_error": [
                r"raise\s+NotImplementedError",
                r"raise\s+NotImplemented\(",
                r'throw\s+new\s+Error\(\s*["\']Not\s+implemented',
                r'throw\s+new\s+Error\(\s*["\']TODO',
            ],
            "stub": [
                r"^\s*pass\s*#\s*stub",
                r"^\s*pass\s*#\s*placeholder",
                r"^\s*pass\s*#\s*TODO",
                r"return\s+None\s*#\s*stub",
            ],
            "console_spam": [
                r"console\.log\(",
                r"console\.debug\(",
                r'print\(\s*["\']DEBUG:',
                r'print\(\s*["\']TODO:',
            ],
            "fake_progress": [
                r'print\(\s*["\']✅',
                r'print\(\s*["\']COMPLETED',
                r'print\(\s*["\']SUCCESS',
                r'logger\.info\(\s*["\']✅',
            ],
        }

        self.exclude_patterns = [
            r"\.git/",
            r"node_modules/",
            r"__pycache__/",
            r"\.pyc$",
            r"\.md$",  # Documentation files are OK to have TODOs
            r"test_",  # Test files
            r"_test\.py$",
        ]

    def should_scan(self, file_path: Path) -> bool:
        """Check if file should be scanned."""
        path_str = str(file_path.relative_to(self.repo_root))

        # Exclude certain paths
        for pattern in self.exclude_patterns:
            if re.search(pattern, path_str):
                return False

        # Only scan source files
        return file_path.suffix in [".py", ".js", ".ts", ".jsx", ".tsx"]

    def scan_file(self, file_path: Path) -> dict[str, list[tuple[int, str]]]:
        """Scan single file for theater patterns.

        Returns dict of {pattern_type: [(line_num, line_text), ...]}
        """
        hits = defaultdict(list)

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    for category, patterns in self.patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                hits[category].append((line_num, line.strip()))
        except (OSError, UnicodeDecodeError):
            pass

        return dict(hits)

    def audit_repository(self) -> dict:
        """Audit entire repository for theater.

        Returns comprehensive theater report
        """
        all_hits = defaultdict(lambda: defaultdict(list))
        files_scanned = 0
        total_theater_hits = 0

        # Scan all source files
        for file_path in self.repo_root.rglob("*"):
            if not file_path.is_file():
                continue

            if not self.should_scan(file_path):
                continue

            files_scanned += 1
            file_hits = self.scan_file(file_path)

            if file_hits:
                relative_path = str(file_path.relative_to(self.repo_root))
                for category, hits in file_hits.items():
                    all_hits[category][relative_path] = hits
                    total_theater_hits += len(hits)

        # Calculate theater score
        # Score based on density: hits per file scanned
        if files_scanned > 0:
            theater_density = total_theater_hits / files_scanned
            # Normalize to 0.0-1.0 scale (assume >10 hits/file = max theater)
            theater_score = min(1.0, theater_density / 10.0)
        else:
            theater_score = 0.0

        # Create report
        report = {
            "timestamp": datetime.now().isoformat(),
            "repository": str(self.repo_root),
            "files_scanned": files_scanned,
            "total_theater_hits": total_theater_hits,
            "theater_score": round(theater_score, 3),
            "hits_by_category": {
                category: {
                    "count": sum(len(hits) for hits in files.values()),
                    "files": dict(files),
                }
                for category, files in all_hits.items()
            },
            "assessment": self._assess_score(theater_score),
            "recommendations": self._generate_recommendations(all_hits, theater_score),
        }

        # Display results
        self._display_report(report)

        return report

    def _assess_score(self, score: float) -> str:
        """Assess theater score."""
        if score < 0.1:
            return "EXCELLENT - Minimal theater"
        elif score < 0.2:
            return "GOOD - Acceptable theater levels"
        elif score < 0.5:
            return "WARNING - Significant theater detected"
        elif score < 0.8:
            return "CRITICAL - High theater levels"
        else:
            return "MAXIMUM THEATER - Immediate action required"

    def _generate_recommendations(self, hits: dict, score: float) -> list[str]:
        """Generate recommendations based on audit."""
        recommendations = []

        if score >= 0.2:
            recommendations.append("Reduce theater score to < 0.2")

        for category, files in hits.items():
            total = sum(len(file_hits) for file_hits in files.values())
            if total > 0:
                if category == "placeholder":
                    recommendations.append(f"Address {total} placeholder comments (TODO/FIXME/XXX)")
                elif category == "hardcoded_error":
                    recommendations.append(f"Implement {total} hardcoded error stubs")
                elif category == "stub":
                    recommendations.append(f"Complete {total} stub implementations")
                elif category == "console_spam":
                    recommendations.append(f"Clean up {total} console/debug statements")
                elif category == "fake_progress":
                    recommendations.append(f"Replace {total} fake progress indicators with real verification")

        if not recommendations:
            recommendations.append("✅ Repository is clean - maintain current standards")

        return recommendations

    def _display_report(self, report: dict):
        """Display theater audit report."""
        for _category, data in report["hits_by_category"].items():
            for _file_path, hits in list(data["files"].items())[:5]:  # Top 5 files
                for _line_num, _line in hits[:3]:  # Top 3 lines
                    pass

        for _i, _rec in enumerate(report["recommendations"], 1):
            pass

        # Save report
        report_file = self.repo_root / "data" / "theater_audit.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)


def main():
    """Run theater audit on NuSyQ-Hub."""
    repo_root = Path.cwd()

    auditor = TheaterAuditor(repo_root)
    report = auditor.audit_repository()

    # Exit with error code if theater score too high
    if report["theater_score"] >= 0.2:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
