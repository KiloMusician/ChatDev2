# Error Monitor Terminal
# Tails unified error report for real-time diagnostics

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

Write-Host "=== ERROR MONITOR (Live Tail) ===" -ForegroundColor Red
Write-Host ""
Write-Host "Monitoring: state/reports/unified_error_report_latest.md" -ForegroundColor Yellow
Write-Host "          + state/logs/errors.log" -ForegroundColor Yellow
Write-Host ""

# Create error log if missing
$errorLog = ".\state\logs\errors.log"
if (-not (Test-Path $errorLog)) {
    New-Item -ItemType File -Force -Path $errorLog | Out-Null
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | Error monitor started" | Add-Content $errorLog
}

# Primary: tail unified error report if exists
$reportPath = ".\state\reports\unified_error_report_latest.md"
if (Test-Path $reportPath) {
    Write-Host "Found report, tailing..." -ForegroundColor Green
    Get-Content $reportPath -Wait -Tail 100
} else {
    Write-Host "Report not found, tailing error log..." -ForegroundColor Yellow
    Get-Content $errorLog -Wait -Tail 100
}
