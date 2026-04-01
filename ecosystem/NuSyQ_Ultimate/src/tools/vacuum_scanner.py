#!/usr/bin/env python3
# Vacuum-mode TODO/FIXME scanner (no external deps)
# Ported from SimulatedVerse with UTF-8 Windows fix
import io
import json
import os
import re
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def scan_file(path):
    patterns = [
        r"\b(TODO|FIXME|XXX|HACK|WIP|TBD)\b",
        r"console\.log\(",
        r"print\(",
        r"debugger;?",
        r'throw new Error\(["\']TODO',
    ]

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        issues = []
        for i, line in enumerate(content.split("\n"), 1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        {
                            "line": i,
                            "text": line.strip()[:100],
                            "pattern": pattern
                        }
                    )
        return issues
    except (OSError, UnicodeDecodeError) as e:
        print(f"⚠️ Warning: Failed to scan {path}: {e}")
        return []


def main():
    exclude = {
        ".git",
        "node_modules",
        ".cache",
        ".attic",
        ".quarantine",
        ".venv",
        "__pycache__",
    }
    results = {}

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude]

        for f in files:
            if f.endswith((
                ".ts", ".js", ".py", ".gd", ".tsx", ".jsx", ".md", ".yaml"
            )):
                path = os.path.join(root, f)
                issues = scan_file(path)
                if issues:
                    results[path] = issues

    os.makedirs("ops/receipts", exist_ok=True)
    with open("ops/receipts/vacuum_scan.json", "w", encoding="utf-8") as w:
        json.dump(results, w, indent=2)

    total = sum(len(issues) for issues in results.values())
    print(f"[OK] Scanned {len(results)} files with {total} issues")
    print("Receipt: ops/receipts/vacuum_scan.json")

    if results:
        print("\nTop 10 files:")
        sorted_files = sorted(
            results.items(), key=lambda x: len(x[1]), reverse=True
        )[:10]
        for file_path, issues in sorted_files:
            print(f"  {file_path}: {len(issues)} issues")


if __name__ == "__main__":
    main()
