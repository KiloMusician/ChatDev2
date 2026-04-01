# Copilot ↔ ChatDev Workflow

This guide explains how GitHub Copilot can call ChatDev to diagnose and fix problems in the repository.

## Overview
- Copilot provides real-time code suggestions.
- When deeper analysis is needed, it triggers ChatDev through the Copilot-ChatDev Bridge.
- ChatDev coordinates multi-agent debugging and returns patches or guidance.

## Order of Operations
1. Review `docs/Checklists/PROJECT_STATUS_CHECKLIST.md` for pending work.
2. Parse `src/Rosetta_Quest_System/quest_log.jsonl` to understand active quests.
3. Consult `config/ZETA_PROGRESS_TRACKER.json` to align with the current phase.
4. If the repository feels unstable, run `python src/diagnostics/system_health_assessor.py`.
5. Proceed with the workflow below.

## Step-by-Step
1. **Install prerequisites**
   - `pip install chatdev`
   - Ensure the Copilot extension is active in your editor.
2. **Launch the Copilot Agent Launcher**
   - Run `python src/scripts/copilot_agent_launcher.py review path/to/file`.
   - Copilot sends the context to ChatDev and waits for results.
   - ![Launcher screenshot placeholder](images/copilot_chatdev_step1.png)
3. **Review ChatDev's output**
   - ChatDev proposes fixes and saves artifacts under `agent_output/`.
   - Apply or refine the changes with Copilot.
   - ![ChatDev results screenshot placeholder](images/copilot_chatdev_step2.png)
4. **Commit and iterate**
   - Integrate the recommended changes and run tests.

## Fallback Behavior
- If the bridge is unavailable, the launcher prints manual steps and no ChatDev session is started.
- When enhanced collaboration fails, the integration manager falls back to a basic session.
- Offline? Run ChatDev separately and coordinate results manually.

## Optimization Hints
- Use OmniTag/MegaTag searches to gather context quickly.
- Keep quest log entries and checklist updates in sync after each commit.
- Record major actions in `docs/Agent-Sessions/SESSION_*.md` for traceability.

## Screenshot Notes
Screenshots are referenced for clarity; replace the placeholders with actual captures when documenting real sessions.
