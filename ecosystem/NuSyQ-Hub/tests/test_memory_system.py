"""Tests for src/memory/ — ContextualMemory, MemoryPalace, SemanticClusters."""

import time

import pytest


class TestContextualMemory:
    """Tests for ContextualMemory store/retrieve/clear lifecycle."""

    @pytest.fixture
    def cm(self):
        from src.memory.contextual_memory import ContextualMemory
        return ContextualMemory()

    def test_store_and_retrieve(self, cm):
        cm.store_context("key1", {"data": 42})
        assert cm.retrieve_context("key1") == {"data": 42}

    def test_retrieve_missing_returns_none(self, cm):
        assert cm.retrieve_context("nonexistent") is None

    def test_overwrite_key(self, cm):
        cm.store_context("k", "first")
        cm.store_context("k", "second")
        assert cm.retrieve_context("k") == "second"

    def test_timestamp_advances_on_store(self, cm):
        from datetime import datetime
        before = datetime.now()
        cm.store_context("t", "x")
        ts = cm.get_context_timestamp("t")
        after = datetime.now()
        assert before <= ts <= after

    def test_timestamp_missing_key_returns_now(self, cm):
        from datetime import datetime
        before = datetime.now()
        ts = cm.get_context_timestamp("missing")
        after = datetime.now()
        assert before <= ts <= after

    def test_clear_context_removes_key(self, cm):
        cm.store_context("r", 99)
        cm.clear_context("r")
        assert cm.retrieve_context("r") is None

    def test_clear_context_noop_for_missing(self, cm):
        # Should not raise
        cm.clear_context("never_stored")

    def test_clear_all_contexts(self, cm):
        cm.store_context("a", 1)
        cm.store_context("b", 2)
        cm.clear_all_contexts()
        assert cm.retrieve_context("a") is None
        assert cm.retrieve_context("b") is None

    def test_list_contexts_empty(self, cm):
        assert cm.list_contexts() == []

    def test_list_contexts_after_store(self, cm):
        cm.store_context("x", 1)
        cm.store_context("y", 2)
        keys = cm.list_contexts()
        assert set(keys) == {"x", "y"}

    def test_list_contexts_after_clear(self, cm):
        cm.store_context("a", 1)
        cm.clear_context("a")
        assert "a" not in cm.list_contexts()

    def test_store_various_types(self, cm):
        cm.store_context("int", 42)
        cm.store_context("list", [1, 2, 3])
        cm.store_context("none", None)
        assert cm.retrieve_context("int") == 42
        assert cm.retrieve_context("list") == [1, 2, 3]
        assert cm.retrieve_context("none") is None


class TestMemoryPalace:
    """Tests for MemoryPalace node management and tag-based search."""

    @pytest.fixture
    def mp(self):
        from src.memory.memory_palace import MemoryPalace
        return MemoryPalace()

    def test_add_and_retrieve_node(self, mp):
        mp.add_memory_node("n1", "content", tags=["python", "code"])
        node = mp.retrieve_memory_node("n1")
        assert node is not None
        assert node["content"] == "content"

    def test_retrieve_missing_node(self, mp):
        assert mp.retrieve_memory_node("nope") is None

    def test_node_has_timestamp(self, mp):
        from datetime import datetime
        before = datetime.now()
        mp.add_memory_node("n2", "x")
        after = datetime.now()
        node = mp.retrieve_memory_node("n2")
        assert before <= node["timestamp"] <= after

    def test_node_tags_stored(self, mp):
        mp.add_memory_node("n3", "y", tags=["a", "b"])
        node = mp.retrieve_memory_node("n3")
        assert node["tags"] == ["a", "b"]

    def test_add_node_no_tags(self, mp):
        mp.add_memory_node("n4", "z")
        node = mp.retrieve_memory_node("n4")
        assert node["tags"] == []

    def test_search_by_tag_returns_node_ids(self, mp):
        mp.add_memory_node("n5", "v", tags=["search_test"])
        mp.add_memory_node("n6", "w", tags=["search_test", "extra"])
        results = mp.search_by_tag("search_test")
        assert "n5" in results
        assert "n6" in results

    def test_search_by_missing_tag_returns_empty(self, mp):
        assert mp.search_by_tag("no_such_tag") == []

    def test_get_all_memory_nodes(self, mp):
        mp.add_memory_node("a", 1)
        mp.add_memory_node("b", 2)
        nodes = mp.get_all_memory_nodes()
        assert "a" in nodes
        assert "b" in nodes

    def test_clear_memory_removes_all(self, mp):
        mp.add_memory_node("x", "data", tags=["t"])
        mp.clear_memory()
        assert mp.retrieve_memory_node("x") is None
        assert mp.search_by_tag("t") == []
        assert mp.get_all_memory_nodes() == {}

    def test_overwrite_node(self, mp):
        mp.add_memory_node("dup", "first")
        mp.add_memory_node("dup", "second")
        node = mp.retrieve_memory_node("dup")
        assert node["content"] == "second"

    def test_multi_tag_clustering(self, mp):
        mp.add_memory_node("m", "val", tags=["python", "ai", "code"])
        assert "m" in mp.search_by_tag("python")
        assert "m" in mp.search_by_tag("ai")
        assert "m" in mp.search_by_tag("code")


