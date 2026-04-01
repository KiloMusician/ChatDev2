## Recommended VS Code Extensions for NuSyQ

This document summarizes recommended VS Code extensions and workspace settings
for development across the NuSyQ ecosystem.

Core extensions (highly recommended):

- GitHub.copilot — (used heavily across the workspace for AI suggestions and
  agentic flows)
- GitHub.copilot-chat — chat/agent surface for GitHub Copilot
- anthropic.claude-code — system-level coding agent integration
- ms-python.python — Python language support
- ms-python.vscode-pylance — Language server with type checking
- charliermarsh.ruff — Ruff linting (this repository uses Ruff as the primary
  linter; enable and prefer over Pylint)
- eamodio.gitlens — GitLens for enhanced git insights
- usernamehw.errorlens — Inline error visualization
- ms-toolsai.jupyter — Jupyter support for notebooks
- Continue.continue — Local LLM assistant integration (Continue.dev)

Optional/Advanced extensions:

- Fuzionix.devtool-plus — local JSON, YAML, Base64, UUID, hashing, and payload
  transformation tools directly in the editor
- hbenl.vscode-test-explorer — targeted test execution surface for faster local
  regression loops
- hediet.vscode-drawio — in-editor architecture/system diagrams
- ms-vsliveshare.vsliveshare — paired debugging/review sessions for editor-only
  issues
- SonarSource.sonarlint-vscode — SonarLint (useful for SonarQube rules; optional
  and may be overlap with Ruff)
- sourcery.sourcery — automated code suggestions (freemium) — optional
- PKief.material-icon-theme / RobbOwen.synthwave-vscode — UI/Theme packages
- oderwat.indent-rainbow — visual indent colors
- usernamehw.errorlens — inline errors display (already recommended)

Preferred AI stack

- Keep: `github.copilot`, `github.copilot-chat`, `anthropic.claude-code`,
  `continue.continue`
- Keep optional: `fuzionix.devtool-plus`
- Disable in focused coding profiles: `bito.bito`, `codeium.codeium`,
  `feiskyer.chatgpt-copilot`, `openai.chatgpt`
- Disable redundant Ollama UI extensions in focused coding profiles:
  `10nates.ollama-autocoder`, `chrisbunting.ollama-code-generator`,
  `codeboss.ollama-ai-assistant`, `desislavarashev.ollama-commit`,
  `diegoomal.ollama-connection`

Codex / Windsurf routing reality

- `openai.chatgpt` is the native OpenAI Codex extension. It can run inside WSL,
  but it is not a generic model-router for Ollama, LM Studio, ChatDev, or the
  rest of the NuSyQ local stack.
- `codeium.codeium` / Windsurf is a cloud assistant with indexing and completion
  settings. It does not expose a local-provider endpoint contract for Ollama or
  LM Studio in this workspace.
- For local/offline model routing in this ecosystem, use `continue.continue`,
  the NuSyQ bridges, and `scripts/start_nusyq.py` actions instead of trying to
  repoint Codex/Windsurf at local model backends they do not support.

Profile recommendation

- Use a dedicated `Codex-Isolation` profile for NuSyQ-Hub work.
- Keep the global profile broad if needed, but keep the focused profile trimmed.
- In that profile, pin DevTool+ tools that are directly useful to the system:
  JSON Editor, Base64 Encoder / Decoder, and UUID Generator.
- In WSL-heavy workflows, Chrome is preferred for DevTool+, but the workspace
  can use Windows Edge as a degraded fallback so browser automation remains
  discoverable instead of disappearing from routing/status reports.
- Use Test Explorer for focused `pytest` loops, Draw.io for architecture map
  updates, and Live Share only when a repro needs a paired editor session.

Docker compatibility note

- If Docker Desktop was recently upgraded, ensure VS Code Docker-related
  extensions are updated too (`ms-azuretools.vscode-docker`,
  `ms-vscode-remote.remote-containers`). Older extension builds can mis-handle
  Docker API changes and show stale errors.
- Prefer `ms-azuretools.vscode-docker` and disable legacy Docker extensions
  like `docker.docker` and `docker.docker-vscode-extension` if they are still
  installed.
- SonarLint local analysis uses a Docker `docker/lsp` image; if Docker is
  unstable, either update the extensions or disable SonarLint local mode and
  use SonarCloud/connected mode.

Key workspace settings you should be aware of (found in
.vscode/Settings/settings.json):

