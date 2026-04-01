"""Documentation Sync Checker.

Compares README claims with actual codebase implementation.
Identifies documented features that don't exist and features that aren't documented.

OmniTag: {'purpose': 'validation', 'type': 'documentation_quality', 'evolution_stage': 'v1.0'}
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DocSyncChecker:
    """Validates documentation accuracy against codebase."""

    def __init__(
        self,
        readme_path: Path | None = None,
        src_path: Path | None = None,
    ) -> None:
        """Initialize DocSyncChecker with readme_path, src_path."""
        self.readme_path = readme_path or Path("README.md")
        self.src_path = src_path or Path("src")
        self.readme_claims: list[dict[str, Any]] = []
        self.codebase_features: list[dict[str, Any]] = []
        self.discrepancies: list[dict[str, Any]] = []
        self.matches: list[dict[str, Any]] = []

    def extract_readme_claims(self) -> None:
        """Extract feature claims from README."""
        if not self.readme_path.exists():
            logger.warning(f"⚠️  README not found: {self.readme_path}")
            return

        with open(self.readme_path, encoding="utf-8") as f:
            content = f.read()

        # Extract module/file references
        module_pattern = r"`([a-z_]+\.py)`"
        modules = re.findall(module_pattern, content)

        for module in modules:
            self.readme_claims.append(
                {
                    "type": "module",
                    "name": module,
                    "source": "README.md",
                }
            )

        # Extract feature descriptions (lines starting with - or *)
        feature_pattern = r"^[\s]*[-*]\s+(.+)$"
        features = re.findall(feature_pattern, content, re.MULTILINE)

        for feature in features:
            # Extract code references from feature descriptions
            code_refs = re.findall(r"`([^`]+)`", feature)
            for ref in code_refs:
                if "." in ref or "_" in ref:  # Likely a module/function name
                    self.readme_claims.append(
                        {
                            "type": "feature",
                            "name": ref,
                            "description": feature[:100],
                            "source": "README.md",
                        }
                    )

        logger.info(f"✅ Extracted {len(self.readme_claims)} claims from README")

    def scan_codebase_features(self) -> None:
        """Scan codebase for actual features."""
        if not self.src_path.exists():
            logger.warning(f"⚠️  Source path not found: {self.src_path}")
            return

        python_files = list(self.src_path.rglob("*.py"))

        for file_path in python_files:
            # Record module
            relative_path = file_path.relative_to(self.src_path.parent)
            self.codebase_features.append(
                {
                    "type": "module",
                    "name": file_path.name,
                    "path": str(relative_path),
                    "source": "codebase",
                }
            )

            # Extract classes and functions
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Extract class definitions
                class_pattern = r"^class\s+(\w+)"
                classes = re.findall(class_pattern, content, re.MULTILINE)
                for class_name in classes:
                    self.codebase_features.append(
                        {
                            "type": "class",
                            "name": class_name,
                            "path": str(relative_path),
                            "source": "codebase",
                        }
                    )

                # Extract function definitions
                function_pattern = r"^def\s+(\w+)"
                functions = re.findall(function_pattern, content, re.MULTILINE)
                for func_name in functions:
                    self.codebase_features.append(
                        {
                            "type": "function",
                            "name": func_name,
                            "path": str(relative_path),
                            "source": "codebase",
                        }
                    )

            except (OSError, ValueError) as e:
                logger.error(f"⚠️  Error scanning {file_path}: {e}")

        logger.info(
            f"✅ Scanned {len(python_files)} files, found {len(self.codebase_features)} features"
        )

    def compare_claims_with_reality(self) -> None:
        """Compare README claims with actual codebase."""
        logger.info("\n🔍 Comparing documentation with codebase...")

        # Create lookup sets for fast comparison
        codebase_modules = {f["name"] for f in self.codebase_features if f["type"] == "module"}
        codebase_classes = {f["name"] for f in self.codebase_features if f["type"] == "class"}
        codebase_functions = {f["name"] for f in self.codebase_features if f["type"] == "function"}

        # Check each README claim
        for claim in self.readme_claims:
            name = claim["name"]
            claim_type = claim["type"]

            found = False

            # Check modules
            if name in codebase_modules:
                found = True
                self.matches.append(
                    {
                        "type": "documented_and_exists",
                        "name": name,
                        "category": "module",
                    }
                )

            # Check classes/functions
            if any(name in feature_name for feature_name in codebase_classes | codebase_functions):
                found = True
                self.matches.append(
                    {
                        "type": "documented_and_exists",
                        "name": name,
                        "category": claim_type,
                    }
                )

            if not found:
                self.discrepancies.append(
                    {
                        "type": "documented_but_missing",
                        "name": name,
                        "description": claim.get("description", ""),
                        "severity": "warning",
                    }
                )

        # Find undocumented features
        readme_claim_names = {claim["name"].lower() for claim in self.readme_claims}

        for feature in self.codebase_features:
            name = feature["name"]

            # Skip private/internal features
            if name.startswith("_"):
                continue

            # Skip test files
            if "test" in feature.get("path", "").lower():
                continue

            # Check if documented
            if (
                not any(name.lower() in claim_name for claim_name in readme_claim_names)
                and feature["type"] == "class"
            ):
                # Major features (classes with significant code)
                self.discrepancies.append(
                    {
                        "type": "exists_but_undocumented",
                        "name": name,
                        "path": feature["path"],
                        "category": "class",
                        "severity": "info",
                    }
                )

        logger.info("✅ Comparison complete!")
        logger.info(f"   Matches: {len(self.matches)}")
        logger.info(f"   Discrepancies: {len(self.discrepancies)}")

    def generate_report(self) -> str:
        """Generate comprehensive discrepancy report."""
        report_lines = [
            "=" * 80,
            "📚 DOCUMENTATION SYNC REPORT",
            "=" * 80,
            f"README: {self.readme_path}",
            f"Source: {self.src_path}",
            "",
            "SUMMARY",
            "-" * 80,
            f"✓ README Claims: {len(self.readme_claims)}",
            f"✓ Codebase Features: {len(self.codebase_features)}",
            f"✓ Verified Matches: {len(self.matches)}",
            f"✗ Discrepancies: {len(self.discrepancies)}",
            "",
        ]

        # Documented but missing
        documented_missing = [
            d for d in self.discrepancies if d["type"] == "documented_but_missing"
        ]
        if documented_missing:
            report_lines.extend(
                [
                    "⚠️  DOCUMENTED BUT MISSING IN CODEBASE",
                    "-" * 80,
                ]
            )
            for disc in documented_missing[:20]:  # Limit to 20
                report_lines.append(f"  • {disc['name']}")
                if disc.get("description"):
                    report_lines.append(f"    Description: {disc['description']}")
            if len(documented_missing) > 20:
                report_lines.append(f"    ... and {len(documented_missing) - 20} more")
            report_lines.append("")

        # Exists but undocumented
        undocumented = [d for d in self.discrepancies if d["type"] == "exists_but_undocumented"]
        if undocumented:
            report_lines.extend(
                [
                    "💡 EXISTS IN CODEBASE BUT UNDOCUMENTED",
                    "-" * 80,
                ]
            )
            for disc in undocumented[:20]:  # Limit to 20
                report_lines.append(f"  • {disc['name']} ({disc['category']})")
                report_lines.append(f"    Path: {disc['path']}")
            if len(undocumented) > 20:
                report_lines.append(f"    ... and {len(undocumented) - 20} more")
            report_lines.append("")

        # Health assessment
        report_lines.extend(["DOCUMENTATION HEALTH", "-" * 80])

        if not self.discrepancies:
            report_lines.append("✅ EXCELLENT - Perfect sync!")
        elif len(self.discrepancies) < 10:
            report_lines.append(f"✓ GOOD - {len(self.discrepancies)} minor discrepancies")
        elif len(self.discrepancies) < 30:
            report_lines.append(f"⚠ NEEDS ATTENTION - {len(self.discrepancies)} discrepancies")
        else:
            report_lines.append(f"✗ CRITICAL - {len(self.discrepancies)} major discrepancies")

        # Accuracy metrics
        if self.readme_claims:
            accuracy = (len(self.matches) / len(self.readme_claims)) * 100
            report_lines.append(f"Documentation Accuracy: {accuracy:.1f}%")

        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def save_report(self, output_path: Path | None = None) -> None:
        """Save report to file."""
        if output_path is None:
            output_path = Path("data/documentation_sync_report.txt")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = self.generate_report()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"📄 Report saved to {output_path}")

    def run(self) -> None:
        """Execute full documentation sync check."""
        logger.info("=" * 80)
        logger.info("📚 DOCUMENTATION SYNC CHECKER")
        logger.info("=" * 80)

        self.extract_readme_claims()
        self.scan_codebase_features()
        self.compare_claims_with_reality()

        logger.info("\n" + self.generate_report())

        logger.info("\n" + "=" * 80)


def main() -> None:
    """CLI entry point."""
    checker = DocSyncChecker()
    checker.run()


if __name__ == "__main__":
    main()
