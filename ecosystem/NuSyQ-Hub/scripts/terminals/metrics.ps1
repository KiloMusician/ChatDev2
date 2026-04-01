# Metrics & Health Monitor Terminal
# Shows system health, coverage, performance metrics

param(
    [switch]$Watch,
    [int]$IntervalSeconds = 10,
    [switch]$NoClear
)

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

$runMode = if ($Watch) { "WATCH" } else { "ONE-SHOT" }

do {
    if (-not $NoClear) { Clear-Host }
    Write-Host "=== METRICS & HEALTH MONITOR ===" -ForegroundColor Green
    Write-Host "Run Mode: $runMode" -ForegroundColor DarkGray
    Write-Host "Monitoring: spine health + test coverage + error trends" -ForegroundColor Yellow
    Write-Host ""

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "Snapshot: $timestamp" -ForegroundColor Cyan
    Write-Host ""

    # Spine health
    Write-Host "--- Spine Health -----------------------------------------------" -ForegroundColor Yellow
    if (Test-Path ".\state\reports\spine_health_snapshot.json") {
        $health = Get-Content ".\state\reports\spine_health_snapshot.json" | ConvertFrom-Json
        $color = if ($health.status -eq "GREEN") { "Green" } elseif ($health.status -eq "YELLOW") { "Yellow" } else { "Red" }
        Write-Host "  Status: $($health.status)" -ForegroundColor $color
        Write-Host "  Signals: $($health.signals | ConvertTo-Json -Compress)" -ForegroundColor Gray
    } else {
        Write-Host "  (spine_health_snapshot.json not found)" -ForegroundColor DarkGray
    }
    Write-Host ""

    # Error count trends
    Write-Host "--- Error Trends ----------------------------------------------" -ForegroundColor Yellow
    if (Test-Path ".\state\reports\unified_error_report_latest.json") {
        $errors = Get-Content ".\state\reports\unified_error_report_latest.json" | ConvertFrom-Json
        Write-Host "  Total Errors: $($errors.total_diagnostics)" -ForegroundColor $(if ($errors.total_diagnostics -eq 0) { "Green" } else { "Red" })
        Write-Host "  By Repo:" -ForegroundColor Gray
        $errors.by_repo.PSObject.Properties | ForEach-Object {
            Write-Host "    $($_.Name): $($_.Value)" -ForegroundColor White
        }
    } else {
        Write-Host "  (unified_error_report_latest.json not found)" -ForegroundColor DarkGray
    }
    Write-Host ""

    # Test coverage
    Write-Host "--- Test Coverage ---------------------------------------------" -ForegroundColor Yellow
    if (Test-Path ".\.coverage") {
        Write-Host "  Coverage data found (.coverage)" -ForegroundColor Green
        # Could parse coverage report here
    } else {
        Write-Host "  (no coverage data found)" -ForegroundColor DarkGray
    }

    if ($Watch) {
        Write-Host ""
        Write-Host "Refreshing in $IntervalSeconds`s... (Ctrl+C to stop)" -ForegroundColor DarkGray
        Start-Sleep -Seconds $IntervalSeconds
    } else {
        Write-Host ""
        Write-Host "One-shot complete. Re-run with -Watch for continuous refresh." -ForegroundColor DarkGray
    }
} while ($Watch)
