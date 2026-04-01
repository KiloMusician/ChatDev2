function Get-TopCpuProcesses {
    param([int]$Top = 5)

    return @(Get-Process -ErrorAction SilentlyContinue |
        ForEach-Object {
            $cpuSeconds = $null
            try {
                $cpuSeconds = [math]::Round($_.TotalProcessorTime.TotalSeconds, 2)
            }
            catch {
                $cpuSeconds = $null
            }

            [pscustomobject]@{
                ProcessName   = $_.ProcessName
                Id            = $_.Id
                CPUSeconds    = $cpuSeconds
                WorkingSetMB  = [math]::Round(($_.WorkingSet64 / 1MB), 1)
            }
        } |
        Sort-Object @{ Expression = { if ($null -ne $_.CPUSeconds) { [double]$_.CPUSeconds } else { -1 } } } -Descending |
        Select-Object -First $Top)
}

function Get-HealthState {
    $modeName = Get-CurrentModeName
    $powerPlan = Get-ActivePowerPlanInfo
    $wslRunning = @(Get-RunningWslDistros)
    $dockerProcesses = @(Find-ProcessesByPatterns -Patterns (Get-DockerProcessPatterns))
    $soundDevices = @()

    try {
        $soundDevices = @(Get-CimInstance Win32_SoundDevice -ErrorAction Stop | Select-Object -ExpandProperty Name)
    }
    catch {
        $soundDevices = @()
    }

    $cpuAverage = $null
    try {
        $processorLoad = @(Get-CimInstance Win32_Processor -ErrorAction Stop | Select-Object -ExpandProperty LoadPercentage)
        if ($processorLoad.Count -gt 0) {
            $cpuAverage = [math]::Round((($processorLoad | Measure-Object -Average).Average), 1)
        }
    }
    catch {
        $cpuAverage = $null
    }

    $freeMemMb = $null
    $totalMemMb = $null
    try {
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $freeMemMb = [math]::Round(($os.FreePhysicalMemory / 1024), 0)
        $totalMemMb = [math]::Round(($os.TotalVisibleMemorySize / 1024), 0)
    }
    catch {
        $freeMemMb = $null
        $totalMemMb = $null
    }

    $gameMode = Get-GameModeState
    $topCpu = @(Get-TopCpuProcesses -Top 5)

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
        docker_active       = ($dockerProcesses.Count -gt 0)
        game_mode_enabled   = $gameMode.effectiveEnabled
        sound_devices       = $soundDevices
        top_offenders       = @($topCpu | ForEach-Object { $_.ProcessName })
    }
}

function Get-ServiceSnapshotsByPatterns {
    param([string[]]$Patterns)

    $allServices = @(Get-Service -ErrorAction SilentlyContinue)
    $matchedNames = @()

    foreach ($pattern in @($Patterns)) {
        $matchedNames += @($allServices | Where-Object {
                $_.Name -like $pattern -or $_.DisplayName -like $pattern
            } | Select-Object -ExpandProperty Name)
    }

    $uniqueNames = @($matchedNames | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } | Sort-Object -Unique)
    $snapshots = @()

    foreach ($name in $uniqueNames) {
        $service = $allServices | Where-Object { $_.Name -eq $name } | Select-Object -First 1
        if ($null -eq $service) {
            continue
        }

        $imagePath = Get-ItemPropertyValue -Path ("HKLM:\SYSTEM\CurrentControlSet\Services\{0}" -f $service.Name) -Name "ImagePath" -ErrorAction SilentlyContinue

        $snapshots += [pscustomobject]@{
            Name        = $service.Name
            DisplayName = $service.DisplayName
            Status      = [string]$service.Status
            StartType   = [string]$service.StartType
            ImagePath   = $imagePath
        }
    }

    return @($snapshots)
}

