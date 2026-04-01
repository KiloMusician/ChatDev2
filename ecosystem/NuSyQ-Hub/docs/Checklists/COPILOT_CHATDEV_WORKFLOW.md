# Copilot + ChatDev Workflow Optimization Checklist

Purpose: Make Copilot and ChatDev interactions efficient, contextual, and actionable.

- [ ] Ensure `src/integration/settings.json` contains valid `chatdev_path` and `default_model`.
- [ ] Add `logs/maze_summary_*.json` ingestion point in `src/orchestration/ai_coordinator.py`.
- [ ] Create a scheduled task to run `src.tools.maze_solver` nightly and upload summary artifacts.
- [ ] Implement automatic creation of `refactoring` workflows from `maze_summary` files.
- [ ] Add `copilot_context.json` rules to prefer project conventions and file associations.
- [ ] Provide Copilot a single canonical onboarding prompt in `.github/` for new contributors.
- [ ] Add notebook demos showing how to use `CopilotChatDevBridge.scan_repository_for_treasures()`.
- [ ] Integrate `run_and_capture.py` into VS Code tasks for consistent log capture.
- [ ] Establish agent memory snapshots in `agent_output/` for Copilot/ChatDev to reference.
- [ ] Document recommended interaction patterns for human reviewers in `docs/`.
