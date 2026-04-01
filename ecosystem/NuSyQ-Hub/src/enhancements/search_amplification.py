"""Search amplification using OmniTag, MegaTag and SmartSearch index.

OmniTag: {
    "purpose": "search_amplification",
    "tags": ["Search", "OmniTag", "MegaTag", "SmartSearch"],
    "category": "enhancements",
    "evolution_stage": "v2.0"
}
"""

from __future__ import annotations

from typing import Any


class SearchAmplification:
    """Enhances search capabilities using accumulated context and integrates OmniTag and MegaTag."""

    def __init__(self) -> None:
        """Initialize SearchAmplification with real OmniTagSystem and MegaTagProcessor."""
        from src.core.megatag_processor import MegaTagProcessor
        from src.tagging.omnitag_system import OmniTagSystem

        self.omni_tag_system = OmniTagSystem()
        self.mega_tag_processor = MegaTagProcessor()

    def amplify_search(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        """Enhance the search query with contextual information and tags.

        Args:
            query: The search query string.
            context: Contextual information for the search.

        Returns:
            dict with ``query``, ``results``, and ``tags`` keys.

        """
        enhanced_query: str = self._apply_omni_tags(query)
        search_results: list[str] = self._perform_search(enhanced_query, context)
        tags = self.mega_tag_processor.extract_semantics(
            [r.split(":")[0] if ":" in r else r for r in search_results]
        )
        return {
            "query": enhanced_query,
            "results": search_results,
            "tags": [t.get("tag", "") for t in tags if t.get("tag")],
        }

    def _apply_omni_tags(self, query: str) -> str:
        """Integrate OmniTag semantic tags into the search query for improved context."""
        raw_tags = self.omni_tag_system.create_tags(query)
        tag_values = [str(t.get("value", "")) for t in raw_tags if t.get("value")]
        suffix = " ".join(tag_values)
        return f"{query} {suffix}".strip() if suffix else query

    def _perform_search(self, query: str, context: dict[str, Any]) -> list[str]:
        """Perform search using SmartSearch keyword index.

        Falls back to a simple string representation when the index is unavailable.
        """
        try:
            from src.search.smart_search import SmartSearch

            ss = SmartSearch()
            # Extract first meaningful word from query for keyword lookup
            keywords = [w for w in query.split() if len(w) > 3 and w.isalpha()]
            if not keywords:
                keywords = query.split()[:1]
            results = ss.search_keyword(keywords[0], max_results=10) if keywords else []
            file_paths = [r.file_path for r in results]

            # Augment with context-based filtering if scope provided
            scope = context.get("scope") or context.get("path")
            if scope:
                file_paths = [p for p in file_paths if str(scope) in p]

            return file_paths if file_paths else [f"No index results for '{query}'"]
        except Exception:
            return [f"Result for '{query}' (context: {list(context.keys())})"]
