#!/usr/bin/env python3
"""Sync Ollama-discovered models to LM Studio by locating local model files
matching Ollama model names and creating links into LM Studio models dir.

Usage:
  python scripts/sync_ollama_to_lmstudio.py --ollama-base http://localhost:11434 \
      --search-dirs C:\\models D:\\gguf --lmstudio-dir C:\\Users\\keath\\.lmstudio\\models --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.error import URLError


def get_ollama_models(base: str) -> list[str]:
    url = base.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.load(r)
            models = [m.get("name") or m.get("model") for m in data.get("models", [])]
            return [m for m in models if m]
    except URLError as e:
        print(f"Failed to query Ollama at {url}: {e}")
        return []


def find_matching_files(model_name: str, search_dirs: list[Path]) -> list[Path]:
    matches = []
    key = model_name.lower()
    for d in search_dirs:
        if not d.exists():
            continue
        # search for gguf files whose name or parent dir contains model name
        for p in d.rglob("*.gguf"):
            n = p.name.lower()
            parent = p.parent.name.lower()
            if key in n or key in parent:
                matches.append(p.resolve())
    return matches


def make_link(src: Path, dest: Path, apply: bool) -> bool:
    if dest.exists():
        print(f"Skipping existing: {dest}")
        return False
    print(f"Link: {src} -> {dest}")
    if not apply:
        return True
    try:
        os.symlink(str(src), str(dest), target_is_directory=src.is_dir())
        return True
    except OSError:
        # fallback to junction on Windows
        if sys.platform.startswith("win"):
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                f"New-Item -ItemType Junction -Path '{dest}' -Target '{src}'",
            ]
            try:
                subprocess.run(cmd, check=True)
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed to create junction: {e}")
                return False
        # POSIX fallback failure
        print("Failed to create link on this platform")
        return False


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ollama-base", default="http://localhost:11434")
    ap.add_argument("--search-dirs", nargs="+", required=True)
    ap.add_argument("--lmstudio-dir", default=None)
    ap.add_argument("--dry-run", action="store_true", help="Do not create links")
    args = ap.parse_args(argv)

    search_dirs = [Path(p).expanduser() for p in args.search_dirs]
    if args.lmstudio_dir:
        lm_dir = Path(args.lmstudio_dir).expanduser()
    else:
        lm_dir = Path(os.environ.get("USERPROFILE", Path.home())) / ".lmstudio" / "models"

    lm_dir.mkdir(parents=True, exist_ok=True)

    print("Querying Ollama for models...")
    models = get_ollama_models(args.ollama_base)
    if not models:
        print("No models reported by Ollama or failed to reach Ollama.")
        return 2

    print(f"Found {len(models)} models from Ollama")
    for m in models:
        print(f"\nModel: {m}")
        matches = find_matching_files(m, search_dirs)
        if not matches:
            print("  No local files matched; consider adding search dirs or downloading model to a known path.")
            continue
        for src in matches:
            # prefer file stem for filenames, otherwise directory name
            base = src.stem if src.is_file() else src.name
            dest = lm_dir / base
            make_link(src, dest, apply=not args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
