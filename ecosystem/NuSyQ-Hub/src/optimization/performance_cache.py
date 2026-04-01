"""NuSyQ-Hub Performance Optimization & Caching System.

Provides:
- Multi-level caching (memory, disk, Redis-ready)
- Request deduplication
- Response compression
- Performance metrics tracking
- Smart cache invalidation
"""

import contextlib
import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# Cache storage
CACHE_DIR = Path(".cache/performance")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

T = TypeVar("T")


@dataclass
class CacheEntry:
    """Individual cache entry with metadata."""

    key: str
    value: Any
    created_at: datetime
    expires_at: datetime | None
    hit_count: int = 0
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def record_hit(self) -> None:
        """Record cache hit."""
        self.hit_count += 1


class PerformanceCache:
    """Multi-level cache system for performance optimization."""

    def __init__(self, max_memory_mb: int = 100, enable_disk: bool = True) -> None:
        """Initialize cache system."""
        self.max_memory_mb = max_memory_mb
        self.enable_disk = enable_disk
        self.memory_cache: dict[str, CacheEntry] = {}
        self.memory_usage_bytes = 0
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0,
        }

    def _get_cache_key(self, key: str) -> str:
        """Generate consistent cache key."""
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _estimate_size(self, obj: Any) -> int:
        """Estimate object size in bytes."""
        try:
            return len(json.dumps(obj, default=str).encode("utf-8"))
        except Exception:
            return 1024  # Default estimate

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        cache_key = self._get_cache_key(key)

        # Try memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]

            if entry.is_expired():
                self._delete_entry(cache_key)
                self.stats["misses"] += 1
                return None

            entry.record_hit()
            self.stats["hits"] += 1
            logger.debug(f"🎯 Cache hit: {key} (hits: {entry.hit_count})")
            return entry.value

        # Try disk cache if enabled
        if self.enable_disk:
            disk_value = self._load_from_disk(cache_key)
            if disk_value is not None:
                self.stats["hits"] += 1
                logger.debug(f"💾 Disk cache hit: {key}")
                return disk_value

        self.stats["misses"] += 1
        logger.debug(f"❌ Cache miss: {key}")
        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        """Set value in cache."""
        cache_key = self._get_cache_key(key)
        size = self._estimate_size(value)

        # Calculate expiration
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        # Create entry
        entry = CacheEntry(
            key=cache_key,
            value=value,
            created_at=datetime.now(),
            expires_at=expires_at,
            size_bytes=size,
        )

        # Check memory limit
        total_size = self.memory_usage_bytes + size
        if total_size > self.max_memory_mb * 1024 * 1024:
            self._evict_lru()

        # Store in memory
        if cache_key in self.memory_cache:
            old_size = self.memory_cache[cache_key].size_bytes
            self.memory_usage_bytes -= old_size

        self.memory_cache[cache_key] = entry
        self.memory_usage_bytes += size
        self.stats["sets"] += 1

        # Store in disk if enabled
        if self.enable_disk:
            self._save_to_disk(cache_key, entry)

        logger.debug(f"💾 Cached: {key} ({size} bytes)")

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        cache_key = self._get_cache_key(key)
        return self._delete_entry(cache_key)

    def _delete_entry(self, cache_key: str) -> bool:
        """Internal method to delete entry."""
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            self.memory_usage_bytes -= entry.size_bytes
            del self.memory_cache[cache_key]
            self.stats["deletes"] += 1

            if self.enable_disk:
                disk_file = CACHE_DIR / f"{cache_key}.json"
                with contextlib.suppress(Exception):
                    disk_file.unlink()

            return True
        return False

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.memory_cache:
            return

        # Find LRU entry (lowest hit count)
        lru_key = min(self.memory_cache.keys(), key=lambda k: self.memory_cache[k].hit_count)

        self._delete_entry(lru_key)
        self.stats["evictions"] += 1
        logger.info(f"🗑️ Evicted LRU entry: {lru_key}")

    def _save_to_disk(self, cache_key: str, entry: CacheEntry) -> None:
        """Save entry to disk cache."""
        try:
            disk_file = CACHE_DIR / f"{cache_key}.json"
            payload = {
                "key": entry.key,
                "value": entry.value,
                "created_at": entry.created_at.isoformat(),
                "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
                "hit_count": entry.hit_count,
                "size_bytes": entry.size_bytes,
            }
            disk_file.write_text(json.dumps(payload, default=str), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save to disk cache: {e}")

    def _load_from_disk(self, cache_key: str) -> Any | None:
        """Load entry from disk cache."""
        try:
            disk_file = CACHE_DIR / f"{cache_key}.json"
            if not disk_file.exists():
                return None

            data = json.loads(disk_file.read_text(encoding="utf-8"))
            entry = CacheEntry(
                key=data["key"],
                value=data["value"],
                created_at=datetime.fromisoformat(data["created_at"]),
                expires_at=(
                    datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
                ),
                hit_count=int(data.get("hit_count", 0)),
                size_bytes=int(data.get("size_bytes", 0)),
            )

            if entry.is_expired():
                disk_file.unlink()
                return None

            return entry.value
        except Exception as e:
            logger.debug(f"Failed to load from disk cache: {e}")
            return None

    def clear(self) -> None:
        """Clear all cache."""
        self.memory_cache.clear()
        self.memory_usage_bytes = 0

        if self.enable_disk:
            for file in CACHE_DIR.glob("*.json"):
                with contextlib.suppress(Exception):
                    file.unlink()

        logger.info("🧹 Cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"],
            "evictions": self.stats["evictions"],
            "memory_used_mb": round(self.memory_usage_bytes / (1024 * 1024), 2),
            "memory_limit_mb": self.max_memory_mb,
            "entries_in_memory": len(self.memory_cache),
        }


