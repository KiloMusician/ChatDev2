#!/usr/bin/env python3
"""
Generate a TODO/FIXME/HACK summary across the repository and write a markdown report.
"""

import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [r"TODO", r"FIXME", r"XXX", r"HACK", r"WIP", r"TBD"]
RE = re.compile(r"\b(?:" + "|".join(PATTERNS) + r")\b", re.IGNORECASE)

counts = Counter()
per_file = defaultdict(int)

for p in ROOT.rglob("*"):
    if p.is_file():
        try:
            text = p.read_text(encoding="utf8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        matches = RE.findall(text)
        if matches:
            per_file[str(p.relative_to(ROOT))] = len(matches)
            counts.update([m.upper() for m in matches])

# Write report
out_dir = ROOT / "docs"
out_dir.mkdir(exist_ok=True)
report = out_dir / "TODO_SUMMARY.md"
with report.open("w", encoding="utf8") as f:
    f.write("# TODO/FIXME/HACK Summary\n\n")
    f.write("Patterns counted: {}\n\n".format(", ".join(PATTERNS)))
    f.write("Total occurrences by pattern:\n\n")
    for pat, num in counts.most_common():
        f.write(f"- {pat}: {num}\n")
    f.write("\nTop files by occurrences:\n\n")
    for fname, num in sorted(per_file.items(), key=lambda x: x[1], reverse=True)[:50]:
        f.write(f"- {num:4d}  {fname}\n")

print("Wrote TODO summary to", str(report))
