# ──────────────────────────────────────────────────────────────────────────────
# Maintenance subsystem — read-only detection + safe cleanup actions
# ──────────────────────────────────────────────────────────────────────────────
# All detection functions are side-effect-free and can run any time.
# All action functions (Invoke-*) respect -WhatIf and log results.
# ──────────────────────────────────────────────────────────────────────────────

function Get-FolderSizeGB {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -ErrorAction SilentlyContinue)) { return 0.0 }
    $bytes = (Get-ChildItem -LiteralPath $Path -Recurse -ErrorAction SilentlyContinue |
              Measure-Object -Property Length -Sum).Sum
    return [math]::Round([double]$bytes / 1GB, 4)
}

function Get-DiskReport {
    $drive = Get-PSDrive C -ErrorAction SilentlyContinue
    if ($null -eq $drive) {
        return [pscustomobject]@{ status = "unavailable"; used_gb = 0; free_gb = 0; pct_used = 0 }
    }

    $usedBytes = $drive.Used
    $freeBytes  = $drive.Free
    $totalBytes = $usedBytes + $freeBytes
    $pctUsed    = if ($totalBytes -gt 0) { [math]::Round($usedBytes * 100.0 / $totalBytes, 1) } else { 0 }

    $status = if ($pctUsed -ge 90) { "critical" } elseif ($pctUsed -ge 80) { "warning" } else { "ok" }

    return [pscustomobject]@{
        status   = $status
        used_gb  = [math]::Round($usedBytes / 1GB, 1)
        free_gb  = [math]::Round($freeBytes / 1GB, 1)
        total_gb = [math]::Round($totalBytes / 1GB, 1)
        pct_used = $pctUsed
    }
}

function Get-DockerDiskInfo {
    $dockerLocalAppData = Join-Path $env:LOCALAPPDATA "Docker"
    $sizeGB = Get-FolderSizeGB -Path $dockerLocalAppData

    $dfOutput = $null
    try {
        $dockerExe = "docker"
        if (Get-Command $dockerExe -ErrorAction SilentlyContinue) {
            $dfOutput = & $dockerExe system df --format "{{json .}}" 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue
        }
    }
    catch { }

    return [pscustomobject]@{
        localappdata_gb  = $sizeGB
        docker_df        = $dfOutput
    }
}

function Get-WslDiskInfo {
    $uwpPackagesPath = Join-Path $env:LOCALAPPDATA "Packages"
    $vhdxFiles = @()
    if (Test-Path -LiteralPath $uwpPackagesPath) {
        $vhdxFiles = @(Get-ChildItem -LiteralPath $uwpPackagesPath -Recurse -Filter "ext4.vhdx" -ErrorAction SilentlyContinue |
            Select-Object FullName, @{ N = "SizeGB"; E = { [math]::Round($_.Length / 1GB, 2) } })
    }

    $totalGB = ($vhdxFiles | Measure-Object -Property SizeGB -Sum).Sum
    return [pscustomobject]@{
        vhdx_files = @($vhdxFiles)
        total_gb   = [math]::Round([double]$totalGB, 2)
    }
}

function Get-TempFolderInfo {
    $tempPath = $env:TEMP
    $sizeGB = Get-FolderSizeGB -Path $tempPath
    $fileCount = 0
    if (Test-Path -LiteralPath $tempPath) {
        $fileCount = (Get-ChildItem -LiteralPath $tempPath -Recurse -ErrorAction SilentlyContinue |
                      Measure-Object).Count
    }
    return [pscustomobject]@{
        path       = $tempPath
        size_gb    = $sizeGB
        file_count = $fileCount
    }
}

function Get-DownloadsFolderInfo {
    param([int]$OldDays = 30, [double]$MinSizeGB = 0.5)

    $downloadsPath = Join-Path $env:USERPROFILE "Downloads"
    $sizeGB = Get-FolderSizeGB -Path $downloadsPath

    $cutoff = (Get-Date).AddDays(-$OldDays)
    $staleFiles = @()
    if (Test-Path -LiteralPath $downloadsPath) {
        $staleFiles = @(Get-ChildItem -LiteralPath $downloadsPath -File -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -lt $cutoff -and ($_.Length / 1GB) -ge $MinSizeGB } |
            Select-Object Name, @{ N = "SizeGB"; E = { [math]::Round($_.Length / 1GB, 2) } }, LastWriteTime |
            Sort-Object SizeGB -Descending)
    }

    return [pscustomobject]@{
        path        = $downloadsPath
        total_gb    = $sizeGB
        stale_files = @($staleFiles)
        stale_count = $staleFiles.Count
    }
}

function Get-NpmCacheInfo {
    $npmCachePath = Join-Path $env:APPDATA "npm-cache"
    $sizeGB = Get-FolderSizeGB -Path $npmCachePath
    return [pscustomobject]@{ path = $npmCachePath; size_gb = $sizeGB }
}

