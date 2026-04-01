# Nightly Scanner & Agent Ingestion Checklist

Purpose: Ensure repository scanner runs nightly, artifacts are stored, and agents ingest results.

- [ ] Add GitHub Action job `nightly: scan-tech-debt` to run `python -m src.tools.maze_solver . --max-depth 12`.
- [ ] Persist `logs/maze_summary_*.json` as build artifacts and upload to `agent_output/`.
- [ ] Add ingestion step in `src/orchestration/ai_coordinator.py` to read latest maze_summary and create issues or workflows.
- [ ] Notify agents (via `orchestration`) of new summary and allow them to propose patches.
- [ ] If patches are proposed, place them in `incoming/patches/` and create a PR draft automatically.
- [ ] Rotate logs older than 30 days to `logs/storage/`.
- [ ] Add tests to validate scanner behavior in CI (small repo snapshot fixture).
- [ ] Add a dashboard `docs/reports/tech_debt_summary.md` that aggregates counts weekly.
