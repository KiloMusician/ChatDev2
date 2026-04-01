<#
.SYNOPSIS
Machine-readable JSON bridge for keeper.

.DESCRIPTION
Exposes keeper state and actions as compact JSON so local UI shells such as the
Godot desktop app can consume keeper without scraping human-oriented console
output. This keeps `keeper.ps1` as the source of truth while giving future
integrations a stable local contract.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Position = 0)]
    [ValidateSet("snapshot", "status", "doctor", "recommend", "auto", "games", "mode", "export", "think", "maintain", "score", "advisor", "analyze", "optimize")]
    [string]$Command = "snapshot",

    [Parameter(Position = 1)]
    [ValidateSet("gaming", "coding", "balanced", "diagnose", "audio-safe", "quiet", "rimworld-mod", "heavy-gaming", "restore")]
    [string]$Mode,

    [switch]$Apply,
    [switch]$Html,
    [switch]$AudioTriage,
    [switch]$DebugMode,
    [switch]$Quiet,
    [switch]$KillCode,
    [switch]$Force,
    [string]$LatencyMonReportPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$WarningPreference = "SilentlyContinue"
$VerbosePreference = "SilentlyContinue"

if ($env:OS -ne "Windows_NT") {
    throw "keeper-bridge.ps1 must run on Windows."
}

if (-not $PSBoundParameters.ContainsKey("Quiet")) {
    $Quiet = $true
}

$script:Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
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
    Write-Log "Failed to preload CimCmdlets during bridge bootstrap: $($_.Exception.Message)" "DEBUG"
}

$settings = Get-Settings
$profiles = Get-Profiles
$script:Settings = $settings
$script:Profiles = $profiles

if ($KillCode) {
    if ($null -eq $settings.safety) { $settings | Add-Member -NotePropertyName "safety" -NotePropertyValue ([pscustomobject]@{}) }
    $settings.safety | Add-Member -NotePropertyName "killVSCode" -NotePropertyValue $true -Force
}

function Write-BridgeJson {
    param(
        [Parameter(Mandatory = $true)]$Data,
        [int]$ExitCode = 0
    )

    $payload = [pscustomobject]@{
        ok          = ($ExitCode -eq 0)
        generated_at = (Get-Date).ToString("o")
        command     = $Command
        data        = $Data
    }

    $payload | ConvertTo-Json -Depth 12 -Compress:$false
    exit $ExitCode
}

function Get-BridgeSnapshot {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Profiles
    )

    $health = Get-HealthState
    $doctor = Get-DoctorReport -Settings $Settings
    $recommendation = Get-ModeRecommendation -Settings $Settings
    $automation = Get-AutomationPlan -Settings $Settings
    $steam = Get-ActiveSteamGames -Settings $Settings
    $recentSessions = Get-RecentSessions -Max 5
    $currentState = Read-JsonFile -Path $script:CurrentStatePath -Default $null
    $rollbackState = Read-JsonFile -Path $script:RollbackPath -Default $null
    $listenerState   = Read-JsonFile -Path (Join-Path $script:StateDir "listener.json")          -Default $null
    $perfScore       = Read-JsonFile -Path (Join-Path $script:StateDir "performance_score.json") -Default $null
    $advisorLast     = Read-JsonFile -Path (Join-Path $script:StateDir "advisor_last.json")      -Default $null

    return [pscustomobject]@{
        surface            = "bridge"
        offline_first      = $true
        repo_root          = $script:Root
        current_state      = $currentState
        rollback_state     = $rollbackState
        health             = $health
        doctor             = $doctor
        recommendation     = $recommendation
        automation         = $automation
        steam              = [pscustomobject]@{
            vdf_path        = Get-ObjectValue -Object $steam -Name "vdf_path" -Default $null
            library_roots   = @(Get-ObjectValue -Object $steam -Name "library_roots" -Default @())
            active          = [bool](Get-ObjectValue -Object $steam -Name "active" -Default $false)
            active_games    = @(Get-UniqueSteamGameSummaries -Processes @(Get-ObjectValue -Object $steam -Name "processes" -Default @()))
        }
        listener_state     = $listenerState
        brain              = [pscustomobject]@{
            score   = $perfScore
            advisor = $advisorLast
        }
        recent_sessions    = $recentSessions
        available_modes    = @(Get-PropertyNames -Object $Profiles)
    }
}

