"""Pre-commit helper to enforce the "Three Before New" rule.

Intended usage (from .git/hooks/pre-commit):
    #!/usr/bin/env python
    import sys
    from pathlib import Path
    sys.exit(
        __import__("scripts.three_before_new_audit").three_before_new_audit.main()
    )

Behavior:
- Scans staged additions for likely new tools (scripts/, src/tools/, src/utils/, src/diagnostics/, src/healing/).
- Reminds contributors to run the discovery helper and document three alternatives.
- Fails by default; set env TBN_WARN_ONLY=1 or pass --warn-only to emit warnings only.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from collections.abc import Iterable
from pathlib import Path

CANDIDATE_DIR_HINTS = (
    "scripts/",
    "src/tools/",
    "src/utils/",
    "src/diagnostics/",
    "src/healing/",
)
CANDIDATE_EXTS = {".py", ".sh", ".ps1", ".md", ".yaml", ".yml"}
DEFAULT_ROOT = Path(__file__).resolve().parent.parent


def _run_git_diff(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=A"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git diff failed: {result.stderr.strip()}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _is_candidate(path: str) -> bool:
    lowered = path.lower()
    if not any(lowered.startswith(prefix) for prefix in CANDIDATE_DIR_HINTS):
        return False
    return Path(path).suffix.lower() in CANDIDATE_EXTS


def _filter_candidates(paths: Iterable[str]) -> list[str]:
    return [p for p in paths if _is_candidate(p)]


def _build_message(candidates: list[str]) -> str:
    lines = [
        "Three Before New check: potential new tools detected.",
        "Before committing, run discovery and document your three alternatives:",
        '  python scripts/find_existing_tool.py --capability "<capability>"',
        "  See docs/THREE_BEFORE_NEW_PROTOCOL.md for the checklist.",
        "Candidates:",
    ]
    lines.extend(f" - {p}" for p in candidates)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-only", action="store_true", help="Do not fail; emit warnings only")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="Repository root")
    args = parser.parse_args(argv)

    warn_only = args.warn_only or os.environ.get("TBN_WARN_ONLY") == "1"
    root = Path(args.root).resolve()

    try:
        staged = _run_git_diff(root)
    except RuntimeError as exc:  # pragma: no cover - defensive
        print(f"three_before_new_audit: {exc}")
        return 1

    candidates = _filter_candidates(staged)
    if not candidates:
        return 0

    message = _build_message(candidates)
    if warn_only:
        print(message)
        print("WARN-ONLY mode: not blocking commit.")
        return 0

    print(message)
    print("Commit blocked. Set TBN_WARN_ONLY=1 or rerun after adding justification to quest/log.")
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
