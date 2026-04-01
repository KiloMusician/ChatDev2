# Test Runner Monitor Terminal
# Continuous verification loop with pass/fail tracking

param(
    [switch]$Watch,
    [int]$IntervalSeconds = 60,
    [switch]$NoClear
)

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

# Create test log if missing
$testLog = ".\state\logs\test_history.log"
if (-not (Test-Path $testLog)) {
    New-Item -ItemType File -Force -Path $testLog | Out-Null
}

$passCount = 0
$failCount = 0
$runMode = if ($Watch) { "WATCH" } else { "ONE-SHOT" }
$pytestCmd = Get-Command pytest -ErrorAction SilentlyContinue

do {
    if (-not $NoClear) { Clear-Host }
    Write-Host "=== TEST RUNNER MONITOR ===" -ForegroundColor Magenta
    Write-Host "Run Mode: $runMode" -ForegroundColor DarkGray
    Write-Host "Running: pytest -q every $IntervalSeconds seconds" -ForegroundColor Yellow
    Write-Host "Logging: state/logs/test_history.log" -ForegroundColor Yellow
    Write-Host ""

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    if (-not $pytestCmd) {
        Write-Host "[$timestamp] pytest not found in PATH for this PowerShell session" -ForegroundColor DarkGray
        if ($Watch) {
            Write-Host ""
            Write-Host "Next run in $IntervalSeconds`s... (Ctrl+C to stop)" -ForegroundColor DarkGray
            Start-Sleep -Seconds $IntervalSeconds
            continue
        }
        Write-Host ""
        Write-Host "One-shot complete. Re-run with -Watch for continuous refresh." -ForegroundColor DarkGray
        break
    }
    Write-Host "[$timestamp] Running tests..." -ForegroundColor Cyan

    # Run pytest
    $output = & $pytestCmd.Path -q 2>&1 | Out-String

    if ($LASTEXITCODE -eq 0) {
        $passCount++
        Write-Host "PASS (total passes: $passCount)" -ForegroundColor Green
        "$timestamp | PASS | Exit: $LASTEXITCODE | Streak: $passCount passes, $failCount fails" | Add-Content $testLog
    } else {
        $failCount++
        Write-Host "FAIL (total fails: $failCount)" -ForegroundColor Red
        "$timestamp | FAIL | Exit: $LASTEXITCODE | Streak: $passCount passes, $failCount fails" | Add-Content $testLog
        Write-Host $output -ForegroundColor Red
    }

    if ($Watch) {
        Write-Host ""
        Write-Host "Next run in $IntervalSeconds`s... (Ctrl+C to stop)" -ForegroundColor DarkGray
        Start-Sleep -Seconds $IntervalSeconds
    } else {
        Write-Host ""
        Write-Host "One-shot complete. Re-run with -Watch for continuous refresh." -ForegroundColor DarkGray
    }
} while ($Watch)
