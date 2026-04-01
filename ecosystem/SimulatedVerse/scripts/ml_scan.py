#!/usr/bin/env python3
import json
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv)>1 else "."
ML_HINTS = re.compile(r"(ml|model|models|ai|training|notebook|notebooks|pipeline|embedd|inference)", re.I)
PLACEHOLDER_PAT = re.compile(r"(TODO|TBD|WIP|placeholder|null|pass|raise NotImplementedError)", re.I)

inventory = []
for base, _dirs, files in os.walk(ROOT):
    rel = os.path.relpath(base, ROOT)
    hits = ML_HINTS.search(rel)
    for f in files:
        p = os.path.join(base, f)
        try:
            size = os.path.getsize(p)
        except OSError:
            size = -1
        tag = "neutral"
        if hits or ML_HINTS.search(f):
            tag = "ml-suspect"
        placeholder = False
        if f.endswith((".py",".ts",".js",".md",".json",".ipynb",".yaml",".yml")):
            try:
                with open(p, "rb") as fh:
                    head = fh.read(4096).decode("utf-8","ignore")
                if PLACEHOLDER_PAT.search(head) or size==0:
                    placeholder = True
            except OSError:
                pass
        if tag=="ml-suspect":
            inventory.append({
                "path": p, "size": size,
                "placeholder": placeholder,
                "ext": os.path.splitext(f)[1]
            })

print(json.dumps(inventory, indent=2))
