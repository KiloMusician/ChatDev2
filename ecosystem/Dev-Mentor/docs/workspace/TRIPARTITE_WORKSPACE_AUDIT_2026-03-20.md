# Tripartite Workspace Audit - 2026-03-20

## Scope

This audit covered the active multi-repo VS Code workspace and the live Windows-side processes behind it:

- `C:\Users\keath\Dev-Mentor`
- `C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse`
- `C:\Users\keath\NuSyQ`
- `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub`

## Process Inventory

### Confirmed live

- `PID 34416`
  - `pwsh.exe`
  - VS Code PowerShell extension host (`Start-EditorServices`)
  - Source: `ms-vscode.powershell-2025.4.0`
  - Status: normal editor services host, not the interactive terminal

- `PID 20684`
  - `pwsh.exe`
  - VS Code integrated PowerShell terminal with shell integration
  - Status: normal interactive shell surface

- `PID 23436`
  - `node.exe`
  - SimulatedVerse native Windows server
  - Command: `server/index.ts` via `tsx`
  - Port: `5001` is listening
  - Status: unhealthy; TCP accepts connections but HTTP requests time out

### Not present at inspection time

- `PID 2812`
  - No active Windows process matched this PID during inspection
  - Most likely explanation: exited before inspection or stale reference

## Workspace Loader Findings

### Root cause chain

1. `C:\Users\keath\Documents\PowerShell\profile.ps1` invoked `workspace_loader.ps1` with `&`, so aliases/functions were created in child scope and discarded.
2. `workspace_loader.ps1` loaded `.env.workspace` literally and did not expand `${VAR}` references.
3. `PYTHON_HUB` pointed at a stale Hub venv path.
4. The custom `prompt` used the startup working directory instead of the current one.

### Fixes applied

- Profile now dot-sources the workspace loader so commands persist in-session.
- `.env.workspace` interpolation now expands nested `${VAR}` references.
- Hub venv target was updated from `.venv` to `.venv-adapter`.
- Loader now recalculates prompt context from the current location.
- Loader now rejects broken venv shims that are missing `pyvenv.cfg` and falls back to alternate interpreters.

### Current behavior after fix

- Working:
  - `cdhub`
  - `cdroot`
  - `cdverse`
  - `cdanchor`
  - `cdsrc`
  - `cdscripts`

- Partially working:
  - `show-state` reads the existing snapshot successfully

- Still blocked:
  - `start-system`
  - `error-report`

These now resolve as commands, but the underlying Hub Python execution path still does not produce a fresh snapshot/report in the current environment.

## SimulatedVerse Runtime Findings

### Current live state

- Native Windows server process is already running on `5001`.
- `Test-NetConnection 127.0.0.1:5001` succeeds.
- `Invoke-WebRequest http://127.0.0.1:5001/api/health -TimeoutSec 5` times out.
- Result: the process is alive but the HTTP surface is effectively hung.

### WSL boot attempts

- `npm run dev` in WSL initially failed with:
  - `ENOTSUP: operation not supported on socket ... tsx-0/...pipe`
- Setting `TMPDIR=/tmp TEMP=/tmp TMP=/tmp` avoids that immediate pipe error, but the server still does not bind from the WSL-side launch path.

### Native Windows boot attempts

- `npm run dev:minimal` from `powershell.exe` failed with:
  - `Could not determine Node.js install directory`

### Recoverable playthrough state

The most concrete recoverable game state found locally was:

- `saves/archive/auto-saves/1756429379794_auto_3c779036.json`
  - `tier: 1`
  - `energy: 5.339658485482117e+48`
  - pantheon entries: `Astra`, `Chronos`, `Logos`
  - unlocked flags:
    - `foundation.ready`
    - `bus.online`
    - `pantheon.visible`
    - `anchor.available`

Related receipts:

- `reports/protagonist_play_receipt.json`
- `reports/protagonist_gameplay.json`

### Practical conclusion

We can identify the last recoverable state, but we cannot continue the live web playthrough cleanly until the hung `5001` server is either repaired or replaced with a reliable boot path.

## Extension Master List

### Installed extension volume

- Total extension directories under `C:\Users\keath\.vscode\extensions`: `251`
- AI/assistant conflict candidates detected from installed IDs: `17`

### Repo recommendations

- `Dev-Mentor`
  - prefers: Copilot, Continue, Ruff, Docker, Dev Containers, GitLens, Godot
  - explicitly suppresses:
    - `visualstudioexptteam.vscodeintellicode`
    - old `ms-vscode.remote-containers`

- `NuSyQ`
  - prefers: Python, Pylance, Ruff, Continue, AIQuickFix, Docker, YAML, Prettier
  - warns against duplicate Ollama UI extensions
  - hard-codes a WindowsApps `pwsh.exe` path in workspace settings

- `NuSyQ-Hub`
  - prefers: Python, Pylance, Ruff, Copilot, Copilot Chat, Claude Code, Continue, GitLens, Error Lens, PowerShell, Todo Tree
  - explicitly marks many ChatGPT/Codeium/Ollama UI variants as unwanted
  - claims "243 extensions installed"; actual count on disk is now `251`

