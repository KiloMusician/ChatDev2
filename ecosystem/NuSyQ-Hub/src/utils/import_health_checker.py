# Systematic import validation tool

"""KILO-FOOLISH Import Health Checker.

Systematically validates and fixes all import statements across the repository.
"""

import ast
import importlib
import json
import logging
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Optional structured logging utilities
try:
    from src.observability.structured_logging import (get_import_logger,
                                                      rate_limited_log,
                                                      setup_logger)
except ImportError:
    get_import_logger = None
    rate_limited_log = None
    setup_logger = None

LOG_FORMAT = os.getenv("NUSYG_LOG_FORMAT", "human")
LOG_FILE = os.getenv("NUSYG_IMPORT_LOG_FILE")

if setup_logger and LOG_FILE:
    IMPORT_LOGGER = setup_logger(
        "nusyq.imports",
        level=logging.WARNING,
        log_format=LOG_FORMAT,
        log_file=LOG_FILE,
    )
elif get_import_logger:
    IMPORT_LOGGER = get_import_logger(log_format=LOG_FORMAT)
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("import_health_check.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    IMPORT_LOGGER = logging.getLogger(__name__)


@dataclass
class ImportIssue:
    """Represents an import issue found in the codebase."""

    file_path: str
    line_number: int
    import_statement: str
    module_name: str
    issue_type: str
    suggestion: str
    severity: str


@dataclass
class ImportAnalysis:
    """Results of import analysis."""

    total_files: int
    total_imports: int
    successful_imports: int
    failed_imports: int
    issues: list[ImportIssue]
    missing_packages: set[str]
    broken_relative_imports: list[str]


class ImportHealthChecker:
    """Comprehensive import health checking system."""

    def __init__(self, repository_root: str) -> None:
        """Initialize ImportHealthChecker with repository_root."""
        self.repository_root = Path(repository_root)
        self.python_files: list[Path] = []
        self.issues: list[dict[str, Any]] = []
        self.missing_packages: set[str] = set()
        self.installed_packages: set[str] = set()
        self.standard_library: set[str] = set()
        self.local_modules: set[str] = set()

        # Initialize package information
        self._load_installed_packages()
        self._load_standard_library()
        self._discover_local_modules()

    def _load_installed_packages(self) -> None:
        """Load list of installed packages."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in result.stdout.strip().split("\n"):
                if "==" in line:
                    package_name = line.split("==")[0].lower().replace("-", "_")
                    self.installed_packages.add(package_name)
        except subprocess.CalledProcessError:
            logging.warning("Could not load installed packages list")

    def _load_standard_library(self) -> None:
        """Load Python standard library modules."""
        # Common standard library modules
        stdlib_modules = {
            "os",
            "sys",
            "json",
            "csv",
            "xml",
            "html",
            "urllib",
            "http",
            "email",
            "datetime",
            "time",
            "calendar",
            "collections",
            "itertools",
            "functools",
            "operator",
            "re",
            "string",
            "io",
            "pathlib",
            "glob",
            "tempfile",
            "shutil",
            "subprocess",
            "threading",
            "multiprocessing",
            "concurrent",
            "asyncio",
            "queue",
            "logging",
            "warnings",
            "traceback",
            "pdb",
            "unittest",
            "doctest",
            "argparse",
            "configparser",
            "getpass",
            "socket",
            "ssl",
            "hashlib",
            "hmac",
            "secrets",
            "uuid",
            "random",
            "statistics",
            "math",
            "decimal",
            "fractions",
            "cmath",
            "numbers",
            "array",
            "struct",
            "codecs",
            "unicodedata",
            "stringprep",
            "readline",
            "rlcompleter",
            "pickle",
            "copyreg",
            "shelve",
            "marshal",
            "dbm",
            "sqlite3",
            "zlib",
            "gzip",
            "bz2",
            "lzma",
            "zipfile",
            "tarfile",
        }
        self.standard_library.update(stdlib_modules)

    def _discover_local_modules(self) -> None:
        """Discover local Python modules in the repository."""
        for py_file in self.repository_root.rglob("*.py"):
            if not any(part.startswith(".") for part in py_file.parts):
                # Get module name from file path
                relative_path = py_file.relative_to(self.repository_root)
                module_path = str(relative_path.with_suffix(""))
                module_name = module_path.replace(os.sep, ".")
                self.local_modules.add(module_name)

                # Also add package names
                parts = module_path.split(os.sep)
                for i in range(len(parts)):
                    package_name = ".".join(parts[: i + 1])
                    self.local_modules.add(package_name)

    def discover_python_files(self) -> list[Path]:
        """Discover all Python files in the repository."""
        python_files: list[Any] = []
        # Patterns to exclude
        exclude_patterns = {
            ".git",
            "__pycache__",
            "venv",
            "venv_kilo",
            ".vscode",
            "node_modules",
            "dist",
            "build",
            ".pytest_cache",
        }

        for py_file in self.repository_root.rglob("*.py"):
            # Check if file should be excluded
            if not any(excluded in str(py_file) for excluded in exclude_patterns):
                python_files.append(py_file)

        self.python_files = python_files
        IMPORT_LOGGER.info("Discovered %d Python files", len(python_files))
        return python_files

    def parse_imports_from_file(self, file_path: Path) -> list[tuple[int, str, str]]:
        """Parse all import statements from a Python file."""
        imports: list[Any] = []
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse with AST
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append((node.lineno, f"import {alias.name}", alias.name))
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        level = node.level
                        if level > 0:
                            # Relative import
                            module = "." * level + module
                        for alias in node.names:
                            stmt = f"from {module} import {alias.name}"
                            imports.append((node.lineno, stmt, module))
            except SyntaxError as e:
                logging.exception(f"Syntax error in {file_path}: {e}")
                # Fallback to regex parsing
                imports.extend(self._regex_parse_imports(content, file_path))

        except Exception as e:
            logging.exception(f"Error reading {file_path}: {e}")

        return imports

    def _regex_parse_imports(self, content: str, _file_path: Path) -> list[tuple[int, str, str]]:
        """Fallback regex-based import parsing."""
        imports: list[Any] = []
        lines = content.split("\n")

        for line_no, line in enumerate(lines, 1):
            line = line.strip()

            # Match import statements
            import_match = re.match(r"^import\s+([^\s#]+)", line)
            if import_match:
                module = import_match.group(1)
                imports.append((line_no, line, module))
                continue

            # Match from...import statements
            from_match = re.match(r"^from\s+([^\s]+)\s+import", line)
            if from_match:
                module = from_match.group(1)
                imports.append((line_no, line, module))

        return imports

    def validate_import(self, module_name: str, file_path: Path) -> tuple[bool, str]:
        """Validate if an import can be resolved."""
        # Handle relative imports
        if module_name.startswith("."):
            return self._validate_relative_import(module_name, file_path)

        # Check standard library
        if module_name in self.standard_library:
            return True, "standard_library"

        # Check installed packages
        base_module = module_name.split(".")[0]
        if base_module in self.installed_packages:
            return True, "installed_package"

        # Check local modules
        if module_name in self.local_modules:
            return True, "local_module"

        # Try dynamic import
        try:
            importlib.import_module(module_name)
            return True, "dynamic_import"
        except ImportError:
            pass

        return False, "not_found"

    def _validate_relative_import(self, module_name: str, file_path: Path) -> tuple[bool, str]:
        """Validate relative imports."""
        try:
            # Calculate the package context
            relative_path = file_path.relative_to(self.repository_root)
            package_parts = list(relative_path.parent.parts)

            # Handle the relative import levels
            level = len(module_name) - len(module_name.lstrip("."))
            module_part = module_name.lstrip(".")

            if level > len(package_parts):
                return False, "relative_import_too_high"

            # Build the absolute module name
            target_package = package_parts[:-level] if level > 0 else package_parts
            if module_part:
                target_package.append(module_part)

            ".".join(target_package)

            # Check if the target exists
            target_path = self.repository_root
            for part in target_package:
                target_path = target_path / part

            if target_path.with_suffix(".py").exists() or (target_path / "__init__.py").exists():
                return True, "relative_import_valid"

            return False, "relative_import_target_missing"

        except (ValueError, OSError, AttributeError):
            return False, "relative_import_error"

    def suggest_fix(self, module_name: str, issue_type: str) -> str:
        """Suggest a fix for import issues."""
        suggestions = {
            "not_found": f"Install package: pip install {module_name}",
            "relative_import_too_high": "Reduce relative import levels or use absolute import",
            "relative_import_target_missing": "Create missing module or fix import path",
            "relative_import_error": "Check relative import syntax",
            "syntax_error": "Fix syntax error in import statement",
        }

        # Check for common package name mappings
        package_mappings = {
            "cv2": "opencv-python",
            "PIL": "Pillow",
            "sklearn": "scikit-learn",
            "yaml": "PyYAML",
            "dateutil": "python-dateutil",
            "psutil": "psutil",
            "requests": "requests",
            "bs4": "beautifulsoup4",
            "jwt": "PyJWT",
        }

        if issue_type == "not_found" and module_name in package_mappings:
            return f"Install package: pip install {package_mappings[module_name]}"

        return suggestions.get(issue_type, "Manual review required")

    def check_file(self, file_path: Path) -> list[ImportIssue]:
        """Check all imports in a single file."""
        issues: list[Any] = []
        imports = self.parse_imports_from_file(file_path)

        for line_no, import_stmt, module_name in imports:
            is_valid, validation_type = self.validate_import(module_name, file_path)

            if not is_valid:
                severity = "HIGH" if validation_type in ["not_found", "syntax_error"] else "MEDIUM"

                issue = ImportIssue(
                    file_path=str(file_path.relative_to(self.repository_root)),
                    line_number=line_no,
                    import_statement=import_stmt,
                    module_name=module_name,
                    issue_type=validation_type,
                    suggestion=self.suggest_fix(module_name, validation_type),
                    severity=severity,
                )
                issues.append(issue)

                # Track missing packages
                if validation_type == "not_found":
                    self.missing_packages.add(module_name.split(".")[0])

        return issues

    def check_all_files(self) -> ImportAnalysis:
        """Check all Python files in the repository."""
        IMPORT_LOGGER.info("Starting comprehensive import health check...")

        if not self.python_files:
            self.discover_python_files()

        all_issues: list[Any] = []
        total_imports = 0
        successful_imports = 0
        failed_imports = 0
        rate_limit_seconds = float(os.getenv("NUSYG_IMPORT_LOG_RATE_SECONDS", "5"))
        log_every_raw = os.getenv("NUSYG_IMPORT_LOG_EVERY", "50")
        log_each_raw = os.getenv("NUSYG_IMPORT_LOG_EACH_FILE", "0")
        try:
            log_every = int(log_every_raw)
        except ValueError:
            log_every = 50
        log_each = log_each_raw.strip().lower() in ("1", "true", "yes")
        total_files = len(self.python_files)

        for index, file_path in enumerate(self.python_files, start=1):
            relative_path = file_path.relative_to(self.repository_root)
            message = f"Checking imports ({index}/{total_files}): {relative_path}"
            should_log = (
                log_each
                or log_every <= 0
                or index == 1
                or index == total_files
                or (log_every and index % log_every == 0)
            )
            if should_log:
                if rate_limited_log:
                    rate_limited_log(
                        IMPORT_LOGGER,
                        logging.INFO,
                        message,
                        rate_limit_key="import:file-progress",
                        rate_limit_seconds=rate_limit_seconds,
                        extra={"file": str(relative_path), "index": index, "total": total_files},
                    )
                else:
                    IMPORT_LOGGER.info(message)

            file_issues = self.check_file(file_path)
            all_issues.extend(file_issues)

            # Count imports
            imports = self.parse_imports_from_file(file_path)
            total_imports += len(imports)
            failed_imports += len(file_issues)
            successful_imports += len(imports) - len(file_issues)

        analysis = ImportAnalysis(
            total_files=len(self.python_files),
            total_imports=total_imports,
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            issues=all_issues,
            missing_packages=self.missing_packages,
            broken_relative_imports=[
                issue.file_path for issue in all_issues if "relative" in issue.issue_type
            ],
        )

        IMPORT_LOGGER.info(
            "Import health check complete: %d/%d imports successful",
            successful_imports,
            total_imports,
        )
        return analysis

    def generate_requirements_txt(self, output_path: str = "requirements_missing.txt") -> None:
        """Generate requirements.txt for missing packages."""
        if not self.missing_packages:
            logging.info("No missing packages found")
            return

        requirements_content: list[Any] = []
        package_mappings = {
            "cv2": "opencv-python",
            "PIL": "Pillow",
            "sklearn": "scikit-learn",
            "yaml": "PyYAML",
            "dateutil": "python-dateutil",
        }

        for package in sorted(self.missing_packages):
            pip_name = package_mappings.get(package, package)
            requirements_content.append(pip_name)

        with open(output_path, "w") as f:
            f.write("\n".join(requirements_content))

        logging.info(f"Generated {output_path} with {len(requirements_content)} missing packages")

    def generate_report(
        self, analysis: ImportAnalysis, output_path: str = "import_health_report.json"
    ) -> dict[str, Any]:
        """Generate comprehensive report."""
        # Group issues by severity and type
        issues_by_severity = defaultdict(list)
        issues_by_type = defaultdict(list)

        for issue in analysis.issues:
            issues_by_severity[issue.severity].append(issue)
            issues_by_type[issue.issue_type].append(issue)

        report = {
            "summary": {
                "total_files": analysis.total_files,
                "total_imports": analysis.total_imports,
                "successful_imports": analysis.successful_imports,
                "failed_imports": analysis.failed_imports,
                "success_rate": (
                    analysis.successful_imports / analysis.total_imports
                    if analysis.total_imports > 0
                    else 0
                ),
            },
            "issues_by_severity": {
                severity: len(issues) for severity, issues in issues_by_severity.items()
            },
            "issues_by_type": {
                issue_type: len(issues) for issue_type, issues in issues_by_type.items()
            },
            "missing_packages": list(analysis.missing_packages),
            "detailed_issues": [
                {
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "statement": issue.import_statement,
                    "module": issue.module_name,
                    "type": issue.issue_type,
                    "suggestion": issue.suggestion,
                    "severity": issue.severity,
                }
                for issue in analysis.issues
            ],
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logging.info(f"Generated detailed report: {output_path}")
        return report

    def auto_fix_issues(self, analysis: ImportAnalysis, dry_run: bool = True) -> int:
        """Automatically fix common import issues."""
        logging.info(f"Auto-fixing issues (dry_run={dry_run})")

        fixes_applied = 0

        for issue in analysis.issues:
            if issue.issue_type == "not_found":
                # Try to install missing package
                package_name = issue.module_name.split(".")[0]

                if not dry_run:
                    try:
                        subprocess.run(
                            [sys.executable, "-m", "pip", "install", package_name],
                            check=True,
                            capture_output=True,
                        )
                        logging.info(f"Installed package: {package_name}")
                        fixes_applied += 1
                    except subprocess.CalledProcessError:
                        logging.warning(f"Failed to install package: {package_name}")
                else:
                    logging.info(f"Would install package: {package_name}")
                    fixes_applied += 1

        logging.info(
            f"Auto-fix complete: {fixes_applied} fixes {'applied' if not dry_run else 'would be applied'}"
        )
        return fixes_applied


def main() -> None:
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="KILO-FOOLISH Import Health Checker")
    parser.add_argument("--repository", "-r", default=".", help="Repository root path")
    parser.add_argument("--fix", action="store_true", help="Automatically fix issues")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without applying",
    )
    parser.add_argument(
        "--generate-requirements",
        action="store_true",
        help="Generate requirements.txt for missing packages",
    )
    parser.add_argument("--output-dir", default=".", help="Output directory for reports")

    args = parser.parse_args()

    # Initialize checker
    checker = ImportHealthChecker(args.repository)

    # Run comprehensive check
    analysis = checker.check_all_files()

    # Generate reports
    output_dir = Path(args.output_dir)
    report_path = output_dir / "import_health_report.json"
    checker.generate_report(analysis, str(report_path))

    if args.generate_requirements:
        requirements_path = output_dir / "requirements_missing.txt"
        checker.generate_requirements_txt(str(requirements_path))

    # Auto-fix if requested
    if args.fix or args.dry_run:
        checker.auto_fix_issues(analysis, dry_run=args.dry_run or not args.fix)

    # Print summary

    if analysis.issues:
        for _issue in analysis.issues[:10]:  # Show first 10 issues
            pass
        if len(analysis.issues) > 10:
            pass


if __name__ == "__main__":
    main()
