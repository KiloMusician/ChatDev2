# lib/doctor.ps1
# Expensive diagnostics: Nahimic, audio risk, LatencyMon (E), GPU mode (F).
# Depends on: config.ps1, health.ps1, actions.ps1

# ── Feature E helpers ────────────────────────────────────────────────────────

function Resolve-DriverCause {
    param([Parameter(Mandatory = $true)][string]$DriverName)
    $map = @{
        "nvlddmkm.sys" = "NVIDIA display driver — update via GeForce Experience or nvidia.com"
        "ndis.sys"      = "Network adapter driver — update in Device Manager or disable Wi-Fi during gaming"
        "HDAudBus.sys"  = "Audio driver itself — check Realtek/Nahimic stack"
        "ACPI.sys"      = "Power management / BIOS firmware — check for BIOS update on MSI support site"
        "dxgkrnl.sys"   = "DirectX GPU scheduler — update GPU driver"
        "storahci.sys"  = "Storage controller — update via Device Manager"
        "tcpip.sys"     = "TCP/IP stack — try disabling Wi-Fi adapter while gaming"
        "Wdf01000.sys"  = "Windows Driver Framework — Windows Update may resolve"
    }
    foreach ($key in $map.Keys) {
        if ($DriverName -like "*$key*") { return $map[$key] }
    }
    return "Unknown driver — search '$DriverName' in LatencyMon documentation"
}

function Parse-LatencyMonReport {
    param([Parameter(Mandatory = $true)][string]$ReportText)
    $lines   = $ReportText -split "`n"
    $drivers = [ordered]@{}

    foreach ($line in $lines) {
        # Match: "Driver with highest ISR/DPC routine execution time: foo.sys"
        if ($line -match "Driver with highest.+time:\s*(.+\.sys)") {
            $driverName = $Matches[1].Trim()
            if (-not $drivers.Contains($driverName)) { $drivers[$driverName] = 0.0 }
        }
        # Match: "Highest reported ISR/DPC routine execution time.*: 312.40"
        if ($line -match "Highest reported .+ execution time.*:\s*([\d.]+)") {
            $timeUs = [double]$Matches[1]
            $lastDriver = @($drivers.Keys)[-1]
            if ($null -ne $lastDriver -and $timeUs -gt $drivers[$lastDriver]) {
                $drivers[$lastDriver] = $timeUs
            }
        }
    }

    $topDrivers = @($drivers.GetEnumerator() |
        Sort-Object Value -Descending |
        Select-Object -First 3 |
        ForEach-Object {
            [pscustomobject]@{
                driver    = $_.Key
                maxTimeUs = [math]::Round($_.Value, 2)
                cause     = Resolve-DriverCause -DriverName $_.Key
            }
        })

    return [pscustomobject]@{
        topDrivers     = $topDrivers
        raw_line_count = $lines.Count
    }
}

function Get-LatencyMonAutoPath {
    param([string[]]$SearchPaths = @())
    if (-not $SearchPaths -or $SearchPaths.Count -eq 0) {
        $SearchPaths = @(
            [Environment]::GetFolderPath("Desktop"),
            [Environment]::GetFolderPath("MyDocuments")
        )
    }
    foreach ($dir in $SearchPaths) {
        if (-not (Test-Path $dir)) { continue }
        $file = Get-ChildItem -LiteralPath $dir -Filter "LatencyMon*.txt" -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
        if ($file) { return $file.FullName }
    }
    return $null
}

# ── Feature F helper ─────────────────────────────────────────────────────────

function Get-GpuModeInfo {
    $basePath   = "HKLM:\SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    $adapterKey = Join-Path $basePath "0000"
    $value = $null
    try { $value = Get-ItemPropertyValue -Path $adapterKey -Name "MSHybridEnabled" -ErrorAction Stop } catch {}
    if ($null -eq $value) {
        return [pscustomobject]@{ detected = $false; mode = "unknown"; note = "GPU mode switching not detected (non-MSI or key absent)" }
    }
    if ($value -eq 1) {
        return [pscustomobject]@{ detected = $true; mode = "MSHybrid"; note = "MSHybrid active — switch to Discrete Only in MSI Center before gaming for lower DPC latency" }
    }
    return [pscustomobject]@{ detected = $true; mode = "DiscreteOnly"; note = "Discrete Only — optimal for gaming" }
}

