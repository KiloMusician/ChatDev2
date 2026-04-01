<#
.SYNOPSIS
Lightweight Steam Web API helper functions for optional enrichment of local Steam detection.

.DESCRIPTION
This file provides small helper functions to call the Steam Web API (GetPlayerSummaries, GetOwnedGames)
and small config-loading helpers that follow this repo's conventions (falling back to `config/machine.local.example.json`).
It is intentionally minimal — treat it as an optional enhancement that you can wire into your existing
automation/listener code. API key and SteamID should be provided through `config/machine.local.json` or
environment variables `KEEPER_STEAM_API_KEY` and `KEEPER_STEAM_ID`.
#>

function Get-RepoRoot {
    # Resolve repository root based on this file's location (assumes lib/ sits directly under repo root)
    return Split-Path -Parent $PSScriptRoot
}

function Get-RepoSettings {
    param(
        [string]$RepoRoot
    )

    if (-not $RepoRoot) { $RepoRoot = Get-RepoRoot }

    $defaultsPath = Join-Path $RepoRoot 'config\defaults.json'
    $machinePath = Join-Path $RepoRoot 'config\machine.local.json'
    $exampleMachine = Join-Path $RepoRoot 'config\machine.local.example.json'
    if (-not (Test-Path -LiteralPath $machinePath) -and (Test-Path -LiteralPath $exampleMachine)) {
        $machinePath = $exampleMachine
    }

    if (Get-Command -Name 'Read-JsonFile' -ErrorAction SilentlyContinue) {
        $defaults = Read-JsonFile -Path $defaultsPath -Default ([pscustomobject]@{})
        $machine = if ($machinePath) { Read-JsonFile -Path $machinePath -Default ([pscustomobject]@{}) } else { [pscustomobject]@{} }
    }
    else {
        $defaults = if (Test-Path -LiteralPath $defaultsPath) { Get-Content -LiteralPath $defaultsPath -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
        $machine = if ($machinePath -and (Test-Path -LiteralPath $machinePath)) { Get-Content -LiteralPath $machinePath -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
    }

    $machineSettings = $null
    if ($machine -and $machine.PSObject.Properties.Name -contains 'settings') { $machineSettings = $machine.settings } else { $machineSettings = [pscustomobject]@{} }

    if (Get-Command -Name 'Merge-Objects' -ErrorAction SilentlyContinue) {
        return Merge-Objects -Base $defaults -Override $machineSettings
    }
    else {
        # shallow merge: machine settings properties override defaults
        $merged = [ordered]@{}
        foreach ($p in $defaults.PSObject.Properties) { $merged[$p.Name] = $p.Value }
        foreach ($p in $machineSettings.PSObject.Properties) { $merged[$p.Name] = $p.Value }
        return [pscustomobject]$merged
    }
}

function Get-SteamConfig {
    param(
        [pscustomobject]$Settings
    )

    if ($null -eq $Settings) {
        if (Get-Command -Name 'Get-Settings' -ErrorAction SilentlyContinue) {
            $Settings = Get-Settings
        }
        else {
            $Settings = Get-RepoSettings
        }
    }

    if (Get-Command -Name 'Get-ObjectValue' -ErrorAction SilentlyContinue) {
        $steam = Get-ObjectValue -Object $Settings -Name 'steam' -Default $null
        $webApiKey = if ($null -ne $steam) { Get-ObjectValue -Object $steam -Name 'webApiKey' -Default $null } else { $null }
        $steamId = if ($null -ne $steam) { Get-ObjectValue -Object $steam -Name 'steamId' -Default $null } else { $null }
    }
    else {
        $steam = if ($Settings -and $Settings.PSObject.Properties.Name -contains 'steam') { $Settings.steam } else { $null }
        $webApiKey = if ($steam -and $steam.PSObject.Properties.Name -contains 'webApiKey') { $steam.webApiKey } else { $null }
        $steamId = if ($steam -and $steam.PSObject.Properties.Name -contains 'steamId') { $steam.steamId } else { $null }
    }

    if ([string]::IsNullOrWhiteSpace([string]$webApiKey) -and $env:KEEPER_STEAM_API_KEY) { $webApiKey = $env:KEEPER_STEAM_API_KEY }
    if ([string]::IsNullOrWhiteSpace([string]$steamId) -and $env:KEEPER_STEAM_ID) { $steamId = $env:KEEPER_STEAM_ID }

    return [pscustomobject]@{ webApiKey = $webApiKey; steamId = $steamId }
}

function Get-SteamApiKey {
    param(
        [pscustomobject]$Settings
    )

    $cfg = Get-SteamConfig -Settings $Settings
    return $cfg.webApiKey
}

function Get-SteamPlayerSummaries {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$ApiKey,
        [Parameter(Mandatory=$true)][string]$SteamId
    )

    $uri = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=$ApiKey&steamids=$SteamId"
    try {
        $resp = Invoke-RestMethod -Uri $uri -UseBasicParsing -ErrorAction Stop
        return $resp.response.players
    }
    catch {
        Write-Error "Get-SteamPlayerSummaries failed: $($_.Exception.Message)"
        return $null
    }
}

function Get-SteamOwnedGames {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$ApiKey,
        [Parameter(Mandatory=$true)][string]$SteamId,
        [switch]$IncludeAppInfo
    )

    $includeAppInfo = if ($IncludeAppInfo) { 1 } else { 0 }
    $uri = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key=$ApiKey&steamid=$SteamId&include_appinfo=$includeAppInfo&include_played_free_games=1"
    try {
        $resp = Invoke-RestMethod -Uri $uri -UseBasicParsing -ErrorAction Stop
        return $resp.response
    }
    catch {
        Write-Error "Get-SteamOwnedGames failed: $($_.Exception.Message)"
        return $null
    }
}

