#!/usr/bin/env python3
from __future__ import annotations

import fnmatch
import json
import os
import pathlib
import re
import time
from collections import defaultdict
from typing import Any

ROOT = pathlib.Path(os.getenv("GIT_ROOT") or pathlib.Path(".").resolve())
OUTDIR = ROOT / "reports" / "chatdev_audit"
OUTDIR.mkdir(parents=True, exist_ok=True)
STAMP = time.strftime("%Y%m%d-%H%M%S")
JSON_OUT = OUTDIR / f"deep_{STAMP}.json"
MD_OUT   = OUTDIR / f"deep_{STAMP}.md"

IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".replit", ".idea", ".vscode"}
PATTERNS = [
  r"\bchatdev\b", r"\bChatDev\b", r"chat[-_\s]?dev", r"agents/team\.ya?ml", r"chatdev\.ya?ml",
  r"chatdev\.config\.(json|ya?ml|toml)"
]
PAT = re.compile("|".join(PATTERNS), re.IGNORECASE)

def iter_files(root: pathlib.Path):
  for base, dirs, files in os.walk(root):
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
    for f in files:
      yield pathlib.Path(base) / f

hits_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
by_ext: dict[str, int] = defaultdict(int)
configs: list[str] = []
packages: dict[str, list[str]] = {"npm": [], "py": []}
imports: dict[str, int] = defaultdict(int)

for p in iter_files(ROOT):
  rel = p.relative_to(ROOT)
  ext = p.suffix.lower()
  by_ext[ext] += 1

  # config find
  if fnmatch.fnmatch(p.name.lower(), "chatdev.y*ml") or fnmatch.fnmatch(str(rel), "*agents/team.y*ml"):
    configs.append(str(rel))

  try:
    text = p.read_text("utf-8", errors="ignore")
  except Exception:
    continue

  # hits
  if PAT.search(text):
    for i, line in enumerate(text.splitlines(), 1):
      if PAT.search(line):
        hits_by_file[str(rel)].append({"line": i, "text": line.strip()})

  # very rough import/require sniff
  if ext in {".ts", ".js", ".mjs", ".cjs", ".tsx", ".jsx"}:
    for m in re.findall(r"(?:from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))", text):
      mod = (m[0] or m[1]).strip()
      if "chatdev" in mod.lower():
        imports[mod] += 1
  if ext in {".py"}:
    for m in re.findall(r"^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)", text, re.M):
      if "chatdev" in m.lower():
        imports[m] += 1

# package hints
pkg_json = ROOT / "package.json"
if pkg_json.exists():
  try:
    pj = json.loads(pkg_json.read_text())
    for sect in ("dependencies","devDependencies","optionalDependencies"):
      for k in (pj.get(sect) or {}):
        if "chatdev" in k.lower():
          packages["npm"].append(f"{sect}:{k}")
  except Exception:
    pass

req = ROOT / "requirements.txt"
if req.exists():
  try:
    for line in req.read_text().splitlines():
      if "chatdev" in line.lower():
        packages["py"].append(line.strip())
  except Exception:
    pass

pyproj = ROOT / "pyproject.toml"
if pyproj.exists():
  for line in pyproj.read_text().splitlines():
    if "chatdev" in line.lower():
      packages["py"].append(line.strip())

# score
score = 0
score += min(25, len(hits_by_file))           # breadth of references
score += 15 if configs else 0                 # config present
score += min(20, sum(imports.values()))       # import strength
score += 10 if packages["npm"] or packages["py"] else 0
score = min(100, score)

data = {
  "root": str(ROOT),
  "timestamp": STAMP,
  "refs": hits_by_file,
  "imports": imports,
  "configs": configs,
  "packages": packages,
  "by_ext": by_ext,
  "zeta_integration_score": score
}
JSON_OUT.write_text(json.dumps(data, indent=2))

# markdown summary
with MD_OUT.open("w", encoding="utf-8") as f:
  f.write(f"# ChatDev Deep Audit ({STAMP})\n\n")
  f.write(f"- Root: `{ROOT}`\n")
  f.write(f"- ZETA Integration Score: **{score}/100**\n")
  f.write("\n## Configs\n")
  for c in (configs or ["(none)"]):
    f.write(f"- {c}\n")
  f.write("\n## Packages\n")
  for n in (packages["npm"] or ["(npm: none)"]):
    f.write(f"- {n}\n")
  for p in (packages["py"]  or ["(py: none)"]):
    f.write(f"- {p}\n")
  f.write("\n## Imports\n")
  for k, v in (imports.items() or [("(none)", 0)]):
    f.write(f"- {k}: {v}\n")
  f.write("\n## Top Reference Files\n")
  for fn, h in sorted(hits_by_file.items(), key=lambda x: -len(x[1]))[:20]:
    f.write(f"- {fn} (hits: {len(h)})\n")
  f.write("\n> Full JSON: " + str(JSON_OUT) + "\n")

# Symlink latest
(OUTDIR / "LATEST.md").unlink(missing_ok=True)
(OUTDIR / "LATEST.md").symlink_to(MD_OUT.name)

print(str(MD_OUT))
