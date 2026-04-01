# NuSyQ Terminal Watcher Launcher
# Reads the terminal PID registry and prints the startup command for each
# assigned terminal.  Run this once to get the list of commands, then
# copy+paste each into the appropriate VS Code terminal tab.
#
# Usage:  & scripts\launch_terminal_watchers.ps1

$repoRoot = Split-Path $PSScriptRoot -Parent
$registryPath = Join-Path $repoRoot "state\terminal_pid_registry.json"

if (-not (Test-Path $registryPath)) {
    Write-Host "Registry not found. Run first:" -ForegroundColor Yellow
    Write-Host "  python scripts/start_nusyq.py terminals assign" -ForegroundColor Cyan
    exit 1
}

$registry = Get-Content $registryPath | ConvertFrom-Json

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   NuSyQ Terminal Watcher — Startup Commands                 ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run each command in its designated VS Code terminal tab:" -ForegroundColor Gray
Write-Host ""

$entries = $registry.entries | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
foreach ($role in $entries) {
    $entry = $registry.entries.$role
    $pid = $entry.pid
    $script = $entry.watcher_script
    $status = $entry.status

    $icon = if ($status -eq "active") { "●" } else { "○" }
    $color = if ($status -eq "active") { "Green" } else { "DarkGray" }

    Write-Host "$icon  [$role]  pid=$pid" -ForegroundColor $color
    if (Test-Path $script) {
        Write-Host "   & '$script'" -ForegroundColor White
    } else {
        $logFile = $entry.log_file
        Write-Host "   Get-Content -Wait -Tail 20 '$logFile'" -ForegroundColor White
    }
    Write-Host ""
}

Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host "Tip: Run 'python scripts/start_nusyq.py terminals emit' to" -ForegroundColor Gray
Write-Host "     send a test message to all terminals after starting watchers." -ForegroundColor Gray
Write-Host ""
