"""🔍 Complete System Function Registry
Comprehensive list of every function definition in the repository with undefined call tracking

OmniTag: {
    "purpose": "Complete function registry and undefined call detection for repository",
    "dependencies": ["ast", "pathlib", "re"],
    "context": "System-wide function mapping and validation",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "FunctionRegistry",
    "integration_points": ["function_mapping", "undefined_detection", "system_validation"],
    "related_tags": ["SystemAnalyzer", "FunctionMapper", "ValidationTool"]
}

RSHTS: ΞΨΩΣ∞⟨FUNCTION-REGISTRY⟩→ΦΣΣ⟨COMPLETE-MAP⟩→∞⟨VALIDATION⟩
"""

import ast
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# Constants for undefined call detection
BUILTIN_FUNCTIONS = {
    "print",
    "len",
    "str",
    "int",
    "float",
    "bool",
    "round",
    "hash",
    "exit",
    "quit",
    "next",
    "ord",
    "list",
    "dict",
    "set",
    "tuple",
    "frozenset",
    "range",
    "enumerate",
    "zip",
    "map",
    "filter",
    "sum",
    "max",
    "min",
    "abs",
    "open",
    "input",
    "isinstance",
    "hasattr",
    "getattr",
    "setattr",
    "delattr",
    "type",
    "id",
    "dir",
    "vars",
    "globals",
    "locals",
    "exec",
    "eval",
    "super",
    "property",
    "classmethod",
    "staticmethod",
    "__import__",
    "sorted",
    "reversed",
    "all",
    "any",
}

LIBRARY_METHODS = {
    "append",
    "extend",
    "insert",
    "remove",
    "pop",
    "clear",
    "index",
    "count",
    "sort",
    "reverse",
    "copy",
    "get",
    "keys",
    "values",
    "items",
    "update",
    "add",
    "discard",
    "union",
    "intersection",
    "difference",
    "split",
    "join",
    "strip",
    "replace",
    "find",
    "startswith",
    "endswith",
    "upper",
    "lower",
    "read",
    "write",
    "close",
    "seek",
    "tell",
    "exists",
    "mkdir",
    "glob",
    "rglob",
    "iterdir",
    "is_file",
    "is_dir",
    "stat",
    "resolve",
    "relative_to",
}

DEFAULT_ALLOWLIST = {
    # pandas
    "DataFrame",
    "Series",
    "Index",
    # numpy
    "array",
    "ndarray",
    # pathlib/typing/common constructors
    "Path",
    "NamedTuple",
    "dataclass",
    # dataclasses helpers
    "field",
    "asdict",
    "astuple",
    "replace",
    "make_dataclass",
    # pygments
    "bygroups",
    # collections
    "Counter",
    "defaultdict",
    "deque",
    # exceptions
    "ValueError",
    "TypeError",
    "KeyError",
    "IndexError",
    "RuntimeError",
    "AssertionError",
    "IOError",
    "OSError",
    "StopIteration",
    "StopAsyncIteration",
    "NotImplementedError",
    "ImportError",
    "ModuleNotFoundError",
    "TimeoutError",
    "ConnectionError",
    "SystemExit",
    "FileNotFoundError",
    "PermissionError",
    "KeyboardInterrupt",
    # unittest.mock
    "MagicMock",
    "Mock",
    "patch",
    # enum
    "auto",
    # datetime
    "timedelta",
    # base
    "Exception",
    # typing
    "TypeVar",
    "cls",
}


