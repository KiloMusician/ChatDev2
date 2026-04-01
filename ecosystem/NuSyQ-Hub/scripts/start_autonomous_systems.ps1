#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start NuSyQ-Hub Autonomous Systems

.DESCRIPTION
    Activates the autonomous development loop with all connected subsystems:
    - Autonomous Monitor (detects issues)
    - Quantum Problem Resolver (auto-fixes)
    - PU Queue (task management)
    - Quest Engine (quest-driven development)
    - Multi-AI Orchestrator (agent coordination)

.PARAMETER Mode
    Operation mode: 'supervised' (default), 'overnight' (safe mode), or 'full' (autonomous)

.PARAMETER Interval
    Minutes between autonomous cycles (default: 30)

.PARAMETER Test
    Run integration tests instead of starting the loop

.EXAMPLE
    .\scripts\start_autonomous_systems.ps1
    Start in supervised mode with 30-minute intervals

.EXAMPLE
    .\scripts\start_autonomous_systems.ps1 -Mode overnight -Interval 60
    Start in overnight safe mode with 60-minute intervals

.EXAMPLE
    .\scripts\start_autonomous_systems.ps1 -Test
    Run integration tests
#>

param(
    [ValidateSet('supervised', 'overnight', 'full')]
    [string]$Mode = 'supervised',
    
    [int]$Interval = 30,
    
    [switch]$Test
)

$ErrorActionPreference = "Stop"

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🤖 NuSyQ-Hub Autonomous Systems" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.12+" -ForegroundColor Red
    exit 1
}

# Check if we're in NuSyQ-Hub root
if (-not (Test-Path "src/automation/autonomous_loop.py")) {
    Write-Host "❌ Not in NuSyQ-Hub root directory" -ForegroundColor Red
    Write-Host "   Current: $PWD" -ForegroundColor Yellow
    Write-Host "   Expected: .../NuSyQ-Hub/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Working Directory: $PWD" -ForegroundColor Green
Write-Host ""

if ($Test) {
    # Run integration tests
    Write-Host "🧪 Running autonomous system integration tests..." -ForegroundColor Yellow
    Write-Host ""
    
    python scripts/wire_autonomous_system.py --test-mode --cycles 1
    
    $exitCode = $LASTEXITCODE
    Write-Host ""
    
    if ($exitCode -eq 0) {
        Write-Host "✅ Integration tests passed!" -ForegroundColor Green
    } else {
        Write-Host "❌ Integration tests failed" -ForegroundColor Red
    }
    
    exit $exitCode
} else {
    # Start autonomous loop
    Write-Host "🚀 Starting Autonomous Loop" -ForegroundColor Yellow
    Write-Host "   Mode: $Mode" -ForegroundColor Cyan
    Write-Host "   Interval: $Interval minutes" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop gracefully" -ForegroundColor Yellow
    Write-Host ""
    
    # Prepare log file
    $logDir = "logs/autonomous_system"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $logFile = "$logDir/autonomous_loop_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
    
    Write-Host "📝 Logging to: $logFile" -ForegroundColor Cyan
    Write-Host ""
    
    # Start the loop (output to both console and log file)
    python -m src.automation.autonomous_loop `
        --interval $Interval `
        --mode $Mode `
        --max-tasks 3 2>&1 | Tee-Object -FilePath $logFile
}
