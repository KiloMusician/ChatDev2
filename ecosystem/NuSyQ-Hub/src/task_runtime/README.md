NuSyQ Task Runtime
===================

Lightweight SQLite-backed task runtime for NuSyQ. Provides:

- `Database` (migration + connection)
- `TaskModel` (create/list/update tasks, runs, artifacts)
- `TaskManager` (start a run, capture logs, update task status)
- CLI: `scripts/nusyq_task.py` (create/list/start tasks)

Quick start
-----------

1. Initialize DB and seed a sample project:

```powershell
python scripts/init_db.py
```

2. Migrate existing quest log (if present):

```powershell
python scripts/migrate_quest_log.py
```

3. Create a task and run a command under it:
4. Migrate model registry and artifacts (optional):

```powershell
python scripts/migrate_models_and_artifacts.py
```


```powershell
python scripts/nusyq_task.py create "Build Windows EXE"
python scripts/nusyq_task.py start 1 --cmd "echo hello"
```

Files
-----

- `src/task_runtime/db.py` — database connection & migrations
- `src/task_runtime/models.py` — ORM-like helpers
- `src/task_runtime/manager.py` — runtime manager to execute commands under tasks
- `scripts/nusyq_task.py` — CLI wrapper
