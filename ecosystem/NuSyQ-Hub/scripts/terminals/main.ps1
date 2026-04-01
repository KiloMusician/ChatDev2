# Main Terminal - Operator Console
# Shows: git status + recent reports + quest log tail

param(
    [switch]$Watch,
    [int]$IntervalSeconds = 5,
    [switch]$NoClear
)

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot

$runMode = if ($Watch) { "WATCH" } else { "ONE-SHOT" }
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
$questLogCandidates = @(
    ".\\src\\Rosetta_Quest_System\\quest_log.jsonl",
    ".\\quest_log.jsonl"
)

do {
    if (-not $NoClear) { Clear-Host }
    Write-Host "=== MAIN TERMINAL (Operator) ===" -ForegroundColor Cyan
    Write-Host "Run Mode: $runMode" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "--- Git Status -----------------------------------------------" -ForegroundColor Yellow
    if ($gitCmd) {
        try {
            & $gitCmd.Path -c status.submoduleSummary=false status -sb --untracked-files=no --ignore-submodules=all
        } catch {
            Write-Host "  git status failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  git not found in PATH for this PowerShell session" -ForegroundColor DarkGray
    }
    Write-Host ""

    Write-Host "--- Last 5 Commits -------------------------------------------" -ForegroundColor Yellow
    if ($gitCmd) {
        & $gitCmd.Path --no-pager log -5 --oneline --color=always
    } else {
        Write-Host "  (commit history unavailable: git missing)" -ForegroundColor DarkGray
    }
    Write-Host ""

    Write-Host "--- Recent Reports -------------------------------------------" -ForegroundColor Yellow
    if (Test-Path ".\state\reports\") {
        Get-ChildItem ".\state\reports\" -File -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 5 |
            ForEach-Object {
                $ago = (Get-Date) - $_.LastWriteTime
                Write-Host "  $($_.Name) " -NoNewline
                Write-Host "($([int]$ago.TotalMinutes)m ago)" -ForegroundColor DarkGray
            }
    } else {
        Write-Host "  (no reports found)" -ForegroundColor DarkGray
    }
    Write-Host ""

    Write-Host "--- Quest Log (tail) -----------------------------------------" -ForegroundColor Yellow
    $questLog = $questLogCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($questLog) {
        Get-Content $questLog -Tail 8 -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "  $_" -ForegroundColor White
        }
        Write-Host "  Source: $questLog" -ForegroundColor DarkGray
    } else {
        Write-Host "  (quest log not found in expected locations)" -ForegroundColor DarkGray
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
