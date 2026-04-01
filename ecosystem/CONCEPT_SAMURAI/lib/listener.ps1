function Normalize-SteamPath {
    param([AllowNull()][string]$Path)

    if ([string]::IsNullOrWhiteSpace([string]$Path)) {
        return $null
    }

    $expanded = [Environment]::ExpandEnvironmentVariables(([string]$Path -replace '\\\\', '\'))
    try {
        return ([IO.Path]::GetFullPath($expanded)).TrimEnd('\')
    }
    catch {
        return ([string]$expanded).TrimEnd('\')
    }
}

function Get-DefaultSteamVdfPath {
    $steamRoots = @()
    if ($env:ProgramFiles -and (Test-Path -LiteralPath (Join-Path $env:ProgramFiles "Steam"))) {
        $steamRoots += (Join-Path $env:ProgramFiles "Steam")
    }
    if (${env:ProgramFiles(x86)} -and (Test-Path -LiteralPath (Join-Path ${env:ProgramFiles(x86)} "Steam"))) {
        $steamRoots += (Join-Path ${env:ProgramFiles(x86)} "Steam")
    }

    foreach ($steamRoot in @($steamRoots | Sort-Object -Unique)) {
        $candidate = Join-Path $steamRoot "config\libraryfolders.vdf"
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

function Get-SteamLibraryRoots {
    param([string]$VdfPath)

    if ([string]::IsNullOrWhiteSpace([string]$VdfPath)) {
        return @()
    }

    $expandedPath = Normalize-SteamPath -Path $VdfPath
    if ([string]::IsNullOrWhiteSpace([string]$expandedPath) -or -not (Test-Path -LiteralPath $expandedPath)) {
        return @()
    }

    $roots = @()
    try {
        $raw = Get-Content -LiteralPath $expandedPath -Raw -ErrorAction Stop
        $matches = @([regex]::Matches($raw, '"path"\s*"([^"]+)"') | ForEach-Object { $_.Groups[1].Value })
        if ($matches.Count -eq 0) {
            $matches = @([regex]::Matches($raw, '"\d+"\s*"([^"]+)"') | ForEach-Object { $_.Groups[1].Value })
        }

        foreach ($match in $matches) {
            $normalized = Normalize-SteamPath -Path $match
            if (-not [string]::IsNullOrWhiteSpace([string]$normalized)) {
                $roots += $normalized
            }
        }
    }
    catch {
        return @()
    }

    $steamRoot = Normalize-SteamPath -Path (Split-Path -Parent (Split-Path -Parent $expandedPath))
    if (-not [string]::IsNullOrWhiteSpace([string]$steamRoot)) {
        $roots += $steamRoot
    }

    return @($roots | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | Sort-Object -Unique)
}

function Get-SteamGameRoots {
    param(
        [string[]]$LibraryRoots,
        [string]$VdfPath
    )

    $roots = @($LibraryRoots)
    if ($roots.Count -eq 0 -and -not [string]::IsNullOrWhiteSpace([string]$VdfPath)) {
        $roots = @(Get-SteamLibraryRoots -VdfPath $VdfPath)
    }

    $gameRoots = @()
    foreach ($libraryRoot in @($roots)) {
        if ([string]::IsNullOrWhiteSpace([string]$libraryRoot)) {
            continue
        }

        $gameRoots += (Join-Path $libraryRoot "steamapps\common")
    }

    return @($gameRoots | Sort-Object -Unique)
}

function Get-SteamAppManifestPaths {
    param(
        [string[]]$LibraryRoots,
        [string]$VdfPath
    )

    $roots = @($LibraryRoots)
    if ($roots.Count -eq 0 -and -not [string]::IsNullOrWhiteSpace([string]$VdfPath)) {
        $roots = @(Get-SteamLibraryRoots -VdfPath $VdfPath)
    }

    $manifests = @()
    foreach ($libraryRoot in @($roots)) {
        if ([string]::IsNullOrWhiteSpace([string]$libraryRoot)) {
            continue
        }

        $steamAppsPath = Join-Path $libraryRoot "steamapps"
        if (-not (Test-Path -LiteralPath $steamAppsPath)) {
            continue
        }

        $manifests += @(Get-ChildItem -LiteralPath $steamAppsPath -Filter "appmanifest_*.acf" -File -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty FullName)
    }

    return @($manifests | Sort-Object -Unique)
}

function Read-SteamAppManifest {
    param([Parameter(Mandatory = $true)][string]$Path)

    $manifestPath = Normalize-SteamPath -Path $Path
    if ([string]::IsNullOrWhiteSpace([string]$manifestPath) -or -not (Test-Path -LiteralPath $manifestPath)) {
        return $null
    }

    try {
        $raw = Get-Content -LiteralPath $manifestPath -Raw -ErrorAction Stop
    }
    catch {
        return $null
    }

    $pairs = @{}
    foreach ($match in @([regex]::Matches($raw, '"([^"]+)"\s*"([^"]*)"'))) {
        $key = [string]$match.Groups[1].Value
        $value = [string]$match.Groups[2].Value
        if (-not $pairs.Contains($key)) {
            $pairs[$key] = $value
        }
    }

    $appId = [string](Get-ObjectValue -Object $pairs -Name "appid" -Default "")
    $name = [string](Get-ObjectValue -Object $pairs -Name "name" -Default "")
    $installDir = [string](Get-ObjectValue -Object $pairs -Name "installdir" -Default "")
    $buildId = [string](Get-ObjectValue -Object $pairs -Name "buildid" -Default "")

    $steamAppsRoot = Split-Path -Parent $manifestPath
    $libraryRoot = Normalize-SteamPath -Path (Split-Path -Parent $steamAppsRoot)
    $gameRoot = $null
    if (-not [string]::IsNullOrWhiteSpace([string]$installDir) -and -not [string]::IsNullOrWhiteSpace([string]$libraryRoot)) {
        $gameRoot = Normalize-SteamPath -Path (Join-Path $libraryRoot ("steamapps\common\{0}" -f $installDir))
    }

    return [pscustomobject]@{
        AppId        = $appId
        Name         = $name
        InstallDir   = $installDir
        BuildId      = $buildId
        ManifestPath = $manifestPath
        LibraryRoot  = $libraryRoot
        GameRoot     = $gameRoot
    }
}

function Get-SteamInstalledGames {
    param(
        [string[]]$LibraryRoots,
        [string]$VdfPath
    )

    $items = @()
    foreach ($manifestPath in @(Get-SteamAppManifestPaths -LibraryRoots $LibraryRoots -VdfPath $VdfPath)) {
        $manifest = Read-SteamAppManifest -Path $manifestPath
        if ($null -ne $manifest) {
            $items += $manifest
        }
    }

    return @($items | Sort-Object Name, AppId)
}

function Test-PathUnderRoots {
    param(
        [string]$Path,
        [string[]]$Roots
    )

    $normalizedPath = Normalize-SteamPath -Path $Path
    if ([string]::IsNullOrWhiteSpace([string]$normalizedPath)) {
        return $false
    }

    foreach ($root in @($Roots)) {
        $normalizedRoot = Normalize-SteamPath -Path $root
        if ([string]::IsNullOrWhiteSpace([string]$normalizedRoot)) {
            continue
        }

        if ($normalizedPath.StartsWith($normalizedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }

    return $false
}

function Resolve-SteamGameMetadata {
    param(
        [string]$Path,
        [AllowEmptyCollection()][array]$InstalledGames = @()
    )

    $normalizedPath = Normalize-SteamPath -Path $Path
    if ([string]::IsNullOrWhiteSpace([string]$normalizedPath)) {
        return $null
    }

    $candidates = @($InstalledGames | Where-Object {
            $gameRoot = Get-ObjectValue -Object $_ -Name "GameRoot" -Default $null
            -not [string]::IsNullOrWhiteSpace([string]$gameRoot) -and
            (Test-PathUnderRoots -Path $normalizedPath -Roots @($gameRoot))
        })

    if ($candidates.Count -eq 0) {
        return $null
    }

    return @($candidates | Sort-Object {
            $gameRoot = [string](Get-ObjectValue -Object $_ -Name "GameRoot" -Default "")
            $gameRoot.Length
        } -Descending | Select-Object -First 1)[0]
}

function Get-SteamGameProcessSnapshots {
    param(
        [Alias("Roots")]
        [string[]]$GameRoots,
        [AllowEmptyCollection()][array]$InstalledGames = @()
    )

    $items = @()
    foreach ($process in @(Get-Process -ErrorAction SilentlyContinue)) {
        $path = $null
        try {
            $path = $process.Path
        }
        catch {
            $path = $null
        }

        if (-not (Test-PathUnderRoots -Path $path -Roots $GameRoots)) {
            continue
        }

        $game = Resolve-SteamGameMetadata -Path $path -InstalledGames $InstalledGames
        $items += [pscustomobject]@{
            ProcessName = $process.ProcessName
            Id          = $process.Id
            Path        = $path
            GameName    = if ($null -ne $game) { Get-ObjectValue -Object $game -Name "Name" -Default $process.ProcessName } else { $process.ProcessName }
            SteamAppId  = if ($null -ne $game) { Get-ObjectValue -Object $game -Name "AppId" -Default $null } else { $null }
            InstallDir  = if ($null -ne $game) { Get-ObjectValue -Object $game -Name "InstallDir" -Default $null } else { $null }
            ManifestPath = if ($null -ne $game) { Get-ObjectValue -Object $game -Name "ManifestPath" -Default $null } else { $null }
            LibraryRoot = if ($null -ne $game) { Get-ObjectValue -Object $game -Name "LibraryRoot" -Default $null } else { $null }
            GameRoot    = if ($null -ne $game) { Get-ObjectValue -Object $game -Name "GameRoot" -Default $null } else { $null }
        }
    }

    return @($items | Sort-Object Id)
}

function Get-SteamContext {
    param([string]$VdfPath)

    $resolvedVdfPath = if (-not [string]::IsNullOrWhiteSpace([string]$VdfPath)) {
        Normalize-SteamPath -Path $VdfPath
    }
    else {
        Get-DefaultSteamVdfPath
    }

    $libraryRoots = @(Get-SteamLibraryRoots -VdfPath $resolvedVdfPath)
    $gameRoots = @(Get-SteamGameRoots -LibraryRoots $libraryRoots)
    $installedGames = @(Get-SteamInstalledGames -LibraryRoots $libraryRoots)

    return [pscustomobject]@{
        vdf_path        = $resolvedVdfPath
        library_roots   = $libraryRoots
        game_roots      = $gameRoots
        installed_games = $installedGames
    }
}

function Get-ActiveSteamGames {
    param([Parameter(Mandatory = $true)]$Settings)

    $listener = Get-ObjectValue -Object $Settings -Name "listener" -Default ([pscustomobject]@{})
    $vdfOverride = Get-ObjectValue -Object $listener -Name "steamVdfPath" -Default $null
    $context = Get-SteamContext -VdfPath $vdfOverride
    $processes = @(Get-SteamGameProcessSnapshots -GameRoots $context.game_roots -InstalledGames $context.installed_games)

    return [pscustomobject]@{
        vdf_path        = $context.vdf_path
        library_roots   = $context.library_roots
        game_roots      = $context.game_roots
        installed_games = $context.installed_games
        processes       = $processes
        active          = ($processes.Count -gt 0)
    }
}

function Get-UniqueSteamGameSummaries {
    param([AllowEmptyCollection()][array]$Processes = @())

    $seen = @{}
    $items = @()
    foreach ($process in @($Processes)) {
        $appId = [string](Get-ObjectValue -Object $process -Name "SteamAppId" -Default "")
        $gameName = [string](Get-ObjectValue -Object $process -Name "GameName" -Default (Get-ObjectValue -Object $process -Name "ProcessName" -Default ""))
        $key = if (-not [string]::IsNullOrWhiteSpace([string]$appId)) { "appid:$appId" } else { "name:$gameName" }
        if ($seen.ContainsKey($key)) {
            continue
        }

        $seen[$key] = $true
        $items += [pscustomobject]@{
            GameName    = $gameName
            SteamAppId  = if ([string]::IsNullOrWhiteSpace([string]$appId)) { $null } else { $appId }
            ProcessName = Get-ObjectValue -Object $process -Name "ProcessName" -Default $null
            Path        = Get-ObjectValue -Object $process -Name "Path" -Default $null
            ManifestPath = Get-ObjectValue -Object $process -Name "ManifestPath" -Default $null
        }
    }

    return @($items)
}

function Test-ListenerGameProfileMatch {
    param(
        [Parameter(Mandatory = $true)]$Rule,
        [Parameter(Mandatory = $true)]$GameSnapshot
    )

    $hasMatcher = $false

    $appId = [string](Get-ObjectValue -Object $GameSnapshot -Name "SteamAppId" -Default "")
    $gameName = [string](Get-ObjectValue -Object $GameSnapshot -Name "GameName" -Default "")
    $processName = [string](Get-ObjectValue -Object $GameSnapshot -Name "ProcessName" -Default "")
    $path = [string](Get-ObjectValue -Object $GameSnapshot -Name "Path" -Default "")
    $installDir = [string](Get-ObjectValue -Object $GameSnapshot -Name "InstallDir" -Default "")

    $ruleAppId = [string](Get-ObjectValue -Object $Rule -Name "appId" -Default "")
    if (-not [string]::IsNullOrWhiteSpace([string]$ruleAppId)) {
        $hasMatcher = $true
        if (-not [string]::Equals($appId, $ruleAppId, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $false
        }
    }

    foreach ($matcher in @(
            @{ Name = "namePattern"; Value = $gameName },
            @{ Name = "processPattern"; Value = $processName },
            @{ Name = "pathPattern"; Value = $path },
            @{ Name = "installDirPattern"; Value = $installDir }
        )) {
        $pattern = [string](Get-ObjectValue -Object $Rule -Name $matcher.Name -Default "")
        if ([string]::IsNullOrWhiteSpace([string]$pattern)) {
            continue
        }

        $hasMatcher = $true
        if (-not ([string]$matcher.Value -like $pattern)) {
            return $false
        }
    }

    return $hasMatcher
}

function Resolve-ListenerGameProfile {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$GameSnapshot,
        [Parameter(Mandatory = $true)][string]$DefaultOnGameStart,
        [Parameter(Mandatory = $true)][string]$DefaultOnGameExit
    )

    $listener = Get-ObjectValue -Object $Settings -Name "listener" -Default ([pscustomobject]@{})
    $rules = @(Get-ObjectValue -Object $listener -Name "gameProfiles" -Default @())

    foreach ($rule in $rules) {
        if (-not (Test-ListenerGameProfileMatch -Rule $rule -GameSnapshot $GameSnapshot)) {
            continue
        }

        $label = [string](Get-ObjectValue -Object $rule -Name "name" -Default "")
        if ([string]::IsNullOrWhiteSpace([string]$label)) {
            $label = [string](Get-ObjectValue -Object $rule -Name "appId" -Default (Get-ObjectValue -Object $rule -Name "namePattern" -Default "custom-game-profile"))
        }

        return [pscustomobject]@{
            matched      = $true
            profile_name = $label
            on_game_start = [string](Get-ObjectValue -Object $rule -Name "onGameStart" -Default $DefaultOnGameStart)
            on_game_exit  = [string](Get-ObjectValue -Object $rule -Name "onGameExit" -Default $DefaultOnGameExit)
        }
    }

    return [pscustomobject]@{
        matched      = $false
        profile_name = "default"
        on_game_start = $DefaultOnGameStart
        on_game_exit  = $DefaultOnGameExit
    }
}

function Invoke-Listen {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Profiles,
        [int]$RunForSeconds = 0
    )

    $listener = Get-ObjectValue -Object $Settings -Name "listener" -Default ([pscustomobject]@{})
    $pollIntervalSec = [int](Get-ObjectValue -Object $listener -Name "pollIntervalSec" -Default 3)
    $defaultOnGameStart = [string](Get-ObjectValue -Object $listener -Name "onGameStart" -Default "gaming")
    $defaultOnGameExit = [string](Get-ObjectValue -Object $listener -Name "onGameExit" -Default "restore")
    $listenerStatePath = Join-Path $script:StateDir "listener.json"

    $steam = Get-ActiveSteamGames -Settings $Settings
    $startedAt = Get-Date
    $tracked = $null

    if ($steam.library_roots.Count -eq 0 -or $steam.game_roots.Count -eq 0) {
        Write-Log "No Steam library roots were detected. Set listener.steamVdfPath in machine.local.json if Steam is installed in a non-standard location." "WARN"
        return [pscustomobject]@{
            status        = "no-steam-library"
            vdf_path      = $steam.vdf_path
            library_roots = $steam.library_roots
            game_roots    = $steam.game_roots
        }
    }

    if (-not (Get-ObjectValue -Object $Profiles -Name $defaultOnGameStart -Default $null)) {
        throw "Listener start mode '$defaultOnGameStart' was not found in profiles."
    }

    if ($defaultOnGameExit -ne "restore" -and -not (Get-ObjectValue -Object $Profiles -Name $defaultOnGameExit -Default $null)) {
        throw "Listener exit mode '$defaultOnGameExit' was not found in profiles."
    }

    foreach ($rule in @(Get-ObjectValue -Object $listener -Name "gameProfiles" -Default @())) {
        $startMode = [string](Get-ObjectValue -Object $rule -Name "onGameStart" -Default $defaultOnGameStart)
        $exitMode = [string](Get-ObjectValue -Object $rule -Name "onGameExit" -Default $defaultOnGameExit)

        if (-not (Get-ObjectValue -Object $Profiles -Name $startMode -Default $null)) {
            throw "Listener game profile start mode '$startMode' was not found in profiles."
        }

        if ($exitMode -ne "restore" -and -not (Get-ObjectValue -Object $Profiles -Name $exitMode -Default $null)) {
            throw "Listener game profile exit mode '$exitMode' was not found in profiles."
        }
    }

    Write-Log "Watching Steam game roots every $pollIntervalSec second(s). Press Ctrl+C to stop." "INFO"

    try {
        while ($true) {
            $candidates = @(Get-SteamGameProcessSnapshots -GameRoots $steam.game_roots -InstalledGames $steam.installed_games)

            if ($null -eq $tracked) {
                $candidate = $candidates | Select-Object -First 1
                if ($null -ne $candidate) {
                    $rule = Resolve-ListenerGameProfile -Settings $Settings -GameSnapshot $candidate -DefaultOnGameStart $defaultOnGameStart -DefaultOnGameExit $defaultOnGameExit
                    $startMode = [string](Get-ObjectValue -Object $rule -Name "on_game_start" -Default $defaultOnGameStart)
                    $exitMode = [string](Get-ObjectValue -Object $rule -Name "on_game_exit" -Default $defaultOnGameExit)

                    if ((Get-CurrentModeName) -ne $startMode) {
                        $script:ActionResults = @()
                        $null = Invoke-ModeProfile -ModeName $startMode -Settings $Settings -Profiles $Profiles
                    }

                    $tracked = [pscustomobject]@{
                        pid              = $candidate.Id
                        process_name     = $candidate.ProcessName
                        game_name        = Get-ObjectValue -Object $candidate -Name "GameName" -Default $candidate.ProcessName
                        steam_app_id     = Get-ObjectValue -Object $candidate -Name "SteamAppId" -Default $null
                        path             = $candidate.Path
                        manifest_path    = Get-ObjectValue -Object $candidate -Name "ManifestPath" -Default $null
                        library_root     = Get-ObjectValue -Object $candidate -Name "LibraryRoot" -Default $null
                        install_dir      = Get-ObjectValue -Object $candidate -Name "InstallDir" -Default $null
                        detected_at      = (Get-Date).ToString("o")
                        applied_mode     = $startMode
                        on_game_exit     = $exitMode
                        matched_profile  = Get-ObjectValue -Object $rule -Name "profile_name" -Default "default"
                    }
                    Write-JsonFile -Path $listenerStatePath -Object $tracked
                    Write-Log ("Detected Steam game: {0} ({1})" -f $tracked.game_name, $tracked.process_name) "INFO"
                }
            }
            else {
                $stillRunning = $candidates | Where-Object { $_.Id -eq $tracked.pid } | Select-Object -First 1
                if ($null -eq $stillRunning) {
                    Write-Log ("Tracked Steam game exited: {0}" -f $tracked.game_name) "INFO"
                    $script:ActionResults = @()
                    if ($tracked.on_game_exit -eq "restore") {
                        $null = Invoke-RestoreMode -Settings $Settings
                    }
                    else {
                        $null = Invoke-ModeProfile -ModeName ([string]$tracked.on_game_exit) -Settings $Settings -Profiles $Profiles
                    }

                    if (-not $WhatIfPreference -and (Test-Path -LiteralPath $listenerStatePath)) {
                        Remove-Item -LiteralPath $listenerStatePath -Force -ErrorAction SilentlyContinue
                    }
                    $tracked = $null
                }
            }

            if ($RunForSeconds -gt 0) {
                $elapsed = (New-TimeSpan -Start $startedAt -End (Get-Date)).TotalSeconds
                if ($elapsed -ge $RunForSeconds) {
                    break
                }
            }

            Start-Sleep -Seconds $pollIntervalSec
        }
    }
    finally {
        if ($null -eq $tracked -and -not $WhatIfPreference -and (Test-Path -LiteralPath $listenerStatePath)) {
            Remove-Item -LiteralPath $listenerStatePath -Force -ErrorAction SilentlyContinue
        }
    }

    return [pscustomobject]@{
        status          = "stopped"
        vdf_path        = $steam.vdf_path
        library_roots   = $steam.library_roots
        game_roots      = $steam.game_roots
        tracked_process = $tracked
    }
}
