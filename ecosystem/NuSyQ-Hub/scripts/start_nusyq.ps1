#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Wrapper for start_nusyq.py - Agent-invokable system state snapshot

.DESCRIPTION
    This PowerShell wrapper makes it easy for agents (Copilot/Claude) to invoke
    the Python snapshot orchestrator. It activates the venv automatically and
    provides clean output.

.PARAMETER Mode
    Operation mode: "normal" or "overnight"

.PARAMETER Output
    Custom output path (optional)

.EXAMPLE
    .\scripts\start_nusyq.ps1
    .\scripts\start_nusyq.ps1 -Mode overnight
#>

param(
    [ValidateSet("normal", "overnight")]
    [string]$Mode = "normal",

    [string]$Output = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent

# Activate venv if exists
$venvActivate = Join-Path $RepoRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
}

# Build Python command
$pythonCmd = @("python", "scripts\start_nusyq.py", "--mode", $Mode)
if ($Output) {
    $pythonCmd += @("--output", $Output)
}

# Run snapshot orchestrator
Push-Location $RepoRoot
try {
    & $pythonCmd[0] $pythonCmd[1..($pythonCmd.Length-1)]
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "`n✅ Snapshot complete. View: state\reports\current_state.md" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Snapshot failed with exit code $exitCode" -ForegroundColor Red
    }

    exit $exitCode
} finally {
    Pop-Location
}
