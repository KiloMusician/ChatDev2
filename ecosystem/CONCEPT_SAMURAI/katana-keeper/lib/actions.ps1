# lib/actions.ps1
# All side-effectful primitives: process, service, power plan, registry, WSL, launcher.
# Depends on: config.ps1 (utilities), state.ps1 (path vars via $script:)
# Uses $script:ActionResults and $script:IsAdmin set by keeper.ps1 at startup.

function Add-ActionResult {
    param(
        [Parameter(Mandatory = $true)][string]$Action,
        [Parameter(Mandatory = $true)][string]$Target,
        [bool]$Success  = $true,
        [bool]$Changed  = $false,
        [bool]$Skipped  = $false,
        [string]$Message  = "",
        [ValidateSet("INFO","WARN","ERROR")][string]$Severity = "INFO"
    )
    $result = [pscustomobject]@{
        action  = $Action; target  = $Target; success = $Success
        changed = $Changed; skipped = $Skipped; message = $Message; severity = $Severity
    }
    $script:ActionResults += $result
    if ($Severity -eq "WARN")        { Write-Log "$Action :: $Target :: $Message" "WARN" }
    elseif ($Severity -eq "ERROR")   { Write-Log "$Action :: $Target :: $Message" "ERROR" }
    else                             { Write-Log "$Action :: $Target :: $Message" "DEBUG" }
    return $result
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

function Format-CmdArgument {
    param([Parameter(Mandatory = $true)][string]$Value)
    if ($Value -match '[\s"]') { return '"' + $Value.Replace('"', '""') + '"' }
    return $Value
}

function Invoke-ExternalProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $null
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName  = $FilePath
    $psi.Arguments = ($Arguments | ForEach-Object { Format-CmdArgument $_ }) -join " "
    $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    if ($WorkingDirectory) { $psi.WorkingDirectory = $WorkingDirectory }
    $proc = [System.Diagnostics.Process]::Start($psi)
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    return [pscustomobject]@{ output = ($stdout + $stderr).Trim(); exitCode = $proc.ExitCode; success = ($proc.ExitCode -eq 0) }
}

function Invoke-PowerCfgCommand {
    param([string[]]$Arguments)
    return Invoke-ExternalProcess -FilePath "powercfg.exe" -Arguments $Arguments
}

function Get-RegistryDword {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string]$Name)
    try { return [int](Get-ItemPropertyValue -Path $Path -Name $Name -ErrorAction Stop) } catch { return $null }
}

function Set-RegistryDwordSafe {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][int]$Value
    )
    if ($WhatIfPreference) { return $true }
    try {
        if (-not (Test-Path $Path)) { New-Item -Path $Path -Force | Out-Null }
        Set-ItemProperty -Path $Path -Name $Name -Value $Value -Type DWord -ErrorAction Stop
        return $true
    } catch { Write-Log "Failed to set registry ${Path}\${Name}: $($_.Exception.Message)" "ERROR"; return $false }
}

function Set-GameModeStateSafe {
    param([Parameter(Mandatory = $true)][bool]$Enabled)
    $path = "HKCU:\Software\Microsoft\GameBar"
    $val  = if ($Enabled) { 1 } else { 0 }
    if ($WhatIfPreference) {
        return Add-ActionResult -Action "set_game_mode" -Target "GameBar" -Changed $false -Skipped $true -Message "WhatIf: would set AllowAutoGameMode=$val."
    }
    $ok = Set-RegistryDwordSafe -Path $path -Name "AllowAutoGameMode" -Value $val
    if ($ok) { return Add-ActionResult -Action "set_game_mode" -Target "GameBar" -Changed $true -Message "AllowAutoGameMode set to $val." }
    return Add-ActionResult -Action "set_game_mode" -Target "GameBar" -Success $false -Changed $false -Message "Registry write failed." -Severity "ERROR"
}

function Resolve-PowerPlanTarget {
    param([Parameter(Mandatory = $true)][string]$PlanName, [Parameter(Mandatory = $true)]$Settings)
    $knownPlans = Get-ObjectValue -Object $Settings -Name "knownPowerPlans" -Default ([pscustomobject]@{})
    $mapped = Get-ObjectValue -Object $knownPlans -Name $PlanName -Default $null
    if ($null -ne $mapped -and -not [string]::IsNullOrWhiteSpace([string]$mapped)) { return [string]$mapped }
    return $PlanName
}

function Set-PowerPlanSafe {
    param([Parameter(Mandatory = $true)][string]$PlanName, [Parameter(Mandatory = $true)]$Settings)
    $target = Resolve-PowerPlanTarget -PlanName $PlanName -Settings $Settings
    if ($WhatIfPreference) {
        return Add-ActionResult -Action "set_power_plan" -Target $PlanName -Changed $false -Skipped $true -Message "WhatIf: would activate '$target'."
    }
    $result = Invoke-PowerCfgCommand -Arguments @("/setactive", $target)
    if ($result.success) { return Add-ActionResult -Action "set_power_plan" -Target $PlanName -Changed $true -Message "Activated '$target'." }
    return Add-ActionResult -Action "set_power_plan" -Target $PlanName -Success $false -Changed $false -Message $result.output -Severity "ERROR"
}

function Get-RunningWslDistros {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) { return @() }
    try { return @(@(wsl.exe --list --quiet --running 2>$null) | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ -ne "" }) }
    catch { return @() }
}

