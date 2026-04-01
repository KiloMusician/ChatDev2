function Initialize-IdleInterop {
    if ("KeeperIdleInterop" -as [type]) {
        return
    }

    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class KeeperIdleInterop {
    [StructLayout(LayoutKind.Sequential)]
    public struct LASTINPUTINFO {
        public uint cbSize;
        public uint dwTime;
    }

    [DllImport("user32.dll")]
    public static extern bool GetLastInputInfo(ref LASTINPUTINFO plii);

    [DllImport("kernel32.dll")]
    public static extern ulong GetTickCount64();
}
"@ | Out-Null
}

function Get-IdleSeconds {
    try {
        Initialize-IdleInterop
        $info = New-Object KeeperIdleInterop+LASTINPUTINFO
        $info.cbSize = [uint32][System.Runtime.InteropServices.Marshal]::SizeOf($info)
        if (-not [KeeperIdleInterop]::GetLastInputInfo([ref]$info)) {
            return $null
        }

        $elapsedMs = [KeeperIdleInterop]::GetTickCount64() - [uint64]$info.dwTime
        return [math]::Max(0, [int]([math]::Floor($elapsedMs / 1000)))
    }
    catch {
        return $null
    }
}

function Get-SteamGameActivity {
    param([Parameter(Mandatory = $true)]$Settings)

    if (-not (Get-Command Get-ActiveSteamGames -ErrorAction SilentlyContinue)) {
        return [pscustomobject]@{
            roots     = @()
            processes = @()
            active    = $false
            games     = @()
        }
    }

    $steam = Get-ActiveSteamGames -Settings $Settings
    return [pscustomobject]@{
        roots     = @(Get-ObjectValue -Object $steam -Name "game_roots" -Default @())
        processes = @(Get-ObjectValue -Object $steam -Name "processes" -Default @())
        games     = @(Get-UniqueSteamGameSummaries -Processes @(Get-ObjectValue -Object $steam -Name "processes" -Default @()))
        active    = [bool](Get-ObjectValue -Object $steam -Name "active" -Default $false)
    }
}

function Get-AutomationPlan {
    param([Parameter(Mandatory = $true)]$Settings)

    $automationCfg = Get-ObjectValue -Object $Settings -Name "automation" -Default ([pscustomobject]@{})
    $idleThresholdSec = [int](Get-ObjectValue -Object $automationCfg -Name "idleThresholdSec" -Default 900)
    $modeWhenIdle = [string](Get-ObjectValue -Object $automationCfg -Name "modeWhenIdle" -Default "balanced")
    $modeWhenActiveDev = [string](Get-ObjectValue -Object $automationCfg -Name "modeWhenActiveDev" -Default "coding")
    $skipWhenGameRunning = [bool](Get-ObjectValue -Object $automationCfg -Name "skipWhenGameRunning" -Default $true)

    $recommendation = Get-ModeRecommendation -Settings $Settings
    $gameActivity = Get-SteamGameActivity -Settings $Settings
    $idleSeconds = Get-IdleSeconds

    $currentMode = [string](Get-ObjectValue -Object $recommendation -Name "current_mode" -Default "idle")
    $devDetected = (@(Get-ObjectValue -Object $recommendation -Name "active_dev_processes" -Default @()).Count -gt 0) `
        -or [bool](Get-ObjectValue -Object $recommendation -Name "wsl_active" -Default $false) `
        -or [bool](Get-ObjectValue -Object $recommendation -Name "docker_active" -Default $false)
    $gameDetected = [bool](Get-ObjectValue -Object $gameActivity -Name "active" -Default $false)

    $targetMode = $modeWhenIdle
    $reasons = @()
    $deferred = $false

    if ($gameDetected -and $skipWhenGameRunning) {
        $targetMode = $currentMode
        $deferred = $true
        $reasons += "A Steam game is running, so automation is deferring to manual gaming mode or the Steam listener."
    }
    elseif ($null -ne $idleSeconds -and $idleSeconds -ge $idleThresholdSec) {
        $targetMode = $modeWhenIdle
        $reasons += ("The system has been idle for {0} seconds, so automation prefers {1} mode." -f $idleSeconds, $modeWhenIdle)
    }
    elseif ($devDetected) {
        $targetMode = $modeWhenActiveDev
        $reasons += ("Active development workloads were detected, so automation prefers {0} mode." -f $modeWhenActiveDev)
    }
    else {
        $targetMode = $modeWhenIdle
        $reasons += ("No active dev workload was detected, so automation prefers {0} mode." -f $modeWhenIdle)
    }

    return [pscustomobject]@{
        generated_at          = (Get-Date).ToString("o")
        current_mode          = $currentMode
        target_mode           = $targetMode
        should_apply          = (-not $deferred -and -not [string]::Equals($currentMode, $targetMode, [System.StringComparison]::OrdinalIgnoreCase))
        deferred              = $deferred
        idle_seconds          = $idleSeconds
        idle_threshold_sec    = $idleThresholdSec
        dev_workload_active   = $devDetected
        game_active           = $gameDetected
        active_game_processes = @($gameActivity.processes | Select-Object -ExpandProperty ProcessName -Unique)
        active_games          = @($gameActivity.games | Select-Object -ExpandProperty GameName -Unique)
        active_dev_processes  = @(Get-ObjectValue -Object $recommendation -Name "active_dev_processes" -Default @())
        reasons               = @($reasons)
    }
}

