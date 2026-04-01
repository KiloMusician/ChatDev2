<#
.SYNOPSIS
Profile-driven Windows mode switcher for gaming, coding, audio-safe, quiet, diagnosis, and restore.

.DESCRIPTION
`keeper.ps1` is a single-entrypoint PowerShell tool that coordinates a small,
reversible set of state changes for a Windows laptop. It focuses on safe mode
switching rather than registry spray or permanent tweaks.

Supported modes:
  gaming     - shuts WSL/Docker/VS Code, high-performance power, Game Mode on
  coding     - balanced power, Game Mode off, restores Windows Search
  balanced   - neutral daily mode, keeps current apps running, balanced power
  diagnose   - balanced baseline for audio stutter testing; run doctor after
  audio-safe - kills all audio-risk processes, shuts WSL/Docker, high-performance
  quiet      - stops all dev workloads and browsers, balanced power, no Game Mode
  restore    - rolls back the last reversible state change

.EXAMPLE
.\keeper.ps1 status

.EXAMPLE
.\keeper.ps1 mode gaming -WhatIf

.EXAMPLE
.\keeper.ps1 mode audio-safe

.EXAMPLE
.\keeper.ps1 mode quiet

.EXAMPLE
.\keeper.ps1 watch -DurationSec 60

.EXAMPLE
.\keeper.ps1 doctor

.EXAMPLE
.\keeper.ps1 recommend -Apply

.EXAMPLE
.\\keeper.ps1 auto -Apply

.EXAMPLE
.\\keeper.ps1 schedule -Apply -WhatIf

.EXAMPLE
.\keeper.ps1 updates

.EXAMPLE
.\keeper.ps1 export -Html

.EXAMPLE
.\keeper.ps1 doctor -Export -AudioTriage -Html

.EXAMPLE
.\keeper.ps1 doctor -AudioTriage -LatencyMonReportPath "C:\Users\you\Desktop\LatencyMon.txt"
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Position = 0)]
    [ValidateSet("status", "watch", "listen", "mode", "recommend", "auto", "schedule", "doctor", "updates", "export", "prune", "think", "maintain", "score", "advisor", "analyze", "optimize")]
    [string]$Command = "status",

    [Parameter(Position = 1)]
    [ValidateSet("gaming", "coding", "balanced", "diagnose", "audio-safe", "quiet", "rimworld-mod", "heavy-gaming", "restore")]
    [string]$Mode,

    [ValidateRange(0, 86400)]
    [int]$DurationSec = 0,

    [switch]$DebugMode,
    [switch]$Quiet,
    [switch]$Html,
    [switch]$Export,
    [switch]$Apply,
    [switch]$Remove,
    [switch]$AudioTriage,
    [switch]$Silent,
    [switch]$KillCode,
    [switch]$Force,
    [string]$LatencyMonReportPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "keeper.ps1 must run from Windows PowerShell or PowerShell on Windows."
}

$script:RequestedWhatIf = [bool]$WhatIfPreference
if ($script:RequestedWhatIf) {
    # Keep bootstrap quiet; restore the caller's WhatIf preference before dispatch.
    $WhatIfPreference = $false
}

$script:Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:LibDir = Join-Path $script:Root "lib"
$script:ConfigDir = Join-Path $script:Root "config"
$script:StateDir = Join-Path $script:Root "state"
$script:SessionsDir = Join-Path $script:Root "sessions"
$script:IncidentsDir = Join-Path $script:Root "incidents"

$script:CurrentStatePath = Join-Path $script:StateDir "current.json"
$script:RingBufferPath = Join-Path $script:StateDir "ringbuffer.json"
$script:RollbackPath = Join-Path $script:StateDir "rollback.json"
$script:DefaultsPath = Join-Path $script:ConfigDir "defaults.json"
$script:ProfilesPath = Join-Path $script:ConfigDir "profiles.json"
$script:MachinePath = Join-Path $script:ConfigDir "machine.local.json"

$script:IsAdmin = $false
$script:ActionResults = @()

$moduleFiles = @(
    "config.ps1",
    "actions.ps1",
    "state.ps1",
    "health.ps1",
    "profiles.ps1",
    "watch.ps1",
    "listener.ps1",
    "automation.ps1",
    "updates.ps1",
    "export.ps1",
    "maintenance.ps1",
    "brain.ps1"
)

foreach ($moduleFile in $moduleFiles) {
    $modulePath = Join-Path $script:LibDir $moduleFile
    if (-not (Test-Path -LiteralPath $modulePath)) {
        throw "Required module file was not found: $modulePath"
    }
    . $modulePath
}

Initialize-Workspace

try {
    Import-Module CimCmdlets -ErrorAction Stop | Out-Null
}
catch {
    Write-Log "Failed to preload CimCmdlets during bootstrap: $($_.Exception.Message)" "DEBUG"
}

$settings = Get-Settings
$profiles = Get-Profiles
$script:Settings = $settings
$script:Profiles = $profiles

