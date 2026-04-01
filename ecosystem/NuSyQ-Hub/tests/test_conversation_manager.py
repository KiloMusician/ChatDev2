"""Unit tests for the lightweight conversation manager."""

"""
OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""


from src.ai.conversation_manager import ConversationManager


def test_create_and_fetch_history(tmp_path):
    """Messages added to a conversation can be retrieved in order."""
    storage = tmp_path / "conv.json"
    manager = ConversationManager(storage)

    manager.add_message("abc", "user", "hello")
    manager.add_message("abc", "assistant", "hi there")

    history = manager.get_history("abc")
    assert len(history) == 2
    assert history[0]["content"] == "hello"
    assert history[1]["role"] == "assistant"


def test_persistence(tmp_path):
    """Conversations are loaded from disk when a new manager is created."""
    storage = tmp_path / "conv.json"
    manager = ConversationManager(storage)
    manager.add_message("conv", "user", "persist me")

    reloaded = ConversationManager(storage)
    history = reloaded.get_history("conv")
    assert history and history[0]["content"] == "persist me"
