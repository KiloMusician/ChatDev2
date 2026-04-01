function Get-CurrentModeName {
    $state = Read-JsonFile -Path $script:CurrentStatePath -Default ([pscustomobject]@{ mode = "idle" })
    return (Get-ObjectValue -Object $state -Name "mode" -Default "idle")
}

function Save-CurrentState {
    param([Parameter(Mandatory = $true)]$State)
    Write-JsonFile -Path $script:CurrentStatePath -Object $State
}

function Save-RollbackState {
    param([Parameter(Mandatory = $true)]$Rollback)
    Write-JsonFile -Path $script:RollbackPath -Object $Rollback
}

function Append-RingBuffer {
    param(
        [Parameter(Mandatory = $true)]$Sample,
        [Parameter(Mandatory = $true)]$Settings
    )

    $watch = Get-ObjectValue -Object $Settings -Name "watch" -Default ([pscustomobject]@{})
    $maxSamples = [int](Get-ObjectValue -Object $watch -Name "ringBufferSamples" -Default 180)

    $existingRaw = Read-JsonFile -Path $script:RingBufferPath -Default @()
    $existing = @()
    if ($null -ne $existingRaw) {
        foreach ($item in $existingRaw) {
            $existing += $item
        }
    }

    $items = $existing + @($Sample)

    if ($items.Count -gt $maxSamples) {
        $items = $items[($items.Count - $maxSamples)..($items.Count - 1)]
    }

    Write-JsonFile -Path $script:RingBufferPath -Object $items
}

function Get-ActionSummary {
    param([Parameter(Mandatory = $true)]$Results)

    $items = @($Results)
    return [pscustomobject]@{
        total   = $items.Count
        changed = @($items | Where-Object { $_.changed }).Count
        skipped = @($items | Where-Object { $_.skipped }).Count
        failed  = @($items | Where-Object { -not $_.success }).Count
    }
}

function New-SessionSummary {
    param(
        [Parameter(Mandatory = $true)][string]$ModeName,
        [Parameter(Mandatory = $true)][datetime]$StartedAt,
        [Parameter(Mandatory = $true)][datetime]$EndedAt,
        [Parameter(Mandatory = $true)]$Before,
        [Parameter(Mandatory = $true)]$After,
        [Parameter(Mandatory = $true)]$Results,
        [string[]]$Notes = @()
    )

    $summary = [pscustomobject]@{
        session_id            = $StartedAt.ToString("yyyy-MM-ddTHH-mm-ss")
        mode                  = $ModeName
        started_at            = $StartedAt.ToString("o")
        ended_at              = $EndedAt.ToString("o")
        duration_min          = [math]::Round((($EndedAt - $StartedAt).TotalMinutes), 2)
        action_summary        = Get-ActionSummary -Results $Results
        cpu_percent_before    = Get-ObjectValue -Object $Before -Name "cpu_percent"
        cpu_percent_after     = Get-ObjectValue -Object $After -Name "cpu_percent"
        free_mem_mb_before    = Get-ObjectValue -Object $Before -Name "free_mem_mb"
        free_mem_mb_after     = Get-ObjectValue -Object $After -Name "free_mem_mb"
        wsl_active_before     = Get-ObjectValue -Object $Before -Name "wsl_active"
        wsl_active_after      = Get-ObjectValue -Object $After -Name "wsl_active"
        docker_active_before  = Get-ObjectValue -Object $Before -Name "docker_active"
        docker_active_after   = Get-ObjectValue -Object $After -Name "docker_active"
        top_offenders_after   = Get-ObjectValue -Object $After -Name "top_offenders" -Default @()
        notes                 = @($Notes)
    }

    $summaryPath = Join-Path $script:SessionsDir ("{0}-{1}.json" -f $summary.session_id, $ModeName)
    Write-JsonFile -Path $summaryPath -Object $summary
    return $summary
}

function Get-RecentSessions {
    param([int]$Max = 5)

    if (-not (Test-Path -LiteralPath $script:SessionsDir)) {
        return @()
    }

    $files = @(Get-ChildItem -LiteralPath $script:SessionsDir -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First $Max)

    $items = @()
    foreach ($file in $files) {
        $items += Read-JsonFile -Path $file.FullName -Default $null
    }
    return @($items | Where-Object { $null -ne $_ })
}

function Initialize-Workspace {
    Ensure-Directory -Path $script:ConfigDir
    Ensure-Directory -Path $script:StateDir
    Ensure-Directory -Path $script:SessionsDir
    Ensure-Directory -Path $script:IncidentsDir
    Ensure-Directory -Path $script:LibDir

    $script:IsAdmin = Test-IsAdministrator
}

function Write-ActionLog {
    param(
        [Parameter(Mandatory = $true)][string]$Mode,
        [Parameter(Mandatory = $true)]$Actions,
        [Parameter(Mandatory = $true)]$Settings
    )

    $logConfig = Get-ObjectValue -Object $Settings -Name "logging" -Default $null
    if ($null -eq $logConfig -or -not [bool](Get-ObjectValue -Object $logConfig -Name "enableActionLog" -Default $true)) {
        return
    }

    $relPath = Get-ObjectValue -Object $logConfig -Name "actionLogPath" -Default "state\action_log.jsonl"
    $logPath = Join-Path $script:Root $relPath
    $logDir = Split-Path $logPath -Parent
    if (-not (Test-Path -LiteralPath $logDir)) {
        New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    }

    $entry = [pscustomobject]@{
        timestamp = (Get-Date).ToString("o")
        mode      = $Mode
        actions   = @($Actions)
    }
    Add-Content -LiteralPath $logPath -Value ($entry | ConvertTo-Json -Depth 10 -Compress) -Encoding UTF8

    $maxEntries = [int](Get-ObjectValue -Object $logConfig -Name "maxEntries" -Default 1000)
    if ($maxEntries -gt 0) {
        [array]$lines = @(Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue)
        if ($lines.Count -gt $maxEntries) {
            Set-Content -LiteralPath $logPath -Value $lines[-$maxEntries..-1] -Encoding UTF8
        }
    }
}
