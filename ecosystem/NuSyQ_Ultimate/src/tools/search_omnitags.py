"""
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.tools.search.omnitag                                     ║
║ TYPE: Python Script                                                     ║
║ STATUS: Production                                                      ║
║ VERSION: 1.0.1                                                          ║
║ TAGS: [tools, search, omnitag, automation, utility]                    ║
║ CONTEXT: Σ2 (Feature Layer)                                            ║
║ AGENTS: [ClaudeCode, AllAgents]                                        ║
║ DEPS: [pathlib, re, argparse]                                          ║
║ INTEGRATIONS: [ΞNuSyQ-Framework]                                        ║
║ CREATED: 2025-10-06                                                     ║
║ UPDATED: 2025-10-06                                                     ║
║ AUTHOR: Claude Code                                                     ║
║ STABILITY: High (Production Ready)                                      ║
╚══════════════════════════════════════════════════════════════════════════╝

OmniTag Search Utility
======================

Search files by OmniTag metadata fields.

Usage:
    python scripts/search_omnitags.py --tag orchestration
    python scripts/search_omnitags.py --context "Σ∞"
    python scripts/search_omnitags.py --agent ChatDev
    python scripts/search_omnitags.py --status Production
    python scripts/search_omnitags.py --type "Python Module"
    python scripts/search_omnitags.py --all  # Show all tagged files
"""

import argparse
import io
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# Force UTF-8 output on Windows — skip under pytest to avoid closing capture buffers
if sys.platform == "win32" and "pytest" not in sys.modules:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


@dataclass
class OmniTag:
    """Parsed OmniTag metadata"""

    file_id: str = ""
    type: str = ""
    status: str = ""
    version: str = ""
    tags: List[str] = field(default_factory=list)
    context: str = ""
    agents: List[str] = field(default_factory=list)
    deps: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)
    created: str = ""
    updated: str = ""
    author: str = ""
    stability: str = ""
    file_path: str = ""


