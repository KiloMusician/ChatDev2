function Test-IsAdministrator {
    try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($identity)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }
    catch {
        return $false
    }
}

function Add-ActionResult {
    param(
        [Parameter(Mandatory = $true)][string]$Action,
        [Parameter(Mandatory = $true)][string]$Target,
        [bool]$Success = $true,
        [bool]$Changed = $false,
        [bool]$Skipped = $false,
        [string]$Message = "",
        [string]$Severity = "INFO"
    )

    $result = [pscustomobject]@{
        timestamp = (Get-Date).ToString("o")
        action    = $Action
        target    = $Target
        success   = $Success
        changed   = $Changed
        skipped   = $Skipped
        severity  = $Severity
        message   = $Message
    }

    $script:ActionResults += $result

    if ($Severity -eq "WARN") {
        Write-Log "$Action :: $Target :: $Message" "WARN"
    }
    elseif ($Severity -eq "ERROR") {
        Write-Log "$Action :: $Target :: $Message" "ERROR"
    }
    else {
        Write-Log "$Action :: $Target :: $Message" "DEBUG"
    }

    return $result
}

function Format-CmdArgument {
    param([Parameter(Mandatory = $true)][string]$Value)

    if ($Value -match '[\s"]') {
        return '"' + $Value.Replace('"', '""') + '"'
    }

    return $Value
}

function Invoke-ExternalProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FilePath
    $startInfo.Arguments = (($Arguments | ForEach-Object { Format-CmdArgument -Value $_ }) -join " ")
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true

    try {
        $process = [System.Diagnostics.Process]::Start($startInfo)
        $stdout = $process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        $process.WaitForExit()

        $combinedOutput = @($stdout, $stderr) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        return [pscustomobject]@{
            success  = ($process.ExitCode -eq 0)
            exitCode = $process.ExitCode
            output   = ($combinedOutput -join [Environment]::NewLine).Trim()
        }
    }
    catch {
        return [pscustomobject]@{
            success  = $false
            exitCode = -1
            output   = $_.Exception.Message
        }
    }
}

function Invoke-PowerCfgCommand {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    $commandText = "powercfg " + (($Arguments | ForEach-Object { Format-CmdArgument -Value $_ }) -join " ")
    return Invoke-ExternalProcess -FilePath "cmd.exe" -Arguments @("/d", "/c", $commandText)
}

function Get-ActivePowerPlanInfo {
    $rootPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes"
    $guid = $null

    try {
        $guid = [string](Get-ItemPropertyValue -Path $rootPath -Name "ActivePowerScheme" -ErrorAction Stop)
    }
    catch {
        $guid = $null
    }

    if (-not [string]::IsNullOrWhiteSpace($guid)) {
        $friendlyName = $null
        try {
            $planPath = Join-Path $rootPath $guid
            $friendlyName = [string](Get-ItemPropertyValue -Path $planPath -Name "FriendlyName" -ErrorAction Stop)
            if ($friendlyName -match ",([^,]+)$") {
                $friendlyName = $matches[1].Trim()
            }
            else {
                $friendlyName = $friendlyName.Trim()
            }
        }
        catch {
            $friendlyName = $null
        }

        $raw = if (-not [string]::IsNullOrWhiteSpace($friendlyName)) {
            "{0} ({1})" -f $guid, $friendlyName
        }
        else {
            $guid
        }

        return [pscustomobject]@{
            raw  = $raw
            guid = $guid
        }
    }

    $result = Invoke-PowerCfgCommand -Arguments @("/getactivescheme")
    $raw = [string](Get-ObjectValue -Object $result -Name "output" -Default "")
    $match = [regex]::Match($raw, "[0-9a-fA-F-]{36}")
    if ($match.Success) {
        $guid = $match.Value
    }

    return [pscustomobject]@{
        raw  = $raw.Trim()
        guid = $guid
    }
}

function Get-RegistryDword {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name
    )

    try {
        $value = Get-ItemPropertyValue -Path $Path -Name $Name -ErrorAction Stop
        return [int]$value
    }
    catch {
        return $null
    }
}

