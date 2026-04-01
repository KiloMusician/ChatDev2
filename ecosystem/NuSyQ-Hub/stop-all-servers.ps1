#!/usr/bin/env pwsh
# NuSyQ Front-End Stop All Servers
# Version: 1.0.0

param(
    [switch]$Force
)

$SimulatedVersePort = 5000
$ChatDevPort = 8000
$ModularWindowPort = 8080

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Red
Write-Host "  NuSyQ Server Shutdown" -ForegroundColor Red
Write-Host "=========================================================" -ForegroundColor Red
Write-Host ""

Write-Host "[Check] Finding running servers..." -ForegroundColor Yellow

$portsToCheck = @(
    @{Port=$SimulatedVersePort; Name="SimulatedVerse"},
    @{Port=$ChatDevPort; Name="ChatDev Visualizers"},
    @{Port=$ModularWindowPort; Name="Modular Window"}
)

$runningServers = @()

foreach ($server in $portsToCheck) {
    $conn = Get-NetTCPConnection -LocalPort $server.Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        $runningServers += @{
            Name = $server.Name
            Port = $server.Port
            ProcessId = $conn.OwningProcess
            ProcessName = $proc.ProcessName
        }
        Write-Host "  RUNNING $($server.Name) (PID: $($conn.OwningProcess))" -ForegroundColor Green
    } else {
        Write-Host "  STOPPED $($server.Name)" -ForegroundColor Gray
    }
}

if ($runningServers.Count -eq 0) {
    Write-Host ""
    Write-Host "[Info] No servers are running" -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

if (-not $Force) {
    Write-Host ""
    Write-Host "[WARNING] About to stop $($runningServers.Count) server(s)" -ForegroundColor Yellow
    $confirm = Read-Host "Continue? (y/N)"
    if ($confirm -ne 'y') {
        exit 1
    }
}

Write-Host ""
Write-Host "[Stop] Stopping servers..." -ForegroundColor Red

$stopCount = 0
$errorCount = 0

foreach ($server in $runningServers) {
    Write-Host "  Stopping $($server.Name)..." -ForegroundColor Yellow
    try {
        Stop-Process -Id $server.ProcessId -Force
        Write-Host "  OK Stopped" -ForegroundColor Green
        $stopCount++
    } catch {
        Write-Host "  ERROR Failed" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host ""
Write-Host "[Verify] Checking shutdown..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

$stillRunning = @()
foreach ($server in $runningServers) {
    $conn = Get-NetTCPConnection -LocalPort $server.Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $stillRunning += $server.Name
        Write-Host "  WARNING $($server.Name) still running" -ForegroundColor Yellow
    } else {
        Write-Host "  OK $($server.Name) stopped" -ForegroundColor Green
    }
}

Write-Host ""
if ($stillRunning.Count -eq 0) {
    Write-Host "=========================================================" -ForegroundColor Green
    Write-Host "  All Servers Stopped Successfully" -ForegroundColor Green
    Write-Host "=========================================================" -ForegroundColor Green
} else {
    Write-Host "=========================================================" -ForegroundColor Yellow
    Write-Host "  Shutdown Completed with Issues" -ForegroundColor Yellow
    Write-Host "=========================================================" -ForegroundColor Yellow
}
Write-Host ""

exit $(if ($stillRunning.Count -gt 0 -or $errorCount -gt 0) { 1 } else { 0 })
