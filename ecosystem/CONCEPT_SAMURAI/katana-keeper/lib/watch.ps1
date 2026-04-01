# lib/watch.ps1
# Watch loop with anomaly auto-capture (Feature B).
# Depends on: config.ps1, state.ps1, health.ps1, doctor.ps1

function Test-AnomalyConditions {
    param(
        [Parameter(Mandatory = $true)]$Sample,
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$WatchState
    )
    $anomalyCfg     = Get-ObjectValue -Object $Settings -Name "anomaly" -Default ([pscustomobject]@{})
    $enabled        = [bool](Get-ObjectValue -Object $anomalyCfg -Name "enabled"                 -Default $true)
    if (-not $enabled) { return $false }

    $cpuThresh      = [int](Get-ObjectValue  -Object $anomalyCfg -Name "cpuSpikePercent"          -Default 80)
    $sustainSamples = [int](Get-ObjectValue  -Object $anomalyCfg -Name "spikeSustainSamples"      -Default 3)
    $captureNahimic = [bool](Get-ObjectValue -Object $anomalyCfg -Name "captureOnNahimicDetected" -Default $true)
    $riskIncrease   = [int](Get-ObjectValue  -Object $anomalyCfg -Name "audioRiskNewProcesses"    -Default 2)

    $cpu = $Sample.cpu_percent
    if ($null -ne $cpu -and [double]$cpu -ge $cpuThresh) {
        $WatchState.HighCpuStreak++
    } else {
        $WatchState.HighCpuStreak = 0
    }
    if ($WatchState.HighCpuStreak -ge $sustainSamples) { return $true }

    $topOffenders = @(Get-ObjectValue -Object $Sample -Name "top_offenders" -Default @())
    $nahimicFound = $topOffenders | Where-Object { $_ -like "Nahimic*" }
    if ($captureNahimic -and $nahimicFound -and -not $WatchState.NahimicSeenAtStart) { return $true }

    $currentRiskCount = @($topOffenders | Where-Object { $_ -match "^(chrome|msedge|firefox|Code|node|python|docker|jupyter)" }).Count
    if (($currentRiskCount - $WatchState.InitialRiskCount) -ge $riskIncrease) { return $true }

    return $false
}

function Invoke-AnomalyCapture {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Sample
    )
    Ensure-Directory -Path $script:IncidentsDir
    $timestamp  = Get-Date -Format "yyyy-MM-ddTHH-mm-ss"
    $outputPath = Join-Path $script:IncidentsDir "anomaly-$timestamp.json"
    $bundle = [pscustomobject]@{
        report_type     = "anomaly"
        captured_at     = (Get-Date).ToString("o")
        trigger_sample  = $Sample
        current_state   = Read-JsonFile -Path $script:CurrentStatePath -Default $null
        recent_sessions = @(Get-ChildItem -LiteralPath $script:SessionsDir -File -ErrorAction SilentlyContinue |
                            Sort-Object LastWriteTime -Descending | Select-Object -First 5 |
                            ForEach-Object { Read-JsonFile -Path $_.FullName -Default $null } |
                            Where-Object { $null -ne $_ })
    }
    $bundle | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $outputPath -Encoding UTF8
    Write-Host "`n[ANOMALY] Incident captured → $outputPath" -ForegroundColor Yellow
    return $outputPath
}

function Invoke-Watch {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [int]$RunForSeconds = 0
    )
    $watch     = Get-ObjectValue -Object $Settings -Name "watch" -Default ([pscustomobject]@{})
    $interval  = [int](Get-ObjectValue -Object $watch -Name "sampleIntervalSec" -Default 5)
    $startedAt = Get-Date

    $initialHealth = Get-HealthState
    $watchState = [pscustomobject]@{
        HighCpuStreak      = 0
        NahimicSeenAtStart = [bool](@($initialHealth.top_offenders | Where-Object { $_ -like "Nahimic*" }).Count -gt 0)
        InitialRiskCount   = @($initialHealth.top_offenders | Where-Object { $_ -match "^(chrome|msedge|firefox|Code|node|python|docker|jupyter)" }).Count
        AnomalyCaptured    = $false
    }

    Write-Log "Watching every $interval second(s). Press Ctrl+C to stop." "INFO"

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
        try { Clear-Host } catch {}
        $display | Format-List

        if (Test-AnomalyConditions -Sample $sample -Settings $Settings -WatchState $watchState) {
            Invoke-AnomalyCapture -Settings $Settings -Sample $sample | Out-Null
            $watchState.AnomalyCaptured = $true
            $watchState.HighCpuStreak   = 0   # reset to avoid capture spam
        }

        if ($RunForSeconds -gt 0) {
            $elapsed = (New-TimeSpan -Start $startedAt -End (Get-Date)).TotalSeconds
            if ($elapsed -ge $RunForSeconds) { break }
        }
        Start-Sleep -Seconds $interval
    }
}
