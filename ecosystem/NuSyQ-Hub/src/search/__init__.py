"""Smart Search System - Culture Ship Powered Search for Large Ecosystems.

Provides fast, zero-token search capabilities using precomputed indices
and intelligent caching. Inspired by the Culture's precognitive Minds.

[OmniTag: smart_search, culture_ship, zero_token, performance, indexing]
"""

from __future__ import annotations

__all__ = ["IndexBuilder", "SearchResult", "SmartSearch"]


# Lazy imports to avoid circular dependencies
def __getattr__(name: str):
    if name == "SmartSearch":
        from src.search.smart_search import SmartSearch

        return SmartSearch
    elif name == "IndexBuilder":
        from src.search.index_builder import IndexBuilder

        return IndexBuilder
    elif name == "SearchResult":
        from src.search.smart_search import SearchResult

        return SearchResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
