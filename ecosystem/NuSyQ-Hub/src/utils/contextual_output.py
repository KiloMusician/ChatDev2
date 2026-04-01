"""contextual_output.py.

A modular utility for intelligent, context-aware file and output management in NuSyQ-Hub.
- Dynamically determines the correct output directory based on file type, context, and config.
- Updates existing files in place, with optional versioning.
- Provides helpful suggestions if output location is ambiguous.
- Designed for use by agents, scripts, and Copilot routines.

References:
- .github/instructions/repository-context.md
- .github/instructions/CONTEXT_REGISTRY.md
- REPO_STRUCTURE.md

"""

import datetime
import shutil
from pathlib import Path

# Map file types/extensions to preferred output directories
OUTPUT_DIR_MAP = {
    ".log": "logs",
    ".json": "reports",
    ".md": "reports",
    ".csv": "data",
    ".txt": "reports",
    ".png": "assets",
    ".jpg": "assets",
    ".py": "scripts",
}

REPO_ROOT = Path(__file__).resolve().parents[2]


def get_output_dir(filename: str, context: str | None = None) -> Path:
    ext = Path(filename).suffix.lower()
    # Use context if provided and valid
    if context and (REPO_ROOT / context).is_dir():
        return REPO_ROOT / context
    # Use mapping
    if ext in OUTPUT_DIR_MAP:
        return REPO_ROOT / OUTPUT_DIR_MAP[ext]
    # Fallback to 'reports' for unknown types
    return REPO_ROOT / "reports"


def contextual_save(
    content: str | bytes,
    filename: str,
    context: str | None = None,
    mode: str = "w",
    encoding: str | None = "utf-8",
    version_if_exists: bool = True,
    overwrite: bool = False,
) -> Path:
    """Save content to the correct output directory, updating or versioning as needed.

    - content: str or bytes to write
    - filename: name of the file (not path)
    - context: optional subdirectory (e.g., 'logs', 'reports')
    - mode: 'w' (text) or 'wb' (binary)
    - version_if_exists: if True, appends a timestamp if file exists and overwrite is False
    - overwrite: if True, replaces existing file
    Returns the full path to the saved file.
    """
    out_dir = get_output_dir(filename, context)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    if out_path.exists() and not overwrite:
        if version_if_exists:
            stem, ext = out_path.stem, out_path.suffix
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = out_dir / f"{stem}_{timestamp}{ext}"
        else:
            # Overwrite in place
            pass
    if "b" in mode:
        with open(out_path, mode) as f:
            f.write(content)
    else:
        with open(out_path, mode, encoding=encoding) as f:
            f.write(content)
    return out_path


def suggest_output_location(filename: str, context: str | None = None) -> Path:
    """Suggest the best output location for a file, without writing it."""
    return get_output_dir(filename, context)


def move_to_contextual_location(filepath: str | Path, context: str | None = None) -> Path:
    """Move an existing file to its correct contextual location."""
    filepath = Path(filepath)
    out_dir = get_output_dir(filepath.name, context)
    out_dir.mkdir(parents=True, exist_ok=True)
    new_path = out_dir / filepath.name
    shutil.move(str(filepath), str(new_path))
    return new_path


# Example usage (uncomment for testing):
# contextual_save('Hello, world!', 'example.txt')
# move_to_contextual_location('somefile.log')
