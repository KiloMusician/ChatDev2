#!/usr/bin/env python3
"""Discover and sync local LLM models between Ollama and LM Studio.

This script:
1. Discovers models from configured paths (model_paths.json)
2. Queries running Ollama/LM Studio APIs for active models
3. Populates state/registry.json with discovered models
4. Creates symlinks/junctions to sync models between systems
5. Reports model inventory and sync status

Usage:
    # Discovery only (dry-run):
    python scripts/discover_and_sync_models.py --discover

    # Full sync (creates links):
    python scripts/discover_and_sync_models.py --discover --sync --apply

    # Query APIs only:
    python scripts/discover_and_sync_models.py --query-apis

    # Full workflow:
    python scripts/discover_and_sync_models.py --discover --query-apis --sync --apply
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError

# Ensure repo root is in path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from src.setup import load_dotenv
from src.shared.model_registry import ModelRegistry


def load_workspace_env() -> None:
    """Load layered dotenv files with workspace overrides taking precedence."""
    load_dotenv(str(repo_root / ".env.workspace"))
    load_dotenv(str(repo_root / ".env"))
    load_dotenv(str(repo_root / ".env.docker"))


def resolve_lmstudio_base_url() -> str:
    """Return the canonical LM Studio base URL for this workspace."""
    return (
        str(
            os.getenv("NUSYQ_LMSTUDIO_BASE_URL")
            or os.getenv("LMSTUDIO_BASE_URL")
            or os.getenv("LM_STUDIO_BASE_URL")
            or "http://10.0.0.172:1234"
        )
        .strip()
        .rstrip("/")
    )


load_workspace_env()


def expand_path(path_str: str) -> Path:
    """Expand environment variables and user paths."""
    env_map = {
        "${USERPROFILE}": os.environ.get("USERPROFILE", str(Path.home())),
        "$USERPROFILE": os.environ.get("USERPROFILE", str(Path.home())),
        "~": str(Path.home()),
    }
    result = path_str
    for var, value in env_map.items():
        result = result.replace(var, value)
    return Path(result).expanduser().resolve()


def load_model_paths_config() -> dict[str, Any]:
    """Load model_paths.json configuration."""
    cfg_path = repo_root / "config" / "model_paths.json"
    if not cfg_path.exists():
        return {
            "search_dirs": [],
            "lmstudio_models_dir": "",
            "ollama_models_dir": "",
        }
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def discover_gguf_files(search_dirs: list[Path], verbose: bool = False) -> list[dict[str, Any]]:
    """Discover all .gguf files in search directories.

    Returns list of model metadata dicts.
    """
    models = []
    seen_paths = set()

    for search_dir in search_dirs:
        if not search_dir.exists():
            if verbose:
                print(f"⚠️  Search directory does not exist: {search_dir}")
            continue

        if verbose:
            print(f"🔍 Scanning: {search_dir}")

        for gguf_file in search_dir.rglob("*.gguf"):
            if gguf_file in seen_paths:
                continue
            seen_paths.add(gguf_file)

            try:
                size_bytes = gguf_file.stat().st_size
                size_gb = size_bytes / (1024**3)

                metadata = {
                    "path": str(gguf_file),
                    "name": gguf_file.name,
                    "source": "local_discovery",
                    "format": "gguf",
                    "size_bytes": size_bytes,
                    "metadata": {
                        "parent_dir": gguf_file.parent.name,
                        "size_gb": round(size_gb, 2),
                        "discovered_at": datetime.now(UTC).isoformat(),
                    },
                }
                models.append(metadata)

                if verbose:
                    print(f"  ✅ Found: {gguf_file.name} ({size_gb:.2f} GB)")

            except Exception as e:
                if verbose:
                    print(f"  ❌ Error reading {gguf_file}: {e}")

    return models


def query_ollama_api(base_url: str = "http://localhost:11434") -> list[dict[str, Any]]:
    """Query Ollama API for available models."""
    url = base_url.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.load(r)
            models = []
            for m in data.get("models", []):
                model_name = m.get("name", m.get("model", "unknown"))
                size_bytes = m.get("size", 0)
                models.append(
                    {
                        "name": model_name,
                        "source": "ollama_api",
                        "format": "ollama",
                        "size_bytes": size_bytes,
                        "metadata": {
                            "modified_at": m.get("modified_at"),
                            "digest": m.get("digest"),
                            "details": m.get("details", {}),
                        },
                    }
                )
            print(f"✅ Ollama API: {len(models)} models")
            return models
    except URLError as e:
        print(f"⚠️  Ollama API unreachable at {url}: {e}")
        return []


def query_lmstudio_api(base_url: str | None = None) -> list[dict[str, Any]]:
    """Query LM Studio API for available models."""
    url = (base_url or resolve_lmstudio_base_url()).rstrip("/") + "/v1/models"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.load(r)
            models = []
            for m in data.get("data", []):
                model_id = m.get("id", "unknown")
                models.append(
                    {
                        "name": model_id,
                        "source": "lmstudio_api",
                        "format": "lmstudio",
                        "size_bytes": 0,  # LM Studio API doesn't report size
                        "metadata": {
                            "type": m.get("type"),
                            "object": m.get("object"),
                        },
                    }
                )
            print(f"✅ LM Studio API: {len(models)} models")
            return models
    except URLError as e:
        print(f"⚠️  LM Studio API unreachable at {url}: {e}")
        return []


def sync_to_lmstudio(
    discovered_models: list[dict[str, Any]],
    lmstudio_dir: Path,
    apply: bool = False,
    verbose: bool = False,
) -> int:
    """Create symlinks from discovered models to LM Studio models directory."""
    if not lmstudio_dir.exists():
        lmstudio_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created LM Studio directory: {lmstudio_dir}")

    linked_count = 0
    for model in discovered_models:
        if model.get("format") != "gguf":
            continue  # Only sync GGUF files

        src_path = Path(model["path"])
        if not src_path.exists():
            continue

        # Create link in LM Studio directory (parent dir structure)
        # Preserve parent directory name for organization
        parent_name = src_path.parent.name
        dest_parent = lmstudio_dir / parent_name
        dest_file = dest_parent / src_path.name

        if dest_file.exists():
            if verbose:
                print(f"  ⏭️  Already exists: {dest_file.name}")
            continue

        print(f"🔗 Link: {src_path.name} → LM Studio/{parent_name}/")

        if not apply:
            linked_count += 1
            continue

        # Create parent directory
        dest_parent.mkdir(parents=True, exist_ok=True)

        # Try to create symlink
        try:
            os.symlink(str(src_path), str(dest_file), target_is_directory=False)
            linked_count += 1
            if verbose:
                print(f"  ✅ Linked: {dest_file}")
        except (OSError, NotImplementedError):
            # Fallback to PowerShell junction on Windows
            if sys.platform.startswith("win"):
                cmd = [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"New-Item -ItemType SymbolicLink -Path '{dest_file}' -Target '{src_path}'",
                ]
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    linked_count += 1
                    if verbose:
                        print(f"  ✅ Linked (PowerShell): {dest_file}")
                except subprocess.CalledProcessError as e:
                    print(f"  ❌ Failed to link: {e}")

    return linked_count


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Discover and sync local LLM models")
    ap.add_argument("--discover", action="store_true", help="Discover .gguf files in search paths")
    ap.add_argument("--query-apis", action="store_true", help="Query Ollama and LM Studio APIs")
    ap.add_argument("--sync", action="store_true", help="Sync models to LM Studio")
    ap.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    ap.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama API base URL (default: http://localhost:11434)",
    )
    ap.add_argument(
        "--lmstudio-url",
        default=resolve_lmstudio_base_url(),
        help=f"LM Studio API base URL (default: {resolve_lmstudio_base_url()})",
    )
    args = ap.parse_args(argv)

    # Load configuration
    config = load_model_paths_config()
    search_dirs = [expand_path(p) for p in config.get("search_dirs", [])]
    lmstudio_dir = expand_path(config.get("lmstudio_models_dir", "${USERPROFILE}\\.lmstudio\\models"))

    # Initialize registry
    registry = ModelRegistry(repo_root / "state" / "registry.json")

    print("\n📊 MODEL DISCOVERY & SYNC")
    print("=" * 60)

    all_models = []

    # Phase 1: Discover local files
    if args.discover:
        print("\n🔍 DISCOVERY PHASE")
        print(f"Search directories: {len(search_dirs)}")
        for d in search_dirs:
            print(f"  - {d}")

        discovered = discover_gguf_files(search_dirs, args.verbose)
        print(f"\n✅ Discovered {len(discovered)} GGUF files locally")

        # Register models
        if args.apply:
            for model in discovered:
                try:
                    # Check if already registered
                    existing = registry.find(model["path"])
                    if not existing:
                        registry.register_model(model, apply=True)
                        if args.verbose:
                            print(f"  📝 Registered: {model['name']}")
                except ValueError as e:
                    print(f"  ⚠️  Validation error for {model['name']}: {e}")

        all_models.extend(discovered)

    # Phase 2: Query APIs
    if args.query_apis:
        print("\n🌐 API QUERY PHASE")
        ollama_models = query_ollama_api(args.ollama_url)
        lmstudio_models = query_lmstudio_api(args.lmstudio_url)

        all_models.extend(ollama_models)
        all_models.extend(lmstudio_models)

    # Phase 3: Sync to LM Studio
    if args.sync and args.discover:
        print("\n🔗 SYNC PHASE")
        print(f"Target: {lmstudio_dir}")
        linked_count = sync_to_lmstudio(
            [m for m in all_models if m.get("format") == "gguf"],
            lmstudio_dir,
            apply=args.apply,
            verbose=args.verbose,
        )
        action = "Would link" if not args.apply else "Linked"
        print(f"\n✅ {action} {linked_count} models to LM Studio")

    # Summary
    print("\n📋 SUMMARY")
    print("=" * 60)
    print(f"Total models found: {len(all_models)}")
    print(f"  Local GGUF: {len([m for m in all_models if m.get('format') == 'gguf'])}")
    print(f"  Ollama API: {len([m for m in all_models if m.get('source') == 'ollama_api'])}")
    print(f"  LM Studio API: {len([m for m in all_models if m.get('source') == 'lmstudio_api'])}")

    registry_count = len(registry.list_models())
    print(f"\nRegistry: {registry_count} models registered")

    if not args.apply:
        print("\n💡 This was a DRY-RUN. Use --apply to make changes.")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
try:  # Python 3.10 compatibility
    from datetime import UTC  # type: ignore
except ImportError:  # pragma: no cover
    UTC = UTC