function Get-ProcessSnapshotsByPatterns {
    param([string[]]$Patterns)

    $matches = @()
    foreach ($pattern in @($Patterns)) {
        $matches += @(Find-ProcessesByPattern -Pattern ([string]$pattern))
    }

    $items = @()
    foreach ($process in @($matches | Sort-Object Id -Unique)) {
        $cpuSeconds = $null
        try {
            $cpuSeconds = [math]::Round($process.TotalProcessorTime.TotalSeconds, 2)
        }
        catch {
            $cpuSeconds = $null
        }

        $items += [pscustomobject]@{
            ProcessName  = $process.ProcessName
            Id           = $process.Id
            CPUSeconds   = $cpuSeconds
            WorkingSetMB = [math]::Round(($process.WorkingSet64 / 1MB), 1)
        }
    }

    return @($items)
}

function Get-InstalledPackagesByPattern {
    param([Parameter(Mandatory = $true)][string]$DisplayNamePattern)

    $paths = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )

    $rawItems = @(Get-ItemProperty -Path $paths -ErrorAction SilentlyContinue |
        Where-Object {
            $displayName = Get-ObjectValue -Object $_ -Name "DisplayName" -Default $null
            $null -ne $displayName -and ([string]$displayName) -match $DisplayNamePattern
        } |
        Select-Object DisplayName, DisplayVersion, Publisher, InstallDate)

    $seen = @{}
    $items = @()
    foreach ($item in $rawItems) {
        $key = "{0}|{1}|{2}|{3}" -f $item.DisplayName, $item.DisplayVersion, $item.Publisher, $item.InstallDate
        if (-not $seen.ContainsKey($key)) {
            $seen[$key] = $true
            $items += $item
        }
    }

    return @($items | Sort-Object DisplayName, DisplayVersion)
}

function Get-AudioDriverSnapshots {
    try {
        return @(Get-CimInstance Win32_PnPSignedDriver -ErrorAction Stop |
            Where-Object {
                $null -ne $_.DeviceName -and ([string]$_.DeviceName) -match 'Realtek|Nahimic|Audio|Smart Sound'
            } |
            Select-Object DeviceName, DriverVersion, DriverDate, Manufacturer, InfName |
            Sort-Object DeviceName, DriverVersion)
    }
    catch {
        return @()
    }
}

function Get-LatencyMonAutoPath {
    param([string[]]$SearchPaths)

    $candidateDirs = @()
    if ($null -ne $SearchPaths) {
        foreach ($searchPath in $SearchPaths) {
            if (-not [string]::IsNullOrWhiteSpace([string]$searchPath)) {
                $candidateDirs += [string]$searchPath
            }
        }
    }

    if ($candidateDirs.Count -eq 0) {
        $candidateDirs = @(
            (Join-Path $env:USERPROFILE "Desktop"),
            (Join-Path $env:USERPROFILE "Documents")
        )
    }

    $matches = @()
    foreach ($dir in $candidateDirs) {
        if ([string]::IsNullOrWhiteSpace([string]$dir) -or -not (Test-Path -LiteralPath $dir)) {
            continue
        }

        $matches += @(Get-ChildItem -LiteralPath $dir -File -Filter "LatencyMon*.txt" -ErrorAction SilentlyContinue)
    }

    $newest = $matches | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($null -eq $newest) {
        return $null
    }

    return $newest.FullName
}

function Get-LatencyMonDriverGuidance {
    param([string]$DriverName)

    switch ($DriverName) {
        "nvlddmkm.sys" { return "NVIDIA display driver - update or clean reinstall the GPU driver." }
        "ndis.sys" { return "Network adapter driver - update Wi-Fi/LAN drivers and retest with networking disabled." }
        "HDAudBus.sys" { return "Windows audio bus - inspect the Realtek/Nahimic stack and audio device path." }
        "ACPI.sys" { return "Power management / BIOS firmware - review BIOS, MSI Center power mode, and CPU power behavior." }
        "dxgkrnl.sys" { return "DirectX GPU scheduler - test HAGS and windowed-game optimization changes." }
        "storahci.sys" { return "Storage controller - update chipset/storage drivers before blaming audio software." }
        "tcpip.sys" { return "TCP/IP stack - disable Wi-Fi temporarily and retest." }
        "RTKVHD64.sys" { return "Realtek audio driver - compare Nahimic-off behavior and consider MSI's clean reinstall path." }
        default {
            if ([string]::IsNullOrWhiteSpace([string]$DriverName)) {
                return $null
            }
            return "Investigate the reported driver directly; driver-level latency usually beats generic tweak packs."
        }
    }
}

