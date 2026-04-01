#Requires -Version 5.1
<#
.SYNOPSIS
    Register (or remove) an Ollama auto-start task in Windows Task Scheduler.

.DESCRIPTION
    Creates a logon-triggered task under NuSyQ\OllamaAutoStart that runs
    `ollama serve` silently on user logon, so Ollama is always available
    without manual intervention.

    This directly addresses the "Ollama offline on startup" failure mode.

.PARAMETER Remove
    If specified, unregisters the task instead of creating it.

.PARAMETER OllamaPath
    Full path to ollama.exe. Auto-detected if omitted.

.EXAMPLE
    .\ensure_ollama_startup.ps1            # Register startup task
    .\ensure_ollama_startup.ps1 -Remove    # Unregister
#>

param(
    [switch]$Remove,
    [string]$OllamaPath = ""
)

$TaskFolder  = "NuSyQ"
$TaskName    = "OllamaAutoStart"
$FullTaskPath = "\$TaskFolder\$TaskName"

# ── Helper ────────────────────────────────────────────────────────────────────
function Write-Status([string]$msg, [string]$color = "Cyan") {
    Write-Host "  $msg" -ForegroundColor $color
}

function Find-Ollama {
    # 1. Explicit path
    if ($OllamaPath -and (Test-Path $OllamaPath)) { return $OllamaPath }

    # 2. PATH
    $fromPath = Get-Command ollama -ErrorAction SilentlyContinue
    if ($fromPath) { return $fromPath.Source }

    # 3. Known install location
    $known = "$env:LOCALAPPDATA\Programs\Ollama\ollama.EXE"
    if (Test-Path $known) { return $known }

    return $null
}

# ── Remove mode ───────────────────────────────────────────────────────────────
if ($Remove) {
    Write-Host "=== Removing Ollama Auto-Start Task ===" -ForegroundColor Yellow
    $existing = Get-ScheduledTask -TaskPath "\$TaskFolder\" -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskPath "\$TaskFolder\" -TaskName $TaskName -Confirm:$false
        Write-Status "Task '$FullTaskPath' removed." "Green"
    } else {
        Write-Status "Task '$FullTaskPath' was not registered — nothing to remove." "Gray"
    }
    exit 0
}

# ── Register mode ─────────────────────────────────────────────────────────────
Write-Host "=== Ollama Auto-Start Task Setup ===" -ForegroundColor Cyan

# Locate ollama.exe
$exe = Find-Ollama
if (-not $exe) {
    Write-Host "[ERROR] Could not locate ollama.exe. Pass -OllamaPath explicitly." -ForegroundColor Red
    Write-Host "  e.g.  .\ensure_ollama_startup.ps1 -OllamaPath 'C:\Program Files\Ollama\ollama.exe'"
    exit 1
}
Write-Status "Found Ollama: $exe"

# Check if already registered
$existing = Get-ScheduledTask -TaskPath "\$TaskFolder\" -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Status "Task '$FullTaskPath' already registered." "Green"
    Write-Status "State: $($existing.State)"
    Write-Host ""
    Write-Host "  To update, run -Remove first, then re-run this script." -ForegroundColor DarkGray
    exit 0
}

# Create the task folder if needed
try {
    $svc = New-Object -ComObject Schedule.Service
    $svc.Connect()
    $root = $svc.GetFolder("\")
    try { $root.GetFolder($TaskFolder) } catch {
        Write-Status "Creating task folder: \$TaskFolder"
        $root.CreateFolder($TaskFolder) | Out-Null
    }
} catch {
    Write-Status "Could not create task folder (may need admin). Continuing..." "Yellow"
}

# Build the task
$action  = New-ScheduledTaskAction -Execute $exe -Argument "serve"
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0) `  # No time limit
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited   # Does NOT need admin

$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Auto-start Ollama on logon so it's always available for NuSyQ-Hub agents. Registered by ensure_ollama_startup.ps1"

Register-ScheduledTask `
    -TaskPath "\$TaskFolder\" `
    -TaskName $TaskName `
    -InputObject $task `
    -Force | Out-Null

# Verify
$registered = Get-ScheduledTask -TaskPath "\$TaskFolder\" -TaskName $TaskName -ErrorAction SilentlyContinue
if ($registered) {
    Write-Status "Task registered successfully!" "Green"
    Write-Status "Path: $FullTaskPath"
    Write-Status "Trigger: On logon for $env:USERNAME"
    Write-Status "Action: $exe serve"
    Write-Host ""
    Write-Host "  Ollama will now auto-start on every logon." -ForegroundColor Green
    Write-Host "  Start now (without rebooting):" -ForegroundColor DarkGray
    Write-Host "    Start-ScheduledTask -TaskPath '\$TaskFolder\' -TaskName '$TaskName'" -ForegroundColor White
    Write-Host ""
    Write-Host "  To remove: .\ensure_ollama_startup.ps1 -Remove" -ForegroundColor DarkGray
} else {
    Write-Host "[ERROR] Task registration failed — check Task Scheduler permissions." -ForegroundColor Red
    exit 1
}

# Optionally start immediately
Write-Host ""
$answer = Read-Host "Start Ollama now? [Y/n]"
if ($answer -ne "n" -and $answer -ne "N") {
    Write-Status "Starting Ollama..." "Yellow"
    Start-ScheduledTask -TaskPath "\$TaskFolder\" -TaskName $TaskName
    Start-Sleep -Seconds 3

    # Quick health check
    try {
        $r = Invoke-WebRequest "http://127.0.0.1:11434/api/tags" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        $count = ($r.Content | ConvertFrom-Json).models.Count
        Write-Status "Ollama online — $count model(s) loaded." "Green"
    } catch {
        Write-Status "Ollama starting (may take a few seconds to be ready)." "Yellow"
        Write-Status "Check: Invoke-WebRequest http://localhost:11434/api/tags" "DarkGray"
    }
}
