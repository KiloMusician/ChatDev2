#!/usr/bin/env python
"""T201 fixer: replace print() calls with logger.LEVEL() in src/ library modules.

Skip list (interactive terminal/game code where print IS the intended output):
  - src/games/**
  - src/culture_ship/integrated_terminal.py

For every other file in src/ that has T201 violations:
  1. Parse with ast to find all print() call nodes (handles multi-line)
  2. Replace print( with logger.LEVEL( (level inferred from message content)
  3. Add `import logging` if missing (top-level only)
  4. Add `logger = logging.getLogger(__name__)` if missing

Run: python scripts/fix_t201_print_to_logging.py [--dry-run]
"""

import ast
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"

# Files/dirs where print() is intentional output — skip conversion
SKIP_PATTERNS = [
    "games",  # src/games/** — game terminal output
    "culture_ship/integrated_terminal.py",  # terminal UI
]

# Indicators for logging level inference (checked in order)
ERROR_TOKENS = [
    "error",
    "Error",
    "ERROR",
    "fail",
    "Fail",
    "FAIL",
    "failed",
    "Failed",
    "FAILED",
    "failure",
    "Failure",
    "exception",
    "Exception",
    "EXCEPTION",
    "traceback",
    "❌",
    "✗",
    "✘",
]
WARNING_TOKENS = [
    "warn",
    "Warn",
    "WARN",
    "warning",
    "Warning",
    "WARNING",
    "⚠️",
    "⚠",
    "caution",
    "deprecated",
    "Deprecated",
]
DEBUG_TOKENS = [
    "debug",
    "Debug",
    "DEBUG",
    "trace",
    "Trace",
    "TRACE",
    "verbose",
]


def should_skip(path: Path) -> bool:
    """Return True if this file should NOT have print() converted."""
    rel = path.relative_to(SRC_ROOT).as_posix()
    for pattern in SKIP_PATTERNS:
        if rel.startswith(pattern) or rel == pattern:
            return True
    return False


def determine_level(call_text: str) -> str:
    """Infer logging level from the print() call text."""
    for token in ERROR_TOKENS:
        if token in call_text:
            return "error"
    for token in WARNING_TOKENS:
        if token in call_text:
            return "warning"
    for token in DEBUG_TOKENS:
        if token in call_text:
            return "debug"
    return "info"


def find_last_toplevel_import_line(tree: ast.Module) -> int:
    """Return the 1-based line number of the last top-level import statement.

    Only looks at ast.Import / ast.ImportFrom that are DIRECT children of the
    module body (col_offset == 0 and no indentation) — skips any lazy imports
    inside function/class bodies.

    Returns 0 if no top-level imports are found.
    """
    last_line = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # node.end_lineno handles multi-line `from x import (a, b, c)` forms
            end = node.end_lineno if node.end_lineno is not None else node.lineno
            if end > last_line:
                last_line = end
    return last_line