function Resolve-MsiGpuModeValue {
    param([AllowNull()]$Value)

    if ($null -eq $Value) {
        return [pscustomobject]@{
            mode  = "Unknown"
            note  = "MSI GPU mode could not be detected on this machine."
            value = $null
        }
    }

    switch ([int]$Value) {
        0 {
            return [pscustomobject]@{
                mode  = "Discrete Only"
                note  = "dGPU always active - preferred for gaming when thermals and battery are acceptable."
                value = 0
            }
        }
        1 {
            return [pscustomobject]@{
                mode  = "MSHybrid"
                note  = "Switch to Discrete Only in MSI Center before gaming for lower DPC latency."
                value = 1
            }
        }
        default {
            return [pscustomobject]@{
                mode  = "Unknown"
                note  = ("Unexpected MSHybridEnabled value: {0}" -f $Value)
                value = [int]$Value
            }
        }
    }
}

function Get-MsiGpuModeInfo {
    $classRoots = @(
        "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}",
        "HKLM:\SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    )

    foreach ($classRoot in $classRoots) {
        if (-not (Test-Path -LiteralPath $classRoot)) {
            continue
        }

        $subkeys = @(Get-ChildItem -LiteralPath $classRoot -ErrorAction SilentlyContinue |
            Where-Object { $_.PSChildName -match '^\d{4}$' } |
            Sort-Object PSChildName)

        foreach ($subkey in $subkeys) {
            try {
                $value = Get-ItemPropertyValue -LiteralPath $subkey.PSPath -Name "MSHybridEnabled" -ErrorAction Stop
                $resolved = Resolve-MsiGpuModeValue -Value $value
                return [pscustomobject]@{
                    supported   = $true
                    mode        = $resolved.mode
                    note        = $resolved.note
                    value       = $resolved.value
                    source_path = $subkey.Name
                }
            }
            catch {
                continue
            }
        }
    }

    return [pscustomobject]@{
        supported   = $false
        mode        = "Unknown"
        note        = "MSHybridEnabled was not found; this may be a non-MSI system or a model without GPU switching."
        value       = $null
        source_path = $null
    }
}

function Get-LatencyMonSummary {
    param(
        [string]$Path,
        [string[]]$SearchPaths
    )

    $wasProvided = -not [string]::IsNullOrWhiteSpace([string]$Path)
    $wasAutoDiscovered = $false

    if (-not $wasProvided) {
        $Path = Get-LatencyMonAutoPath -SearchPaths $SearchPaths
        if (-not [string]::IsNullOrWhiteSpace([string]$Path)) {
            $wasAutoDiscovered = $true
        }
    }

    if ([string]::IsNullOrWhiteSpace([string]$Path)) {
        return [pscustomobject]@{
            provided        = $false
            exists          = $false
            auto_discovered = $false
            report_path     = $null
            top_driver      = $null
            driver_guidance = $null
            matched_drivers = @()
            matched_lines   = @()
            notes           = @("No LatencyMon report path was provided and no recent LatencyMon*.txt report was found on Desktop or Documents.")
        }
    }

    $expandedPath = [Environment]::ExpandEnvironmentVariables([string]$Path)
    if (-not (Test-Path -LiteralPath $expandedPath)) {
        return [pscustomobject]@{
            provided        = $wasProvided
            exists          = $false
            auto_discovered = $wasAutoDiscovered
            report_path     = $expandedPath
            top_driver      = $null
            driver_guidance = $null
            matched_drivers = @()
            matched_lines   = @()
            notes           = @("LatencyMon report path was provided but the file was not found.")
        }
    }

    $raw = ""
    $lines = @()
    try {
        $raw = Get-Content -LiteralPath $expandedPath -Raw -ErrorAction Stop
        $lines = @(Get-Content -LiteralPath $expandedPath -ErrorAction Stop)
    }
    catch {
        return [pscustomobject]@{
            provided        = $wasProvided
            exists          = $true
            auto_discovered = $wasAutoDiscovered
            report_path     = $expandedPath
            top_driver      = $null
            driver_guidance = $null
            matched_drivers = @()
            matched_lines   = @()
            notes           = @("LatencyMon report exists but could not be read.")
        }
    }

    $matchedDrivers = @([regex]::Matches($raw, '[A-Za-z0-9_+\-]+\.sys') | ForEach-Object { $_.Value } | Sort-Object -Unique)
    $matchedLines = @()
    foreach ($line in $lines) {
        $trimmed = ([string]$line).Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed)) {
            continue
        }

        if ($trimmed -match '\.sys' -or $trimmed -match 'Highest reported' -or $trimmed -match '\bDPC\b' -or $trimmed -match '\bISR\b') {
            $matchedLines += $trimmed
        }

        if ($matchedLines.Count -ge 20) {
            break
        }
    }

    $knownPriorityDrivers = @(
        "nvlddmkm.sys",
        "ndis.sys",
        "ACPI.sys",
        "dxgkrnl.sys",
        "HDAudBus.sys",
        "RTKVHD64.sys",
        "storahci.sys"
    )

    $topDriver = $null
    foreach ($driver in $knownPriorityDrivers) {
        if ($matchedDrivers -contains $driver) {
            $topDriver = $driver
            break
        }
    }

    $driverGuidance = Get-LatencyMonDriverGuidance -DriverName $topDriver

    return [pscustomobject]@{
        provided        = $wasProvided
        exists          = $true
        auto_discovered = $wasAutoDiscovered
        report_path     = $expandedPath
        top_driver      = $topDriver
        driver_guidance = $driverGuidance
        matched_drivers = $matchedDrivers
        matched_lines   = $matchedLines
        notes           = @()
    }
}

