#!/usr/bin/env python3
"""Render Boss Rush summary without brittle inline quoting."""

import argparse
from pathlib import Path


def load_text(path: Path) -> str:
    if not path.exists():
        return f"[ERROR] Missing file: {path}"
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser(description="Show Boss Rush deployment summary")
    parser.add_argument(
        "--path",
        default="docs/BOSS_RUSH_DEPLOYMENT_COMPLETE.md",
        help="Path to summary markdown file.",
    )
    args = parser.parse_args()

    path = Path(args.path)
    content = load_text(path)

    try:
        from rich.console import Console
        from rich.markdown import Markdown

        console = Console()
        console.print(Markdown(content))
    except Exception:
        print(content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
