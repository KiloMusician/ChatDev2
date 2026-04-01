import logging

logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""Safe File Reader Utility

Handles encoding issues when reading files with unknown encodings.

OmniTag: {
    "purpose": "Robust file reading with automatic encoding detection",
    "tags": ["Utilities", "Encoding", "Error Handling"],
    "category": "file_io",
    "evolution_stage": "v1.0"
}
"""

from pathlib import Path

try:
    import chardet

    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False


def read_text_safe(
    file_path: str | Path,
    fallback_encoding: str = "latin-1",
    detect_encoding: bool = False,
) -> str | None:
    """Safely read text file content with automatic encoding handling.

    Args:
        file_path: Path to the file to read
        fallback_encoding: Encoding to use if UTF-8 fails (default: latin-1, accepts all bytes)
        detect_encoding: Use chardet to detect encoding (slower but more accurate)

    Returns:
        File content as string, or None if all attempts fail

    Example:
        >>> content = read_text_safe('myfile.py')
        >>> if content:
        ...     lines = content.splitlines()

    """
    file_path = Path(file_path)

    if not file_path.is_file():
        return None

    # Strategy 1: Try UTF-8 (most common for Python files)
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logger.debug("Suppressed UnicodeDecodeError", exc_info=True)

    # Strategy 2: Use chardet for automatic detection (optional, slower)
    if detect_encoding and CHARDET_AVAILABLE:
        try:
            raw_data = file_path.read_bytes()
            detected = chardet.detect(raw_data)
            if detected and detected.get("encoding"):
                return raw_data.decode(detected["encoding"], errors="replace")
        except OSError:
            logger.debug("Suppressed OSError", exc_info=True)

    # Strategy 3: Try common encodings
    encodings_to_try = ["utf-8-sig", "cp1252", "iso-8859-1", fallback_encoding]

    for encoding in encodings_to_try:
        try:
            return file_path.read_text(encoding=encoding)
        except (UnicodeDecodeError, LookupError):
            continue

    # Strategy 4: Last resort - latin-1 with error replacement
    try:
        return file_path.read_text(encoding="latin-1", errors="replace")
    except OSError:
        return None


def count_lines_safe(file_path: str | Path) -> int:
    """Count lines in a file with robust encoding handling.

    Args:
        file_path: Path to the file

    Returns:
        Number of lines, or 0 if file cannot be read

    Example:
        >>> line_count = count_lines_safe('myfile.py')

    """
    content = read_text_safe(file_path)
    if content is None:
        return 0
    return len(content.splitlines())


def read_files_safe(
    file_paths: list[str | Path],
    skip_errors: bool = True,
) -> dict[Path, str | None]:
    """Read multiple files safely, returning a dictionary of path -> content.

    Args:
        file_paths: list of file paths to read
        skip_errors: If True, skip files that cannot be read; if False, include None values

    Returns:
        Dictionary mapping file paths to their content (or None if failed and skip_errors=False)

    Example:
        >>> files = read_files_safe(['file1.py', 'file2.py'])
        >>> for path, content in files.items():
        ...     if content:
        ...         print(f"{path}: {len(content)} chars")

    """
    results: dict[Path, str | None] = {}

    for file_path in file_paths:
        path = Path(file_path)
        content = read_text_safe(path)

        if content is not None or not skip_errors:
            results[path] = content

    return results


# Backwards compatibility alias
safe_read_text = read_text_safe


if __name__ == "__main__":
    # Self-test
    import sys

    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])

        if test_file.exists():
            content = read_text_safe(test_file, detect_encoding=True)
            if content:
                lines = content.splitlines()
            else:
                pass
    else:
        pass
