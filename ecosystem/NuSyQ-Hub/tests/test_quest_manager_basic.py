"""Tests for Rosetta_Quest_System.QuestManager facade."""

from src.Rosetta_Quest_System.quest_manager import QuestManager


def test_quest_manager_instantiation():
    """QuestManager can be instantiated."""
    mgr = QuestManager()
    assert mgr is not None
    assert mgr.engine is not None


def test_list_questlines_returns_list():
    """list_questlines returns a list."""
    mgr = QuestManager()
    result = mgr.list_questlines()
    assert isinstance(result, list)


def test_list_quests_returns_list():
    """list_quests returns a list of dicts."""
    mgr = QuestManager()
    result = mgr.list_quests()
    assert isinstance(result, list)


def test_add_quest_and_retrieve():
    """add_quest creates a quest accessible via list_quests."""
    mgr = QuestManager()
    initial_count = len(mgr.list_quests())
    mgr.add_quest(
        title="Test Quest",
        description="A test quest",
        questline="test",
        tags=["test"],
    )
    assert len(mgr.list_quests()) == initial_count + 1


def test_update_quest_status():
    """update_quest_status changes quest status."""
    mgr = QuestManager()
    quest_id = mgr.add_quest(
        title="Status Quest",
        description="Quest for status testing",
        questline="test",
        tags=[],
    )
    mgr.update_quest_status(quest_id, "active")
    # Find the quest in list and check status
    quests = mgr.list_quests()
    match = next((q for q in quests if q.get("id") == quest_id), None)
    assert match is not None
    assert match["status"] == "active"
