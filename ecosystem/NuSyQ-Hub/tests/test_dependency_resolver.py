"""Tests for src/orchestration/dependency_resolver.py — enums, dataclasses, resolver."""

import time

import pytest


class TestTaskDependencyEnum:
    """Tests for TaskDependency enum."""

    def test_has_four_values(self):
        from src.orchestration.dependency_resolver import TaskDependency
        assert len(list(TaskDependency)) == 4

    def test_sequential_value(self):
        from src.orchestration.dependency_resolver import TaskDependency
        assert TaskDependency.SEQUENTIAL.value == "sequential"

    def test_all_members_present(self):
        from src.orchestration.dependency_resolver import TaskDependency
        names = {t.name for t in TaskDependency}
        assert names == {"SEQUENTIAL", "CONDITIONAL", "PARALLEL", "GROUPED"}


class TestCachedResult:
    """Tests for CachedResult dataclass."""

    def _make(self, **kwargs):
        from src.orchestration.dependency_resolver import CachedResult
        defaults = {
            "fingerprint": "abc123",
            "task_type": "code_review",
            "parameters": {"file": "foo.py"},
            "result": {"issues": []},
            "tokens_saved": 50,
        }
        defaults.update(kwargs)
        return CachedResult(**defaults)

    def test_instantiation(self):
        assert self._make() is not None

    def test_fields_stored(self):
        cr = self._make(fingerprint="xyz", task_type="test_run", tokens_saved=100)
        assert cr.fingerprint == "xyz"
        assert cr.task_type == "test_run"
        assert cr.tokens_saved == 100

    def test_default_hit_count_zero(self):
        assert self._make().hit_count == 0

    def test_is_stale_fresh(self):
        cr = self._make()
        assert cr.is_stale(max_age_seconds=3600) is False

    def test_is_stale_old(self):
        from datetime import UTC, datetime, timedelta
        from src.orchestration.dependency_resolver import CachedResult
        old_time = datetime.now(UTC) - timedelta(hours=2)
        cr = CachedResult(
            fingerprint="x",
            task_type="t",
            parameters={},
            result=None,
            tokens_saved=0,
            cached_at=old_time,
        )
        assert cr.is_stale(max_age_seconds=3600) is True

    def test_to_dict_has_required_keys(self):
        d = self._make().to_dict()
        for key in ("fingerprint", "task_type", "parameters", "result", "tokens_saved",
                    "cached_at", "hit_count"):
            assert key in d

    def test_from_dict_roundtrip(self):
        cr = self._make(fingerprint="roundtrip", tokens_saved=75)
        d = cr.to_dict()
        cr2 = type(cr).from_dict(d)
        assert cr2.fingerprint == "roundtrip"
        assert cr2.tokens_saved == 75
        assert cr2.hit_count == cr.hit_count


class TestTaskDependencyEdge:
    """Tests for TaskDependencyEdge dataclass."""

    def _make(self, **kwargs):
        from src.orchestration.dependency_resolver import TaskDependency, TaskDependencyEdge
        defaults = {
            "source_task": "code_review",
            "target_task": "refactor",
            "dependency_type": TaskDependency.SEQUENTIAL,
            "confidence": 0.85,
        }
        defaults.update(kwargs)
        return TaskDependencyEdge(**defaults)

    def test_instantiation(self):
        assert self._make() is not None

    def test_default_frequency_one(self):
        assert self._make().frequency == 1

    def test_to_dict_structure(self):
        d = self._make().to_dict()
        assert d["source"] == "code_review"
        assert d["target"] == "refactor"
        assert d["type"] == "sequential"
        assert d["confidence"] == 0.85


