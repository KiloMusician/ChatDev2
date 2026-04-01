<#
.SYNOPSIS
Launch the Keeper desktop shell.

.DESCRIPTION
Prefers the local Godot shell when Godot is available. Falls back to the local
web dashboard when Godot cannot be found or when -PreferWebFallback is used.
#>
[CmdletBinding()]
param(
    [switch]$PreferWebFallback
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $toolsDir
$projectDir = Join-Path $rootDir "godot\keeper-shell"
$projectFile = Join-Path $projectDir "project.godot"
$bridgePath = Join-Path $rootDir "tools\keeper-bridge.ps1"
$dashboardPath = Join-Path $rootDir "index.html"

function Resolve-GodotExecutable {
    $candidates = @()

    if ($env:KEEPER_GODOT_EXE) {
        $candidates += $env:KEEPER_GODOT_EXE
    }

    foreach ($commandName in @("godot4.exe", "godot4", "godot.exe", "godot")) {
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($null -ne $command) {
            $candidates += $command.Source
        }
    }

    $searchGlobs = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Godot\Godot*.exe"),
        (Join-Path $env:LOCALAPPDATA "Godot\Godot*.exe"),
        (Join-Path $env:ProgramFiles "Godot*\Godot*.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Godot*\Godot*.exe")
    )

    foreach ($glob in $searchGlobs) {
        $candidates += @(Get-ChildItem -Path $glob -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName)
    }

    return @($candidates | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) -and (Test-Path -LiteralPath $_) } | Sort-Object -Unique | Select-Object -First 1)
}

function Start-WebFallback {
    if (-not (Test-Path -LiteralPath $dashboardPath)) {
        throw "The dashboard fallback file was not found: $dashboardPath"
    }

    Start-Process -FilePath $dashboardPath | Out-Null
    return [pscustomobject]@{
        surface = "web-fallback"
        path    = $dashboardPath
        note    = "Opened the local dashboard because Godot was not selected or not available."
    }
}

if ($PreferWebFallback) {
    Start-WebFallback | Format-List
    exit 0
}

$godotExe = Resolve-GodotExecutable
if ($null -ne $godotExe -and (Test-Path -LiteralPath $projectFile)) {
    $env:KEEPER_ROOT = $rootDir
    $env:KEEPER_BRIDGE_PATH = $bridgePath
    Start-Process -FilePath $godotExe -ArgumentList @("--path", $projectDir) -WorkingDirectory $projectDir | Out-Null
    [pscustomobject]@{
        surface      = "godot"
        executable   = $godotExe
        project_path = $projectFile
        note         = "Launched the offline-first Godot shell."
    } | Format-List
    exit 0
}

Start-WebFallback | Format-List
