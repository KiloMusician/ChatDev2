# VS Code Extension Optimization Plan

Generated: 2025-12-27 Scope: Tri-Repository Workspace (NuSyQ-Hub,
SimulatedVerse, NuSyQ)

## High-Impact Optimizations

1. Enable Copilot advanced features (Labs/code actions) and integrate with Error
   Lens for auto-fix prompts.
2. Implement lazy loading for heavy extensions (Live Share, debug visualizers,
   Kubernetes) to reduce startup time.
3. Align Python tooling (Black/Isort/Mypy/Pylint/Ruff) with format-on-save and
   organize imports.
4. Unify GitLens usage with VS Code SCM and GitKraken CLI for consistent
   history/graphs.
5. Consolidate AI assistants; prefer Copilot + Claude + local Ollama bridges;
   disable duplicate ChatGPT frontends where overlapping.

## Medium-Impact Improvements

- Standardize Markdown tooling across repos (markdownlint + preview enhanced +
  mermaid).
- Rationalize icon/themes to reduce UI churn (material-icon-theme + one material
  theme).
- Strengthen security: SonarLint on-demand analyzers enabled; review extension
  telemetry settings.

## Low-Effort Fixes

- Update outdated extensions weekly; remove deprecated/duplicate functionality
  covered by core VS Code.
- Add keybindings for common actions: format, organize imports, run tests, AI
  explain.

## Action Items

- Create `.vscode/optimized_settings.json` (done in NuSyQ-Hub) and sync to other
  repos.
- Add `.vscode/extension_workflows.yaml` describing event chains.
- Run `scripts/extension_monitor.py` daily to collect active extension
  snapshots.
