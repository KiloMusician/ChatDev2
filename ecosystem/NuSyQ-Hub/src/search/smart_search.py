"""Smart Search API - Fast, Zero-Token Search for Agents.

Provides instant search capabilities using precomputed indices and intelligent
caching. The Culture Ship way: Don't search, already know.

[OmniTag: smart_search, zero_token, culture_ship, agent_api, performance]
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import logging
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, TextIO

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""

    file_path: str
    relevance: float = 1.0
    line: int | None = None
    snippet: str | None = None
    metadata: dict[str, Any] | None = None


class OutputFormat(str, Enum):
    """Output formats for human/agent/pipeline consumers."""

    PRETTY = "pretty"
    AGENT = "agent"
    JSONL = "jsonl"


class SmartSearch:
    """Smart Search API for agents.

    Provides fast, zero-token search using precomputed indices.
    No grep timeouts, no token costs.
    """

    def __init__(self, repo_root: Path | None = None):
        """Initialize Smart Search.

        Args:
            repo_root: Repository root. Auto-detected if None.
        """
        if repo_root is None:
            # Find repo root
            current = Path.cwd()
            while current != current.parent:
                if (current / ".git").exists():
                    repo_root = current
                    break
                current = current.parent
            else:
                repo_root = Path.cwd()

        self.repo_root = repo_root
        self.index_dir = repo_root / "state" / "search_index"

        # Lazy load indices (only when needed)
        self._file_metadata: dict[str, Any] | None = None
        self._keyword_index: dict[str, list[str]] | None = None
        self._find_files_cache: dict[str, list[str]] = {}
        self._search_keyword_cache: dict[tuple[str, bool], list[SearchResult]] = {}

    @property
    def file_metadata(self) -> dict[str, Any]:
        """Get file metadata index (lazy loaded).

        Returns:
            File metadata dictionary
        """
        if self._file_metadata is None:
            self._file_metadata = self._load_file_metadata()
        return self._file_metadata

    @property
    def keyword_index(self) -> dict[str, list[str]]:
        """Get keyword index (lazy loaded).

        Returns:
            Keyword inverted index
        """
        if self._keyword_index is None:
            self._keyword_index = self._load_keyword_index()
        return self._keyword_index

    def _load_file_metadata(self) -> dict[str, Any]:
        """Load file metadata index from disk.

        Returns:
            File metadata dictionary
        """
        metadata_path = self.index_dir / "file_metadata.json"
        if not metadata_path.exists():
            logger.warning("⚠️  No search index found. Run index builder first.")
            return {}

        try:
            data = json.loads(metadata_path.read_text())
            logger.info(f"✅ Loaded file metadata: {data.get('total_files', 0)} files")
            index_obj = data.get("index", {})
            return index_obj if isinstance(index_obj, dict) else {}
        except Exception as e:
            logger.error(f"❌ Failed to load file metadata: {e}")
            return {}

    def _load_keyword_index(self) -> dict[str, list[str]]:
        """Load keyword index from disk.

        Returns:
            Keyword inverted index
        """
        keyword_path = self.index_dir / "keyword_index.json"
        if not keyword_path.exists():
            logger.warning("⚠️  No keyword index found. Run index builder first.")
            return {}

        try:
            data = json.loads(keyword_path.read_text())
            logger.info(f"✅ Loaded keyword index: {data.get('total_keywords', 0)} keywords")
            index_obj = data.get("index", {})
            return index_obj if isinstance(index_obj, dict) else {}
        except Exception as e:
            logger.error(f"❌ Failed to load keyword index: {e}")
            return {}

    def find_files(self, pattern: str) -> list[str]:
        """Find files matching pattern (glob-style).

        Args:
            pattern: Glob pattern (e.g., "*culture_ship*", "*.py")

        Returns:
            List of matching file paths

        Example:
            >>> search = SmartSearch()
            >>> files = search.find_files("*orchestrator*.py")
            >>> print(files[:3])
            ['src/orchestration/unified_ai_orchestrator.py', ...]
        """
        if pattern in self._find_files_cache:
            return self._find_files_cache[pattern]

        all_files = list(self.file_metadata.keys())

        # Match pattern
        matches = [f for f in all_files if fnmatch.fnmatch(f, pattern)]

        logger.debug(f"🔍 Pattern '{pattern}': {len(matches)} matches")
        sorted_matches = sorted(matches)
        self._find_files_cache[pattern] = sorted_matches
        return sorted_matches

    def search_keyword(
        self, keyword: str, limit: int = 100, case_sensitive: bool = False
    ) -> list[SearchResult]:
        """Search for keyword in indexed files.

        Args:
            keyword: Keyword to search for
            limit: Maximum results to return
            case_sensitive: Whether search is case-sensitive

        Returns:
            List of SearchResult objects

        Example:
            >>> search = SmartSearch()
            >>> results = search.search_keyword("culture_ship", limit=10)
            >>> print(results[0].file_path)
            'src/orchestration/culture_ship_strategic_advisor.py'
        """
        cache_key = (keyword if case_sensitive else keyword.lower(), case_sensitive)
        if cache_key in self._search_keyword_cache:
            cached = self._search_keyword_cache[cache_key]
            return cached[:limit]

        normalized_keyword = keyword if case_sensitive else keyword.lower()

        # Check keyword index
        if normalized_keyword in self.keyword_index:
            file_paths = self.keyword_index[normalized_keyword]
        else:
            # Fallback: partial match
            file_paths = []
            for kw, paths in self.keyword_index.items():
                if normalized_keyword in kw:
                    file_paths.extend(paths)
            file_paths = list(set(file_paths))  # Remove duplicates

        # Create SearchResult objects
        results = []
        for file_path in file_paths[:limit]:
            metadata = self.file_metadata.get(file_path, {})
            result = SearchResult(
                file_path=file_path,
                relevance=1.0 if keyword in self.keyword_index else 0.5,
                metadata=metadata,
            )
            results.append(result)

        logger.debug(f"🔍 Keyword '{normalized_keyword}': {len(results)} results")
        self._search_keyword_cache[cache_key] = results
        return results[:limit]

    def search_multi_keyword(
        self, keywords: list[str], operator: str = "AND", limit: int = 100
    ) -> list[SearchResult]:
        """Search for multiple keywords.

        Args:
            keywords: List of keywords to search
            operator: "AND" (all keywords) or "OR" (any keyword)
            limit: Maximum results

        Returns:
            List of SearchResult objects

        Example:
            >>> search = SmartSearch()
            >>> results = search.search_multi_keyword(
            ...     ["culture", "ship"], operator="AND"
            ... )
        """
        if not keywords:
            return []

        # Get results for each keyword
        keyword_results = [
            {r.file_path for r in self.search_keyword(kw, limit=len(self.file_metadata))}
            for kw in keywords
        ]

        # Combine based on operator
        if operator == "AND":
            # Intersection (all keywords must match)
            combined = set.intersection(*keyword_results) if keyword_results else set()
        else:  # OR
            # Union (any keyword matches)
            combined = set.union(*keyword_results) if keyword_results else set()

        # Create SearchResult objects
        results = []
        for file_path in list(combined)[:limit]:
            metadata = self.file_metadata.get(file_path, {})
            # Calculate relevance based on how many keywords matched
            matches = sum(1 for kr in keyword_results if file_path in kr)
            relevance = matches / len(keywords)

            result = SearchResult(file_path=file_path, relevance=relevance, metadata=metadata)
            results.append(result)

        # Sort by relevance
        results.sort(key=lambda r: r.relevance, reverse=True)

        logger.debug(f"🔍 Multi-keyword {operator}: {len(results)} results")
        return results

    def search_by_type(
        self, file_type: str, keyword: str | None = None, limit: int = 100
    ) -> list[SearchResult]:
        """Search files by type."""
        results = []

        for file_path, metadata in self.file_metadata.items():
            if metadata.get("file_type") != file_type:
                continue

            # Optional keyword filter
            if keyword and keyword.lower() not in metadata.get("keywords", []):
                continue

            result = SearchResult(file_path=file_path, metadata=metadata)
            results.append(result)

            if len(results) >= limit:
                break

        logger.debug(f"🔍 Type '{file_type}': {len(results)} results")
        return results

    def search_by_class(self, class_name: str, exact: bool = True) -> list[SearchResult]:
        """Search for files containing a class."""
        results = []

        for file_path, metadata in self.file_metadata.items():
            classes = metadata.get("classes", [])

            if exact:
                if class_name in classes:
                    results.append(SearchResult(file_path=file_path, metadata=metadata))
            else:
                for cls in classes:
                    if class_name.lower() in cls.lower():
                        results.append(SearchResult(file_path=file_path, metadata=metadata))
                        break

        logger.debug(f"🔍 Class '{class_name}': {len(results)} results")
        return results

    def search_by_function(self, function_name: str, exact: bool = True) -> list[SearchResult]:
        """Search for files containing a function."""
        results = []

        for file_path, metadata in self.file_metadata.items():
            functions = metadata.get("functions", [])

            if exact:
                if function_name in functions:
                    results.append(SearchResult(file_path=file_path, metadata=metadata))
            else:
                for func in functions:
                    if function_name.lower() in func.lower():
                        results.append(SearchResult(file_path=file_path, metadata=metadata))
                        break

        logger.debug(f"🔍 Function '{function_name}': {len(results)} results")
        return results

    def search_hacking_quests(
        self,
        query: str,
        tier: int | None = None,
        difficulty: int | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search hacking quest templates by name, skills, or tags.

        Args:
            query: Search query (quest name, skill, tag)
            tier: Filter by Rosetta tier (1-5)
            difficulty: Filter by difficulty (1-5)
            limit: Maximum results

        Returns:
            List of SearchResult objects with quest metadata
        """
        try:
            from src.games.hacking_quests import HACKING_QUEST_TEMPLATES
        except ImportError:
            logger.warning("⚠️  Hacking quests not available")
            return []

        all_quests = list(HACKING_QUEST_TEMPLATES.values())

        # Filter by tier if specified
        if tier is not None:
            all_quests = [q for q in all_quests if f"tier-{tier}" in q.narrative_tags]

        # Filter by difficulty if specified
        if difficulty is not None:
            all_quests = [q for q in all_quests if q.difficulty == difficulty]

        # Search by query in title, description, skills, tags
        query_lower = query.lower()
        results = []

        for quest in all_quests:
            relevance = 0.0

            # Title match (highest relevance)
            if query_lower in quest.title.lower():
                relevance = 1.0
            # Description match
            elif query_lower in quest.description.lower():
                relevance = 0.85
            # Skill match
            elif any(query_lower in skill.lower() for skill in quest.required_skills):
                relevance = 0.8
            # Narrative tag/objective match
            elif any(query_lower in tag.lower() for tag in quest.narrative_tags) or any(
                query_lower in obj.lower() for obj in quest.objectives
            ):
                relevance = 0.7
            # Component/target match
            elif query_lower in quest.target_component.lower():
                relevance = 0.65

            if relevance > 0:
                quest_tier = next(
                    (int(t.split("-")[1]) for t in quest.narrative_tags if t.startswith("tier-")),
                    None,
                )
                result = SearchResult(
                    file_path=f"quest://{quest.id}",
                    line=None,
                    relevance=relevance,
                    snippet=quest.title,
                    metadata={
                        "id": quest.id,
                        "title": quest.title,
                        "target": quest.target_component,
                        "difficulty": quest.difficulty,
                        "xp_reward": quest.xp_reward,
                        "required_skills": quest.required_skills,
                        "tags": quest.narrative_tags,
                        "time_limit": quest.time_limit_minutes,
                        "tier": quest_tier,
                    },
                )
                results.append(result)

        # Sort by relevance
        results.sort(key=lambda x: x.relevance, reverse=True)
        logger.debug(f"🔍 Quest search '{query}': {len(results)} results")
        return results[:limit]

    def get_index_stats(self) -> dict[str, Any]:
        """Get statistics about the current index."""
        cache_size = 0
        if hasattr(self.find_files, "cache_info"):
            try:
                cache_size = self.find_files.cache_info().currsize
            except Exception:
                cache_size = 0

        stats = {
            "total_files": len(self.file_metadata),
            "total_keywords": len(self.keyword_index),
            "index_location": str(self.index_dir),
            "cache_size": cache_size,
        }

        # Add staleness info
        health = self.get_index_health()
        stats.update(health)
        return stats

    def get_index_health(self) -> dict[str, Any]:
        """Check health and staleness of the search index.

        Returns:
            Health status with age, staleness warning, and rebuild suggestion.

        Example:
            >>> search = SmartSearch()
            >>> health = search.get_index_health()
            >>> if health["is_stale"]:
            ...     print("Run: python -m src.search.index_builder")
        """
        import os
        from datetime import datetime

        metadata_path = self.index_dir / "file_metadata.json"

        if not metadata_path.exists():
            return {
                "status": "missing",
                "is_stale": True,
                "age_hours": -1,
                "message": "No search index found. Run: python -m src.search.index_builder",
            }

        try:
            # Get file modification time as proxy for index age
            mtime = os.path.getmtime(metadata_path)
            age_hours = (datetime.now().timestamp() - mtime) / 3600

            # Load metadata to check indexed_at if available
            data = self._load_file_metadata()
            total_files = len(data)

            # Check keyword index
            kw_data = self._load_keyword_index()
            total_keywords = len(kw_data)

            # Determine staleness thresholds
            # < 12 hours: healthy
            # 12-24 hours: aging
            # 24-48 hours: stale
            # > 48 hours: very stale
            if age_hours < 12:
                status = "healthy"
                is_stale = False
            elif age_hours < 24:
                status = "aging"
                is_stale = False
            elif age_hours < 48:
                status = "stale"
                is_stale = True
            else:
                status = "very_stale"
                is_stale = True

            return {
                "status": status,
                "is_stale": is_stale,
                "age_hours": round(age_hours, 1),
                "total_files": total_files,
                "total_keywords": total_keywords,
                "message": (
                    f"Index is {age_hours:.1f}h old. "
                    + ("Consider rebuilding." if is_stale else "Healthy.")
                ),
                "rebuild_command": "python -m src.search.index_builder" if is_stale else None,
            }
        except (OSError, ValueError, KeyError) as e:
            return {
                "status": "error",
                "is_stale": True,
                "age_hours": -1,
                "message": f"Failed to check index health: {e}",
            }

    def warn_if_stale(self) -> bool:
        """Log a warning if the index is stale. Returns True if stale.

        This method is called automatically during searches to help agents
        know when they should rebuild the index for better results.
        """
        health = self.get_index_health()
        if health.get("is_stale"):
            logger.warning(
                "⚠️  Search index is %s (%.1fh old). %s",
                health.get("status", "stale"),
                health.get("age_hours", -1),
                health.get("rebuild_command", ""),
            )
            return True
        return False


