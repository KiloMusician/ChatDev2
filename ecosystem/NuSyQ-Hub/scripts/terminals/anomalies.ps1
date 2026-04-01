# Anomaly Detection Terminal
# Shows unusual patterns, spikes, unexpected behaviors

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

Write-Host "=== ANOMALY DETECTION (Pattern Analysis) ===" -ForegroundColor Red
Write-Host ""
Write-Host "Monitoring: state/logs/anomalies.log" -ForegroundColor Yellow
Write-Host "Events: spike_detected, pattern_break, unexpected_behavior" -ForegroundColor Yellow
Write-Host ""

# Create anomaly log if missing
$anomalyLog = ".\state\logs\anomalies.log"
if (-not (Test-Path $anomalyLog)) {
    New-Item -ItemType File -Force -Path $anomalyLog | Out-Null
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | EVENT=detector_started | Anomaly detection system initialized" | Add-Content $anomalyLog
}

# Tail anomalies
Get-Content $anomalyLog -Wait -Tail 120
