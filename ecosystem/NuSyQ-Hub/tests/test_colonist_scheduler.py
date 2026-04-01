from src.orchestration.colonist_scheduler import Agent, Scheduler, Task


def test_basic_assignment():
    s = Scheduler()
    s.register_agent(
        Agent(id="a1", skills={"coding": 7}, preferences={"coding": 1}, capabilities=[])
    )
    s.register_agent(
        Agent(id="a2", skills={"coding": 5}, preferences={"coding": 2}, capabilities=[])
    )

    s.enqueue_task(Task(id="t1", priority=10, skill_req="coding", min_skill=6))
    s.enqueue_task(Task(id="t2", priority=5, skill_req="coding", min_skill=4))

    assigned = s.assign_once()
    # Expect t1 assigned to a1 (skill 7 >=6) and t2 assigned to a2
    mapping = {t.id: (a.id if a else None) for t, a in assigned}
    assert mapping["t1"] == "a1"
    assert mapping["t2"] in {"a2", "a1"}  # second could be requeued if agent busy
