# ChatDev Live Terminal
# Streams ChatDev channel + state logs + job logs through NuSyQ terminal router.

param(
    [switch]$Watch,
    [int]$IntervalSeconds = 5,
    [switch]$NoClear
)

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

$repoPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$pythonCmd = $null
if (Test-Path $repoPython) {
    $pythonCmd = @{ Path = $repoPython; Name = "python.exe" }
} else {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
    }
}
if (-not $pythonCmd) {
    Write-Host "❌ python/py not found in PATH and no local .venv python detected" -ForegroundColor Red
    exit 1
}

if (-not $NoClear) { Clear-Host }
Write-Host "=== CHATDEV LIVE STREAM ===" -ForegroundColor Green
Write-Host "Source: terminals stream --focus=chatdev" -ForegroundColor DarkGray
Write-Host ""

$streamArgs = @(
    "scripts/start_nusyq.py",
    "terminals",
    "stream",
    "--focus=chatdev",
    "--lines=120"
)

if ($Watch) {
    $streamArgs += "--follow"
    $streamArgs += "--interval=$IntervalSeconds"
}

if ($pythonCmd.Name -ieq "py.exe" -or $pythonCmd.Name -ieq "py") {
    & $pythonCmd.Path "-3" @streamArgs
} else {
    & $pythonCmd.Path @streamArgs
}
exit $LASTEXITCODE