function Invoke-AutomationPass {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Profiles
    )

    $plan = Get-AutomationPlan -Settings $Settings
    if (-not (Get-ObjectValue -Object $plan -Name "should_apply" -Default $false)) {
        return [pscustomobject]@{
            generated_at = (Get-Date).ToString("o")
            applied      = $false
            plan         = $plan
            message      = if ((Get-ObjectValue -Object $plan -Name "deferred" -Default $false)) {
                "Automation deferred because a game is running."
            }
            else {
                "Automation determined that no mode change is needed."
            }
        }
    }

    $script:ActionResults = @()
    $targetMode = [string](Get-ObjectValue -Object $plan -Name "target_mode" -Default "balanced")
    $result = Invoke-ModeProfile -ModeName $targetMode -Settings $Settings -Profiles $Profiles

    return [pscustomobject]@{
        generated_at = (Get-Date).ToString("o")
        applied      = $true
        plan         = $plan
        summary      = $result.summary
    }
}

function Get-AutomationScheduleStatus {
    param([Parameter(Mandatory = $true)]$Settings)

    $automationCfg = Get-ObjectValue -Object $Settings -Name "automation" -Default ([pscustomobject]@{})
    $taskName = [string](Get-ObjectValue -Object $automationCfg -Name "taskName" -Default "Keeper Auto Mode")
    $intervalMinutes = [int](Get-ObjectValue -Object $automationCfg -Name "intervalMinutes" -Default 5)

    $status = [pscustomobject]@{
        task_name         = $taskName
        interval_minutes  = $intervalMinutes
        installed         = $false
        state             = $null
        command           = 'powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "<repo>\\keeper.ps1" auto -Apply -Quiet'
        notes             = @()
    }

    if (-not (Get-Command Get-ScheduledTask -ErrorAction SilentlyContinue)) {
        $status.notes += "ScheduledTasks module is not available in this shell."
        return $status
    }

    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        $status.notes += "Automation task is not installed."
        return $status
    }

    $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction SilentlyContinue
    $status.installed = $true
    $status.state = if ($taskInfo) { [string]$taskInfo.State } else { [string]$task.State }
    $status.notes += "Automation task is installed."
    return $status
}

function Set-AutomationSchedule {
    param([Parameter(Mandatory = $true)]$Settings)

    $automationCfg = Get-ObjectValue -Object $Settings -Name "automation" -Default ([pscustomobject]@{})
    $taskName = [string](Get-ObjectValue -Object $automationCfg -Name "taskName" -Default "Keeper Auto Mode")
    $intervalMinutes = [int](Get-ObjectValue -Object $automationCfg -Name "intervalMinutes" -Default 5)
    $rootDir = $script:Root
    $keeperPath = Join-Path $rootDir "keeper.ps1"

    if ($WhatIfPreference) {
        return [pscustomobject]@{
            task_name        = $taskName
            installed        = $false
            action           = "WhatIf: would install or update the Keeper automation scheduled task."
            interval_minutes = $intervalMinutes
            command          = "powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$keeperPath`" auto -Apply -Quiet"
        }
    }

    if (-not (Get-Command Register-ScheduledTask -ErrorAction SilentlyContinue)) {
        throw "Register-ScheduledTask is not available on this system."
    }

    $logonTrigger = New-ScheduledTaskTrigger -AtLogOn
    $repeatStart = (Get-Date).AddMinutes(1)
    $repeatTrigger = New-ScheduledTaskTrigger -Once -At $repeatStart
    $repeatTrigger.Repetition = New-ScheduledTaskTrigger -Once -At $repeatStart -RepetitionInterval (New-TimeSpan -Minutes $intervalMinutes) -RepetitionDuration (New-TimeSpan -Days 3650) | Select-Object -ExpandProperty Repetition

    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$keeperPath`" auto -Apply -Quiet"
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel LeastPrivilege
    $taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($logonTrigger, $repeatTrigger) -Principal $principal -Settings $taskSettings -Force | Out-Null

    return [pscustomobject]@{
        task_name        = $taskName
        installed        = $true
        interval_minutes = $intervalMinutes
        action           = "Installed or updated the Keeper automation scheduled task."
        command          = "powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$keeperPath`" auto -Apply -Quiet"
    }
}

function Remove-AutomationSchedule {
    param([Parameter(Mandatory = $true)]$Settings)

    $automationCfg = Get-ObjectValue -Object $Settings -Name "automation" -Default ([pscustomobject]@{})
    $taskName = [string](Get-ObjectValue -Object $automationCfg -Name "taskName" -Default "Keeper Auto Mode")

    if ($WhatIfPreference) {
        return [pscustomobject]@{
            task_name = $taskName
            removed   = $false
            action    = "WhatIf: would remove the Keeper automation scheduled task."
        }
    }

    if (-not (Get-Command Unregister-ScheduledTask -ErrorAction SilentlyContinue)) {
        throw "Unregister-ScheduledTask is not available on this system."
    }

    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        return [pscustomobject]@{
            task_name = $taskName
            removed   = $false
            action    = "Automation task was not installed."
        }
    }

    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    return [pscustomobject]@{
        task_name = $taskName
        removed   = $true
        action    = "Removed the Keeper automation scheduled task."
    }
}