function Get-GameModeState {
    $path = "HKCU:\Software\Microsoft\GameBar"
    $allowAuto = Get-RegistryDword -Path $path -Name "AllowAutoGameMode"
    $autoEnabled = Get-RegistryDword -Path $path -Name "AutoGameModeEnabled"

    return [pscustomobject]@{
        allowAutoGameMode = $allowAuto
        autoGameModeEnabled = $autoEnabled
        effectiveEnabled = (($allowAuto -eq 1) -or ($autoEnabled -eq 1))
    }
}

function Set-RegistryDwordSafe {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][int]$Value
    )

    $target = "{0}::{1}" -f $Path, $Name

    if ($WhatIfPreference) {
        return Add-ActionResult -Action "set_registry" -Target $target -Changed $false -Skipped $true -Message "WhatIf: would set DWORD to $Value."
    }

    try {
        if (-not (Test-Path -LiteralPath $Path)) {
            New-Item -Path $Path -Force | Out-Null
        }

        New-ItemProperty -Path $Path -Name $Name -Value $Value -PropertyType DWord -Force | Out-Null
        return Add-ActionResult -Action "set_registry" -Target $target -Changed $true -Message "Set DWORD to $Value."
    }
    catch {
        return Add-ActionResult -Action "set_registry" -Target $target -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR"
    }
}

function Set-GameModeStateSafe {
    param([bool]$Enabled)

    $value = if ($Enabled) { 1 } else { 0 }
    $path = "HKCU:\Software\Microsoft\GameBar"

    $resultA = Set-RegistryDwordSafe -Path $path -Name "AllowAutoGameMode" -Value $value
    $resultB = Set-RegistryDwordSafe -Path $path -Name "AutoGameModeEnabled" -Value $value
    return @($resultA, $resultB)
}

function Resolve-PowerPlanTarget {
    param(
        [Parameter(Mandatory = $true)][string]$PlanName,
        [Parameter(Mandatory = $true)]$Settings
    )

    $knownPowerPlans = Get-ObjectValue -Object $Settings -Name "knownPowerPlans" -Default ([pscustomobject]@{})
    $mappedValue = Get-ObjectValue -Object $knownPowerPlans -Name $PlanName -Default $null
    if ($null -ne $mappedValue -and -not [string]::IsNullOrWhiteSpace([string]$mappedValue)) {
        return [string]$mappedValue
    }

    return $PlanName
}

function Set-PowerPlanSafe {
    param(
        [Parameter(Mandatory = $true)][string]$PlanName,
        [Parameter(Mandatory = $true)]$Settings
    )

    $target = Resolve-PowerPlanTarget -PlanName $PlanName -Settings $Settings

    if ($WhatIfPreference) {
        return Add-ActionResult -Action "set_power_plan" -Target $PlanName -Changed $false -Skipped $true -Message "WhatIf: would activate '$target'."
    }

    $result = Invoke-PowerCfgCommand -Arguments @("/setactive", $target)
    if ($result.success) {
        return Add-ActionResult -Action "set_power_plan" -Target $PlanName -Changed $true -Message "Activated '$target'."
    }

    $message = [string](Get-ObjectValue -Object $result -Name "output" -Default "")
    $exitCode = Get-ObjectValue -Object $result -Name "exitCode" -Default -1
    if ([string]::IsNullOrWhiteSpace($message)) {
        $message = "powercfg failed with exit code $exitCode."
    }

    return Add-ActionResult -Action "set_power_plan" -Target $PlanName -Success $false -Changed $false -Message $message -Severity "ERROR"
}

function Get-RunningWslDistros {
    $wslCmd = Get-Command wsl.exe -ErrorAction SilentlyContinue
    if (-not $wslCmd) {
        return @()
    }

    try {
        $lines = @(wsl.exe --list --quiet --running 2>$null)
        $names = @()
        foreach ($line in $lines) {
            $trimmed = ([string]$line).Trim()
            if (-not [string]::IsNullOrWhiteSpace($trimmed)) {
                $names += $trimmed
            }
        }
        return $names
    }
    catch {
        return @()
    }
}

