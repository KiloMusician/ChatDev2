"""Tests for Unified AI Context Manager."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_db():
    """Fixture to create temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_context.db"


@pytest.fixture
def context_manager(temp_db):
    """Fixture to create context manager with temporary database."""
    from src.integration.unified_ai_context_manager import (
        UnifiedAIContextManager,
    )

    manager = UnifiedAIContextManager(db_path=temp_db)
    yield manager
    # Cleanup: close all pooled connections before temp directory cleanup
    manager.close_all_connections()


def test_context_manager_initialization(context_manager):
    """Test that context manager initializes properly."""
    assert context_manager.db_path.exists()
    assert len(context_manager.system_contexts) >= 5  # At least 5 default systems


def test_add_context(context_manager):
    """Test adding context entry."""
    context_id = context_manager.add_context(
        content="Test context content",
        context_type="code",
        source_system="copilot",
        metadata={"file": "test.py"},
        tags=["test", "python"],
    )

    assert context_id is not None
    assert context_id.startswith("copilot_")


def test_get_context(context_manager):
    """Test retrieving context entry."""
    # Add context first
    context_id = context_manager.add_context(
        content="Test retrieval",
        context_type="conversation",
        source_system="claude",
    )

    # Retrieve it
    context = context_manager.get_context(context_id)

    assert context is not None
    assert context.id == context_id
    assert context.content == "Test retrieval"
    assert context.context_type == "conversation"
    assert context.source_system == "claude"


def test_get_context_cache(context_manager):
    """Test that context cache works."""
    context_id = context_manager.add_context(
        content="Cached content", context_type="code", source_system="ollama"
    )

    # First retrieval (from DB)
    context1 = context_manager.get_context(context_id, use_cache=False)

    # Second retrieval (from cache)
    context2 = context_manager.get_context(context_id, use_cache=True)

    assert context1.id == context2.id
    assert context_id in context_manager.context_cache


def test_get_contexts_by_type(context_manager):
    """Test retrieving contexts by type."""
    # Add multiple contexts of different types
    context_manager.add_context(content="Error 1", context_type="error", source_system="copilot")
    context_manager.add_context(content="Error 2", context_type="error", source_system="ollama")
    context_manager.add_context(content="Code 1", context_type="code", source_system="chatdev")

    # Retrieve error contexts
    error_contexts = context_manager.get_contexts_by_type("error")

    assert len(error_contexts) == 2
    assert all(c.context_type == "error" for c in error_contexts)


def test_get_contexts_by_system(context_manager):
    """Test retrieving contexts by system."""
    # Add contexts from different systems
    context_manager.add_context(
        content="From copilot", context_type="code", source_system="copilot"
    )
    context_manager.add_context(
        content="From copilot 2", context_type="code", source_system="copilot"
    )
    context_manager.add_context(content="From ollama", context_type="code", source_system="ollama")

    # Retrieve copilot contexts
    copilot_contexts = context_manager.get_contexts_by_system("copilot")

    assert len(copilot_contexts) == 2
    assert all(c.source_system == "copilot" for c in copilot_contexts)


def test_update_system_status(context_manager):
    """Test updating system status."""
    context_manager.update_system_status(
        system_name="copilot", status="active", current_task="Code generation"
    )

    system = context_manager.get_system_status("copilot")

    assert system is not None
    assert system.status == "active"
    assert system.current_task == "Code generation"


def test_update_system_with_output(context_manager):
    """Test adding output to system status."""
    context_manager.update_system_status(
        system_name="ollama",
        status="active",
        recent_output="Generated code successfully",
    )

    system = context_manager.get_system_status("ollama")

    assert system is not None
    assert len(system.recent_outputs) == 1
    assert system.recent_outputs[0] == "Generated code successfully"


def test_system_output_limit(context_manager):
    """Test that recent outputs are limited to 10."""
    # Add 15 outputs
    for i in range(15):
        context_manager.update_system_status(
            system_name="chatdev", status="active", recent_output=f"Output {i}"
        )

    system = context_manager.get_system_status("chatdev")

    # Should only keep last 10
    assert len(system.recent_outputs) == 10
    assert "Output 14" in system.recent_outputs


def test_get_all_system_statuses(context_manager):
    """Test retrieving all system statuses."""
    statuses = context_manager.get_all_system_statuses()

    assert len(statuses) >= 5  # At least 5 default systems
    assert "copilot" in statuses
    assert "ollama" in statuses
    assert "chatdev" in statuses
    assert "claude" in statuses
    assert "consciousness" in statuses