- `SimulatedVerse`
  - no local `extensions.json`
  - mostly tuned through `.vscode/settings.json`

### Conflict clusters

#### AI assistant overlap

Installed simultaneously:

- `github.copilot-chat`
- `anthropic.claude-code`
- `continue.continue`
- `codeium.codeium`
- `openai.chatgpt`
- `sourcegraph.cody-ai`
- `bito.bito`
- `feiskyer.chatgpt-copilot`
- `genieai.chatgpt-vscode`
- `ikasann-self.vscode-chat-gpt`
- `silasnevstad.gpthelper`
- `sixth.sixth-ai`
- `danielsanmedium.dscodegpt`

Recommendation:

- Keep the core triad:
  - `github.copilot`
  - `github.copilot-chat`
  - `anthropic.claude-code`
  - `continue.continue`
- Disable/remove the rest unless one has a unique required workflow.

#### Ollama UI duplication

Installed simultaneously:

- `10nates.ollama-autocoder`
- `chrisbunting.ollama-code-generator`
- `codeboss.ollama-ai-assistant`
- `desislavarashev.ollama-commit`
- `diegoomal.ollama-connection`
- `technovangelist.ollamamodelfile`

Recommendation:

- Keep one primary Ollama chat/UI layer plus `Continue`.
- Keep `technovangelist.ollamamodelfile` only if Modelfile editing is needed.

#### Stale/mismatched IDs and references

- Dev-Mentor recommends `godotengine.godot-tools`, but the installed Godot tool seen on disk is `geequlim.godot-tools`.
- Hub workflow file references IDs that may not match current installs:
  - `saul-mirone.claude-dev`
  - `ms-vscode.live-share`
  - `vsls-contrib.gistfs`
  - `ms-vscode.live-share-audio`
  - `hediet.debug-visualizer`
  - `hediet.vscode-debug-visualizer`
  - `gitkraken.gitkraken-client`
  - `huggingface.huggingface-vscode`

These are migration hazards because workflow docs/tasks may assume extensions that are not actually present.

## Migration Risks

### Highest risk

1. Mixed Windows/WSL startup assumptions for SimulatedVerse
   - Native Windows server is hung
   - WSL `tsx` startup is unreliable on mounted-path temp sockets

2. PowerShell path drift
   - Repo settings mix `C:\Program Files\PowerShell\7\pwsh.exe` and WindowsApps `pwsh.exe`

3. Extension sprawl
   - Too many overlapping chat/AI extensions increase command collisions, keybinding conflicts, and completion noise

4. Workflow drift
   - Docs reference extension/task ecosystems that no longer match installed reality

## Recommended Graceful Migration Path

1. Canonicalize PowerShell
   - Standardize on `C:\Program Files\PowerShell\7\pwsh.exe`
   - Remove WindowsApps-specific `pwsh.exe` paths from repo-local settings

2. Canonicalize SimulatedVerse boot
   - Pick one supported runtime:
     - Windows native only, or
     - WSL native only
   - Add a single health-checked launcher that fails fast if `/api/health` does not answer within 5s

3. Reduce assistant overlap
   - Keep one primary local-model surface and one primary cloud surface
   - Treat all other AI/chat extensions as optional and normally disabled

4. Create a real workspace modlist
   - One canonical file should declare:
     - required repos
     - required extensions
     - optional extensions
     - unwanted extensions
     - expected PowerShell path
     - expected Node/Python runtimes
     - expected ports

5. Reconcile workflow files with installed reality
   - Audit `.vscode/extension_workflows.yaml`
   - Remove or rename dead extension IDs

## Suggested Canonical Modlist Shape

Use one machine-readable manifest, for example:

```json
{
  "repos": [
    "Dev-Mentor",
    "SimulatedVerse",
    "NuSyQ",
    "NuSyQ-Hub"
  ],
  "requiredExtensions": [
    "github.copilot",
    "github.copilot-chat",
    "anthropic.claude-code",
    "continue.continue",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "ms-vscode.powershell"
  ],
  "optionalExtensions": [
    "eamodio.gitlens",
    "nguyenngoclong.terminal-keeper",
    "ms-azuretools.vscode-docker",
    "redhat.vscode-yaml"
  ],
  "unwantedExtensions": [
    "codeium.codeium",
    "openai.chatgpt",
    "sourcegraph.cody-ai",
    "bito.bito",
    "feiskyer.chatgpt-copilot",
    "genieai.chatgpt-vscode",
    "ikasann-self.vscode-chat-gpt",
    "silasnevstad.gpthelper",
    "sixth.sixth-ai",
    "danielsanmedium.dscodegpt",
    "10nates.ollama-autocoder",
    "chrisbunting.ollama-code-generator",
    "codeboss.ollama-ai-assistant",
    "desislavarashev.ollama-commit",
    "diegoomal.ollama-connection"
  ]
}
```

## Summary

The workspace is not failing because of a single broken process. It is drifting across four separate axes:

- PowerShell bootstrap drift
- Python runtime drift
- Windows/WSL runtime drift
- VS Code extension sprawl

The bootstrap layer is now materially better than before, but the full environment is still not "fully activated" because SimulatedVerse is hung on the live port and Hub reporting commands still do not emit fresh state from the current Python path.