if ($KillCode) {
    if ($null -eq $settings.safety) { $settings | Add-Member -NotePropertyName "safety" -NotePropertyValue ([pscustomobject]@{}) }
    $settings.safety | Add-Member -NotePropertyName "killVSCode" -NotePropertyValue $true -Force
}

if ($script:RequestedWhatIf) {
    $WhatIfPreference = $true
}

switch ($Command) {
    "status" {
        Invoke-Status -Settings $settings | Format-List
        break
    }

    "watch" {
        $duration = $DurationSec
        if ($duration -eq 0) {
            $watchSettings = Get-ObjectValue -Object $settings -Name "watch" -Default ([pscustomobject]@{})
            $duration = [int](Get-ObjectValue -Object $watchSettings -Name "defaultDurationSec" -Default 0)
        }
        Invoke-Watch -Settings $settings -RunForSeconds $duration
        break
    }

    "listen" {
        $duration = $DurationSec
        Invoke-Listen -Settings $settings -Profiles $profiles -RunForSeconds $duration | Format-List
        break
    }

    "mode" {
        if (-not $Mode) {
            throw "Mode is required when Command=mode."
        }

        $script:ActionResults = @()

        if ($Mode -eq "restore") {
            $result = Invoke-RestoreMode -Settings $settings
        }
        else {
            $result = Invoke-ModeProfile -ModeName $Mode -Settings $settings -Profiles $profiles
        }

        if ($DebugMode) {
            $result.actions | Format-Table -AutoSize
        }

        $result.summary | Format-List
        break
    }

    "recommend" {
        $recommendation = Get-ModeRecommendation -Settings $settings
        if ($Apply) {
            $targetMode = [string](Get-ObjectValue -Object $recommendation -Name "recommended_mode" -Default "")
            if ([string]::IsNullOrWhiteSpace($targetMode)) {
                throw "Unable to apply recommendation because no target mode was returned."
            }

            $script:ActionResults = @()
            $result = Invoke-ModeProfile -ModeName $targetMode -Settings $settings -Profiles $profiles
            [pscustomobject]@{
                recommendation = $recommendation
                summary        = $result.summary
            } | Format-List
        }
        else {
            $recommendation | Format-List
        }
        break
    }

    "auto" {
        $plan = Get-AutomationPlan -Settings $settings
        if ($Apply) {
            $result = Invoke-AutomationPass -Settings $settings -Profiles $profiles
            $result | Format-List
        }
        else {
            $plan | Format-List
        }
        break
    }

    "schedule" {
        if ($Remove) {
            Remove-AutomationSchedule -Settings $settings | Format-List
        }
        elseif ($Apply) {
            Set-AutomationSchedule -Settings $settings | Format-List
        }
        else {
            Get-AutomationScheduleStatus -Settings $settings | Format-List
        }
        break
    }

    "doctor" {
        if ($Export) {
            Invoke-Export -Settings $settings -AsHtml:$Html -AudioTriage:$AudioTriage -LatencyMonReportPath $LatencyMonReportPath | Format-List
        }
        elseif ($AudioTriage) {
            Get-AudioTriageReport -Settings $settings -LatencyMonReportPath $LatencyMonReportPath | Format-List
        }
        else {
            Get-DoctorReport -Settings $settings | Format-List
        }
        break
    }

    "updates" {
        if ($Apply) {
            Invoke-Updates -Settings $settings -Silent:$Silent | Format-List
        }
        else {
            Get-UpdateReport -Settings $settings | Format-List
        }
        break
    }

    "export" {
        Invoke-Export -Settings $settings -AsHtml:$Html -AudioTriage:$AudioTriage -LatencyMonReportPath $LatencyMonReportPath | Format-List
        break
    }

    "prune" {
        Invoke-Prune -Settings $settings | Format-List
        break
    }

    "think" {
        # Read-only analysis — disk, Docker, WSL, temp, downloads
        $plan = Get-MaintenancePlan -Settings $settings
        $plan | ConvertTo-Json -Depth 8
        break
    }

    "maintain" {
        # Apply safe maintenance actions (respects safety thresholds + config.maintenance.actions)
        $script:ActionResults = @()
        Invoke-MaintenancePass -Settings $settings | ConvertTo-Json -Depth 8
        break
    }

    "score" {
        # Deterministic weighted pressure score (0-100); no LLM, no network
        Get-SystemScore -Settings $settings | ConvertTo-Json -Depth 6
        break
    }

    "advisor" {
        # Rules-based recommendation (action + why + confidence); no LLM, no network
        Get-AdvisorRecommendation -Settings $settings | ConvertTo-Json -Depth 6
        break
    }

    "analyze" {
        # Ollama-backed log analysis (warm path, graceful fallback)
        Invoke-Analyze -Settings $settings | ConvertTo-Json -Depth 8
        break
    }

    "optimize" {
        # Apply the advisor recommendation; -Force overrides safe_to_apply gate
        $script:ActionResults = @()
        Invoke-Optimize -Settings $settings -Force:$Force | ConvertTo-Json -Depth 8
        break
    }
}
