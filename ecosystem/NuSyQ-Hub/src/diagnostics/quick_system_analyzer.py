#!/usr/bin/env python3
"""🎯 KILO-FOOLISH Quick System Analysis & Enhancement Tracker.

Rapid assessment of all src/ files with immediate actionable insights.
"""

import ast
import json
import logging
import warnings  # Suppress unwanted syntax warnings
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=SyntaxWarning)


class QuickSystemAnalyzer:
    """Quick analysis for immediate insights and action items."""

    def __init__(self) -> None:
        """Initialize QuickSystemAnalyzer."""
        self.repo_root = Path.cwd()
        self.results: dict[str, Any] = {
            "working_files": [],
            "broken_files": [],
            "launch_pad_files": [],
            "enhancement_candidates": [],
            "consolidation_opportunities": [],
            "priority_fixes": [],
            "integration_gaps": [],
        }

    def quick_scan(self) -> None:
        """Rapid scan of all Python files in src/."""
        src_dir = self.repo_root / "src"
        if not src_dir.exists():
            return

        # Scan all Python files
        py_files = list(src_dir.rglob("*.py"))

        for py_file in py_files:
            self._analyze_file_quick(py_file)

        self._generate_quick_report()

    def _analyze_file_quick(self, file_path: Path) -> None:
        """Quick analysis of a single file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Basic checks
            relative_path = file_path.relative_to(self.repo_root)

            # Check if it's a skeleton/launch pad
            is_launch_pad = self._is_launch_pad(content)

            # Check if it can be parsed
            try:
                ast.parse(content)
                can_parse = True
            except SyntaxError:
                can_parse = False

            # Quick import test
            import_issues = self._quick_import_test(content)

            # Check for KILO-FOOLISH integration patterns
            integration_level = self._check_integration_patterns(content)

            # Categorize the file
            category = self._categorize_file(
                file_path, content, can_parse, import_issues, integration_level
            )

            file_info = {
                "path": str(relative_path),
                "category": category,
                "can_parse": can_parse,
                "import_issues": import_issues,
                "integration_level": integration_level,
                "is_launch_pad": is_launch_pad,
                "size": len(content),
                "lines": len(content.split("\n")),
            }

            # Route to appropriate category
            if category == "working":
                self.results["working_files"].append(file_info)
            elif category == "broken":
                self.results["broken_files"].append(file_info)
            elif category == "launch_pad":
                self.results["launch_pad_files"].append(file_info)
            elif category == "enhancement_candidate":
                self.results["enhancement_candidates"].append(file_info)

        except Exception as e:
            self.results["broken_files"].append(
                {
                    "path": str(file_path.relative_to(self.repo_root)),
                    "error": str(e),
                    "category": "broken",
                }
            )

    def _is_launch_pad(self, content: str) -> bool:
        """Check if file is a launch pad for future development.

        Returns:
            True if file contains placeholder patterns indicating incomplete work
        """
        # Patterns indicating incomplete or template code (detection only)
        indicators = [
            "TODO",
            "TODO",
            "PLACEHOLDER",
            "NotImplementedError",
            "pass  # Placeholder",
            "# Future",
            "skeleton",
            "stub",
        ]
        return any(indicator in content for indicator in indicators)

    def _quick_import_test(self, content: str) -> list[str]:
        """Quick check for obvious import issues."""
        issues: list[Any] = []
        lines = content.split("\n")

        for i, line in enumerate(lines[:50]):  # Check first 50 lines
            normalized = line.strip()
            if normalized.startswith(("import ", "from ")):
                # Check for obvious problems
                if normalized.startswith(
                    "from LOGGING.modular_logging_system import"
                ) or normalized.startswith("import LOGGING.modular_logging_system"):
                    issues.append(f"Line {i + 1}: Old logging path")
                elif normalized.startswith("from LOGGING"):
                    issues.append(f"Line {i + 1}: Old LOGGING path")
                elif normalized.startswith(
                    "from src.LOGGING.infrastructure.modular_logging_system import"
                ):
                    issues.append(f"Line {i + 1}: Legacy compatibility logging path")
                elif "from ..." in normalized and normalized.count(".") > 3:
                    issues.append(f"Line {i + 1}: Complex relative import")

        return issues

    def _check_integration_patterns(self, content: str) -> str:
        """Check for KILO-FOOLISH integration patterns."""
        patterns = {
            "high": [
                "omnitag",
                "megatag",
                "quest_engine",
                "ai_coordinator",
                "consciousness",
            ],
            "medium": ["logging", "workflow", "copilot", "ollama"],
            "low": ["import os", "import sys", "from pathlib"],
        }

        content_lower = content.lower()

        if any(pattern in content_lower for pattern in patterns["high"]):
            return "high"
        if any(pattern in content_lower for pattern in patterns["medium"]):
            return "medium"
        return "low"

    def _categorize_file(
        self,
        _file_path: Path,
        content: str,
        can_parse: bool,
        import_issues: list[str],
        integration_level: str,
    ) -> str:
        """Categorize file for action planning."""
        # Broken files
        if not can_parse or len(import_issues) > 3:
            return "broken"

        # Launch pad detection
        if self._is_launch_pad(content):
            return "launch_pad"

        # Working files with good integration
        if can_parse and len(import_issues) == 0 and integration_level in ["high", "medium"]:
            return "working"

        # Files that could be enhanced
        if can_parse and (len(import_issues) <= 2 or integration_level == "low"):
            return "enhancement_candidate"

        return "working"

    def _generate_quick_report(self) -> None:
        """Generate quick actionable report."""
        # Summary stats
        total_files = sum(len(files) for files in self.results.values() if isinstance(files, list))
        logger.info(f"📊 Total files scanned: {total_files}")
        logger.info(f"   ✅ Working: {len(self.results['working_files'])}")
        logger.info(f"   🚀 Launch pads: {len(self.results['launch_pad_files'])}")
        logger.info(f"   🔧 Enhancement candidates: {len(self.results['enhancement_candidates'])}")
        logger.error(f"   ❌ Broken: {len(self.results['broken_files'])}")

        # Priority actions
        if self.results["broken_files"]:
            logger.warning(f"\n⚠️  Top {min(5, len(self.results['broken_files']))} broken files:")
            for file_info in self.results["broken_files"][:5]:  # Show top 5
                issues = file_info.get("import_issues", [])
                issue_str = f" - {issues[0]}" if issues else ""
                logger.info(f"   {file_info['path']}{issue_str}")

        if self.results["launch_pad_files"]:
            logger.info(f"\n🚀 Launch pad files ({len(self.results['launch_pad_files'])}):")
            for file_info in self.results["launch_pad_files"][:5]:
                logger.info(f"   {file_info['path']}")

        if self.results["enhancement_candidates"]:
            logger.info(
                f"\n💡 Enhancement candidates ({len(self.results['enhancement_candidates'])}):"
            )
            for file_info in self.results["enhancement_candidates"][:5]:
                level = file_info["integration_level"]
                logger.info(f"   {file_info['path']} (integration: {level})")

        # Working files by category
        working_by_dir: dict[str, Any] = {}
        for file_info in self.results["working_files"]:
            dir_name = (
                Path(file_info["path"]).parts[1]
                if len(Path(file_info["path"]).parts) > 1
                else "src"
            )
            working_by_dir[dir_name] = working_by_dir.get(dir_name, 0) + 1

        if working_by_dir:
            logger.info("\n📁 Working files by directory:")
            for dir_name, count in sorted(working_by_dir.items()):
                logger.info(f"   {dir_name}: {count}")

        # Integration analysis
        integration_stats = {"high": 0, "medium": 0, "low": 0}
        for category in ["working_files", "enhancement_candidates"]:
            for file_info in self.results[category]:
                level = file_info.get("integration_level", "low")
                integration_stats[level] += 1

        logger.info("\n🔗 Integration levels:")
        for level in ["high", "medium", "low"]:
            logger.info(f"   {level}: {integration_stats[level]}")

        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"quick_system_analysis_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info(f"\n📄 Detailed report saved: {report_file}")


if __name__ == "__main__":
    analyzer = QuickSystemAnalyzer()
    analyzer.quick_scan()
