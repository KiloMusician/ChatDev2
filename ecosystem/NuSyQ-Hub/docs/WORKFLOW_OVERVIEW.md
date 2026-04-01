# Optimized Interaction Flow — NuSyQ-Hub

Purpose: Provide a single, ordered, actionable workflow that makes Copilot, ChatDev, Ollama, and human contributors more effective. Follow this sequence for routine maintenance, feature work, and agent-driven automation.

## High-level order of operations (canonical)

1. Prepare environment
   - Create/activate venv: `python -m venv .venv` → activate (`.venv\Scripts\Activate.ps1` on Windows).
   - Install deps: `pip install -r requirements.txt`.
   - Ensure `src/integration/settings.json` has `chatdev_path` or set `CHATDEV_PATH` env.

2. Local quick-scan (pre-work)
   - Run the repo maze scanner to find TODO/FIXME/BUG markers and produce a JSON summary:
     - Streaming (recommended):
       ```powershell
       python -m src.tools.run_and_capture python -m src.tools.maze_solver . --max-depth 8
       ```
     - Direct: `python -m src.tools.maze_solver . --max-depth 8`
   - Inspect `logs/maze_summary_*.json` for prioritized findings.

3. Ingest and generate workflow
   - Use the ingestion helper to create a `refactoring` workflow from the latest summary:
     ```powershell
     python -m src.orchestration.ingest_maze_summary
     ```
   - This creates a workflow in the Copilot-ChatDev bridge context and attaches findings.

4. Agent-driven triage
   - Launch ChatDev with the generated task (via `CopilotChatDevBridge.launch_collaborative_session` or local `chatdev_launcher` scripts).
   - Copilot provides inline code suggestions; ChatDev coordinates multi-agent analysis and proposes patches.
   - Use `run_and_capture` to keep full logs for agent consumption and debugging.

5. Review & apply
   - Patches proposed by agents are placed under `incoming/patches/*.diff`.
   - Use `review_and_apply_patch()` or `git apply` locally to review and apply patches.
   - Run `python scripts/lint_test_check.py` to validate changes.

6. Commit & merge
   - Commit using conventional message: `git commit -m "chore: tech-debt cleanup (auto)"`.
   - Push branch and open PR, tag with `docs/Checklists/COPILOT_CHATDEV_WORKFLOW.md` and `NIGHTLY_SCANNER_CI.md` items completed when relevant.

7. Nightly automation
   - GitHub Action (`.github/workflows/nightly_scan.yml`) runs the scanner daily and uploads `maze_summary` artifacts.
   - Orchestrator ingests summaries and can open PRs or file issues with agent proposals.

## Best practices for agents (Copilot / ChatDev / Ollama)

- Copilot: use for quick, context-aware edits in the editor. Respect `copilot_context.json` conventions (snake_case, markdown docs).
- ChatDev: use for higher-level planning, code reviews, multi-file refactors, and PR drafting.
- Ollama/local LLMs: use for experimentations and privacy-sensitive tasks. Keep deterministic prompts and seed artifacts from `logs/`.

## Practical tips

- Always run the scanner before major refactors to know the current technical debt surface.
- Use `run_and_capture` to produce a persistent log file that agents can read; agents should prefer `logs/maze_summary_*.json` for structured data.
- Keep `copilot_context.json` updated with domain keywords to bias suggestions.
- For large outputs, open the log file rather than expecting full terminal output in some UIs.

## Quick commands

- Stream scanner & capture log:
```powershell
python -m src.tools.run_and_capture python -m src.tools.maze_solver . --max-depth 8
```

- Ingest latest summary and create workflow:
```powershell
python -m src.orchestration.ingest_maze_summary
```

- Manually run bridge scan from Python:
```powershell
python - <<'PY'
from src.integration.copilot_chatdev_bridge import CopilotChatDevBridge
b = CopilotChatDevBridge(workspace_root='.')
res = b.run_scanner_and_capture(max_depth=8)
print(res)
PY
```

## Where agents look for artifacts

- Human-readable logs: `logs/run_capture_*.log` or `logs/maze_scan_*.log`
- Machine-readable summaries: `logs/maze_summary_*.json`
- Proposed patches: `incoming/patches/*.diff`

## Next growth items

- Add automated PR creation from `incoming/patches/` with draft PR metadata.
- Integrate `maze_summary` ingestion within `ai_coordinator` for automatic task creation.
- Add unit tests and small fixture repo for scanner validation in CI.

---

Keep this file as the single canonical workflow reference for contributors and agents.
