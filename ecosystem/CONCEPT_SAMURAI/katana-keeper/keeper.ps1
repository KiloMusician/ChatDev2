<#
.SYNOPSIS
    katana-keeper: lightweight performance orchestrator for gaming/coding modes on Windows.

.DESCRIPTION
    Thin router that dot-sources lib/ modules and dispatches commands.
    Supports: status, watch, listen, mode, doctor, export, prune.

.PARAMETER Command
    Action to perform: status | watch | listen | mode | doctor | export | prune

.PARAMETER Mode
    Profile name for the 'mode' command: gaming | coding | diagnose | restore

.PARAMETER Html
    With 'export': also generate an HTML report and open it.

.PARAMETER AudioTriage
    With 'doctor' or 'export': include Nahimic / audio driver deep-scan.

.PARAMETER LatencyMonReportPath
    Path to a LatencyMon .txt report for audio triage / LatencyMon parsing.

.PARAMETER DurationSec
    With 'watch': run for this many seconds then exit (0 = run forever).

.PARAMETER DebugMode
    Verbose action-level logging.

.PARAMETER Quiet
    Suppress INFO-level log lines.

.NOTES
    Respects -WhatIf via ShouldProcess on all side-effectful lib functions.
    Config in config/, state in state/, sessions in sessions/, incidents in incidents/.
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Position = 0)]
    [ValidateSet("status","watch","listen","mode","doctor","export","prune")]
    [string]$Command = "status",

    [Parameter(Position = 1)]
    [string]$Mode,

    [switch]$Html,
    [switch]$AudioTriage,
    [string]$LatencyMonReportPath,
    [int]$DurationSec = 0,
    [switch]$DebugMode,
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "keeper.ps1 must run from Windows PowerShell or PowerShell on Windows."
}

# ── Path setup ────────────────────────────────────────────────────────────────
$script:Root         = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:LibDir       = Join-Path $script:Root "lib"
$script:ConfigDir    = Join-Path $script:Root "config"
$script:StateDir     = Join-Path $script:Root "state"
$script:SessionsDir  = Join-Path $script:Root "sessions"
$script:IncidentsDir = Join-Path $script:Root "incidents"

$script:CurrentStatePath = Join-Path $script:StateDir  "current.json"
$script:RingBufferPath   = Join-Path $script:StateDir  "ringbuffer.json"
$script:RollbackPath     = Join-Path $script:StateDir  "rollback.json"
$script:DefaultsPath     = Join-Path $script:ConfigDir "defaults.json"
$script:ProfilesPath     = Join-Path $script:ConfigDir "profiles.json"
$script:MachinePath      = Join-Path $script:ConfigDir "machine.local.json"

# ── Mutable script-scope state ────────────────────────────────────────────────
$script:IsAdmin       = $false
$script:ActionResults = @()

# ── Load lib modules (order matters: config first, then state, then the rest) ─
. (Join-Path $script:LibDir "config.ps1")
. (Join-Path $script:LibDir "state.ps1")
. (Join-Path $script:LibDir "actions.ps1")
. (Join-Path $script:LibDir "health.ps1")
. (Join-Path $script:LibDir "doctor.ps1")
. (Join-Path $script:LibDir "profiles.ps1")
. (Join-Path $script:LibDir "export.ps1")
. (Join-Path $script:LibDir "watch.ps1")
. (Join-Path $script:LibDir "listener.ps1")

# ── Bootstrap ─────────────────────────────────────────────────────────────────
Ensure-Directory -Path $script:ConfigDir
Ensure-Directory -Path $script:StateDir
Ensure-Directory -Path $script:SessionsDir
Ensure-Directory -Path $script:IncidentsDir
$script:IsAdmin = Test-IsAdministrator

$settings = Get-Settings
$profiles  = Get-Profiles

# ── Command router ────────────────────────────────────────────────────────────
switch ($Command) {
    "status" {
        Invoke-Status -Settings $settings | Format-List
    }
    "watch" {
        $dur = $DurationSec
        if ($dur -eq 0) {
            $watchCfg = Get-ObjectValue -Object $settings -Name "watch" -Default ([pscustomobject]@{})
            $dur = [int](Get-ObjectValue -Object $watchCfg -Name "defaultDurationSec" -Default 0)
        }
        Invoke-Watch -Settings $settings -RunForSeconds $dur
    }
    "listen" {
        Invoke-Listen -Settings $settings -Profiles $profiles
    }
    "mode" {
        if (-not $Mode) { throw "Specify -Mode: gaming, coding, diagnose, or restore." }
        $script:ActionResults = @()
        if ($Mode -eq "restore") {
            $result = Invoke-RestoreMode -Settings $settings
        } else {
            $result = Invoke-ModeProfile -ModeName $Mode -Settings $settings -Profiles $profiles
        }
        if ($DebugMode) { $result.actions | Format-Table -AutoSize }
        $result.summary | Format-List
    }
    "doctor" {
        if ($AudioTriage) {
            Get-AudioTriageReport -Settings $settings -LatencyMonReportPath $LatencyMonReportPath | Format-List
        } else {
            Get-DoctorReport -Settings $settings | Format-List
        }
    }
    "export" {
        Invoke-Export -Settings $settings -AsHtml:$Html -AudioTriage:$AudioTriage -LatencyMonReportPath $LatencyMonReportPath | Format-List
    }
    "prune" {
        Invoke-Prune -Settings $settings | Format-List
    }
}