function Get-UnknownLargeDirReport {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [int]$TopN = 20
    )

    $maint = Get-ObjectValue -Object $Settings -Name "maintenance" -Default $null
    $dirs  = @(Get-ObjectValue -Object $maint -Name "unknownLargeDirs" -Default @())

    $reports = @()
    foreach ($dirPath in $dirs) {
        if (-not (Test-Path -LiteralPath $dirPath -ErrorAction SilentlyContinue)) {
            $reports += [pscustomobject]@{ path = $dirPath; exists = $false; total_gb = 0; top_files = @() }
            continue
        }

        $totalGB = Get-FolderSizeGB -Path $dirPath

        $topFiles = @(Get-ChildItem -LiteralPath $dirPath -ErrorAction SilentlyContinue |
            Select-Object Name,
                @{ N = "SizeGB"; E = { [math]::Round($_.Length / 1GB, 2) } },
                LastWriteTime, Attributes |
            Sort-Object SizeGB -Descending |
            Select-Object -First $TopN)

        $reports += [pscustomobject]@{
            path      = $dirPath
            exists    = $true
            total_gb  = $totalGB
            top_files = @($topFiles)
        }
    }

    return @($reports)
}

function Test-MaintenanceSafe {
    param([Parameter(Mandatory = $true)]$Settings)

    $maint      = Get-ObjectValue -Object $Settings -Name "maintenance" -Default $null
    $maxCpu     = [double](Get-ObjectValue -Object $maint -Name "maxCpuThreshold" -Default 20)
    $denyModes  = @(Get-ObjectValue -Object $maint -Name "denyModes" -Default @("gaming", "heavy-gaming", "rimworld-mod", "audio-safe"))

    # Check CPU
    $cpuPct = 100.0
    try {
        $counter = Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 1 -ErrorAction SilentlyContinue
        $cpuPct  = [math]::Round($counter.CounterSamples[0].CookedValue, 1)
    }
    catch { }

    $currentMode = Get-CurrentModeName
    $inDeniedMode = $currentMode -in $denyModes

    $reasons = @()
    if ($inDeniedMode) { $reasons += ("Mode '{0}' is in denyModes list" -f $currentMode) }
    if ($cpuPct -gt $maxCpu)  { $reasons += ("CPU at {0}% exceeds threshold of {1}%" -f $cpuPct, $maxCpu) }

    return [pscustomobject]@{
        safe          = ($cpuPct -le $maxCpu -and -not $inDeniedMode)
        cpu_pct       = $cpuPct
        in_game_mode  = $inDeniedMode
        current_mode  = $currentMode
        reasons       = @($reasons)
    }
}

