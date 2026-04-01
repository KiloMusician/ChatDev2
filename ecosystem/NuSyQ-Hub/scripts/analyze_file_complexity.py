#!/usr/bin/env python3
"""Intelligent File Analysis for Ruff/Quality Tool Processing

Analyzes file characteristics to predict processing time and categorize files:
- Large files (>5000 lines)
- Complex files (many imports, classes, functions)
- Problematic patterns (circular imports, complex decorators)

This helps the batch processor allocate appropriate timeouts and batch sizes.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"


@dataclass
class FileAnalysis:
    """Analysis results for a file."""

    path: str
    lines: int
    imports: int
    classes: int
    functions: int
    complexity_score: float  # 0-10, where 10 is very complex
    estimated_time: float  # seconds
    category: str  # "simple" | "moderate" | "complex" | "problematic"


class FileAnalyzer:
    """Analyzes files to predict processing difficulty."""

    def __init__(self):
        self.simple_files: list[str] = []
        self.moderate_files: list[str] = []
        self.complex_files: list[str] = []
        self.problematic_files: list[str] = []

    def _analyze_file(self, file_path: Path) -> FileAnalysis:
        """Analyze a single file."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return FileAnalysis(
                path=str(file_path.relative_to(PROJECT_ROOT)),
                lines=0,
                imports=0,
                classes=0,
                functions=0,
                complexity_score=0,
                estimated_time=5,
                category="error",
            )

        lines = content.split("\n")
        line_count = len(lines)

        # Count imports
        imports = sum(1 for line in lines if re.match(r"^\s*(?:from|import)\s+", line))

        # Count classes
        classes = sum(1 for line in lines if re.match(r"^\s*class\s+", line))

        # Count functions
        functions = sum(1 for line in lines if re.match(r"^\s*(?:async\s+)?def\s+", line))

        # Detect patterns that make files slow to analyze
        has_circular_imports = "from src" in content and any(f"from src.{SRC_DIR.name}" in line for line in lines)
        has_complex_decorators = content.count("@property") + content.count("@cached") > 5
        has_metaclass = "metaclass" in content
        has_typing_overload = "@overload" in content

        # Calculate complexity score (0-10)
        complexity = (
            min(line_count / 100, 3)  # File size (max 3 points)
            + min(imports / 10, 2)  # Import count (max 2 points)
            + min(classes / 5, 2)  # Class count (max 2 points)
            + min(functions / 10, 2)  # Function count (max 2 points)
            + (1 if has_circular_imports else 0)
            + (1 if has_complex_decorators else 0)
            + (1 if has_metaclass else 0)
            + (0.5 if has_typing_overload else 0)
        )
        complexity = min(complexity, 10)

        # Estimate time based on complexity
        base_time = 10  # base 10 seconds
        estimated_time = base_time + (complexity * 5)  # +5 seconds per complexity point

        # Categorize
        if line_count > 5000 or complexity > 8:
            category = "problematic"
        elif line_count > 1000 or complexity > 6:
            category = "complex"
        elif line_count > 500 or complexity > 3:
            category = "moderate"
        else:
            category = "simple"

        return FileAnalysis(
            path=str(file_path.relative_to(PROJECT_ROOT)),
            lines=line_count,
            imports=imports,
            classes=classes,
            functions=functions,
            complexity_score=complexity,
            estimated_time=estimated_time,
            category=category,
        )

    def analyze_all(self) -> dict[str, list[FileAnalysis]]:
        """Analyze all Python files."""
        all_files = sorted([f for f in SRC_DIR.rglob("*.py") if f.is_file()])
        print(f"📁 Analyzing {len(all_files)} files...")

        analyses = {
            "simple": [],
            "moderate": [],
            "complex": [],
            "problematic": [],
        }

        for i, file_path in enumerate(all_files, 1):
            analysis = self._analyze_file(file_path)
            analyses[analysis.category].append(analysis)

            if i % 50 == 0:
                print(f"  ... {i}/{len(all_files)}")

        return analyses

    def print_report(self, analyses: dict[str, list[FileAnalysis]]) -> None:
        """Print analysis report."""
        print("\n" + "=" * 70)
        print("📊 FILE COMPLEXITY ANALYSIS REPORT")
        print("=" * 70)

        total = sum(len(v) for v in analyses.values())

        for category, files in sorted(analyses.items()):
            if not files:
                continue

            print(f"\n{category.upper()} ({len(files)} files, {len(files) * 100 // total}%)")
            print("-" * 70)

            total_time = sum(f.estimated_time for f in files)
            avg_complexity = sum(f.complexity_score for f in files) / len(files) if files else 0

            print(f"  Total estimated time: {total_time:.1f}s ({total_time / 60:.1f} minutes)")
            print(f"  Average complexity: {avg_complexity:.2f}/10")

            # Show top 5 files by complexity
            if files:
                top_5 = sorted(files, key=lambda f: f.complexity_score, reverse=True)[:5]
                print("  Top 5 by complexity:")
                for f in top_5:
                    print(f"    - {f.path} (score: {f.complexity_score:.2f}, est: {f.estimated_time:.1f}s)")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        problematic_count = len(analyses.get("problematic", []))
        if problematic_count > 0:
            print(f"  ⚠️  {problematic_count} problematic files detected")
            print("      → Increase timeout to 120+ seconds")
            print("      → Process these 1 file per batch")

        complex_count = len(analyses.get("complex", []))
        if complex_count > 5:
            print(f"  ⚠️  {complex_count} complex files detected")
            print("      → Recommend batch_size=5 for complex files")

        print("\n  ✅ Run batch processors with these settings:")
        print("      1. python scripts/ruff_batch_processor.py 5 120  # For complex files")
        print("      2. python scripts/ruff_batch_processor.py 15 20  # For moderate files")
        print("      3. python scripts/ruff_batch_processor.py 20 15  # For simple files")
        print("\n      OR use: python scripts/quality_tools_batch.py --batch-size 5 --verbose")


def main():
    """Main entry point."""
    analyzer = FileAnalyzer()
    analyses = analyzer.analyze_all()
    analyzer.print_report(analyses)

    # Save detailed report
    report_file = PROJECT_ROOT / "state" / "file_complexity_analysis.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "timestamp": str(Path.cwd()),
        "categories": {
            cat: [
                {
                    "path": f.path,
                    "lines": f.lines,
                    "complexity": f.complexity_score,
                    "estimated_time": f.estimated_time,
                }
                for f in files
            ]
            for cat, files in analyses.items()
        },
    }

    report_file.write_text(json.dumps(report_data, indent=2))
    print(f"\n📝 Detailed report saved to: {report_file}")


if __name__ == "__main__":
    main()
