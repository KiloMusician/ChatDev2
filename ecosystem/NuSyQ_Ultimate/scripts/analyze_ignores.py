"""analyze_ignores.py

Scan repository ignore and git-related files across the workspace and produce
a simple JSON report highlighting cross-repo references and potential issues.

Run from workspace root: python scripts/analyze_ignores.py
"""

import json
from pathlib import Path

ROOTS = [
    Path("c:/Users/keath/NuSyQ"),
    Path(r"c:/Users/keath/Desktop/Legacy/NuSyQ-Hub"),
    Path(r"c:/Users/keath/Desktop/SimulatedVerse"),
]

PATTERNS = [
    ".gitignore",
    ".dockerignore",
    ".gitattributes",
    ".gitmodules",
    ".prettierignore",
    ".eslintignore",
    "CODEOWNERS",
]


def load_file(p: Path):
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def analyze():
    report = {"files": []}
    for root in ROOTS:
        for pat in PATTERNS:
            for p in root.rglob(pat):
                txt = load_file(p)
                item = {
                    "path": str(p),
                    "root": str(root),
                    "pattern": pat,
                    "present": txt is not None,
                    "references": [],
                }
                if txt:
                    # find simple cross-repo references that look like sibling paths
                    lines = [
                        ln.strip()
                        for ln in txt.splitlines()
                        if ln.strip() and not ln.strip().startswith("#")
                    ]
                    for ln in lines:
                        # heuristic: lines with a slash and a repo-like token
                        if ("/" in ln) and (
                            "ChatDev" in ln or "NuSyQ-Hub" in ln or "SimulatedVerse" in ln
                        ):
                            item["references"].append(ln)
                report["files"].append(item)

    out = Path("c:/Users/keath/NuSyQ/state/ignore_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote report to {out}")


if __name__ == "__main__":
    analyze()