class TestDependencyGraph:
    """Tests for DependencyGraph dataclass."""

    def _make(self):
        from src.orchestration.dependency_resolver import DependencyGraph
        return DependencyGraph()

    def test_instantiation(self):
        g = self._make()
        assert g.edges == []
        assert g.cached_results == {}

    def test_get_dependencies_for_task_empty(self):
        result = self._make().get_dependencies_for_task("task_a")
        assert result == []

    def test_get_dependencies_high_confidence(self):
        from src.orchestration.dependency_resolver import (
            DependencyGraph,
            TaskDependency,
            TaskDependencyEdge,
        )
        g = DependencyGraph()
        g.edges.append(TaskDependencyEdge(
            source_task="a", target_task="b",
            dependency_type=TaskDependency.SEQUENTIAL, confidence=0.9
        ))
        g.edges.append(TaskDependencyEdge(
            source_task="a", target_task="c",
            dependency_type=TaskDependency.PARALLEL, confidence=0.4  # below threshold
        ))
        deps = g.get_dependencies_for_task("a")
        assert len(deps) == 1
        assert deps[0].target_task == "b"

    def test_get_blocking_tasks(self):
        from src.orchestration.dependency_resolver import (
            DependencyGraph,
            TaskDependency,
            TaskDependencyEdge,
        )
        g = DependencyGraph()
        g.edges.append(TaskDependencyEdge(
            source_task="review", target_task="refactor",
            dependency_type=TaskDependency.SEQUENTIAL, confidence=0.9
        ))
        blockers = g.get_blocking_tasks("refactor")
        assert "review" in blockers

    def test_get_blocking_tasks_non_sequential_excluded(self):
        from src.orchestration.dependency_resolver import (
            DependencyGraph,
            TaskDependency,
            TaskDependencyEdge,
        )
        g = DependencyGraph()
        g.edges.append(TaskDependencyEdge(
            source_task="a", target_task="b",
            dependency_type=TaskDependency.PARALLEL, confidence=0.9
        ))
        blockers = g.get_blocking_tasks("b")
        assert blockers == []

    def test_optimal_execution_order_no_deps(self):
        tasks = ["task_c", "task_b", "task_a"]
        result = self._make().get_optimal_execution_order(tasks)
        # All tasks returned, in some order
        assert set(result) == set(tasks)

    def test_optimal_execution_order_with_deps(self):
        from src.orchestration.dependency_resolver import (
            DependencyGraph,
            TaskDependency,
            TaskDependencyEdge,
        )
        g = DependencyGraph()
        # review must happen before refactor
        g.edges.append(TaskDependencyEdge(
            source_task="review", target_task="refactor",
            dependency_type=TaskDependency.SEQUENTIAL, confidence=0.9
        ))
        ordered = g.get_optimal_execution_order(["refactor", "review", "deploy"])
        review_idx = ordered.index("review")
        refactor_idx = ordered.index("refactor")
        assert review_idx < refactor_idx

    def test_to_dict_structure(self):
        d = self._make().to_dict()
        assert "edges" in d
        assert "cached_results" in d
        assert "total_cache_hits" in d


class TestSHA256Fingerprinter:
    """Tests for SHA256Fingerprinter."""

    def test_returns_string(self):
        from src.orchestration.dependency_resolver import SHA256Fingerprinter
        fp = SHA256Fingerprinter().fingerprint("code_review", {"file": "foo.py"})
        assert isinstance(fp, str)

    def test_fixed_length(self):
        from src.orchestration.dependency_resolver import SHA256Fingerprinter
        fp = SHA256Fingerprinter().fingerprint("test", {})
        assert len(fp) == 16

    def test_deterministic(self):
        from src.orchestration.dependency_resolver import SHA256Fingerprinter
        f = SHA256Fingerprinter()
        fp1 = f.fingerprint("review", {"file": "a.py"})
        fp2 = f.fingerprint("review", {"file": "a.py"})
        assert fp1 == fp2

    def test_different_params_different_fp(self):
        from src.orchestration.dependency_resolver import SHA256Fingerprinter
        f = SHA256Fingerprinter()
        fp1 = f.fingerprint("review", {"file": "a.py"})
        fp2 = f.fingerprint("review", {"file": "b.py"})
        assert fp1 != fp2

    def test_different_task_types_different_fp(self):
        from src.orchestration.dependency_resolver import SHA256Fingerprinter
        f = SHA256Fingerprinter()
        fp1 = f.fingerprint("review", {})
        fp2 = f.fingerprint("refactor", {})
        assert fp1 != fp2


class TestDependencyResolverConfig:
    """Tests for DependencyResolverConfig defaults."""

    def test_defaults(self, tmp_path):
        from src.orchestration.dependency_resolver import DependencyResolverConfig
        cfg = DependencyResolverConfig(persistence_path=tmp_path / "deps")
        assert cfg.cache_max_age_seconds == 3600
        assert cfg.min_dependency_confidence == 0.7
        assert cfg.enable_caching is True
        assert cfg.enable_batching is True


class TestDependencyResolver:
    """Tests for DependencyResolver with tmp_path isolation."""

    @pytest.fixture
    def resolver(self, tmp_path):
        from src.orchestration.dependency_resolver import DependencyResolver, DependencyResolverConfig
        config = DependencyResolverConfig(persistence_path=tmp_path / "deps")
        return DependencyResolver(config=config)

    def test_instantiation(self, resolver):
        assert resolver is not None

    def test_graph_starts_empty(self, resolver):
        assert resolver.graph.edges == []

    def test_record_task_caches_result(self, resolver):
        resolver.record_task_execution(
            task_id="t1",
            task_type="code_review",
            parameters={"file": "foo.py"},
            result={"issues": 0},
            duration_ms=100.0,
            tokens_used=200,
        )
        assert len(resolver.graph.cached_results) == 1

    def test_record_two_sequential_tasks_builds_edge(self, resolver):
        resolver.record_task_execution(
            task_id="t1",
            task_type="code_review",
            parameters={},
            result={},
            duration_ms=100.0,
            tokens_used=100,
        )
        resolver.record_task_execution(
            task_id="t2",
            task_type="refactor",
            parameters={},
            result={},
            duration_ms=100.0,
            tokens_used=100,
            previous_task_id="t1",
            previous_task_type="code_review",
        )
        # Should have a dependency edge between them
        assert len(resolver.graph.edges) >= 1