function Get-DoctorReport {
    param([Parameter(Mandatory = $true)]$Settings)

    $doctor = Get-ObjectValue -Object $Settings -Name "doctor" -Default ([pscustomobject]@{})
    $cpuWarningPercent = [int](Get-ObjectValue -Object $doctor -Name "cpuWarningPercent" -Default 60)
    $nahimicServicePatterns = @(Get-ObjectValue -Object $doctor -Name "nahimicServicePatterns" -Default @("Nahimic*"))
    $nahimicProcessPatterns = @(Get-ObjectValue -Object $doctor -Name "nahimicProcessPatterns" -Default @("Nahimic*"))
    $audioRiskProcessPatterns = @(Get-ObjectValue -Object $doctor -Name "audioRiskProcessPatterns" -Default @())

    $health = Get-HealthState
    $gpuMode = Get-MsiGpuModeInfo
    $steamGames = @()
    if (Get-Command Get-ActiveSteamGames -ErrorAction SilentlyContinue) {
        $steam = Get-ActiveSteamGames -Settings $Settings
        $steamGames = @(Get-UniqueSteamGameSummaries -Processes @(Get-ObjectValue -Object $steam -Name "processes" -Default @()))
    }
    $findings = @()
    $riskScore = 0

    if (-not $script:IsAdmin) {
        $findings += "The shell is not elevated, so service control actions will be skipped."
    }

    if ((Get-ObjectValue -Object $health -Name "wsl_active" -Default $false)) {
        $findings += "WSL is currently active."
        $riskScore += 1
    }

    if ((Get-ObjectValue -Object $health -Name "docker_active" -Default $false)) {
        $findings += "Docker-related processes are active."
        $riskScore += 1
    }

    if ($steamGames.Count -gt 0) {
        $findings += ("Active Steam game(s): {0}" -f (($steamGames | Select-Object -ExpandProperty GameName) -join ", "))
    }

    $cpuPercent = Get-ObjectValue -Object $health -Name "cpu_percent" -Default $null
    if ($null -ne $cpuPercent -and [double]$cpuPercent -ge $cpuWarningPercent) {
        $findings += "CPU load is currently high."
        $riskScore += 1
    }

    $nahimicServices = @()
    foreach ($pattern in $nahimicServicePatterns) {
        $nahimicServices += @(Get-Service -Name $pattern -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
    }

    $nahimicProcesses = @()
    foreach ($pattern in $nahimicProcessPatterns) {
        $nahimicProcesses += @(Find-ProcessesByPattern -Pattern ([string]$pattern) | Select-Object -ExpandProperty ProcessName)
    }

    if (@($nahimicServices).Count -gt 0 -or @($nahimicProcesses).Count -gt 0) {
        $findings += "Nahimic-related services or processes were detected."
        $riskScore += 2
    }

    $activeRiskProcesses = @()
    foreach ($pattern in $audioRiskProcessPatterns) {
        $activeRiskProcesses += @(Find-ProcessesByPattern -Pattern ([string]$pattern) | Select-Object -ExpandProperty ProcessName)
    }
    $activeRiskProcesses = @($activeRiskProcesses | Sort-Object -Unique)

    if ($activeRiskProcesses.Count -gt 0) {
        $findings += ("Potentially noisy background processes are active: {0}" -f ($activeRiskProcesses -join ", "))
        $riskScore += 1
    }

    if ($gpuMode.mode -eq "MSHybrid") {
        $findings += $gpuMode.note
        $riskScore += 1
    }

    $riskLevel = "low"
    if ($riskScore -ge 4) {
        $riskLevel = "high"
    }
    elseif ($riskScore -ge 2) {
        $riskLevel = "medium"
    }

    return [pscustomobject]@{
        generated_at        = (Get-Date).ToString("o")
        risk_level          = $riskLevel
        findings            = $findings
        cpu_percent         = $cpuPercent
        power_plan_raw      = Get-ObjectValue -Object $health -Name "power_plan_raw"
        game_mode_enabled   = Get-ObjectValue -Object $health -Name "game_mode_enabled"
        gpu_mode            = $gpuMode.mode
        gpu_mode_note       = $gpuMode.note
        gpu_mode_source     = $gpuMode.source_path
        wsl_running_distros = Get-ObjectValue -Object $health -Name "wsl_running_distros"
        sound_devices       = Get-ObjectValue -Object $health -Name "sound_devices"
        top_offenders       = Get-ObjectValue -Object $health -Name "top_offenders"
        steam_games         = $steamGames
        nahimic_services    = @($nahimicServices | Sort-Object -Unique)
        nahimic_processes   = @($nahimicProcesses | Sort-Object -Unique)
    }
}

function Get-AudioTriageReport {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [string]$LatencyMonReportPath
    )

    $doctor = Get-ObjectValue -Object $Settings -Name "doctor" -Default ([pscustomobject]@{})
    $nahimicServicePatterns = @(Get-ObjectValue -Object $doctor -Name "nahimicServicePatterns" -Default @("Nahimic*"))
    $nahimicProcessPatterns = @(Get-ObjectValue -Object $doctor -Name "nahimicProcessPatterns" -Default @("Nahimic*"))

    $doctorReport = Get-DoctorReport -Settings $Settings
    $serviceDetails = @(Get-ServiceSnapshotsByPatterns -Patterns $nahimicServicePatterns)
    $processDetails = @(Get-ProcessSnapshotsByPatterns -Patterns $nahimicProcessPatterns)
    $audioDrivers = @(Get-AudioDriverSnapshots)
    $installedPackages = @(Get-InstalledPackagesByPattern -DisplayNamePattern 'Nahimic|Realtek Audio|A-Volute')
    $latencyMon = Get-LatencyMonSummary -Path $LatencyMonReportPath

    $recommendationReasons = @()
    $nextSteps = @()
    $recommendedAction = "collect-latencymon"
    $recommendUninstallNow = $false

    if ($serviceDetails.Count -gt 0 -or $processDetails.Count -gt 0) {
        $recommendedAction = "disable-nahimic-first"
        $recommendationReasons += "Nahimic service/processes are active on this system."
        $nextSteps += "Temporarily stop NahimicService in an elevated shell and re-test the stutter before uninstalling anything."
    }

    if (@($audioDrivers | Where-Object { ([string]$_.DeviceName) -match 'Nahimic' }).Count -gt 0) {
        $recommendationReasons += "Nahimic audio components are present in the current driver stack."
    }

    if (@($audioDrivers | Where-Object { ([string]$_.DeviceName) -match 'Realtek High Definition Audio|Realtek Audio' }).Count -gt 0) {
        $nextSteps += "If the A/B test improves audio, use MSI's official Realtek/Nahimic clean reinstall path rather than a third-party cleanup script."
    }

    if ($latencyMon.auto_discovered) {
        $nextSteps += "Keeper auto-discovered the newest LatencyMon report on Desktop/Documents; rerun with -LatencyMonReportPath if you want to pin a different file."
    }

    if (-not $latencyMon.provided -and -not $latencyMon.auto_discovered) {
        $nextSteps += "Run LatencyMon for 10 to 15 minutes while reproducing the stutter, then rerun doctor/export with -LatencyMonReportPath."
    }
    elseif (-not $latencyMon.exists) {
        $nextSteps += "Fix the LatencyMon report path and rerun the export so the report can be attached to the bundle."
    }

    $driverFocusedActionMap = @{
        "nvlddmkm.sys" = "investigate-nvidia-driver"
        "ndis.sys"     = "investigate-network-driver"
        "ACPI.sys"     = "investigate-firmware-power"
        "dxgkrnl.sys"  = "investigate-gpu-scheduling"
        "HDAudBus.sys" = "investigate-audio-bus-driver"
        "RTKVHD64.sys" = "investigate-realtek-driver"
        "storahci.sys" = "investigate-storage-driver"
    }

    if ($latencyMon.top_driver) {
        $recommendationReasons += ("LatencyMon report references {0}." -f $latencyMon.top_driver)
        $mappedAction = Get-ObjectValue -Object $driverFocusedActionMap -Name $latencyMon.top_driver -Default $null
        if ($null -ne $mappedAction) {
            $recommendedAction = $mappedAction
        }

        if ($latencyMon.driver_guidance) {
            $nextSteps += $latencyMon.driver_guidance
        }

        switch ($latencyMon.top_driver) {
            "nvlddmkm.sys" {
                $nextSteps += "LatencyMon points at the NVIDIA path; update or clean reinstall the NVIDIA driver before blaming Nahimic alone."
            }
            "ndis.sys" {
                $nextSteps += "LatencyMon points at the network stack; disable Wi-Fi temporarily and retest to separate Wi-Fi DPC issues from audio software."
            }
            "ACPI.sys" {
                $nextSteps += "LatencyMon points at ACPI; test MSI Center power mode, BIOS updates, and CPU power behavior before uninstalling audio software."
            }
            "dxgkrnl.sys" {
                $nextSteps += "LatencyMon points at GPU scheduling; test HAGS/windowed-game optimization changes before removing Nahimic."
            }
            "HDAudBus.sys" {
                $nextSteps += "LatencyMon points at the Windows audio bus; disabling Nahimic is still a good reversible first A/B test."
            }
            "RTKVHD64.sys" {
                $nextSteps += "LatencyMon points at the Realtek path; if disabling Nahimic does not help, use MSI's official Realtek/Nahimic clean reinstall sequence."
            }
            "storahci.sys" {
                $nextSteps += "LatencyMon points at storage; investigate chipset/storage drivers before uninstalling audio software."
            }
        }
    }

    if ($recommendedAction -eq "disable-nahimic-first") {
        $nextSteps += "Do not uninstall Nahimic first. Disable it temporarily, compare behavior, then uninstall only if the A/B test is clearly positive or LatencyMon still implicates the audio path."
    }

    return [pscustomobject]@{
        generated_at             = (Get-Date).ToString("o")
        doctor_report            = $doctorReport
        recommended_action       = $recommendedAction
        recommend_uninstall_now  = $recommendUninstallNow
        recommendation_reasons   = @($recommendationReasons | Sort-Object -Unique)
        next_steps               = @($nextSteps | Sort-Object -Unique)
        nahimic_service_details  = $serviceDetails
        nahimic_process_details  = $processDetails
        audio_driver_inventory   = $audioDrivers
        installed_audio_packages = $installedPackages
        latencymon_summary       = $latencyMon
    }
}

