<#
Example: wire Steam Web API data into the repo's automation flow (non-destructive)

This script demonstrates how to load repo settings, read Steam API credentials
(if present), call the Steam Web API helpers in `lib/steam-web.ps1`, and
show how you could attach the returned data to the listener settings so
`Invoke-Listen` or automation code can use it.

Note: This script does NOT call `Invoke-Listen` or apply any modes — it's
intentionally read-only and safe to run locally.
#>

$repoRoot = Split-Path -Parent $PSScriptRoot

# Dot-source helper libraries (safe no-op if already loaded)
$lib = Join-Path $repoRoot 'lib'
if (Test-Path (Join-Path $lib 'config.ps1')) { . (Join-Path $lib 'config.ps1') }
. (Join-Path $lib 'steam-web.ps1')

# Ensure Get-Settings will find the repo config if it is used by other helpers
if (-not $script:DefaultsPath) { $script:DefaultsPath = Join-Path $repoRoot 'config\defaults.json' }
if (-not $script:MachinePath)  { $script:MachinePath  = Join-Path $repoRoot 'config\machine.local.json' }
if (-not $script:ProfilesPath) { $script:ProfilesPath = Join-Path $repoRoot 'config\profiles.json' }

# Load settings (will fall back to defaults/example if machine.local.json is absent)
if (Get-Command -Name 'Get-Settings' -ErrorAction SilentlyContinue) {
    $settings = Get-Settings
    $profiles = Get-Profiles
}
else {
    Write-Host "Get-Settings not available; calling Get-RepoSettings from steam-web helper"
    $settings = Get-RepoSettings
    $profiles = @{}
}

# Get Steam credentials from settings or env
$steamCfg = Get-SteamConfig -Settings $settings
if (-not $steamCfg.webApiKey) {
    Write-Warning "No Steam Web API key found. Set 'settings.steam.webApiKey' in config/machine.local.json or set KEEPER_STEAM_API_KEY env var to try the API."
    return
}
if (-not $steamCfg.steamId) {
    Write-Warning "No Steam ID found. Set 'settings.steam.steamId' in config/machine.local.json or set KEEPER_STEAM_ID env var."
    return
}

Write-Host "Found Steam API key and SteamID. Querying Steam Web API (read-only)..."

$player = Get-SteamPlayerSummaries -ApiKey $steamCfg.webApiKey -SteamId $steamCfg.steamId
if ($null -ne $player) {
    Write-Host "Player summary:"
    $player | Select-Object personaname, steamid, lastlogoff | Format-List
}

$owned = Get-SteamOwnedGames -ApiKey $steamCfg.webApiKey -SteamId $steamCfg.steamId -IncludeAppInfo
if ($null -ne $owned) {
    Write-Host "Owned games count: $($owned.game_count)"
    $owned.games | Select-Object appid, name | Select-Object -First 10 | Format-Table -AutoSize
}

# Example: attach remote owned games to listener settings for later enrichment
if (-not $settings.listener) { $settings.listener = [pscustomobject]@{} }
$settings.listener.remoteOwnedGames = if ($owned) { $owned.games } else { @() }

Write-Host "Attached remote owned games to settings.listener.remoteOwnedGames (read-only in memory)."
Write-Host "You can now pass this $settings object into your automation or a modified Invoke-Listen that reads these values."

# End
