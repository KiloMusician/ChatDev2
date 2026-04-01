"""Small helper to enqueue a cycle from non-async contexts."""
from ecosystem.shared.task_queue import enqueue


def enqueue_cycle() -> dict:
    tid = enqueue("chug_cycle_trigger", repo="ecosystem", agent="chug_daemon", priority=1)
    return {"task_id": tid, "queued": True}
