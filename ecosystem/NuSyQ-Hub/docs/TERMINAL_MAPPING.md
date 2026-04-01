# Terminal Mapping (Suggested)

This mapping suggests which VS Code terminal names map to the TerminalManager
channels and what to display there.

| VS Code Terminal name       | Channel                         | Purpose                                                |
| --------------------------- | ------------------------------- | ------------------------------------------------------ |
| NuSyQ: Activate Ecosystem   | `NuSyQ: Activate Ecosystem`     | Orchestration actions and high-level activation logs   |
| PowerShell Extension / pwsh | `pwsh` / `PowerShell Extension` | Raw PowerShell agent outputs, local PS sessions        |
| Claude                      | `Claude`                        | Claude agent outputs and suggestions                   |
| Copilot                     | `Copilot`                       | Copilot-assisted actions and outputs                   |
| Codex                       | `Codex`                         | Codex/LLM code generation outputs                      |
| ChatDev                     | `ChatDev`                       | ChatDev multi-agent outputs                            |
| AI Council                  | `AI Council`                    | Aggregated high-level decisions                        |
| Intermediary                | `Intermediary`                  | Message router / intermediary logs                     |
| Errors                      | `Errors`                        | All errors, machine-readable JSON (primary error sink) |
| Suggestions                 | `Suggestions`                   | Non-critical suggestions / improvements                |
| Tasks                       | `Tasks`                         | Task assignments, job starts/completions               |
| Tests                       | `Tests`                         | Test runner outputs (also link to TAP/JSON logs)       |
| Zeta                        | `Zeta`                          | ZETA pipeline job outputs                              |
| Agents                      | `Agents`                        | Agent lifecycle and heartbeats                         |
| Metrics                     | `Metrics`                       | Health checks and metric summaries                     |
| Anomalies                   | `Anomalies`                     | Detected anomalies / security events                   |
| Main                        | `Main`                          | General orchestrator info                              |
| Future                      | `Future`                        | Experimental / future channels                         |

Notes

- Channels are created on first use; TerminalManager writes logs under
- `data/terminal_logs/<channel_slug>.log` (names are normalized lower-case,
- e.g., `ai_council`, `errors`, `tasks`).
- Use `scripts/emit_terminal.py` as a portable wrapper for shell-based systems
  to write into channels.
- Consider pinning a dedicated terminal panel per critical channel (Errors,
  Tasks, Tests, Agents) in VS Code.
