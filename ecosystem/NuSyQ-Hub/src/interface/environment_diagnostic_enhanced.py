"""KILO-FOOLISH Environment Diagnostic & Recovery System.

Enhanced PATH detection, module verification, and auto-healing capabilities
Integrates with the Copilot Enhancement Bridge for intelligent diagnostics.
"""

import importlib
import json
import logging
import os
import platform
import subprocess
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticResult:
    """Structured diagnostic result."""

    category: str
    status: str  # 'OK', 'WARNING', 'ERROR', 'CRITICAL'
    message: str
    details: dict[str, Any] | None = None
    fix_command: str | None = None
    confidence: float = 1.0


class KILOEnvironmentDiagnostic:
    """Advanced environment diagnostic and recovery system."""

    def __init__(self) -> None:
        """Initialize KILOEnvironmentDiagnostic."""
        self.results: list[DiagnosticResult] = []
        self.environment_data: dict[str, Any] = {}
        self.start_time = datetime.now()
        self.critical_modules = ["yaml", "requests", "pathlib", "ast", "json"]
        self.kilo_files = [
            "setup.ps1",
            "src",
            "README.md",
            ".git",
            "src/diagnostics/repository_syntax_analyzer.py",
            "src/interface/modular_window_system.js",
        ]

    def _resolve_module_version(self, module_name: str) -> str:
        """Resolve a module's version using importlib.metadata, avoiding pkg_resources."""
        if not module_name:
            return "Unknown"

        try:
            return importlib_metadata.version(module_name)
        except importlib_metadata.PackageNotFoundError:
            try:
                dist_candidates = importlib_metadata.packages_distributions().get(module_name, [])
            except (OSError, ValueError, AttributeError):
                dist_candidates = []
            for dist_name in dist_candidates:
                try:
                    return importlib_metadata.version(dist_name)
                except importlib_metadata.PackageNotFoundError:
                    continue
        except (OSError, ValueError, AttributeError):
            # metadata backends vary, safe fallback to Unknown
            logger.debug("Suppressed AttributeError/OSError/ValueError", exc_info=True)

        return "Unknown"

    def run_comprehensive_diagnostic(self) -> list[DiagnosticResult]:
        """Run complete system diagnostic."""
        # Core diagnostics
        self._check_python_environment()
        self._check_virtual_environment()
        self._check_critical_modules()
        self._check_repository_structure()
        self._check_file_integrity()
        self._check_path_variables()
        self._check_git_status()
        self._check_system_resources()
        self._analyze_recent_changes()
        self._perform_predictive_analysis()

        # Advanced diagnostics
        self._check_dependency_conflicts()
        self._verify_module_versions()
        self._analyze_import_paths()
        self._check_permissions()
        self._validate_configuration_files()

        # Recovery suggestions
        self._generate_recovery_plan()

        return self.results

    def _check_python_environment(self) -> None:
        """Comprehensive Python environment analysis."""
        try:
            python_version = sys.version
            executable = sys.executable
            platform_info = platform.platform()

            self.environment_data["python"] = {
                "version": python_version,
                "executable": executable,
                "platform": platform_info,
                "paths": sys.path[:5],  # First 5 paths
            }

            # Version compatibility check
            version_tuple = sys.version_info
            if version_tuple.major < 3 or (version_tuple.major == 3 and version_tuple.minor < 8):
                self.results.append(
                    DiagnosticResult(
                        "Python Environment",
                        "WARNING",
                        f"Python {version_tuple.major}.{version_tuple.minor} may have compatibility issues",
                        {
                            "recommended": "3.8+",
                            "current": f"{version_tuple.major}.{version_tuple.minor}",
                        },
                        "Consider upgrading Python",
                    )
                )
            else:
                self.results.append(
                    DiagnosticResult(
                        "Python Environment",
                        "OK",
                        f"Python {version_tuple.major}.{version_tuple.minor}.{version_tuple.micro} - Compatible",
                        {"executable": executable},
                    )
                )

        except (OSError, subprocess.SubprocessError, ValueError) as e:
            self.results.append(
                DiagnosticResult(
                    "Python Environment",
                    "CRITICAL",
                    f"Failed to analyze Python environment: {e!s}",
                    fix_command="Reinstall Python",
                )
            )

    def _check_virtual_environment(self) -> None:
        """Advanced virtual environment detection and analysis."""
        try:
            # Multiple methods to detect virtual environment
            venv_methods = {
                "hasattr_real_prefix": hasattr(sys, "real_prefix"),
                "base_prefix_check": (
                    hasattr(sys, "base_prefix") and (sys.base_prefix != sys.prefix)
                ),
                "virtual_env_var": ("VIRTUAL_ENV" in os.environ),
                "conda_env": ("CONDA_DEFAULT_ENV" in os.environ),
            }

            venv_active = any(venv_methods.values())
            venv_path = os.environ.get("VIRTUAL_ENV", "Not detected")

            self.environment_data["virtual_env"] = {
                "active": venv_active,
                "path": venv_path,
                "detection_methods": venv_methods,
            }

            if venv_active:
                if "venv_kilo" in venv_path or "KILO" in venv_path:
                    self.results.append(
                        DiagnosticResult(
                            "Virtual Environment",
                            "OK",
                            "KILO-FOOLISH virtual environment active",
                            {"path": venv_path},
                        )
                    )
                else:
                    self.results.append(
                        DiagnosticResult(
                            "Virtual Environment",
                            "WARNING",
                            "Virtual environment active but not KILO-specific",
                            {"path": venv_path},
                            "Consider using KILO-FOOLISH specific environment",
                        )
                    )
            else:
                self.results.append(
                    DiagnosticResult(
                        "Virtual Environment",
                        "WARNING",
                        "No virtual environment detected",
                        fix_command="python -m venv venv_kilo && venv_kilo\\Scripts\\activate",
                    )
                )

        except (OSError, ValueError, AttributeError) as e:
            self.results.append(
                DiagnosticResult(
                    "Virtual Environment",
                    "ERROR",
                    f"Virtual environment check failed: {e!s}",
                )
            )

    def _check_critical_modules(self) -> None:
        """Enhanced module availability and version checking."""
        module_status: dict[str, Any] = {}
        for module_name in self.critical_modules:
            try:
                # Try to import the module
                module = importlib.import_module(module_name)  # nosemgrep

                # Get version if available
                version = getattr(module, "__version__", None)
                if not version:
                    version = self._resolve_module_version(module_name)
                if not version:
                    version = "Unknown"

                module_status[module_name] = {
                    "status": "OK",
                    "version": version,
                    "location": getattr(module, "__file__", "Built-in"),
                }

                self.results.append(
                    DiagnosticResult(
                        "Module Check",
                        "OK",
                        f"{module_name} available",
                        {"version": version},
                    )
                )

            except ModuleNotFoundError as e:
                module_status[module_name] = {
                    "status": "MISSING",
                    "error": str(e),
                }

                fix_cmd = f"pip install {module_name}"
                if module_name == "yaml":
                    fix_cmd = "pip install PyYAML"

                self.results.append(
                    DiagnosticResult(
                        "Module Check",
                        "ERROR",
                        f"{module_name} not available",
                        {"error": str(e)},
                        fix_cmd,
                    )
                )

            except ImportError as e:
                module_status[module_name] = {
                    "status": "ERROR",
                    "error": str(e),
                }

            except (AttributeError, ValueError) as e:
                module_status[module_name] = {
                    "status": "ERROR",
                    "error": str(e),
                }

        self.environment_data["modules"] = module_status

    def _check_repository_structure(self) -> None:
        """Advanced repository structure validation."""
        cwd = Path.cwd()
        self.environment_data["current_directory"] = str(cwd)

        # Check if we're in KILO-FOOLISH repository
        repo_score = 0
        found_files: dict[str, Any] = {}
        for file_path in self.kilo_files:
            full_path = cwd / file_path
            if full_path.exists():
                repo_score += 1
                found_files[file_path] = str(full_path)
            else:
                found_files[file_path] = "NOT FOUND"

        confidence = repo_score / len(self.kilo_files)

        if confidence > 0.7:
            self.results.append(
                DiagnosticResult(
                    "Repository Structure",
                    "OK",
                    f"KILO-FOOLISH repository detected ({repo_score}/{len(self.kilo_files)} files found)",
                    {"confidence": confidence, "found_files": found_files},
                )
            )
        elif confidence > 0.3:
            self.results.append(
                DiagnosticResult(
                    "Repository Structure",
                    "WARNING",
                    f"Partial KILO-FOOLISH repository ({repo_score}/{len(self.kilo_files)} files found)",
                    {"confidence": confidence, "found_files": found_files},
                    "Navigate to KILO-FOOLISH root directory",
                )
            )
        else:
            self.results.append(
                DiagnosticResult(
                    "Repository Structure",
                    "ERROR",
                    f"KILO-FOOLISH repository not detected ({repo_score}/{len(self.kilo_files)} files found)",
                    {"confidence": confidence, "found_files": found_files},
                    f"cd {Path(os.getenv('KILO_FOOLISH_ROOT', 'KILO-FOOLISH'))}",
                )
            )

    def _check_file_integrity(self) -> None:
        """Check critical files for corruption or syntax errors."""
        critical_files = [
            ("src/diagnostics/repository_syntax_analyzer.py", "python"),
            ("src/interface/modular_window_system.js", "javascript"),
            ("setup.ps1", "powershell"),
        ]

        for file_path, file_type in critical_files:
            full_path = Path.cwd() / file_path
            if full_path.exists():
                try:
                    with open(full_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Basic syntax checks
                    issues = self._basic_syntax_check(content, file_type)

                    if issues:
                        self.results.append(
                            DiagnosticResult(
                                "File Integrity",
                                "WARNING",
                                f"{file_path} has potential syntax issues",
                                {"issues": issues[:3]},  # First 3 issues
                            )
                        )
                    else:
                        self.results.append(
                            DiagnosticResult(
                                "File Integrity",
                                "OK",
                                f"{file_path} appears syntactically correct",
                            )
                        )

                except (OSError, UnicodeDecodeError) as e:
                    self.results.append(
                        DiagnosticResult(
                            "File Integrity",
                            "ERROR",
                            f"Cannot read {file_path}: {e!s}",
                        )
                    )
            else:
                pass

    def _basic_syntax_check(self, content: str, file_type: str) -> list[str]:
        """Basic syntax checking for different file types."""
        issues: list[Any] = []
        lines = content.split("\n")

        if file_type == "python":
            # Check for basic Python syntax issues
            try:
                compile(content, "<string>", "exec")
            except SyntaxError as e:
                issues.append(f"Python syntax error at line {e.lineno}: {e.msg}")

        elif file_type == "powershell":
            # Check for common PowerShell issues
            brace_count = content.count("{") - content.count("}")
            if brace_count != 0:
                issues.append(
                    f"Unmatched braces: {abs(brace_count)} {'opening' if brace_count > 0 else 'closing'}"
                )

            # Check for pipe operator issues
            for i, line in enumerate(lines, 1):
                if "| Start-Process" in line:
                    issues.append(f"Line {i}: Use '&' instead of '| Start-Process'")

        elif file_type == "javascript":
            # Basic JavaScript checks
            brace_count = content.count("{") - content.count("}")
            if brace_count != 0:
                issues.append(f"Unmatched braces: {abs(brace_count)}")

            paren_count = content.count("(") - content.count(")")
            if paren_count != 0:
                issues.append(f"Unmatched parentheses: {abs(paren_count)}")

        return issues

    def _check_path_variables(self) -> None:
        """Analyze PATH and environment variables."""
        path_var = os.environ.get("PATH", "")
        python_paths = [p for p in path_var.split(os.pathsep) if "python" in p.lower()]

        self.environment_data["path_analysis"] = {
            "total_paths": len(path_var.split(os.pathsep)),
            "python_paths": python_paths,
            "venv_in_path": any("venv" in p for p in python_paths),
        }

        if python_paths:
            pass

        # Check for common issues
        if len(python_paths) > 3:
            self.results.append(
                DiagnosticResult(
                    "PATH Analysis",
                    "WARNING",
                    f"Multiple Python installations detected ({len(python_paths)})",
                    {"paths": python_paths[:3]},
                    "Consider cleaning up PATH",
                )
            )

    def _check_git_status(self) -> None:
        """Check Git repository status."""
        try:
            # Check if git is available
            result = subprocess.run(
                ["git", "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Check repository status
                status_result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if status_result.returncode == 0:
                    modified_files = (
                        len(status_result.stdout.strip().split("\n"))
                        if status_result.stdout.strip()
                        else 0
                    )

                    self.environment_data["git"] = {
                        "available": True,
                        "modified_files": modified_files,
                    }

                    if modified_files > 0:
                        self.results.append(
                            DiagnosticResult(
                                "Git Status",
                                "INFO",
                                f"{modified_files} modified files in repository",
                                fix_command="git status",
                            )
                        )
                else:
                    pass
            else:
                pass

        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("Suppressed FileNotFoundError/subprocess", exc_info=True)

    def _check_system_resources(self) -> None:
        """Check system resources and performance."""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(".")

            self.environment_data["system_resources"] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
            }

            if memory.percent > 80:
                self.results.append(
                    DiagnosticResult(
                        "System Resources",
                        "WARNING",
                        f"High memory usage: {memory.percent:.1f}%",
                    )
                )

        except ImportError:
            pass

    def _analyze_recent_changes(self) -> None:
        """Analyze recent file changes."""
        try:
            # Check modification times of critical files
            recent_changes: list[Any] = []
            now = datetime.now()

            for file_path in [
                "src/diagnostics/repository_syntax_analyzer.py",
                "src/interface/modular_window_system.js",
            ]:
                full_path = Path.cwd() / file_path
                if full_path.exists():
                    mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                    age_hours = (now - mtime).total_seconds() / 3600

                    if age_hours < 24:  # Modified in last 24 hours
                        recent_changes.append(
                            {
                                "file": file_path,
                                "modified": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                                "hours_ago": age_hours,
                            }
                        )

            if recent_changes:
                for _change in recent_changes:
                    pass

                self.environment_data["recent_changes"] = recent_changes

        except (OSError, subprocess.SubprocessError, AttributeError):
            logger.debug("Suppressed AttributeError/OSError/subprocess", exc_info=True)

    def _perform_predictive_analysis(self) -> None:
        """Predictive analysis for potential issues."""
        predictions: list[Any] = []
        # Predict issues based on current state
        if self.environment_data.get("modules", {}).get("yaml", {}).get("status") == "MISSING":
            predictions.append("Repository syntax analyzer will fail without PyYAML")

        if not any(r.status == "OK" and r.category == "Repository Structure" for r in self.results):
            predictions.append("File operations may fail outside KILO-FOOLISH directory")

        if predictions:
            for _pred in predictions:
                pass

    def _check_dependency_conflicts(self) -> None:
        """Check for package dependency conflicts."""
        try:
            installed_packages = set()
            for dist in importlib_metadata.distributions():
                name = dist.metadata["Name"]
                if name:
                    installed_packages.add(name.lower())
            package_map = importlib_metadata.packages_distributions()
            conflicts: list[Any] = []
            # Check for known problematic combinations
            if package_map.get("yaml") and "pyyaml" in installed_packages:
                conflicts.append("Both 'yaml' and 'pyyaml' packages detected")

            if conflicts:
                self.results.append(
                    DiagnosticResult(
                        "Dependency Check",
                        "WARNING",
                        "Potential package conflicts detected",
                        {"conflicts": conflicts},
                    )
                )

        except (AttributeError, ImportError, subprocess.SubprocessError):
            logger.debug("Suppressed AttributeError/ImportError/subprocess", exc_info=True)

    def _verify_module_versions(self) -> None:
        """Verify module versions for compatibility."""
        # Implementation would check actual versions against requirements

    def _analyze_import_paths(self) -> None:
        """Analyze Python import paths for issues."""
        problematic_paths: list[Any] = []
        for path in sys.path:
            if not Path(path).exists():
                problematic_paths.append(path)

        if problematic_paths:
            self.results.append(
                DiagnosticResult(
                    "Import Paths",
                    "WARNING",
                    f"{len(problematic_paths)} non-existent paths in sys.path",
                    {"paths": problematic_paths[:3]},
                )
            )

    def _check_permissions(self) -> None:
        """Check file and directory permissions."""
        critical_paths = [
            "src/diagnostics",
            "src/interface",
            ".",
        ]

        permission_issues: list[Any] = []
        for path_str in critical_paths:
            path = Path.cwd() / path_str
            if path.exists() and not os.access(path, os.R_OK | os.W_OK):
                permission_issues.append(path_str)

        if permission_issues:
            self.results.append(
                DiagnosticResult(
                    "Permissions",
                    "WARNING",
                    "Permission issues detected",
                    {"paths": permission_issues},
                )
            )

    def _validate_configuration_files(self) -> None:
        """Validate configuration files."""
        config_files = [
            ("setup.ps1", "powershell"),
            ("requirements.txt", "text"),
        ]

        for file_path, file_type in config_files:
            full_path = Path.cwd() / file_path
            if full_path.exists():
                try:
                    with open(full_path, encoding="utf-8") as f:
                        content = f.read()

                    if file_type == "powershell" and content.count("{") != content.count("}"):
                        self.results.append(
                            DiagnosticResult(
                                "Configuration",
                                "WARNING",
                                f"{file_path} has brace mismatch",
                            )
                        )

                except (OSError, ValueError, KeyError) as e:
                    self.results.append(
                        DiagnosticResult(
                            "Configuration",
                            "ERROR",
                            f"Cannot validate {file_path}: {e!s}",
                        )
                    )

    def _generate_recovery_plan(self) -> None:
        """Generate intelligent recovery suggestions."""
        critical_issues = [r for r in self.results if r.status in ["ERROR", "CRITICAL"]]

        if critical_issues:
            # Prioritize fixes
            for issue in critical_issues[:3]:  # Top 3 critical issues
                if issue.fix_command:
                    pass
        else:
            pass

        # Generate comprehensive fix script
        fix_commands = [r.fix_command for r in self.results if r.fix_command]
        if fix_commands:
            for _cmd in fix_commands[:5]:  # Top 5 fixes
                pass

    def generate_report(self) -> dict:
        """Generate comprehensive diagnostic report."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        return {
            "diagnostic_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total_checks": len(self.results),
            },
            "summary": {
                "ok": len([r for r in self.results if r.status == "OK"]),
                "warnings": len([r for r in self.results if r.status == "WARNING"]),
                "errors": len([r for r in self.results if r.status == "ERROR"]),
                "critical": len([r for r in self.results if r.status == "CRITICAL"]),
            },
            "environment_data": self.environment_data,
            "detailed_results": [
                {
                    "category": r.category,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                    "fix_command": r.fix_command,
                    "confidence": r.confidence,
                }
                for r in self.results
            ],
        }

    def save_report(self, filename: str | None = None) -> str:
        """Save diagnostic report to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kilo_diagnostic_{timestamp}.json"

        report = self.generate_report()

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return filename


def main():
    """Main diagnostic execution."""
    try:
        diagnostic = KILOEnvironmentDiagnostic()
        results = diagnostic.run_comprehensive_diagnostic()

        # Print summary

        summary: dict[str, int] = {}
        for result in results:
            summary[result.status] = summary.get(result.status, 0) + 1

        for status in summary:
            {"OK": "✅", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "🚨"}.get(status, "📊")

        # Save detailed report
        diagnostic.save_report()

        # Quick fixes
        critical_fixes = [
            r.fix_command for r in results if r.status in ["ERROR", "CRITICAL"] and r.fix_command
        ]
        if critical_fixes:
            for _i, _fix in enumerate(critical_fixes[:3], 1):
                pass

        return len([r for r in results if r.status in ["ERROR", "CRITICAL"]]) == 0

    except (KeyboardInterrupt, SystemExit, RuntimeError):
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
