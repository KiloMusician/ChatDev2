"""OmniTag: {.

from typing import Any.

    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""

import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Optional: Enable file watching
WATCH_MODE = False

# Files/folders to ignore
EXCLUDE = {".git", ".venv", "__pycache__", "node_modules", ".DS_Store"}

# Output file
OUTPUT_FILE = Path("REPO_STRUCTURE.md")


def extract_context(file_path: Path) -> str | None:
    try:
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith(("#", '"""')):
                    return stripped.replace('"""', "").replace("#", "").strip()
    except (OSError, UnicodeDecodeError):
        logger.debug("Suppressed OSError/UnicodeDecodeError", exc_info=True)
    return None


def build_tree(root: Path, max_depth=5) -> None:
    lines: list[Any] = []
    main_dirs = [p for p in root.iterdir() if p.is_dir() and p.name not in EXCLUDE]
    files = [p for p in root.iterdir() if p.is_file() and p.name not in EXCLUDE]

    # YAML Frontmatter
    lines.append("---")
    lines.append("applyTo: '**'")
    lines.append("---")
    lines.append("# 🗂 Repository Structure Tree")
    lines.append("")
    lines.append(f"_Generated from_: `{root.resolve()}`")
    lines.append("")

    # Preamble
    lines.append("## 📦 Top-Level Modules")
    for d in sorted(main_dirs):
        lines.append(f"- `{d.name}/`")
    lines.append("")

    # Files in root
    lines.append("## 📄 Root-Level Files")
    for f in sorted(files):
        rel_path = f.relative_to(root).as_posix()
        context = extract_context(f)
        comment = f" - {context}" if context else ""
        lines.append(f"- [{f.name}]({rel_path}){comment}")
    lines.append("")

    # Recursive structure
    lines.append("## 🌲 Full Structure")
    recurse_tree(lines, root, "", depth=0, max_depth=max_depth)

    # Write output
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")


def recurse_tree(lines, path: Path, prefix: str = "", depth: int = 0, max_depth: int = 5) -> None:
    if depth > max_depth:
        return

    children = [c for c in sorted(path.iterdir(), key=lambda p: p.name) if c.name not in EXCLUDE]
    for idx, child in enumerate(children):
        connector = "└── " if idx == len(children) - 1 else "├── "
        rel = child.relative_to(Path.cwd())
        line = f"{prefix}{connector}[{child.name}]({rel.as_posix()})"

        if child.is_dir():
            lines.append(line + " (dir)")
            recurse_tree(
                lines,
                child,
                prefix + ("    " if idx == len(children) - 1 else "│   "),
                depth + 1,
                max_depth,
            )
        else:
            context = extract_context(child)
            comment = f" - {context}" if context else ""
            lines.append(line + comment)


# Optional: Watchdog auto-update
if WATCH_MODE:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class RepoChangeHandler(FileSystemEventHandler):
        def on_any_event(self, event) -> None:
            if not event.is_directory:
                build_tree(Path.cwd())

    observer = Observer()
    observer.schedule(RepoChangeHandler(), path=str(Path.cwd()), recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def main() -> None:
    # Default CLI entrypoint for generating the repo structure
    build_tree(Path.cwd())


if __name__ == "__main__":
    main()
