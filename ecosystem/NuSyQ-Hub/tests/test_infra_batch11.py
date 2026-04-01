"""Tests for infrastructure batch 11: memory_palace, ollama_hub, log_indexer."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch


# =============================================================================
# Memory Palace Tests
# =============================================================================
class TestMemoryPalaceInit:
    """Tests for MemoryPalace initialization."""

    def test_empty_on_init(self) -> None:
        from src.memory.memory_palace import MemoryPalace

        mp = MemoryPalace()
        assert mp.memory_nodes == {}
        assert mp.semantic_clusters == {}


class TestMemoryPalaceAddNode:
    """Tests for adding memory nodes."""

    def test_add_node_no_tags(self) -> None:
        from src.memory.memory_palace import MemoryPalace

        mp = MemoryPalace()
        mp.add_memory_node("node-001", {"data": "test"})
        assert "node-001" in mp.memory_nodes
        assert mp.memory_nodes["node-001"]["content"] == {"data": "test"}
        assert mp.memory_nodes["node-001"]["tags"] == []
        assert isinstance(mp.memory_nodes["node-001"]["timestamp"], datetime)

    def test_add_node_with_tags(self) -> None:
        from src.memory.memory_palace import MemoryPalace

        mp = MemoryPalace()
        mp.add_memory_node("node-002", "content", tags=["python", "test"])
        assert mp.memory_nodes["node-002"]["tags"] == ["python", "test"]
        assert "python" in mp.semantic_clusters
        assert "test" in mp.semantic_clusters
        assert "node-002" in mp.semantic_clusters["python"]
        assert "node-002" in mp.semantic_clusters["test"]

    def test_add_multiple_nodes_same_tag(self) -> None:
        from src.memory.memory_palace import MemoryPalace

        mp = MemoryPalace()
        mp.add_memory_node("node-001", "c1", tags=["shared"])
        mp.add_memory_node("node-002", "c2", tags=["shared"])
        assert len(mp.semantic_clusters["shared"]) == 2
        assert "node-001" in mp.semantic_clusters["shared"]
        assert "node-002" in mp.semantic_clusters["shared"]


class TestMemoryPalaceRetrieve:
    """Tests for retrieving memory nodes."""

    def test_retrieve_existing(self) -> None:
        from src.memory.memory_palace import MemoryPalace

        mp = MemoryPalace()
        mp.add_memory_node("node-001", [1, 2, 3])
        result = mp.retrieve_memory_node("node-001")
        assert result["content"] == [1, 2, 3]

    def test_retrieve_nonexistent(self) -> None:
        from src.memory.memory_palace import MemoryPalace

        mp = MemoryPalace()
        assert mp.retrieve_memory_node("missing") is None


class TestMemoryPalaceSearch:
    """Tests for searching by tag."""

    def test_search_existing_tag(self) -> None:
        from src.memory.memory_palace import MemoryPalace

        mp = MemoryPalace()
        mp.add_memory_node("node-001", "c", tags=["python"])
        result = mp.search_by_tag("python")
        assert result == ["node-001"]

    def test_search_nonexistent_tag(self) -> None:
        from src.memory.memory_palace import MemoryPalace

        mp = MemoryPalace()
        result = mp.search_by_tag("nonexistent")
        assert result == []


class TestMemoryPalaceGetAll:
    """Tests for getting all nodes."""

    def test_get_all_empty(self) -> None:
        from src.memory.memory_palace import MemoryPalace

        mp = MemoryPalace()
        assert mp.get_all_memory_nodes() == {}

    def test_get_all_with_nodes(self) -> None:
        from src.memory.memory_palace import MemoryPalace

        mp = MemoryPalace()
        mp.add_memory_node("n1", "c1")
        mp.add_memory_node("n2", "c2")
        nodes = mp.get_all_memory_nodes()
        assert len(nodes) == 2
        assert "n1" in nodes
        assert "n2" in nodes


class TestMemoryPalaceClear:
    """Tests for clearing memory."""

    def test_clear_all(self) -> None:
        from src.memory.memory_palace import MemoryPalace

        mp = MemoryPalace()
        mp.add_memory_node("n1", "c1", tags=["t1"])
        mp.clear_memory()
        assert mp.memory_nodes == {}
        assert mp.semantic_clusters == {}


# =============================================================================
# Ollama Hub Tests
# =============================================================================
class TestOllamaHubInit:
    """Tests for OllamaHub initialization."""

    def test_init(self) -> None:
        with patch("src.ai.ollama_hub.ollama") as mock_ollama:
            from src.ai.ollama_hub import OllamaHub

            hub = OllamaHub()
            assert hub.available_models == []
            assert hub.ollama is mock_ollama


class TestOllamaHubListModels:
    """Tests for listing models."""

    def test_list_models_success(self) -> None:
        with patch("src.ai.ollama_hub.ollama") as mock_ollama:
            mock_ollama.list_models.return_value = ["llama2", "mistral"]

            from src.ai.ollama_hub import OllamaHub

            hub = OllamaHub()
            result = hub.list_models()
            assert result == ["llama2", "mistral"]
            assert hub.available_models == ["llama2", "mistral"]

    def test_list_models_error(self) -> None:
        with patch("src.ai.ollama_hub.ollama") as mock_ollama:
            mock_ollama.list_models.side_effect = RuntimeError("No connection")

            from src.ai.ollama_hub import OllamaHub

            hub = OllamaHub()
            result = hub.list_models()
            assert result == []

    def test_list_models_none_returned(self) -> None:
        with patch("src.ai.ollama_hub.ollama") as mock_ollama:
            mock_ollama.list_models.return_value = None

            from src.ai.ollama_hub import OllamaHub

            hub = OllamaHub()
            result = hub.list_models()
            assert result == []


class TestOllamaHubLoadModel:
    """Tests for loading models."""

    def test_load_model_not_available(self) -> None:
        with patch("src.ai.ollama_hub.ollama") as mock_ollama:
            mock_ollama.is_available.return_value = False

            from src.ai.ollama_hub import OllamaHub

            hub = OllamaHub()
            result = hub.load_model("llama2")
            assert result is False

    def test_load_model_already_available(self) -> None:
        with patch("src.ai.ollama_hub.ollama") as mock_ollama:
            mock_ollama.is_available.return_value = True
            mock_ollama.list_models.return_value = ["llama2"]

            from src.ai.ollama_hub import OllamaHub

            hub = OllamaHub()
            result = hub.load_model("llama2")
            assert result is True

    def test_load_model_pull_success(self) -> None:
        with patch("src.ai.ollama_hub.ollama") as mock_ollama:
            mock_ollama.is_available.return_value = True
            mock_ollama.list_models.return_value = []
            mock_ollama.pull.return_value = True

            from src.ai.ollama_hub import OllamaHub

            hub = OllamaHub()
            result = hub.load_model("llama2")
            mock_ollama.pull.assert_called_with("llama2")
            assert result is True

    def test_load_model_ensure_model_fallback(self) -> None:
        with patch("src.ai.ollama_hub.ollama") as mock_ollama:
            mock_ollama.is_available.return_value = True
            mock_ollama.list_models.return_value = []
            # No pull method
            del mock_ollama.pull
            mock_ollama.ensure_model.return_value = True

            from src.ai.ollama_hub import OllamaHub

            hub = OllamaHub()
            result = hub.load_model("llama2")
            assert result is True

    def test_load_model_no_method_available(self) -> None:
        with patch("src.ai.ollama_hub.ollama") as mock_ollama:
            mock_ollama.is_available.return_value = True
            mock_ollama.list_models.return_value = []
            # Remove pull and ensure_model
            del mock_ollama.pull
            del mock_ollama.ensure_model

            from src.ai.ollama_hub import OllamaHub

            hub = OllamaHub()
            result = hub.load_model("llama2")
            assert result is False

    def test_load_model_exception(self) -> None:
        with patch("src.ai.ollama_hub.ollama") as mock_ollama:
            mock_ollama.is_available.side_effect = RuntimeError("Error")

            from src.ai.ollama_hub import OllamaHub

            hub = OllamaHub()
            result = hub.load_model("llama2")
            assert result is False


# =============================================================================
# Log Indexer Tests
# =============================================================================
class TestLatestMazeSummaries:
    """Tests for the log indexer function."""

    def test_no_log_dir(self, tmp_path: Path) -> None:
        from src.tools.log_indexer import latest_maze_summaries

        result = latest_maze_summaries(log_dir=tmp_path / "nonexistent")
        assert result == []

    def test_empty_log_dir(self, tmp_path: Path) -> None:
        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        result = latest_maze_summaries(log_dir=log_dir)
        assert result == []

    def test_no_matching_files(self, tmp_path: Path) -> None:
        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        (log_dir / "other_file.json").write_text("{}")
        result = latest_maze_summaries(log_dir=log_dir)
        assert result == []

    def test_returns_sorted_by_mtime(self, tmp_path: Path) -> None:
        import time

        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create files with different mtimes
        f1 = log_dir / "maze_summary_001.json"
        f1.write_text("{}")
        time.sleep(0.01)
        f2 = log_dir / "maze_summary_002.json"
        f2.write_text("{}")
        time.sleep(0.01)
        f3 = log_dir / "maze_summary_003.json"
        f3.write_text("{}")

        result = latest_maze_summaries(log_dir=log_dir, limit=3)
        # Most recent first
        assert result[0].name == "maze_summary_003.json"
        assert len(result) == 3

    def test_respects_limit(self, tmp_path: Path) -> None:
        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        for i in range(5):
            (log_dir / f"maze_summary_{i:03d}.json").write_text("{}")

        result = latest_maze_summaries(log_dir=log_dir, limit=2)
        assert len(result) == 2

    def test_default_limit(self, tmp_path: Path) -> None:
        from src.tools.log_indexer import latest_maze_summaries

        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        for i in range(10):
            (log_dir / f"maze_summary_{i:03d}.json").write_text("{}")

        result = latest_maze_summaries(log_dir=log_dir)
        assert len(result) == 3  # Default limit is 3
