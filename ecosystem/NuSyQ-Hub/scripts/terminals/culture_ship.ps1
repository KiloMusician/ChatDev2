# Culture Ship Audit Terminal
# Shows proof gating, theater detection, audit results

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

Write-Host "=== CULTURE SHIP (Proof Gates & Theater Audits) ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitoring: state/logs/culture_ship_audits.log" -ForegroundColor Yellow
Write-Host "Events: proof_submitted, audit_started, theater_detected, proof_validated" -ForegroundColor Yellow
Write-Host ""

# Create culture ship log if missing
$auditLog = ".\state\logs\culture_ship_audits.log"
if (-not (Test-Path $auditLog)) {
    New-Item -ItemType File -Force -Path $auditLog | Out-Null
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | EVENT=audit_system_started | Culture Ship audit system initialized" | Add-Content $auditLog
}

# Tail audits
Get-Content $auditLog -Wait -Tail 120
