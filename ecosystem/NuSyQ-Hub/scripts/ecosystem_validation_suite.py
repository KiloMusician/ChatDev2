#!/usr/bin/env python3
"""Comprehensive NuSyQ Ecosystem Validation Suite
Tests all commands, scripts, workflows, and orchestrations
Generates report for documentation updates
"""

import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class TestResult:
    name: str
    category: str
    command: str
    success: bool
    output: str = ""
    error: str = ""
    duration_ms: float = 0
    notes: str = ""


class EcosystemValidator:
    def __init__(self):
        self.results = []
        self.nusyq_hub = Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub")
        self.nusyq_root = Path("C:/Users/keath/NuSyQ")
        self.simulated_verse = Path("C:/Users/keath/Desktop/SimulatedVerse")
        self.report = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "tests": [], "summary": {}}

    def run_command(self, cmd, cwd=None, name="", category="", timeout=30, shell=True):
        """Execute command and capture result"""
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or Path.cwd(),
                capture_output=True,
                text=True,
                shell=shell,
                timeout=timeout,
            )

            duration = (time.time() - start) * 1000
            success = result.returncode == 0

            test_result = TestResult(
                name=name,
                category=category,
                command=cmd,
                success=success,
                output=result.stdout[:500],  # First 500 chars
                error=result.stderr[:500],
                duration_ms=duration,
            )

            self.results.append(test_result)
            status = "✅" if success else "❌"
            print(f"{status} {name:40} ({duration:.0f}ms)")

            return success

        except subprocess.TimeoutExpired:
            test_result = TestResult(
                name=name,
                category=category,
                command=cmd,
                success=False,
                error=f"TIMEOUT after {timeout}s",
                duration_ms=timeout * 1000,
            )
            self.results.append(test_result)
            print(f"⏱️  {name:40} (TIMEOUT)")
            return False
        except Exception as e:
            test_result = TestResult(
                name=name,
                category=category,
                command=cmd,
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )
            self.results.append(test_result)
            print(f"❌ {name:40} (ERROR)")
            return False

    def test_python_syntax(self, file_path, name="", category=""):
        """Validate Python file syntax"""
        import ast

        try:
            with open(file_path) as f:
                ast.parse(f.read())

            test_result = TestResult(
                name=name or f"Syntax: {file_path.name}",
                category=category or "syntax",
                command=f"ast.parse({file_path.name})",
                success=True,
            )
            self.results.append(test_result)
            print(f"✅ {test_result.name:40} (syntax valid)")
            return True
        except SyntaxError as e:
            test_result = TestResult(
                name=name or f"Syntax: {file_path.name}",
                category=category or "syntax",
                command=f"ast.parse({file_path.name})",
                success=False,
                error=f"Line {e.lineno}: {e.msg}",
            )
            self.results.append(test_result)
            print(f"❌ {test_result.name:40} ({e.msg})")
            return False

    def test_repo_structure(self):
        """Verify all repos exist"""
        print("\n📁 Repository Structure:")
        print("-" * 70)

        repos = [
            (self.nusyq_hub, "NuSyQ-Hub"),
            (self.nusyq_root, "NuSyQ Root"),
            (self.simulated_verse, "SimulatedVerse"),
        ]

        for repo_path, repo_name in repos:
            exists = repo_path.exists()
            status = "✅" if exists else "❌"
            print(f"{status} {repo_name:20} {repo_path}")

            test_result = TestResult(
                name=f"Repo exists: {repo_name}",
                category="structure",
                command=f"Path.exists({repo_name})",
                success=exists,
            )
            self.results.append(test_result)

    def test_nusyq_hub(self):
        """Test NuSyQ-Hub commands"""
        print("\n🧠 NuSyQ-Hub Tests:")
        print("-" * 70)

        # Test 1: Snapshot generation
        self.run_command(
            "python scripts/start_nusyq.py --help",
            cwd=self.nusyq_hub,
            name="start_nusyq.py --help",
            category="hub_basic",
            timeout=10,
        )

        # Test 2: Error report
        self.run_command(
            "python scripts/start_nusyq.py error_report --sample",
            cwd=self.nusyq_hub,
            name="error_report (sample mode)",
            category="hub_diagnostics",
            timeout=15,
        )

        # Test 3: Smart search
        self.run_command(
            "python -m src.search.smart_search auth --limit 5",
            cwd=self.nusyq_hub,
            name="SmartSearch: auth",
            category="hub_search",
            timeout=10,
        )

        # Test 4: Quest system
        self.run_command(
            "python -c \"from src.Rosetta_Quest_System import quest_log; print(f'Quests: {len(quest_log.get_active())}')\"",
            cwd=self.nusyq_hub,
            name="Quest system check",
            category="hub_quests",
            timeout=10,
        )

        # Test 5: Import health
        self.run_command(
            "python src/utils/quick_import_fix.py --scan --report",
            cwd=self.nusyq_hub,
            name="Import health check",
            category="hub_imports",
            timeout=15,
        )

    def test_nusyq_root(self):
        """Test NuSyQ Root (MCP Server, Context, etc.)"""
        print("\n🧬 NuSyQ Root Tests:")
        print("-" * 70)

        # Test 1: Check venv
        self.run_command(
            "python --version",
            cwd=self.nusyq_root,
            name="Python version check",
            category="root_env",
            timeout=5,
        )

        # Test 2: MCP help
        self.run_command(
            "python mcp_server/main.py --help",
            cwd=self.nusyq_root,
            name="MCP Server --help",
            category="root_mcp",
            timeout=5,
        )

        # Test 3: Context manager
        self.run_command(
            "python -c \"from src.tools.agent_context_manager import AgentContextManager; print('OK')\"",
            cwd=self.nusyq_root,
            name="Context manager import",
            category="root_context",
            timeout=10,
        )

    def test_simulated_verse(self):
        """Test SimulatedVerse"""
        print("\n🎮 SimulatedVerse Tests:")
        print("-" * 70)

        # Test 1: Check package.json
        package_json = self.simulated_verse / "SimulatedVerse" / "package.json"
        if package_json.exists():
            print("✅ package.json exists")
            test_result = TestResult(
                name="package.json exists",
                category="simverse_structure",
                command="Path.exists(package.json)",
                success=True,
            )
            self.results.append(test_result)

    def test_syntax_validation(self):
        """Validate Python syntax across repos"""
        print("\n🔍 Syntax Validation:")
        print("-" * 70)

        py_files = [
            self.nusyq_hub / "src" / "orchestration" / "multi_ai_orchestrator.py",
            self.nusyq_hub / "src" / "tools" / "agent_task_router.py",
            self.nusyq_hub / "src" / "search" / "smart_search.py",
            self.nusyq_root / "mcp_server" / "main.py",
        ]

        for py_file in py_files:
            if py_file.exists():
                self.test_python_syntax(py_file, name=f"Syntax: {py_file.name}", category="syntax_validation")

    def test_key_scripts(self):
        """Test key scripts in each repo"""
        print("\n⚙️  Key Scripts:")
        print("-" * 70)

        scripts = [
            (self.nusyq_hub / "scripts" / "start_nusyq.py", "start_nusyq.py", "scripts"),
            (self.nusyq_hub / "scripts" / "lint_test_check.py", "lint_test_check.py", "scripts"),
        ]

        for script_path, script_name, category in scripts:
            if script_path.exists():
                self.test_python_syntax(script_path, name=f"Syntax: {script_name}", category=f"script_{category}")

    def generate_report(self):
        """Generate validation report"""
        print("\n" + "=" * 70)
        print("📊 VALIDATION REPORT SUMMARY")
        print("=" * 70)

        # Count by category
        by_category = {}
        for result in self.results:
            if result.category not in by_category:
                by_category[result.category] = {"passed": 0, "failed": 0}
            if result.success:
                by_category[result.category]["passed"] += 1
            else:
                by_category[result.category]["failed"] += 1

        # Print summary
        total_passed = sum(1 for r in self.results if r.success)
        total_failed = sum(1 for r in self.results if not r.success)

        print(f"\n📈 Overall: {total_passed}✅ / {total_failed}❌ ({len(self.results)} tests)")

        print("\n📋 By Category:")
        for category in sorted(by_category.keys()):
            stats = by_category[category]
            total = stats["passed"] + stats["failed"]
            pct = (stats["passed"] / total * 100) if total > 0 else 0
            print(f"  {category:20} {stats['passed']:2}✅ {stats['failed']:2}❌ ({pct:5.1f}%)")

        # Failures detail
        failures = [r for r in self.results if not r.success]
        if failures:
            print("\n⚠️  FAILURES:")
            for result in failures:
                print(f"  ❌ {result.name}")
                if result.error:
                    print(f"     {result.error[:80]}")

        self.report["summary"] = {
            "total": len(self.results),
            "passed": total_passed,
            "failed": total_failed,
            "by_category": by_category,
        }
        self.report["tests"] = [asdict(r) for r in self.results]

        return self.report

    def run_all_tests(self):
        """Execute all tests"""
        print("🚀 NuSyQ ECOSYSTEM VALIDATION SUITE")
        print("=" * 70)

        self.test_repo_structure()
        self.test_nusyq_hub()
        self.test_nusyq_root()
        self.test_simulated_verse()
        self.test_syntax_validation()
        self.test_key_scripts()

        report = self.generate_report()

        # Save report
        report_path = self.nusyq_hub / "ecosystem_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Report saved to: {report_path}")

        return report


if __name__ == "__main__":
    validator = EcosystemValidator()
    report = validator.run_all_tests()

    # Exit with error code if any tests failed
    sys.exit(0 if report["summary"]["failed"] == 0 else 1)
