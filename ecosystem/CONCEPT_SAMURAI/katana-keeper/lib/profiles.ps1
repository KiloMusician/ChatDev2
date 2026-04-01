# lib/profiles.ps1
# Mode application + restore orchestration, session summaries.
# Depends on: config.ps1, state.ps1, health.ps1, actions.ps1

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
        session_id           = $StartedAt.ToString("yyyy-MM-ddTHH-mm-ss")
        mode                 = $ModeName
        started_at           = $StartedAt.ToString("o")
        ended_at             = $EndedAt.ToString("o")
        duration_min         = [math]::Round((($EndedAt - $StartedAt).TotalMinutes), 2)
        cpu_percent_before   = Get-ObjectValue -Object $Before -Name "cpu_percent"
        cpu_percent_after    = Get-ObjectValue -Object $After  -Name "cpu_percent"
        wsl_active_before    = Get-ObjectValue -Object $Before -Name "wsl_active"  -Default $false
        wsl_active_after     = Get-ObjectValue -Object $After  -Name "wsl_active"  -Default $false
        docker_active_before = Get-ObjectValue -Object $Before -Name "docker_active" -Default $false
        docker_active_after  = Get-ObjectValue -Object $After  -Name "docker_active" -Default $false
        top_offenders        = @(Get-ObjectValue -Object $After -Name "top_offenders" -Default @())
        action_summary       = Get-ActionSummary -Results $Results
        notes                = $Notes
    }
    $filePath = Join-Path $script:SessionsDir "$($summary.session_id)-$ModeName.json"
    Ensure-Directory -Path $script:SessionsDir
    Write-JsonFile -Path $filePath -Object $summary
    return $summary
}

function Invoke-ModeProfile {
    param(
        [Parameter(Mandatory = $true)][string]$ModeName,
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Profiles
    )
    $profile = Get-ObjectValue -Object $Profiles -Name $ModeName -Default $null
    if ($null -eq $profile) { throw "Profile '$ModeName' is not defined in config/profiles.json." }

    $startedAt = Get-Date
    $before    = Get-HealthState
    $notes     = @((Get-ObjectValue -Object $profile -Name "notes" -Default @()))

    $rollback = [ordered]@{
        timestamp          = $startedAt.ToString("o")
        priorMode          = Get-ObjectValue -Object $before -Name "mode" -Default "idle"
        priorPowerPlanGuid = Get-ObjectValue -Object $before -Name "power_plan_guid"
        priorPowerPlanRaw  = Get-ObjectValue -Object $before -Name "power_plan_raw"
        priorGameMode      = Get-GameModeState
        priorWslActive     = Get-ObjectValue -Object $before -Name "wsl_active" -Default $false
        stoppedProcesses   = @()
        stoppedServices    = @()
        relaunchers        = @()
    }

    Save-CurrentState -State ([pscustomobject]@{
        mode        = $ModeName; status = "applying"
        started_at  = $startedAt.ToString("o")
        description = ($notes -join " ")
    })

    if ([bool](Get-ObjectValue -Object $profile -Name "shutdownWsl" -Default $false)) {
        [void](Invoke-WslShutdownSafe)
    }
    foreach ($pattern in @(Get-ObjectValue -Object $profile -Name "stopProcesses" -Default @())) {
        [void](Stop-ProcessesByPatternSafe -Pattern ([string]$pattern) -Settings $Settings -RollbackState ([ref]$rollback))
    }
    foreach ($svcName in @(Get-ObjectValue -Object $profile -Name "stopServices" -Default @())) {
        [void](Stop-ServiceSafe -ServiceName ([string]$svcName) -RollbackState ([ref]$rollback))
    }
    $powerPlan = Get-ObjectValue -Object $profile -Name "setPowerPlan" -Default $null
    if ($null -ne $powerPlan) { [void](Set-PowerPlanSafe -PlanName ([string]$powerPlan) -Settings $Settings) }
    $setGameMode = Get-ObjectValue -Object $profile -Name "setGameMode" -Default $null
    if ($null -ne $setGameMode) { [void](Set-GameModeStateSafe -Enabled ([bool]$setGameMode)) }
    foreach ($svcName in @(Get-ObjectValue -Object $profile -Name "startServices" -Default @())) {
        [void](Start-ServiceSafe -ServiceName ([string]$svcName))
    }
    foreach ($launcherName in @(Get-ObjectValue -Object $profile -Name "startLaunchers" -Default @())) {
        [void](Start-LauncherSafe -LauncherName ([string]$launcherName) -Settings $Settings)
    }

    $endedAt = Get-Date
    $after   = Get-HealthState
    Add-RingBufferSample -Sample $after -Settings $Settings
    Save-RollbackState -Rollback ([pscustomobject]$rollback)

    $currentState = [pscustomobject]@{
        mode            = $ModeName; status = "ready"
        started_at      = $startedAt.ToString("o"); updated_at = $endedAt.ToString("o")
        power_plan_raw  = Get-ObjectValue -Object $after -Name "power_plan_raw"
        power_plan_guid = Get-ObjectValue -Object $after -Name "power_plan_guid"
        wsl_active      = Get-ObjectValue -Object $after -Name "wsl_active"
        docker_active   = Get-ObjectValue -Object $after -Name "docker_active"
        cpu_percent     = Get-ObjectValue -Object $after -Name "cpu_percent"
        free_mem_mb     = Get-ObjectValue -Object $after -Name "free_mem_mb"
        top_offenders   = Get-ObjectValue -Object $after -Name "top_offenders"
        game_mode       = Get-ObjectValue -Object $after -Name "game_mode_enabled"
        action_summary  = Get-ActionSummary -Results $script:ActionResults
    }
    Save-CurrentState -State $currentState

    $summary = New-SessionSummary -ModeName $ModeName -StartedAt $startedAt -EndedAt $endedAt -Before $before -After $after -Results $script:ActionResults -Notes $notes
    return [pscustomobject]@{ mode = $ModeName; before = $before; after = $after; summary = $summary; actions = @($script:ActionResults) }
}

