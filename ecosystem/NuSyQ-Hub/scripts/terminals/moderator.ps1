# Moderator Gate Terminal
# Shows risk assessments, safety gates, compliance checks

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

Write-Host "=== MODERATOR GATE (Risk & Compliance) ===" -ForegroundColor Yellow
Write-Host ""
Write-Host "Monitoring: state/logs/moderator.log" -ForegroundColor Cyan
Write-Host "Events: risk_assessed, gate_passed, gate_blocked, escalation" -ForegroundColor Cyan
Write-Host ""

# Create moderator log if missing
$modLog = ".\state\logs\moderator.log"
if (-not (Test-Path $modLog)) {
    New-Item -ItemType File -Force -Path $modLog | Out-Null
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | EVENT=moderator_started | Moderator gate system initialized" | Add-Content $modLog
}

# Tail moderator log
Get-Content $modLog -Wait -Tail 120