class _FunctionAnalyzer(ast.NodeVisitor):
    """Fast, context-aware analyzer for function defs and calls.

    Tracks current class and function to correctly mark class methods and
    to annotate calls with their enclosing function/class context.
    """

    def __init__(self) -> None:
        self.definitions: list[dict] = []
        self.calls: list[dict] = []
        self.class_defs: list[dict] = []
        self._class_stack: list[str] = []
        self._func_stack: list[str] = []

    # ---- Helpers ----
    def _current_class(self) -> str | None:
        """Return the name of the current enclosing class, if any."""
        return self._class_stack[-1] if self._class_stack else None

    def _current_function(self) -> str | None:
        """Return the name of the current enclosing function, if any."""
        return self._func_stack[-1] if self._func_stack else None

    def _collect_function(self, node: ast.AST, is_async: bool) -> None:
        """Collect function definition metadata from an AST node."""
        assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        func_info = {
            "name": node.name,
            "line": node.lineno,
            "args": [arg.arg for arg in node.args.args],
            "docstring": ast.get_docstring(node) or "",
            "is_async": is_async,
            "class_method": self._current_class() is not None,
            "decorators": [
                ast.unparse(dec) if hasattr(ast, "unparse") else str(dec)
                for dec in getattr(node, "decorator_list", [])
            ],
        }
        if self._current_class():
            func_info["class_name"] = self._current_class()
        self.definitions.append(func_info)

    def _collect_call(self, node: ast.Call) -> None:
        """Collect function call metadata from an AST Call node."""
        call_info: dict[str, Any] | None = None
        if isinstance(node.func, ast.Name):
            call_info = {
                "function_name": node.func.id,
                "line": node.lineno,
                "call_type": "direct",
                "full_call": node.func.id,
            }
        elif isinstance(node.func, ast.Attribute):
            base = ast.unparse(node.func.value) if hasattr(ast, "unparse") else "obj"
            call_info = {
                "function_name": node.func.attr,
                "line": node.lineno,
                "call_type": "method",
                "full_call": f"{base}.{node.func.attr}",
            }
        if call_info:
            # annotate call context
            if self._current_function():
                call_info["enclosing_function"] = self._current_function()
            if self._current_class():
                call_info["enclosing_class"] = self._current_class()
            self.calls.append(call_info)

    # ---- Visitors ----
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition and track it in the class stack."""
        # collect class definition metadata
        self.class_defs.append(
            {
                "name": node.name,
                "line": node.lineno,
                "docstring": ast.get_docstring(node) or "",
            }
        )
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition and track it in the function stack."""
        self._collect_function(node, is_async=False)
        self._func_stack.append(node.name)
        self.generic_visit(node)
        self._func_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an async function definition and track it in the function stack."""
        self._collect_function(node, is_async=True)
        self._func_stack.append(node.name)
        self.generic_visit(node)
        self._func_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        """Visit a function call and collect its metadata."""
        self._collect_call(node)
        self.generic_visit(node)


class CompleteFunctionRegistry:
    """🔍 Complete Function Registry System

    Scans entire repository to:
    - Catalog every function definition
    - Track function calls
    - Identify undefined function calls
    - Generate comprehensive function reference
    """

    def __init__(self, repository_root: str = ".") -> None:
        """Initialize the function registry.

        Args:
            repository_root: Path to the repository root directory (default: current directory)
        """
        self.repository_root: Path = Path(repository_root).resolve()
        self.timestamp: str = datetime.now().isoformat()

        # Storage for analysis results
        self.defined_functions: dict[str, list[dict[str, Any]]] = {}  # {file_path: [function_info]}
        self.function_calls: dict[str, list[dict[str, Any]]] = {}  # {file_path: [call_info]}
        self.all_definitions: dict[str, list[dict[str, Any]]] = {}  # {function_name: [locations]}
        self.defined_classes: dict[str, list[dict[str, Any]]] = {}  # {class_name: [locations]}
        self.undefined_calls: list[dict[str, Any]] = []  # [undefined_call_info]

        print(f"🔍 Function Registry initialized for {self.repository_root.name}")

    def analyze_file(
        self, file_path: Path
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Analyze a single Python file for functions and calls.

        Uses a single AST pass with a NodeVisitor to avoid O(N^2) parent scans
        and to capture enclosing class/function contexts.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            Tuple of (definitions, calls, class_defs) where each is a list of metadata dicts
        """
        definitions: list[dict[str, Any]] = []
        calls: list[dict[str, Any]] = []
        class_defs: list[dict[str, Any]] = []

        if not file_path.exists() or file_path.suffix != ".py":
            return definitions, calls, class_defs

        # Skip very large files (> 1.5 MB) to avoid excessive memory/CPU
        try:
            if file_path.stat().st_size > 1_500_000:
                print(f"⏭️ Skipping large file: {file_path}")
                return definitions, calls, class_defs
        except OSError:
            pass

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            analyzer = _FunctionAnalyzer()
            analyzer.visit(tree)
            definitions, calls = analyzer.definitions, analyzer.calls
            class_defs = analyzer.class_defs

        except (SyntaxError, UnicodeDecodeError, OSError) as e:
            print(f"⚠️ Error analyzing {file_path}: {e}")

        return definitions, calls, class_defs

    def scan_repository(
        self,
        max_files: int | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Scan entire repository for functions.

        Args:
            max_files: Optional cap on number of .py files to process (for fast runs)
            exclude_patterns: Optional list of path substrings to skip
                (e.g., ['/.git/', '/archive/'])

        Returns:
            Dictionary with scan statistics and results
        """
        print("🔍 Scanning repository for function definitions and calls...")

        # Clear previous results
        self.defined_functions.clear()
        self.function_calls.clear()
        self.all_definitions.clear()
        self.undefined_calls.clear()

        total_files = 0
        total_functions = 0
        total_calls = 0

        # Defaults for excludes
        default_excludes = [
            os.sep + ".git" + os.sep,
            os.sep + ".venv" + os.sep,
            os.sep + ".venv.old" + os.sep,
            os.sep + "venv" + os.sep,
            os.sep + "env" + os.sep,
            os.sep + "build" + os.sep,
            os.sep + "dist" + os.sep,
            os.sep + "archive" + os.sep,
            os.sep + "cleanup_backup" + os.sep,
            os.sep + "__pycache__" + os.sep,
            os.sep + "site-packages" + os.sep,
            os.sep + "Lib" + os.sep + "site-packages" + os.sep,
        ]
        excludes = set(default_excludes)
        if exclude_patterns:
            excludes.update(exclude_patterns)

        processed = 0

        # Scan all Python files
        for py_file in self.repository_root.rglob("*.py"):
            path_str = str(py_file)
            if any(ex in path_str for ex in excludes):
                continue

            relative_path = str(py_file.relative_to(self.repository_root))
            definitions, calls, class_defs = self.analyze_file(py_file)

            if definitions or calls:
                total_files += 1
                total_functions += len(definitions)
                total_calls += len(calls)

                self.defined_functions[relative_path] = definitions
                self.function_calls[relative_path] = calls

                # Build class definitions lookup
                if class_defs:
                    for cls in class_defs:
                        name = cls["name"]
                        if name not in self.defined_classes:
                            self.defined_classes[name] = []
                        self.defined_classes[name].append(
                            {
                                "file": relative_path,
                                "line": cls["line"],
                            }
                        )

                # Build all_definitions lookup
                for func_def in definitions:
                    func_name = func_def["name"]
                    if func_name not in self.all_definitions:
                        self.all_definitions[func_name] = []

                    self.all_definitions[func_name].append(
                        {
                            "file": relative_path,
                            "line": func_def["line"],
                            "class_method": func_def["class_method"],
                            "class_name": func_def.get("class_name", ""),
                            "is_async": func_def["is_async"],
                        }
                    )

            processed += 1
            if max_files is not None and processed >= max_files:
                print(f"⏹️ Max files limit reached: {processed}/{max_files}")
                break

        print(
            "✅ Scanned %s files, found %s functions, %s calls"
            % (total_files, total_functions, total_calls)
        )

        # Identify undefined calls
        self._identify_undefined_calls()

        # Return scan results
        return {
            "total_files": total_files,
            "python_files": total_files,
            "total_functions": total_functions,
            "total_calls": total_calls,
            "undefined_calls": len(self.undefined_calls),
            "functions_by_category": self._categorize_functions(),
            "all_functions": self._get_all_functions_list(),
            "potentially_undefined": self.undefined_calls,
        }

    def _identify_undefined_calls(self) -> None:
        """Identify function calls that don't have definitions.

        Populates self.undefined_calls with calls that appear to be undefined.
        Ignores built-in functions, common library methods, and private methods.
        """
        print("🔍 Identifying undefined function calls...")

        # Allow further customization via environment variable (comma-separated names)
        extra_allow_env = os.getenv("NUSYQ_REGISTRY_UNDEFINED_ALLOWLIST", "")
        extra_allow = {name.strip() for name in extra_allow_env.split(",") if name.strip()}
        allowed_names = BUILTIN_FUNCTIONS | LIBRARY_METHODS | DEFAULT_ALLOWLIST | extra_allow

        undefined_calls = []

        for file_path, calls in self.function_calls.items():
            for call in calls:
                func_name = call["function_name"]

                # Skip built-ins, common library methods, and default allowlisted names
                if func_name in allowed_names:
                    continue

                # Skip private/magic methods
                if func_name.startswith("_"):
                    continue

                # Skip if we have a function or class definition
                if func_name in self.all_definitions:
                    continue
                if func_name in self.defined_classes:
                    continue

                # Skip method calls (they might be from imported libraries)
                if call["call_type"] == "method":
                    continue

                undefined_calls.append(
                    {
                        "function_name": func_name,
                        "file": file_path,
                        "line": call["line"],
                        "full_call": call["full_call"],
                    }
                )

        self.undefined_calls = undefined_calls
        print(f"⚠️ Found {len(undefined_calls)} potentially undefined function calls")

    def generate_function_reference(self) -> str:
        """Generate comprehensive function reference in Markdown format.

        Returns:
            Markdown-formatted string containing complete function registry
        """
        reference = f"""# 🔍 Complete System Function Registry

**Generated:** {self.timestamp}
**Repository:** {self.repository_root.name}
**Total Files Analyzed:** {len(self.defined_functions)}
**Total Functions Found:** {sum(len(funcs) for funcs in self.defined_functions.values())}
**Total Function Calls:** {sum(len(calls) for calls in self.function_calls.values())}
**Undefined Calls Found:** {len(self.undefined_calls)}

## 📋 Function Definitions by File

"""

        # Sort files for consistent output
        sorted_files = sorted(self.defined_functions.keys())

        for file_path in sorted_files:
            functions = self.defined_functions[file_path]
            if not functions:
                continue

            reference += f"\n### 📄 `{file_path}`\n"
            reference += f"**Functions:** {len(functions)}\n\n"

            # Sort functions by line number
            sorted_functions = sorted(functions, key=lambda x: x["line"])

            for func in sorted_functions:
                # Function signature
                args_str = ", ".join(func["args"]) if func["args"] else ""
                async_str = "async " if func["is_async"] else ""
                class_str = f"[Class: {func['class_name']}] " if func["class_method"] else ""

                reference += f"- **{async_str}def {func['name']}({args_str})** "
                reference += f"_(Line {func['line']})_ {class_str}\n"

                # Decorators
                if func["decorators"]:
                    decorators_str = ", ".join(func["decorators"])
                    reference += f"  - *Decorators:* `{decorators_str}`\n"

                # Docstring (first line only)
                if func["docstring"]:
                    first_line = func["docstring"].split("\n")[0].strip()
                    if first_line:
                        reference += f"  - *Description:* {first_line}\n"

                reference += "\n"

        # Alphabetical function index
        reference += "\n## 🔤 Alphabetical Function Index\n\n"

        all_func_names = sorted(self.all_definitions.keys())
        for func_name in all_func_names:
            locations = self.all_definitions[func_name]
            reference += f"- **{func_name}** - "

            location_strs = []
            for loc in locations:
                class_info = f" [{loc['class_name']}]" if loc["class_method"] else ""
                async_info = " (async)" if loc["is_async"] else ""
                location_strs.append(f"`{loc['file']}:{loc['line']}`{class_info}{async_info}")

            reference += ", ".join(location_strs) + "\n"

        # Function statistics
        reference += "\n## 📊 Function Statistics\n\n"

        # Count by file type
        file_types: dict[str, int] = {}
        for file_path in self.defined_functions.keys():
            if "/ai/" in file_path:
                file_types["AI Systems"] = file_types.get("AI Systems", 0) + len(
                    self.defined_functions[file_path]
                )
            elif "/system/" in file_path:
                file_types["System"] = file_types.get("System", 0) + len(
                    self.defined_functions[file_path]
                )
            elif "/utils/" in file_path:
                file_types["Utils"] = file_types.get("Utils", 0) + len(
                    self.defined_functions[file_path]
                )
            elif "/diagnostics/" in file_path:
                file_types["Diagnostics"] = file_types.get("Diagnostics", 0) + len(
                    self.defined_functions[file_path]
                )
            elif "/analysis/" in file_path:
                file_types["Analysis"] = file_types.get("Analysis", 0) + len(
                    self.defined_functions[file_path]
                )
            else:
                file_types["Other"] = file_types.get("Other", 0) + len(
                    self.defined_functions[file_path]
                )

        for category, count in sorted(file_types.items()):
            reference += f"- **{category}:** {count} functions\n"

        # Count class methods vs standalone functions
        class_methods = 0
        standalone_functions = 0
        async_functions = 0

        for functions in self.defined_functions.values():
            for func in functions:
                if func["class_method"]:
                    class_methods += 1
                else:
                    standalone_functions += 1

                if func["is_async"]:
                    async_functions += 1

        reference += "\n**Function Types:**\n"
        reference += f"- Class Methods: {class_methods}\n"
        reference += f"- Standalone Functions: {standalone_functions}\n"
        reference += f"- Async Functions: {async_functions}\n"

        # Undefined function calls
        if self.undefined_calls:
            reference += "\n## ⚠️ Undefined Function Calls\n\n"
            reference += f"**Total:** {len(self.undefined_calls)}\n\n"

            # Group by function name
            undefined_by_name: dict[str, list[dict[str, Any]]] = {}
            for call in self.undefined_calls:
                func_name = call["function_name"]
                if func_name not in undefined_by_name:
                    undefined_by_name[func_name] = []
                undefined_by_name[func_name].append(call)

            for func_name in sorted(undefined_by_name.keys()):
                calls = undefined_by_name[func_name]
                reference += f"### ❌ `{func_name}`\n"
                reference += f"**Called {len(calls)} time(s):**\n"

                for call in calls:
                    reference += f"- `{call['file']}:{call['line']}` - `{call['full_call']}`\n"

                reference += "\n"
        else:
            reference += "\n## ✅ No Undefined Function Calls Found\n\n"
            reference += "All function calls appear to have corresponding definitions or are from standard libraries.\n"

        reference += f"\n---\n*Generated by CompleteFunctionRegistry v1.0 - {self.timestamp}*\n"

        return reference

    def export_undefined_calls_report(self, output_path: str | None = None) -> str:
        """Export a focused Markdown report of undefined calls for quick action.

        Args:
            output_path: Optional custom path for the report file

        Returns:
            Path to the exported report file
        """
        resolved_path: Path
        if output_path is None:
            resolved_path = self.repository_root / "UNDEFINED_FUNCTION_CALLS.md"
        else:
            resolved_path = Path(output_path)

        lines: list[str] = []
        lines.append("# ⚠️ Potentially Undefined Function Calls\n")
        lines.append(f"Generated: {self.timestamp}  ")
        lines.append(f"Repository: {self.repository_root.name}\n\n")

        if not self.undefined_calls:
            lines.append("✅ No potentially undefined function calls found.\n")
        else:
            # Group by function name
            by_name: dict[str, list[dict[str, Any]]] = {}
            for call in self.undefined_calls:
                by_name.setdefault(call["function_name"], []).append(call)

            for func_name in sorted(by_name.keys()):
                calls = sorted(by_name[func_name], key=lambda c: (c["file"], c["line"]))
                lines.append(f"## ❌ {func_name}\n")
                lines.append(f"Occurrences: {len(calls)}\n\n")
                for c in calls:
                    lines.append(f"- `{c['file']}:{c['line']}` - `{c['full_call']}`\n")
                lines.append("\n")

        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write("".join(lines))

        print(f"✅ Undefined calls report exported to {resolved_path}")
        return str(resolved_path)

    def export_function_registry(self, output_path: str | None = None) -> str:
        """Export complete function registry to Markdown file.

        Args:
            output_path: Optional custom path for the registry file

        Returns:
            Path to the exported registry file
        """
        resolved_path: Path
        if output_path is None:
            resolved_path = self.repository_root / "COMPLETE_FUNCTION_REGISTRY.md"
        else:
            resolved_path = Path(output_path)

        # Generate reference
        reference = self.generate_function_reference()

        # Write to file
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(reference)

        print(f"✅ Function registry exported to {resolved_path}")
        return str(resolved_path)

    def export_json_data(self, output_path: str | None = None) -> str:
        """Export raw data as JSON for programmatic use.

        Args:
            output_path: Optional custom path for the JSON file

        Returns:
            Path to the exported JSON file
        """
        resolved_path: Path
        if output_path is None:
            resolved_path = self.repository_root / "function_registry_data.json"
        else:
            resolved_path = Path(output_path)

        export_data = {
            "metadata": {
                "timestamp": self.timestamp,
                "repository": self.repository_root.name,
                "total_files": len(self.defined_functions),
                "total_functions": sum(len(funcs) for funcs in self.defined_functions.values()),
                "total_calls": sum(len(calls) for calls in self.function_calls.values()),
                "undefined_calls": len(self.undefined_calls),
            },
            "defined_functions": self.defined_functions,
            "function_calls": self.function_calls,
            "all_definitions": self.all_definitions,
            "undefined_calls": self.undefined_calls,
        }

        with open(resolved_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON data exported to {resolved_path}")
        return str(resolved_path)

    def _categorize_functions(self) -> dict[str, int]:
        """Categorize functions by file type/location.

        Returns:
            Dictionary mapping category names to function counts
        """
        categories: dict[str, int] = {}

        for file_path, functions in self.defined_functions.items():
            # Determine category based on file path
            if "/core/" in file_path or "\\core\\" in file_path:
                category = "core"
            elif "/ai/" in file_path or "\\ai\\" in file_path:
                category = "ai"
            elif "/system/" in file_path or "\\system\\" in file_path:
                category = "system"
            elif "/diagnostics/" in file_path or "\\diagnostics\\" in file_path:
                category = "diagnostics"
            elif "/integration/" in file_path or "\\integration\\" in file_path:
                category = "integration"
            elif "/scripts/" in file_path or "\\scripts\\" in file_path:
                category = "scripts"
            elif "/tools/" in file_path or "\\tools\\" in file_path:
                category = "tools"
            elif "/utils/" in file_path or "\\utils\\" in file_path:
                category = "utils"
            else:
                category = "other"

            if category not in categories:
                categories[category] = 0
            categories[category] += len(functions)

        return categories

    def _get_all_functions_list(self) -> list[dict[str, Any]]:
        """Get a flat list of all functions with metadata.

        Returns:
            List of dictionaries containing function metadata
        """
        all_functions: list[dict[str, Any]] = []

        for file_path, functions in self.defined_functions.items():
            for func in functions:
                all_functions.append(
                    {
                        "name": func["name"],
                        "file": file_path,
                        "line": func["line"],
                        "args": func["args"],
                        "is_async": func["is_async"],
                        "class_method": func["class_method"],
                        "class_name": func.get("class_name", ""),
                        "docstring": (
                            func["docstring"][:100] + "..."
                            if len(func["docstring"]) > 100
                            else func["docstring"]
                        ),
                    }
                )

        # Sort alphabetically by name
        all_functions.sort(key=lambda x: x["name"].lower())
        return all_functions


def main() -> None:
    """Run the complete function registry analysis and export results."""
    print("🔍 Complete System Function Registry")
    print("=" * 50)

    registry = CompleteFunctionRegistry()

    # Read optional scan controls from environment
    max_files_env = os.getenv("NUSYQ_REGISTRY_MAX_FILES")
    max_files = None
    if max_files_env:
        try:
            max_files = int(max_files_env)
        except ValueError:
            print(f"⚠️ Invalid NUSYQ_REGISTRY_MAX_FILES='{max_files_env}', ignoring.")

    exclude_env = os.getenv("NUSYQ_REGISTRY_EXCLUDE", "")
    exclude_patterns = [p.strip() for p in exclude_env.split(",") if p.strip()] or None

    # Scan repository
    registry.scan_repository(max_files=max_files, exclude_patterns=exclude_patterns)

    # Export markdown reference
    md_path = registry.export_function_registry()

    # Export JSON data
    json_path = registry.export_json_data()

    # Export undefined calls focused report
    registry.export_undefined_calls_report()

    print("\n📊 Analysis Complete!")
    print(f"📄 Markdown Reference: {md_path}")
    print(f"📊 JSON Data: {json_path}")

    # Summary
    total_functions = sum(len(funcs) for funcs in registry.defined_functions.values())
    print("\n🎯 Summary:")
    print(f"  📁 Files analyzed: {len(registry.defined_functions)}")
    print(f"  🔧 Functions found: {total_functions}")
    print(f"  ⚠️ Undefined calls: {len(registry.undefined_calls)}")

    if registry.undefined_calls:
        print("\n⚠️ Most Common Undefined Calls:")
        undefined_names: dict[str, int] = {}
        for call in registry.undefined_calls:
            name = call["function_name"]
            undefined_names[name] = undefined_names.get(name, 0) + 1

        for name, count in sorted(undefined_names.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {name}: {count} calls")


if __name__ == "__main__":
    main()
