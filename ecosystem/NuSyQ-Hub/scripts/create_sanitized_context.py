#!/usr/bin/env python3
"""Create a sanitized Docker build context excluding problematic or sensitive paths.

This script works around the Windows ACL denial on `config/.secure` by:
  * Skipping any directory named `.secure` during traversal (even nested)
  * Copying only necessary project artifacts for building the NuSyQ-Hub image
  * Providing a manifest of copied files for audit transparency

Resulting context path: `.sanitized_build_context`

Idempotent: existing directory is removed first.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTEXT_DIR = PROJECT_ROOT / ".sanitized_build_context"
MANIFEST_FILE = PROJECT_ROOT / "sanitized_context_manifest.json"

# Directories we intentionally include (if they exist)
INCLUDE_DIRS = [
    "src",
    "deploy",
    "web",  # optional web assets
]

# Individual files to include from root
INCLUDE_FILES = [
    "Dockerfile",
    "Dockerfile.prod",
    "Dockerfile.dev",
    "requirements.txt",
    "pyproject.toml",
    "README.md",
]

# Always include config (except .secure) because runtime may read templates or settings
CONFIG_DIR_NAME = "config"

SKIP_NAMES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "tests",  # not required to build runtime image
    "docs",  # bulky documentation
    "Reports",
    "Logs",
    "node_modules",
    "ChatDev",
}


def is_secure_dir(path: Path) -> bool:
    return path.name == ".secure" or (".secure" in path.parts)


def safe_copy_file(src: Path, dst: Path, manifest: list[dict]):
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        manifest.append(
            {
                "type": "file",
                "src": str(src.relative_to(PROJECT_ROOT)),
                "dst": str(dst.relative_to(PROJECT_ROOT)),
            }
        )
    except PermissionError:
        manifest.append({"type": "skip", "reason": "permission-denied", "src": str(src)})
    except OSError as e:
        manifest.append({"type": "skip", "reason": f"os-error: {e}", "src": str(src)})


def copy_tree(src_dir: Path, dst_dir: Path, manifest: list[dict]):
    for root, dirs, files in os.walk(src_dir):
        root_path = Path(root)
        # Dynamically edit dirs list in-place to prune traversal
        pruned = []
        for d in list(dirs):
            full = root_path / d
            if d in SKIP_NAMES or is_secure_dir(full):
                manifest.append(
                    {
                        "type": "skip_dir",
                        "src": str(full.relative_to(PROJECT_ROOT)),
                        "reason": "secure-or-skipped",
                    }
                )
                continue
            pruned.append(d)
        dirs[:] = pruned  # modify in-place for os.walk

        for f in files:
            src_file = root_path / f
            if f.startswith(".") and f != ".env":  # skip hidden random metadata
                continue
            dst_file = CONTEXT_DIR / src_file.relative_to(PROJECT_ROOT)
            safe_copy_file(src_file, dst_file, manifest)


def main() -> int:
    if CONTEXT_DIR.exists():
        shutil.rmtree(CONTEXT_DIR)
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []

    # Copy selected root-level files
    for fname in INCLUDE_FILES:
        src = PROJECT_ROOT / fname
        if src.exists():
            safe_copy_file(src, CONTEXT_DIR / fname, manifest)
        else:
            manifest.append({"type": "missing", "src": fname})

    # Copy config (excluding .secure)
    config_root = PROJECT_ROOT / CONFIG_DIR_NAME
    if config_root.exists():
        for item in config_root.iterdir():
            if is_secure_dir(item):
                manifest.append(
                    {
                        "type": "skip_dir",
                        "src": str(item.relative_to(PROJECT_ROOT)),
                        "reason": "secure",
                    }
                )
                continue
            if item.is_dir():
                copy_tree(item, CONTEXT_DIR / CONFIG_DIR_NAME / item.name, manifest)
            else:
                safe_copy_file(item, CONTEXT_DIR / CONFIG_DIR_NAME / item.name, manifest)
    else:
        manifest.append({"type": "missing", "src": CONFIG_DIR_NAME})

    # Copy included directories
    for d in INCLUDE_DIRS:
        src_dir = PROJECT_ROOT / d
        if src_dir.exists():
            copy_tree(src_dir, CONTEXT_DIR / d, manifest)
        else:
            manifest.append({"type": "missing", "src": d})

    # Write manifest
    with MANIFEST_FILE.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "context_root": str(CONTEXT_DIR.relative_to(PROJECT_ROOT)),
                "entries": manifest,
                "summary": {
                    "files": sum(1 for m in manifest if m.get("type") == "file"),
                    "skipped": sum(1 for m in manifest if m.get("type", "").startswith("skip")),
                },
            },
            f,
            indent=2,
        )

    print(f"✅ Sanitized context ready: {CONTEXT_DIR}")
    print(f"🧾 Manifest: {MANIFEST_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