try {
    switch ($Command) {
        "snapshot" {
            Write-BridgeJson -Data (Get-BridgeSnapshot -Settings $settings -Profiles $profiles)
        }

        "status" {
            Write-BridgeJson -Data (Get-HealthState)
        }

        "doctor" {
            if ($AudioTriage) {
                Write-BridgeJson -Data (Get-AudioTriageReport -Settings $settings -LatencyMonReportPath $LatencyMonReportPath)
            }
            else {
                Write-BridgeJson -Data (Get-DoctorReport -Settings $settings)
            }
        }

        "recommend" {
            $recommendation = Get-ModeRecommendation -Settings $settings
            if ($Apply) {
                $targetMode = [string](Get-ObjectValue -Object $recommendation -Name "recommended_mode" -Default "")
                if ([string]::IsNullOrWhiteSpace([string]$targetMode)) {
                    throw "No recommended mode was returned."
                }

                $script:ActionResults = @()
                $result = Invoke-ModeProfile -ModeName $targetMode -Settings $settings -Profiles $profiles
                Write-BridgeJson -Data ([pscustomobject]@{
                    recommendation = $recommendation
                    result         = $result
                })
            }
            else {
                Write-BridgeJson -Data $recommendation
            }
        }

        "auto" {
            if ($Apply) {
                Write-BridgeJson -Data (Invoke-AutomationPass -Settings $settings -Profiles $profiles)
            }
            else {
                Write-BridgeJson -Data (Get-AutomationPlan -Settings $settings)
            }
        }

        "games" {
            $steam = Get-ActiveSteamGames -Settings $settings
            Write-BridgeJson -Data ([pscustomobject]@{
                vdf_path        = Get-ObjectValue -Object $steam -Name "vdf_path" -Default $null
                library_roots   = @(Get-ObjectValue -Object $steam -Name "library_roots" -Default @())
                game_roots      = @(Get-ObjectValue -Object $steam -Name "game_roots" -Default @())
                active          = [bool](Get-ObjectValue -Object $steam -Name "active" -Default $false)
                processes       = @(Get-ObjectValue -Object $steam -Name "processes" -Default @())
                active_games    = @(Get-UniqueSteamGameSummaries -Processes @(Get-ObjectValue -Object $steam -Name "processes" -Default @()))
            })
        }

        "mode" {
            if (-not $Mode) {
                throw "Mode is required when Command=mode."
            }

            $script:ActionResults = @()
            if ($Mode -eq "restore") {
                Write-BridgeJson -Data (Invoke-RestoreMode -Settings $settings)
            }
            else {
                Write-BridgeJson -Data (Invoke-ModeProfile -ModeName $Mode -Settings $settings -Profiles $profiles)
            }
        }

        "export" {
            Write-BridgeJson -Data (Invoke-Export -Settings $settings -AsHtml:$Html -AudioTriage:$AudioTriage -LatencyMonReportPath $LatencyMonReportPath)
        }

        "think" {
            Write-BridgeJson -Data (Get-MaintenancePlan -Settings $settings)
        }

        "maintain" {
            $script:ActionResults = @()
            Write-BridgeJson -Data (Invoke-MaintenancePass -Settings $settings)
        }

        "score" {
            Write-BridgeJson -Data (Get-SystemScore -Settings $settings)
        }

        "advisor" {
            Write-BridgeJson -Data (Get-AdvisorRecommendation -Settings $settings)
        }

        "analyze" {
            Write-BridgeJson -Data (Invoke-Analyze -Settings $settings)
        }

        "optimize" {
            $script:ActionResults = @()
            Write-BridgeJson -Data (Invoke-Optimize -Settings $settings -Force:$Force)
        }
    }
}
catch {
    $errorPayload = [pscustomobject]@{
        ok           = $false
        generated_at = (Get-Date).ToString("o")
        command      = $Command
        error        = $_.Exception.Message
        details      = if ($DebugMode) { $_ | Out-String } else { $null }
    }

    $errorPayload | ConvertTo-Json -Depth 12 -Compress:$false
    exit 1
}
