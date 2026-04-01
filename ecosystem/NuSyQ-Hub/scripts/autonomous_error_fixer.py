#!/usr/bin/env python3
"""🤖 Autonomous Error Fixer - Ecosystem-Guided Systematic Repair
===============================================================

Uses the newly activated ecosystem to autonomously fix errors:
1. Queries ecosystem_integrator for past solutions
2. Routes tasks to specialist models
3. Applies fixes systematically
4. Verifies results
5. Documents progress

Targets: F401 (unused imports), E402 (import order), F841 (unused vars)

OmniTag: [autonomous_fixing, ecosystem_guided, systematic_repair, qwen2.5-coder_specialist]
"""

from __future__ import annotations

import subprocess
import sys
from importlib import import_module
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def _load_ecosystem_integrator():
    """Import EcosystemIntegrator from available module paths."""
    try:
        module = import_module("diagnostics.ecosystem_integrator")
    except ModuleNotFoundError:
        module = import_module("src.diagnostics.ecosystem_integrator")
    return module.EcosystemIntegrator()


class AutonomousErrorFixer:
    """🤖 Autonomous error fixing using ecosystem intelligence"""

    def __init__(self):
        self.integrator = _load_ecosystem_integrator()
        self.fixes_applied = []
        self.errors_before = {}
        self.errors_after = {}

    def scan_errors(self, error_codes: list[str] | None = None) -> dict[str, int]:
        """Scan for errors and return counts."""
        if error_codes is None:
            error_codes = ["F401", "E402", "F841", "W605"]

        cmd = ["ruff", "check", "src/", f"--select={','.join(error_codes)}", "--statistics"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)

            # Parse statistics
            counts = {}
            for line in result.stdout.split("\n"):
                if line.strip() and not line.startswith("Found"):
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        try:
                            count = int(parts[0])
                            code = parts[1]
                            counts[code] = count
                        except ValueError:
                            continue

            return counts

        except subprocess.TimeoutExpired as exc:
            print(f"⚠️  Error scanning (timeout): {exc}")
            return {}
        except subprocess.CalledProcessError as exc:
            print(f"⚠️  Error scanning (non-zero exit): {exc.stderr or exc}")
            return {}
        except FileNotFoundError as exc:
            print(f"⚠️  Error scanning (ruff missing): {exc}")
            return {}

    def fix_f401_unused_imports(self) -> int:
        """Fix F401 (unused import) errors automatically.
        Specialist: qwen2.5-coder:14b
        """
        print("\n🔧 Fixing F401 (unused imports)")
        print(f"   Specialist: {self.integrator.route_task_to_specialist('Fix F401 unused imports', 'F401')}")

        # Get intelligence from ecosystem
        intel = self.integrator.get_comprehensive_intelligence("F401")
        print(f"   Confidence: {intel['synthesis']['confidence']:.0%}")
        print(f"   Recommended: {intel['synthesis']['recommended_action'][:80]}...")

        # Apply ruff auto-fix
        cmd = ["ruff", "check", "src/", "--select=F401", "--fix", "--no-cache"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)

            # Count fixes
            fixes = result.stdout.count("Fixed")
            self.fixes_applied.append(
                {
                    "error_code": "F401",
                    "fixes": fixes,
                    "specialist": "qwen2.5-coder:14b",
                    "method": "ruff auto-fix",
                }
            )

            print(f"   ✅ Applied {fixes} automated fixes")
            return fixes

        except subprocess.TimeoutExpired as exc:
            print(f"   ❌ Error: ruff timed out ({exc})")
            return 0
        except subprocess.CalledProcessError as exc:
            print(f"   ❌ Error: ruff failed ({exc.stderr or exc})")
            return 0
        except FileNotFoundError as exc:
            print(f"   ❌ Error: ruff not found ({exc})")
            return 0

    def fix_f841_unused_variables(self) -> int:
        """Fix F841 (unused variable) errors automatically.
        Specialist: deepseek-coder-v2:16b (debugging specialist)
        """
        print("\n🔧 Fixing F841 (unused variables)")
        print(f"   Specialist: {self.integrator.route_task_to_specialist('Fix unused variables', 'F841')}")

        # Apply ruff auto-fix
        cmd = ["ruff", "check", "src/", "--select=F841", "--fix", "--no-cache"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)

            fixes = result.stdout.count("Fixed")
            self.fixes_applied.append(
                {
                    "error_code": "F841",
                    "fixes": fixes,
                    "specialist": "deepseek-coder-v2:16b",
                    "method": "ruff auto-fix",
                }
            )

            print(f"   ✅ Applied {fixes} automated fixes")
            return fixes

        except subprocess.TimeoutExpired as exc:
            print(f"   ❌ Error: ruff timed out ({exc})")
            return 0
        except subprocess.CalledProcessError as exc:
            print(f"   ❌ Error: ruff failed ({exc.stderr or exc})")
            return 0
        except FileNotFoundError as exc:
            print(f"   ❌ Error: ruff not found ({exc})")
            return 0

    def analyze_e402_patterns(self) -> dict[str, Any]:
        """Analyze E402 (module import not at top) patterns.
        E402 often requires manual review due to conditional imports.
        """
        print("\n🔍 Analyzing E402 (module import not at top)")
        print(f"   Specialist: {self.integrator.route_task_to_specialist('Fix E402 import order', 'E402')}")

        # Get past solutions
        intel = self.integrator.get_comprehensive_intelligence("E402")

        print(f"   Past solutions: {intel['sources']['knowledge_base'].get('total_past_solutions', 0)}")
        print(f"   Confidence: {intel['synthesis']['confidence']:.0%}")

        # Get sample E402 errors
        cmd = ["ruff", "check", "src/", "--select=E402", "--output-format=concise"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)

            lines = [line for line in result.stdout.split("\n") if "E402" in line][:10]

            return {
                "total_errors": len([line for line in result.stdout.split("\n") if "E402" in line]),
                "sample_errors": lines,
                "intelligence": intel,
            }

        except subprocess.TimeoutExpired as exc:
            print(f"   ❌ Error: ruff timed out ({exc})")
            return {}
        except subprocess.CalledProcessError as exc:
            print(f"   ❌ Error: ruff failed ({exc.stderr or exc})")
            return {}
        except FileNotFoundError as exc:
            print(f"   ❌ Error: ruff not found ({exc})")
            return {}

    def run_autonomous_fixes(self):
        """Run autonomous fixing pipeline."""
        print("=" * 80)
        print("🤖 AUTONOMOUS ERROR FIXER - Ecosystem-Guided Repair")
        print("=" * 80)

        # Step 1: Initial scan
        print("\n📊 Step 1: Initial Error Scan")
        self.errors_before = self.scan_errors()

        total_before = sum(self.errors_before.values())
        print(f"\n   Initial Error Count: {total_before}")
        for code, count in sorted(self.errors_before.items()):
            print(f"      {code}: {count}")

        # Step 2: Fix F401 (unused imports) - safest, auto-fixable
        self.fix_f401_unused_imports()

        # Step 3: Fix F841 (unused variables) - safe, auto-fixable
        self.fix_f841_unused_variables()

        # Step 4: Analyze E402 (requires review)
        e402_analysis = self.analyze_e402_patterns()

        if e402_analysis:
            print(f"\n   E402 Errors: {e402_analysis.get('total_errors', 0)}")
            print("   Sample errors:")
            for err in e402_analysis.get("sample_errors", [])[:5]:
                print(f"      {err[:120]}")

        # Step 5: Final scan
        print("\n📊 Step 2: Final Error Scan")
        self.errors_after = self.scan_errors()

        total_after = sum(self.errors_after.values())
        print(f"\n   Final Error Count: {total_after}")
        for code, count in sorted(self.errors_after.items()):
            before = self.errors_before.get(code, 0)
            diff = before - count
            symbol = "✅" if diff > 0 else "⚠️" if diff == 0 else "❌"
            print(f"      {code}: {count} ({symbol} {diff:+d})")

        # Summary
        print("\n" + "=" * 80)
        print("📊 AUTONOMOUS FIXING SUMMARY")
        print("=" * 80)

        total_fixed = total_before - total_after
        print(f"\n✅ Total Errors Fixed: {total_fixed}")
        print(f"   Before: {total_before}")
        print(f"   After: {total_after}")
        print(f"   Improvement: {(total_fixed / total_before * 100) if total_before > 0 else 0:.1f}%")

        print("\n🔧 Fixes Applied by Specialist:")
        for fix in self.fixes_applied:
            print(f"   {fix['error_code']}: {fix['fixes']} fixes via {fix['specialist']}")

        # Recommendations
        print("\n💡 Recommendations:")

        if self.errors_after.get("E402", 0) > 50:
            print("   • E402 (import order): Requires manual review - many conditional imports")
            print("     Consider: Review import patterns and consolidate where safe")

        if self.errors_after.get("F401", 0) > 0:
            print(f"   • F401 (unused imports): {self.errors_after.get('F401', 0)} remaining")
            print("     Consider: Run ruff with --unsafe-fixes for aggressive cleanup")

        print("\n" + "=" * 80)
        print("✅ AUTONOMOUS FIXING COMPLETE")
        print("=" * 80)

        return {
            "before": self.errors_before,
            "after": self.errors_after,
            "fixes": self.fixes_applied,
            "total_fixed": total_fixed,
        }


def main():
    """Run autonomous error fixer."""
    fixer = AutonomousErrorFixer()
    result = fixer.run_autonomous_fixes()

    # Return non-zero if no fixes applied
    return 0 if result["total_fixed"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
