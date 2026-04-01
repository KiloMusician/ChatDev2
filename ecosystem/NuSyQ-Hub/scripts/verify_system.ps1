#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Reality-Anchored System Verification Script
.DESCRIPTION
    Verifies MCP server health, environment variables, and path resolution.
    Outputs actionable next steps based on actual system state.
#>

param(
    [switch]$Fix,  # Attempt to fix issues automatically
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

Write-Host "🔍 TRIPARTITE SYSTEM VERIFICATION" -ForegroundColor Cyan
Write-Host "=" * 70

# Get absolute paths for the three repos
$HubPath = Split-Path -Parent $PSScriptRoot
$SimulatedVersePath = $null
$NuSyQPath = $null

# Try to find SimulatedVerse
$SimVerseGuesses = @(
    "C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse",
    "$($HubPath)\..\SimulatedVerse\SimulatedVerse",
    "$($HubPath)\..\..\SimulatedVerse\SimulatedVerse"
)

foreach ($path in $SimVerseGuesses) {
    if (Test-Path $path) {
        $SimulatedVersePath = Resolve-Path $path
        break
    }
}

# Try to find NuSyQ
$NuSyQGuesses = @(
    "C:\Users\keath\NuSyQ",
    "$($HubPath)\..\NuSyQ",
    "$($HubPath)\..\..\NuSyQ"
)

foreach ($path in $NuSyQGuesses) {
    if (Test-Path $path) {
        $NuSyQPath = Resolve-Path $path
        break
    }
}

# PHASE 1: PATH RESOLUTION
Write-Host "`n📁 PHASE 1: Repository Path Resolution" -ForegroundColor Yellow

$PathStatus = @{
    Hub = @{Path = $HubPath; Found = $true; HasPython = (Test-Path "$HubPath\src")}
    SimulatedVerse = @{Path = $SimulatedVersePath; Found = ($null -ne $SimulatedVersePath); HasPython = $false}
    NuSyQ = @{Path = $NuSyQPath; Found = ($null -ne $NuSyQPath); HasPython = $false}
}

if ($SimulatedVersePath) {
    $PathStatus.SimulatedVerse.HasPython = (
        (Test-Path "$SimulatedVersePath\src") -or
        (Test-Path "$SimulatedVersePath\core")
    )
}

if ($NuSyQPath) {
    $PathStatus.NuSyQ.HasPython = (
        (Test-Path "$NuSyQPath\src") -or
        (Test-Path "$NuSyQPath\mcp_server")
    )
}

foreach ($repo in $PathStatus.Keys) {
    $status = $PathStatus[$repo]
    $icon = if ($status.Found -and $status.HasPython) { "✅" }
            elseif ($status.Found) { "⚠️ " }
            else { "❌" }

    Write-Host "  $icon $repo"
    if ($status.Found) {
        Write-Host "     Path: $($status.Path)" -ForegroundColor Gray
        Write-Host "     Python: $($status.HasPython)" -ForegroundColor Gray
    } else {
        Write-Host "     NOT FOUND" -ForegroundColor Red
    }
}

# PHASE 2: ENVIRONMENT VARIABLES
Write-Host "`n🌍 PHASE 2: Environment Variables" -ForegroundColor Yellow

$EnvVars = @{
    SIMULATEDVERSE_ROOT = $env:SIMULATEDVERSE_ROOT
    NUSYQ_ROOT = $env:NUSYQ_ROOT
    NUSYQ_RUN_ID = $env:NUSYQ_RUN_ID
}

$EnvStatus = @{}
foreach ($var in $EnvVars.Keys) {
    $val = $EnvVars[$var]
    $EnvStatus[$var] = @{
        Set = ($null -ne $val -and $val -ne "")
        Value = $val
    }

    $icon = if ($EnvStatus[$var].Set) { "✅" } else { "❌" }
    Write-Host "  $icon $var"
    if ($EnvStatus[$var].Set) {
        Write-Host "     $val" -ForegroundColor Gray
    } else {
        Write-Host "     NOT SET" -ForegroundColor Red
    }
}

# PHASE 3: MCP SERVER HEALTH
Write-Host "`n🚀 PHASE 3: MCP Server Health" -ForegroundColor Yellow

$MCPHealthy = $false
$MCPPort = 3000
$MCPEndpoint = "http://localhost:$MCPPort/health"

try {
    $response = Invoke-RestMethod -Uri $MCPEndpoint -TimeoutSec 2 -ErrorAction Stop
    $MCPHealthy = $true
    Write-Host "  ✅ MCP Server HEALTHY" -ForegroundColor Green
    Write-Host "     $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ MCP Server NOT RESPONDING" -ForegroundColor Red
    Write-Host "     Endpoint: $MCPEndpoint" -ForegroundColor Gray
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Red
}

# PHASE 4: PYTHON ENVIRONMENT
Write-Host "`n🐍 PHASE 4: Python Environments" -ForegroundColor Yellow

$PythonStatus = @{}

# Check Hub Python
if (Test-Path "$HubPath\.venv\Scripts\python.exe") {
    $PythonStatus.Hub = "✅ .venv found"
} else {
    $PythonStatus.Hub = "❌ No .venv"
}

# Check NuSyQ Python
if ($NuSyQPath -and (Test-Path "$NuSyQPath\.venv\Scripts\python.exe")) {
    $PythonStatus.NuSyQ = "✅ .venv found"
} else {
    $PythonStatus.NuSyQ = "❌ No .venv"
}

foreach ($repo in $PythonStatus.Keys) {
    Write-Host "  $($PythonStatus[$repo]) $repo"
}

# SUMMARY
Write-Host "`n📊 SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 70

$AllGood = $PathStatus.Hub.Found -and $PathStatus.Hub.HasPython -and
           $PathStatus.SimulatedVerse.Found -and
           $PathStatus.NuSyQ.Found -and $PathStatus.NuSyQ.HasPython -and
           $EnvStatus.SIMULATEDVERSE_ROOT.Set -and
           $EnvStatus.NUSYQ_ROOT.Set -and
           $MCPHealthy

if ($AllGood) {
    Write-Host "✅ ALL SYSTEMS OPERATIONAL" -ForegroundColor Green
    Write-Host "`nNext Step: Run error report"
    Write-Host "  python scripts\start_nusyq.py error_report --force" -ForegroundColor Cyan
} else {
    Write-Host "⚠️  ISSUES DETECTED - Follow steps below" -ForegroundColor Yellow

    # ACTIONABLE FIXES
    Write-Host "`n🔧 REQUIRED ACTIONS:" -ForegroundColor Yellow

    if (-not $EnvStatus.SIMULATEDVERSE_ROOT.Set -and $SimulatedVersePath) {
        Write-Host "`n1. Set SIMULATEDVERSE_ROOT environment variable:"
        Write-Host "   [Environment]::SetEnvironmentVariable('SIMULATEDVERSE_ROOT', '$SimulatedVersePath', 'User')" -ForegroundColor Cyan
    }

    if (-not $EnvStatus.NUSYQ_ROOT.Set -and $NuSyQPath) {
        Write-Host "`n2. Set NUSYQ_ROOT environment variable:"
        Write-Host "   [Environment]::SetEnvironmentVariable('NUSYQ_ROOT', '$NuSyQPath', 'User')" -ForegroundColor Cyan
    }

    if (-not $MCPHealthy -and $NuSyQPath) {
        Write-Host "`n3. Start MCP Server:"
        Write-Host "   cd $NuSyQPath" -ForegroundColor Cyan
        Write-Host "   .\.venv\Scripts\python.exe mcp_server\main.py" -ForegroundColor Cyan
        Write-Host "   OR use VS Code Task: Ctrl+Shift+P → Tasks: Run Task → 🚀 Start MCP Server" -ForegroundColor Gray
    }

    if (-not $PathStatus.SimulatedVerse.Found) {
        Write-Host "`n4. SimulatedVerse NOT FOUND at expected locations:"
        Write-Host "   Searched: $($SimVerseGuesses -join ', ')" -ForegroundColor Gray
        Write-Host "   Clone or specify correct path" -ForegroundColor Cyan
    }
}

# AUTO-FIX MODE
if ($Fix) {
    Write-Host "`n🔧 AUTO-FIX MODE ENABLED" -ForegroundColor Cyan

    if (-not $EnvStatus.SIMULATEDVERSE_ROOT.Set -and $SimulatedVersePath) {
        Write-Host "Setting SIMULATEDVERSE_ROOT=$SimulatedVersePath"
        [Environment]::SetEnvironmentVariable('SIMULATEDVERSE_ROOT', $SimulatedVersePath, 'User')
    }

    if (-not $EnvStatus.NUSYQ_ROOT.Set -and $NuSyQPath) {
        Write-Host "Setting NUSYQ_ROOT=$NuSyQPath"
        [Environment]::SetEnvironmentVariable('NUSYQ_ROOT', $NuSyQPath, 'User')
    }

    Write-Host "`n✅ Environment variables set. Restart terminal for changes to take effect."
}

$separator = "=" * 70
Write-Host "`n$separator"
