#!/usr/bin/env python3
"""Register local GGUF/LLM model folders with LM Studio by creating
directory junctions/symlinks into the LM Studio models directory.

This utility is Windows-first but supports POSIX symlinks. It performs a
dry-run by default and can create junctions using PowerShell if os.symlink
is not permitted.

Usage:
  python scripts/register_local_models.py --search-dirs "C:\\models" "C:\\other_models" \
      --lmstudio-dir "C:\\Users\\keath\\.lmstudio\\models" --apply

Options:
  --search-dirs DIR [DIR ...]   Directories to search for model files (gguf)
  --lmstudio-dir DIR            LM Studio models directory (default: ~/.lmstudio/models)
  --apply                       Actually create junctions/symlinks (default: dry-run)
  --http-ping URL               After linking, optionally ping LM Studio models endpoint
  --verbose                     Verbose output
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# ensure repo root and src are importable when running as a script
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))
try:
    from src.shared.model_registry import ModelRegistry
except Exception:
    # fallback import path when running scripts from repo root
    from shared.model_registry import ModelRegistry  # type: ignore


def find_models(search_dirs: list[Path]) -> list[Path]:
    """Return a list of model files or model directories containing .gguf files.

    This collects both individual .gguf files and parent directories that contain
    .gguf files, and returns unique, resolved paths.
    """
    found = set()
    for d in search_dirs:
        if not d.exists():
            continue
        for p in d.rglob("*.gguf"):
            found.add(p.resolve())
            found.add(p.resolve().parent)
    return [Path(p) for p in sorted(str(p) for p in found)]


def make_link(src: Path, dest: Path, apply: bool, verbose: bool) -> bool:
    if dest.exists():
        if verbose:
            print(f"Skipping existing: {dest}")
        return False
    print(f"Linking {src} -> {dest}")
    if not apply:
        return True

    try:
        # Try native symlink (may require developer mode on Windows)
        os.symlink(str(src), str(dest), target_is_directory=src.is_dir())
        return True
    except (OSError, NotImplementedError) as e:
        if verbose:
            print(f"os.symlink failed: {e}; trying PowerShell junction (Windows)")

    # Windows junction via PowerShell New-Item -ItemType Junction
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
            print(f"Failed to create junction via PowerShell: {e}")
            return False
    else:
        # POSIX fallback: create symlink with os.symlink already tried, so fail
        print("Failed to create link on this platform")
        return False


def ping_models_endpoint(url: str) -> None:
    try:
        import urllib.request
        from urllib.error import URLError

        with urllib.request.urlopen(url, timeout=5) as r:
            data = r.read().decode("utf-8")
            print("Ping response (truncated):")
            print(data[:1000])
    except URLError as e:
        print(f"Failed to ping {url}: {e}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Register local LLM model files with LM Studio")
    ap.add_argument("--search-dirs", nargs="+", required=False)
    ap.add_argument("--lmstudio-dir", default=None)
    ap.add_argument("--apply", action="store_true", help="Create links; default is dry-run")
    ap.add_argument(
        "--http-ping",
        default=None,
        help="URL to ping after linking (e.g., http://localhost:1234/v1/models)",
    )
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    def _load_model_paths() -> dict[str, Any]:
        cfg_path = repo_root / "config" / "model_paths.json"
        if not cfg_path.exists():
            return {}
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def _expand_path(p: str) -> Path:
        env = os.environ.get("USERPROFILE") or str(Path.home())
        return Path(p.replace("${USERPROFILE}", env)).expanduser()

    if args.search_dirs:
        search_dirs = [Path(p).expanduser() for p in args.search_dirs]
    else:
        cfg = _load_model_paths()
        cfg_dirs = cfg.get("search_dirs") or []
        search_dirs = [_expand_path(p) for p in cfg_dirs]
    if args.lmstudio_dir:
        lm_dir = Path(args.lmstudio_dir).expanduser()
    else:
        cfg = _load_model_paths()
        cfg_dir = cfg.get("lmstudio_models_dir")
        if cfg_dir:
            lm_dir = _expand_path(cfg_dir)
        else:
            lm_dir = Path(os.environ.get("USERPROFILE", Path.home())) / ".lmstudio" / "models"

    if args.verbose:
        print(f"Searching: {search_dirs}")
        print(f"LM Studio models dir: {lm_dir}")

    lm_dir.mkdir(parents=True, exist_ok=True)

    # model registry (state/registry.json)
    registry = ModelRegistry()

    models = find_models(search_dirs)
    if not models:
        print("No models found in search dirs.")
        return 2

    for m in models:
        # determine destination folder name
        base = m.name
        if m.is_file():
            base = Path(m).stem
        dest = lm_dir / base
        make_link(m, dest, args.apply, args.verbose)
        # prepare metadata for registry (schema requires name, source, path)
        try:
            stat = m.stat()
            size = stat.st_size
            mtime = stat.st_mtime
        except Exception:
            size = None
            mtime = None
        metadata = {
            "path": str(m),
            "name": base,
            "source": "lmstudio" if ".lmstudio" in str(m) else "ollama",
            "dest": str(dest),
            "format": "gguf" if m.suffix.lower() == ".gguf" or any(m.glob("*.gguf")) else "unknown",
            "size_bytes": size,
            "mtime": mtime,
            "metadata": {"is_dir": m.is_dir()},
        }
        if args.verbose:
            print(f"Registry: proposed metadata: {metadata}")
        if args.apply:
            registered = registry.register_model(metadata, apply=True)
            if args.verbose:
                print(f"Registry: registered={registered}")
        else:
            # dry-run: show what would be registered
            print(f"Registry (dry-run): would register {metadata['path']} -> {metadata['dest']}")

    if args.http_ping:
        ping_models_endpoint(args.http_ping)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
