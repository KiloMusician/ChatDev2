#!/usr/bin/env pwsh
<#
Interactive helper to set Semgrep API token for NuSyQ-Hub.
It will store the token in the repository `.env` file (creating or updating the SEMGREP_API_TOKEN entry).
Use this on Windows PowerShell or pwsh.
#>

Set-StrictMode -Version Latest

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$envPath = Join-Path $repoRoot '.env'

Write-Host "Semgrep token helper"
$token = Read-Host -Prompt 'Enter Semgrep API token (paste and press Enter)'
if (-not $token) { Write-Error 'No token entered — aborting.'; exit 1 }

if (Test-Path $envPath) {
  $content = Get-Content $envPath -Raw
  if ($content -match '^(SEMGREP_API_TOKEN=).*' -m) {
    $new = $content -replace '^(SEMGREP_API_TOKEN=).*', "SEMGREP_API_TOKEN=$token"
    Set-Content -Path $envPath -Value $new -Encoding UTF8
    Write-Host "Updated SEMGREP_API_TOKEN in $envPath"
  } else {
    Add-Content -Path $envPath -Value "`nSEMGREP_API_TOKEN=$token"
    Write-Host "Appended SEMGREP_API_TOKEN to $envPath"
  }
} else {
  "SEMGREP_API_TOKEN=$token" | Out-File -FilePath $envPath -Encoding UTF8
  Write-Host "Created $envPath with SEMGREP_API_TOKEN"
}

Write-Host "To use this token in the current PowerShell session run:`n`$env:SEMGREP_API_TOKEN='$token'`nOr restart your shell/IDE to pick up the .env file via your environment loader.`nIf you use CI, ensure the CI secret is configured in the pipeline settings instead of committing tokens to repo." -ForegroundColor Yellow
