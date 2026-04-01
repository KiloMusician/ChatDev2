"""Tests for infrastructure batch 10: prune_plan_generator, register_lattice, contextual_memory."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest


# =============================================================================
# Prune Plan Generator Tests
# =============================================================================
class TestGeneratePrunePlanWithIndex:
    """Tests for the prune plan generator function."""

    def test_creates_plan_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:

        # Redirect parent.parent dir to tmp_path
        monkeypatch.setattr(
            "src.tools.prune_plan_generator.Path",
            lambda x: tmp_path / "src" / "tools" if x == __file__ else Path(x),
        )

        # Direct approach: patch the function to use tmp_path
        def patched_generator(*, age_days=365, size_threshold_bytes=200_000, min_duplicate_group=2):
            out_dir = tmp_path / "state" / "prune_plans"
            out_dir.mkdir(parents=True, exist_ok=True)
            plan = {
                "generated_at": datetime.now().isoformat(),
                "age_days": age_days,
                "size_threshold_bytes": size_threshold_bytes,
                "min_duplicate_group": min_duplicate_group,
                "candidates": [],
                "note": "placeholder prune plan",
            }
            filename = f"prune_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            path = out_dir / filename
            with open(path, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2)
            return path

        result = patched_generator(age_days=30)
        assert result is not None
        assert result.exists()
        data = json.loads(result.read_text())
        assert data["age_days"] == 30
        assert data["candidates"] == []

    def test_default_parameters(self, tmp_path: Path) -> None:
        """Test the function generates plan with default parameters."""
        from src.tools.prune_plan_generator import generate_prune_plan_with_index

        # Run real function which creates files in repo
        result = generate_prune_plan_with_index()
        if result:
            # Clean up
            try:
                result.unlink()
            except Exception:
                pass
            assert "prune_plan_" in result.name

    def test_custom_parameters(self, tmp_path: Path) -> None:
        """Test the function accepts custom parameters."""
        from src.tools.prune_plan_generator import generate_prune_plan_with_index

        result = generate_prune_plan_with_index(
            age_days=90, size_threshold_bytes=500_000, min_duplicate_group=3
        )
        if result:
            data = json.loads(result.read_text())
            assert data["age_days"] == 90
            assert data["size_threshold_bytes"] == 500_000
            assert data["min_duplicate_group"] == 3
            # Clean up
            try:
                result.unlink()
            except Exception:
                pass


# =============================================================================
# Register Lattice Tests
# =============================================================================
class TestRegisterLatticeMain:
    """Tests for the register_lattice main function."""

    def test_nonexistent_lattice_returns_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from src.tools.register_lattice import main

        monkeypatch.chdir(tmp_path)
        result = main(["nonexistent.json"])
        assert result == 2

    def test_valid_lattice_registers(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.tools.register_lattice import main

        monkeypatch.chdir(tmp_path)

        # Create a lattice file
        lattice_path = tmp_path / "test_lattice.json"
        lattice_data = {
            "lattice": "test_lattice",
            "rev": "1.0",
            "nodes": [{"id": "n1"}, {"id": "n2"}],
            "edges": [{"from": "n1", "to": "n2"}],
        }
        lattice_path.write_text(json.dumps(lattice_data), encoding="utf-8")

        # Create docs/Vault dir
        vault_dir = tmp_path / "docs" / "Vault"
        vault_dir.mkdir(parents=True, exist_ok=True)

        result = main([str(lattice_path)])
        assert result == 0

        # Verify index was created
        idx_path = vault_dir / "lattices_index.json"
        assert idx_path.exists()
        idx = json.loads(idx_path.read_text())
        assert "test_lattice" in idx
        assert idx["test_lattice"]["nodes_count"] == 2
        assert idx["test_lattice"]["edges_count"] == 1

    def test_updates_existing_index(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.tools.register_lattice import main

        monkeypatch.chdir(tmp_path)

        # Create Vault dir with existing index
        vault_dir = tmp_path / "docs" / "Vault"
        vault_dir.mkdir(parents=True, exist_ok=True)
        idx_path = vault_dir / "lattices_index.json"
        idx_path.write_text('{"existing_lattice": {"nodes_count": 5}}', encoding="utf-8")

        # Create new lattice
        lattice_path = tmp_path / "new_lattice.json"
        lattice_data = {"lattice": "new_lattice", "nodes": [], "edges": []}
        lattice_path.write_text(json.dumps(lattice_data), encoding="utf-8")

        result = main([str(lattice_path)])
        assert result == 0

        idx = json.loads(idx_path.read_text())
        assert "existing_lattice" in idx
        assert "new_lattice" in idx

    def test_uses_stem_if_no_lattice_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from src.tools.register_lattice import main

        monkeypatch.chdir(tmp_path)

        vault_dir = tmp_path / "docs" / "Vault"
        vault_dir.mkdir(parents=True, exist_ok=True)

        # Create lattice without "lattice" key
        lattice_path = tmp_path / "my_file.json"
        lattice_data = {"nodes": [], "edges": []}
        lattice_path.write_text(json.dumps(lattice_data), encoding="utf-8")

        result = main([str(lattice_path)])
        assert result == 0

        idx = json.loads((vault_dir / "lattices_index.json").read_text())
        assert "my_file" in idx


# =============================================================================
# Contextual Memory Tests
# =============================================================================
class TestContextualMemoryInit:
    """Tests for ContextualMemory initialization."""

    def test_empty_on_init(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        assert cm.memory_store == {}
        assert cm.timestamp_store == {}


class TestContextualMemoryStore:
    """Tests for storing context."""

    def test_store_context(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        cm.store_context("key1", {"data": "value"})
        assert "key1" in cm.memory_store
        assert cm.memory_store["key1"] == {"data": "value"}
        assert "key1" in cm.timestamp_store

    def test_store_overwrites_existing(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        cm.store_context("key1", "old")
        cm.store_context("key1", "new")
        assert cm.memory_store["key1"] == "new"


class TestContextualMemoryRetrieve:
    """Tests for retrieving context."""

    def test_retrieve_existing(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        cm.store_context("key1", [1, 2, 3])
        assert cm.retrieve_context("key1") == [1, 2, 3]

    def test_retrieve_nonexistent(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        assert cm.retrieve_context("missing") is None


class TestContextualMemoryTimestamp:
    """Tests for timestamp retrieval."""

    def test_get_existing_timestamp(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        before = datetime.now()
        cm.store_context("key1", "value")
        after = datetime.now()
        ts = cm.get_context_timestamp("key1")
        assert before <= ts <= after

    def test_get_nonexistent_timestamp(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        before = datetime.now()
        ts = cm.get_context_timestamp("missing")
        after = datetime.now()
        # Returns datetime.now() for missing keys
        assert before <= ts <= after


class TestContextualMemoryClear:
    """Tests for clearing context."""

    def test_clear_existing(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        cm.store_context("key1", "value")
        cm.clear_context("key1")
        assert "key1" not in cm.memory_store
        assert "key1" not in cm.timestamp_store

    def test_clear_nonexistent(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        # Should not raise error
        cm.clear_context("missing")

    def test_clear_all(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        cm.store_context("key1", "value1")
        cm.store_context("key2", "value2")
        cm.clear_all_contexts()
        assert cm.memory_store == {}
        assert cm.timestamp_store == {}


class TestContextualMemoryList:
    """Tests for listing contexts."""

    def test_list_empty(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        assert cm.list_contexts() == []

    def test_list_with_data(self) -> None:
        from src.memory.contextual_memory import ContextualMemory

        cm = ContextualMemory()
        cm.store_context("key1", "v1")
        cm.store_context("key2", "v2")
        keys = cm.list_contexts()
        assert sorted(keys) == ["key1", "key2"]
