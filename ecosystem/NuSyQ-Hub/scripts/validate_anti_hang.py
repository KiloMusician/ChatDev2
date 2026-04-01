#!/usr/bin/env python3
"""Anti-Hang Solution Validation Script

Validates that all components are working properly:
- Scripts exist and are runnable
- Dependencies installed
- State directories accessible
- Checkpoints can be read/written
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"
DOCS_DIR = PROJECT_ROOT / "docs"


class ValidationReport:
    """Tracks validation results."""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0

    def check(self, condition: bool, message: str) -> None:
        """Record a check result."""
        if condition:
            print(f"  ✅ {message}")
            self.checks_passed += 1
        else:
            print(f"  ❌ {message}")
            self.checks_failed += 1

    def warn(self, condition: bool, message: str) -> None:
        """Record a warning."""
        if not condition:
            print(f"  ⚠️  {message}")
            self.warnings += 1

    def summary(self) -> int:
        """Print summary and return exit code."""
        print("\n" + "=" * 70)
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"⚠️  Warnings: {self.warnings}")

        if self.checks_failed == 0:
            print("\n🎉 All validations passed! Ready to use anti-hang system.")
            return 0
        else:
            print(f"\n❌ {self.checks_failed} validation(s) failed. See above for details.")
            return 1


def main():
    """Run validation."""
    report = ValidationReport()

    print("🔍 Anti-Hang Solution Validation")
    print("=" * 70)

    # 1. Check scripts exist
    print("\n📝 Checking scripts exist...")
    scripts = [
        "analyze_file_complexity.py",
        "ruff_batch_processor.py",
        "quality_tools_batch.py",
        "quality_orchestrator.py",
        "hang_detector.py",
    ]
    for script in scripts:
        script_path = SCRIPTS_DIR / script
        report.check(script_path.exists(), f"Script exists: {script}")

    # 2. Check directories
    print("\n📁 Checking directories...")
    report.check(STATE_DIR.exists(), f"State directory exists: {STATE_DIR}")
    report.check(LOGS_DIR.exists(), f"Logs directory exists: {LOGS_DIR}")
    report.check(DOCS_DIR.exists(), f"Docs directory exists: {DOCS_DIR}")

    # 3. Check documentation
    print("\n📚 Checking documentation...")
    docs = [
        "ANTI_HANG_SOLUTION.md",
        "QUALITY_TOOLS_BATCH_PROCESSING.md",
        "QUICK_REFERENCE_ANTI_HANG.md",
    ]
    for doc in docs:
        doc_path = DOCS_DIR / doc
        report.check(doc_path.exists(), f"Documentation exists: {doc}")

    # 4. Check Python dependencies
    print("\n🐍 Checking Python dependencies...")
    dependencies = ["ruff", "black", "mypy", "psutil"]
    for dep in dependencies:
        try:
            __import__(dep)
            report.check(True, f"Module available: {dep}")
        except ImportError:
            if dep == "psutil":
                report.warn(True, f"Optional module missing (nice-to-have): {dep}")
            else:
                report.check(False, f"Module available: {dep}")

    # 5. Check script syntax
    print("\n✓ Checking script syntax...")
    for script in scripts:
        script_path = SCRIPTS_DIR / script
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(script_path)],
                capture_output=True,
                timeout=5,
            )
            report.check(result.returncode == 0, f"Script valid Python: {script}")
        except Exception as e:
            report.check(False, f"Script valid Python: {script} ({e})")

    # 6. Check write permissions
    print("\n🔒 Checking file permissions...")
    try:
        test_file = STATE_DIR / ".permission_test"
        test_file.write_text("test")
        test_file.unlink()
        report.check(True, f"Write permission: {STATE_DIR}")
    except Exception as e:
        report.check(False, f"Write permission: {STATE_DIR} ({e})")

    # 7. Test basic import
    print("\n⚙️  Testing basic imports...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from src.integrations.nogic_quest_integration import NogicQuestIntegration",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=10,
        )
        report.warn(result.returncode == 0, "Main imports working (optional)")
    except Exception:
        report.warn(False, "Main imports working (optional)")

    # 8. Check VS Code tasks
    print("\n🎮 Checking VS Code integration...")
    tasks_file = PROJECT_ROOT / ".vscode" / "tasks.json"
    if tasks_file.exists():
        content = tasks_file.read_text()
        report.check("Smart Orchestrator" in content, "VS Code task: Smart Orchestrator")
        report.check("Batch Tools" in content, "VS Code task: Batch Tools")
        report.check("Analyze File Complexity" in content, "VS Code task: Analyze Complexity")
    else:
        report.check(False, "VS Code tasks file exists")

    return report.summary()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        sys.exit(1)
