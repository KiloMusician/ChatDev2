#!/usr/bin/env python3
"""BOSS RUSH ERROR CRUSHER - Chug Mode
Systematically destroys errors starting with easiest targets (files with 1-5 errors).
Uses Culture Ship-style parallel orchestration.
"""

import asyncio
import json
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ErrorTarget:
    """Error-bearing file to crush."""

    file: Path
    error_count: int
    error_types: list[str]
    complexity: str  # 'trivial', 'simple', 'moderate', 'complex'


class BossRushErrorCrusher:
    """Systematically eliminates errors using intelligent prioritization."""

    def __init__(self):
        self.root = Path(__file__).parents[1]
        self.targets: list[ErrorTarget] = []
        self.crushed = []
        self.failed = []

    def scan_errors(self) -> dict[str, Any]:
        """Quick scan to identify all error-bearing files."""
        print("🔍 Scanning for errors...")

        # Run ruff on key directories
        result = subprocess.run(
            ["ruff", "check", "src", "scripts", "tests", "--output-format=json"],
            capture_output=True,
            text=True,
            cwd=self.root,
        )

        if not result.stdout:
            print("✅ No errors found!")
            return {"total": 0, "targets": []}

        errors = json.loads(result.stdout)

        # Group by file
        file_errors = defaultdict(list)
        for error in errors:
            file_errors[error["filename"]].append(error["code"])

        # Create targets sorted by error count
        for file, error_list in file_errors.items():
            count = len(error_list)
            complexity = self._assess_complexity(count, error_list)

            target = ErrorTarget(
                file=Path(file),
                error_count=count,
                error_types=list(set(error_list)),
                complexity=complexity,
            )
            self.targets.append(target)

        # Sort by complexity then count (easiest first)
        complexity_order = {"trivial": 0, "simple": 1, "moderate": 2, "complex": 3}
        self.targets.sort(key=lambda t: (complexity_order[t.complexity], t.error_count))

        print(f"📊 Found {len(self.targets)} files with errors")
        print(f"   Trivial: {sum(1 for t in self.targets if t.complexity == 'trivial')}")
        print(f"   Simple: {sum(1 for t in self.targets if t.complexity == 'simple')}")
        print(f"   Moderate: {sum(1 for t in self.targets if t.complexity == 'moderate')}")
        print(f"   Complex: {sum(1 for t in self.targets if t.complexity == 'complex')}")

        return {"total": len(self.targets), "targets": self.targets}

    def _assess_complexity(self, count: int, error_types: list[str]) -> str:
        """Assess fix complexity."""
        # Auto-fixable errors (ruff can handle)
        auto_fixable = {"F401", "F541", "I001", "E501", "W291", "W293"}

        if count <= 3 and all(e in auto_fixable for e in error_types):
            return "trivial"
        elif count <= 5:
            return "simple"
        elif count <= 15:
            return "moderate"
        else:
            return "complex"

    async def crush_trivial_targets(self) -> dict[str, Any]:
        """Auto-fix all trivial targets using ruff --fix."""
        trivial = [t for t in self.targets if t.complexity == "trivial"]

        if not trivial:
            print("⚠️  No trivial targets found")
            return {"crushed": 0}

        print(f"\n🎯 Crushing {len(trivial)} trivial targets...")

        # Ruff can auto-fix these
        subprocess.run(
            ["ruff", "check", "--fix", "src", "scripts", "tests"],
            capture_output=True,
            text=True,
            cwd=self.root,
        )

        self.crushed.extend(trivial)

        print("✅ Auto-fixed trivial errors")
        return {"crushed": len(trivial)}

    async def crush_simple_targets(self) -> dict[str, Any]:
        """Systematically fix simple targets (1-5 errors)."""
        simple = [t for t in self.targets if t.complexity == "simple"][:20]  # Batch of 20

        if not simple:
            print("⚠️  No simple targets in queue")
            return {"crushed": 0}

        print(f"\n🎯 Crushing {len(simple)} simple targets...")

        crushed_count = 0
        for target in simple:
            print(f"   Fixing {target.file.name} ({target.error_count} errors)...")

            # Try auto-fix first
            result = subprocess.run(["ruff", "check", "--fix", str(target.file)], capture_output=True, cwd=self.root)

            if result.returncode == 0:
                crushed_count += 1
                self.crushed.append(target)
            else:
                self.failed.append(target)

        print(f"✅ Crushed {crushed_count}/{len(simple)} simple targets")
        return {"crushed": crushed_count, "failed": len(simple) - crushed_count}

    def generate_report(self) -> dict[str, Any]:
        """Generate boss rush completion report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_targets": len(self.targets),
            "crushed": len(self.crushed),
            "failed": len(self.failed),
            "remaining": len(self.targets) - len(self.crushed) - len(self.failed),
            "crushed_files": [str(t.file) for t in self.crushed],
            "failed_files": [str(t.file) for t in self.failed],
            "complexity_breakdown": {
                "trivial": sum(1 for t in self.targets if t.complexity == "trivial"),
                "simple": sum(1 for t in self.targets if t.complexity == "simple"),
                "moderate": sum(1 for t in self.targets if t.complexity == "moderate"),
                "complex": sum(1 for t in self.targets if t.complexity == "complex"),
            },
        }


async def main():
    """Execute Boss Rush - Chug Mode."""
    print("💪 BOSS RUSH ERROR CRUSHER - Chug Mode Activated")
    print("=" * 70)

    crusher = BossRushErrorCrusher()

    # Scan
    scan_result = crusher.scan_errors()

    if scan_result["total"] == 0:
        print("\n🎉 No errors to crush! System is clean!")
        return

    # Crush trivial
    await crusher.crush_trivial_targets()

    # Crush simple
    await crusher.crush_simple_targets()

    # Report
    report = crusher.generate_report()

    print("\n" + "=" * 70)
    print("📊 BOSS RUSH REPORT")
    print("=" * 70)
    print(f"Total targets identified: {report['total_targets']}")
    print(f"Crushed: {report['crushed']}")
    print(f"Failed: {report['failed']}")
    print(f"Remaining: {report['remaining']}")

    # Save report
    report_path = (
        Path(__file__).parents[1] / "state" / "reports" / f"boss_rush_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"\n✅ Report saved: {report_path}")

    if report["remaining"] > 0:
        print("\n💡 Next Steps:")
        print("   1. Review failed targets manually")
        print("   2. Run again to tackle remaining moderate/complex targets")
        print("   3. Consider using Task agent for complex cases")


if __name__ == "__main__":
    asyncio.run(main())