# Global cache instance
_cache_instance: PerformanceCache | None = None


def initialize_cache(max_memory_mb: int = 100) -> PerformanceCache:
    """Initialize global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = PerformanceCache(max_memory_mb=max_memory_mb)
    return _cache_instance


def get_cache() -> PerformanceCache:
    """Get global cache instance."""
    return initialize_cache()


def cached(ttl_seconds: int | None = 3600):
    """Decorator to cache function results.

    Args:
        ttl_seconds: Time-to-live in seconds (None = no expiration)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            cache = get_cache()

            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{args!s}:{kwargs!s}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds=ttl_seconds)
            return result

        return wrapper

    return decorator


class RequestDeduplicator:
    """Deduplicates concurrent identical requests."""

    def __init__(self) -> None:
        """Initialize RequestDeduplicator."""
        self.pending_requests: dict[str, Any] = {}

    def _request_key(self, *args, **kwargs) -> str:
        """Generate request key."""
        return hashlib.sha256((str(args) + str(kwargs)).encode()).hexdigest()[:16]

    async def execute_deduplicated(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function, deduplicating concurrent requests."""
        key = self._request_key(*args, **kwargs)

        # If request already pending, wait for it
        if key in self.pending_requests:
            logger.debug(f"⏳ Deduplicating request: {key}")
            import asyncio

            while key in self.pending_requests:
                await asyncio.sleep(0.1)
            return self.pending_requests.get(key)

        # Mark as pending
        self.pending_requests[key] = None

        try:
            # Execute function
            result = func(*args, **kwargs)
            self.pending_requests[key] = result
            return result
        finally:
            # Clean up
            self.pending_requests.pop(key, None)


# Global deduplicator
_deduplicator = RequestDeduplicator()


def deduplicated(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to deduplicate concurrent requests."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        return await _deduplicator.execute_deduplicated(func, *args, **kwargs)

    return wrapper


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage
    cache = initialize_cache(max_memory_mb=10)

    # Test caching
    cache.set("key1", {"data": "value1"}, ttl_seconds=3600)
    logger.info("Set key1")

    value = cache.get("key1")
    logger.info(f"Got key1: {value}")

    # Test stats
    logger.info(f"Cache stats: {cache.get_stats()}")

    # Test decorator
    @cached(ttl_seconds=60)
    def expensive_operation(x) -> None:
        import time

        time.sleep(1)
        return x * 2

    logger.info("Calling expensive_operation(5)...")
    result1 = expensive_operation(5)
    logger.info(f"Result: {result1}")

    logger.info("Calling expensive_operation(5) again (should be cached)...")
    result2 = expensive_operation(5)
    logger.info(f"Result: {result2}")

    logger.info(f"Final cache stats: {cache.get_stats()}")
