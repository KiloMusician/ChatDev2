# lib/listener.ps1
# Steam game-watcher daemon (Feature A).
# Watches for Steam game processes → auto-applies gaming profile → restores on exit.
# Depends on: config.ps1, profiles.ps1

function Read-SteamVdf {
    param([Parameter(Mandatory = $true)][string]$Content)
    $paths = @()
    foreach ($line in ($Content -split "`n")) {
        if ($line -match '^\s*"path"\s+"(.+)"\s*$') {
            $rawPath = $Matches[1] -replace '\\\\', '\'
            $paths += $rawPath.Trim()
        }
    }
    return $paths
}

function Get-SteamLibraryPaths {
    param([string]$VdfOverridePath = $null)
    $vdfPath = $VdfOverridePath
    if ([string]::IsNullOrWhiteSpace($vdfPath)) {
        $vdfPath = Join-Path ${env:ProgramFiles(x86)} "Steam\config\libraryfolders.vdf"
    }
    if (-not (Test-Path -LiteralPath $vdfPath)) {
        Write-Log "Steam VDF not found at '$vdfPath'. Is Steam installed?" "WARN"
        return @()
    }
    try {
        $content = Get-Content -LiteralPath $vdfPath -Raw -ErrorAction Stop
        return @(Read-SteamVdf -Content $content)
    } catch {
        Write-Log "Failed to read Steam VDF: $($_.Exception.Message)" "WARN"
        return @()
    }
}

function Test-IsUnderSteamLibrary {
    param(
        [Parameter(Mandatory = $true)][string]$ExePath,
        [Parameter(Mandatory = $true)][string[]]$LibraryPaths
    )
    foreach ($libPath in $LibraryPaths) {
        if ($ExePath -like "$libPath*") { return $true }
    }
    return $false
}

function Find-SteamGameProcess {
    param([Parameter(Mandatory = $true)][string[]]$LibraryPaths)
    if ($LibraryPaths.Count -eq 0) { return $null }
    $candidates = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        try {
            $exePath = $_.MainModule.FileName
            $exePath -and (Test-IsUnderSteamLibrary -ExePath $exePath -LibraryPaths $LibraryPaths)
        } catch { $false }
    })
    return ($candidates | Select-Object -First 1)
}

function Invoke-Listen {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Profiles
    )
    $listenerCfg  = Get-ObjectValue -Object $Settings -Name "listener" -Default ([pscustomobject]@{})
    $pollInterval = [int](Get-ObjectValue  -Object $listenerCfg -Name "pollIntervalSec" -Default 3)
    $vdfOverride  = Get-ObjectValue        -Object $listenerCfg -Name "steamVdfPath"    -Default $null
    $onGameStart  = Get-ObjectValue        -Object $listenerCfg -Name "onGameStart"     -Default "gaming"
    $onGameExit   = Get-ObjectValue        -Object $listenerCfg -Name "onGameExit"      -Default "restore"

    $listenerStatePath = Join-Path $script:StateDir "listener.json"

    Write-Log "Discovering Steam library paths..." "INFO"
    $libraryPaths = @(Get-SteamLibraryPaths -VdfOverridePath $vdfOverride)
    if ($libraryPaths.Count -eq 0) {
        Write-Log "No Steam libraries found. Listening anyway (manual mode trigger still works)." "WARN"
    } else {
        Write-Log ("Steam libraries: {0}" -f ($libraryPaths -join "; ")) "INFO"
    }

    Write-Log "Listening for Steam game launches. Press Ctrl+C to stop." "INFO"

    $trackedPid     = $null
    $trackedExe     = $null
    $gameModeActive = $false

    $existing = Read-JsonFile -Path $listenerStatePath -Default $null
    if ($null -ne $existing) {
        $trackedPid     = Get-ObjectValue -Object $existing -Name "game_pid" -Default $null
        $trackedExe     = Get-ObjectValue -Object $existing -Name "game_exe" -Default $null
        $gameModeActive = $true
        Write-Log "Resuming tracking of previously detected game: $trackedExe (PID $trackedPid)" "INFO"
    }

    while ($true) {
        if (-not $gameModeActive) {
            $gameProc = Find-SteamGameProcess -LibraryPaths $libraryPaths
            if ($null -ne $gameProc) {
                $trackedPid     = $gameProc.Id
                $trackedExe     = $gameProc.ProcessName
                $gameModeActive = $true
                Write-Log "Game detected: $trackedExe (PID $trackedPid) — applying '$onGameStart' profile." "INFO"
                $gamePath = try { $gameProc.MainModule.FileName } catch { "unknown" }
                $listenerState = [pscustomobject]@{
                    game_exe    = $trackedExe
                    game_path   = $gamePath
                    game_pid    = $trackedPid
                    detected_at = (Get-Date).ToString("o")
                    prior_mode  = Get-CurrentModeName
                }
                Write-JsonFile -Path $listenerStatePath -Object $listenerState
                $script:ActionResults = @()
                $currentMode = Get-CurrentModeName
                if ($currentMode -ne $onGameStart) {
                    try { Invoke-ModeProfile -ModeName $onGameStart -Settings $Settings -Profiles $Profiles | Out-Null }
                    catch { Write-Log "Failed to apply '$onGameStart' profile: $($_.Exception.Message)" "ERROR" }
                } else {
                    Write-Log "Already in '$onGameStart' mode — skipping re-apply." "INFO"
                }
            }
        } else {
            $stillRunning = [bool](Get-Process -Id $trackedPid -ErrorAction SilentlyContinue)
            if (-not $stillRunning) {
                Write-Log "Game exited: $trackedExe — applying '$onGameExit' profile." "INFO"
                Remove-Item $listenerStatePath -ErrorAction SilentlyContinue
                $gameModeActive = $false
                $trackedPid     = $null
                $trackedExe     = $null
                $script:ActionResults = @()
                try { Invoke-RestoreMode -Settings $Settings | Out-Null }
                catch { Write-Log "Failed to apply '$onGameExit' profile: $($_.Exception.Message)" "ERROR" }
            }
        }
        Start-Sleep -Seconds $pollInterval
    }
}