function Invoke-WslShutdownSafe {
    $wslCmd = Get-Command wsl.exe -ErrorAction SilentlyContinue
    if (-not $wslCmd) {
        return Add-ActionResult -Action "shutdown_wsl" -Target "wsl.exe" -Changed $false -Skipped $true -Message "WSL is not installed." -Severity "WARN"
    }

    $running = @(Get-RunningWslDistros)
    if ($running.Count -eq 0) {
        return Add-ActionResult -Action "shutdown_wsl" -Target "WSL" -Changed $false -Skipped $true -Message "No running WSL distributions were detected."
    }

    if ($WhatIfPreference) {
        return Add-ActionResult -Action "shutdown_wsl" -Target "WSL" -Changed $false -Skipped $true -Message ("WhatIf: would shut down {0} running distro(s)." -f $running.Count)
    }

    try {
        wsl.exe --shutdown | Out-Null
        Start-Sleep -Milliseconds 500
        $remaining = @(Get-RunningWslDistros)
        if ($remaining.Count -gt 0) {
            return Add-ActionResult -Action "shutdown_wsl" -Target "WSL" -Changed $true -Message ("Requested WSL shutdown, but {0} distro(s) are still running: {1}" -f $remaining.Count, ($remaining -join ", ")) -Severity "WARN"
        }

        return Add-ActionResult -Action "shutdown_wsl" -Target "WSL" -Changed $true -Message ("Shut down {0} running distro(s)." -f $running.Count)
    }
    catch {
        return Add-ActionResult -Action "shutdown_wsl" -Target "WSL" -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR"
    }
}

function Get-ConfiguredProcessPatterns {
    param(
        [Parameter(Mandatory = $true)][string]$Category,
        [string[]]$Default = @()
    )

    $settings = $null
    if (Get-Variable -Name Settings -Scope Script -ErrorAction SilentlyContinue) {
        $settings = $script:Settings
    }

    $processPatterns = Get-ObjectValue -Object $settings -Name "processPatterns" -Default $null
    $patterns = Get-ObjectValue -Object $processPatterns -Name $Category -Default $null

    $normalized = @($patterns | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique)
    if ($normalized.Count -gt 0) {
        return $normalized
    }

    return @($Default)
}

function Get-DockerProcessPatterns {
    return @(Get-ConfiguredProcessPatterns -Category "docker" -Default @(
            "Docker*",
            "com.docker.*",
            "dockerd*"
        ))
}

function Find-ProcessesByPattern {
    param([Parameter(Mandatory = $true)][string]$Pattern)

    return @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like $Pattern })
}

function Find-ProcessesByPatterns {
    param([Parameter(Mandatory = $true)][string[]]$Patterns)

    $matches = @()
    foreach ($pattern in @($Patterns)) {
        $matches += @(Find-ProcessesByPattern -Pattern ([string]$pattern))
    }

    $seen = @{}
    $unique = @()
    foreach ($process in @($matches)) {
        if ($null -eq $process) {
            continue
        }

        $key = "{0}|{1}" -f $process.ProcessName, $process.Id
        if (-not $seen.ContainsKey($key)) {
            $seen[$key] = $true
            $unique += $process
        }
    }

    return @($unique)
}

