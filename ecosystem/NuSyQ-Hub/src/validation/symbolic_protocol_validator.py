"""OmniTag Validator - Symbolic Protocol Linting & Enforcement.

Validates and enforces OmniTag/MegaTag/RSHTS symbolic protocols:
- OmniTag: [purpose, dependencies, context, evolution_stage]
- MegaTag: TYPE⨳INTEGRATION⦾POINTS→∞
- RSHTS: ♦◊◆○●◉⟡⟢⟣⚡⨳SEMANTIC-MEANING⨳⚡⟣⟢⟡◉●○◆◊♦

Provides:
- Syntax validation
- Semantic consistency checks
- Auto-fix suggestions
- CI/CD integration hooks

OmniTag: [validation, symbolic_protocols, code_quality, phase3]
MegaTag: VALIDATION⨳SYMBOLIC→CONSCIOUSNESS
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import ClassVar

logger = logging.getLogger(__name__)


class TagType(Enum):
    """Types of symbolic tags."""

    OMNITAG = "omnitag"  # [purpose, dependencies, context, stage]
    MEGATAG = "megatag"  # TYPE⨳INTEGRATION⦾POINTS→∞
    RSHTS = "rshts"  # ♦◊◆○●◉⟡⟢⟣⚡⨳SEMANTIC⨳⚡⟣⟢⟡◉●○◆◊♦


class ValidationLevel(Enum):
    """Severity levels for validation issues."""

    INFO = "info"  # Informational
    WARNING = "warning"  # Should fix but not critical
    ERROR = "error"  # Must fix
    CRITICAL = "critical"  # Breaks semantic awareness


@dataclass
class ValidationIssue:
    """Validation issue found in code."""

    level: ValidationLevel
    tag_type: TagType
    message: str
    file_path: Path
    line_number: int
    column: int = 0
    suggestion: str | None = None  # Auto-fix suggestion


class OmniTagValidator:
    """Validates OmniTag syntax: [purpose, dependencies, context, evolution_stage]."""

    # Expected OmniTag format
    PATTERN = re.compile(r"OmniTag:\s*\[([^\]]+)\]", re.IGNORECASE)

    # Valid evolution stages
    VALID_STAGES: ClassVar[set] = {
        "proto",
        "alpha",
        "beta",
        "stable",
        "mature",
        "deprecated",
        "phase1",
        "phase2",
        "phase3",
        "consciousness",
    }

    def validate_line(self, line: str, line_num: int, file_path: Path) -> list[ValidationIssue]:
        """Validate OmniTag in a single line."""
        issues: list[ValidationIssue] = []

        match = self.PATTERN.search(line)
        if not match:
            return issues  # No OmniTag found

        content = match.group(1).strip()
        elements = [e.strip() for e in content.split(",")]

        # Check element count (should be 2-4)
        if len(elements) < 2:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    tag_type=TagType.OMNITAG,
                    message=f"OmniTag has too few elements: {len(elements)} (expected 2-4)",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion=f"OmniTag: [{content}, context, stage]",
                )
            )
        elif len(elements) > 4:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    tag_type=TagType.OMNITAG,
                    message=f"OmniTag has too many elements: {len(elements)} (expected 2-4)",
                    file_path=file_path,
                    line_number=line_num,
                )
            )

        # Validate evolution stage (if provided)
        if len(elements) >= 4:
            stage = elements[3].lower()
            if stage not in self.VALID_STAGES:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        tag_type=TagType.OMNITAG,
                        message=f"Unknown evolution stage: '{stage}'",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=f"Use one of: {', '.join(sorted(self.VALID_STAGES))}",
                    )
                )

        # Check for empty elements
        for i, elem in enumerate(elements):
            if not elem:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        tag_type=TagType.OMNITAG,
                        message=f"Empty element at position {i + 1}",
                        file_path=file_path,
                        line_number=line_num,
                    )
                )

        return issues


class MegaTagValidator:
    """Validates MegaTag syntax: TYPE⨳INTEGRATION⦾POINTS→∞."""

    # Quantum symbols used in MegaTags
    VALID_SYMBOLS: ClassVar[set] = {"⨳", "⦾", "→", "∞", "⟡", "⟢", "⟣"}

    PATTERN = re.compile(r"MegaTag:\s*(.+)", re.IGNORECASE)

    def validate_line(self, line: str, line_num: int, file_path: Path) -> list[ValidationIssue]:
        """Validate MegaTag in a single line."""
        issues: list[ValidationIssue] = []

        match = self.PATTERN.search(line)
        if not match:
            return issues

        content = match.group(1).strip()

        # Check if contains at least one valid symbol
        has_symbol = any(sym in content for sym in self.VALID_SYMBOLS)
        if not has_symbol:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    tag_type=TagType.MEGATAG,
                    message="MegaTag missing quantum symbols",
                    file_path=file_path,
                    line_number=line_num,
                    suggestion=f"Use symbols: {', '.join(self.VALID_SYMBOLS)}",
                )
            )

        # Check for balanced structure
        if "⨳" in content:
            parts = content.split("⨳")
            if len(parts) < 2:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.INFO,
                        tag_type=TagType.MEGATAG,
                        message="MegaTag has single ⨳ separator (consider pairing)",
                        file_path=file_path,
                        line_number=line_num,
                    )
                )

        return issues


class RSHTSValidator:
    """Validates RSHTS (Recursive Symbolic Harmonic Tag System)."""

    # RSHTS pattern: symmetric symbolic brackets
    OPENING_SYMBOLS: ClassVar[list] = ["♦", "◊", "◆", "○", "●", "◉", "⟡", "⟢", "⟣", "⚡", "⨳"]
    CLOSING_SYMBOLS: ClassVar[list] = ["⨳", "⚡", "⟣", "⟢", "⟡", "◉", "●", "○", "◆", "◊", "♦"]

    def validate_line(self, line: str, line_num: int, file_path: Path) -> list[ValidationIssue]:
        """Validate RSHTS pattern in a single line."""
        issues = []

        # Check for RSHTS tag (heuristic: multiple symbolic patterns)
        symbol_count = sum(1 for sym in self.OPENING_SYMBOLS if sym in line)

        if symbol_count >= 3:  # Likely RSHTS
            # Check for symmetry
            opening = [sym for sym in self.OPENING_SYMBOLS if sym in line]
            closing = [sym for sym in self.CLOSING_SYMBOLS if sym in line]

            if len(opening) != len(closing):
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        tag_type=TagType.RSHTS,
                        message=f"RSHTS pattern asymmetric: {len(opening)} opening, {len(closing)} closing",
                        file_path=file_path,
                        line_number=line_num,
                    )
                )

            # Check for semantic content between symbols
            content_match = re.search(r"⨳(.+?)⨳", line)
            if content_match:
                content = content_match.group(1).strip()
                if not content:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.ERROR,
                            tag_type=TagType.RSHTS,
                            message="RSHTS semantic content is empty",
                            file_path=file_path,
                            line_number=line_num,
                        )
                    )

        return issues


class SymbolicProtocolValidator:
    """Master validator for all symbolic protocols."""

    def __init__(self, enable_omnitag=True, enable_megatag=True, enable_rshts=False):
        """Initialize SymbolicProtocolValidator with enable_omnitag, enable_megatag, enable_rshts."""
        self.enable_omnitag = enable_omnitag
        self.enable_megatag = enable_megatag
        self.enable_rshts = enable_rshts

        self.omnitag_validator = OmniTagValidator()
        self.megatag_validator = MegaTagValidator()
        self.rshts_validator = RSHTSValidator()

        # Paths that require symbolic annotations (opt-in)
        self.required_paths: set[Path] = set()

    def validate_file(self, file_path: Path) -> list[ValidationIssue]:
        """Validate all symbolic protocols in a file."""
        issues = []

        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, start=1):
                # OmniTag validation
                if self.enable_omnitag:
                    issues.extend(self.omnitag_validator.validate_line(line, line_num, file_path))

                # MegaTag validation
                if self.enable_megatag:
                    issues.extend(self.megatag_validator.validate_line(line, line_num, file_path))

                # RSHTS validation (opt-in only for consciousness modules)
                if self.enable_rshts:
                    issues.extend(self.rshts_validator.validate_line(line, line_num, file_path))

        except Exception as e:
            logger.error(f"Error validating {file_path}: {e}")
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    tag_type=TagType.OMNITAG,
                    message=f"Failed to read file: {e}",
                    file_path=file_path,
                    line_number=0,
                )
            )

        return issues

    def validate_directory(
        self, directory: Path, pattern: str = "**/*.py"
    ) -> dict[Path, list[ValidationIssue]]:
        """Validate all Python files in a directory."""
        results = {}

        for file_path in directory.glob(pattern):
            if file_path.is_file():
                issues = self.validate_file(file_path)
                if issues:
                    results[file_path] = issues

        return results

    def generate_report(self, results: dict[Path, list[ValidationIssue]]) -> str:
        """Generate human-readable validation report."""
        if not results:
            return "✅ No symbolic protocol issues found."

        report = "🏷️  Symbolic Protocol Validation Report\n"
        report += "=" * 60 + "\n\n"

        total_issues = sum(len(issues) for issues in results.values())
        report += f"Total Issues: {total_issues}\n"
        report += f"Files Affected: {len(results)}\n\n"

        # Group by level
        by_level = dict.fromkeys(ValidationLevel, 0)
        for issues in results.values():
            for issue in issues:
                by_level[issue.level] += 1

        report += "By Severity:\n"
        for level, count in by_level.items():
            if count > 0:
                report += f"  {level.value.upper()}: {count}\n"
        report += "\n"

        # Detailed issues
        for file_path, issues in results.items():
            report += f"{file_path}:\n"
            for issue in issues:
                report += (
                    f"  Line {issue.line_number}: [{issue.level.value.upper()}] {issue.message}\n"
                )
                if issue.suggestion:
                    report += f"    Suggestion: {issue.suggestion}\n"
            report += "\n"

        return report

    def auto_fix(self, file_path: Path, issues: list[ValidationIssue]) -> bool:
        """Attempt to auto-fix issues in a file."""
        # Only auto-fix if all issues have suggestions
        fixable = [i for i in issues if i.suggestion]
        if not fixable:
            logger.warning(f"No auto-fixable issues in {file_path}")
            return False

        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Apply fixes (sorted reverse to avoid line shifting)
            for issue in sorted(fixable, key=lambda i: i.line_number, reverse=True):
                if 0 < issue.line_number <= len(lines):
                    # Simple replacement (can be enhanced)
                    lines[issue.line_number - 1] = lines[issue.line_number - 1].replace(
                        "OmniTag:", f"OmniTag: {issue.suggestion}"
                    )

            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            logger.info(f"✅ Auto-fixed {len(fixable)} issues in {file_path}")
            return True

        except Exception as e:
            logger.error(f"Auto-fix failed for {file_path}: {e}")
            return False


def validate_symbolic_protocols(
    path: Path,
    enable_omnitag: bool = True,
    enable_megatag: bool = True,
    enable_rshts: bool = False,
    auto_fix: bool = False,
) -> dict[Path, list[ValidationIssue]]:
    """Main entry point for symbolic protocol validation."""
    validator = SymbolicProtocolValidator(
        enable_omnitag=enable_omnitag,
        enable_megatag=enable_megatag,
        enable_rshts=enable_rshts,
    )

    if path.is_file():
        issues = validator.validate_file(path)
        results = {path: issues} if issues else {}
    else:
        results = validator.validate_directory(path)

    # Auto-fix if requested
    if auto_fix:
        for file_path, issues in results.items():
            validator.auto_fix(file_path, issues)

    # Print report
    report = validator.generate_report(results)
    logger.info(report)

    logger.info(f"✅ Symbolic protocol validation complete: {len(results)} files with issues")

    return results


# CLI integration
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate symbolic protocols")
    parser.add_argument("path", type=Path, help="File or directory to validate")
    parser.add_argument("--omnitag", action="store_true", default=True, help="Validate OmniTag")
    parser.add_argument("--megatag", action="store_true", default=True, help="Validate MegaTag")
    parser.add_argument("--rshts", action="store_true", help="Validate RSHTS (opt-in)")
    parser.add_argument("--auto-fix", action="store_true", help="Attempt auto-fix")

    args = parser.parse_args()

    validate_symbolic_protocols(
        args.path,
        enable_omnitag=args.omnitag,
        enable_megatag=args.megatag,
        enable_rshts=args.rshts,
        auto_fix=args.auto_fix,
    )
