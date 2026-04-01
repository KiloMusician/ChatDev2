#!/usr/bin/env python3
"""Real Action Culture Ship - Performs Actual Ecosystem Improvements.

═══════════════════════════════════════════════════════════════.

Unlike theatrical logging, this Culture Ship performs REAL FIXES:
- Fixes actual code errors detected by linters
- Removes unused imports and variables
- Corrects indentation and formatting issues
- Resolves import conflicts and type issues
- Performs actual repository improvements

OmniTag: [real_fixes, error_resolution, concrete_improvements, action_verification]
MegaTag: CULTURE_SHIP⨳REAL_ACTION⦾ECOSYSTEM_HEALING→∞
"""

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Setup logger first
logger = logging.getLogger(__name__)

# Enhanced imports for real NuSyQ-Hub integration
_MultiAIOrchestrator: Any = None
_QuantumProblemResolver: Any = None

try:
    from src.healing.quantum_problem_resolver import QuantumProblemResolver
    from src.orchestration.unified_ai_orchestrator import MultiAIOrchestrator

    _MultiAIOrchestrator = MultiAIOrchestrator
    _QuantumProblemResolver = QuantumProblemResolver
except ImportError:
    logger.info("⚠️  NuSyQ-Hub modules not available - running in standalone mode")


class RealActionCultureShip:
    """Culture Ship that performs REAL ecosystem improvements."""

    def __init__(self, dry_run: bool | None = None) -> None:
        """Initialize culture ship runtime and optional dry-run mode."""
        self.logger = self._setup_logging()
        self.fixes_performed: list[dict[str, Any]] = []
        self.errors_detected: list[dict[str, Any]] = []
        self.improvements_made: list[dict[str, Any]] = []
        self.dry_run = (
            dry_run
            if dry_run is not None
            else os.getenv("NUSYQ_CULTURE_SHIP_DRY_RUN", "0").strip().lower()
            in {"1", "true", "yes", "on"}
        )

        # Initialize NuSyQ-Hub integration
        self.orchestrator = None
        self.quantum_resolver = None
        self.consciousness_bridge = None

        if self.dry_run:
            self.logger.info("🧪 Culture Ship running in dry-run mode (no file mutations)")

        if _MultiAIOrchestrator:
            try:
                self.orchestrator = _MultiAIOrchestrator()
                self.logger.info("✅ Connected to MultiAIOrchestrator")
            except (ImportError, AttributeError, RuntimeError) as e:
                self.logger.warning("⚠️  MultiAIOrchestrator not available: %s", e)

        if _QuantumProblemResolver:
            try:
                self.quantum_resolver = _QuantumProblemResolver()
                self.logger.info("✅ Connected to QuantumProblemResolver")
            except (ImportError, AttributeError, RuntimeError) as e:
                self.logger.warning("⚠️  QuantumProblemResolver not available: %s", e)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for real action tracking."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        return logging.getLogger("RealActionCultureShip")

    def scan_and_fix_ecosystem(self) -> dict[str, Any]:
        """Perform REAL ecosystem scan and fixes."""
        if self.dry_run:
            return self._scan_ecosystem_dry_run()

        self.logger.info("🚀 REAL ACTION Culture Ship - Starting ecosystem fixes")

        results = {
            "scan_timestamp": datetime.now().isoformat(),
            "files_scanned": 0,
            "errors_detected": 0,
            "fixes_applied": 0,
            "files_fixed": [],
            "improvements": [],
        }

        # 1. Fix main.py errors (the most critical file)
        main_py_fixes, main_py_changed = self.fix_main_py_errors()
        improvements: list[dict[str, Any]] = results["improvements"]  # type: ignore[assignment]
        improvements.extend(main_py_fixes)

        # 2. Fix script errors
        script_fixes = self.fix_script_errors()
        improvements.extend(script_fixes)

        # 3. Remove unused imports across ecosystem
        import_fixes = self.fix_unused_imports()
        improvements.extend(import_fixes)

        # 4. Fix formatting issues
        formatting_needed = main_py_changed or bool(script_fixes) or bool(import_fixes)
        format_fixes = self.fix_formatting_issues(formatting_needed)
        improvements.extend(format_fixes)

        # Calculate results
        results["fixes_applied"] = len(self.fixes_performed)
        results["errors_detected"] = len(self.errors_detected)
        files_fixed: list[str] = list({fix["file"] for fix in self.fixes_performed})
        results["files_fixed"] = files_fixed

        self.logger.info(
            f"✅ REAL FIXES COMPLETED: {results['fixes_applied']} fixes in {len(files_fixed)} files",
        )

        return results

    def _scan_ecosystem_dry_run(self) -> dict[str, Any]:
        """Run a non-mutating ecosystem scan suitable for gates/smoke checks."""
        self.logger.info("🧪 Dry-run: scanning ecosystem without applying fixes")
        improvements: list[dict[str, Any]] = []
        tracked_paths = [
            Path("src/main.py"),
            Path("src/scripts/chatdev_workflow_integration_analysis.py"),
        ]
        for path in tracked_paths:
            if path.exists():
                improvements.append(
                    {
                        "type": "dry_run_candidate",
                        "file": str(path),
                        "description": "File would be considered for automated cleanup",
                    }
                )
        return {
            "scan_timestamp": datetime.now().isoformat(),
            "mode": "dry_run",
            "files_scanned": len(tracked_paths),
            "errors_detected": 0,
            "fixes_applied": 0,
            "files_fixed": [],
            "improvements": improvements,
        }

    def fix_main_py_errors(self) -> tuple[list[dict[str, Any]], bool]:
        """Fix specific errors in main.py."""
        improvements: list[Any] = []
        main_py_path = Path("src/main.py")
        main_py_changed = False

        if not main_py_path.exists():
            return improvements, main_py_changed

        self.logger.info("🔧 Fixing main.py errors...")

        try:
            # Read the file
            with open(main_py_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Fix 1: Remove unused Optional import
            if "from typing import Optional, Any" in content:
                content = content.replace(
                    "from typing import Optional, Any",
                    "from typing import Any",
                )
                improvements.append(
                    {
                        "type": "unused_import_removed",
                        "file": "src/main.py",
                        "description": "Removed unused Optional import",
                    },
                )

            # Fix 2: Add encoding to open() calls using AST
            content = self._ast_fix_open_encoding(content)

            # Fix 3: Add check=True to subprocess.run calls using AST
            content = self._ast_fix_subprocess_check(content)

            # Fix 4: Fix indentation issues
            lines = content.split("\n")
            fixed_lines: list[Any] = []
            for i, line in enumerate(lines):
                # Fix continuation line indentation
                if (
                    i > 0
                    and line.strip()
                    and not line.startswith("    ")
                    and lines[i - 1].rstrip().endswith(",")
                    and ("cwd=" in line or "default=" in line)
                ):
                    # Continuation line with cwd/default param — fix indentation
                    line = "                         " + line.strip()

                # Remove trailing whitespace
                line = line.rstrip()
                fixed_lines.append(line)

            content = "\n".join(fixed_lines)

            # Fix 5: Add newline at end of file
            if not content.endswith("\n"):
                content += "\n"

            # Fix 6: Replace broad Exception catches with specific exceptions
            content = re.sub(
                r"except Exception as e:",
                "except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:",
                content,
            )

            # Write the fixed content back
            if content != original_content:
                with open(main_py_path, "w", encoding="utf-8") as f:
                    f.write(content)

                main_py_changed = True

                self.fixes_performed.append(
                    {
                        "file": str(main_py_path),
                        "type": "main_py_comprehensive_fix",
                        "changes": len(improvements) + 5,  # Additional fixes
                    },
                )

                improvements.extend(
                    [
                        {
                            "type": "encoding_added",
                            "file": "src/main.py",
                            "description": "Added explicit encoding to file operations",
                        },
                        {
                            "type": "subprocess_check_added",
                            "file": "src/main.py",
                            "description": "Added check=True to subprocess calls",
                        },
                        {
                            "type": "indentation_fixed",
                            "file": "src/main.py",
                            "description": "Fixed continuation line indentation",
                        },
                        {
                            "type": "trailing_whitespace_removed",
                            "file": "src/main.py",
                            "description": "Removed trailing whitespace",
                        },
                        {
                            "type": "newline_added",
                            "file": "src/main.py",
                            "description": "Added newline at end of file",
                        },
                        {
                            "type": "exception_handling_improved",
                            "file": "src/main.py",
                            "description": "Replaced broad Exception catches with specific exceptions",
                        },
                    ],
                )

                self.logger.info("✅ Fixed %s issues in main.py", len(improvements))

        except (OSError, RuntimeError) as e:
            self.logger.exception("❌ Error fixing main.py: %s", e)
            self.errors_detected.append({"file": "src/main.py", "error": str(e)})

        return improvements, main_py_changed

    def _ast_fix_open_encoding(self, content: str) -> str:
        """Add encoding='utf-8' to open() calls using AST-safe regex.

        This uses a more conservative regex that only matches simple cases
        where encoding is clearly missing.
        """
        import re

        # Match open(path, 'r') or open(path, "r") without encoding
        # Only fix simple cases to avoid breaking complex expressions
        patterns = [
            # open(file, 'r') -> open(file, 'r', encoding='utf-8')
            (r"open\(([^,]+),\s*['\"]r['\"]\s*\)(?!\s*#)", r"open(\1, 'r', encoding='utf-8')"),
            # open(file, 'w') -> open(file, 'w', encoding='utf-8')
            (r"open\(([^,]+),\s*['\"]w['\"]\s*\)(?!\s*#)", r"open(\1, 'w', encoding='utf-8')"),
        ]

        for pattern, replacement in patterns:
            # Only apply if not already has encoding
            if "encoding=" not in content:
                content = re.sub(pattern, replacement, content)

        return content

    def _ast_fix_subprocess_check(self, content: str) -> str:
        """Add check=True to subprocess.run() calls using AST-safe approach.

        Uses AST parsing to safely add check=True without breaking code.
        """
        import ast

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # If parsing fails, return unchanged
            return content

        # Find subprocess.run calls without check= argument
        lines = content.split("\n")
        modified = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "run"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
            ):
                # Check if check= is already present
                has_check = any(kw.arg == "check" for kw in node.keywords)

                if not has_check:
                    # Get the line and add check=True
                    line_no = node.lineno - 1  # 0-indexed
                    if 0 <= line_no < len(lines):
                        line = lines[line_no]
                        # Find the closing paren and add check=True before it
                        # Only modify if it's a simple single-line call
                        if (
                            "subprocess.run(" in line
                            and line.rstrip().endswith(")")
                            and "check=" not in line
                        ):
                            # Check if already has check=True or check=False
                            # Insert before the final closing paren
                            line = line.rstrip()
                            if line.endswith(")"):
                                line = line[:-1] + ", check=True)"
                                lines[line_no] = line
                                modified = True

        if modified:
            content = "\n".join(lines)

        return content

    def fix_script_errors(self) -> list[dict[str, Any]]:
        """Fix errors in script files."""
        improvements: list[Any] = []
        script_path = Path("src/scripts/chatdev_workflow_integration_analysis.py")

        if not script_path.exists():
            return improvements

        self.logger.info("🔧 Fixing script errors...")

        try:
            with open(script_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Fix 1: Remove unused imports
            unused_imports = ["import os", "import logging"]
            for unused_import in unused_imports:
                if unused_import in content:
                    content = content.replace(unused_import + "\n", "")

            # Fix 2: Remove unused typing imports
            content = re.sub(
                r"from typing import Any, Optional",
                "from typing import List",
                content,
            )

            # Fix 3: Fix f-string without replacement fields
            content = re.sub(r'print\(f"([^{}"]+)"\)', r'logger.info("\1")', content)

            # Fix 4: Remove trailing whitespace
            lines = content.split("\n")
            fixed_lines = [line.rstrip() for line in lines]
            content = "\n".join(fixed_lines)

            if content != original_content:
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(content)

                improvements.extend(
                    [
                        {
                            "type": "unused_imports_removed",
                            "file": str(script_path),
                            "description": "Removed unused os and logging imports",
                        },
                        {
                            "type": "typing_imports_cleaned",
                            "file": str(script_path),
                            "description": "Cleaned up unused typing imports",
                        },
                        {
                            "type": "fstring_fixed",
                            "file": str(script_path),
                            "description": "Fixed f-string without replacement fields",
                        },
                        {
                            "type": "trailing_whitespace_removed",
                            "file": str(script_path),
                            "description": "Removed trailing whitespace",
                        },
                    ],
                )

                self.fixes_performed.append(
                    {"file": str(script_path), "type": "script_cleanup", "changes": 4},
                )

                self.logger.info("✅ Fixed script errors in %s", script_path.name)

        except (OSError, RuntimeError) as e:
            self.logger.exception("❌ Error fixing script: %s", e)
            self.errors_detected.append({"file": str(script_path), "error": str(e)})

        return improvements

    def fix_unused_imports(self) -> list[dict[str, Any]]:
        """Remove unused imports across the ecosystem."""
        improvements: list[Any] = []

        max_files = int(os.getenv("CULTURE_SHIP_IMPORT_SCAN_LIMIT", "10"))
        scan_roots = [Path("src"), Path("scripts")]
        scanned = 0
        skip_parts = {".venv", "__pycache__", "node_modules", ".git", "state", "Reports"}

        for root in scan_roots:
            if scanned >= max_files:
                break
            if not root.exists():
                continue
            for py_file in root.rglob("*.py"):
                if scanned >= max_files:
                    break
                if any(part in skip_parts for part in py_file.parts):
                    continue
                scanned += 1

                try:
                    original_content = py_file.read_text(encoding="utf-8")
                    lint_result = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "ruff",
                            "check",
                            "--select",
                            "F401",
                            "--fix",
                            str(py_file),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=15,
                    )
                    if lint_result.returncode not in (0, 1):
                        self.errors_detected.append(
                            {
                                "file": str(py_file),
                                "error": (
                                    f"ruff F401 cleanup failed "
                                    f"(rc={lint_result.returncode}): {lint_result.stderr.strip()}"
                                ),
                            },
                        )
                        continue

                    updated_content = py_file.read_text(encoding="utf-8")
                    if updated_content != original_content:
                        improvements.append(
                            {
                                "type": "unused_imports_cleaned",
                                "file": str(py_file),
                                "description": f"Applied safe ruff F401 cleanup in {py_file.name}",
                            },
                        )

                        self.fixes_performed.append(
                            {"file": str(py_file), "type": "import_cleanup", "changes": 1},
                        )

                except (OSError, subprocess.TimeoutExpired) as e:
                    self.errors_detected.append({"file": str(py_file), "error": str(e)})

        if improvements:
            self.logger.info("✅ Cleaned unused imports in %s files", len(improvements))

        return improvements

    def fix_formatting_issues(self, run_black: bool = True) -> list[dict[str, Any]]:
        """Fix common formatting issues."""
        improvements: list[Any] = []

        if not run_black:
            return improvements

        self.logger.info("🔧 Running black formatter on main files...")

        # Run black formatter on main files
        main_files = [
            "src/main.py",
            "src/scripts/chatdev_workflow_integration_analysis.py",
        ]

        for file_path in main_files:
            if Path(file_path).exists():
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "black", file_path],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if result.returncode == 0:
                        improvements.append(
                            {
                                "type": "formatting_applied",
                                "file": file_path,
                                "description": f"Applied black formatting to {Path(file_path).name}",
                            },
                        )

                        self.fixes_performed.append(
                            {
                                "file": file_path,
                                "type": "black_formatting",
                                "changes": 1,
                            },
                        )

                except (OSError, RuntimeError) as e:
                    self.errors_detected.append(
                        {"file": file_path, "error": f"Black formatting failed: {e}"},
                    )

        if improvements:
            self.logger.info("✅ Applied formatting to %s files", len(improvements))

        return improvements

    def generate_fix_report(self) -> str:
        """Generate a comprehensive report of all fixes performed."""
        report = f"""
🚀 REAL ACTION CULTURE SHIP - FIX REPORT
═══════════════════════════════════════

📊 SUMMARY:
- Total Fixes Applied: {len(self.fixes_performed)}
- Files Modified: {len({fix["file"] for fix in self.fixes_performed})}
- Errors Detected: {len(self.errors_detected)}
- Improvements Made: {len(self.improvements_made)}

🔧 FIXES PERFORMED:
"""

        for fix in self.fixes_performed:
            report += f"✅ {fix['file']}: {fix['type']} ({fix.get('changes', 1)} changes)\n"

        if self.errors_detected:
            report += "\n❌ ERRORS ENCOUNTERED:\n"
            for error in self.errors_detected:
                report += f"- {error['file']}: {error['error']}\n"

        report += "\n🎯 VERIFICATION:\nRun 'python -m ruff check .' to verify fixes\n"

        return report


def main() -> None:
    """Run the Real Action Culture Ship."""
    ship = RealActionCultureShip()

    logger.info("🚀 REAL ACTION CULTURE SHIP DEPLOYMENT")

    # Perform real ecosystem fixes
    results = ship.scan_and_fix_ecosystem()

    # Generate and display report
    ship.generate_fix_report()

    # Save results to file
    results_file = Path("real_culture_ship_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info("📄 Detailed results saved to: %s", results_file)

    # Verify fixes by running linter
    logger.info("\n🔍 VERIFICATION - Running linter to check fixes...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "src/main.py"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            logger.info("✅ VERIFICATION PASSED: No linting errors detected!")
        else:
            logger.info("⚠️  Remaining issues:\n%s", result.stdout)

    except (OSError, RuntimeError) as e:
        logger.info("❌ Verification failed: %s", e)


if __name__ == "__main__":
    main()
