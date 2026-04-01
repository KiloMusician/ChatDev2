"""Smoke Test Runner for Testing Chamber.

Executes lightweight smoke tests on staged code to verify basic functionality.

Tests:
- boot: Can the file be parsed?
- import: Can the module be imported?
- render: Does basic structure exist?
- syntax: Is Python syntax valid?

Version: 1.0.0
"""

import ast
import importlib.util
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class SmokeTestRunner:
    """Runs smoke tests on Python files to verify basic functionality."""

    def __init__(self, timeout_seconds: int = 30) -> None:
        """Initialize smoke test runner.

        Args:
            timeout_seconds: Maximum time for each test

        """
        self.timeout = timeout_seconds

    def run_all_tests(self, file_path: Path) -> dict[str, bool]:
        """Run all smoke tests on a file.

        Args:
            file_path: Path to Python file

        Returns:
            dict mapping test names to pass/fail results

        """
        logger.info("🧪 Running smoke tests on %s...", file_path.name)

        results = {
            "boot": self.test_boot(file_path),
            "import": self.test_import(file_path),
            "render": self.test_render(file_path),
            "syntax": self.test_syntax(file_path),
        }

        passed = sum(results.values())
        total = len(results)
        logger.info("   Results: %s/%s passed", passed, total)

        return results

    def test_boot(self, file_path: Path) -> bool:
        """Test: Can the file be parsed without errors?

        Args:
            file_path: Path to file

        Returns:
            True if file can be parsed

        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Try to parse as AST
            ast.parse(content)
            logger.debug("✅ boot: %s parses successfully", file_path.name)
            return True

        except SyntaxError as e:
            logger.debug("❌ boot: Syntax error in %s: %s", file_path.name, e)
            return False
        except Exception as e:
            logger.debug("❌ boot: Error parsing %s: %s", file_path.name, e)
            return False

    def test_import(self, file_path: Path) -> bool:
        """Test: Can the module be imported?

        Args:
            file_path: Path to file

        Returns:
            True if module can be imported

        """
        try:
            # Create module spec
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            if spec is None or spec.loader is None:
                logger.debug("❌ import: Could not create spec for %s", file_path.name)
                return False

            # Try to load the module (but don't execute it fully)
            # This checks if imports resolve
            module = importlib.util.module_from_spec(spec)

            # Add to sys.modules temporarily
            sys.modules[module_name] = module

            try:
                spec.loader.exec_module(module)
                logger.debug("✅ import: %s imports successfully", file_path.name)
                return True
            finally:
                # Clean up
                if module_name in sys.modules:
                    del sys.modules[module_name]

        except ImportError as e:
            logger.debug("❌ import: Import error in %s: %s", file_path.name, e)
            return False
        except Exception as e:
            logger.debug("❌ import: Error importing %s: %s", file_path.name, e)
            return False

    def test_render(self, file_path: Path) -> bool:
        """Test: Does the file have basic structure?

        Checks:
        - Non-empty file
        - Has docstring or comments
        - Has at least one function/class definition

        Args:
            file_path: Path to file

        Returns:
            True if file has basic structure

        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Check non-empty
            if len(content.strip()) == 0:
                logger.debug("❌ render: %s is empty", file_path.name)
                return False

            # Parse AST
            tree = ast.parse(content)

            # Check for at least one function or class
            has_definition = any(
                isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))
                for node in ast.walk(tree)
            )

            # Check for docstring
            has_docstring = ast.get_docstring(tree) is not None

            if has_definition or has_docstring:
                logger.debug("✅ render: %s has basic structure", file_path.name)
                return True
            logger.debug("❌ render: %s lacks definitions", file_path.name)
            return False

        except Exception as e:
            logger.debug("❌ render: Error checking structure of %s: %s", file_path.name, e)
            return False

    def test_syntax(self, file_path: Path) -> bool:
        """Test: Is Python syntax valid?

        Uses Python's own syntax checker.

        Args:
            file_path: Path to file

        Returns:
            True if syntax is valid

        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(file_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.returncode == 0:
                logger.debug("✅ syntax: %s has valid syntax", file_path.name)
                return True
            logger.debug("❌ syntax: %s has syntax errors: %s", file_path.name, result.stderr)
            return False

        except subprocess.TimeoutExpired:
            logger.debug("❌ syntax: Syntax check timed out for %s", file_path.name)
            return False
        except Exception as e:
            logger.debug("❌ syntax: Error checking syntax of %s: %s", file_path.name, e)
            return False

    def run_custom_test(self, file_path: Path, test_command: str) -> tuple[bool, str]:
        """Run a custom test command.

        Args:
            file_path: Path to file
            test_command: Command to run (e.g., "pytest {file}")

        Returns:
            tuple of (passed, output)

        """
        try:
            command = test_command.replace("{file}", str(file_path))

            result = subprocess.run(
                command.split(),
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            passed = result.returncode == 0
            output = result.stdout + result.stderr

            return passed, output

        except subprocess.TimeoutExpired:
            return False, f"Test timed out after {self.timeout}s"
        except Exception as e:
            return False, f"Test error: {e}"


# ==================================================================
# CLI INTERFACE
# ==================================================================


def main() -> None:
    """CLI interface for smoke test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Smoke Test Runner")
    parser.add_argument("file", help="Python file to test")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    runner = SmokeTestRunner(timeout_seconds=args.timeout)
    results = runner.run_all_tests(Path(args.file))

    if args.json:
        pass
    else:
        for _test_name, _passed in results.items():
            pass

        sum(results.values())
        len(results)


if __name__ == "__main__":
    main()
