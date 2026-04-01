"""Simple indexer for 'vibe' lattices.

Usage:
  python -m src.tools.vibe_indexer <path_to_repo> --out <out.json>

This script looks for README*.md files under the provided path, parses
headings and links, and produces a small manifest (lattice JSON) suitable
for registeration with local RAG/agents.

It's deliberately conservative and uses only the standard library so it
can run in minimal CI.
"""

# mypy: disable-error-code=unreachable

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:
    from datetime import timezone

    UTC = timezone.utc  # noqa: UP017

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s*(.+)$")


def find_md_files(root: Path) -> list[Path]:
    md: list[Any] = []
    for p in root.rglob("*.md"):
        # skip node_modules or hidden .git
        if ".git" in p.parts:
            continue
        md.append(p)
    return sorted(md)


def parse_markdown_sections(path: Path) -> list[tuple[str, str]]:
    """Return list of (heading, body_text) tuples for the file.

    If no headings found, the whole file is returned under a top-level
    heading derived from the filename.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    sections: list[tuple[str, str]] = []
    cur_head = None
    cur_buf: list[str] = []
    for ln in lines:
        m = HEADING_RE.match(ln)
        if m:
            # push previous
            if cur_head is not None:
                sections.append((cur_head, "\n".join(cur_buf)))
            cur_head = m.group(2).strip()
            cur_buf = []
        else:
            cur_buf.append(ln)
    if cur_head is not None:
        sections.append((cur_head, "\n".join(cur_buf)))
    else:
        # whole file as one section
        sections = [(path.stem, text)]
    return sections


def extract_links(text: str) -> list[tuple[str, str]]:
    return LINK_RE.findall(text)


def heuristics_for_node(url: str) -> dict:
    """Guess kind and fit from a url/text hint."""
    kind = "doc"
    fit = "doc"
    if "github.com" in url:
        kind = "repo"
        fit = "ide"
    if url.endswith((".zip", ".tgz")):
        kind = "artifact"
        fit = "browser"
    if url.startswith("http") and ("chrome" in url or "extension" in url):
        kind = "plugin"
        fit = "ide"
    return {"kind": kind, "fit": fit}


def node_id_from_title(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    if not slug:
        slug = "node"
    return slug


def build_lattice(root: Path) -> dict:
    md_files = find_md_files(root)
    nodes: list[Any] = []
    edges: list[Any] = []
    seen: dict[str, Any] = {}
    for p in md_files:
        sections = parse_markdown_sections(p)
        for heading, body in sections:
            links = extract_links(body)
            node_title = f"{p.name}::{heading}"
            nid = node_id_from_title(node_title)
            mtime = p.stat().st_mtime
            rev_ts = datetime.utcfromtimestamp(mtime).isoformat() + "Z"
            node: dict[str, Any] = {
                "id": nid,
                "title": node_title,
                "file": str(p.relative_to(root)),
                "shadow": {
                    "lic": "unknown",
                    "fresh": rev_ts,
                    "fit": "doc",
                    "risk": "med",
                },
                "links": [],
            }
            for text, url in links:
                node["links"].append({"text": text, "url": url})
                guess = heuristics_for_node(url)
                # create a lightweight node for the target if not seen
                tgt_id = node_id_from_title(url)
                if tgt_id not in seen:
                    seen[tgt_id] = {
                        "id": tgt_id,
                        "title": url,
                        "file": None,
                        "shadow": {
                            "lic": "unknown",
                            "fresh": None,
                            "fit": guess["fit"],
                            "risk": "med",
                        },
                    }
                edges.append({"from": nid, "to": seen[tgt_id]["id"], "rel": "references"})
            nodes.append(node)
    # add seen nodes
    for v in seen.values():
        nodes.append(v)

    return {
        "lattice": "vibe-coding",
        "rev": datetime.now(UTC).isoformat(),
        "nodes": nodes,
        "edges": edges,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Index a local 'vibe' repo into a lattice JSON")
    parser.add_argument("path", help="Path to cloned repo (e.g. ./_vibe)")
    parser.add_argument("--out", default="lattices/vibe.json", help="Output lattice JSON path")
    args = parser.parse_args(argv)

    root = Path(args.path)
    if not root.exists():
        return 2

    lattice = build_lattice(root)
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8") as fh:
        json.dump(lattice, fh, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
