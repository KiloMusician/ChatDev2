function Test-AnomalyConditions {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Sample,
        [Parameter(Mandatory = $true)]$State,
        [Nullable[bool]]$NahimicDetectedOverride = $null,
        [Nullable[int]]$AudioRiskProcessCountOverride = $null
    )

    $anomaly = Get-ObjectValue -Object $Settings -Name "anomaly" -Default ([pscustomobject]@{})
    $enabled = [bool](Get-ObjectValue -Object $anomaly -Name "enabled" -Default $true)
    $cpuThreshold = [int](Get-ObjectValue -Object $anomaly -Name "cpuSpikePercent" -Default 80)
    $sustainSamples = [int](Get-ObjectValue -Object $anomaly -Name "spikeSustainSamples" -Default 3)
    $captureNahimic = [bool](Get-ObjectValue -Object $anomaly -Name "captureOnNahimicDetected" -Default $true)
    $audioRiskIncrease = [int](Get-ObjectValue -Object $anomaly -Name "audioRiskNewProcesses" -Default 2)

    $capturedSignatures = @()
    foreach ($signature in @(Get-ObjectValue -Object $State -Name "capturedSignatures" -Default @())) {
        $capturedSignatures += [string]$signature
    }

    if (-not $enabled) {
        return [pscustomobject]@{
            should_capture = $false
            reasons        = @()
            state          = [pscustomobject]@{
                cpuSpikeSamples   = 0
                nahimicSeen       = $false
                lastAudioRiskCount = 0
                capturedSignatures = $capturedSignatures
            }
        }
    }

    $cpuPercent = Get-ObjectValue -Object $Sample -Name "cpu_percent" -Default 0
    $cpuSpikeSamples = [int](Get-ObjectValue -Object $State -Name "cpuSpikeSamples" -Default 0)
    if ($null -ne $cpuPercent -and [double]$cpuPercent -ge $cpuThreshold) {
        $cpuSpikeSamples += 1
    }
    else {
        $cpuSpikeSamples = 0
    }

    if ($NahimicDetectedOverride -ne $null) {
        $nahimicDetected = [bool]$NahimicDetectedOverride
    }
    else {
        $doctor = Get-ObjectValue -Object $Settings -Name "doctor" -Default ([pscustomobject]@{})
        $servicePatterns = @(Get-ObjectValue -Object $doctor -Name "nahimicServicePatterns" -Default @("Nahimic*"))
        $processPatterns = @(Get-ObjectValue -Object $doctor -Name "nahimicProcessPatterns" -Default @("Nahimic*"))
        $nahimicDetected = (@(Get-ServiceSnapshotsByPatterns -Patterns $servicePatterns).Count -gt 0) -or (@(Get-ProcessSnapshotsByPatterns -Patterns $processPatterns).Count -gt 0)
    }

    if ($AudioRiskProcessCountOverride -ne $null) {
        $audioRiskProcessCount = [int]$AudioRiskProcessCountOverride
    }
    else {
        $doctor = Get-ObjectValue -Object $Settings -Name "doctor" -Default ([pscustomobject]@{})
        $audioRiskPatterns = @(Get-ObjectValue -Object $doctor -Name "audioRiskProcessPatterns" -Default @())
        $audioRiskNames = @()
        foreach ($pattern in $audioRiskPatterns) {
            $audioRiskNames += @(Find-ProcessesByPattern -Pattern ([string]$pattern) | Select-Object -ExpandProperty ProcessName)
        }
        $audioRiskProcessCount = @($audioRiskNames | Sort-Object -Unique).Count
    }

    $lastAudioRiskCount = [int](Get-ObjectValue -Object $State -Name "lastAudioRiskCount" -Default 0)
    $nahimicSeen = [bool](Get-ObjectValue -Object $State -Name "nahimicSeen" -Default $false)
    $initialized = [bool](Get-ObjectValue -Object $State -Name "initialized" -Default $false)
    $reasons = @()

    if ($cpuSpikeSamples -ge $sustainSamples -and -not ($capturedSignatures -contains "cpu")) {
        $reasons += ("CPU stayed above {0}% for {1} consecutive samples." -f $cpuThreshold, $cpuSpikeSamples)
        $capturedSignatures += "cpu"
    }

    if ($initialized -and $captureNahimic -and $nahimicDetected -and -not $nahimicSeen -and -not ($capturedSignatures -contains "nahimic")) {
        $reasons += "Nahimic was detected after the watch session started."
        $capturedSignatures += "nahimic"
    }

    if ($initialized -and ($audioRiskProcessCount - $lastAudioRiskCount) -ge $audioRiskIncrease -and -not ($capturedSignatures -contains "audio-risk")) {
        $reasons += ("Audio-risk background process count increased by {0}." -f ($audioRiskProcessCount - $lastAudioRiskCount))
        $capturedSignatures += "audio-risk"
    }

    return [pscustomobject]@{
        should_capture = ($reasons.Count -gt 0)
        reasons        = @($reasons)
        state          = [pscustomobject]@{
            initialized        = $true
            cpuSpikeSamples    = $cpuSpikeSamples
            nahimicSeen        = ($nahimicSeen -or $nahimicDetected)
            lastAudioRiskCount = $audioRiskProcessCount
            capturedSignatures = @($capturedSignatures | Sort-Object -Unique)
        }
    }
}

