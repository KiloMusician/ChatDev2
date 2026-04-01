Phase 2 — Task Enforcement: design notes
======================================

Goal
----
Ensure agents operate inside an enforced task runtime so work is recorded, resumable, and machine-checkable.

Key concepts
------------
- Task: objective + machine-checkable completion criteria
- Run: a single execution attempt attached to a Task (logs, exit_code)
- Artifact: produced build/package recorded in DB
- Agent wrapper: proxies AI agent actions to require a Task context

Minimal enforcement model
------------------------
1. Agents must create or attach to a Task before mutating files.
2. Task creation records objective and metadata in `tasks` table.
3. Runs created by TaskManager capture stdout/stderr and exit code.
4. Completion criteria are either (a) exit_code == 0 and artifact registered, or (b) explicit verification script passes.

Integration points
------------------
- `src/task_runtime/agent_wrapper.py` — context manager for agent code (example usage provided).
- `src/tools/agent_task_router.py` — router now records agent-created tasks into DB (best-effort).
- `scripts/agent_adapter_example.py` — example adapter showing how to wrap agent actions.

Next steps
----------
1. Expand precondition checks (smart_search invoked, repo clean, tests pass).
2. Add postcondition verifiers (unit tests, smoke tests, artifact existence).
3. Integrate wrapper into agent orchestration flows and require task-id in agent calls.
4. Add RBAC/approval gates for high-impact tasks (DB flag `requires_approval`).
