# Get-ProcessesByCmdline and compact-output helpers

Two small PowerShell helpers to safely enumerate processes and reduce repeated
terminal output.

Files:

- `Get-ProcessesByCmdline.ps1` — enumerates Win32 processes and prints one JSON
  object per line with ProcessId, Name and CommandLine. Normalizes newlines so
  no output line begins with a leading dot token.
- `compact-output.ps1` — reads stdin and collapses consecutive identical lines,
  printing a `(repeated: N times)` marker when N>1.

## Examples

From the repository root (PowerShell):

pwsh -NoProfile -File .\scripts\pwsh_helpers\Get-ProcessesByCmdline.ps1 | pwsh
-NoProfile -File .\scripts\pwsh_helpers\compact-output.ps1

Or produce formatted table locally (JSON -> objects):

pwsh -NoProfile -Command ".\scripts\pwsh_helpers\Get-ProcessesByCmdline.ps1 |
ConvertFrom-Json | Format-Table -AutoSize"

## Notes

- Use `-Max N` to limit the number of processes queried (helpful on very large
  systems).
- These are diagnostics helpers — they do not change system state.
