"""Fix remaining SIM102 (collapsible-if) violations that ruff can't auto-fix.

Handles:
  A: block comment between outer and inner if → re-indented inside merged block
  B: inline comment on inner if condition   → kept on merged condition line
  C: plain (no comment)                      → direct merge

Run from repo root: python scripts/fix_sim102.py
"""

from __future__ import annotations

import re
import subprocess
import sys


def get_indent(line: str) -> str:
    m = re.match(r"^(\s*)", line)
    return m.group(1) if m else ""


def try_fix_sim102(lines: list[str], outer_idx: int) -> list[str] | None:
    """Try to merge nested ifs at outer_idx (0-based).
    Returns new lines list if fix applied, else None.
    """
    outer_line = lines[outer_idx]
    outer_indent = get_indent(outer_line)
    inner_indent = outer_indent + "    "

    # Outer line must be:  <indent>if <cond>:\n  (no trailing stuff)
    if not re.match(r"^\s*if .+:\s*$", outer_line.rstrip()):
        return None

    # Collect block comments between outer and next code line
    j = outer_idx + 1
    block_comments: list[str] = []
    while j < len(lines):
        s = lines[j].strip()
        if not s:
            break
        if s.startswith("#") and get_indent(lines[j]) == inner_indent:
            block_comments.append(lines[j])
            j += 1
        else:
            break

    if j >= len(lines):
        return None

    inner_line = lines[j]

    # Inner line must be at inner_indent and be an if (possibly with inline comment).
    # Pattern: <indent>if <cond>:  [# optional comment]
    # The colon is FIRST, then optional whitespace+comment — handle inline comments correctly.
    inner_m = re.match(r"^(\s*)(if )(.+?):\s*(#.*)?\s*$", inner_line.rstrip())
    if not inner_m or inner_m.group(1) != inner_indent:
        return None

    candidate_cond = inner_m.group(3)
    # Quote-balance guard: odd unescaped quotes → regex ate inside a string literal
    if candidate_cond.count('"') % 2 != 0 or candidate_cond.count("'") % 2 != 0:
        return None

    inner_cond = candidate_cond
    inline_comment = ("  " + inner_m.group(4)) if inner_m.group(4) else ""

    # Collect body lines of the inner if
    body_indent = inner_indent + "    "
    k = j + 1
    body_lines: list[str] = []
    while k < len(lines):
        bl = lines[k]
        if not bl.strip():
            break
        cur_ind = get_indent(bl)
        if len(cur_ind) < len(body_indent):
            break
        body_lines.append(bl)
        k += 1

    if not body_lines:
        return None

    # Make sure there's no else/elif at inner_indent level
    for bk in range(j + 1, min(k + 3, len(lines))):
        bl = lines[bk]
        if not bl.strip():
            continue
        cur_ind = get_indent(bl)
        if cur_ind == inner_indent:
            if re.match(r"\s*(else|elif)\b", bl):
                return None
            break

    # Extract outer condition
    outer_m2 = re.match(r"^\s*if (.+):\s*$", outer_line.rstrip())
    if not outer_m2:
        return None
    outer_cond = outer_m2.group(1)

    # Build merged line
    merged = f"{outer_indent}if {outer_cond} and {inner_cond}:{inline_comment}\n"

    # Re-indent block comments to body_indent
    reindented_comments = [body_indent + c.lstrip() for c in block_comments]

    return [*lines[:outer_idx], merged, *reindented_comments, *body_lines, *lines[k:]]


def fix_file(filepath: str, violations: list[int]) -> bool:
    """Fix all SIM102 violations in a file. violations = list of 1-based line numbers."""
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    original = list(lines)
    # Sort descending so indices stay valid after edits
    for lineno in sorted(violations, reverse=True):
        idx = lineno - 1
        result = try_fix_sim102(lines, idx)
        if result is not None:
            lines = result

    if lines != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    return False


def main() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "src/",
            "--select=SIM102",
            "--output-format=concise",
        ],
        capture_output=True,
        text=True,
    )

    file_violations: dict[str, list[int]] = {}
    for line in proc.stdout.splitlines():
        m = re.match(r"^([^:]+):(\d+):", line)
        if m:
            fp = m.group(1)
            ln = int(m.group(2))
            file_violations.setdefault(fp, []).append(ln)

    fixed_files = 0
    for fp, lnos in file_violations.items():
        if fix_file(fp, lnos):
            fixed_files += 1
            print(f"  fixed: {fp}")

    print(f"\nFixed {fixed_files} files")

    # Re-check
    proc2 = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "src/", "--select=SIM102", "--statistics"],
        capture_output=True,
        text=True,
    )
    remaining = proc2.stdout.strip() or "0 SIM102 issues"
    print(f"Remaining: {remaining}")


if __name__ == "__main__":
    main()
