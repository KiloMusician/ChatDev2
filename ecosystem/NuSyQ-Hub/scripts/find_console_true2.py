#!/usr/bin/env python3
import os
import re

pattern = re.compile(r"console\.log\s*\(([^)]*)\)")

matches = []
for root, _dirs, files in os.walk("src"):
    for f in files:
        if f.endswith((".js", ".ts", ".tsx", ".jsx")):
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        m = pattern.search(line)
                        if m:
                            arg = m.group(1).strip()
                            if arg in ("true", '"true"', "'true'"):
                                matches.append(f"{path}:{i}:{line.strip()}")
            except Exception:
                pass

if not matches:
    print("no matches")
else:
    print("\n".join(matches[:50]))
