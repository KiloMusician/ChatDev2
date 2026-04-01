"""KILO-FOOLISH Repository Python File Classifier.

Classifies .py files as: Script, Module, Tool, Test, Config, or Unknown.

OmniTag: [repo_scan, file_classification, context_extraction]
MegaTag: [REPO_AWARENESS, CONTEXT_PROPAGATION, TOOL_DISCOVERY]
"""

import os
import re
from pathlib import Path

EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".vscode",
    ".idea",
}


def should_exclude(path: str | Path) -> bool:
    """Check if a path should be excluded from scanning.

    Args:
        path: Path to check

    Returns:
        True if path contains excluded directory

    """
    parts = set(Path(path).parts)
    return bool(parts & EXCLUDE_DIRS)


def classify_file(filepath) -> str:
    """Classify a Python file as one of.

    - Script: Has __main__ block, meant to be run directly
    - Module: No __main__, likely imported elsewhere
    - Tool: Script in 'tools/' or 'Scripts/' or named like a utility
    - Test: In 'tests/' or filename starts with 'test_'
    - Config: In 'config/' or filename contains 'config', 'setup', or 'settings'
    - Unknown: Does not match above.

    OmniTag: [file_classification, context_extraction]
    MegaTag: [CLASSIFICATION, TOOL_DETECTION]
    """
    path = Path(filepath)
    fname = path.name.lower()
    parent_dirs = [p.name.lower() for p in path.parents]

    try:
        # Skip large files (>1MB) for speed
        if path.stat().st_size > 1_000_000:
            return "Unknown"
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except (FileNotFoundError, UnicodeDecodeError, OSError):
        return "Unknown"

    # Test
    if "tests" in parent_dirs or fname.startswith("test_"):
        return "Test"
    # Config
    if "config" in parent_dirs or any(x in fname for x in ["config", "setup", "settings"]):
        return "Config"
    # Tool
    if any(
        (
            "tools" in parent_dirs,
            "scripts" in parent_dirs,
            re.search(
                r"(tool|cli|browser|manager|auditor|dashboard|extract|import|export)",
                fname,
            )
            is not None,
        )
    ):
        return "Tool"
    # Script
    if 'if __name__ == "__main__":' in content:
        return "Script"
    # Module
    if re.search(r"def\s+\w+\(", content) or re.search(r"class\s+\w+\(", content):
        return "Module"
    return "Unknown"


def scan_repo(root: str | Path = ".") -> list[dict[str, str]]:
    """Scan repository and classify Python files.

    Args:
        root: Root directory to scan

    Returns:
        List of dictionaries with file path and classification

    """
    findings: list[dict[str, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude unwanted directories in-place for os.walk
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in filenames:
            if fname.endswith(".py"):
                fpath = os.path.join(dirpath, fname)
                if should_exclude(fpath):
                    continue
                classification = classify_file(fpath)
                findings.append({"path": fpath, "classification": classification})
    return findings


def print_report(results: list[dict[str, str]], export_path: str | None = None) -> None:
    report_lines: list[str] = []
    report_lines.append("=== KILO-FOOLISH Python File Classification Report ===\n")
    categories = ["Script", "Module", "Tool", "Test", "Config", "Unknown"]
    for cat in categories:
        report_lines.append(f"\n--- {cat.upper()} ---")
        for item in results:
            if item.get("classification") == cat:
                report_lines.append(f"  {item.get('path')}")
    report = "\n".join(report_lines)
    if export_path:
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(report)


if __name__ == "__main__":
    _results = scan_repo(".")
    print_report(_results, export_path="python_file_classification_report.md")