# ── Diagnostic helpers ────────────────────────────────────────────────────────

function Get-ServiceSnapshotsByPatterns {
    param([string[]]$Patterns)
    $allServices = @(Get-Service -ErrorAction SilentlyContinue)
    $results = @()
    foreach ($pattern in $Patterns) {
        $results += @($allServices | Where-Object { $_.Name -like $pattern -or $_.DisplayName -like $pattern } |
            Select-Object Name, DisplayName, Status, StartType)
    }
    return $results
}

function Get-ProcessSnapshotsByPatterns {
    param([string[]]$Patterns)
    $results = @()
    foreach ($pattern in $Patterns) {
        $results += @(Find-ProcessesByPattern -Pattern $pattern |
            Select-Object ProcessName, Id,
                @{ Name="CPU_s"; Expression={ try { [math]::Round($_.TotalProcessorTime.TotalSeconds,2) } catch { $null } } },
                @{ Name="WS_MB"; Expression={ [math]::Round($_.WorkingSet64/1MB,1) } })
    }
    return $results
}

function Get-InstalledPackagesByPattern {
    param([string]$DisplayNamePattern)
    $paths = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    )
    $results = @()
    foreach ($path in $paths) {
        if (-not (Test-Path $path)) { continue }
        $results += @(Get-ChildItem $path -ErrorAction SilentlyContinue |
            ForEach-Object { Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue } |
            Where-Object { $_.DisplayName -match $DisplayNamePattern } |
            Select-Object DisplayName, DisplayVersion, Publisher, InstallDate)
    }
    return $results
}

function Get-AudioDriverSnapshots {
    try {
        return @(Get-CimInstance Win32_PnPSignedDriver -ErrorAction Stop |
            Where-Object { $null -ne $_.DeviceName -and ([string]$_.DeviceName) -match "Realtek|Nahimic|Audio|Smart Sound" } |
            Select-Object DeviceName, DriverVersion, DriverDate, Manufacturer)
    } catch { return @() }
}

function Get-LatencyMonSummary {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) {
        $Path = Get-LatencyMonAutoPath
    }
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return [pscustomobject]@{ provided = $false; found = $false; auto_discovered = $false; top_drivers = @(); notes = @("No LatencyMon report path provided and none found on Desktop/Documents.") }
    }
    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{ provided = $true; found = $false; auto_discovered = $false; path = $Path; top_drivers = @(); notes = @("LatencyMon report path provided but file not found.") }
    }
    try {
        $content = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
        $parsed  = Parse-LatencyMonReport -ReportText $content
        return [pscustomobject]@{ provided = $true; found = $true; auto_discovered = $false; path = $Path; top_drivers = $parsed.topDrivers; notes = @() }
    } catch {
        return [pscustomobject]@{ provided = $true; found = $true; path = $Path; top_drivers = @(); notes = @("Could not read LatencyMon report: $($_.Exception.Message)") }
    }
}

function Get-RecentSessions {
    param([int]$Max = 10)
    return @(Get-ChildItem -LiteralPath $script:SessionsDir -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First $Max |
        ForEach-Object { Read-JsonFile -Path $_.FullName -Default $null } |
        Where-Object { $null -ne $_ })
}