function Invoke-RestoreMode {
    param([Parameter(Mandatory = $true)]$Settings)
    $rollback = Read-JsonFile -Path $script:RollbackPath -Default $null
    if ($null -eq $rollback) { throw "No rollback.json found. Run a mode change first." }

    $startedAt = Get-Date
    $before    = Get-HealthState

    foreach ($svcName in @(Get-ObjectValue -Object $rollback -Name "stoppedServices" -Default @())) {
        [void](Start-ServiceSafe -ServiceName ([string]$svcName))
    }
    $priorGuid = Get-ObjectValue -Object $rollback -Name "priorPowerPlanGuid" -Default $null
    if ($null -ne $priorGuid -and -not [string]::IsNullOrWhiteSpace([string]$priorGuid)) {
        [void](Invoke-PowerCfgCommand -Arguments @("/setactive", [string]$priorGuid))
        Add-ActionResult -Action "restore_power_plan" -Target ([string]$priorGuid) -Changed $true -Message "Power plan restored." | Out-Null
    }
    $priorGameMode = Get-ObjectValue -Object $rollback -Name "priorGameMode" -Default $null
    if ($null -ne $priorGameMode) {
        $priorEnabled = Get-ObjectValue -Object $priorGameMode -Name "effectiveEnabled" -Default $false
        [void](Set-GameModeStateSafe -Enabled ([bool]$priorEnabled))
    }
    foreach ($launcherName in @(Get-ObjectValue -Object $rollback -Name "relaunchers" -Default @())) {
        [void](Start-LauncherSafe -LauncherName ([string]$launcherName) -Settings $Settings)
    }

    $endedAt = Get-Date
    $after   = Get-HealthState
    Add-RingBufferSample -Sample $after -Settings $Settings
    $summary = New-SessionSummary -ModeName "restore" -StartedAt $startedAt -EndedAt $endedAt -Before $before -After $after -Results $script:ActionResults -Notes @("Rolled back to prior state.")
    Save-CurrentState -State ([pscustomobject]@{ mode = "restored"; status = "ready"; updated_at = $endedAt.ToString("o") })
    return [pscustomobject]@{ mode = "restore"; before = $before; after = $after; summary = $summary; actions = @($script:ActionResults) }
}
