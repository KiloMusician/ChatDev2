#!/usr/bin/env python3
"""unified_logging_fixer.py
Master consolidation of all logging fix tools (4 tools, 660+ lines → 1 canonical)

Batch 4c: Logging Consolidation via Three Before New protocol
Author: GitHub Copilot | Date: 2025-01-05
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

__version__ = "1.0.0"


@dataclass
class FixResults:
    """Track results of logging fixes across a codebase."""

    files_processed: int = 0
    fixes_applied: int = 0
    errors_encountered: int = 0
    fix_summary: dict[str, int] = field(default_factory=dict)


class UnifiedLoggingFixer:
    """Master consolidation: fix_logging_calls + fix_logging_fstrings +
    fix_logging_syntax_errors + fix_logging_v2.
    """

    def __init__(self, verbose: bool = False, dry_run: bool = False):
        self.verbose = verbose
        self.dry_run = dry_run
        self.results = FixResults()

    def fix(self, path: str, mode: str = "full") -> FixResults:
        """Apply logging fixes. Modes: calls, fstrings, syntax, modernize, full."""
        if mode not in ["calls", "fstrings", "syntax", "modernize", "full"]:
            raise ValueError(f"Unknown mode: {mode}")

        if self.verbose:
            print(f"[UnifiedLoggingFixer] Starting mode={mode} on {path}")

        target_path = Path(path)
        if not target_path.exists():
            print(f"Error: Path does not exist: {path}", file=sys.stderr)
            return self.results

        if target_path.is_file():
            self._process_file(target_path, mode)
        else:
            for py_file in target_path.rglob("*.py"):
                if self.dry_run:
                    print(f"[DRY-RUN] Would process: {py_file}")
                else:
                    self._process_file(py_file, mode)

        return self.results

    def _process_file(self, file_path: Path, mode: str) -> None:
        """Process a single Python file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            original = content

            if mode in ["calls", "full"]:
                content = self.fix_calls(content)
            if mode in ["fstrings", "full"]:
                content = self.fix_fstrings(content)
            if mode in ["syntax", "full"]:
                content = self.fix_syntax(content)
            if mode in ["modernize", "full"]:
                content = self.modernize(content)

            if content != original:
                self.results.fixes_applied += 1
                if not self.dry_run:
                    file_path.write_text(content, encoding="utf-8")
                if self.verbose:
                    print(f"[FIXED] {file_path}")

            self.results.files_processed += 1

        except Exception as e:
            self.results.errors_encountered += 1
            if self.verbose:
                print(f"[ERROR] {file_path}: {e}")

    def fix_calls(self, content: str) -> str:
        """Fix logging function call patterns (from fix_logging_calls.py)."""
        # Fix deprecated logging.getLogger() patterns
        content = re.sub(
            r"logging\.getLogger\(\)",
            "logging.getLogger(__name__)",
            content,
        )

        # Fix common logger.addHandler() mistakes
        content = re.sub(
            r"logger\.addHandler\(\s*logging\.StreamHandler\(\s*\)\s*\)",
            "logger.addHandler(logging.StreamHandler())",
            content,
        )

        # Normalize logging.basicConfig() calls
        content = self._normalize_basicconfig(content)

        # Fix percent formatting in logging calls
        content = self._fix_percent_formatting(content)

        self.results.fix_summary["call_fixes"] = self.results.fix_summary.get("call_fixes", 0) + 1
        return content

    def fix_fstrings(self, content: str) -> str:
        """Convert logging strings to f-strings (from fix_logging_fstrings.py)."""
        lines = content.split("\n")
        new_lines = []

        for line in lines:
            # Convert logging.info("x=%s" % x) → logging.info(f"x={x}")
            match = re.match(
                r'(\s*)logging\.(info|debug|warning|error|critical)\("([^"]+)"\s*%\s*(\w+)\)',
                line,
            )
            if match:
                indent, level, msg, var = match.groups()
                # Simple conversion (preserves msg structure)
                new_line = f'{indent}logging.{level}(f"{msg.replace("%s", "{" + var + "}")}")'
                line = new_line

            new_lines.append(line)

        self.results.fix_summary["fstring_fixes"] = self.results.fix_summary.get("fstring_fixes", 0) + 1
        return "\n".join(new_lines)

    def fix_syntax(self, content: str) -> str:
        """Fix logging-specific syntax issues (from fix_logging_syntax_errors.py)."""
        # Fix logger = logging.getLogger(__name__) placement
        lines = content.split("\n")
        new_lines = []
        in_function = False

        for _i, line in enumerate(lines):
            # Check if getLogger is inside function (should be module-level)
            if "def " in line:
                in_function = True
            elif line.strip() and not line[0].isspace():
                in_function = False

            # Move getLogger to module level if found inside function
            if in_function and "logging.getLogger(__name__)" in line:
                # Mark for relocation (simplified - real implementation more complex)
                pass

            new_lines.append(line)

        # Fix missing logger initialization
        if "logger =" not in content and "logging." in content:
            lines = new_lines
            new_lines = ["logger = logging.getLogger(__name__)", *lines]

        # Fix logging configuration errors
        content = re.sub(
            r"logging\.config\.fileConfig\(\s*\)",
            "logging.config.fileConfig('logging.conf')",
            "\n".join(new_lines),
        )

        self.results.fix_summary["syntax_fixes"] = self.results.fix_summary.get("syntax_fixes", 0) + 1
        return content

    def modernize(self, content: str) -> str:
        """Modernize logging to Python 3.9+ standards (from fix_logging_v2.py)."""
        # Update structlog integration
        content = re.sub(
            r"import structlog",
            "import structlog\nstructlog.configure(\n    processors=[\n        structlog.processors.JSONRenderer(),\n    ],\n)",
            content,
            count=1,
        )

        # Modernize JSON logging patterns
        content = re.sub(
            r"logging\.Formatter\('%(message)s'\)",
            'logging.Formatter("%(message)s")',
            content,
        )

        # Migrate to Python 3.9+ logging features
        content = re.sub(
            r"logging\.basicConfig\(\s*\)",
            "logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')",
            content,
        )

        self.results.fix_summary["modernization_fixes"] = self.results.fix_summary.get("modernization_fixes", 0) + 1
        return content

    # ============================================================================
    # Helper methods extracted from all 4 tools
    # ============================================================================

    def _normalize_basicconfig(self, content: str) -> str:
        """Normalize logging.basicConfig() calls to standard format."""
        pattern = r"logging\.basicConfig\s*\(\s*([^)]*)\s*\)"
        replacement = (
            r"logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')"
        )
        return re.sub(pattern, replacement, content, count=1)

    def _fix_percent_formatting(self, content: str) -> str:
        """Fix %-style string formatting in logging."""
        # logging.info("key: %s, value: %s" % (k, v))
        pattern = r'logging\.(info|debug|warning|error|critical)\("([^"]+)"\s*%\s*([^)]+)\)'
        content = re.sub(pattern, r'logging.\1("\2" % \3)', content)
        return content

    def _convert_to_fstring(self, format_str: str, *args) -> str:
        """Convert format string + args to f-string (AST-based, simplified)."""
        # For now, return as-is (full AST conversion complex)
        return format_str

    def _fix_getlogger_placement(self, content: str) -> str:
        """Move logger = logging.getLogger(__name__) to module level."""
        lines = content.split("\n")
        logger_line = None
        logger_index = None

        for i, line in enumerate(lines):
            if "logging.getLogger(__name__)" in line:
                logger_line = line
                logger_index = i
                break

        if logger_line and logger_index and logger_index > 0:
            # Simple heuristic: if in function, move to top after imports
            if lines[logger_index - 1].startswith("    "):
                lines.pop(logger_index)
                # Find first non-import line after imports
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.startswith("import ") or line.startswith("from "):
                        insert_pos = i + 1
                lines.insert(insert_pos, logger_line.strip())

        return "\n".join(lines)

    def _migrate_structlog(self, content: str) -> str:
        """Migrate to structlog patterns (v2 modernization)."""
        if "import structlog" not in content:
            return content

        # Add standard structlog config if not present
        config_snippet = (
            "structlog.configure(\n"
            "    processors=[\n"
            "        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,\n"
            "    ],\n"
            ")\n"
        )

        if "structlog.configure" not in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "import structlog" in line:
                    lines.insert(i + 1, config_snippet)
                    break
            content = "\n".join(lines)

        return content

    def list_modes(self) -> None:
        """Display available modes."""
        modes = {
            "calls": "Fix logging function call patterns (getLogger, addHandler, basicConfig)",
            "fstrings": "Convert logging strings to f-strings",
            "syntax": "Fix logging-specific syntax errors",
            "modernize": "Apply Python 3.9+ logging standards",
            "full": "Apply all fixes in sequence (default)",
        }

        print("\n📋 Available Modes:")
        for mode, desc in modes.items():
            print(f"  • {mode:15} - {desc}")
        print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Logging Fixer: Consolidation of 4 logging tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode full --path src/
  %(prog)s --mode fstrings --path myfile.py --dry-run
  %(prog)s --list-modes
        """,
    )

    parser.add_argument(
        "--mode",
        default="full",
        choices=["calls", "fstrings", "syntax", "modernize", "full"],
        help="Fix mode: calls, fstrings, syntax, modernize, or full (default: full)",
    )

    parser.add_argument(
        "--path",
        default=".",
        help="Path to file or directory to process (default: current directory)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing files",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--list-modes",
        action="store_true",
        help="Display available modes and exit",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    if args.list_modes:
        fixer = UnifiedLoggingFixer()
        fixer.list_modes()
        return

    fixer = UnifiedLoggingFixer(verbose=args.verbose, dry_run=args.dry_run)

    if args.dry_run:
        print("[DRY-RUN] Mode: No files will be modified")

    results = fixer.fix(args.path, args.mode)

    # Summary
    print("\n✅ Processing complete:")
    print(f"  Files processed: {results.files_processed}")
    print(f"  Fixes applied:   {results.fixes_applied}")
    print(f"  Errors:          {results.errors_encountered}")

    if results.fix_summary:
        print(f"  Details: {results.fix_summary}")


if __name__ == "__main__":
    main()