function Get-DoctorReport {
    param([Parameter(Mandatory = $true)]$Settings)
    $doctor  = Get-ObjectValue -Object $Settings -Name "doctor" -Default ([pscustomobject]@{})
    $cpuWarn = [int](Get-ObjectValue -Object $doctor -Name "cpuWarningPercent" -Default 60)
    $nahimicSvcPatterns  = @(Get-ObjectValue -Object $doctor -Name "nahimicServicePatterns"  -Default @("Nahimic*"))
    $nahimicProcPatterns = @(Get-ObjectValue -Object $doctor -Name "nahimicProcessPatterns"  -Default @("Nahimic*"))
    $audioRiskPatterns   = @(Get-ObjectValue -Object $doctor -Name "audioRiskProcessPatterns" -Default @())

    $health    = Get-HealthState
    $findings  = @()
    $riskScore = 0

    if (-not $script:IsAdmin) { $findings += "Not running as administrator — service control unavailable." }

    $nahimicSvcs  = @($nahimicSvcPatterns  | ForEach-Object { @(Get-Service -Name $_ -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name) } | Sort-Object -Unique)
    $nahimicProcs = @($nahimicProcPatterns | ForEach-Object { @(Find-ProcessesByPattern -Pattern $_ | Select-Object -ExpandProperty ProcessName) } | Sort-Object -Unique)
    if ($nahimicSvcs.Count -gt 0 -or $nahimicProcs.Count -gt 0) {
        $findings  += "Nahimic services or processes detected (common MSI audio conflict)."
        $riskScore += 2
    }

    if ($health.docker_active) { $findings += "Docker Desktop is active."; $riskScore++ }
    if ($health.wsl_active)    { $findings += "WSL is running: $($health.wsl_running_distros -join ', ')."; $riskScore++ }

    $cpuPercent = $health.cpu_percent
    if ($null -ne $cpuPercent -and [double]$cpuPercent -ge $cpuWarn) {
        $findings += "CPU usage is high ($cpuPercent%)."; $riskScore++
    }

    $activeAudioRisk = @()
    foreach ($pattern in $audioRiskPatterns) {
        $activeAudioRisk += @(Find-ProcessesByPattern -Pattern $pattern | Select-Object -ExpandProperty ProcessName)
    }
    $activeAudioRisk = @($activeAudioRisk | Sort-Object -Unique)
    if ($activeAudioRisk.Count -gt 0) {
        $findings += "Audio-risk processes active: $($activeAudioRisk -join ', ')."; $riskScore++
    }

    $riskLevel = if ($riskScore -ge 4) { "high" } elseif ($riskScore -ge 2) { "medium" } else { "low" }
    $gpuMode   = Get-GpuModeInfo

    return [pscustomobject]@{
        timestamp           = $health.timestamp
        risk_level          = $riskLevel
        risk_score          = $riskScore
        findings            = $findings
        nahimic_services    = $nahimicSvcs
        nahimic_processes   = $nahimicProcs
        audio_risk_active   = $activeAudioRisk
        top_offenders       = $health.top_offenders
        wsl_running_distros = $health.wsl_running_distros
        power_plan_raw      = $health.power_plan_raw
        game_mode_enabled   = $health.game_mode_enabled
        gpu_mode            = $gpuMode.mode
        gpu_mode_note       = $gpuMode.note
        cpu_percent         = $cpuPercent
    }
}

function Get-AudioTriageReport {
    param([Parameter(Mandatory = $true)]$Settings, [string]$LatencyMonReportPath)
    $doctor              = Get-ObjectValue -Object $Settings -Name "doctor" -Default ([pscustomobject]@{})
    $nahimicSvcPatterns  = @(Get-ObjectValue -Object $doctor -Name "nahimicServicePatterns"  -Default @("Nahimic*"))
    $nahimicProcPatterns = @(Get-ObjectValue -Object $doctor -Name "nahimicProcessPatterns"  -Default @("Nahimic*"))
    $serviceDetails  = @(Get-ServiceSnapshotsByPatterns  -Patterns $nahimicSvcPatterns)
    $processDetails  = @(Get-ProcessSnapshotsByPatterns  -Patterns $nahimicProcPatterns)
    $audioDrivers    = @(Get-AudioDriverSnapshots)
    $installedPkgs   = @(Get-InstalledPackagesByPattern -DisplayNamePattern "Nahimic|Realtek Audio|A-Volute")
    $latencyMon      = Get-LatencyMonSummary -Path $LatencyMonReportPath

    $recommendedAction = "collect-latencymon"
    if ($serviceDetails.Count -gt 0 -or $processDetails.Count -gt 0) { $recommendedAction = "disable-nahimic-first" }
    if ($latencyMon.top_drivers.Count -gt 0 -and $latencyMon.top_drivers[0].driver -notmatch "Nahimic") {
        $recommendedAction = "investigate-top-driver"
    }

    return [pscustomobject]@{
        timestamp          = (Get-Date).ToString("o")
        nahimic_services   = $serviceDetails
        nahimic_processes  = $processDetails
        audio_drivers      = $audioDrivers
        installed_packages = $installedPkgs
        latencymon         = $latencyMon
        recommended_action = $recommendedAction
    }
}
