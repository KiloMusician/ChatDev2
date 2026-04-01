#!/usr/bin/env pwsh
# Simple system verification - no fancy formatting

$ErrorActionPreference = "Continue"

Write-Host "=== TRIPARTITE SYSTEM VERIFICATION ==="
Write-Host ""

# Find repos
$HubPath = Split-Path -Parent $PSScriptRoot
$SimVerseGuesses = @(
    "C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse",
    "$($HubPath)\..\SimulatedVerse\SimulatedVerse"
)
$NuSyQGuesses = @(
    "C:\Users\keath\NuSyQ",
    "$($HubPath)\..\NuSyQ"
)

$SimulatedVersePath = $null
foreach ($path in $SimVerseGuesses) {
    if (Test-Path $path) {
        $SimulatedVersePath = Resolve-Path $path
        break
    }
}

$NuSyQPath = $null
foreach ($path in $NuSyQGuesses) {
    if (Test-Path $path) {
        $NuSyQPath = Resolve-Path $path
        break
    }
}

# Check paths
Write-Host "REPOSITORY PATHS:"
Write-Host "  Hub: $HubPath $(if (Test-Path "$HubPath\src") {'[OK]'} else {'[NO SRC]'})"
Write-Host "  SimulatedVerse: $(if ($SimulatedVersePath) {$SimulatedVersePath + ' [OK]'} else {'NOT FOUND'})"
Write-Host "  NuSyQ: $(if ($NuSyQPath) {$NuSyQPath + ' [OK]'} else {'NOT FOUND'})"
Write-Host ""

# Check environment variables
Write-Host "ENVIRONMENT VARIABLES:"
$SimVerseEnv = $env:SIMULATEDVERSE_ROOT
$NuSyQEnv = $env:NUSYQ_ROOT
$RunID = $env:NUSYQ_RUN_ID

Write-Host "  SIMULATEDVERSE_ROOT: $(if ($SimVerseEnv) {$SimVerseEnv} else {'NOT SET'})"
Write-Host "  NUSYQ_ROOT: $(if ($NuSyQEnv) {$NuSyQEnv} else {'NOT SET'})"
Write-Host "  NUSYQ_RUN_ID: $(if ($RunID) {$RunID} else {'NOT SET'})"
Write-Host ""

# Check MCP server
Write-Host "MCP SERVER:"
try {
    $response = Invoke-RestMethod -Uri "http://localhost:3000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "  Status: HEALTHY"
    Write-Host "  Response: $($response | ConvertTo-Json -Compress)"
}
catch {
    Write-Host "  Status: NOT RESPONDING"
    Write-Host "  Error: $($_.Exception.Message)"
}
Write-Host ""

# Summary
Write-Host "=== NEXT STEPS ==="
if (-not $SimVerseEnv -and $SimulatedVersePath) {
    Write-Host "1. Set SIMULATEDVERSE_ROOT:"
    Write-Host "   [Environment]::SetEnvironmentVariable('SIMULATEDVERSE_ROOT', '$SimulatedVersePath', 'User')"
}
if (-not $NuSyQEnv -and $NuSyQPath) {
    Write-Host "2. Set NUSYQ_ROOT:"
    Write-Host "   [Environment]::SetEnvironmentVariable('NUSYQ_ROOT', '$NuSyQPath', 'User')"
}
Write-Host "3. Start MCP server if not running:"
Write-Host "   cd $NuSyQPath"
Write-Host "   .\.venv\Scripts\python.exe mcp_server\main.py"
Write-Host ""
