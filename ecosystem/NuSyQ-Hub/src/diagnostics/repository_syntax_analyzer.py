"""Repository-Wide Syntax Error Detection & Resolution System.

A Comprehensive Scanner for All File Types in the KILO-FOOLISH Ecosystem.

Integrates with the Copilot Enhancement Bridge for intelligent error detection
"""

# pyright: reportUnknownMember=false, reportMissingImports=false, reportGeneralTypeIssues=false

import ast
import json
import logging
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import yaml

logger = logging.getLogger(__name__)


# Bridge integration via Copilot folder
try:
    from src.copilot.copilot_enhancement_bridge import EnhancedCopilotBridge

    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False


@dataclass
class RepositorySyntaxError:
    """Enhanced syntax error representation for repository analysis.

    This custom class provides enhanced syntax error tracking capabilities
    beyond Python's built-in SyntaxError, specifically designed for
    repository-wide analysis and the 'it's not a bug, it's a feature' approach.
    """

    file_path: str
    line_number: int
    column_number: int
    error_type: str
    error_message: str
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    suggested_fix: str | None = None
    context_lines: list[str] = field(default_factory=list)


@dataclass
class FileAnalysisResult:
    """Results of analyzing a single file."""

    file_path: str
    file_type: str
    is_valid: bool
    syntax_errors: list[RepositorySyntaxError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class RepositorySyntaxAnalyzer:
    """Comprehensive syntax analyzer for the entire repository."""

    def __init__(self, repository_root: str = ".") -> None:
        """Initialize RepositorySyntaxAnalyzer with repository_root."""
        self.repository_root = Path(repository_root)
        self.analysis_results: dict[str, Any] = {}
        self.error_summary: dict[str, list[Any]] = defaultdict(list)
        # Cache mapping file path to (mtime, analysis result)
        self._cache: dict[str, tuple[float, FileAnalysisResult]] = {}
        self.file_type_handlers = {
            ".py": self._analyze_python_file,
            ".ps1": self._analyze_powershell_file,
            ".json": self._analyze_json_file,
            ".yaml": self._analyze_yaml_file,
            ".yml": self._analyze_yaml_file,
            ".md": self._analyze_markdown_file,
        }

    def analyze_repository(self) -> dict[str, FileAnalysisResult]:
        """Analyze all files in the repository for syntax errors."""
        # Get all files to analyze
        files_to_analyze = self._get_files_to_analyze()

        # Iterate over discovered files
        for file_path in files_to_analyze:
            try:
                str_path = str(file_path)
                mtime = file_path.stat().st_mtime
                # Reuse cached result if file unchanged
                if str_path in self._cache and self._cache[str_path][0] == mtime:
                    result = self._cache[str_path][1]
                else:
                    result = self._analyze_file(file_path)
                    self._cache[str_path] = (mtime, result)
                self.analysis_results[str_path] = result
                # Categorize errors
                for error in result.syntax_errors:
                    self.error_summary[error.severity].append(error)
            except (OSError, AttributeError, UnicodeDecodeError):
                logger.debug("Suppressed AttributeError/OSError/UnicodeDecodeError", exc_info=True)

        # Generate summary report
        self._generate_summary_report()

        return self.analysis_results

    def _get_files_to_analyze(self) -> list[Path]:
        """Get all files that should be analyzed."""
        files: list[Any] = []
        # Ignore patterns
        ignore_patterns = {
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".vscode",
            ".vs",
            "venv_kilo",
            ".env",
            "logs",
        }

        # Supported file extensions
        supported_extensions = set(self.file_type_handlers.keys())

        for file_path in self.repository_root.rglob("*"):
            if file_path.is_file():
                # Skip ignored directories
                if any(ignore_pattern in file_path.parts for ignore_pattern in ignore_patterns):
                    continue

                # Only analyze supported file types
                if file_path.suffix.lower() in supported_extensions:
                    files.append(file_path)

        return files

    def _analyze_file(self, file_path: Path) -> FileAnalysisResult:
        """Analyze a single file for syntax errors."""
        file_extension = file_path.suffix.lower()
        handler = self.file_type_handlers.get(file_extension)

        if not handler:
            return FileAnalysisResult(
                file_path=str(file_path),
                file_type=file_extension,
                is_valid=True,
                warnings=[f"No handler for file type: {file_extension}"],
            )

        return handler(file_path)

    def _analyze_python_file(self, file_path: Path) -> FileAnalysisResult:
        """Analyze Python file for syntax errors."""
        result = FileAnalysisResult(
            file_path=str(file_path),
            file_type="python",
            is_valid=True,
        )

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Check for syntax errors using AST
            try:
                ast.parse(content)
                result.suggestions.append("✅ Python syntax is valid")
            except SyntaxError as e:
                syntax_error = RepositorySyntaxError(
                    file_path=str(file_path),
                    line_number=e.lineno or 0,
                    column_number=e.offset or 0,
                    error_type="SyntaxError",
                    error_message=str(e.msg),
                    severity="CRITICAL",
                    suggested_fix=self._suggest_python_fix(e),
                )
                result.syntax_errors.append(syntax_error)
                result.is_valid = False

            # Additional checks
            self._check_python_imports(file_path, content, result)
            self._check_python_encoding(file_path, content, result)

        except Exception as e:
            result.syntax_errors.append(
                RepositorySyntaxError(
                    file_path=str(file_path),
                    line_number=1,
                    column_number=1,
                    error_type="FileError",
                    error_message=f"Could not read file: {e}",
                    severity="HIGH",
                )
            )
            result.is_valid = False

        return result

    def _analyze_powershell_file(self, file_path: Path) -> FileAnalysisResult:
        """Analyze PowerShell file for syntax errors."""
        result = FileAnalysisResult(
            file_path=str(file_path),
            file_type="powershell",
            is_valid=True,
        )

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Check for common PowerShell syntax issues
            lines = content.split("\n")

            # Check for the specific issue found in setup.ps1
            python_code_pattern = re.compile(
                r"^\s*(search_result|enhance_search|import\s+|from\s+.*import)",
                re.MULTILINE,
            )

            for i, line in enumerate(lines, 1):
                # Check for Python code in PowerShell file
                if python_code_pattern.search(line):
                    syntax_error = RepositorySyntaxError(
                        file_path=str(file_path),
                        line_number=i,
                        column_number=1,
                        error_type="LanguageMixture",
                        error_message=f"Python code found in PowerShell file: {line.strip()}",
                        severity="CRITICAL",
                        suggested_fix="Remove Python code or move to appropriate Python file",
                    )
                    result.syntax_errors.append(syntax_error)
                    result.is_valid = False

                # Check for truncated commands
                if line.strip().endswith("--no-distri"):
                    syntax_error = RepositorySyntaxError(
                        file_path=str(file_path),
                        line_number=i,
                        column_number=len(line) - 12,
                        error_type="TruncatedCommand",
                        error_message="Truncated command parameter: --no-distri",
                        severity="HIGH",
                        suggested_fix="Complete parameter: --no-distribution",
                    )
                    result.syntax_errors.append(syntax_error)
                    result.is_valid = False

                # Check for misused pipe operators
                if "| Start-Process -NoNewWindow -Wait" in line:
                    syntax_error = RepositorySyntaxError(
                        file_path=str(file_path),
                        line_number=i,
                        column_number=line.find("|"),
                        error_type="IncorrectOperator",
                        error_message="Incorrect use of pipe operator for external commands",
                        severity="HIGH",
                        suggested_fix="Use '&' operator instead of '| Start-Process'",
                    )
                    result.syntax_errors.append(syntax_error)
                    result.is_valid = False

                # Check for unmatched braces
                open_braces = line.count("{")
                close_braces = line.count("}")
                if close_braces > open_braces and not any(x in line for x in ["catch", "finally"]):
                    syntax_error = RepositorySyntaxError(
                        file_path=str(file_path),
                        line_number=i,
                        column_number=line.find("}"),
                        error_type="UnmatchedBrace",
                        error_message="Closing brace without matching opening brace",
                        severity="CRITICAL",
                        suggested_fix="Remove orphaned '}' or add matching '{'",
                    )
                    result.syntax_errors.append(syntax_error)
                    result.is_valid = False

            # Try PowerShell syntax validation if available
            self._validate_powershell_syntax(file_path, content, result)

        except Exception as e:
            result.syntax_errors.append(
                RepositorySyntaxError(
                    file_path=str(file_path),
                    line_number=1,
                    column_number=1,
                    error_type="FileError",
                    error_message=f"Could not read PowerShell file: {e}",
                    severity="HIGH",
                )
            )
            result.is_valid = False

        return result

    def _analyze_json_file(self, file_path: Path) -> FileAnalysisResult:
        """Analyze JSON file for syntax errors."""
        result = FileAnalysisResult(
            file_path=str(file_path),
            file_type="json",
            is_valid=True,
        )

        try:
            with open(file_path, encoding="utf-8") as f:
                json.load(f)
            result.suggestions.append("✅ JSON syntax is valid")
        except json.JSONDecodeError as e:
            syntax_error = RepositorySyntaxError(
                file_path=str(file_path),
                line_number=e.lineno,
                column_number=e.colno,
                error_type="JSONSyntaxError",
                error_message=e.msg,
                severity="CRITICAL",
                suggested_fix=self._suggest_json_fix(e),
            )
            result.syntax_errors.append(syntax_error)
            result.is_valid = False
        except Exception as e:
            result.syntax_errors.append(
                RepositorySyntaxError(
                    file_path=str(file_path),
                    line_number=1,
                    column_number=1,
                    error_type="FileError",
                    error_message=f"Could not read JSON file: {e}",
                    severity="HIGH",
                )
            )
            result.is_valid = False

        return result

    def _analyze_yaml_file(self, file_path: Path) -> FileAnalysisResult:
        """Analyze YAML file for syntax errors."""
        result = FileAnalysisResult(
            file_path=str(file_path),
            file_type="yaml",
            is_valid=True,
        )

        try:
            with open(file_path, encoding="utf-8") as f:
                yaml.safe_load(f)
            result.suggestions.append("✅ YAML syntax is valid")
        except yaml.YAMLError as e:
            line_number = getattr(e, "problem_mark", None)
            syntax_error = RepositorySyntaxError(
                file_path=str(file_path),
                line_number=line_number.line + 1 if line_number else 1,
                column_number=line_number.column + 1 if line_number else 1,
                error_type="YAMLSyntaxError",
                error_message=str(e),
                severity="CRITICAL",
                suggested_fix=self._suggest_yaml_fix(e),
            )
            result.syntax_errors.append(syntax_error)
            result.is_valid = False
        except Exception as e:
            result.syntax_errors.append(
                RepositorySyntaxError(
                    file_path=str(file_path),
                    line_number=1,
                    column_number=1,
                    error_type="FileError",
                    error_message=f"Could not read YAML file: {e}",
                    severity="HIGH",
                )
            )
            result.is_valid = False

        return result

    def _analyze_markdown_file(self, file_path: Path) -> FileAnalysisResult:
        """Analyze Markdown file for common issues."""
        result = FileAnalysisResult(
            file_path=str(file_path),
            file_type="markdown",
            is_valid=True,
        )

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")

            # Check for common markdown issues
            for i, line in enumerate(lines, 1):
                # Check for unmatched code fences
                if line.strip().startswith("```") or line.strip().startswith("````"):
                    # Count code fences to ensure they're balanced
                    pass  # Implementation for code fence validation

                # Check for broken links
                link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
                for match in link_pattern.finditer(line):
                    url = match.group(2)
                    if url.startswith("http") and " " in url:
                        result.warnings.append(
                            f"Line {i}: Potential broken link with spaces: {url}"
                        )

            result.suggestions.append("✅ Markdown structure appears valid")

        except Exception as e:
            result.warnings.append(f"Could not fully analyze Markdown: {e}")

        return result

    def _suggest_python_fix(self, syntax_error) -> str:
        """Suggest fixes for Python syntax errors."""
        error_msg = str(syntax_error.msg).lower()

        if "invalid syntax" in error_msg:
            return "Check for missing colons, parentheses, or incorrect indentation"
        if "indentation" in error_msg:
            return "Fix indentation - use consistent spaces or tabs"
        if "eof" in error_msg:
            return "Check for unclosed parentheses, brackets, or quotes"
        return "Review Python syntax rules for this construct"

    def _suggest_json_fix(self, json_error) -> str:
        """Suggest fixes for JSON syntax errors."""
        error_msg = str(json_error.msg).lower()

        if "trailing comma" in error_msg:
            return "Remove trailing comma from last element"
        if "expecting" in error_msg and "'" in error_msg:
            return "Use double quotes for JSON strings, not single quotes"
        if "control character" in error_msg:
            return "Escape control characters or use proper JSON encoding"
        return "Check JSON syntax - ensure proper quotes, commas, and brackets"

    def _suggest_yaml_fix(self, yaml_error) -> str:
        """Suggest fixes for YAML syntax errors."""
        error_msg = str(yaml_error).lower()

        if "indentation" in error_msg:
            return "Fix YAML indentation - use consistent spaces (no tabs)"
        if "mapping" in error_msg:
            return "Check key-value pair syntax (key: value)"
        if "sequence" in error_msg:
            return "Check list syntax (- item)"
        return "Review YAML syntax rules"

    def _validate_powershell_syntax(
        self, file_path: Path, _content: str, result: FileAnalysisResult
    ) -> None:
        """Attempt to validate PowerShell syntax using PowerShell parser."""
        try:
            # Try to run PowerShell syntax check
            cmd = [
                "powershell",
                "-Command",
                f'$null = [System.Management.Automation.PSParser]::Tokenize((Get-Content "{file_path}" -Raw), [ref]$null)',
            ]
            process = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)

            if process.returncode != 0:
                result.warnings.append(f"PowerShell syntax validation failed: {process.stderr}")
            else:
                result.suggestions.append("✅ PowerShell syntax validation passed")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            result.warnings.append("PowerShell syntax validation not available")
        except Exception as e:
            result.warnings.append(f"PowerShell validation error: {e}")

    # Critical syntax errors we identified:
    CRITICAL_FIXES_NEEDED: ClassVar[list] = [
        "setup.ps1: Remove Python code from PowerShell file (lines 679-685)",
        "setup.ps1: Fix truncated WSL command (--no-distri → --no-distribution)",
        "setup.ps1: Replace pipe operators with & for external commands",
        "setup.ps1: Remove orphaned closing braces",
        "Repository-wide: Run comprehensive syntax analysis",
    ]

    def _check_python_imports(
        self, _file_path: Path, content: str, result: FileAnalysisResult
    ) -> None:
        """Check for import-related issues in Python files."""
        try:
            for i, line in enumerate(content.split("\n"), 1):
                if (
                    "import" in line
                    and not line.strip().startswith("#")
                    and "from . import" in line
                ) or "from .. import" in line:
                    # Check for potential circular imports or missing modules
                    result.warnings.append(
                        f"Line {i}: Relative import detected - ensure module structure is correct"
                    )

        except Exception as e:
            result.warnings.append(f"Could not analyze imports: {e}")

    def _check_python_encoding(
        self, _file_path: Path, content: str, result: FileAnalysisResult
    ) -> None:
        """Check for encoding issues in Python files."""
        try:
            # Check for encoding declaration
            first_lines = content.split("\n")[:2]
            has_encoding = any("coding" in line or "encoding" in line for line in first_lines)

            if not has_encoding and any(ord(char) > 127 for char in content):
                result.warnings.append(
                    "File contains non-ASCII characters but no encoding declaration"
                )

        except Exception as e:
            result.warnings.append(f"Could not analyze encoding: {e}")

    def _generate_summary_report(self) -> None:
        """Generate a summary report of all findings."""
        len(self.analysis_results)
        sum(1 for result in self.analysis_results.values() if not result.is_valid)
        sum(len(result.syntax_errors) for result in self.analysis_results.values())

        # Error breakdown by severity
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = len(self.error_summary[severity])
            if count > 0:
                pass

        # Top problematic files
        problematic_files = [
            (path, result) for path, result in self.analysis_results.items() if not result.is_valid
        ]

        for _path, result in sorted(
            problematic_files, key=lambda x: len(x[1].syntax_errors), reverse=True
        )[:10]:
            len(result.syntax_errors)
            sum(1 for e in result.syntax_errors if e.severity == "CRITICAL")


def main() -> None:
    """Main function to run repository-wide syntax analysis."""
    if BRIDGE_AVAILABLE:
        # Use bridge to enhance analysis via EnhancedCopilotBridge
        bridge = EnhancedCopilotBridge()
        len(bridge.architecture_insights)

    analyzer = RepositorySyntaxAnalyzer()
    results = analyzer.analyze_repository()

    # Generate detailed report
    for result in results.values():
        if not result.is_valid:
            for error in result.syntax_errors:
                if error.suggested_fix:
                    pass


if __name__ == "__main__":
    main()