function Invoke-AnomalyCapture {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Sample,
        [Parameter(Mandatory = $true)][string[]]$Reasons
    )

    $timestamp = Get-Date -Format "yyyy-MM-ddTHH-mm-ss"
    $outputPath = Join-Path $script:IncidentsDir ("anomaly-{0}.json" -f $timestamp)

    $bundle = [pscustomobject]@{
        report_type      = "anomaly"
        exported_at      = (Get-Date).ToString("o")
        trigger_reasons  = @($Reasons)
        current_state    = $Sample
        rollback_state   = Read-JsonFile -Path $script:RollbackPath -Default $null
        recent_sessions  = Get-RecentSessions -Max 10
        doctor_report    = Get-DoctorReport -Settings $Settings
    }

    if ($WhatIfPreference) {
        return $outputPath
    }

    Write-JsonFile -Path $outputPath -Object $bundle
    return $outputPath
}

function Invoke-Watch {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [int]$RunForSeconds = 0
    )

    $watch = Get-ObjectValue -Object $Settings -Name "watch" -Default ([pscustomobject]@{})
    $interval = [int](Get-ObjectValue -Object $watch -Name "sampleIntervalSec" -Default 5)
    $startedAt = Get-Date
    $lastNotice = $null
    $anomalyState = [pscustomobject]@{
        initialized        = $false
        cpuSpikeSamples    = 0
        nahimicSeen        = $false
        lastAudioRiskCount = 0
        capturedSignatures = @()
    }

    Write-Log "Watching state every $interval second(s). Press Ctrl+C to stop." "INFO"

    while ($true) {
        $sample = Invoke-Status -Settings $Settings
        $display = [pscustomobject]@{
            timestamp     = Get-ObjectValue -Object $sample -Name "timestamp"
            mode          = Get-ObjectValue -Object $sample -Name "mode"
            cpu_percent   = Get-ObjectValue -Object $sample -Name "cpu_percent"
            free_mem_mb   = Get-ObjectValue -Object $sample -Name "free_mem_mb"
            wsl_active    = Get-ObjectValue -Object $sample -Name "wsl_active"
            docker_active = Get-ObjectValue -Object $sample -Name "docker_active"
            top_offenders = (Get-ObjectValue -Object $sample -Name "top_offenders" -Default @()) -join ", "
        }

        $anomalyResult = Test-AnomalyConditions -Settings $Settings -Sample $sample -State $anomalyState
        $anomalyState = $anomalyResult.state

        if ($anomalyResult.should_capture) {
            $capturePath = Invoke-AnomalyCapture -Settings $Settings -Sample $sample -Reasons $anomalyResult.reasons
            if ($capturePath) {
                $lastNotice = "[ANOMALY] Captured -> $capturePath"
            }
        }

        Clear-Host
        $display | Format-List
        if ($lastNotice) {
            Write-Host ""
            Write-Host $lastNotice -ForegroundColor Yellow
        }

        if ($RunForSeconds -gt 0) {
            $elapsed = (New-TimeSpan -Start $startedAt -End (Get-Date)).TotalSeconds
            if ($elapsed -ge $RunForSeconds) {
                break
            }
        }

        Start-Sleep -Seconds $interval
    }
}
