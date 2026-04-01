"""generate_structure_tree.py.

Purpose:
- Generate a human-readable and Copilot-friendly `REPO_STRUCTURE.md` that
    documents the repository tree and small file-level contexts.

Who/What/Where/When/Why/How:
- Who: Developers, reviewers, and agents that need a quick map of the
    repository layout.
- What: Produces `REPO_STRUCTURE.md` with YAML frontmatter and a full tree
    listing, including short context excerpts for files.
- Where: Run from the repository root. Output file: `REPO_STRUCTURE.md`.
- When: Useful for documentation updates, audits, and onboarding flows.
- Why: Makes repository structure discoverable and easier to navigate for
    both humans and AI agents.
- How: `build_tree(Path.cwd())` builds and writes the file. `WATCH_MODE`
    can be enabled for auto-updating but use with caution on large repos.

Tips:
- Exclude large folders or add more entries to `EXCLUDE` to reduce noise.
- Prefer running with `WATCH_MODE=False` in CI; use `True` in local dev
    sessions when actively modifying structure.

"""

import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ========= Configuration =========
WATCH_MODE = False  # set to True for auto-updating structure file
OUTPUT_FILE = Path("REPO_STRUCTURE.md")
EXCLUDE = {".git", ".venv", "__pycache__", "node_modules", ".DS_Store", ".mypy_cache"}


# ========= Extract File Context =========
def extract_context(file_path: Path) -> str | None:
    try:
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith(("#", '"""', "'''")):
                    return stripped.strip("#\"' ").rstrip()
    except (FileNotFoundError, UnicodeDecodeError, OSError):
        logger.debug("Suppressed FileNotFoundError/OSError/UnicodeDecodeError", exc_info=True)
    return None


# ========= Tree Builder =========
def build_tree(root: Path, max_depth: int = 5) -> None:
    lines: list[Any] = []
    # --- YAML Frontmatter for Copilot context ---
    lines.extend(
        [
            "---",
            "applyTo: '**'",
            "---",
            "# 🗂 Repository Structure Tree",
            "",
            f"_Generated from_: `{root.resolve()}`",
            "",
        ]
    )

    # --- Preamble: Top-Level Folders ---
    main_dirs = [p for p in root.iterdir() if p.is_dir() and p.name not in EXCLUDE]
    lines.append("## 📦 Top-Level Modules")
    for d in sorted(main_dirs):
        lines.append(f"- `{d.name}/`")
    lines.append("")

    # --- Root-Level Files ---
    root_files = [p for p in root.iterdir() if p.is_file() and p.name not in EXCLUDE]
    lines.append("## 📄 Root-Level Files")
    for f in sorted(root_files):
        rel_path = f.relative_to(root).as_posix()
        context = extract_context(f)
        comment = f" - {context}" if context else ""
        lines.append(f"- [{f.name}]({rel_path}){comment}")
    lines.append("")

    # --- Full Recursive Structure ---
    lines.append("## 🌲 Full Tree Structure")
    recurse(lines, root, prefix="", depth=0, max_depth=max_depth)

    # --- Write to file ---
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")


# ========= Recursive Printer =========
def recurse(lines: list, path: Path, prefix: str, depth: int, max_depth: int) -> None:
    if depth > max_depth:
        return

    try:
        children = [
            p for p in sorted(path.iterdir(), key=lambda x: x.name) if p.name not in EXCLUDE
        ]
    except (OSError, PermissionError):
        return

    for idx, child in enumerate(children):
        connector = "└── " if idx == len(children) - 1 else "├── "
        rel_path = child.relative_to(Path.cwd())
        line = f"{prefix}{connector}[{child.name}]({rel_path.as_posix()})"

        if child.is_dir():
            lines.append(line + " (dir)")
            recurse(
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


# ========= Optional: CLI / Script Entry Point =========
def main() -> None:
    """CLI entry point to generate the repository structure file.

    This function is intentionally not run at import-time so that importing
    the module during test collection (import-all-modules) does not execute
    heavy file-system work.
    """
    if WATCH_MODE:
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except Exception:
            # If watchdog isn't available, fall back to a single build.
            build_tree(Path.cwd())
            return

        class ChangeHandler(FileSystemEventHandler):
            def on_any_event(self, event) -> None:
                if not event.is_directory and not any(ex in event.src_path for ex in EXCLUDE):
                    build_tree(Path.cwd())

        observer = Observer()
        observer.schedule(ChangeHandler(), str(Path.cwd()), recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        build_tree(Path.cwd())


if __name__ == "__main__":
    main()
