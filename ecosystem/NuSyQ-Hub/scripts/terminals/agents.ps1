# Agent Coordination Hub Terminal
# Shows inter-agent messages, task routing, coordination events

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

Write-Host "=== AGENT COORDINATION HUB (Event Bus) ===" -ForegroundColor Magenta
Write-Host ""
Write-Host "Monitoring: state/logs/agent_bus.log" -ForegroundColor Yellow
Write-Host "Events: task_routed, agent_assigned, work_completed, proof_validated" -ForegroundColor Yellow
Write-Host ""

# Create agent bus if missing
$busLog = ".\state\logs\agent_bus.log"
if (-not (Test-Path $busLog)) {
    New-Item -ItemType File -Force -Path $busLog | Out-Null
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | EVENT=bus_started | Agent coordination hub initialized" | Add-Content $busLog
}

# Tail the bus
Get-Content $busLog -Wait -Tail 150