def extract_omnitag(file_path: Path) -> Optional[OmniTag]:
    """Extract OmniTag metadata from a file"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"⚠️ Warning: Failed to read {file_path}: {e}")
        return None

    # Look for OmniTag block
    omnitag_pattern = r"║ FILE-ID: (.+?)║.*?║ TYPE: (.+?)║.*?║ STATUS: (.+?)║.*?║ VERSION: (.+?)║.*?║ TAGS: \[(.+?)\].*?║ CONTEXT: (.+?)║.*?║ AGENTS: \[(.+?)\].*?║ DEPS: \[(.+?)\].*?║ INTEGRATIONS: \[(.+?)\].*?║ CREATED: (.+?)║.*?║ UPDATED: (.+?)║.*?║ AUTHOR: (.+?)║.*?║ STABILITY: (.+?)║"

    match = re.search(omnitag_pattern, content, re.DOTALL)

    if not match:
        return None

    return OmniTag(
        file_id=match.group(1).strip(),
        type=match.group(2).strip(),
        status=match.group(3).strip(),
        version=match.group(4).strip(),
        tags=[t.strip() for t in match.group(5).split(",")],
        context=match.group(6).strip(),
        agents=[a.strip() for a in match.group(7).split(",")],
        deps=[d.strip() for d in match.group(8).split(",")],
        integrations=[i.strip() for i in match.group(9).split(",")],
        created=match.group(10).strip(),
        updated=match.group(11).strip(),
        author=match.group(12).strip(),
        stability=match.group(13).strip(),
        file_path=str(file_path),
    )


def search_files(root_dir: Path, pattern: str = "**/*") -> List[OmniTag]:
    """Search all files and extract OmniTags"""
    omnitags = []
    skip_dir_names = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".hypothesis",
        ".tox",
        ".eggs",
        "build",
        "dist",
        "ChatDev",
        "GODOT",
        "Jupyter",
        "Archive",
        "Logs",
        "Reports",
        "State",
        "AI_Hub",
        "claude_code",
        "nul",
    }
    skip_path_substrings = [
        "ChatDev/WareHouse",
        ".coverage",
    ]
    text_extensions = {
        ".md",
        ".py",
        ".ps1",
        ".psm1",
        ".txt",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".ini",
        ".cfg",
        ".rst",
        ".sh",
        ".bat",
    }

    def should_skip_path(path: Path) -> bool:
        path_str = str(path)
        if path.name in skip_dir_names:
            return True
        return any(token in path_str for token in skip_path_substrings)

    def iter_files(start_dir: Path):
        for dirpath, dirnames, filenames in os.walk(start_dir):
            dir_path = Path(dirpath)
            dirnames[:] = [d for d in dirnames if not should_skip_path(dir_path / d)]
            for filename in filenames:
                file_path = dir_path / filename
                if should_skip_path(file_path):
                    continue
                yield file_path

    if pattern != "**/*":
        for file_path in root_dir.glob(pattern):
            if not file_path.is_file():
                continue
            if should_skip_path(file_path):
                continue
            if text_extensions and file_path.suffix.lower() not in text_extensions:
                continue
            omnitag = extract_omnitag(file_path)
            if omnitag:
                omnitags.append(omnitag)
        return omnitags

    repo_allowlist = [
        "config",
        "docs",
        "examples",
        "ops",
        "scripts",
        "src",
        "tests",
    ]
    if (root_dir / "nusyq.manifest.yaml").exists():
        for entry in root_dir.iterdir():
            if not entry.is_file():
                continue
            if should_skip_path(entry):
                continue
            if text_extensions and entry.suffix.lower() not in text_extensions:
                continue
            omnitag = extract_omnitag(entry)
            if omnitag:
                omnitags.append(omnitag)

        for dirname in repo_allowlist:
            dir_path = root_dir / dirname
            if not dir_path.is_dir():
                continue
            for file_path in iter_files(dir_path):
                if text_extensions and file_path.suffix.lower() not in text_extensions:
                    continue
                omnitag = extract_omnitag(file_path)
                if omnitag:
                    omnitags.append(omnitag)
        return omnitags

    for file_path in iter_files(root_dir):
        if text_extensions and file_path.suffix.lower() not in text_extensions:
            continue
        omnitag = extract_omnitag(file_path)
        if omnitag:
            omnitags.append(omnitag)

    return omnitags


def search_omnitags(root_dir: Path, **filters) -> List[OmniTag]:
    """Search for OmniTags under root_dir and apply optional filters."""
    omnitags = search_files(root_dir)
    if filters:
        return filter_omnitags(omnitags, **filters)
    return omnitags


def filter_omnitags(omnitags: List[OmniTag], **filters) -> List[OmniTag]:
    """Filter OmniTags by criteria"""
    results = omnitags

    if filters.get("tag"):
        tag = filters["tag"].lower()
        results = [ot for ot in results if any(tag in t.lower() for t in (ot.tags or []))]

    if filters.get("context"):
        context = filters["context"]
        results = [ot for ot in results if context in ot.context]

    if filters.get("agent"):
        agent = filters["agent"]
        results = [ot for ot in results if any(agent in a for a in (ot.agents or []))]

    if filters.get("status"):
        status = filters["status"]
        results = [ot for ot in results if status.lower() in ot.status.lower()]

    if filters.get("type"):
        file_type = filters["type"]
        results = [ot for ot in results if file_type.lower() in ot.type.lower()]

    if filters.get("stability"):
        stability = filters["stability"]
        results = [ot for ot in results if stability.lower() in ot.stability.lower()]

    return results


def print_results(omnitags: List[OmniTag], verbose: bool = False):
    """Print search results"""
    if not omnitags:
        print("No files found matching criteria.")
        return

    print(f"\n{'=' * 80}")
    print(f"Found {len(omnitags)} file(s) with OmniTags")
    print(f"{'=' * 80}\n")

    for ot in sorted(omnitags, key=lambda x: x.context):
        if verbose:
            print(f"[FILE] {ot.file_path}")
            print(f"   FILE-ID: {ot.file_id}")
            print(f"   TYPE: {ot.type}")
            print(f"   STATUS: {ot.status}")
            print(f"   VERSION: {ot.version}")
            print(f"   TAGS: {', '.join(ot.tags or [])}")
            print(f"   CONTEXT: {ot.context}")
            print(f"   AGENTS: {', '.join(ot.agents or [])}")
            print(f"   STABILITY: {ot.stability}")
            print(f"   UPDATED: {ot.updated}")
            print()
        else:
            # Compact format (ASCII-safe for Windows)
            context_marker = {
                "Σ∞": "[GLOBAL]",
                "Σ0": "[SYSTEM]",
                "Σ1": "[COMPON]",
                "Σ2": "[FEAT  ]",
                "Σ3": "[DETAIL]",
                "Σ∆": "[META  ]",
            }
            marker = context_marker.get(ot.context.split()[0], "[FILE  ]")
            print(f"{marker} {ot.context.ljust(10)} | {ot.file_id.ljust(45)} | {ot.file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Search files by OmniTag metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find all orchestration-related files
  python scripts/search_omnitags.py --tag orchestration

  # Find all global orchestration layer files (Σ∞)
  python scripts/search_omnitags.py --context "Σ∞"

  # Find all files compatible with ChatDev
  python scripts/search_omnitags.py --agent ChatDev

  # Find all production-ready files
  python scripts/search_omnitags.py --status Production

  # Find all Python modules
  python scripts/search_omnitags.py --type "Python Module"

  # Show all tagged files
  python scripts/search_omnitags.py --all

  # Verbose output
  python scripts/search_omnitags.py --tag ai-agent -v
        """,
    )

    parser.add_argument("--tag", help="Search by tag")
    parser.add_argument("--context", help="Search by context level (Σ∞, Σ0, Σ1, Σ2, Σ3, Σ∆)")
    parser.add_argument("--agent", help="Search by agent compatibility")
    parser.add_argument(
        "--status", help="Search by status (Draft, Review, Active, Production, etc.)"
    )
    parser.add_argument("--type", help="Search by file type")
    parser.add_argument("--stability", help="Search by stability level")
    parser.add_argument("--all", action="store_true", help="Show all tagged files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory to search (default: current directory)",
    )

    args = parser.parse_args()

    # Get root directory
    root_dir = Path(args.root).resolve()

    # Search for all OmniTags
    print(f"Searching for OmniTags in: {root_dir}")
    omnitags = search_files(root_dir)

    # Apply filters
    filters = {}
    if args.tag:
        filters["tag"] = args.tag
    if args.context:
        filters["context"] = args.context
    if args.agent:
        filters["agent"] = args.agent
    if args.status:
        filters["status"] = args.status
    if args.type:
        filters["type"] = args.type
    if args.stability:
        filters["stability"] = args.stability

    if filters:
        omnitags = filter_omnitags(omnitags, **filters)
    elif not args.all:
        # No filters and not --all, show usage
        parser.print_help()
        return

    # Print results
    print_results(omnitags, verbose=args.verbose)

    # Summary
    if omnitags:
        print(f"\n{'=' * 80}")
        print("Summary:")
        print(f"  Total files: {len(omnitags)}")

        # Count by context
        contexts = {}
        for ot in omnitags:
            ctx = ot.context.split()[0]
            contexts[ctx] = contexts.get(ctx, 0) + 1

        print("\n  By Context:")
        for ctx, count in sorted(contexts.items()):
            print(f"    {ctx}: {count}")

        # Count by status
        statuses = {}
        for ot in omnitags:
            statuses[ot.status] = statuses.get(ot.status, 0) + 1

        print("\n  By Status:")
        for status, count in sorted(statuses.items()):
            print(f"    {status}: {count}")

        print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
