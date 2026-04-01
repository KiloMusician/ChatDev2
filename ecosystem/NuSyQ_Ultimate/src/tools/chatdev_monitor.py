"""ChatDev Real-Time Monitoring & Observability System"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ChatDevMonitor:
    """Monitor ChatDev task execution with real-time status updates."""

    def __init__(self, warehouse_root: str = None):
        if warehouse_root is None:
            warehouse_root = r"C:\Users\keath\NuSyQ\ChatDev\WareHouse"

        self.warehouse_root = Path(warehouse_root)
        self.status_log = []
        self.project_dirs = {}

    def _get_project_status(self, project_path: Path) -> Dict:
        """Get detailed status of a ChatDev project."""
        status = {
            "name": project_path.name,
            "path": str(project_path),
            "created": project_path.stat().st_ctime,
            "modified": project_path.stat().st_mtime,
            "files": {},
            "has_code": False,
            "has_tests": False,
            "has_docs": False,
            "file_count": 0,
            "total_lines": 0,
        }

        # Analyze files
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                status["file_count"] += 1

                if file_path.suffix == ".py":
                    try:
                        with open(file_path, "r") as f:
                            lines = len(f.readlines())
                            status["total_lines"] += lines
                            name = file_path.name
                            status["files"][name] = {
                                "type": "python",
                                "lines": lines,
                                "size_kb": file_path.stat().st_size / 1024,
                            }

                            if "test" in name.lower():
                                status["has_tests"] = True
                            else:
                                status["has_code"] = True
                    except (OSError, UnicodeDecodeError):
                        pass

                elif file_path.suffix in [".md", ".txt"]:
                    status["has_docs"] = True
                    status["files"][file_path.name] = {
                        "type": "docs",
                        "size_kb": file_path.stat().st_size / 1024,
                    }

        return status

    def get_latest_projects(self, count: int = 5) -> List[Dict]:
        """Get latest N ChatDev projects with status."""
        if not self.warehouse_root.exists():
            return []

        projects = sorted(
            self.warehouse_root.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True
        )[:count]

        results = []
        for proj in projects:
            if proj.is_dir():
                status = self._get_project_status(proj)
                results.append(status)

        return results

    def find_consolidation_tasks(self) -> List[Dict]:
        """Find all Consolidate_6_ChatDev projects with status."""
        tasks = []

        if not self.warehouse_root.exists():
            return tasks

        for proj_dir in self.warehouse_root.iterdir():
            if "Consolidate_6_ChatDev" in proj_dir.name:
                status = self._get_project_status(proj_dir)
                tasks.append(status)

        return sorted(tasks, key=lambda x: x["modified"], reverse=True)

    def check_process_running(self, process_name: str = "run_ollama.py") -> Optional[Dict]:
        """Check if ChatDev main process is running."""
        try:
            result = subprocess.run(
                ["Get-CimInstance", "Win32_Process"],
                capture_output=True,
                text=True,
                shell=True,
                check=False,
            )

            for line in result.stdout.split("\n"):
                if process_name in line:
                    return {
                        "running": True,
                        "process_name": process_name,
                        "line": line.strip(),
                    }

            return {"running": False, "process_name": process_name}
        except (subprocess.SubprocessError, OSError, ValueError, TypeError) as e:
            return {"running": False, "error": str(e)}

    def validate_generated_code(self, project_path: Path) -> Dict:
        """Validate Python code quality of generated files."""
        validation = {
            "project": project_path.name,
            "syntax_errors": [],
            "import_errors": [],
            "python_files": [],
            "is_valid": True,
        }

        python_files = list(project_path.rglob("*.py"))

        for py_file in python_files:
            try:
                with open(py_file, "r") as f:
                    code = f.read()

                # Try to compile
                compile(code, py_file.name, "exec")
                validation["python_files"].append(
                    {"file": py_file.name, "status": "✓ Valid syntax"}
                )
            except SyntaxError as e:
                validation["syntax_errors"].append({"file": py_file.name, "error": str(e)})
                validation["is_valid"] = False
            except (OSError, UnicodeDecodeError, ValueError, TypeError) as e:
                validation["import_errors"].append({"file": py_file.name, "error": str(e)})

        return validation

    def test_generated_code(self, project_path: Path) -> Dict:
        """Run tests on generated code."""
        results = {
            "project": project_path.name,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_files": [],
        }

        # Find test files
        test_files = list(project_path.rglob("test*.py")) + list(project_path.rglob("*test.py"))

        for test_file in test_files:
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", str(test_file), "-v"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )

                results["test_files"].append(
                    {
                        "file": test_file.name,
                        "passed": result.returncode == 0,
                        "output": result.stdout[:500],  # First 500 chars
                    }
                )

                if result.returncode == 0:
                    results["tests_passed"] += 1
                else:
                    results["tests_failed"] += 1

                results["tests_run"] += 1
            except subprocess.TimeoutExpired:
                results["test_files"].append(
                    {"file": test_file.name, "passed": False, "error": "Test timeout"}
                )
                results["tests_failed"] += 1
                results["tests_run"] += 1
            except (subprocess.SubprocessError, OSError, ValueError, TypeError) as e:
                results["test_files"].append(
                    {"file": test_file.name, "passed": False, "error": str(e)}
                )
                results["tests_failed"] += 1
                results["tests_run"] += 1

        return results

    def generate_status_report(self) -> str:
        """Generate comprehensive status report."""
        report = []
        report.append("=" * 80)
        report.append("CHATDEV REAL-TIME STATUS REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)

        # Process status
        report.append("\n[1] PROCESS STATUS")
        process_status = self.check_process_running()
        if process_status["running"]:
            report.append("✓ ChatDev consolidation task: RUNNING")
        else:
            report.append("✗ ChatDev consolidation task: NOT RUNNING")

        # Latest projects
        report.append("\n[2] LATEST PROJECTS (Top 5)")
        projects = self.get_latest_projects(5)
        for i, proj in enumerate(projects, 1):
            mod_time = datetime.fromtimestamp(proj["modified"]).strftime("%Y-%m-%d %H:%M:%S")
            report.append(f"\n  {i}. {proj['name']}")
            report.append(f"     Modified: {mod_time}")
            report.append(f"     Files: {proj['file_count']} | Lines: {proj['total_lines']}")
            report.append(
                f"     Has Code: {proj['has_code']} | Tests: {proj['has_tests']} | Docs: {proj['has_docs']}"
            )

        # Consolidation tasks
        report.append("\n[3] CONSOLIDATION TASKS")
        tasks = self.find_consolidation_tasks()
        if tasks:
            for task in tasks[:3]:  # Show last 3
                mod_time = datetime.fromtimestamp(task["modified"]).strftime("%Y-%m-%d %H:%M:%S")
                report.append(f"\n  {task['name']}")
                report.append(f"    Modified: {mod_time}")
                report.append(
                    f"    Code: {task['total_lines']} lines | Files: {task['file_count']}"
                )

                # Show key files
                if task["files"]:
                    report.append("    Key Files:")
                    for fname in list(task["files"].keys())[:5]:
                        finfo = task["files"][fname]
                        if finfo["type"] == "python":
                            report.append(
                                f"      - {fname}: {finfo['lines']} lines ({finfo['size_kb']:.1f} KB)"
                            )
                        else:
                            report.append(f"      - {fname}: ({finfo['size_kb']:.1f} KB)")
        else:
            report.append("  No consolidation tasks found")

        report.append("\n" + "=" * 80)
        return "\n".join(report)


def main():
    """Main observability dashboard."""
    monitor = ChatDevMonitor()

    # Generate and print report
    print(monitor.generate_status_report())

    # Check latest consolidation project
    tasks = monitor.find_consolidation_tasks()
    if tasks:
        latest = tasks[0]
        print(f"\n[ANALYSIS] Latest consolidation task: {latest['name']}")

        # Validate code
        project_path = Path(latest["path"])
        validation = monitor.validate_generated_code(project_path)

        print("\n[CODE VALIDATION]")
        print(f"  Python files: {len(validation['python_files'])}")
        print(f"  Syntax errors: {len(validation['syntax_errors'])}")
        print(f"  Status: {'✓ VALID' if validation['is_valid'] else '✗ INVALID'}")

        # Try to run tests
        if validation["is_valid"]:
            print("\n[RUNNING TESTS]")
            test_results = monitor.test_generated_code(project_path)
            print(f"  Tests run: {test_results['tests_run']}")
            print(f"  Passed: {test_results['tests_passed']}")
            print(f"  Failed: {test_results['tests_failed']}")


if __name__ == "__main__":
    main()