def test_create_context_link(context_manager):
    """Test creating relationships between contexts."""
    # Add two contexts
    id1 = context_manager.add_context(
        content="Error occurred", context_type="error", source_system="copilot"
    )
    id2 = context_manager.add_context(
        content="Solution applied", context_type="code", source_system="ollama"
    )

    # Create link
    context_manager.create_context_link(
        source_id=id1, target_id=id2, relationship_type="solution_for", strength=0.9
    )

    # Verify link exists (should not raise exception)
    assert True  # Link creation succeeded


def test_get_related_contexts(context_manager):
    """Test retrieving related contexts."""
    # Add contexts
    error_id = context_manager.add_context(
        content="Bug found", context_type="error", source_system="copilot"
    )
    solution_id = context_manager.add_context(
        content="Bug fixed", context_type="code", source_system="ollama"
    )

    # Create relationship
    context_manager.create_context_link(
        source_id=error_id, target_id=solution_id, relationship_type="solution_for"
    )

    # Get related contexts
    related = context_manager.get_related_contexts(error_id)

    assert len(related) >= 1
    assert any(c.id == solution_id for c in related)


def test_get_related_contexts_filtered(context_manager):
    """Test retrieving related contexts with filter."""
    # Add contexts
    main_id = context_manager.add_context(
        content="Main context", context_type="code", source_system="chatdev"
    )
    related1_id = context_manager.add_context(
        content="Related 1", context_type="code", source_system="ollama"
    )
    related2_id = context_manager.add_context(
        content="Related 2", context_type="code", source_system="copilot"
    )

    # Create relationships
    context_manager.create_context_link(main_id, related1_id, "caused_by")
    context_manager.create_context_link(main_id, related2_id, "related")

    # Get only "caused_by" relationships
    caused_by = context_manager.get_related_contexts(main_id, relationship_type="caused_by")

    assert len(caused_by) == 1
    assert caused_by[0].id == related1_id


def test_export_context_for_system(context_manager):
    """Test exporting context for specific system."""
    # Add contexts for copilot
    for i in range(3):
        context_manager.add_context(
            content=f"Copilot context {i}",
            context_type="code",
            source_system="copilot",
        )

    # Export
    export = context_manager.export_context_for_system("copilot")

    assert export["system"] == "copilot"
    assert export["context_count"] == 3
    assert len(export["contexts"]) == 3
    assert "system_status" in export


def test_export_context_with_type_filter(context_manager):
    """Test exporting context with type filter."""
    # Add contexts of different types
    context_manager.add_context(content="Code 1", context_type="code", source_system="ollama")
    context_manager.add_context(content="Code 2", context_type="code", source_system="ollama")
    context_manager.add_context(content="Error 1", context_type="error", source_system="ollama")

    # Export only code contexts
    export = context_manager.export_context_for_system("ollama", context_types=["code"])

    assert export["context_count"] == 2
    assert all(c["context_type"] == "code" for c in export["contexts"])


def test_context_with_metadata(context_manager):
    """Test context with metadata."""
    metadata = {"file": "test.py", "line": 42, "severity": "high"}

    context_id = context_manager.add_context(
        content="Error on line 42",
        context_type="error",
        source_system="copilot",
        metadata=metadata,
    )

    context = context_manager.get_context(context_id)

    assert context.metadata == metadata
    assert context.metadata["file"] == "test.py"
    assert context.metadata["line"] == 42


def test_context_with_tags(context_manager):
    """Test context with tags."""
    tags = ["python", "error", "syntax"]

    context_id = context_manager.add_context(
        content="Syntax error", context_type="error", source_system="claude", tags=tags
    )

    context = context_manager.get_context(context_id)

    assert context.tags == tags
    assert "python" in context.tags


def test_default_system_capabilities(context_manager):
    """Test that default systems have capabilities."""
    copilot = context_manager.get_system_status("copilot")
    ollama = context_manager.get_system_status("ollama")

    assert copilot is not None
    assert len(copilot.capabilities) > 0
    assert "code_completion" in copilot.capabilities

    assert ollama is not None
    assert len(ollama.capabilities) > 0
    assert "code_generation" in ollama.capabilities


def test_new_system_creation(context_manager):
    """Test creating status for new system."""
    context_manager.update_system_status(
        system_name="custom_ai", status="active", current_task="Custom task"
    )

    system = context_manager.get_system_status("custom_ai")

    assert system is not None
    assert system.system_name == "custom_ai"
    assert system.status == "active"


def test_global_context_manager():
    """Test global context manager singleton."""
    from src.integration.unified_ai_context_manager import (
        get_unified_context_manager,
    )

    manager1 = get_unified_context_manager()
    manager2 = get_unified_context_manager()

    # Should return same instance
    assert manager1 is manager2
