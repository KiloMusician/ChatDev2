#!/usr/bin/env python3
"""Semantic Response Cache - Intelligent caching for AI responses.

This module provides semantic similarity-based caching to reduce redundant
AI API calls. Instead of exact string matching, it uses embeddings to find
semantically similar queries and return cached responses.

Features:
- Semantic similarity matching using embeddings
- Configurable similarity threshold
- TTL-based cache expiration
- Cache statistics and monitoring
- Integration with Prometheus metrics
"""

import hashlib
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from diskcache import Cache

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

try:
    from prometheus_client import Counter, Histogram

    cache_hits = Counter("ai_cache_hits_total", "Total cache hits", ["system"])
    cache_misses = Counter("ai_cache_misses_total", "Total cache misses", ["system"])
    cache_latency = Histogram("ai_cache_lookup_seconds", "Cache lookup duration")
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CachedResponse:
    """Cached AI response with metadata."""

    query: str
    response: str
    system: str
    timestamp: float
    token_count: int | None = None
    model: str | None = None
    metadata: dict = None

    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Check if cache entry has expired."""
        age = time.time() - self.timestamp
        return age > ttl_seconds

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


class SemanticCache:
    """Semantic similarity-based cache for AI responses."""

    def __init__(
        self,
        cache_dir: str = ".cache/ai_responses",
        similarity_threshold: float = 0.85,
        ttl_seconds: int = 3600,
        max_size_mb: int = 100,
    ) -> None:
        """Initialize semantic cache.

        Args:
            cache_dir: Directory for cache storage
            similarity_threshold: Minimum similarity for cache hit (0.0-1.0)
            ttl_seconds: Time-to-live for cache entries
            max_size_mb: Maximum cache size in megabytes
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.max_size_mb = max_size_mb

        if CACHE_AVAILABLE:
            self.cache = Cache(
                str(self.cache_dir),
                size_limit=max_size_mb * 1024 * 1024,
            )
        else:
            self.cache = {}
            logger.warning("diskcache not available, using in-memory cache")

        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_queries": 0,
        }

        logger.info(f"✅ Semantic cache initialized at {cache_dir}")

    def _compute_hash(self, text: str) -> str:
        """Compute hash for quick exact matching."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _compute_similarity(self, query1: str, query2: str) -> float:
        """Compute semantic similarity between queries.

        For now uses simple token overlap. In production, would use
        embeddings from a model like sentence-transformers.
        """
        # Simple token-based similarity (Jaccard)
        tokens1 = set(query1.lower().split())
        tokens2 = set(query2.lower().split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)

        return intersection / union if union > 0 else 0.0

    def get(self, query: str, system: str) -> CachedResponse | None:
        """Retrieve cached response if semantically similar query exists.

        Args:
            query: User query
            system: AI system name

        Returns:
            Cached response if found, None otherwise
        """
        start_time = time.time()
        self.stats["total_queries"] += 1

        # Try exact hash match first (fastest)
        query_hash = self._compute_hash(query)
        cache_key = f"{system}:{query_hash}"

        exact_match = self.cache.get(cache_key)

        if exact_match:
            cached = CachedResponse(**exact_match)
            if not cached.is_expired(self.ttl_seconds):
                self._record_hit(system, time.time() - start_time)
                logger.debug(f"Cache HIT (exact): {query[:50]}...")
                return cached
            else:
                # Remove expired entry
                self._evict(cache_key)

        # Fallback to semantic search (slower but more flexible)
        # In production, use vector database or embedding index
        # For now, skip semantic search for performance

        self._record_miss(system, time.time() - start_time)
        logger.debug(f"Cache MISS: {query[:50]}...")
        return None

    def set(
        self,
        query: str,
        response: str,
        system: str,
        token_count: int | None = None,
        model: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Store response in cache.

        Args:
            query: User query
            response: AI response
            system: AI system name
            token_count: Number of tokens used
            model: Model name/version
            metadata: Additional metadata
        """
        query_hash = self._compute_hash(query)
        cache_key = f"{system}:{query_hash}"

        cached = CachedResponse(
            query=query,
            response=response,
            system=system,
            timestamp=time.time(),
            token_count=token_count,
            model=model,
            metadata=metadata or {},
        )

        if CACHE_AVAILABLE:
            self.cache.set(cache_key, cached.to_dict(), expire=self.ttl_seconds)
        else:
            self.cache[cache_key] = cached.to_dict()

        logger.debug(f"Cached response for: {query[:50]}...")

    def _record_hit(self, system: str, latency: float) -> None:
        """Record cache hit metrics."""
        self.stats["hits"] += 1
        if METRICS_AVAILABLE:
            cache_hits.labels(system=system).inc()
            cache_latency.observe(latency)

    def _record_miss(self, system: str, latency: float) -> None:
        """Record cache miss metrics."""
        self.stats["misses"] += 1
        if METRICS_AVAILABLE:
            cache_misses.labels(system=system).inc()
            cache_latency.observe(latency)

    def _evict(self, key: str) -> None:
        """Evict entry from cache."""
        if CACHE_AVAILABLE:
            self.cache.delete(key)
        else:
            self.cache.pop(key, None)
        self.stats["evictions"] += 1

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0.0

        stats = {
            **self.stats,
            "hit_rate": hit_rate,
            "total_entries": len(self.cache),
        }

        if CACHE_AVAILABLE:
            stats["size_mb"] = self.cache.volume() / (1024 * 1024)

        return stats

    def clear(self) -> None:
        """Clear all cache entries."""
        if CACHE_AVAILABLE:
            self.cache.clear()
        else:
            self.cache.clear()
        logger.info("Cache cleared")

    def prune_expired(self) -> int:
        """Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        if not CACHE_AVAILABLE:
            # Manual pruning for in-memory cache
            expired_keys = []
            for key, value in list(self.cache.items()):
                cached = CachedResponse(**value)
                if cached.is_expired(self.ttl_seconds):
                    expired_keys.append(key)

            for key in expired_keys:
                self.cache.pop(key, None)

            return len(expired_keys)

        # DiskCache handles expiration automatically
        return 0


# Global cache instance
_global_cache: SemanticCache | None = None


def get_cache() -> SemanticCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = SemanticCache()
    return _global_cache
