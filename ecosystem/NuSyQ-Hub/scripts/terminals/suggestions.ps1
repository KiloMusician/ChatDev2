# Suggestion Stream Terminal
# Shows ruff + mypy linting trends

param(
    [switch]$Watch,
    [int]$IntervalSeconds = 90,
    [switch]$NoClear
)

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

$runMode = if ($Watch) { "WATCH" } else { "ONE-SHOT" }
$ruffCmd = Get-Command ruff -ErrorAction SilentlyContinue
$mypyCmd = Get-Command mypy -ErrorAction SilentlyContinue

do {
    if (-not $NoClear) { Clear-Host }
    Write-Host "=== SUGGESTION STREAM (Ruff + Mypy) ===" -ForegroundColor Cyan
    Write-Host "Run Mode: $runMode" -ForegroundColor DarkGray
    Write-Host "Running: ruff check + mypy every $IntervalSeconds seconds" -ForegroundColor Yellow
    Write-Host ""

    $timestamp = Get-Date -Format "HH:mm:ss"

    Write-Host "--- Ruff (first 40 issues) ------------------------ [$timestamp]" -ForegroundColor Yellow
    if ($ruffCmd) {
        $ruffOutput = & $ruffCmd.Path check . 2>&1 | Select-Object -First 40
        if ($ruffOutput) {
            $ruffOutput | ForEach-Object { Write-Host $_ -ForegroundColor White }
        } else {
            Write-Host "  OK: No ruff issues found" -ForegroundColor Green
        }
    } else {
        Write-Host "  ruff not found in PATH for this PowerShell session" -ForegroundColor DarkGray
    }

    Write-Host ""
    Write-Host "--- Mypy (first 40 issues) ------------------------- [$timestamp]" -ForegroundColor Yellow
    if ($mypyCmd) {
        $mypyOutput = & $mypyCmd.Path . 2>&1 | Select-Object -First 40
        if ($mypyOutput) {
            $mypyOutput | ForEach-Object { Write-Host $_ -ForegroundColor White }
        } else {
            Write-Host "  OK: No mypy issues found" -ForegroundColor Green
        }
    } else {
        Write-Host "  mypy not found in PATH for this PowerShell session" -ForegroundColor DarkGray
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
