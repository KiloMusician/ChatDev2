#!/usr/bin/env python3
"""Scan Python entrypoints and optionally inject a best-effort init_terminal_logging call.

This tool discovers Python files under the repo that contain a `if __name__ == '__main__'`
block and that do not already import `init_terminal_logging`. It can print a report
or apply changes in-place (use --apply to modify files).

Usage:
  python scripts/wire_terminal_logging.py --report
  python scripts/wire_terminal_logging.py --apply

This is provided as a safe helper — review the proposed patches before applying.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def find_candidates(root: Path) -> list[Path]:
    py_files = list(root.rglob("*.py"))
    candidates = []
    for p in py_files:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if "if __name__ == '__main__'" in text or 'if __name__ == "__main__"' in text:
            if "init_terminal_logging" not in text:
                candidates.append(p)
    return candidates


INJECT_SNIPPET = (
    "\n# Best-effort initialize terminal logging for visibility in TerminalManager\n"
    "try:\n"
    "    from src.system.init_terminal import init_terminal_logging\n"
    "    try:\n"
    '        init_terminal_logging(channel="Auto-Wired")\n'
    "    except Exception:\n"
    "        pass\n"
    "except Exception:\n"
    "    pass\n"
)


def apply_injection(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False
    # insert after module docstring or first top-level imports
    # simple heuristic: find the first occurrence of a top-level import block
    m = re.search(r"(^from\s+.*\n|^import\s+.*\n)+", text, flags=re.MULTILINE)
    if m:
        idx = m.end()
    else:
        # after module docstring if present
        if text.startswith(('"""', "'''")):
            # find the closing triple-quote
            closing = text.find('"""', 3)
            if closing == -1:
                closing = text.find("'''", 3)
            if closing != -1:
                idx = closing + 3
            else:
                idx = 0
        else:
            idx = 0
    new_text = text[:idx] + INJECT_SNIPPET + text[idx:]
    path.write_text(new_text, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--yes", "-y", action="store_true", help="Automatically confirm apply without prompting")
    args = parser.parse_args()
    candidates = find_candidates(ROOT)
    print(f"Found {len(candidates)} candidate files for wiring:\n")
    for p in candidates:
        print(p.relative_to(ROOT))
    if args.apply:
        auto = args.yes or ("WIRE_AUTO_APPLY" in __import__("os").environ)
        if not auto:
            confirm = input("Apply injection to these files? [y/N]: ")
            if confirm.lower().strip() != "y":
                print("Aborted.")
                return
        for p in candidates:
            ok = apply_injection(p)
            print(f"{p.relative_to(ROOT)} -> {'patched' if ok else 'failed'}")


if __name__ == "__main__":
    main()
