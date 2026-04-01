"""Tool discovery helper for the "Three Before New" rule.

Usage:
    python scripts/find_existing_tool.py --capability "error reporting"

The script scores existing files that may satisfy a requested capability so
agents can extend/combine/modernize instead of creating duplicates.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Directories to search by default (relative to repo root)
SEARCH_DIRS = [
    Path("scripts"),
    Path("src"),
    Path("docs"),
    Path("config"),
    Path("deploy"),
    Path("web"),
]
# Extensions worth scanning (balanced for speed)
SCAN_EXTENSIONS = {".py", ".md", ".ps1", ".sh", ".json", ".yaml", ".yml"}
# Directories to skip
SKIP_PARTS = {
    "venv",
    ".venv",
    ".git",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    "htmlcov",
    "coverage_batches",
    "archive",
    "agent_output",
    "tmp",
}
SKIP_PREFIXES = ("tmpclaude-", "tmpcodex-", "quick_system_analysis_", "system_health_assessment_")
MAX_FILES_DEFAULT = 1500


@dataclass
class ToolHit:
    path: Path
    score: float
    reasons: list[str]
    excerpt: str | None


class OutputFormat(str, Enum):
    HUMAN = "human"
    AGENT = "agent"
    JSON = "json"


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^A-Za-z0-9]+", text.lower()) if t]


def _skip_path(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_PARTS:
            return True
        if any(part.startswith(prefix) for prefix in SKIP_PREFIXES):
            return True
    return False


def _skip_part(part: str) -> bool:
    return part in SKIP_PARTS or any(part.startswith(prefix) for prefix in SKIP_PREFIXES)


def iter_files(root: Path) -> Iterator[Path]:
    for search_dir in SEARCH_DIRS:
        base = root / search_dir
        if not base.exists():
            continue
        for current_root, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if not _skip_part(d)]
            root_path = Path(current_root)
            if _skip_path(root_path):
                continue
            for filename in filenames:
                if _skip_part(filename):
                    continue
                path = root_path / filename
                if path.suffix.lower() not in SCAN_EXTENSIONS:
                    continue
                yield path


def _score_name_and_path(path: Path, tokens: list[str]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    lower_name = path.name.lower()
    for tok in tokens:
        if tok in lower_name:
            score += 2.0
            reasons.append(f"filename contains '{tok}'")
    lower_segments = " ".join(path.parts).lower()
    for tok in tokens:
        if tok in lower_segments:
            score += 1.0
            reasons.append(f"path segment contains '{tok}'")
    return score, reasons


def _score_content(text: str, tokens: list[str]) -> tuple[float, list[str], str | None]:
    score = 0.0
    reasons: list[str] = []
    excerpt: str | None = None
    lowered = text.lower()
    hits = 0
    for tok in tokens:
        occurrences = lowered.count(tok)
        if occurrences:
            hits += occurrences
            reasons.append(f"content mentions '{tok}' {occurrences}x")
    if hits:
        score += min(3.0, 0.5 * hits)
        first_token = tokens[0] if tokens else ""
        first_index = lowered.find(first_token) if first_token else -1
        if first_index != -1:
            start = max(0, first_index - 80)
            end = min(len(text), first_index + 160)
            excerpt = text[start:end].strip().replace("\n", " ")
    return score, reasons, excerpt


def score_file(path: Path, tokens: list[str], max_bytes: int = 4000) -> ToolHit | None:
    name_score, name_reasons = _score_name_and_path(path, tokens)

    try:
        with path.open("rb") as handle:
            raw = handle.read(max_bytes)
        text = raw.decode("utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return None

    content_score, content_reasons, excerpt = _score_content(text, tokens)
    total_score = name_score + content_score
    reasons = name_reasons + content_reasons

    if total_score <= 0:
        return None
    return ToolHit(path=path, score=total_score, reasons=reasons, excerpt=excerpt)


def discover(root: Path, capability: str, max_results: int, max_files: int) -> list[ToolHit]:
    tokens = tokenize(capability)
    hits: list[ToolHit] = []
    scanned = 0
    for file_path in iter_files(root):
        scanned += 1
        if scanned > max_files:
            break
        hit = score_file(file_path, tokens)
        if hit:
            hits.append(hit)
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:max_results]


def print_human(hits: list[ToolHit], capability: str) -> None:
    print(f"Found {len(hits)} candidate tools for capability '{capability}':")
    for idx, hit in enumerate(hits, start=1):
        print(f"{idx}. {hit.path}  (score={hit.score:.1f})")
        if hit.reasons:
            print(f"   why: {', '.join(hit.reasons[:3])}")
        if hit.excerpt:
            print(f"   excerpt: {hit.excerpt[:200]}")
    print("\nBefore creating anything new, extend/modernize/merge one of the above or document why none fit.")


def print_agent(hits: list[ToolHit]) -> None:
    """Emit minimal, parseable lines: path|score|reasons|excerpt (no emoji, no padding)."""
    for hit in hits:
        reasons = ";".join(hit.reasons[:5])
        excerpt = (hit.excerpt or "").replace("\n", " ")
        fields = [
            "record=tool",
            f"path={hit.path}",
            f"score={hit.score:.2f}",
            f"reasons={reasons}",
        ]
        if excerpt:
            fields.append(f"excerpt={excerpt[:160]}")
        print("\t".join(fields))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capability", required=True, help="Capability you need (keywords)")
    parser.add_argument("--root", default=".", help="Repository root to search from")
    parser.add_argument("--max-results", type=int, default=12, help="Number of candidates to return")
    parser.add_argument(
        "--max-files",
        type=int,
        default=MAX_FILES_DEFAULT,
        help=f"Maximum files to scan before returning (default: {MAX_FILES_DEFAULT})",
    )
    parser.add_argument(
        "--format",
        choices=[fmt.value for fmt in OutputFormat],
        default=OutputFormat.HUMAN.value,
        help="Output format: human (default), agent (LLM-friendly), json",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human output (deprecated; use --format json)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    hits = discover(root, args.capability, args.max_results, args.max_files)

    fmt = OutputFormat.JSON if args.json else OutputFormat(args.format)

    if fmt == OutputFormat.JSON:
        print(
            json.dumps(
                [
                    {
                        "path": str(hit.path),
                        "score": hit.score,
                        "reasons": hit.reasons,
                        "excerpt": hit.excerpt,
                    }
                    for hit in hits
                ],
                indent=2,
            )
        )
    elif fmt == OutputFormat.AGENT:
        print_agent(hits)
    else:
        print_human(hits, args.capability)

    if not hits:
        print("No existing tools found. Document why and proceed carefully.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
