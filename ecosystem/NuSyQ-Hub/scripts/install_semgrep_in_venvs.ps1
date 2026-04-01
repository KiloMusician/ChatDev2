#!/usr/bin/env pwsh
Set-StrictMode -Version Latest

Write-Host "Installing semgrep into known venv interpreters (if present)"

$candidates = @(
  'C:\Users\keath\NuSyQ\\.venv\\Scripts\\python.exe',
  'C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\\.venv\\Scripts\\python.exe',
  'C:\Users\keath\\.venv\\Scripts\\python.exe'
)

foreach ($p in $candidates) {
  Write-Host "--- Checking $p ---"
  if (Test-Path $p) {
    Write-Host "Found interpreter: $p"
    & $p -m pip install -U pip setuptools wheel
    if ($LASTEXITCODE -ne 0) { Write-Host 'pip upgrade encountered errors but continuing' }
    & $p -m pip install semgrep -q
    if ($LASTEXITCODE -eq 0) {
      Write-Host "installed semgrep into $p"
      try { & $p -m semgrep --version } catch { Write-Host 'semgrep run failed' }
    } else {
      Write-Host "semgrep install failed for $p"
    }
  } else {
    Write-Host "Not present: $p"
  }
}

Write-Host "If no venv had semgrep installed, consider using pipx: pipx install semgrep"
