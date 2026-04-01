# lib/health.ps1
# Cheap health snapshot and system detection.
# Depends on: config.ps1, state.ps1, actions.ps1
# Note: Get-RegistryDword, Get-RunningWslDistros, Find-ProcessesByPattern,
#       and Invoke-PowerCfgCommand are provided by actions.ps1 (sourced first).

function Test-IsAdministrator {
    $identity  = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-GameModeState {
    $path        = "HKCU:\Software\Microsoft\GameBar"
    $allowAuto   = Get-RegistryDword -Path $path -Name "AllowAutoGameMode"
    $autoEnabled = Get-RegistryDword -Path $path -Name "AutoGameModeEnabled"
    return [pscustomobject]@{
        allowAutoGameMode   = $allowAuto
        autoGameModeEnabled = $autoEnabled
        effectiveEnabled    = (($allowAuto -eq 1) -or ($autoEnabled -eq 1))
    }
}

function Get-ActivePowerPlanInfo {
    $rootPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes"
    $guid = $null
    try { $guid = [string](Get-ItemPropertyValue -Path $rootPath -Name "ActivePowerScheme" -ErrorAction Stop) } catch {}
    if (-not [string]::IsNullOrWhiteSpace($guid)) {
        $friendlyName = $null
        try {
            $planPath     = Join-Path $rootPath $guid
            $friendlyName = [string](Get-ItemPropertyValue -Path $planPath -Name "FriendlyName" -ErrorAction Stop)
            if ($friendlyName -match ",([^,]+)$") { $friendlyName = $Matches[1].Trim() } else { $friendlyName = $friendlyName.Trim() }
        } catch {}
        $raw = if ($friendlyName) { "{0} ({1})" -f $guid, $friendlyName } else { $guid }
        return [pscustomobject]@{ raw = $raw; guid = $guid }
    }
    $result = Invoke-PowerCfgCommand -Arguments @("/getactivescheme")
    $raw    = [string](Get-ObjectValue -Object $result -Name "output" -Default "")
    $match  = [regex]::Match($raw, "[0-9a-fA-F-]{36}")
    return [pscustomobject]@{ raw = $raw.Trim(); guid = if ($match.Success) { $match.Value } else { $null } }
}

function Get-TopCpuProcesses {
    param([int]$Top = 5)
    return @(Get-Process -ErrorAction SilentlyContinue |
        ForEach-Object {
            $cpu = $null
            try { $cpu = [math]::Round($_.TotalProcessorTime.TotalSeconds, 2) } catch {}
            [pscustomobject]@{ ProcessName = $_.ProcessName; Id = $_.Id; CPUSeconds = $cpu; WorkingSetMB = [math]::Round(($_.WorkingSet64/1MB),1) }
        } |
        Sort-Object @{ Expression = { if ($null -ne $_.CPUSeconds) { [double]$_.CPUSeconds } else { -1 } } } -Descending |
        Select-Object -First $Top)
}

function Get-HealthState {
    $modeName     = Get-CurrentModeName
    $powerPlan    = Get-ActivePowerPlanInfo
    $wslRunning   = @(Get-RunningWslDistros)
    $soundDevices = @()
    try { $soundDevices = @(Get-CimInstance Win32_SoundDevice -ErrorAction Stop | Select-Object -ExpandProperty Name) } catch {}
    $cpuAverage = $null
    try {
        $loads = @(Get-CimInstance Win32_Processor -ErrorAction Stop | Select-Object -ExpandProperty LoadPercentage)
        if ($loads.Count -gt 0) { $cpuAverage = [math]::Round((($loads | Measure-Object -Average).Average), 1) }
    } catch {}
    $freeMemMb = $null; $totalMemMb = $null
    try {
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $freeMemMb  = [math]::Round(($os.FreePhysicalMemory / 1024), 0)
        $totalMemMb = [math]::Round(($os.TotalVisibleMemorySize / 1024), 0)
    } catch {}
    $gameMode = Get-GameModeState
    $topCpu   = @(Get-TopCpuProcesses -Top 5)
    return [pscustomobject]@{
        timestamp           = (Get-Date).ToString("o")
        mode                = $modeName
        cpu_percent         = $cpuAverage
        free_mem_mb         = $freeMemMb
        total_mem_mb        = $totalMemMb
        power_plan_raw      = $powerPlan.raw
        power_plan_guid     = $powerPlan.guid
        wsl_active          = ($wslRunning.Count -gt 0)
        wsl_running_distros = $wslRunning
        docker_active       = (@(Find-ProcessesByPattern -Pattern "Docker*").Count -gt 0)
        game_mode_enabled   = $gameMode.effectiveEnabled
        sound_devices       = $soundDevices
        top_offenders       = @($topCpu | ForEach-Object { $_.ProcessName })
    }
}

function Invoke-Status {
    param([Parameter(Mandatory = $true)]$Settings)
    $status = Get-HealthState
    Save-CurrentState -State $status
    Add-RingBufferSample -Sample $status -Settings $Settings
    return $status
}
