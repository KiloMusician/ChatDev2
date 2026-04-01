#!/usr/bin/env pwsh
# NuSyQ Front-End Orchestration - Start All Servers
# Version: 1.0.0

param(
    [switch]$Silent,
    [switch]$WaitForHealth
)

$HubRoot = $PSScriptRoot
$SimulatedVersePath = $env:SIMULATEDVERSE_PATH
if (-not $SimulatedVersePath) {
    $SimulatedVersePath = Join-Path $env:USERPROFILE "Desktop\SimulatedVerse\SimulatedVerse"
}

$ChatDevRoot = $env:CHATDEV_PATH
if (-not $ChatDevRoot) {
    $ChatDevRoot = $env:NUSYQ_ROOT_PATH
    if (-not $ChatDevRoot) {
        $ChatDevRoot = Join-Path $env:USERPROFILE "NuSyQ"
    }
    $ChatDevRoot = Join-Path $ChatDevRoot "ChatDev"
}
$ChatDevVisualizerPath = Join-Path $ChatDevRoot "visualizer"

$ModularWindowPath = Join-Path $HubRoot "web\modular-window-server"

$SimulatedVersePort = 5000
$ChatDevPort = 8000
$ModularWindowPort = 8080

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  NuSyQ Front-End Orchestration - Starting Servers" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

# Pre-flight checks
Write-Host "[Check] Verifying directories..." -ForegroundColor Yellow
$checks = @(
    @{Name="SimulatedVerse"; Path=$SimulatedVersePath},
    @{Name="ChatDev Visualizers"; Path=$ChatDevVisualizerPath},
    @{Name="Modular Window"; Path=$ModularWindowPath}
)

$allGood = $true
foreach ($check in $checks) {
    if (Test-Path $check.Path) {
        Write-Host "  OK $($check.Name)" -ForegroundColor Green
    } else {
        Write-Host "  ERROR $($check.Name) NOT FOUND" -ForegroundColor Red
        $allGood = $false
    }
}

if (-not $allGood) {
    Write-Host ""
    Write-Host "[ERROR] Pre-flight checks failed" -ForegroundColor Red
    exit 1
}

# Check ports
Write-Host ""
Write-Host "[Check] Port availability..." -ForegroundColor Yellow
$portsToCheck = @($SimulatedVersePort, $ChatDevPort, $ModularWindowPort)
$portsInUse = @()

foreach ($port in $portsToCheck) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "  WARNING Port $port already in use" -ForegroundColor Yellow
        $portsInUse += $port
    } else {
        Write-Host "  OK Port $port available" -ForegroundColor Green
    }
}

if ($portsInUse.Count -gt 0) {
    Write-Host ""
    Write-Host "[WARNING] Some ports in use. Run ./stop-all-servers.ps1 first" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne 'y') {
        exit 1
    }
}

# Start servers
Write-Host ""
Write-Host "[Start] Launching servers..." -ForegroundColor Cyan

if ($Silent) {
    Start-Process pwsh -ArgumentList "-NoProfile", "-Command", "Set-Location '$SimulatedVersePath'; npm run dev" -WindowStyle Hidden
    Start-Process pwsh -ArgumentList "-NoProfile", "-Command", "Set-Location '$ChatDevVisualizerPath'; python -m http.server $ChatDevPort" -WindowStyle Hidden
    Start-Process pwsh -ArgumentList "-NoProfile", "-Command", "Set-Location '$ModularWindowPath'; node server.js" -WindowStyle Hidden
} else {
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Set-Location '$SimulatedVersePath'; npm run dev"
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Set-Location '$ChatDevVisualizerPath'; python -m http.server $ChatDevPort"
    Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Set-Location '$ModularWindowPath'; node server.js"
}

# Start MCP adapter prototype
Write-Host "[Start] Launching MCP Agent Adapter (prototype)" -ForegroundColor Cyan
if (Test-Path "$PSScriptRoot\scripts\start_mcp_adapter.ps1") {
    Start-Process pwsh -ArgumentList "-NoProfile", "-Command", "Set-Location '$PSScriptRoot\scripts'; .\\start_mcp_adapter.ps1" -WindowStyle Hidden
    Write-Host "  Adapter start requested" -ForegroundColor Green
} else {
    Write-Host "  Adapter start script not found: $PSScriptRoot\scripts\start_mcp_adapter.ps1" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[Wait] Initializing (5 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

if ($WaitForHealth) {
    Write-Host ""
    & "$PSScriptRoot\health-check.ps1"
}

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Green
Write-Host "  All Servers Started" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:"
Write-Host "  SimulatedVerse:      http://localhost:$SimulatedVersePort"
Write-Host "  ChatDev Visualizers: http://localhost:$ChatDevPort/static/index.html"
Write-Host "  Modular Window:      http://localhost:$ModularWindowPort"
Write-Host ""
