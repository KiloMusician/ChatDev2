# AI Council Deliberation Terminal
# Shows votes, debates, consensus decisions

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

Write-Host "=== AI COUNCIL (Votes & Consensus) ===" -ForegroundColor Blue
Write-Host ""
Write-Host "Monitoring: state/logs/council_decisions.log" -ForegroundColor Yellow
Write-Host "Events: vote_started, vote_cast, consensus_reached, decision_final" -ForegroundColor Yellow
Write-Host ""

# Create council log if missing
$councilLog = ".\state\logs\council_decisions.log"
if (-not (Test-Path $councilLog)) {
    New-Item -ItemType File -Force -Path $councilLog | Out-Null
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | EVENT=council_started | AI Council session initialized" | Add-Content $councilLog
}

# Tail council decisions
Get-Content $councilLog -Wait -Tail 120