function Get-MaintenancePlan {
    param([Parameter(Mandatory = $true)]$Settings)

    $maint   = Get-ObjectValue -Object $Settings -Name "maintenance" -Default $null
    $actions = Get-ObjectValue -Object $maint -Name "actions" -Default $null

    $disk        = Get-DiskReport
    $docker      = Get-DockerDiskInfo
    $wsl         = Get-WslDiskInfo
    $temp        = Get-TempFolderInfo
    $downloads   = Get-DownloadsFolderInfo
    $npm         = Get-NpmCacheInfo
    $unknownDirs = Get-UnknownLargeDirReport -Settings $Settings
    $safety      = Test-MaintenanceSafe -Settings $Settings

    $issues = @()

    # Disk criticality
    if ($disk.pct_used -ge 90) {
        $issues += [pscustomobject]@{
            type       = "disk"
            severity   = "critical"
            message    = ("C: drive is {0}% full ({1} GB free of {2} GB total)" -f $disk.pct_used, $disk.free_gb, $disk.total_gb)
            suggestion = $null
        }
    }

    # Docker
    if ($docker.localappdata_gb -ge 10) {
        $issues += [pscustomobject]@{
            type       = "docker"
            severity   = if ($docker.localappdata_gb -ge 50) { "critical" } elseif ($docker.localappdata_gb -ge 20) { "warning" } else { "info" }
            message    = ("Docker is using {0} GB in AppData" -f $docker.localappdata_gb)
            suggestion = "docker-prune"
        }
    }

    # WSL
    if ($wsl.total_gb -ge 5) {
        $issues += [pscustomobject]@{
            type       = "wsl"
            severity   = if ($wsl.total_gb -ge 30) { "warning" } else { "info" }
            message    = ("WSL ext4.vhdx files total {0} GB (may contain unused space)" -f $wsl.total_gb)
            suggestion = "wsl-compact"
        }
    }

    # Temp
    if ($temp.size_gb -ge 1) {
        $issues += [pscustomobject]@{
            type       = "temp"
            severity   = if ($temp.size_gb -ge 5) { "warning" } else { "info" }
            message    = ("TEMP folder is {0} GB ({1} files)" -f $temp.size_gb, $temp.file_count)
            suggestion = "clean-temp"
        }
    }

    # Downloads
    if ($downloads.stale_count -gt 0) {
        $totalStaleGB = ($downloads.stale_files | Measure-Object -Property SizeGB -Sum).Sum
        $issues += [pscustomobject]@{
            type       = "downloads"
            severity   = "info"
            message    = ("{0} stale files ({1} GB) in Downloads older than 30 days" -f $downloads.stale_count, [math]::Round($totalStaleGB, 1))
            suggestion = "review-downloads"
        }
    }

    # npm cache
    if ($npm.size_gb -ge 1) {
        $issues += [pscustomobject]@{
            type       = "npm-cache"
            severity   = "info"
            message    = ("npm cache is {0} GB" -f $npm.size_gb)
            suggestion = "clean-npm-cache"
        }
    }

    # Unknown large dirs (inspection-only - never auto-deleted)
    foreach ($dir in $unknownDirs) {
        if ($dir.exists -and $dir.total_gb -ge 1) {
            $issues += [pscustomobject]@{
                type       = "unknown-dir"
                severity   = if ($dir.total_gb -ge 10) { "warning" } else { "info" }
                message    = ("Unknown directory '{0}' is {1} GB - inspect before deleting" -f $dir.path, $dir.total_gb)
                suggestion = "prime-anchor-report"
            }
        }
    }

    # Downloads report trigger
    if ($downloads.stale_count -gt 0) {
        $isEnabled = [bool](Get-ObjectValue -Object $actions -Name "downloads-report" -Default $true)
        if ($isEnabled) {
            $issues | Where-Object { $_.suggestion -eq "review-downloads" } | ForEach-Object {
                $_.suggestion = "downloads-report"
            }
        }
    }

    # Suggested actions — only enabled ones
    $enabled = @()
    if ($null -ne $actions) {
        $issues | Where-Object { $null -ne $_.suggestion } | ForEach-Object {
            $key = $_.suggestion
            $isEnabled = [bool](Get-ObjectValue -Object $actions -Name $key -Default $false)
            if ($isEnabled) { $enabled += $key }
        }
    }

    return [pscustomobject]@{
        timestamp         = (Get-Date).ToString("o")
        status            = if ($issues | Where-Object severity -eq "critical") { "critical" } elseif ($issues | Where-Object severity -eq "warning") { "warning" } else { "ok" }
        disk              = $disk
        docker            = $docker
        wsl               = $wsl
        temp              = $temp
        downloads         = $downloads
        npm_cache         = $npm
        unknown_dirs      = @($unknownDirs)
        issues            = @($issues)
        safe_to_maintain  = $safety.safe
        safety_detail     = $safety
        suggested_actions = @($enabled | Select-Object -Unique)
    }
}

# ─── Actions ──────────────────────────────────────────────────────────────────

function Invoke-CleanTemp {
    param([Parameter(Mandatory = $true)]$Settings)

    $path = $env:TEMP
    if ($WhatIfPreference) {
        return Add-ActionResult -Action "clean-temp" -Target $path -Changed $false -Skipped $true -Message "WhatIf: would remove contents of $path"
    }

    $before = Get-FolderSizeGB -Path $path
    Remove-Item -LiteralPath $path\* -Recurse -Force -ErrorAction SilentlyContinue
    $after = Get-FolderSizeGB -Path $path
    $freed = [math]::Round($before - $after, 2)

    return Add-ActionResult -Action "clean-temp" -Target $path -Changed ($freed -gt 0) -Message ("Freed {0} GB from TEMP folder" -f $freed)
}

function Invoke-DockerPrune {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        return Add-ActionResult -Action "docker-prune" -Target "docker" -Success $false -Changed $false -Message "docker CLI not found" -Severity "WARN"
    }

    if ($WhatIfPreference) {
        return Add-ActionResult -Action "docker-prune" -Target "docker" -Changed $false -Skipped $true -Message "WhatIf: would run docker system prune -f"
    }

    try {
        $output = & docker system prune -f 2>&1
        return Add-ActionResult -Action "docker-prune" -Target "docker" -Changed $true -Message ($output -join " ")
    }
    catch {
        return Add-ActionResult -Action "docker-prune" -Target "docker" -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR"
    }
}

