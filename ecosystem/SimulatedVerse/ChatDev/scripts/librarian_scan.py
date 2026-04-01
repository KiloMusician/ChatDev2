#!/usr/bin/env python3
"""
Zero-token local scan: Obsidian vault, notebooks, markdown docs → index.json
"""
import os
import json
import re
ROOT = os.getcwd()
vaults = [os.path.join(ROOT,"obsidian"), os.path.join(ROOT,"docs"), os.path.join(ROOT,"knowledge")]
index = {"md":[], "ipynb":[], "metrics":{"todos":0,"placeholders":0}}
for base in vaults:
  if not os.path.isdir(base): continue
  for dp,_,files in os.walk(base):
    for f in files:
      p = os.path.join(dp,f)
      try:
        if f.endswith(".md"):
          t = open(p, "r", encoding="utf-8", errors="ignore").read()
          index["md"].append({"path":p, "title": re.findall(r"#\\s+(.*)", t[:200])[:1] or ["Untitled"]})
          index["metrics"]["todos"] += len(re.findall(r"TODO|FIXME|PLACEHOLDER", t))
        if f.endswith(".ipynb"):
          index["ipynb"].append({"path":p})
      except:
        continue
os.makedirs(".ship", exist_ok=True)
open(".ship/librarian_index.json","w",encoding="utf-8").write(json.dumps(index,indent=2))
print("[Librarian] index written to .ship/librarian_index.json")