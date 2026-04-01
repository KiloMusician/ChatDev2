from src.Rosetta_Quest_System.quest_engine import QuestEngine
from src.utils.status_helpers import is_completed


def test_update_quest_status_normalizes():
    engine = QuestEngine()
    engine.quests.clear()
    engine.questlines.clear()

    qid = engine.add_quest("T", "D", "G")
    engine.update_quest_status(qid, "complete")
    q = engine.quests[qid]
    assert is_completed(q.status)
