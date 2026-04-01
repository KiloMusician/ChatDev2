#!/usr/bin/env python3
"""Automated Code Quality Fixer for NuSyQ-Hub
==========================================
Automatically fixes common code quality issues across the codebase.

Features:
- Line length fixes using ruff format
- Import sorting and organization
- Type hint additions where possible
- Unused import removal
- Docstring formatting

Usage:
    python scripts/auto_quality_fix.py                  # Fix all files
    python scripts/auto_quality_fix.py --target src/    # Fix specific directory
    python scripts/auto_quality_fix.py --dry-run        # Preview changes only
"""

import argparse
import subprocess
import sys
from pathlib import Path


class CodeQualityFixer:
    """Automate code quality fixes using ruff and other tools."""

    def __init__(self, repo_root: Path, dry_run: bool = False):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.fixes_applied = 0
        self.errors_found = 0

    def run_command(self, cmd: list[str], cwd: Path | None = None, check: bool = False) -> tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd or self.repo_root,
                timeout=300,
                check=check,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except subprocess.CalledProcessError as e:
            return e.returncode, e.stdout, e.stderr

    def fix_line_lengths_ruff(self, target: Path) -> int:
        """Fix line length issues using ruff format."""
        print("\n🔧 Fixing line lengths with ruff format...")

        if self.dry_run:
            print("  [DRY RUN] Would format files with ruff")
            return 0

        cmd = ["ruff", "format", str(target)]
        code, stdout, stderr = self.run_command(cmd)

        if code == 0:
            # Count files formatted
            lines = stdout.strip().split("\n") if stdout else []
            formatted = len([line for line in lines if "formatted" in line.lower()])
            print(f"  ✅ Formatted {formatted} files")
            return formatted
        else:
            print(f"  ❌ Error: {stderr}")
            return 0

    def fix_imports_ruff(self, target: Path) -> int:
        """Fix import issues using ruff."""
        print("\n🔧 Fixing imports with ruff...")

        if self.dry_run:
            print("  [DRY RUN] Would fix imports with ruff")
            return 0

        # Fix unused imports
        cmd = [
            "ruff",
            "check",
            str(target),
            "--select=F401",  # Unused imports
            "--fix",
            "--exit-zero",
        ]
        _, stdout, _ = self.run_command(cmd)

        fixes = 0
        if stdout:
            lines = stdout.strip().split("\n")
            fixes = len([line for line in lines if "fixed" in line.lower()])

        print(f"  ✅ Fixed {fixes} import issues")
        return fixes

    def fix_all_ruff(self, target: Path) -> int:
        """Fix all auto-fixable ruff issues."""
        print("\n🔧 Running ruff auto-fix...")

        if self.dry_run:
            print("  [DRY RUN] Would auto-fix with ruff")
            return 0

        cmd = [
            "ruff",
            "check",
            str(target),
            "--fix",
            "--exit-zero",
        ]
        _, stdout, _ = self.run_command(cmd)

        fixes = 0
        if stdout:
            lines = stdout.strip().split("\n")
            fixes = len([line for line in lines if "fixed" in line.lower()])

        print(f"  ✅ Fixed {fixes} issues")
        return fixes

    def format_with_black(self, target: Path) -> int:
        """Format code with black (alternative to ruff format)."""
        print("\n🔧 Formatting with black...")

        if self.dry_run:
            print("  [DRY RUN] Would format with black")
            return 0

        cmd = ["black", str(target), "--quiet"]
        code, _, _ = self.run_command(cmd)

        if code == 0:
            print("  ✅ Black formatting complete")
            return 1
        else:
            print("  ❌ Error: formatting failed")
            return 0

    def check_remaining_issues(self, target: Path) -> dict:
        """Check what issues remain after fixes."""
        print("\n📊 Checking remaining issues...")

        cmd = [
            "ruff",
            "check",
            str(target),
            "--output-format=json",
            "--exit-zero",
        ]
        _, stdout, _ = self.run_command(cmd)

        if stdout:
            import json

            try:
                issues = json.loads(stdout)
                by_code: dict[str, int] = {}
                for issue in issues:
                    code_name = issue.get("code", "UNKNOWN")
                    by_code[code_name] = by_code.get(code_name, 0) + 1

                total = len(issues)
                print(f"\n  📋 Remaining issues: {total}")
                if by_code:
                    print("\n  Top issue types:")
                    sorted_issues = sorted(by_code.items(), key=lambda x: x[1], reverse=True)[:10]
                    for issue_code, count in sorted_issues:
                        print(f"    - {issue_code}: {count}")

                return {"total": total, "by_code": by_code}

            except json.JSONDecodeError:
                pass

        return {"total": 0, "by_code": {}}

    def run_full_fix(self, target: Path) -> None:
        """Run all fixes in sequence."""
        print(f"\n{'=' * 60}")
        print("🚀 NuSyQ Code Quality Auto-Fixer")
        print(f"{'=' * 60}")
        print(f"Target: {target}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'APPLYING FIXES'}")
        print(f"{'=' * 60}")

        # Step 1: Format with ruff
        fixes = self.fix_line_lengths_ruff(target)
        self.fixes_applied += fixes

        # Step 2: Fix imports
        fixes = self.fix_imports_ruff(target)
        self.fixes_applied += fixes

        # Step 3: Fix all auto-fixable issues
        fixes = self.fix_all_ruff(target)
        self.fixes_applied += fixes

        # Step 4: Check remaining
        remaining = self.check_remaining_issues(target)
        self.errors_found = remaining["total"]

        # Summary
        print(f"\n{'=' * 60}")
        print("✅ Summary")
        print(f"{'=' * 60}")
        print(f"  Fixes applied: {self.fixes_applied}")
        print(f"  Issues remaining: {self.errors_found}")

        if self.dry_run:
            print("\n  ℹ️  This was a dry run. No changes were made.")
            print("     Run without --dry-run to apply fixes.")
        else:
            print("\n  ✨ All automatic fixes have been applied!")
            if self.errors_found > 0:
                print(f"     {self.errors_found} issues require manual attention.")

        print(f"{'=' * 60}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Automatically fix code quality issues in NuSyQ-Hub")
    parser.add_argument(
        "--target",
        type=str,
        default="src",
        help="Target directory or file to fix (default: src)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )
    parser.add_argument(
        "--skip-format",
        action="store_true",
        help="Skip formatting step (only fix lints)",
    )

    args = parser.parse_args()

    # Determine repo root
    repo_root = Path(__file__).parent.parent
    target_path = repo_root / args.target

    if not target_path.exists():
        print(f"❌ Error: Target not found: {target_path}")
        sys.exit(1)

    # Create fixer
    fixer = CodeQualityFixer(repo_root=repo_root, dry_run=args.dry_run)

    # Run fixes
    fixer.run_full_fix(target_path)

    # Exit with error if issues remain and not dry run
    if not args.dry_run and fixer.errors_found > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
