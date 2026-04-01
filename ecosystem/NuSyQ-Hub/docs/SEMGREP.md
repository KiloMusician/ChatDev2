# Semgrep Integration and Login

This project supports Semgrep scanning and (optionally) the Semgrep Cloud API.
If your Semgrep-powered checks require a Semgrep API token, follow the steps
below.

1. Create or obtain a Semgrep API token from https://semgrep.dev/account or your
   organization's Semgrep Cloud admin.
2. Run the provided helper to store the token in the repository `.env` file:

```powershell
pwsh ./scripts/semgrep_set_token.ps1
```

3. For your current PowerShell session, export the token:

```powershell
$env:SEMGREP_API_TOKEN = '<your-token-here>'
```

4. Verify Semgrep can see the token (example):

```powershell
semgrep --config auto --strict --verbose
```

Notes

- Do NOT commit real tokens to source control. The `.env` file in this repo is a
  convenience placeholder; prefer CI secrets for automated runs.
- If you prefer, set the system/user environment variable via Windows `setx` or
  your shell profile.

Troubleshooting (hangs / slow scans)

- Prefer the minimal runner: `python scripts/run_semgrep_minimal.py`
- Ensure Semgrep is discoverable:
  - `where semgrep` (Windows) or `which semgrep` (Unix)
  - Or set `SEMGREP` to the full path of the semgrep executable
- If the VS Code Semgrep extension hangs:
  - Disable the experimental language server (`semgrep.useExperimentalLS=false`)
  - Keep `semgrep.scan.onlyGitDirty=true`
  - Reduce scope via `semgrep.scan.include` / `semgrep.scan.exclude`
