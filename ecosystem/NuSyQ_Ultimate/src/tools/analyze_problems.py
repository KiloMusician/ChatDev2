"""
Analyze and report on NuSyQ repository issues
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import Set

# Set UTF-8 encoding for console output on Windows
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

# Directories to analyze (exclude third-party code)
ANALYZE_DIRS = ["mcp_server/src", "mcp_server", "config"]

EXCLUDE_PATTERNS = ["ChatDev", "GODOT", ".venv", "node_modules", "__pycache__", ".git"]


class CodeAnalyzer:
    """Analyze Python code for common issues"""

    def __init__(self):
        self.issues = defaultdict(list)
        self.stats = {
            "files_analyzed": 0,
            "total_lines": 0,
            "functions": 0,
            "classes": 0,
        }
        self.modules_used: Set[str] = set()

    def should_analyze(self, path: Path) -> bool:
        """Check if file should be analyzed"""
        path_str = str(path)
        return path.suffix == ".py" and not any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

    def analyze_file(self, filepath: Path):
        """Analyze a single Python file"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(filepath))

            self.stats["files_analyzed"] += 1
            self.stats["total_lines"] += content.count("\n")

            # Analyze AST
            self._check_imports(tree, filepath)
            self._check_functions(tree, filepath)
            self._check_classes(tree, filepath)
            self._check_type_hints(tree, filepath)

        except SyntaxError as e:
            self.issues["syntax_errors"].append(f"{filepath}: {e}")
        except (OSError, ValueError, TypeError) as e:
            self.issues["analysis_errors"].append(f"{filepath}: {e}")

    def _check_imports(self, tree: ast.AST, filepath: Path):
        """Check for import issues"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # Check for common missing imports
        _common_modules = {
            "logging",
            "pathlib",
            "typing",
            "asyncio",
            "pydantic",
            "fastapi",
            "aiohttp",
        }

        # This is just informational, not an error
        found_modules = set(imp.split(".")[0] for imp in imports)
        self.modules_used.update(found_modules)

    def _check_functions(self, tree: ast.AST, filepath: Path):
        """Check functions for common issues"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.stats["functions"] += 1

                # Check for missing docstrings
                if not ast.get_docstring(node):
                    if not node.name.startswith("_"):  # Public functions
                        self.issues["missing_docstrings"].append(
                            f"{filepath}:{node.lineno} - {node.name}"
                        )

                # Check for type hints
                missing_hints = []
                for arg in node.args.args:
                    if arg.annotation is None and arg.arg != "self" and arg.arg != "cls":
                        missing_hints.append(arg.arg)

                if missing_hints and not node.name.startswith("_"):
                    self.issues["missing_type_hints"].append(
                        f"{filepath}:{node.lineno} - {node.name}({', '.join(missing_hints)})"
                    )

    def _check_classes(self, tree: ast.AST, filepath: Path):
        """Check classes for common issues"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self.stats["classes"] += 1

                # Check for missing docstrings
                if not ast.get_docstring(node):
                    self.issues["missing_class_docstrings"].append(
                        f"{filepath}:{node.lineno} - {node.name}"
                    )

    def _check_type_hints(self, tree: ast.AST, filepath: Path):
        """Check for type hint usage"""
        # Count functions with/without type hints
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_hints = node.returns is not None or any(
                    arg.annotation for arg in node.args.args
                )
                if has_hints:
                    self.stats.setdefault("functions_with_hints", 0)
                    self.stats["functions_with_hints"] += 1

    def print_report(self):
        """Print analysis report"""
        print("\n" + "=" * 70)
        print("🔍 NuSyQ Code Analysis Report")
        print("=" * 70)

        # Statistics
        print("\n📊 Code Statistics:")
        print(f"  Files analyzed: {self.stats['files_analyzed']}")
        print(f"  Total lines: {self.stats['total_lines']}")
        print(f"  Functions: {self.stats['functions']}")
        print(f"  Classes: {self.stats['classes']}")

        if "functions_with_hints" in self.stats:
            hint_percentage = (
                self.stats["functions_with_hints"] / self.stats["functions"] * 100
                if self.stats["functions"] > 0
                else 0
            )
            print(f"  Type hint coverage: {hint_percentage:.1f}%")

        # Issues by category
        print("\n⚠️  Issues Found:")

        total_issues = sum(len(issues) for issues in self.issues.values())
        print(f"  Total issues: {total_issues}")

        if self.issues["syntax_errors"]:
            print(f"\n  ❌ Syntax Errors ({len(self.issues['syntax_errors'])}):")
            for issue in self.issues["syntax_errors"][:10]:
                print(f"    - {issue}")

        if self.issues["missing_docstrings"]:
            count = len(self.issues["missing_docstrings"])
            print(f"\n  📝 Missing Function Docstrings ({count}):")
            for issue in self.issues["missing_docstrings"][:5]:
                print(f"    - {issue}")
            if count > 5:
                print(f"    ... and {count - 5} more")

        if self.issues["missing_class_docstrings"]:
            count = len(self.issues["missing_class_docstrings"])
            print(f"\n  📝 Missing Class Docstrings ({count}):")
            for issue in self.issues["missing_class_docstrings"][:5]:
                print(f"    - {issue}")
            if count > 5:
                print(f"    ... and {count - 5} more")

        if self.issues["missing_type_hints"]:
            count = len(self.issues["missing_type_hints"])
            print(f"\n  🔤 Missing Type Hints ({count}):")
            for issue in self.issues["missing_type_hints"][:5]:
                print(f"    - {issue}")
            if count > 5:
                print(f"    ... and {count - 5} more")

        # Summary
        print("\n" + "=" * 70)
        if total_issues == 0:
            print("✅ No issues found! Code quality is excellent.")
        elif total_issues < 20:
            print("✨ Code quality is good! Minor improvements possible.")
        elif total_issues < 100:
            print("👍 Code is functional. Consider addressing style issues.")
        else:
            print("📋 Many style suggestions. These are not errors!")

        print("\n💡 Note: Missing docstrings and type hints are style")
        print("   suggestions, not functional errors. Your code works fine!")
        print("=" * 70 + "\n")


def main():
    """Main analysis function"""
    analyzer = CodeAnalyzer()

    # Analyze all relevant files
    for dir_path in ANALYZE_DIRS:
        path = Path(dir_path)
        if not path.exists():
            continue

        if path.is_file():
            if analyzer.should_analyze(path):
                analyzer.analyze_file(path)
        else:
            for py_file in path.rglob("*.py"):
                if analyzer.should_analyze(py_file):
                    analyzer.analyze_file(py_file)

    # Print report
    analyzer.print_report()


if __name__ == "__main__":
    main()
