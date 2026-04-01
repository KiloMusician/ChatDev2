function Invoke-ModeProfile {
    param(
        [Parameter(Mandatory = $true)][string]$ModeName,
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Profiles
    )

    $profile = Get-ObjectValue -Object $Profiles -Name $ModeName -Default $null
    if ($null -eq $profile) {
        throw "Profile '$ModeName' is not defined in config/profiles.json."
    }

    $startedAt = Get-Date
    $before = Get-HealthState
    $notes = @((Get-ObjectValue -Object $profile -Name "notes" -Default @()))

    $rollback = [ordered]@{
        timestamp            = $startedAt.ToString("o")
        priorMode            = Get-ObjectValue -Object $before -Name "mode" -Default "idle"
        priorPowerPlanGuid   = Get-ObjectValue -Object $before -Name "power_plan_guid"
        priorPowerPlanRaw    = Get-ObjectValue -Object $before -Name "power_plan_raw"
        priorGameMode        = Get-GameModeState
        priorWslActive       = Get-ObjectValue -Object $before -Name "wsl_active" -Default $false
        stoppedProcesses     = @()
        stoppedServices      = @()
        relaunchers          = @()
        priorityChanges      = @()
        gpuPreferences       = @()
    }

    Save-CurrentState -State ([pscustomobject]@{
        mode         = $ModeName
        status       = "applying"
        started_at   = $startedAt.ToString("o")
        description  = ($notes -join " ")
    })

    $safetyCfg = Get-ObjectValue -Object $Settings -Name "safety" -Default $null
    $killVSCode = [bool](Get-ObjectValue -Object $safetyCfg -Name "killVSCode" -Default $false)
    $stopProcessList = @(Get-ObjectValue -Object $profile -Name "stopProcesses" -Default @())
    if ($killVSCode) {
        $stopProcessList = @("Code") + $stopProcessList
    }
    foreach ($pattern in $stopProcessList) {
        [void](Stop-ProcessesByPatternSafe -Pattern ([string]$pattern) -Settings $Settings -RollbackState ([ref]$rollback))
    }

    $shutdownWsl = [bool](Get-ObjectValue -Object $profile -Name "shutdownWsl" -Default $false)
    if ($shutdownWsl) {
        [void](Invoke-WslShutdownSafe)
    }

    foreach ($serviceName in @(Get-ObjectValue -Object $profile -Name "stopServices" -Default @())) {
        [void](Stop-ServiceSafe -ServiceName ([string]$serviceName) -RollbackState ([ref]$rollback))
    }

    $powerPlan = Get-ObjectValue -Object $profile -Name "setPowerPlan" -Default $null
    if ($null -ne $powerPlan) {
        [void](Set-PowerPlanSafe -PlanName ([string]$powerPlan) -Settings $Settings)
    }

    $setGameMode = Get-ObjectValue -Object $profile -Name "setGameMode" -Default $null
    if ($null -ne $setGameMode) {
        [void](Set-GameModeStateSafe -Enabled ([bool]$setGameMode))
    }

    foreach ($serviceName in @(Get-ObjectValue -Object $profile -Name "startServices" -Default @())) {
        [void](Start-ServiceSafe -ServiceName ([string]$serviceName))
    }

    foreach ($launcherName in @(Get-ObjectValue -Object $profile -Name "startLaunchers" -Default @())) {
        [void](Start-LauncherSafe -LauncherName ([string]$launcherName) -Settings $Settings)
    }

    $priorityRules = @(Get-ObjectValue -Object $profile -Name "setPriorities" -Default @())
    if ($priorityRules.Count -gt 0) {
        Apply-PriorityRules -Rules $priorityRules -RollbackState ([ref]$rollback)
    }

    $gpuRules = @(Get-ObjectValue -Object $profile -Name "setGpuPreference" -Default @())
    if ($gpuRules.Count -gt 0) {
        Apply-GpuPreferences -Rules $gpuRules -RollbackState ([ref]$rollback)
    }

    $endedAt = Get-Date
    $after = Get-HealthState
    Append-RingBuffer -Sample $after -Settings $Settings
    Save-RollbackState -Rollback ([pscustomobject]$rollback)

    $actionSummary = Get-ActionSummary -Results $script:ActionResults
    $currentState = [pscustomobject]@{
        mode            = $ModeName
        status          = "ready"
        started_at      = $startedAt.ToString("o")
        updated_at      = $endedAt.ToString("o")
        power_plan_raw  = Get-ObjectValue -Object $after -Name "power_plan_raw"
        power_plan_guid = Get-ObjectValue -Object $after -Name "power_plan_guid"
        wsl_active      = Get-ObjectValue -Object $after -Name "wsl_active"
        docker_active   = Get-ObjectValue -Object $after -Name "docker_active"
        cpu_percent     = Get-ObjectValue -Object $after -Name "cpu_percent"
        free_mem_mb     = Get-ObjectValue -Object $after -Name "free_mem_mb"
        top_offenders   = Get-ObjectValue -Object $after -Name "top_offenders"
        game_mode       = Get-ObjectValue -Object $after -Name "game_mode_enabled"
        action_summary  = $actionSummary
    }
    Save-CurrentState -State $currentState

    $summary = New-SessionSummary -ModeName $ModeName -StartedAt $startedAt -EndedAt $endedAt -Before $before -After $after -Results $script:ActionResults -Notes $notes
    Write-ActionLog -Mode $ModeName -Actions $script:ActionResults -Settings $Settings

    return [pscustomobject]@{
        mode    = $ModeName
        before  = $before
        after   = $after
        summary = $summary
        actions = @($script:ActionResults)
    }
}

