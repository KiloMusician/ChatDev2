"""
Deep analysis of NuSyQ repository to find all issues
"""

import ast
import re
import sys
from collections import defaultdict
from pathlib import Path

# UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

ANALYZE_DIRS = ["mcp_server", "config", "AI_Hub"]
EXCLUDE = ["ChatDev", "GODOT", ".venv", "__pycache__", "WareHouse"]


class DeepAnalyzer:
    """Deep code analysis"""

    def __init__(self):
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)

    def analyze_file(self, filepath: Path):
        """Comprehensive file analysis"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(filepath))

            self.stats["files"] += 1

            # Multiple checks
            self._check_imports(tree, filepath, content)
            self._check_type_annotations(tree, filepath)
            self._check_error_handling(tree, filepath)
            self._check_async_patterns(tree, filepath)
            self._check_security(tree, filepath, content)
            self._check_deprecated(content, filepath)
            self._check_todos(content, filepath)
            self._check_bare_excepts(tree, filepath)
            self._check_unused_imports(tree, filepath, content)

        except SyntaxError as e:
            self.issues["syntax_errors"].append(f"{filepath}:{e.lineno} - {e.msg}")
        except (OSError, ValueError, TypeError):
            pass  # Skip files we can't parse

    def _check_imports(self, tree: ast.AST, filepath: Path, content: str):
        """Check import issues"""
        imports_defined = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports_defined.add(name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        name = alias.asname or alias.name
                        imports_defined.add(name)

        # Check for common missing imports
        if "typing" not in str(content) and ("Dict" in content or "List" in content):
            if "from typing import" not in content:
                self.issues["missing_typing_import"].append(str(filepath))

    def _check_type_annotations(self, tree: ast.AST, filepath: Path):
        """Check for missing type annotations"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private/magic methods
                if node.name.startswith("_"):
                    continue

                # Check parameters
                for arg in node.args.args:
                    if arg.arg not in ["self", "cls"] and arg.annotation is None:
                        self.issues["missing_param_types"].append(
                            f"{filepath}:{node.lineno} - {node.name}({arg.arg})"
                        )

                # Check return type
                if node.returns is None and node.name not in ["__init__"]:
                    self.issues["missing_return_types"].append(
                        f"{filepath}:{node.lineno} - {node.name}"
                    )

    def _check_error_handling(self, tree: ast.AST, filepath: Path):
        """Check error handling patterns"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Bare except
                if node.type is None:
                    self.issues["bare_except"].append(
                        f"{filepath}:{node.lineno} - Bare except clause"
                    )
                # Catching Exception
                elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                    self.issues["broad_except"].append(
                        f"{filepath}:{node.lineno} - Catching broad Exception"
                    )

    def _check_async_patterns(self, tree: ast.AST, filepath: Path):
        """Check async/await patterns"""
        for node in ast.walk(tree):
            # Async function without await
            if isinstance(node, ast.AsyncFunctionDef):
                has_await = any(isinstance(n, ast.Await) for n in ast.walk(node))
                if not has_await:
                    self.issues["async_without_await"].append(
                        f"{filepath}:{node.lineno} - Async function without await: {node.name}"
                    )

    def _check_security(self, tree: ast.AST, filepath: Path, content: str):
        """Check security issues"""
        dangerous_patterns = [
            (r"eval\s*\(", "eval() usage"),
            (r"exec\s*\(", "exec() usage"),
            (r"__import__\s*\(", "__import__() usage"),
            (r"subprocess\.call\s*\(", "subprocess.call without shell=False"),
        ]

        for pattern, desc in dangerous_patterns:
            if re.search(pattern, content):
                self.issues["security_concern"].append(f"{filepath} - {desc}")

    def _check_deprecated(self, content: str, filepath: Path):
        """Check for deprecated patterns"""
        deprecated = [
            (r"@validator\(", "Pydantic v1 @validator (use @field_validator)"),
            (r"\.warn\(", "warnings.warn (use logging.warning)"),
            (r"assertEquals\(", "assertEquals (use assertEqual)"),
        ]

        for pattern, desc in deprecated:
            if re.search(pattern, content):
                self.issues["deprecated_api"].append(f"{filepath} - {desc}")

    def _check_todos(self, content: str, filepath: Path):
        """Find TODO comments"""
        for i, line in enumerate(content.split("\n"), 1):
            if "TODO" in line or "FIXME" in line or "HACK" in line:
                self.issues["todo_comments"].append(f"{filepath}:{i} - {line.strip()[:60]}")

    def _check_bare_excepts(self, tree: ast.AST, filepath: Path):
        """Check for bare except clauses"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    if handler.type is None:
                        self.issues["bare_except_detailed"].append(f"{filepath}:{handler.lineno}")

    def _check_unused_imports(self, tree: ast.AST, filepath: Path, content: str):
        """Check for potentially unused imports"""
        # This is approximate - just check if import name appears in content
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    # Simple check: does the name appear elsewhere?
                    occurrences = content.count(name)
                    if occurrences <= 1:  # Only in import line
                        self.issues["possibly_unused_import"].append(
                            f"{filepath}:{node.lineno} - {name}"
                        )

    def print_report(self):
        """Print comprehensive report"""
        print("\n" + "=" * 70)
        print("🔬 NuSyQ Deep Analysis Report")
        print("=" * 70)

        total_issues = sum(len(v) for v in self.issues.values())
        print(f"\n📊 Total Issues Found: {total_issues}")
        print(f"📁 Files Analyzed: {self.stats['files']}")

        # Group by severity
        critical = ["syntax_errors", "security_concern"]
        important = ["bare_except", "async_without_await", "deprecated_api"]
        style = ["missing_param_types", "missing_return_types", "todo_comments"]

        if any(self.issues[k] for k in critical):
            print("\n🚨 CRITICAL ISSUES:")
            for category in critical:
                if self.issues[category]:
                    print(
                        f"\n  ❌ {category.replace('_', ' ').title()} ({len(self.issues[category])}):"
                    )
                    for issue in self.issues[category][:5]:
                        print(f"    {issue}")
                    if len(self.issues[category]) > 5:
                        print(f"    ... and {len(self.issues[category]) - 5} more")

        if any(self.issues[k] for k in important):
            print("\n⚠️  IMPORTANT ISSUES:")
            for category in important:
                if self.issues[category]:
                    print(
                        f"\n  ⚡ {category.replace('_', ' ').title()} ({len(self.issues[category])}):"
                    )
                    for issue in self.issues[category][:5]:
                        print(f"    {issue}")
                    if len(self.issues[category]) > 5:
                        print(f"    ... and {len(self.issues[category]) - 5} more")

        if any(self.issues[k] for k in style):
            print("\n📝 STYLE SUGGESTIONS:")
            for category in style:
                if self.issues[category]:
                    count = len(self.issues[category])
                    print(f"  • {category.replace('_', ' ').title()}: {count}")

        # Other issues
        other_categories = set(self.issues.keys()) - set(critical + important + style)
        if other_categories:
            print("\n💡 OTHER FINDINGS:")
            for category in sorted(other_categories):
                count = len(self.issues[category])
                print(f"  • {category.replace('_', ' ').title()}: {count}")

        print("\n" + "=" * 70)

        # Priority recommendations
        print("\n🎯 RECOMMENDED ACTIONS:")
        if self.issues["syntax_errors"]:
            print("  1. Fix syntax errors immediately")
        if self.issues["security_concern"]:
            print("  2. Review security concerns")
        if self.issues["deprecated_api"]:
            print("  3. Update deprecated API usage")
        if self.issues["bare_except"]:
            print("  4. Replace bare except clauses with specific exceptions")

        print("\n" + "=" * 70 + "\n")


def main():
    analyzer = DeepAnalyzer()

    for dir_path in ANALYZE_DIRS:
        path = Path(dir_path)
        if not path.exists():
            continue

        for py_file in path.rglob("*.py"):
            if any(exc in str(py_file) for exc in EXCLUDE):
                continue
            analyzer.analyze_file(py_file)

    analyzer.print_report()


if __name__ == "__main__":
    main()
