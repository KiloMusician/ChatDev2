#!/usr/bin/env pwsh
param(
  [switch]$ForceInstall
)
Set-StrictMode -Version Latest

try {
  $root = Split-Path -Parent $MyInvocation.MyCommand.Path
  $canonical = Join-Path $root "Start-SimulatedVerse.ps1"
  if (-not (Test-Path $canonical)) {
    Write-Error "Canonical launcher missing: $canonical"
    exit 1
  }

  Write-Host "[INFO] Delegating to canonical launcher: $canonical"
  if ($ForceInstall) {
    & $canonical -ForceInstall
  } else {
    & $canonical
  }
  exit $LASTEXITCODE
} catch {
  Write-Error "Failed to delegate to canonical launcher: $_"
  exit 1
}