function Invoke-NpmCacheClean {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        return Add-ActionResult -Action "clean-npm-cache" -Target "npm" -Success $false -Changed $false -Message "npm not found" -Severity "WARN"
    }

    if ($WhatIfPreference) {
        return Add-ActionResult -Action "clean-npm-cache" -Target "npm" -Changed $false -Skipped $true -Message "WhatIf: would run npm cache clean --force"
    }

    try {
        & npm cache clean --force 2>&1 | Out-Null
        return Add-ActionResult -Action "clean-npm-cache" -Target "npm" -Changed $true -Message "npm cache cleaned"
    }
    catch {
        return Add-ActionResult -Action "clean-npm-cache" -Target "npm" -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR"
    }
}

function Invoke-WslCompact {
    if (-not $script:IsAdmin) {
        return Add-ActionResult -Action "wsl-compact" -Target "ext4.vhdx" -Success $false -Changed $false -Message "WSL compaction requires Administrator. Re-run keeper.ps1 as Admin." -Severity "WARN"
    }

    $packagesPath = Join-Path $env:LOCALAPPDATA "Packages"
    $vhdxFiles = @(Get-ChildItem -LiteralPath $packagesPath -Recurse -Filter "ext4.vhdx" -ErrorAction SilentlyContinue)

    if ($vhdxFiles.Count -eq 0) {
        return Add-ActionResult -Action "wsl-compact" -Target "ext4.vhdx" -Changed $false -Skipped $true -Message "No ext4.vhdx files found"
    }

    # WSL must be shut down first
    if ($WhatIfPreference) {
        return Add-ActionResult -Action "wsl-compact" -Target "ext4.vhdx" -Changed $false -Skipped $true -Message ("WhatIf: would shut down WSL and compact {0} VHDX file(s)" -f $vhdxFiles.Count)
    }

    & wsl --shutdown 2>$null
    Start-Sleep -Seconds 3

    $results = @()
    foreach ($vhdx in $vhdxFiles) {
        try {
            $before = [math]::Round($vhdx.Length / 1GB, 2)
            Optimize-VHD -Path $vhdx.FullName -Mode Full -ErrorAction Stop
            $after = [math]::Round((Get-Item -LiteralPath $vhdx.FullName).Length / 1GB, 2)
            $results += ("{0}: {1} GB -> {2} GB" -f $vhdx.Name, $before, $after)
        }
        catch {
            $results += ("{0}: error - {1}" -f $vhdx.Name, $_.Exception.Message)
        }
    }

    return Add-ActionResult -Action "wsl-compact" -Target "ext4.vhdx" -Changed $true -Message ($results -join "; ")
}

function Invoke-MaintenancePass {
    param([Parameter(Mandatory = $true)]$Settings)

    $plan = Get-MaintenancePlan -Settings $Settings

    $attempted = @()
    $skipped   = @()

    if (-not $plan.safe_to_maintain) {
        Write-Log ("Maintenance skipped: {0}" -f ($plan.safety_detail.reasons -join "; ")) "INFO"
        return [pscustomobject]@{
            status           = "skipped"
            safe_to_maintain = $false
            skip_reasons     = @($plan.safety_detail.reasons)
            issues           = @($plan.issues)
            disk             = $plan.disk
            actions_attempted = @()
            actions_skipped  = @($plan.suggested_actions)
            summary          = ("Maintenance skipped: {0}" -f ($plan.safety_detail.reasons -join "; "))
        }
    }

    # Destructive action map
    $actionMap = @{
        "clean-temp"      = { Invoke-CleanTemp -Settings $Settings }
        "docker-prune"    = { Invoke-DockerPrune }
        "clean-npm-cache" = { Invoke-NpmCacheClean }
        "wsl-compact"     = { Invoke-WslCompact }
    }

    # Report-only actions — never destructive
    $reportOnly = @("downloads-report", "prime-anchor-report")

    foreach ($action in $plan.suggested_actions) {
        if ($reportOnly -contains $action) {
            $skipped += $action   # reports surface via plan data, not action execution
        }
        elseif ($actionMap.ContainsKey($action)) {
            [void](& $actionMap[$action])
            $attempted += $action
        }
        else {
            $skipped += $action
        }
    }

    Write-ActionLog -Mode "maintenance" -Actions $script:ActionResults -Settings $Settings

    $successCount = @($script:ActionResults | Where-Object { $_.success -eq $true -and $_.changed -eq $true }).Count
    $errorCount   = @($script:ActionResults | Where-Object { $_.success -eq $false }).Count

    return [pscustomobject]@{
        status            = if ($errorCount -gt 0) { "partial" } elseif ($successCount -gt 0) { "ok" } else { "no-op" }
        safe_to_maintain  = $true
        skip_reasons      = @()
        issues            = @($plan.issues)
        disk              = $plan.disk
        actions_attempted = @($attempted)
        actions_skipped   = @($skipped)
        action_results    = @($script:ActionResults)
        summary           = ("{0} action(s) applied, {1} skipped, {2} error(s)" -f $attempted.Count, $skipped.Count, $errorCount)
    }
}