- python.linting.enabled: true
- python.linting.pylintEnabled: false # We prefer Ruff
- python.linting.ruffEnabled: true
- errorLens.enabled: true
- semgrep.useExperimentalLS: true
- semgrep.doHover: false
- semgrep.scan.onlyGitDirty: true
- editor.codeActions.triggerOnFocusChange: false

Semgrep latency notes

- If VS Code repeatedly shows `Getting code actions from 'Semgrep'`, the usual issue is provider churn, not a crash loop.
- Keep Semgrep bounded to `src`, dirty-only scanning, one job, explicit excludes, and the experimental LS.
- Keep `editor.codeActions.triggerOnFocusChange=false` in this workspace so VS Code does not keep re-querying code-action providers when focus changes.
- Prefer explicit quick-fix/save actions over broad focus-triggered code-action refresh in this repo.

Important security note

- Never store API keys in workspace files. Remove secrets from `.code-workspace`
  files and add them to `.env` or `config/secrets.json`. `*.code-workspace` is
  now ignored by the repo via `.gitignore`.

Quick setup if you prefer Ruff & Developer Tools

1. Install the recommended extensions (via `extensions.json` or package
   manager).
2. Add keys to `.env` or your OS secret manager.
3. Run:
   ```pwsh
   python -m pip install -r dev-requirements.txt
   code --install-extension charliermarsh.ruff
   code --install-extension eamodio.gitlens
   ```

Automated install (PowerShell)

1. Run the convenience script to perform dev setup and optionally install
   recommended extensions:

```pwsh
cd c:\Users\keath\Desktop\Legacy\NuSyQ-Hub
 pwsh -Command "& ./scripts/setup-dev.ps1 -InstallExtensions -InstallDevRequirements -AutoInstallLocalExtensions -InstallRecommendedOptional"
```

The script will:

- Install `dev-requirements.txt` packages (Ruff, Black, Pytest, etc.)
- Scan for `.vscode/extensions.json` files across the workspace root and install
  recommended extensions using the `code` CLI

Using the Dev Container (recommended)

1. Open the NuSyQ-Hub repository in VS Code and choose 'Dev Containers: Reopen in Container' from the Command Palette.
2. Container uses `Dockerfile` in `.devcontainer` and mounts your workspace in `/workspaces/NuSyQ-Hub`.
3. The container's `postCreateCommand` runs `.devcontainer/post-create.sh` which installs dev dependencies and prepares the `vscode-extension` local package for debugging.
4. To connect to host Ollama set the `OLLAMA_BASE_URL` to `http://host.docker.internal:11434` in `.devcontainer/.env` and restart the container.
5. If you'd like to run ChatDev inside the container, set `CHATDEV_PATH` to a workspace path containing the ChatDev installation or use host ChatDev with forwarded ports.


Local development extension (Ollama integration)

This repository includes a local extension in `vscode-extension` that provides
convenience commands and status for Ollama model selection and monitoring.

To use it in dev mode (recommended for extension debugging):

1. Open the `vscode-extension` folder in VS Code and press F5 to launch an
  Extension Development Host.
2. Optionally, package and install it using `npx vsce package` and
  `code --install-extension ./vscode-extension-<version>.vsix`.

The `scripts/install-vscode-extensions.ps1` script also supports `localRecommendations`
entries in `extensions.json`. If the extension is found under a `localRecommendations`
path, it will attempt to package & install it automatically (if `npm`/`vsce` are
available). Otherwise, the script prints manual install instructions.

Current local recommendations in this workspace:

- `../vscode-extension` — NuSyQ Copilot Bridge / control surface
- `../extensions/agent-dashboard` — NuSyQ Agent Dashboard

ChatDev

ChatDev is primarily script-based and not a single VS Code extension. We recommend
the following for ChatDev workflows:
- Terminal manager extension (e.g., `formulahendry.terminal`) and `ms-vscode-remote.remote-containers` for containerized ChatDev runs.
- Ensure `CHATDEV_PATH` is set in `.env` or via your OS env variables so the workspace tools can detect ChatDev.
- Use `src/integration/chatdev_launcher.py` and our `bootstrap_chatdev_pipeline.py` to integrate ChatDev with Ollama and to run multi-agent flows.

Notes

- SonarLint provides additional rules; use as-needed in code-smell sweeping jobs
  and not as the primary inline linter unless you want to keep the GitHub-based
  Sonar metrics.

If you'd like, I can add a `requirements-tracing.txt` to make it easy to install
OpenTelemetry packages for local tracing, or a `setup-dev.ps1` to install all
recommended extensions automatically in new dev environments.