def _result_to_dict(result: SearchResult) -> dict[str, Any]:
    data: dict[str, Any] = {
        "record": "result",
        "file": result.file_path,
        "relevance": result.relevance,
    }
    if result.line is not None:
        data["line"] = result.line
    if result.snippet:
        data["snippet"] = result.snippet
    if result.metadata:
        data["metadata"] = result.metadata
    return data


def _render_jsonl(results: Iterable[SearchResult], out: TextIO) -> None:
    for res in results:
        out.write(json.dumps(_result_to_dict(res), ensure_ascii=False) + "\n")


def _render_agent(results: Iterable[SearchResult], out: TextIO) -> None:
    for res in results:
        data = _result_to_dict(res)
        fields = [f"{k}={data[k]}" for k in data]
        out.write("\t".join(fields) + "\n")


def _render_pretty(results: Iterable[SearchResult], out: TextIO) -> None:
    for res in results:
        out.write(f"{res.file_path}\n")
        out.write(f"  relevance: {res.relevance:.2f}\n")
        if res.line is not None:
            out.write(f"  line: {res.line}\n")
        if res.snippet:
            out.write(f"  snippet: {res.snippet}\n")
        if res.metadata:
            out.write(f"  metadata: {json.dumps(res.metadata)}\n")
        out.write("\n")


