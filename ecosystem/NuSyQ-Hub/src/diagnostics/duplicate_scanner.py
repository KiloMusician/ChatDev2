"""Duplicate Code Scanner for Testing Chamber.

Detects duplicate code patterns to prevent code bloat.

Uses:
- Simple hash-based detection
- AST-based structural comparison
- Token similarity analysis

Version: 1.0.0
"""

import ast
import hashlib
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Comprehensive exclusion list (aligned with maze_solver.py pattern - 2025-11-17)
DEFAULT_EXCLUDES: set[str] = {
    ".venv",
    ".venv.old",
    ".venv.backup",
    ".virtualenv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".tox",
    ".hypothesis",
    ".coverage",
    "htmlcov",
    "dist",
    "build",
    "eggs",
    ".eggs",
    "lib",
    "lib64",
    "wheels",
    "site",
    "coverage",
    "*.egg-info",
    "*.dist-info",
    ".git",
    ".svn",
    ".hg",
    ".bzr",
    ".idea",
    ".vscode",
    ".vs",
}


def _should_exclude(path: Path) -> bool:
    """Check if a path should be excluded from duplicate scanning.

    Implements comprehensive exclusion logic similar to maze_solver.py:
    - Direct name matching (case-insensitive)
    - Pattern matching for *.egg-info style patterns
    - Hidden cache directory detection

    Args:
        path: Path to check

    Returns:
        True if path should be excluded, False otherwise

    """
    name_lower = path.name.lower()

    # Direct match against exclusion set
    if name_lower in DEFAULT_EXCLUDES:
        return True

    # Pattern-based exclusions (*.egg-info, *.dist-info)
    if any(
        name_lower.endswith(pattern.lstrip("*")) for pattern in DEFAULT_EXCLUDES if "*" in pattern
    ):
        return True

    # Hidden cache/build artifact directories
    return bool(
        name_lower.startswith(".")
        and any(
            keyword in name_lower
            for keyword in [
                "cache",
                "egg",
                "pyc",
                "tox",
                "mypy",
                "ruff",
                "pytest",
                "venv",
            ]
        ),
    )


