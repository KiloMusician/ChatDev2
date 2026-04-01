#!/usr/bin/env python3
import os

matches = []
for root, _dirs, files in os.walk("src"):
    for f in files:
        if f.endswith((".js", ".ts")):
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        if "console.log(true" in line:
                            matches.append(f"{path}:{i}:{line.strip()}")
            except Exception:
                pass

if not matches:
    print("no matches")
else:
    print("\n".join(matches[:50]))