class TestSemanticClusters:
    """Tests for SemanticClusters tag-based node organization."""

    @pytest.fixture
    def sc(self):
        from src.memory.semantic_clusters import SemanticClusters
        return SemanticClusters()

    def test_add_and_get_cluster(self, sc):
        sc.add_memory_node("n1", ["python", "code"])
        assert "n1" in sc.get_cluster("python")
        assert "n1" in sc.get_cluster("code")

    def test_get_empty_cluster(self, sc):
        assert sc.get_cluster("nothing") == []

    def test_remove_memory_node(self, sc):
        sc.add_memory_node("n2", ["tag"])
        sc.remove_memory_node("n2", ["tag"])
        assert "n2" not in sc.get_cluster("tag")

    def test_remove_node_from_multiple_tags(self, sc):
        sc.add_memory_node("n3", ["a", "b"])
        sc.remove_memory_node("n3", ["a", "b"])
        assert "n3" not in sc.get_cluster("a")
        assert "n3" not in sc.get_cluster("b")

    def test_remove_nonexistent_node_is_safe(self, sc):
        sc.add_memory_node("n4", ["tag"])
        sc.remove_memory_node("missing", ["tag"])  # should not raise

    def test_clear_clusters(self, sc):
        sc.add_memory_node("n5", ["x"])
        sc.clear_clusters()
        assert sc.get_cluster("x") == []
        assert sc.get_all_clusters() == {}

    def test_get_all_clusters(self, sc):
        sc.add_memory_node("n6", ["p"])
        sc.add_memory_node("n7", ["q"])
        clusters = sc.get_all_clusters()
        assert "p" in clusters
        assert "q" in clusters

    def test_multiple_nodes_same_tag(self, sc):
        sc.add_memory_node("a", ["shared"])
        sc.add_memory_node("b", ["shared"])
        assert set(sc.get_cluster("shared")) == {"a", "b"}

    def test_repr(self, sc):
        r = repr(sc)
        assert "SemanticClusters" in r

    def test_add_node_no_tags(self, sc):
        sc.add_memory_node("empty", [])
        assert sc.get_all_clusters() == {}


class TestMemorySystemIntegration:
    """Integration: memory palace feeds semantic clusters for retrieval."""

    def test_full_memory_lifecycle(self):
        from src.memory import ContextualMemory, MemoryPalace, SemanticClusters

        # Build memory palace
        mp = MemoryPalace()
        mp.add_memory_node("concept_a", "NuSyQ orchestration hub", tags=["architecture", "python"])
        mp.add_memory_node("concept_b", "MJOLNIR dispatch protocol", tags=["architecture", "dispatch"])
        mp.add_memory_node("concept_c", "Ollama local inference", tags=["llm", "local"])

        # Architecture nodes
        arch_nodes = mp.search_by_tag("architecture")
        assert "concept_a" in arch_nodes
        assert "concept_b" in arch_nodes
        assert "concept_c" not in arch_nodes

        # Store retrieval results in contextual memory
        cm = ContextualMemory()
        cm.store_context("last_arch_query", arch_nodes)
        cached = cm.retrieve_context("last_arch_query")
        assert cached == arch_nodes

        # Semantic clusters for cross-reference
        sc = SemanticClusters()
        for nid in arch_nodes:
            node = mp.retrieve_memory_node(nid)
            sc.add_memory_node(nid, node["tags"])

        assert "concept_a" in sc.get_cluster("python")
        assert "concept_b" in sc.get_cluster("dispatch")

    def test_memory_package_exports(self):
        from src.memory import ContextualMemory, MemoryPalace, SemanticClusters
        assert ContextualMemory is not None
        assert MemoryPalace is not None
        assert SemanticClusters is not None
