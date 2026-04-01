"""Error Prioritization System - Intelligent error analysis and auto-fix suggestions.

This module provides:
- Severity scoring (which errors matter most)
- Auto-fix confidence levels (safe vs risky)
- Healing progress tracking
- Batch error fixing workflow

Usage:
    python scripts/start_nusyq.py analyze_errors --prioritize
    python scripts/start_nusyq.py heal --auto --confidence high --limit 10
    python scripts/start_nusyq.py heal --watch  # Continuous healing
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class ErrorClassification:
    """Classification of an error with priority and fix confidence."""

    file_path: str
    line_number: int | None
    error_code: str
    error_type: str  # 'ruff', 'mypy', 'pylint', etc.
    severity: Literal["critical", "high", "medium", "low", "info"]
    message: str
    fix_confidence: Literal["high", "medium", "low", "manual"]
    auto_fix_available: bool
    priority_score: float  # 0-100, higher = more important
    category: str  # 'import', 'type', 'style', 'security', etc.
    suggested_fix: str | None
    fix_command: str | None


def run_ruff_check(path: Path | None = None) -> list[dict[str, Any]]:
    """Run ruff check and return parsed results."""
    target = str(path) if path else str(PROJECT_ROOT / "src")

    try:
        result = subprocess.run(
            ["ruff", "check", target, "--output-format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.stdout:
            return json.loads(result.stdout)
        return []

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
        return []


def run_mypy_check(path: Path | None = None) -> list[dict[str, Any]]:
    """Run mypy and parse results."""
    target = str(path) if path else str(PROJECT_ROOT / "src")

    try:
        result = subprocess.run(
            ["mypy", target, "--no-error-summary"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        errors: list[dict[str, Any]] = []
        for line in result.stdout.splitlines():
            if ":" not in line:
                continue

            parts = line.split(":", 3)
            if len(parts) >= 4:
                file_path = parts[0]
                try:
                    line_num = int(parts[1])
                except ValueError:
                    line_num = None

                message = parts[3].strip() if len(parts) > 3 else ""
                error_code = parts[2].strip() if len(parts) > 2 else "error"

                errors.append(
                    {
                        "file": file_path,
                        "line": line_num,
                        "code": error_code,
                        "message": message,
                        "tool": "mypy",
                    }
                )

        return errors

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return []


def calculate_severity(
    error: dict[str, Any],
) -> Literal["critical", "high", "medium", "low", "info"]:
    """Calculate error severity based on type and context."""
    error_code = error.get("code", "").lower()
    message = error.get("message", "").lower()

    # Critical errors (breaking functionality)
    if any(keyword in message for keyword in ["importerror", "modulenotfounderror", "syntaxerror", "nameerror"]):
        return "critical"
    if any(keyword in error_code for keyword in ["e999", "f821", "f822", "f831"]):
        return "critical"

    # High priority (likely bugs)
    if any(keyword in error_code for keyword in ["f", "e7", "e9"]):  # pyflakes, syntax
        return "high"
    if "type" in error_code or "attr" in message:
        return "high"

    # Medium priority (code quality)
    if any(keyword in error_code for keyword in ["c", "n", "w"]):  # convention, naming, warning
        return "medium"

    # Low priority (style)
    if any(keyword in error_code for keyword in ["e1", "e2", "e3", "e5"]):  # indentation, whitespace
        return "low"

    # Info (documentation, comments)
    if any(keyword in error_code for keyword in ["d", "rst"]):
        return "info"

    return "medium"  # Default


def calculate_fix_confidence(
    error: dict[str, Any],
) -> tuple[Literal["high", "medium", "low", "manual"], bool]:
    """Calculate confidence in automated fix and whether auto-fix is available.

    Returns:
        (confidence_level, auto_fix_available)
    """
    error_code = error.get("code", "").lower()
    message = error.get("message", "").lower()
    tool = error.get("tool", "unknown")

    # High confidence auto-fixes (safe transformations)
    if tool == "ruff" and any(keyword in error_code for keyword in ["f401", "f541", "i001", "e501"]):
        return ("high", True)  # Unused imports, import sorting, line length

    if any(keyword in error_code for keyword in ["w291", "w292", "w293"]):
        return ("high", True)  # Trailing whitespace

    # Medium confidence (usually safe but review recommended)
    if tool == "ruff" and any(keyword in error_code for keyword in ["f811", "e701", "e702"]):
        return ("medium", True)  # Redefined, multiple statements

    if "missing type annotation" in message:
        return ("medium", False)  # Can suggest but needs human input

    # Low confidence (context-dependent)
    if tool == "mypy" or "type" in message:
        return ("low", False)  # Type errors need careful analysis

    if "import" in message and "cannot" in message:
        return ("low", False)  # Import errors need investigation

    # Manual required (complex logic changes)
    if any(keyword in message for keyword in ["refactor", "too complex", "cyclomatic"]):
        return ("manual", False)

    return ("medium", tool == "ruff")  # Ruff has auto-fix capability


def categorize_error(error: dict[str, Any]) -> str:
    """Categorize error by type."""
    error_code = error.get("code", "").lower()
    message = error.get("message", "").lower()

    if "import" in message or error_code.startswith("f4") or error_code.startswith("i"):
        return "import"
    elif "type" in message or error_code.startswith("type"):
        return "type_annotation"
    elif any(keyword in message for keyword in ["security", "injection", "crypto"]):
        return "security"
    elif any(keyword in error_code for keyword in ["c", "n"]):
        return "naming_convention"
    elif any(keyword in error_code for keyword in ["w", "e1", "e2", "e3", "e5"]):
        return "style"
    elif error_code.startswith("d"):
        return "documentation"
    elif any(keyword in message for keyword in ["unused", "defined"]):
        return "dead_code"
    else:
        return "logic"


def calculate_priority_score(severity: str, fix_confidence: str, category: str) -> float:
    """Calculate 0-100 priority score.

    Higher score = should fix first.
    """
    # Base score from severity
    severity_scores = {
        "critical": 100,
        "high": 75,
        "medium": 50,
        "low": 25,
        "info": 10,
    }
    base_score = severity_scores.get(severity, 50)

    # Adjust for fix confidence (easier to fix = higher priority)
    confidence_multipliers = {
        "high": 1.2,
        "medium": 1.0,
        "low": 0.8,
        "manual": 0.6,
    }
    confidence_mult = confidence_multipliers.get(fix_confidence, 1.0)

    # Adjust for category (some categories more impactful)
    category_adjustments = {
        "import": 10,  # Breaking issues
        "security": 15,  # Critical issues
        "type_annotation": 5,  # Quality improvement
        "dead_code": -5,  # Can defer
        "documentation": -10,  # Low impact
    }
    category_adj = category_adjustments.get(category, 0)

    return min(100, max(0, base_score * confidence_mult + category_adj))


def suggest_fix(error: dict[str, Any], confidence: str) -> str | None:
    """Generate suggested fix description."""
    if confidence == "manual":
        return "Requires manual review and refactoring"

    error_code = error.get("code", "")
    message = error.get("message", "")

    # Import errors
    if "f401" in error_code.lower():
        return "Remove unused import"
    elif "f811" in error_code.lower():
        return "Rename duplicate definition"
    elif "i001" in error_code.lower():
        return "Sort imports alphabetically"

    # Style errors
    elif "e501" in error_code.lower():
        return "Break line at 88 characters"
    elif "w291" in error_code.lower() or "trailing whitespace" in message.lower():
        return "Remove trailing whitespace"

    # Type errors
    elif "missing type" in message.lower():
        return "Add type annotation"

    return None


def generate_fix_command(error: dict[str, Any], confidence: str) -> str | None:
    """Generate command to auto-fix error if possible."""
    if confidence not in ("high", "medium"):
        return None

    tool = error.get("tool", "unknown")
    file_path = error.get("file", "")

    if tool == "ruff":
        # Ruff can auto-fix many issues
        return f"ruff check {file_path} --fix --unsafe-fixes"

    return None


def classify_errors(errors: list[dict[str, Any]]) -> list[ErrorClassification]:
    """Classify and prioritize a list of errors."""
    classified: list[ErrorClassification] = []

    for error in errors:
        severity = calculate_severity(error)
        confidence, auto_fix = calculate_fix_confidence(error)
        category = categorize_error(error)
        priority = calculate_priority_score(severity, confidence, category)

        classified.append(
            ErrorClassification(
                file_path=error.get("file", error.get("filename", "unknown")),
                line_number=error.get("line", error.get("location", {}).get("row")),
                error_code=error.get("code", "unknown"),
                error_type=error.get("tool", "unknown"),
                severity=severity,
                message=error.get("message", ""),
                fix_confidence=confidence,
                auto_fix_available=auto_fix,
                priority_score=priority,
                category=category,
                suggested_fix=suggest_fix(error, confidence),
                fix_command=generate_fix_command(error, confidence),
            )
        )

    # Sort by priority (highest first)
    classified.sort(key=lambda e: e.priority_score, reverse=True)

    return classified


def save_analysis(classified_errors: list[ErrorClassification], output_path: Path | None = None) -> Path:
    """Save error analysis to JSON file."""
    if output_path is None:
        output_path = PROJECT_ROOT / "state" / "error_analysis.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    analysis = {
        "timestamp": datetime.now().isoformat(),
        "total_errors": len(classified_errors),
        "by_severity": {},
        "by_category": {},
        "by_confidence": {},
        "auto_fixable_count": sum(1 for e in classified_errors if e.auto_fix_available),
        "errors": [asdict(e) for e in classified_errors],
    }

    # Count by severity
    for error in classified_errors:
        analysis["by_severity"][error.severity] = analysis["by_severity"].get(error.severity, 0) + 1
        analysis["by_category"][error.category] = analysis["by_category"].get(error.category, 0) + 1
        analysis["by_confidence"][error.fix_confidence] = analysis["by_confidence"].get(error.fix_confidence, 0) + 1

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    return output_path


def print_analysis_summary(classified_errors: list[ErrorClassification]):
    """Print human-readable summary of error analysis."""
    print("📊 Error Prioritization Analysis")
    print("=" * 60)
    print(f"\nTotal Errors: {len(classified_errors)}")

    # By severity
    print("\n🔥 By Severity:")
    severity_counts: dict[str, int] = {}
    for error in classified_errors:
        severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1

    severity_symbols = {"critical": "🚨", "high": "⚠️ ", "medium": "📋", "low": "💡", "info": "ℹ️ "}

    for severity in ["critical", "high", "medium", "low", "info"]:
        count = severity_counts.get(severity, 0)
        if count > 0:
            pct = (count / len(classified_errors) * 100) if classified_errors else 0
            symbol = severity_symbols.get(severity, "")
            print(f"   {symbol} {severity}: {count} ({pct:.1f}%)")

    # By category
    print("\n🏷️  By Category:")
    category_counts: dict[str, int] = {}
    for error in classified_errors:
        category_counts[error.category] = category_counts.get(error.category, 0) + 1

    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = (count / len(classified_errors) * 100) if classified_errors else 0
        print(f"   {category}: {count} ({pct:.1f}%)")

    # Fix confidence
    print("\n🔧 Fix Confidence:")
    confidence_counts: dict[str, int] = {}
    auto_fixable = 0
    for error in classified_errors:
        confidence_counts[error.fix_confidence] = confidence_counts.get(error.fix_confidence, 0) + 1
        if error.auto_fix_available:
            auto_fixable += 1

    for confidence in ["high", "medium", "low", "manual"]:
        count = confidence_counts.get(confidence, 0)
        if count > 0:
            pct = (count / len(classified_errors) * 100) if classified_errors else 0
            symbol = "✅" if confidence == "high" else "⚠️ " if confidence == "medium" else "❌"
            print(f"   {symbol} {confidence}: {count} ({pct:.1f}%)")

    print(
        f"\n🤖 Auto-fixable: {auto_fixable} ({auto_fixable / len(classified_errors) * 100:.1f}%)"
        if classified_errors
        else ""
    )

    # Top priority errors
    print("\n🎯 Top 10 Priority Errors:")
    for i, error in enumerate(classified_errors[:10], 1):
        severity_symbol = severity_symbols.get(error.severity, "")
        print(f"\n{i}. {severity_symbol} [{error.severity.upper()}] {error.file_path}:{error.line_number or '?'}")
        print(f"   Code: {error.error_code} | Category: {error.category}")
        print(f"   Priority Score: {error.priority_score:.1f}/100")
        print(f"   Message: {error.message[:80]}...")
        if error.suggested_fix:
            print(f"   Fix: {error.suggested_fix}")
        if error.fix_command:
            print(f"   Command: {error.fix_command}")


def main():
    """Command-line interface for error prioritization."""
    import argparse

    parser = argparse.ArgumentParser(description="Error Prioritization System")
    parser.add_argument("--path", type=str, help="Path to analyze (default: src/)")
    parser.add_argument("--output", type=str, help="Output JSON file")
    parser.add_argument("--tool", choices=["ruff", "mypy", "all"], default="all", help="Which tool to run")
    parser.add_argument(
        "--min-severity",
        choices=["critical", "high", "medium", "low", "info"],
        default="info",
        help="Minimum severity to show",
    )

    args = parser.parse_args()

    target_path = Path(args.path) if args.path else None

    print("🔍 Scanning for errors...")
    print("=" * 60)

    all_errors: list[dict[str, Any]] = []

    if args.tool in ("ruff", "all"):
        print("\n📝 Running ruff...")
        ruff_errors = run_ruff_check(target_path)
        for error in ruff_errors:
            error["tool"] = "ruff"
        all_errors.extend(ruff_errors)
        print(f"   Found {len(ruff_errors)} ruff errors")

    if args.tool in ("mypy", "all"):
        print("\n🔬 Running mypy...")
        mypy_errors = run_mypy_check(target_path)
        all_errors.extend(mypy_errors)
        print(f"   Found {len(mypy_errors)} mypy errors")

    print(f"\n✅ Total errors found: {len(all_errors)}")
    print("\n🧠 Classifying and prioritizing...")

    classified = classify_errors(all_errors)

    # Filter by minimum severity
    severity_order = ["info", "low", "medium", "high", "critical"]
    min_idx = severity_order.index(args.min_severity)
    classified = [e for e in classified if severity_order.index(e.severity) >= min_idx]

    print(f"   {len(classified)} errors at {args.min_severity}+ severity\n")

    # Save analysis
    output_path = Path(args.output) if args.output else None
    saved_path = save_analysis(classified, output_path)
    print(f"✅ Analysis saved to: {saved_path}\n")

    # Print summary
    print_analysis_summary(classified)


if __name__ == "__main__":
    main()
