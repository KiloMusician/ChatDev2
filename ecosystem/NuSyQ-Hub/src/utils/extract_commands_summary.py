"""OmniTag: {.

    "purpose": "file_systematically_tagged",
    "tags": ["Python"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}.
"""

import os
import re
from pathlib import Path
from typing import Any


def extract_commands_from_md(md_path: str | Path) -> list[str]:
    """Extract shell commands from markdown code blocks.

    Args:
        md_path: Path to markdown file

    Returns:
        List of extracted commands

    """
    commands: list[Any] = []
    with open(md_path, encoding="utf-8") as f:
        content = f.read()
        # Find code blocks with bash, powershell, or generic
        blocks = re.findall(r"```(?:bash|powershell)?\n(.*?)```", content, re.DOTALL)
        for block in blocks:
            for line in block.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    commands.append(line)
    return commands


def extract_commands_from_logs(log_dir: str | Path) -> list[str]:
    """Extract commands from log files.

    Args:
        log_dir: Directory containing log files

    Returns:
        List of extracted commands

    """
    commands: list[Any] = []
    for root, _, files in os.walk(log_dir):
        for file in files:
            if file.endswith((".log", ".txt")):
                file_path = Path(root) / file
                with open(file_path, encoding="utf-8") as f:
                    for line in f:
                        # Simple heuristic: lines starting with known command prefixes
                        if line.strip().startswith(
                            ("python", "ollama", "powershell", "npm", "git")
                        ):
                            commands.append(line.strip())
    return commands


def main() -> None:
    base_dir = Path(
        os.getenv("KILO_FOOLISH_ROOT", Path.home() / "Documents" / "GitHub" / "KILO-FOOLISH")
    )
    docs_dir = base_dir / "docs"
    archive_dir = docs_dir / "Archive"
    log_dir = base_dir / "data" / "logs"

    all_commands = set()

    # Scan markdown documentation
    for root, _, files in os.walk(archive_dir):
        for file in files:
            if file.endswith(".md"):
                md_path = Path(root) / file
                cmds = extract_commands_from_md(md_path)
                all_commands.update(cmds)

    # Scan log files (optional)
    if log_dir.exists():
        log_cmds = extract_commands_from_logs(log_dir)
        all_commands.update(log_cmds)

    # Output summary
    output_path = base_dir / "extracted_commands.md"
    with open(output_path, "w", encoding="utf-8") as out:
        out.write("# Known System Commands (Extracted)\n")
        out.writelines(cmd + "\n" for cmd in sorted(all_commands))


if __name__ == "__main__":
    main()
