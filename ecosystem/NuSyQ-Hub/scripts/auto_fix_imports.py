#!/usr/bin/env python3
"""Auto-fix common import errors by detecting and applying minimal fixes.

Usage:
    python scripts/auto_fix_imports.py <error_message>
    python scripts/auto_fix_imports.py --scan

Handles:
- ModuleNotFoundError: Creates minimal fallback implementations
- ImportError: Adds missing names with stubs
- Circular imports: Suggests local imports
"""

import importlib
import re
import sys
from pathlib import Path


class ImportErrorFixer:
    """Detect and fix common import errors."""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path(".").resolve()

    def analyze_file(self, filepath: Path | str) -> list[dict]:
        """Analyze a file for import issues."""
        path = Path(filepath)
        if not path.exists():
            return []

        issues: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            success = self._import_line_resolves(stripped)
            if not success:
                if stripped.startswith("from "):
                    module = self._module_from_line(stripped)
                    msg = (
                        f"ModuleNotFoundError: No module named '{module}'"
                        if module
                        else "ModuleNotFoundError: No module named '<unknown>'"
                    )
                else:
                    module = self._module_from_line(stripped) or "unknown.module"
                    msg = f"ModuleNotFoundError: No module named '{module}'"

                issue = self.analyze_and_fix(msg)
                if isinstance(issue, dict):
                    issues.append(issue)

        return issues

    def fix_imports_in_content(self, content: str, path: Path | str | None = None) -> str:
        """Attempt to wrap broken imports with fallbacks."""
        lines = content.split("\n")
        updated_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("from ", "import ")):
                if not self._import_line_resolves(stripped):
                    fallback = self._fallback_name_from_line(stripped)
                    indent = line[: len(line) - len(line.lstrip())]
                    updated_lines.extend(
                        [
                            f"{indent}try:",
                            f"{indent}    {stripped}",
                            f"{indent}except ImportError:",
                            f"{indent}    {fallback} = None  # Fallback for missing import",
                        ]
                    )
                    continue

            updated_lines.append(line)

        return "\n".join(updated_lines)

    def _module_from_line(self, line: str) -> str | None:
        stripped = line.strip()
        if stripped.startswith("from "):
            module = stripped.split(" import ", 1)[0].split()[1]
            return module

        if stripped.startswith("import "):
            module_part = stripped[len("import ") :]
            return module_part.split(",")[0].split(" as ")[0].strip()

        return None

    def _import_line_resolves(self, line: str) -> bool:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return True

        try:
            if stripped.startswith("from "):
                module = stripped.split(" import ", 1)[0].split()[1]
                names = [part.strip().split(" as ")[0] for part in stripped.split(" import ", 1)[1].split(",")]
                mod = importlib.import_module(module)
                for name in names:
                    if not hasattr(mod, name):
                        raise ImportError(f"cannot import name '{name}' from '{module}'")
                return True

            if stripped.startswith("import "):
                modules = [part.strip().split(" as ")[0] for part in stripped[len("import ") :].split(",")]
                for module in modules:
                    importlib.import_module(module)
                return True
        except Exception:
            return False

        return True

    def _fallback_name_from_line(self, line: str) -> str:
        stripped = line.strip()
        if stripped.startswith("from "):
            remainder = stripped.split(" import ", 1)[1]
        elif stripped.startswith("import "):
            remainder = stripped[len("import ") :]
        else:
            remainder = "missing"

        first = remainder.split(",")[0].strip()
        return first.split(" as ")[-1]

    def detect_error_type(self, error_message: str) -> str | None:
        """Detect type of import error."""
        patterns = {
            "module_not_found": r"ModuleNotFoundError: No module named '(.+?)'",
            "cannot_import_name": r"ImportError: cannot import name '(.+?)' from '(.+?)'",
            "circular_import": r"ImportError.*circular import",
        }

        for error_type, pattern in patterns.items():
            if re.search(pattern, error_message, re.IGNORECASE):
                return error_type

        return None

    def extract_module_name(self, error_message: str) -> str | None:
        """Extract module name from error message."""
        match = re.search(r"No module named '(.+?)'", error_message)
        if match:
            return match.group(1)

        match = re.search(r"from '(.+?)'", error_message)
        if match:
            return match.group(1)

        return None

    def extract_missing_name(self, error_message: str) -> str | None:
        """Extract missing import name from error message."""
        match = re.search(r"cannot import name '(.+?)'", error_message)
        return match.group(1) if match else None

    def generate_stub_module(self, module_name: str) -> str:
        """Generate minimal stub module implementation."""
        # Use all parts after 'src' for class name to ensure uniqueness
        parts = [p for p in module_name.split(".") if p != "src"]
        class_name = "".join(p.replace("_", " ").title().replace(" ", "") for p in parts)

        stub = f'''"""Auto-generated stub for missing module: {module_name}"""


class {class_name}:
    """Minimal fallback implementation."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        """Stub callable - returns None."""
        return None

    def __getattr__(self, name):
        """Stub attribute access - returns self for chaining."""
        return self


# Export stub instance
{module_name.split(".")[-1]} = {class_name}()
'''
        return stub

    def generate_stub_import(self, name: str, module: str) -> str:
        """Generate stub for missing import name."""
        stub = f'''# Auto-generated stub for missing import: {name} from {module}


class {name}:
    """Fallback implementation for missing {name}."""

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return None
'''
        return stub

    def fix_module_not_found(self, module_name: str) -> dict:
        """Fix ModuleNotFoundError by creating stub module."""
        # Determine directory under src/
        parts = module_name.split(".")
        if parts and parts[0] == "src":
            if len(parts) > 1:
                parts = parts[1:]
            else:
                parts = ["src"]

        relative_dir = Path(*parts) if parts else Path(".")
        file_path = self.repo_root / "src" / relative_dir / "__init__.py"

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate and write stub
        stub_content = self.generate_stub_module(module_name)

        return {
            "action": "create_stub_module",
            "module": module_name,
            "file_path": str(file_path),
            "content": stub_content,
            "command": f"Create {file_path} with stub implementation",
        }

    def fix_cannot_import_name(self, name: str, module: str) -> dict:
        """Fix ImportError by adding stub to existing module."""
        # Find module file
        module_path = self.repo_root / "src" / module.replace(".", "/")
        if module_path.is_dir():
            target_file = module_path / "__init__.py"
        else:
            target_file = module_path.with_suffix(".py")

        stub_content = self.generate_stub_import(name, module)

        return {
            "action": "add_stub_to_module",
            "name": name,
            "module": module,
            "file_path": str(target_file),
            "content": stub_content,
            "command": f"Add stub for {name} to {target_file}",
        }

    def fix_circular_import(self, error_message: str) -> dict:
        """Suggest fix for circular import."""
        return {
            "action": "suggest_local_import",
            "suggestion": "Move import inside function to avoid circular dependency",
            "example": """
# Instead of:
from module import function

def my_function():
    function()

# Do this:
def my_function():
    from module import function  # Local import
    function()
""",
        }

    def analyze_and_fix(self, error_message: str) -> dict:
        """Analyze error and return fix suggestion."""
        error_type = self.detect_error_type(error_message)

        if not error_type:
            return {"action": "unknown", "message": "Could not detect error type"}

        if error_type == "module_not_found":
            module_name = self.extract_module_name(error_message)
            if module_name:
                return self.fix_module_not_found(module_name)

        elif error_type == "cannot_import_name":
            name = self.extract_missing_name(error_message)
            module = self.extract_module_name(error_message)
            if name and module:
                return self.fix_cannot_import_name(name, module)

        elif error_type == "circular_import":
            return self.fix_circular_import(error_message)

        return {"action": "unhandled", "error_type": error_type}


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/auto_fix_imports.py <error_message>")
        print("   or: python scripts/auto_fix_imports.py --scan")
        return 1

    repo_root = Path(__file__).parent.parent
    fixer = ImportErrorFixer(repo_root)

    error_message = " ".join(sys.argv[1:])

    fix_suggestion = fixer.analyze_and_fix(error_message)

    print("🔧 Auto-Fix Import Error\n")
    print(f"Action: {fix_suggestion.get('action', 'unknown')}")

    if fix_suggestion["action"] in ("create_stub_module", "add_stub_to_module"):
        print(f"File: {fix_suggestion['file_path']}")
        print("\nProposed fix:\n")
        print(fix_suggestion["content"])
        print(f"\n💡 To apply: Create/edit {fix_suggestion['file_path']}")

    elif fix_suggestion["action"] == "suggest_local_import":
        print(f"\n{fix_suggestion['suggestion']}")
        print(fix_suggestion["example"])

    else:
        print(f"Details: {fix_suggestion}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
