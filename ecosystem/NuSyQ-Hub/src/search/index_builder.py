"""Index Builder - Culture Ship Simulation of Future Search Needs.

Precomputes search indices by scanning the entire ecosystem and building
optimized data structures for instant retrieval.

[OmniTag: index_builder, culture_ship, precomputation, zero_token]
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """Metadata for a single file in the index."""

    path: str
    size: int
    modified: str
    file_type: str
    imports: list[str]
    classes: list[str]
    functions: list[str]
    keywords: list[str]
    symbol_hash: str


class IndexBuilder:
    """Builds and maintains search indices for the ecosystem.

    The Culture Ship way: Simulate future needs and precompute answers.
    """

    def __init__(self, repo_root: Path | None = None):
        """Initialize the index builder.

        Args:
            repo_root: Root of the repository. Defaults to current repo.
        """
        if repo_root is None:
            # Find repo root by looking for .git
            current = Path.cwd()
            while current != current.parent:
                if (current / ".git").exists():
                    repo_root = current
                    break
                current = current.parent
            else:
                repo_root = Path.cwd()

        self.repo_root = repo_root
        self.index_dir = repo_root / "state" / "search_index"
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.file_metadata_path = self.index_dir / "file_metadata.json"
        self.keyword_index_path = self.index_dir / "keyword_index.json"
        self.content_snippets_path = self.index_dir / "content_snippets.json"

        # Exclusion patterns
        self.exclude_dirs = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "htmlcov",
            ".coverage",
            "dist",
            "build",
            ".egg-info",
            "nusyq_clean_clone",  # Backup directories (has symlink issues)
            "_vibe",  # Additional backups
        }

        self.exclude_patterns = {
            r"\.pyc$",
            r"\.pyo$",
            r"\.so$",
            r"\.dylib$",
            r"\.dll$",
            r"\.log$",
            r"\.swp$",
            r"\.bak$",
            r"~$",
        }

        self.exclude_extensions = {
            ".pyc",
            ".pyo",
            ".so",
            ".dylib",
            ".dll",
            ".log",
            ".swp",
            ".bak",
        }

    def should_exclude(self, path: Path) -> bool:
        """Check if a file/directory should be excluded from indexing.

        Args:
            path: Path to check

        Returns:
            True if should be excluded
        """
        # Exclude directories
        for part in path.parts:
            if part in self.exclude_dirs:
                return True

        # Exclude by pattern
        path_str = str(path)
        return any(re.search(pattern, path_str) for pattern in self.exclude_patterns)

    def extract_python_metadata(self, file_path: Path) -> FileMetadata:
        """Extract metadata from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            FileMetadata with extracted information
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            # Binary file or encoding issue
            logger.debug("Cannot read %s as UTF-8: %s", file_path, exc)
            return self._create_basic_metadata(file_path)

        # Parse AST for imports, classes, functions
        imports: list[str] = []
        classes: list[str] = []
        functions: list[str] = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
        except (SyntaxError, ValueError):
            # Invalid Python syntax
            logger.debug("Suppressed SyntaxError/ValueError", exc_info=True)

        # Extract keywords from filename and content
        keywords = self._extract_keywords(file_path, content)

        # Generate symbol hash
        symbol_hash = hashlib.md5(("|".join(sorted(classes + functions))).encode()).hexdigest()[:8]

        return FileMetadata(
            path=str(file_path.relative_to(self.repo_root)),
            size=file_path.stat().st_size,
            modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            file_type="python",
            imports=imports,
            classes=classes,
            functions=functions,
            keywords=keywords,
            symbol_hash=symbol_hash,
        )

    def extract_generic_metadata(self, file_path: Path) -> FileMetadata:
        """Extract metadata from non-Python files.

        Falls back to basic metadata when the file cannot be parsed as text.
        """
        basic = self._create_basic_metadata(file_path)

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            logger.debug("Cannot read %s as UTF-8: %s", file_path, exc)
            return basic

        keywords = self._extract_keywords(file_path, content)
        symbol_hash = hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()[:8]

        return FileMetadata(
            path=basic.path,
            size=basic.size,
            modified=basic.modified,
            file_type=basic.file_type,
            imports=[],
            classes=[],
            functions=[],
            keywords=keywords or basic.keywords,
            symbol_hash=symbol_hash,
        )

    def _create_basic_metadata(self, file_path: Path) -> FileMetadata:
        """Create basic metadata for non-Python files.

        Args:
            file_path: Path to file

        Returns:
            Basic FileMetadata
        """
        # Determine file type
        suffix = file_path.suffix.lower()
        type_map = {
            ".md": "markdown",
            ".txt": "text",
            ".json": "json",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".toml": "toml",
            ".sh": "shell",
            ".ps1": "powershell",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
        }
        file_type = type_map.get(suffix, "other")

        # Extract keywords from filename
        keywords = self._extract_keywords_from_name(file_path.name)

        return FileMetadata(
            path=str(file_path.relative_to(self.repo_root)),
            size=file_path.stat().st_size,
            modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            file_type=file_type,
            imports=[],
            classes=[],
            functions=[],
            keywords=keywords,
            symbol_hash="",
        )

    def _extract_keywords(self, file_path: Path, content: str) -> list[str]:
        """Extract keywords from file path and content.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            List of keywords
        """
        keywords = set()

        # From filename
        keywords.update(self._extract_keywords_from_name(file_path.name))

        # From content (simple word extraction)
        # Look for common patterns: class names, function names, variables
        words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b", content)
        keyword_candidates = [w.lower() for w in words if len(w) >= 3]

        # Count occurrences and take top keywords
        from collections import Counter

        word_counts = Counter(keyword_candidates)
        top_keywords = [word for word, _count in word_counts.most_common(20)]
        keywords.update(top_keywords)

        return sorted(keywords)

    def _extract_keywords_from_name(self, filename: str) -> list[str]:
        """Extract keywords from filename.

        Args:
            filename: Name of file

        Returns:
            List of keywords
        """
        # Remove extension
        name_without_ext = Path(filename).stem

        # Split on underscores and camelCase
        parts = re.split(r"[_\-\s]+", name_without_ext)

        # Expand camelCase
        expanded: list[str] = []
        for part in parts:
            # Split camelCase
            words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", part)
            expanded.extend([w.lower() for w in words if w])

        return [w for w in expanded if len(w) >= 2]

    def build_full_index(self, max_files: int | None = None) -> dict[str, Any]:
        """Build complete search index for the repository.

        Args:
            max_files: Maximum files to index (for testing). None = all files

        Returns:
            Index statistics
        """
        logger.info("🚀 Culture Ship Index Builder - Starting full scan")
        logger.info(f"   Repository: {self.repo_root}")

        start_time = datetime.now()

        # Data structures
        file_metadata: dict[str, dict[str, Any]] = {}
        keyword_index: dict[str, list[str]] = {}

        # Scan all files
        files_indexed = 0
        files_skipped = 0

        for file_path in self.repo_root.rglob("*"):
            # Skip symlinks and handle access errors
            try:
                if file_path.is_symlink():
                    continue
                # Skip if not a file
                if not file_path.is_file():
                    continue
            except (OSError, PermissionError):
                files_skipped += 1
                continue

            # Skip excluded paths
            if self.should_exclude(file_path):
                files_skipped += 1
                continue

            # Check max_files limit
            if max_files and files_indexed >= max_files:
                break

            # Extract metadata
            try:
                if file_path.suffix == ".py":
                    metadata = self.extract_python_metadata(file_path)
                else:
                    metadata = self._create_basic_metadata(file_path)

                # Store metadata
                file_metadata[metadata.path] = asdict(metadata)

                # Update keyword index
                for keyword in metadata.keywords:
                    if keyword not in keyword_index:
                        keyword_index[keyword] = []
                    keyword_index[keyword].append(metadata.path)

                files_indexed += 1

                if files_indexed % 1000 == 0:
                    logger.info(f"   Indexed {files_indexed} files...")

            except Exception as e:
                logger.warning(f"   Failed to index {file_path}: {e}")
                files_skipped += 1

        # Build final index structure
        index = {
            "version": "1.0.0",
            "indexed_at": datetime.now().isoformat(),
            "repo_root": str(self.repo_root),
            "total_files": files_indexed,
            "skipped_files": files_skipped,
            "index": file_metadata,
        }

        keyword_index_data = {
            "version": "1.0.0",
            "indexed_at": datetime.now().isoformat(),
            "total_keywords": len(keyword_index),
            "index": keyword_index,
        }

        # Save indices
        logger.info("💾 Saving indices...")
        self.file_metadata_path.write_text(json.dumps(index, indent=2))
        self.keyword_index_path.write_text(json.dumps(keyword_index_data, indent=2))

        elapsed = (datetime.now() - start_time).total_seconds()

        stats = {
            "files_indexed": files_indexed,
            "files_skipped": files_skipped,
            "keywords_found": len(keyword_index),
            "elapsed_seconds": elapsed,
            "files_per_second": files_indexed / elapsed if elapsed > 0 else 0,
        }

        logger.info("✅ Culture Ship Index Building Complete!")
        logger.info(f"   Files indexed: {files_indexed}")
        logger.info(f"   Files skipped: {files_skipped}")
        logger.info(f"   Keywords found: {len(keyword_index)}")
        logger.info(f"   Time elapsed: {elapsed:.1f}s")
        logger.info(f"   Speed: {stats['files_per_second']:.0f} files/sec")

        return stats

    def update_incremental(self, changed_files: list[str] | None = None) -> dict[str, Any]:
        """Incrementally update index for changed files.

        Args:
            changed_files: List of file paths that changed. If None, uses git to detect.

        Returns:
            Update statistics
        """
        logger.info("🔄 Culture Ship Index - Incremental Update")

        start_time = datetime.now()

        # Load existing indices
        if not self.file_metadata_path.exists() or not self.keyword_index_path.exists():
            logger.warning("   No existing index found - running full build")
            return self.build_full_index()

        file_index_data = json.loads(self.file_metadata_path.read_text())
        keyword_index_data = json.loads(self.keyword_index_path.read_text())

        file_metadata = file_index_data["index"]
        keyword_index = keyword_index_data["index"]

        # Detect changed files if not provided
        if changed_files is None:
            changed_files = self._detect_changed_files()

        if not changed_files:
            logger.info("   No changes detected")
            return {"files_updated": 0, "files_removed": 0, "elapsed_seconds": 0}

        logger.info(f"   Processing {len(changed_files)} changed files")

        files_updated = 0
        files_removed = 0

        for file_path_str in changed_files:
            file_path = Path(file_path_str)

            # Make path relative to repo root
            if file_path.is_absolute():
                try:
                    rel_path = str(file_path.relative_to(self.repo_root))
                except ValueError:
                    # File outside repo root
                    continue
            else:
                rel_path = str(file_path)

            # Check if file exists
            full_path = self.repo_root / rel_path

            if not full_path.exists():
                # File deleted - remove from index
                if rel_path in file_metadata:
                    old_metadata = file_metadata.pop(rel_path)
                    # Remove keywords pointing to this file
                    for keyword in old_metadata.get("keywords", []):
                        if keyword in keyword_index and rel_path in keyword_index[keyword]:
                            keyword_index[keyword].remove(rel_path)
                            # Remove empty keyword entries
                            if not keyword_index[keyword]:
                                del keyword_index[keyword]
                    files_removed += 1
                continue

            # Skip if excluded
            if self._should_exclude(full_path):
                continue

            # Remove old keywords for this file
            if rel_path in file_metadata:
                old_keywords = file_metadata[rel_path].get("keywords", [])
                for keyword in old_keywords:
                    if keyword in keyword_index and rel_path in keyword_index[keyword]:
                        keyword_index[keyword].remove(rel_path)
                        if not keyword_index[keyword]:
                            del keyword_index[keyword]

            # Index the file
            try:
                if full_path.suffix == ".py":
                    metadata = self.extract_python_metadata(full_path)
                else:
                    metadata = self.extract_generic_metadata(full_path)  # type: ignore[attr-defined]

                # Update file metadata
                file_metadata[rel_path] = {
                    "path": metadata.path,
                    "size": metadata.size,
                    "modified": metadata.modified,
                    "file_type": metadata.file_type,
                    "imports": metadata.imports,
                    "classes": metadata.classes,
                    "functions": metadata.functions,
                    "keywords": metadata.keywords,
                }

                # Update keyword index
                for keyword in metadata.keywords:
                    if keyword not in keyword_index:
                        keyword_index[keyword] = []
                    if rel_path not in keyword_index[keyword]:
                        keyword_index[keyword].append(rel_path)

                files_updated += 1

            except Exception as e:
                logger.warning(f"   Failed to update {rel_path}: {e}")

        # Save updated indices
        file_index_data["indexed_at"] = datetime.now().isoformat()
        file_index_data["total_files"] = len(file_metadata)
        file_index_data["index"] = file_metadata

        keyword_index_data["indexed_at"] = datetime.now().isoformat()
        keyword_index_data["total_keywords"] = len(keyword_index)
        keyword_index_data["index"] = keyword_index

        self.file_metadata_path.write_text(json.dumps(file_index_data, indent=2))
        self.keyword_index_path.write_text(json.dumps(keyword_index_data, indent=2))

        elapsed = (datetime.now() - start_time).total_seconds()

        stats = {
            "files_updated": files_updated,
            "files_removed": files_removed,
            "elapsed_seconds": elapsed,
        }

        logger.info("✅ Incremental Update Complete!")
        logger.info(f"   Files updated: {files_updated}")
        logger.info(f"   Files removed: {files_removed}")
        logger.info(f"   Time elapsed: {elapsed:.2f}s")

        return stats

    def _detect_changed_files(self) -> list[str]:
        """Detect changed files using git.

        Returns:
            List of changed file paths
        """
        import subprocess

        try:
            # Get uncommitted changes
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
            )

            changed_files = []
            if result.returncode == 0:
                changed_files.extend(result.stdout.strip().split("\n"))

            # Get staged changes
            result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                changed_files.extend(result.stdout.strip().split("\n"))

            # Remove empty strings and duplicates
            changed_files = list({f for f in changed_files if f})

            return changed_files

        except Exception as e:
            logger.warning(f"   Failed to detect git changes: {e}")
            return []

    def _should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded from indexing.

        Args:
            file_path: Path to check

        Returns:
            True if should exclude
        """
        # Check if in excluded directory
        for part in file_path.parts:
            if part in self.exclude_dirs:
                return True

        # Check file extension
        if file_path.suffix in self.exclude_extensions:
            return True

        # Skip symlinks
        try:
            if file_path.is_symlink():
                return True
        except (OSError, PermissionError):
            return True

        return False

    def get_index_health(self) -> dict[str, Any]:
        """Check health of existing index.

        Returns:
            Health status and statistics
        """
        if not self.file_metadata_path.exists():
            return {
                "status": "missing",
                "message": "No index found. Run build_full_index() first.",
            }

        try:
            index = json.loads(self.file_metadata_path.read_text())
            keyword_index = json.loads(self.keyword_index_path.read_text())

            indexed_at = datetime.fromisoformat(index["indexed_at"])
            age_hours = (datetime.now() - indexed_at).total_seconds() / 3600

            return {
                "status": "healthy" if age_hours < 24 else "stale",
                "version": index["version"],
                "indexed_at": index["indexed_at"],
                "age_hours": age_hours,
                "total_files": index["total_files"],
                "total_keywords": keyword_index["total_keywords"],
                "index_size_mb": self.file_metadata_path.stat().st_size / 1024 / 1024,
            }
        except Exception as e:
            return {
                "status": "corrupted",
                "message": f"Index corrupted: {e}",
            }


def main() -> None:
    """CLI entry point for index building."""
    import argparse
    import sys

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s", datefmt="%H:%M:%S"
    )

    parser = argparse.ArgumentParser(description="Build Smart Search Index")
    parser.add_argument("--max-files", type=int, help="Max files to index (for testing)")
    parser.add_argument("--check-health", action="store_true", help="Check index health")
    parser.add_argument("--incremental", action="store_true", help="Incremental update only")
    parser.add_argument("--files", nargs="*", help="Specific files to update")

    args = parser.parse_args()

    builder = IndexBuilder()

    if args.check_health:
        health = builder.get_index_health()
        logger.info(json.dumps(health, indent=2))
        sys.exit(0 if health["status"] == "healthy" else 1)

    if args.incremental:
        # Incremental update
        stats = builder.update_incremental(changed_files=args.files)
        logger.info(json.dumps(stats, indent=2))
    else:
        # Build full index
        stats = builder.build_full_index(max_files=args.max_files)
        logger.info(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