def render_results(results: Iterable[SearchResult], fmt: OutputFormat, out: TextIO) -> None:
    if fmt == OutputFormat.JSONL:
        _render_jsonl(results, out)
    elif fmt == OutputFormat.AGENT:
        _render_agent(results, out)
    else:
        _render_pretty(results, out)


def _format_argument(parser: Any) -> None:
    parser.add_argument(
        "--format",
        choices=[fmt.value for fmt in OutputFormat],
        default=OutputFormat.PRETTY.value,
        help="Output format: pretty (default), agent, jsonl",
    )


def build_parser() -> Any:
    parser = argparse.ArgumentParser(prog="smart_search")
    sub = parser.add_subparsers(dest="command", required=True)

    find_cmd = sub.add_parser("find", help="Glob search over indexed files")
    _format_argument(find_cmd)
    find_cmd.add_argument("pattern", type=str)
    find_cmd.add_argument("--limit", type=int, default=100)

    kw_cmd = sub.add_parser("keyword", help="Search by keyword")
    _format_argument(kw_cmd)
    kw_cmd.add_argument("keyword", type=str)
    kw_cmd.add_argument("--limit", type=int, default=100)
    kw_cmd.add_argument("--case-sensitive", action="store_true")

    multi_cmd = sub.add_parser("multi", help="Search by multiple keywords")
    _format_argument(multi_cmd)
    multi_cmd.add_argument("keywords", nargs="+", type=str)
    multi_cmd.add_argument("--operator", choices=["AND", "OR"], default="AND")
    multi_cmd.add_argument("--limit", type=int, default=100)

    type_cmd = sub.add_parser("type", help="Search by file type")
    _format_argument(type_cmd)
    type_cmd.add_argument("file_type", type=str)
    type_cmd.add_argument("--keyword", type=str, default=None)
    type_cmd.add_argument("--limit", type=int, default=100)

    return parser


def _run_find(search: SmartSearch, args: Any) -> list[SearchResult]:
    files = search.find_files(args.pattern)
    limited = files[: args.limit] if args.limit else files
    return [SearchResult(file_path=f, relevance=1.0) for f in limited]


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    fmt = OutputFormat(args.format)

    search = SmartSearch()

    if args.command == "find":
        results = _run_find(search, args)
    elif args.command == "keyword":
        results = search.search_keyword(
            args.keyword, limit=args.limit, case_sensitive=args.case_sensitive
        )
    elif args.command == "multi":
        results = search.search_multi_keyword(
            args.keywords, operator=args.operator, limit=args.limit
        )
    elif args.command == "type":
        results = search.search_by_type(args.file_type, keyword=args.keyword, limit=args.limit)
    else:
        parser.error(f"Unknown command: {args.command}")
        return 1

    render_results(results, fmt, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