function Stop-ProcessesByPatternSafe {
    param(
        [Parameter(Mandatory = $true)][string]$Pattern,
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)][ref]$RollbackState
    )

    $matches = @(Find-ProcessesByPattern -Pattern $Pattern)
    if ($matches.Count -eq 0) {
        return Add-ActionResult -Action "stop_process" -Target $Pattern -Changed $false -Skipped $true -Message "No matching processes were running."
    }

    if ($WhatIfPreference) {
        return Add-ActionResult -Action "stop_process" -Target $Pattern -Changed $false -Skipped $true -Message ("WhatIf: would stop {0} process(es)." -f $matches.Count)
    }

    $relaunchMappings = Get-ObjectValue -Object $Settings -Name "relaunchMappings" -Default ([pscustomobject]@{})
    $stoppedNames = @()

    foreach ($process in $matches) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        $stoppedNames += $process.ProcessName

        $launcherName = Get-ObjectValue -Object $relaunchMappings -Name $process.ProcessName -Default $null
        if ($null -ne $launcherName -and -not ($RollbackState.Value.relaunchers -contains $launcherName)) {
            $RollbackState.Value.relaunchers += $launcherName
        }
    }

    $RollbackState.Value.stoppedProcesses += $stoppedNames

    return Add-ActionResult -Action "stop_process" -Target $Pattern -Changed $true -Message ("Stopped {0} process(es): {1}" -f $matches.Count, (($stoppedNames | Sort-Object -Unique) -join ", "))
}

function Stop-ServiceSafe {
    param(
        [Parameter(Mandatory = $true)][string]$ServiceName,
        [Parameter(Mandatory = $true)][ref]$RollbackState
    )

    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service was not found."
    }

    if ($service.Status -ne "Running") {
        return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service is not running."
    }

    if (-not $script:IsAdmin) {
        return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Skipped: administrative privileges are required." -Severity "WARN"
    }

    if ($WhatIfPreference) {
        return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "WhatIf: would stop the service."
    }

    try {
        Stop-Service -Name $ServiceName -Force -ErrorAction Stop
        $RollbackState.Value.stoppedServices += $ServiceName
        return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $true -Message "Service stopped."
    }
    catch {
        return Add-ActionResult -Action "stop_service" -Target $ServiceName -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR"
    }
}

function Start-ServiceSafe {
    param([Parameter(Mandatory = $true)][string]$ServiceName)

    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service was not found."
    }

    if ($service.Status -eq "Running") {
        return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service is already running."
    }

    if (-not $script:IsAdmin) {
        return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Skipped: administrative privileges are required." -Severity "WARN"
    }

    if ($WhatIfPreference) {
        return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "WhatIf: would start the service."
    }

    try {
        Start-Service -Name $ServiceName -ErrorAction Stop
        return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $true -Message "Service started."
    }
    catch {
        return Add-ActionResult -Action "start_service" -Target $ServiceName -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR"
    }
}

function Resolve-LauncherSpec {
    param(
        [Parameter(Mandatory = $true)][string]$LauncherName,
        [Parameter(Mandatory = $true)]$Settings
    )

    $launchers = Get-ObjectValue -Object $Settings -Name "launchers" -Default ([pscustomobject]@{})
    return Get-ObjectValue -Object $launchers -Name $LauncherName -Default $null
}

function Start-LauncherSafe {
    param(
        [Parameter(Mandatory = $true)][string]$LauncherName,
        [Parameter(Mandatory = $true)]$Settings
    )

    $spec = Resolve-LauncherSpec -LauncherName $LauncherName -Settings $Settings
    if ($null -eq $spec) {
        return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $false -Skipped $true -Message "Launcher is not defined in config." -Severity "WARN"
    }

    $command = Get-ObjectValue -Object $spec -Name "command" -Default $null
    $arguments = @(Get-ObjectValue -Object $spec -Name "arguments" -Default @())
    $workingDirectory = Get-ObjectValue -Object $spec -Name "workingDirectory" -Default $null

    if ([string]::IsNullOrWhiteSpace([string]$command)) {
        return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $false -Skipped $true -Message "Launcher command is empty." -Severity "WARN"
    }

    if ($WhatIfPreference) {
        return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $false -Skipped $true -Message ("WhatIf: would start '{0}'." -f $command)
    }

    $startArgs = @{
        FilePath = $command
    }

    if ($arguments.Count -gt 0) {
        $startArgs["ArgumentList"] = $arguments
    }

    if (-not [string]::IsNullOrWhiteSpace([string]$workingDirectory)) {
        $startArgs["WorkingDirectory"] = $workingDirectory
    }

    try {
        Start-Process @startArgs | Out-Null
        return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $true -Message ("Started '{0}'." -f $command)
    }
    catch {
        return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR"
    }
}