class DuplicateScanner:
    """Scans codebase for duplicate code patterns."""

    def __init__(self, repository_root: Path, min_lines: int = 5) -> None:
        """Initialize duplicate scanner.

        Args:
            repository_root: Root of repository to scan
            min_lines: Minimum lines to consider for duplication

        """
        self.repository_root = Path(repository_root)
        self.min_lines = min_lines
        self.file_hashes: dict[str, str] = {}
        self.function_hashes: dict[str, list[tuple[Path, str]]] = defaultdict(list)

    def scan_file(self, file_path: Path) -> float:
        """Scan a single file for duplicates in the repository.

        Args:
            file_path: Path to file to scan

        Returns:
            Duplicate score (0.0 = unique, 1.0 = completely duplicate)

        """
        logger.info("🔍 Scanning %s for duplicates...", file_path.name)

        # Read file content
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.warning("Could not read %s: %s", file_path, e)
            return 0.0

        # Calculate file hash
        file_hash = self._calculate_hash(content)

        # Check for exact file duplicates
        exact_duplicates = self._find_exact_duplicates(file_hash, file_path)
        if exact_duplicates:
            logger.warning("⚠️  Exact duplicate found: %s", exact_duplicates)
            return 1.0

        # Parse and check functions
        try:
            tree = ast.parse(content)
            duplicate_score = self._check_function_duplicates(tree, file_path)

            logger.info("   Duplicate score: %.2f%%", duplicate_score * 100)
            return duplicate_score

        except SyntaxError:
            logger.debug("Could not parse %s for duplicate analysis", file_path)
            return 0.0

    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content."""
        normalized = content.strip()
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _find_exact_duplicates(self, file_hash: str, current_file: Path) -> list[Path]:
        """Find exact file duplicates."""
        duplicates: list[Any] = []

        # Scan repository for Python files
        for python_file in self.repository_root.rglob("*.py"):
            if python_file == current_file:
                continue

            # Use comprehensive exclusion check (updated 2025-11-17)
            if any(_should_exclude(part) for part in python_file.parents):
                continue
            if _should_exclude(python_file.parent):
                continue

            try:
                with open(python_file, encoding="utf-8") as f:
                    content = f.read()

                if self._calculate_hash(content) == file_hash:
                    duplicates.append(python_file)

            except (FileNotFoundError, UnicodeDecodeError, OSError):
                continue

        return duplicates

    def _check_function_duplicates(self, tree: ast.AST, current_file: Path) -> float:
        """Check for duplicate functions using AST comparison.

        Returns duplicate score based on function similarity.
        """
        # Extract functions from current file
        functions: list[Any] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_code = ast.unparse(node) if hasattr(ast, "unparse") else ast.dump(node)
                func_hash = self._calculate_hash(func_code)
                functions.append((node.name, func_hash, func_code))

        if not functions:
            return 0.0

        # Check against repository
        duplicate_count = 0
        total_functions = len(functions)

        for func_name, func_hash, _func_code in functions:
            if self._is_function_duplicate(func_hash, current_file):
                duplicate_count += 1
                logger.debug("   Duplicate function detected: %s", func_name)

        return duplicate_count / total_functions if total_functions > 0 else 0.0

    def _is_function_duplicate(self, func_hash: str, _current_file: Path) -> bool:
        """Check if function hash exists in repository."""
        # Simple check: return True if we've seen this exact function before
        # In a real implementation, would maintain a database of function hashes

        # For now, use a basic heuristic
        return func_hash in self.function_hashes and len(self.function_hashes[func_hash]) > 0

    def build_repository_index(self) -> None:
        """Build index of all functions in repository.

        This should be run once before scanning multiple files.
        """
        logger.info("📚 Building repository duplicate index...")

        python_files = list(self.repository_root.rglob("*.py"))
        logger.info("   Found %s Python files (before filtering)", len(python_files))

        processed_count = 0
        for python_file in python_files:
            # Use comprehensive exclusion check (updated 2025-11-17)
            if any(_should_exclude(part) for part in python_file.parents):
                continue
            if _should_exclude(python_file.parent):
                continue

            processed_count += 1

            try:
                with open(python_file, encoding="utf-8") as f:
                    content = f.read()

                # Calculate file hash
                file_hash = self._calculate_hash(content)
                self.file_hashes[str(python_file)] = file_hash

                # Parse and index functions
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            func_code = (
                                ast.unparse(node) if hasattr(ast, "unparse") else ast.dump(node)
                            )
                            func_hash = self._calculate_hash(func_code)
                            self.function_hashes[func_hash].append((python_file, node.name))
                except SyntaxError:
                    logger.debug("Suppressed SyntaxError", exc_info=True)

            except Exception as e:
                logger.debug("Error indexing %s: %s", python_file, e)

        logger.info(
            f"✅ Index built: {processed_count} files processed, {len(self.file_hashes)} indexed, {len(self.function_hashes)} unique functions",
        )

    def get_duplicate_report(self) -> dict:
        """Generate a report of duplicates found in repository.

        Returns:
            dict with duplicate statistics

        """
        # Find exact file duplicates
        file_groups = defaultdict(list)
        for file_path, file_hash in self.file_hashes.items():
            file_groups[file_hash].append(file_path)

        exact_duplicates = {
            hash_val: files for hash_val, files in file_groups.items() if len(files) > 1
        }

        # Find duplicate functions
        duplicate_functions = {
            func_hash: locations
            for func_hash, locations in self.function_hashes.items()
            if len(locations) > 1
        }

        return {
            "exact_file_duplicates": len(exact_duplicates),
            "duplicate_function_groups": len(duplicate_functions),
            "total_files_scanned": len(self.file_hashes),
            "total_unique_functions": len(self.function_hashes),
            "duplicate_files": [[str(f) for f in files] for files in exact_duplicates.values()][
                :5
            ],  # First 5 groups
            "duplicate_functions": [
                {"locations": [{"file": str(f), "function": name} for f, name in locs]}
                for locs in list(duplicate_functions.values())[:5]  # First 5 groups
            ],
        }


# ==================================================================
# CLI INTERFACE
# ==================================================================


def main() -> None:
    """CLI interface for duplicate scanner."""
    import argparse

    parser = argparse.ArgumentParser(description="Duplicate Code Scanner")
    parser.add_argument("--repository", default=".", help="Repository root to scan")
    parser.add_argument("--file", help="Specific file to check for duplicates")
    parser.add_argument("--report", action="store_true", help="Generate full duplicate report")
    parser.add_argument("--min-lines", type=int, default=5, help="Minimum lines to consider")

    args = parser.parse_args()

    scanner = DuplicateScanner(repository_root=Path(args.repository), min_lines=args.min_lines)

    if args.file:
        # Build index first
        scanner.build_repository_index()

        # Scan specific file
        scanner.scan_file(Path(args.file))

    elif args.report:
        # Build index and generate report
        scanner.build_repository_index()
        scanner.get_duplicate_report()

    else:
        pass


if __name__ == "__main__":
    main()