function Invoke-WslShutdownSafe {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
        return Add-ActionResult -Action "shutdown_wsl" -Target "wsl.exe" -Changed $false -Skipped $true -Message "WSL is not installed." -Severity "WARN"
    }
    if ($WhatIfPreference) {
        return Add-ActionResult -Action "shutdown_wsl" -Target "wsl.exe" -Changed $false -Skipped $true -Message "WhatIf: would run wsl --shutdown."
    }
    $result = Invoke-ExternalProcess -FilePath "wsl.exe" -Arguments @("--shutdown")
    if ($result.success) { return Add-ActionResult -Action "shutdown_wsl" -Target "wsl.exe" -Changed $true -Message "WSL shutdown." }
    return Add-ActionResult -Action "shutdown_wsl" -Target "wsl.exe" -Success $false -Changed $false -Message $result.output -Severity "ERROR"
}

function Find-ProcessesByPattern {
    param([Parameter(Mandatory = $true)][string]$Pattern)
    if ($Pattern -match '\*') {
        return @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like $Pattern })
    }
    return @(Get-Process -Name $Pattern -ErrorAction SilentlyContinue)
}

function Stop-ProcessesByPatternSafe {
    param(
        [Parameter(Mandatory = $true)][string]$Pattern,
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)][ref]$RollbackState
    )
    $procs = @(Find-ProcessesByPattern -Pattern $Pattern)
    if ($procs.Count -eq 0) {
        return Add-ActionResult -Action "stop_process" -Target $Pattern -Changed $false -Skipped $true -Message "No matching processes found."
    }
    if ($WhatIfPreference) {
        return Add-ActionResult -Action "stop_process" -Target $Pattern -Changed $false -Skipped $true -Message ("WhatIf: would stop {0} process(es)." -f $procs.Count)
    }
    $relaunchMappings = Get-ObjectValue -Object $Settings -Name "relaunchMappings" -Default ([pscustomobject]@{})
    $stoppedNames = @()
    foreach ($proc in $procs) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        $stoppedNames += $proc.ProcessName
        $launcherName = Get-ObjectValue -Object $relaunchMappings -Name $proc.ProcessName -Default $null
        if ($null -ne $launcherName -and -not ($RollbackState.Value.relaunchers -contains $launcherName)) {
            $RollbackState.Value.relaunchers += $launcherName
        }
    }
    $RollbackState.Value.stoppedProcesses += $stoppedNames
    return Add-ActionResult -Action "stop_process" -Target $Pattern -Changed $true -Message ("Stopped {0} process(es): {1}" -f $procs.Count, (($stoppedNames | Sort-Object -Unique) -join ", "))
}

function Stop-ServiceSafe {
    param([Parameter(Mandatory = $true)][string]$ServiceName, [Parameter(Mandatory = $true)][ref]$RollbackState)
    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $svc) { return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service not found." }
    if ($svc.Status -ne "Running") { return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service not running." }
    if (-not $script:IsAdmin) { return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Requires administrator privileges." -Severity "WARN" }
    if ($WhatIfPreference) { return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "WhatIf: would stop service." }
    try {
        Stop-Service -Name $ServiceName -Force -ErrorAction Stop
        $RollbackState.Value.stoppedServices += $ServiceName
        return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $true -Message "Service stopped."
    } catch { return Add-ActionResult -Action "stop_service" -Target $ServiceName -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR" }
}

function Start-ServiceSafe {
    param([Parameter(Mandatory = $true)][string]$ServiceName)
    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $svc) { return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service not found." }
    if ($svc.Status -eq "Running") { return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service already running." }
    if (-not $script:IsAdmin) { return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Requires administrator privileges." -Severity "WARN" }
    if ($WhatIfPreference) { return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "WhatIf: would start service." }
    try { Start-Service -Name $ServiceName -ErrorAction Stop; return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $true -Message "Service started." }
    catch { return Add-ActionResult -Action "start_service" -Target $ServiceName -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR" }
}

function Resolve-LauncherSpec {
    param([Parameter(Mandatory = $true)][string]$LauncherName, [Parameter(Mandatory = $true)]$Settings)
    $launchers = Get-ObjectValue -Object $Settings -Name "launchers" -Default ([pscustomobject]@{})
    return Get-ObjectValue -Object $launchers -Name $LauncherName -Default $null
}

function Start-LauncherSafe {
    param([Parameter(Mandatory = $true)][string]$LauncherName, [Parameter(Mandatory = $true)]$Settings)
    $spec = Resolve-LauncherSpec -LauncherName $LauncherName -Settings $Settings
    if ($null -eq $spec) { return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $false -Skipped $true -Message "Launcher not defined in config." -Severity "WARN" }
    $command = Get-ObjectValue -Object $spec -Name "command" -Default $null
    if ([string]::IsNullOrWhiteSpace([string]$command)) { return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $false -Skipped $true -Message "Launcher command is empty." -Severity "WARN" }
    if ($WhatIfPreference) { return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $false -Skipped $true -Message "WhatIf: would start '$command'." }
    $cmdArgs   = @(Get-ObjectValue -Object $spec -Name "arguments" -Default @())
    $workDir   = Get-ObjectValue -Object $spec -Name "workingDirectory" -Default $null
    $startArgs = @{ FilePath = $command }
    if ($cmdArgs.Count -gt 0) { $startArgs["ArgumentList"] = $cmdArgs }
    if ($workDir)              { $startArgs["WorkingDirectory"] = $workDir }
    try { Start-Process @startArgs | Out-Null; return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $true -Message "Started '$command'." }
    catch { return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR" }
}
