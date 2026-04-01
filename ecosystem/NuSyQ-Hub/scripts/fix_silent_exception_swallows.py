#!/usr/bin/env python3
"""Fix non-intentional silent exception swallows.

Converts `except SomeError: pass` → `except SomeError: logger.debug(...)` for
all non-intentional exception types. Intentional types (ImportError,
ModuleNotFoundError, KeyboardInterrupt, SystemExit, GeneratorExit) are skipped.

Usage:
    python scripts/fix_silent_exception_swallows.py --dry-run   # preview only
    python scripts/fix_silent_exception_swallows.py             # apply fixes
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple

# Exception types that are intentionally swallowed (optional deps, user interrupts)
INTENTIONAL_TYPES: set[str] = {
    "ImportError",
    "ModuleNotFoundError",
    "KeyboardInterrupt",
    "SystemExit",
    "GeneratorExit",
}

# ── helpers ────────────────────────────────────────────────────────────────────


class SwallowSite(NamedTuple):
    path: Path
    lineno: int  # 1-based line of `except` keyword
    exc_label: str  # human-readable exception type(s)
    body_lineno: int  # 1-based line of `pass`


def _exc_names_from_handler(handler: ast.ExceptHandler) -> list[str]:
    """Return all concrete exception names from an ExceptHandler node."""
    if handler.type is None:
        return ["bare"]
    if isinstance(handler.type, ast.Name):
        return [handler.type.id]
    if isinstance(handler.type, ast.Attribute):
        return [handler.type.attr]
    if isinstance(handler.type, ast.Tuple):
        names: list[str] = []
        for elt in ast.walk(handler.type):
            if isinstance(elt, ast.Name):
                names.append(elt.id)
        return names
    return ["unknown"]


def _is_intentional(names: list[str]) -> bool:
    """Return True if ALL names in the handler are intentional types."""
    return all(n in INTENTIONAL_TYPES for n in names)


def find_swallows(path: Path) -> list[SwallowSite]:
    """Return all non-intentional silent swallow sites in a Python file."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    sites: list[SwallowSite] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        # Must be a single `pass` body
        if len(node.body) != 1 or not isinstance(node.body[0], ast.Pass):
            continue
        names = _exc_names_from_handler(node)
        if _is_intentional(names):
            continue
        label = "/".join(sorted(set(names)))
        sites.append(
            SwallowSite(
                path=path,
                lineno=node.lineno,
                exc_label=label,
                body_lineno=node.body[0].lineno,
            )
        )
    return sites


def _has_logger(source: str) -> bool:
    """Return True if the file already declares a module-level logger."""
    return bool(re.search(r"^logger\s*=", source, re.MULTILINE))


def _add_logger_import(lines: list[str]) -> list[str]:
    """Inject `import logging` + `logger = logging.getLogger(__name__)` near top.

    Inserts after the last existing `import` / `from` statement in the header
    block (before the first class/def), or after the module docstring.
    """
    insert_after = 0
    in_docstring = False
    docstring_done = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip blank lines and shebang
        if not stripped or stripped.startswith("#") or stripped.startswith("#!/"):
            continue
        # Module docstring (triple-quoted)
        if not docstring_done and (stripped.startswith('"""') or stripped.startswith("'''")):
            in_docstring = True
        if in_docstring:
            # Look for closing triple quote
            count = stripped.count('"""') + stripped.count("'''")
            if count >= 2 or (i > insert_after and (stripped.endswith('"""') or stripped.endswith("'''"))):
                in_docstring = False
                docstring_done = True
                insert_after = i + 1
            continue
        if stripped.startswith(("import ", "from ")):
            insert_after = i + 1
        elif stripped.startswith(("class ", "def ", "@")):
            break

    injection = [
        "import logging\n",
        "logger = logging.getLogger(__name__)\n",
        "\n",
    ]
    # Avoid duplicate injection
    source_joined = "".join(lines)
    if "import logging" in source_joined and "logger = logging.getLogger" in source_joined:
        return lines  # already set up

    return lines[:insert_after] + injection + lines[insert_after:]


def _get_indent(line: str) -> str:
    """Return leading whitespace of a line."""
    return line[: len(line) - len(line.lstrip())]


def apply_fixes(path: Path, sites: list[SwallowSite], dry_run: bool) -> int:
    """Replace `pass` with `logger.debug(...)` at each swallow site.

    Returns the number of fixes applied.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

    # Work bottom-up to preserve line numbers
    for site in sorted(sites, key=lambda s: s.body_lineno, reverse=True):
        target_lineno = site.body_lineno  # 1-based
        idx = target_lineno - 1  # 0-based
        if idx >= len(lines):
            continue
        original_line = lines[idx]
        indent = _get_indent(original_line)
        # Replace the entire `pass` line
        new_line = f'{indent}logger.debug("Suppressed {site.exc_label}", exc_info=True)\n'
        if dry_run:
            print(f"  {path}:{target_lineno}  pass → logger.debug()")
        else:
            lines[idx] = new_line

    if dry_run:
        return len(sites)

    new_source = "".join(lines)

    # Ensure logger is available
    if not _has_logger(new_source):
        lines = list(new_source.splitlines(keepends=True))
        lines = _add_logger_import(lines)
        new_source = "".join(lines)

    path.write_text(new_source, encoding="utf-8")
    return len(sites)


# ── main ───────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing any files",
    )
    parser.add_argument(
        "--src",
        default="src",
        help="Source root to scan (default: src)",
    )
    args = parser.parse_args(argv)

    src_root = Path(args.src)
    if not src_root.exists():
        print(f"ERROR: {src_root} does not exist", file=sys.stderr)
        return 1

    all_sites: dict[Path, list[SwallowSite]] = {}
    for py_file in sorted(src_root.rglob("*.py")):
        sites = find_swallows(py_file)
        if sites:
            all_sites[py_file] = sites

    total = sum(len(v) for v in all_sites.values())
    print(f"Found {total} non-intentional silent swallows across {len(all_sites)} files")

    if args.dry_run:
        print("\n--- DRY RUN (no files written) ---\n")
        for path, sites in sorted(all_sites.items()):
            print(f"\n{path} ({len(sites)} sites):")
            for site in sites:
                print(f"  line {site.body_lineno}: except {site.exc_label}: pass")
        print(f"\nTotal: {total} fixes would be applied")
        return 0

    # Apply
    fixed = 0
    for path, sites in sorted(all_sites.items()):
        count = apply_fixes(path, sites, dry_run=False)
        fixed += count
        print(f"  Fixed {count:>3} in {path}")

    print(f"\nDone — {fixed} silent swallows converted to logger.debug() calls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
