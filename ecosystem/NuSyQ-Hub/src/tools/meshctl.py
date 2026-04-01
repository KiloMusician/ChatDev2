"""meshctl - lightweight mesh/lattice management CLI.

Creates a small index and exports embeddings for lattices.

Usage (examples):
  python -m src.tools.meshctl index lattices/vibe.json --out ./.hub/index.json --dry-run
  python -m src.tools.meshctl embed --lattice lattices/vibe.json --out lattices/vibe.embeddings.jsonl --dry-run

This module prefers reuse: if an existing indexer module is present (src.tools.vibe_indexer)
it will call into it. Embedding work delegates to src.tools.embeddings_exporter.
"""

from __future__ import annotations

import argparse
import json
import logging
import pathlib
import sys
from typing import Any

logger = logging.getLogger(__name__)


EXCLUDES = {".venv", "node_modules", ".git", "dist", "build", ".cache"}


def safe_path_parts(p: pathlib.Path) -> list[str]:
    try:
        return list(p.parts)
    except (AttributeError, OSError):
        return [str(p)]


def cmd_index(args: argparse.Namespace) -> None:
    paths = [pathlib.Path(p) for p in args.paths]
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    index: dict[str, list[dict[str, str]]] = {"lattices": []}

    # Try to reuse existing indexer if available
    _vi: Any | None = None
    try:
        from src.tools import vibe_indexer as _vi  # type: ignore[assignment]
    except (ImportError, ModuleNotFoundError):
        _vi = None

    for p in paths:
        # skip excluded components
        if any(part in EXCLUDES for part in safe_path_parts(p)):
            continue

        if p.is_file() and p.name.endswith(".json") and "vibe" in p.name.lower():
            index["lattices"].append({"id": p.stem, "path": str(p)})
        elif p.is_dir() and _vi is not None:
            # if directory and we have a vibe_indexer, call it to produce a lattice
            try:
                outp = out.parent / (p.name + "-lattice.json")
                if args.dry_run:
                    pass
                else:
                    _vi.main([str(p), "--out", str(outp)])
                    index["lattices"].append({"id": p.name, "path": str(outp)})
            except (OSError, RuntimeError):
                logger.debug("Suppressed OSError/RuntimeError", exc_info=True)

    if args.dry_run:
        pass
    else:
        out.write_text(json.dumps(index, indent=2))


def cmd_embed(args: argparse.Namespace) -> None:
    # delegate to embeddings_exporter
    try:
        from src.tools.embeddings_exporter import embed_lattice
    except (ImportError, ModuleNotFoundError):
        sys.exit(2)

    embed_lattice(
        lattice=args.lattice,
        out=args.out,
        dry_run=args.dry_run,
        model=args.model,
        rate_limit=args.rate_limit,
    )


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    ap = argparse.ArgumentParser("meshctl")
    sp = ap.add_subparsers(dest="cmd")

    ix = sp.add_parser("index")
    ix.add_argument("paths", nargs="+", help="files or directories to index")
    ix.add_argument("--out", default="./.hub/index.json")
    ix.add_argument("--dry-run", action="store_true")
    ix.set_defaults(func=cmd_index)

    em = sp.add_parser("embed")
    em.add_argument("--lattice", default="lattices/vibe.json")
    em.add_argument("--out", default="lattices/vibe.embeddings.jsonl")
    em.add_argument("--model", default="ollama:nomic-embed-text")
    em.add_argument("--rate-limit", type=float, default=8.0)
    em.add_argument("--dry-run", action="store_true")
    em.set_defaults(func=cmd_embed)

    args = ap.parse_args(argv)
    if not hasattr(args, "func"):
        ap.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