function Invoke-RestoreMode {
    param([Parameter(Mandatory = $true)]$Settings)

    $rollback = Read-JsonFile -Path $script:RollbackPath -Default $null
    if ($null -eq $rollback) {
        throw "No rollback.json state was found. Run a mode change first."
    }

    $startedAt = Get-Date
    $before = Get-HealthState

    $priorPowerPlanGuid = Get-ObjectValue -Object $rollback -Name "priorPowerPlanGuid" -Default $null
    if ($null -ne $priorPowerPlanGuid -and -not [string]::IsNullOrWhiteSpace([string]$priorPowerPlanGuid)) {
        [void](Set-PowerPlanSafe -PlanName ([string]$priorPowerPlanGuid) -Settings $Settings)
    }

    $priorGameMode = Get-ObjectValue -Object $rollback -Name "priorGameMode" -Default $null
    if ($null -ne $priorGameMode) {
        $allowAuto = Get-ObjectValue -Object $priorGameMode -Name "allowAutoGameMode" -Default $null
        $autoEnabled = Get-ObjectValue -Object $priorGameMode -Name "autoGameModeEnabled" -Default $null

        if ($null -ne $allowAuto) {
            [void](Set-RegistryDwordSafe -Path "HKCU:\Software\Microsoft\GameBar" -Name "AllowAutoGameMode" -Value ([int]$allowAuto))
        }

        if ($null -ne $autoEnabled) {
            [void](Set-RegistryDwordSafe -Path "HKCU:\Software\Microsoft\GameBar" -Name "AutoGameModeEnabled" -Value ([int]$autoEnabled))
        }
    }

    foreach ($serviceName in @(Get-ObjectValue -Object $rollback -Name "stoppedServices" -Default @())) {
        [void](Start-ServiceSafe -ServiceName ([string]$serviceName))
    }

    foreach ($launcherName in @(Get-ObjectValue -Object $rollback -Name "relaunchers" -Default @() | Sort-Object -Unique)) {
        [void](Start-LauncherSafe -LauncherName ([string]$launcherName) -Settings $Settings)
    }

    $gpuRegPath = "HKCU:\Software\Microsoft\DirectX\UserGpuPreferences"

    foreach ($p in @(Get-ObjectValue -Object $rollback -Name "priorityChanges" -Default @())) {
        try {
            $proc = Get-Process -Id ([int]$p.pid) -ErrorAction SilentlyContinue
            if ($null -ne $proc) {
                $proc.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::$([string]$p.original)
                [void](Add-ActionResult -Action "restore_priority" -Target "$($p.processName)[$($p.pid)]" -Changed $true -Message ("Priority restored to {0}" -f $p.original))
            }
        }
        catch { }
    }

    foreach ($g in @(Get-ObjectValue -Object $rollback -Name "gpuPreferences" -Default @())) {
        try {
            $exe = [string]$g.executable
            $orig = $g.original
            if ($null -eq $orig -or [string]::IsNullOrWhiteSpace([string]$orig)) {
                Remove-ItemProperty -Path $gpuRegPath -Name $exe -ErrorAction SilentlyContinue
                [void](Add-ActionResult -Action "restore_gpu_preference" -Target $exe -Changed $true -Message "GPU preference entry removed")
            }
            else {
                Set-ItemProperty -Path $gpuRegPath -Name $exe -Value ([string]$orig)
                [void](Add-ActionResult -Action "restore_gpu_preference" -Target $exe -Changed $true -Message ("GPU preference restored to {0}" -f $orig))
            }
        }
        catch { }
    }

    $endedAt = Get-Date
    $after = Get-HealthState
    Append-RingBuffer -Sample $after -Settings $Settings

    Save-CurrentState -State ([pscustomobject]@{
        mode            = "restore"
        status          = "ready"
        started_at      = $startedAt.ToString("o")
        updated_at      = $endedAt.ToString("o")
        power_plan_raw  = Get-ObjectValue -Object $after -Name "power_plan_raw"
        power_plan_guid = Get-ObjectValue -Object $after -Name "power_plan_guid"
        wsl_active      = Get-ObjectValue -Object $after -Name "wsl_active"
        docker_active   = Get-ObjectValue -Object $after -Name "docker_active"
        action_summary  = Get-ActionSummary -Results $script:ActionResults
    })

    $summary = New-SessionSummary -ModeName "restore" -StartedAt $startedAt -EndedAt $endedAt -Before $before -After $after -Results $script:ActionResults -Notes @("Restored the most recent reversible changes.")
    Write-ActionLog -Mode "restore" -Actions $script:ActionResults -Settings $Settings

    return [pscustomobject]@{
        mode    = "restore"
        before  = $before
        after   = $after
        summary = $summary
        actions = @($script:ActionResults)
    }
}
