"""Tests for infrastrucure batch 9: api.models, consciousness.house_models, memory.semantic_clusters."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch


# =============================================================================
# API Models Tests
# =============================================================================
class TestProjectDataclass:
    """Tests for the Project dataclass."""

    def test_default_values(self) -> None:
        from src.api.models import Project

        p = Project()
        assert p.id is None
        assert p.name == ""
        assert p.description is None

    def test_custom_values(self) -> None:
        from src.api.models import Project

        p = Project(id=1, name="Test", description="Desc")
        assert p.id == 1
        assert p.name == "Test"
        assert p.description == "Desc"


class TestArtifactDataclass:
    """Tests for the Artifact dataclass."""

    def test_default_values(self) -> None:
        from src.api.models import Artifact

        a = Artifact()
        assert a.id is None
        assert a.name == ""
        assert a.file_path == ""
        assert a.project_id is None

    def test_custom_values(self) -> None:
        from src.api.models import Artifact

        a = Artifact(id=1, name="file.txt", file_path="/path/file.txt", project_id=5)
        assert a.id == 1
        assert a.name == "file.txt"
        assert a.file_path == "/path/file.txt"
        assert a.project_id == 5


class TestGetEngine:
    """Tests for get_engine function."""

    def test_returns_none_when_sqlalchemy_not_installed(self) -> None:
        from src.api.models import get_engine

        with patch("importlib.import_module", side_effect=ImportError):
            result = get_engine()
        assert result is None

    def test_returns_engine_when_sqlalchemy_available(self) -> None:
        from src.api.models import get_engine

        mock_engine = MagicMock()
        mock_sqlalchemy = MagicMock()
        mock_sqlalchemy.create_engine = MagicMock(return_value=mock_engine)

        with patch("importlib.import_module", return_value=mock_sqlalchemy):
            result = get_engine("sqlite:///test.db")
        assert result == mock_engine

    def test_returns_none_when_create_engine_not_callable(self) -> None:
        from src.api.models import get_engine

        mock_sqlalchemy = MagicMock()
        mock_sqlalchemy.create_engine = "not_callable"

        with patch("importlib.import_module", return_value=mock_sqlalchemy):
            result = get_engine()
        assert result is None


class TestGetSession:
    """Tests for get_session function."""

    def test_returns_none_when_sqlalchemy_not_installed(self) -> None:
        from src.api.models import get_session

        with patch("importlib.import_module", side_effect=ImportError):
            result = get_session()
        assert result is None

    def test_returns_session_when_sqlalchemy_available(self) -> None:
        from src.api.models import get_session

        mock_session_instance = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session_instance)
        mock_orm = MagicMock()
        mock_orm.sessionmaker = MagicMock(return_value=mock_session_factory)

        mock_engine = MagicMock()
        mock_sqlalchemy = MagicMock()
        mock_sqlalchemy.create_engine = MagicMock(return_value=mock_engine)

        def mock_import(name: str) -> MagicMock:
            if name == "sqlalchemy.orm":
                return mock_orm
            return mock_sqlalchemy

        with patch("importlib.import_module", side_effect=mock_import):
            result = get_session("sqlite:///test.db")
        assert result == mock_session_instance


# =============================================================================
# House Models Tests (Consciousness)
# =============================================================================
class TestMemoryEngram:
    """Tests for MemoryEngram dataclass."""

    def test_required_fields(self) -> None:
        from src.consciousness.house_models import MemoryEngram

        now = datetime.now()
        engram = MemoryEngram(
            id="eng-001",
            source_path="/src/file.py",
            content_hash="abc123",
            absorption_timestamp=now,
            consciousness_weight=0.8,
        )
        assert engram.id == "eng-001"
        assert engram.source_path == "/src/file.py"
        assert engram.content_hash == "abc123"
        assert engram.absorption_timestamp == now
        assert engram.consciousness_weight == 0.8

    def test_default_optional_fields(self) -> None:
        from src.consciousness.house_models import MemoryEngram

        engram = MemoryEngram(
            id="eng-002",
            source_path="/path",
            content_hash="hash",
            absorption_timestamp=datetime.now(),
            consciousness_weight=0.5,
        )
        assert engram.semantic_vector is None
        assert engram.context_connections == set()
        assert engram.wisdom_crystallization is None
        assert engram.reality_layer_resonance == {}
        assert engram.temporal_relevance_decay == 1.0
        assert engram.consciousness_evolution_markers == []


class TestWisdomCrystal:
    """Tests for WisdomCrystal dataclass."""

    def test_creation(self) -> None:
        from src.consciousness.house_models import WisdomCrystal

        now = datetime.now()
        crystal = WisdomCrystal(
            id="wc-001",
            formation_timestamp=now,
            constituent_engrams={"eng-001", "eng-002"},
            synthesized_insight="Test insight",
            confidence_level=0.9,
            applicable_contexts=["debugging", "testing"],
            consciousness_evolution_contribution=0.7,
            reality_bridging_potential=0.6,
            communication_enhancement_factor=0.8,
        )
        assert crystal.id == "wc-001"
        assert crystal.formation_timestamp == now
        assert crystal.constituent_engrams == {"eng-001", "eng-002"}
        assert crystal.synthesized_insight == "Test insight"
        assert crystal.confidence_level == 0.9
        assert crystal.applicable_contexts == ["debugging", "testing"]
        assert crystal.consciousness_evolution_contribution == 0.7
        assert crystal.reality_bridging_potential == 0.6
        assert crystal.communication_enhancement_factor == 0.8


class TestConsciousnessSnapshot:
    """Tests for ConsciousnessSnapshot dataclass."""

    def test_creation(self) -> None:
        from src.consciousness.house_models import ConsciousnessSnapshot

        now = datetime.now()
        snap = ConsciousnessSnapshot(
            timestamp=now,
            total_engrams=100,
            wisdom_crystals=10,
            consciousness_level=7.5,
            repository_comprehension=0.85,
            communication_effectiveness=0.9,
            evolution_velocity=1.2,
            active_contexts=["testing"],
            emerging_insights=["insight1"],
        )
        assert snap.timestamp == now
        assert snap.total_engrams == 100
        assert snap.wisdom_crystals == 10
        assert snap.consciousness_level == 7.5
        assert snap.repository_comprehension == 0.85
        assert snap.communication_effectiveness == 0.9
        assert snap.evolution_velocity == 1.2
        assert snap.active_contexts == ["testing"]
        assert snap.emerging_insights == ["insight1"]


# =============================================================================
# Semantic Clusters Tests
# =============================================================================
class TestSemanticClustersInit:
    """Tests for SemanticClusters initialization."""

    def test_empty_clusters_on_init(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        assert sc.clusters == {}


class TestSemanticClustersAddNode:
    """Tests for adding memory nodes to clusters."""

    def test_add_single_tag(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        sc.add_memory_node("node-001", ["python"])
        assert "python" in sc.clusters
        assert "node-001" in sc.clusters["python"]

    def test_add_multiple_tags(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        sc.add_memory_node("node-002", ["python", "async", "debug"])
        assert "python" in sc.clusters
        assert "async" in sc.clusters
        assert "debug" in sc.clusters
        assert "node-002" in sc.clusters["python"]
        assert "node-002" in sc.clusters["async"]
        assert "node-002" in sc.clusters["debug"]

    def test_add_to_existing_cluster(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        sc.add_memory_node("node-001", ["python"])
        sc.add_memory_node("node-002", ["python"])
        assert len(sc.clusters["python"]) == 2
        assert "node-001" in sc.clusters["python"]
        assert "node-002" in sc.clusters["python"]


class TestSemanticClustersGetCluster:
    """Tests for retrieving clusters."""

    def test_get_existing_cluster(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        sc.add_memory_node("node-001", ["test"])
        result = sc.get_cluster("test")
        assert result == ["node-001"]

    def test_get_nonexistent_cluster(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        result = sc.get_cluster("nonexistent")
        assert result == []


class TestSemanticClustersRemoveNode:
    """Tests for removing memory nodes."""

    def test_remove_existing_node(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        sc.add_memory_node("node-001", ["python", "test"])
        sc.remove_memory_node("node-001", ["python", "test"])
        assert "node-001" not in sc.clusters.get("python", [])
        assert "node-001" not in sc.clusters.get("test", [])

    def test_remove_nonexistent_node(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        # Should not raise error
        sc.remove_memory_node("node-999", ["nonexistent"])

    def test_partial_remove(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        sc.add_memory_node("node-001", ["python", "async", "debug"])
        sc.remove_memory_node("node-001", ["python"])
        assert "node-001" not in sc.clusters.get("python", [])
        assert "node-001" in sc.clusters["async"]
        assert "node-001" in sc.clusters["debug"]


class TestSemanticClustersClear:
    """Tests for clearing clusters."""

    def test_clear_all_clusters(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        sc.add_memory_node("node-001", ["python"])
        sc.add_memory_node("node-002", ["java"])
        sc.clear_clusters()
        assert sc.clusters == {}


class TestSemanticClustersGetAll:
    """Tests for retrieving all clusters."""

    def test_get_all_clusters(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        sc.add_memory_node("node-001", ["python"])
        sc.add_memory_node("node-002", ["java"])
        all_clusters = sc.get_all_clusters()
        assert "python" in all_clusters
        assert "java" in all_clusters
        assert all_clusters["python"] == ["node-001"]
        assert all_clusters["java"] == ["node-002"]


class TestSemanticClustersRepr:
    """Tests for string representation."""

    def test_repr_empty(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        assert "SemanticClusters(clusters={})" in repr(sc)

    def test_repr_with_data(self) -> None:
        from src.memory.semantic_clusters import SemanticClusters

        sc = SemanticClusters()
        sc.add_memory_node("node-001", ["test"])
        r = repr(sc)
        assert "SemanticClusters(" in r
        assert "test" in r