function Get-ModeRecommendation {
    param([Parameter(Mandatory = $true)]$Settings)

    $health = Get-HealthState
    $recommendationCfg = Get-ObjectValue -Object $Settings -Name "recommendation" -Default ([pscustomobject]@{})
    $devPatterns = @(Get-ObjectValue -Object $recommendationCfg -Name "devProcessPatterns" -Default @(
            "Code",
            "Docker*",
            "com.docker.*",
            "dockerd*",
            "python*",
            "node*",
            "jupyter*",
            "ollama*",
            "LM Studio*"
        ))
    $preferBalancedWhenMixed = [bool](Get-ObjectValue -Object $recommendationCfg -Name "preferBalancedWhenMixed" -Default $true)

    $devProcesses = @(Get-ProcessSnapshotsByPatterns -Patterns $devPatterns)
    $gameProcesses = @()
    $activeGames = @()
    if (Get-Command Get-ActiveSteamGames -ErrorAction SilentlyContinue) {
        $steam = Get-ActiveSteamGames -Settings $Settings
        $gameProcesses = @(Get-ObjectValue -Object $steam -Name "processes" -Default @())
        $activeGames = @(Get-UniqueSteamGameSummaries -Processes $gameProcesses)
    }

    $hasDevLoad = (($devProcesses.Count -gt 0) -or
        (Get-ObjectValue -Object $health -Name "wsl_active" -Default $false) -or
        (Get-ObjectValue -Object $health -Name "docker_active" -Default $false))
    $hasGameLoad = ($gameProcesses.Count -gt 0)

    $recommendedMode = "balanced"
    $confidence = "high"
    $reasons = @()

    if ($hasGameLoad -and $hasDevLoad -and $preferBalancedWhenMixed) {
        $recommendedMode = "balanced"
        $confidence = "medium"
        $reasons += "Mixed workload detected: a game is running while dev workloads are still active."
        $reasons += "Balanced mode avoids unexpectedly killing coding tools until you explicitly choose gaming mode."
    }
    elseif ($hasGameLoad) {
        $recommendedMode = "gaming"
        $confidence = "high"
        $reasons += "Detected active Steam game process(es)."
        $reasons += "Gaming mode is the best fit when a game is already running and no competing dev stack needs to stay up."
    }
    elseif ($hasDevLoad) {
        $recommendedMode = "coding"
        $confidence = "high"
        $reasons += "Detected active development workloads such as Docker, WSL, or coding/model processes."
        $reasons += "Coding mode keeps the dev environment stable and avoids killing project tools."
    }
    else {
        $recommendedMode = "balanced"
        $confidence = "high"
        $reasons += "No active game process or heavy dev workload was detected."
        $reasons += "Balanced mode is the safest default for general work and idle use."
    }

    if ((Get-ObjectValue -Object $health -Name "cpu_percent" -Default 0) -ge 70) {
        $reasons += "CPU usage is already high, so mode changes should stay conservative."
    }

    return [pscustomobject]@{
        generated_at          = (Get-Date).ToString("o")
        current_mode          = Get-ObjectValue -Object $health -Name "mode" -Default "idle"
        recommended_mode      = $recommendedMode
        confidence            = $confidence
        reasons               = @($reasons | Sort-Object -Unique)
        active_dev_processes  = @($devProcesses | Select-Object -ExpandProperty ProcessName -Unique)
        active_game_processes = @($gameProcesses | Select-Object -ExpandProperty ProcessName -Unique)
        active_games          = @($activeGames)
        wsl_active            = Get-ObjectValue -Object $health -Name "wsl_active" -Default $false
        docker_active         = Get-ObjectValue -Object $health -Name "docker_active" -Default $false
        cpu_percent           = Get-ObjectValue -Object $health -Name "cpu_percent"
    }
}

function Invoke-Status {
    param([Parameter(Mandatory = $true)]$Settings)

    $status = Get-HealthState
    Save-CurrentState -State $status
    Append-RingBuffer -Sample $status -Settings $Settings
    return $status
}
