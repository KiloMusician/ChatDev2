Colonist-style Scheduler

Quick summary

- `src/orchestration/colonist_scheduler.py` implements a minimal agent/task scheduler inspired by the RimWorld "colonist" concept.
- Agents have skills, preferences, capabilities, and state.
- Tasks have skill requirements, minimum skill, and priority.
- Scheduler assigns queued tasks (priority first) to available agents using a simple scoring function.

How to run

Activate your venv and run:

```powershell
python -m src.orchestration.colonist_scheduler
```

This prints a small demo assignment JSON.

Integration notes

- This module is lightweight and designed to be imported by higher-level orchestrators (e.g., `kilo_ai_orchestration_master.py`).
- Consider adding persistence, database-backed queues, or adaptive learning hooks depending on scale.
