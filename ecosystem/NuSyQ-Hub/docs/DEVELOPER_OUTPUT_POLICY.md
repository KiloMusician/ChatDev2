# NuSyQ-Hub Developer Output & State Policy

## Purpose

To ensure the system remains lean, intelligent, and maintainable, all outputs
(reports, logs, docs, prototypes) must follow these principles:

---

## 1. Ephemeral State & On-Demand Reports

- **System state** (status, queues, agent health) must be kept in-memory, in a
  status file (e.g., `system_status.json`), or a lightweight DB.
- **Reports, markdown, and logs** should only be generated on explicit request
  or for audit/history—not on every run.
- **No static 'current state' markdowns** as proof of system health; use
  programmatic status checks.

## 2. Cleanup & Archival

- **Old reports/logs** must be pruned or archived. Use
  `scripts/cleanup_bloat.py` to keep only the most recent N per type.
- **Session logs, quest logs, and prototypes** must be archived or deleted after
  review, promotion, or a set retention period.
- **Logs** should be rotated and not accumulate indefinitely.

## 3. Graduation Protocol for Prototypes

- **Prototypes and stubs** in `prototypes/`, `WareHouse/`, or `testing_chamber/`
  must be reviewed and either promoted to canonical code or archived/deleted.
- **Incomplete or placeholder code** should not persist in the main codebase.

## 4. Documentation & Enforcement

- **Update this policy** as new output types or workflows are introduced.
- **All agents and developers** must follow these rules for any new scripts,
  tools, or modules.
- **Code review** must check for compliance with output/state policy.

## 5. Refactoring Guidance

- **Move toward service/stateful design:** Prefer in-memory or service-based
  state over static files.
- **Add CLI/agent commands** for on-demand report generation and state queries.
- **Implement cleanup/archival** for all outputs.

---

## See Also

- `scripts/cleanup_bloat.py` — for automated cleanup
- `src/system/status.py` — for system heartbeat/state
- `.github/copilot-instructions.md` and `AGENTS.md` — for agent/developer
  doctrine

---

**This policy is mandatory for all contributors and agents.**
