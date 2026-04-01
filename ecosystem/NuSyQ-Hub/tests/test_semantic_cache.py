"""Tests for src/orchestration/semantic_cache.py — CachedResponse and SemanticCache."""

import time


class TestCachedResponse:
    """Tests for CachedResponse dataclass."""

    def _make(self, **kwargs):
        from src.orchestration.semantic_cache import CachedResponse
        defaults = {
            "query": "What is Python?",
            "response": "Python is a programming language.",
            "system": "ollama",
            "timestamp": time.time(),
        }
        defaults.update(kwargs)
        return CachedResponse(**defaults)

    def test_instantiation(self):
        assert self._make() is not None

    def test_fields_stored(self):
        cr = self._make(query="test query", system="chatdev")
        assert cr.query == "test query"
        assert cr.system == "chatdev"

    def test_default_token_count_none(self):
        assert self._make().token_count is None

    def test_default_model_none(self):
        assert self._make().model is None

    def test_is_not_expired_fresh(self):
        cr = self._make(timestamp=time.time())
        assert cr.is_expired(ttl_seconds=3600) is False

    def test_is_expired_old(self):
        cr = self._make(timestamp=time.time() - 7200)  # 2 hours ago
        assert cr.is_expired(ttl_seconds=3600) is True

    def test_is_expired_zero_ttl(self):
        cr = self._make(timestamp=time.time() - 1)
        assert cr.is_expired(ttl_seconds=0) is True

    def test_to_dict_returns_dict(self):
        d = self._make().to_dict()
        assert isinstance(d, dict)

    def test_to_dict_has_required_keys(self):
        d = self._make().to_dict()
        for key in ("query", "response", "system", "timestamp"):
            assert key in d

    def test_custom_metadata(self):
        cr = self._make(metadata={"source": "test"})
        assert cr.metadata == {"source": "test"}


class TestSemanticCacheInit:
    """Tests for SemanticCache initialization."""

    def test_instantiation(self, tmp_path):
        from src.orchestration.semantic_cache import SemanticCache
        sc = SemanticCache(cache_dir=str(tmp_path / "cache"))
        assert sc is not None

    def test_cache_dir_created(self, tmp_path):
        from src.orchestration.semantic_cache import SemanticCache
        cache_path = tmp_path / "ai_cache"
        SemanticCache(cache_dir=str(cache_path))
        assert cache_path.exists()

    def test_default_similarity_threshold(self, tmp_path):
        from src.orchestration.semantic_cache import SemanticCache
        sc = SemanticCache(cache_dir=str(tmp_path / "c"))
        assert sc.similarity_threshold == 0.85

    def test_custom_similarity_threshold(self, tmp_path):
        from src.orchestration.semantic_cache import SemanticCache
        sc = SemanticCache(cache_dir=str(tmp_path / "c"), similarity_threshold=0.7)
        assert sc.similarity_threshold == 0.7

    def test_stats_initialized(self, tmp_path):
        from src.orchestration.semantic_cache import SemanticCache
        sc = SemanticCache(cache_dir=str(tmp_path / "c"))
        assert sc.stats["hits"] == 0
        assert sc.stats["misses"] == 0
        assert sc.stats["total_queries"] == 0


class TestSemanticCacheCompute:
    """Tests for internal helper methods."""

    def _make_cache(self, tmp_path):
        from src.orchestration.semantic_cache import SemanticCache
        return SemanticCache(cache_dir=str(tmp_path / "c"))

    def test_compute_hash_returns_string(self, tmp_path):
        sc = self._make_cache(tmp_path)
        h = sc._compute_hash("hello world")
        assert isinstance(h, str)

    def test_compute_hash_fixed_length(self, tmp_path):
        sc = self._make_cache(tmp_path)
        h = sc._compute_hash("any text here")
        assert len(h) == 16

    def test_compute_hash_deterministic(self, tmp_path):
        sc = self._make_cache(tmp_path)
        assert sc._compute_hash("test") == sc._compute_hash("test")

    def test_compute_hash_different_texts(self, tmp_path):
        sc = self._make_cache(tmp_path)
        assert sc._compute_hash("hello") != sc._compute_hash("world")

    def test_compute_similarity_identical(self, tmp_path):
        sc = self._make_cache(tmp_path)
        sim = sc._compute_similarity("hello world", "hello world")
        assert sim == 1.0

    def test_compute_similarity_no_overlap(self, tmp_path):
        sc = self._make_cache(tmp_path)
        sim = sc._compute_similarity("apple banana", "car dog")
        assert sim == 0.0

    def test_compute_similarity_partial(self, tmp_path):
        sc = self._make_cache(tmp_path)
        sim = sc._compute_similarity("hello world", "hello there")
        assert 0.0 < sim < 1.0

    def test_compute_similarity_empty_returns_zero(self, tmp_path):
        sc = self._make_cache(tmp_path)
        assert sc._compute_similarity("", "hello") == 0.0


class TestSemanticCacheGetSet:
    """Tests for SemanticCache get() and set() operations."""

    def _make_cache(self, tmp_path):
        from src.orchestration.semantic_cache import SemanticCache
        return SemanticCache(cache_dir=str(tmp_path / "c"), ttl_seconds=3600)

    def test_get_miss_returns_none(self, tmp_path):
        sc = self._make_cache(tmp_path)
        result = sc.get("unknown query", "ollama")
        assert result is None

    def test_get_miss_increments_misses(self, tmp_path):
        sc = self._make_cache(tmp_path)
        sc.get("unknown query", "ollama")
        assert sc.stats["misses"] == 1

    def test_set_then_get_returns_response(self, tmp_path):
        sc = self._make_cache(tmp_path)
        sc.set("What is Python?", "A programming language", "ollama")
        result = sc.get("What is Python?", "ollama")
        assert result is not None
        assert result.response == "A programming language"

    def test_set_then_get_increments_hits(self, tmp_path):
        sc = self._make_cache(tmp_path)
        sc.set("my query", "my response", "chatdev")
        sc.get("my query", "chatdev")
        assert sc.stats["hits"] == 1

    def test_different_system_no_hit(self, tmp_path):
        sc = self._make_cache(tmp_path)
        sc.set("my query", "response", "ollama")
        result = sc.get("my query", "chatdev")  # Different system
        assert result is None

    def test_set_with_token_count(self, tmp_path):
        sc = self._make_cache(tmp_path)
        sc.set("query", "response", "ollama", token_count=150)
        result = sc.get("query", "ollama")
        assert result is not None
        assert result.token_count == 150

    def test_total_queries_increments(self, tmp_path):
        sc = self._make_cache(tmp_path)
        sc.get("q1", "ollama")
        sc.get("q2", "ollama")
        assert sc.stats["total_queries"] == 2
