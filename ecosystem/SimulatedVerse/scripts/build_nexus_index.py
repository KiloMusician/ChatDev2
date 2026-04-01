#!/usr/bin/env python3
import hashlib
import json
import os
import re
import time
from pathlib import Path

ROOT = Path(".").resolve()
NEXUS = ROOT / "NEXUS"
DATASETS = NEXUS / "datasets"
MAPS = NEXUS / "maps"
SCHEMAS = NEXUS / "schemas"

IGNORE_DIRS = {".git", ".snapshot", "node_modules", ".venv", ".mypy_cache", "__pycache__", ".ruff_cache"}
ROSETTA_RE = re.compile(r"^#\s*---\s*ROSETTA\s*---(.*?)#\s*---\s*/ROSETTA\s*---", re.S | re.M)


def sha256(p: Path):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lang_of(p: Path):
    ext = p.suffix.lower()
    return {
        ".ts": "ts",
        ".tsx": "tsx",
        ".js": "js",
        ".jsx": "jsx",
        ".py": "py",
        ".md": "md",
        ".json": "json",
        ".sh": "sh",
        ".yml": "yml",
        ".yaml": "yaml",
        ".css": "css",
        ".html": "html",
    }.get(ext, ext.strip("."))


def parse_rosetta(text: str):
    m = ROSETTA_RE.search(text)
    if not m:
        return None
    block = m.group(1)
    kv = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            kv[k.strip()] = v.strip()
    return kv


def collect():
    index_lines = []
    anchors = []
    for d, _, files in os.walk(ROOT):
        dpath = Path(d)
        if any(part in IGNORE_DIRS for part in dpath.parts):
            continue
        for f in files:
            p = dpath / f
            if any(part in IGNORE_DIRS for part in p.parts):
                continue
            if str(p).startswith(str(NEXUS)):
                continue
            rel = str(p.relative_to(ROOT))
            try:
                size = p.stat().st_size
                lang = lang_of(p)
                content = ""
                if size < 2_000_000 and lang in {
                    "ts",
                    "tsx",
                    "js",
                    "jsx",
                    "py",
                    "md",
                    "json",
                    "yml",
                    "yaml",
                    "html",
                    "css",
                    "sh",
                }:
                    content = p.read_text(errors="ignore")
                rosetta = parse_rosetta(content or "")
                line = {
                    "path": rel,
                    "sha256": sha256(p),
                    "size": size,
                    "lang": lang or "",
                    "rosetta": rosetta or {},
                    "tags": (rosetta.get("TAGS","").split(",") if rosetta else []),
                    "anchors": []
                }
                # rudimentary anchor sniffing (APIs, pages, agents)
                if "/routes" in rel and ("api/" in content or "router." in content):
                    line["anchors"].append({"kind": "endpoint", "id": rel})
                if "client/src/pages" in rel:
                    line["anchors"].append({"kind": "page", "id": rel})
                if "agents/" in rel:
                    line["anchors"].append({"kind": "agent", "id": rel})
                index_lines.append(line)
                anchors.extend(line["anchors"])
            except Exception:
                # tolerate unreadable files
                pass
    return index_lines, anchors


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    NEXUS.mkdir(exist_ok=True)
    (NEXUS / "datasets").mkdir(parents=True, exist_ok=True)
    (NEXUS / "maps").mkdir(parents=True, exist_ok=True)

    index_lines, anchors = collect()

    write_jsonl(DATASETS / "index.ndjson", index_lines)
    with (MAPS / "tree.snapshot.json").open("w", encoding="utf-8") as f:
        json.dump({"generated_at": int(time.time()), "files": len(index_lines)}, f)

    # naive module graph (mermaid)
    modules: dict[str, int] = {}
    for x in index_lines:
        top = x["path"].split("/")[0]
        modules[top] = modules.get(top, 0) + 1
    mermaid = "graph TD\n" + "\n".join([f'  A["repo"] -->|{c}| "{m}"' for m, c in sorted(modules.items())])
    (NEXUS / "maps" / "modules.mmd").write_text(mermaid)


if __name__ == "__main__":
    main()