def insert_logger_setup(content: str, tree: ast.Module) -> str:
    """Add `import logging` and/or `logger = logging.getLogger(__name__)`.

    Insertion is placed immediately after the last top-level import block.
    Uses the pre-parsed AST to find the correct position (never touches
    function-body lazy imports).
    """
    has_logging_import = bool(re.search(r"^import logging\b", content, re.MULTILINE))
    has_logger_var = bool(
        re.search(r"^logger\s*[:=]", content, re.MULTILINE)
        or re.search(r"^logger\s*=\s*logging\.getLogger", content, re.MULTILINE)
    )

    if has_logging_import and has_logger_var:
        return content  # nothing to add

    lines = content.splitlines(keepends=True)

    insert_after = find_last_toplevel_import_line(tree)  # 1-based → index = insert_after
    if insert_after == 0:
        # No imports at all: insert at top, after any module docstring
        insert_after = 0
        for node in tree.body:
            if (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                # Module docstring
                insert_after = node.end_lineno if node.end_lineno is not None else node.lineno
                break

    # Build lines to insert (we insert them in order after `insert_after`)
    to_insert: list[str] = []
    if not has_logging_import:
        to_insert.append("import logging\n")
    if not has_logger_var:
        to_insert.append("logger = logging.getLogger(__name__)\n")

    if not to_insert:
        return content

    # Ensure a blank line separates the new block from whatever follows
    next_idx = insert_after  # 0-indexed position of the line AFTER insert point
    if next_idx < len(lines) and lines[next_idx].strip() != "":
        to_insert.append("\n")
    # And a blank line before (if the insertion point line isn't blank)
    if insert_after > 0 and lines[insert_after - 1].strip() != "":
        to_insert.insert(0, "\n")

    for i, extra in enumerate(to_insert):
        lines.insert(insert_after + i, extra)

    return "".join(lines)


def fix_file(path: Path, dry_run: bool = False) -> int:
    """Fix T201 violations in a single file. Returns count replaced."""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return 0

    # Collect all print() call expression nodes at ANY depth
    print_nodes: list[ast.Expr] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "print"
        ):
            print_nodes.append(node)  # type: ignore[arg-type]

    if not print_nodes:
        return 0

    # Sort descending by line so bottom-up replacement keeps preceding line
    # numbers valid throughout the loop
    print_nodes.sort(key=lambda n: n.lineno, reverse=True)

    lines = content.splitlines(keepends=True)
    replaced = 0

    for node in print_nodes:
        start = node.lineno - 1  # 0-indexed
        end = node.end_lineno - 1  # 0-indexed (same line for single-line calls)

        call_lines = lines[start : end + 1]
        call_text = "".join(call_lines)

        level = determine_level(call_text)

        # Replace the first `print(` with `logger.LEVEL(`
        new_text = re.sub(r"\bprint\(", f"logger.{level}(", call_text, count=1)

        if new_text != call_text:
            new_call_lines = new_text.splitlines(keepends=True)
            lines[start : end + 1] = new_call_lines
            replaced += 1

    if replaced == 0:
        return 0

    new_content = "".join(lines)

    # Add logger setup if needed (using the ORIGINAL tree for import positions)
    needs_logger = any(f"logger.{lvl}(" in new_content for lvl in ("info", "warning", "error", "debug", "critical"))
    has_logger_already = (
        "logger = logging.getLogger" in new_content
        or re.search(r"^logger\s*[:=]", new_content, re.MULTILINE) is not None
    )
    if needs_logger and not has_logger_already:
        new_content = insert_logger_setup(new_content, tree)

    if not dry_run:
        path.write_text(new_content, encoding="utf-8")

    return replaced


def get_t201_files() -> list[Path]:
    """Run ruff to get the list of files with T201 violations in src/."""
    result = subprocess.run(
        ["python", "-m", "ruff", "check", "src/", "--select=T201", "--output-format=concise"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    files: set[Path] = set()
    for line in (result.stdout + result.stderr).splitlines():
        if ".py:" in line:
            file_part = line.split(":")[0].strip()
            files.add(REPO_ROOT / file_part)
    return sorted(files)


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("[DRY RUN] No files will be modified.")

    files = get_t201_files()
    print(f"Found {len(files)} files with T201 violations.")

    total_replaced = 0
    skipped = 0
    changed_files: list[Path] = []

    for path in files:
        if should_skip(path):
            skipped += 1
            continue

        count = fix_file(path, dry_run=dry_run)
        if count > 0:
            rel = path.relative_to(REPO_ROOT).as_posix()
            print(f"  [{count:3d}]  {rel}")
            total_replaced += count
            changed_files.append(path)

    print(f"\nTotal prints replaced: {total_replaced}")
    print(f"Files modified: {len(changed_files)}")
    print(f"Files skipped (interactive): {skipped}")


if __name__ == "__main__":
    main()