function Apply-PriorityRules {
    param(
        [Parameter(Mandatory = $true)][array]$Rules,
        [Parameter(Mandatory = $true)][ref]$RollbackState
    )

    $blocked = @("RealTime")
    $processes = @(Get-Process -ErrorAction SilentlyContinue)

    foreach ($proc in $processes) {
        foreach ($rule in $Rules) {
            $pattern = [string](Get-ObjectValue -Object $rule -Name "match" -Default "")
            if ([string]::IsNullOrWhiteSpace($pattern)) { continue }
            if (-not ($proc.ProcessName -like $pattern)) { continue }

            $priorityStr = [string](Get-ObjectValue -Object $rule -Name "priority" -Default "Normal")
            $target = "$($proc.ProcessName)[$($proc.Id)]"

            if ($blocked -contains $priorityStr) {
                [void](Add-ActionResult -Action "set_priority" -Target $target -Success $false -Changed $false -Message "Priority '$priorityStr' is blocked for safety." -Severity "WARN")
                break
            }

            try {
                $oldPriority = $proc.PriorityClass
                $newPriority = [System.Diagnostics.ProcessPriorityClass]::$priorityStr

                if ($oldPriority -ne $newPriority) {
                    $RollbackState.Value.priorityChanges += [pscustomobject]@{
                        processName = $proc.ProcessName
                        pid         = $proc.Id
                        original    = [string]$oldPriority
                    }
                    if (-not $WhatIfPreference) {
                        $proc.PriorityClass = $newPriority
                    }
                    [void](Add-ActionResult -Action "set_priority" -Target $target -Changed $true -Message ("Priority {0} -> {1}" -f $oldPriority, $newPriority))
                }
                else {
                    [void](Add-ActionResult -Action "set_priority" -Target $target -Changed $false -Skipped $true -Message "Already $priorityStr")
                }
            }
            catch {
                [void](Add-ActionResult -Action "set_priority" -Target $target -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR")
            }
            break  # first matching rule wins per process
        }
    }
}

function Apply-GpuPreferences {
    param(
        [Parameter(Mandatory = $true)][array]$Rules,
        [Parameter(Mandatory = $true)][ref]$RollbackState
    )

    $regPath = "HKCU:\Software\Microsoft\DirectX\UserGpuPreferences"

    foreach ($rule in $Rules) {
        $exe = [string](Get-ObjectValue -Object $rule -Name "executable" -Default "")
        if ([string]::IsNullOrWhiteSpace($exe)) { continue }

        $prefStr = [string](Get-ObjectValue -Object $rule -Name "preference" -Default "SystemDefault")
        $value = switch ($prefStr) {
            "SystemDefault"   { "GpuPreference=0;" }
            "PowerSaving"     { "GpuPreference=1;" }
            "HighPerformance" { "GpuPreference=2;" }
            default           { "GpuPreference=0;" }
        }

        try {
            if (-not (Test-Path -LiteralPath $regPath)) {
                if (-not $WhatIfPreference) { New-Item -Path $regPath -Force | Out-Null }
            }

            $existing = (Get-ItemProperty -Path $regPath -Name $exe -ErrorAction SilentlyContinue).$exe

            $RollbackState.Value.gpuPreferences += [pscustomobject]@{
                executable = $exe
                original   = $existing  # $null = key did not exist before
            }

            if (-not $WhatIfPreference) {
                Set-ItemProperty -Path $regPath -Name $exe -Value $value
            }

            [void](Add-ActionResult -Action "set_gpu_preference" -Target $exe -Changed $true -Message ("GPU preference set to {0}" -f $prefStr))
        }
        catch {
            [void](Add-ActionResult -Action "set_gpu_preference" -Target $exe -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR")
        }
    }
}
