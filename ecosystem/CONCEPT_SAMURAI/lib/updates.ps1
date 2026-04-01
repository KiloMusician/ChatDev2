function Get-WingetExecutablePath {
    $candidates = @()

    if (Get-Variable -Name Settings -Scope Script -ErrorAction SilentlyContinue) {
        $updatesSettings = Get-ObjectValue -Object $script:Settings -Name "updates" -Default ([pscustomobject]@{})
        $configuredCommand = Get-ObjectValue -Object $updatesSettings -Name "wingetCommand" -Default $null
        if (-not [string]::IsNullOrWhiteSpace([string]$configuredCommand)) {
            $candidates += [string]$configuredCommand
        }
    }

    $appInstallerPackage = Get-AppxPackage Microsoft.DesktopAppInstaller -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $appInstallerPackage) {
        $installLocation = [string](Get-ObjectValue -Object $appInstallerPackage -Name "InstallLocation" -Default $null)
        if (-not [string]::IsNullOrWhiteSpace($installLocation)) {
            $candidates += (Join-Path $installLocation "winget.exe")
        }
    }

    $localWindowsApps = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\winget.exe"
    $candidates += @(
        $localWindowsApps,
        "winget.exe"
    )

    foreach ($candidate in @($candidates | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }

        try {
            $command = Get-Command $candidate -ErrorAction Stop
            if ($null -ne $command -and -not [string]::IsNullOrWhiteSpace([string]$command.Source)) {
                return [string]$command.Source
            }
        }
        catch {
        }
    }

    $whereResult = Invoke-ExternalProcess -FilePath "cmd.exe" -Arguments @("/d", "/c", "where winget")
    if ((Get-ObjectValue -Object $whereResult -Name "success" -Default $false)) {
        $firstPath = @(([string](Get-ObjectValue -Object $whereResult -Name "output" -Default "")) -split "\r?\n" |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Select-Object -First 1)
        if ($firstPath.Count -gt 0) {
            return [string]$firstPath[0]
        }
    }

    return $null
}

function Invoke-WingetCommand {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    $wingetCommand = "%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe"
    if (Get-Variable -Name Settings -Scope Script -ErrorAction SilentlyContinue) {
        $updatesSettings = Get-ObjectValue -Object $script:Settings -Name "updates" -Default ([pscustomobject]@{})
        $configuredCommand = Get-ObjectValue -Object $updatesSettings -Name "wingetCommand" -Default $null
        if (-not [string]::IsNullOrWhiteSpace([string]$configuredCommand)) {
            $wingetCommand = [string]$configuredCommand
        }
    }

    $tempCmd = [System.IO.Path]::ChangeExtension([System.IO.Path]::GetTempFileName(), ".cmd")
    $tempOut = [System.IO.Path]::ChangeExtension([System.IO.Path]::GetTempFileName(), ".txt")
    $commandText = (Format-CmdArgument -Value $wingetCommand) + " " + (($Arguments | ForEach-Object { Format-CmdArgument -Value $_ }) -join " ")
    $scriptBody = [string]::Format(
        '@echo off{0}{1} > "{2}" 2>&1{0}',
        [Environment]::NewLine,
        $commandText,
        $tempOut
    )

    [System.IO.File]::WriteAllText($tempCmd, $scriptBody, [System.Text.Encoding]::ASCII)

    $shellResult = Invoke-ExternalProcess -FilePath "cmd.exe" -Arguments @("/d", "/c", $tempCmd)
    $output = ""
    if (Test-Path -LiteralPath $tempOut) {
        $output = [string](Get-Content -LiteralPath $tempOut -Raw -ErrorAction SilentlyContinue)
    }

    [System.IO.File]::Delete($tempCmd)
    [System.IO.File]::Delete($tempOut)

    if ([string]::IsNullOrWhiteSpace($output) -and -not (Get-ObjectValue -Object $shellResult -Name "success" -Default $false)) {
        return [pscustomobject]@{
            success  = $false
            exitCode = Get-ObjectValue -Object $shellResult -Name "exitCode" -Default -1
            output   = [string](Get-ObjectValue -Object $shellResult -Name "output" -Default "winget output could not be captured.")
        }
    }

    return [pscustomobject]@{
        success  = [bool](Get-ObjectValue -Object $shellResult -Name "success" -Default $false)
        exitCode = Get-ObjectValue -Object $shellResult -Name "exitCode" -Default -1
        output   = $output
    }
}

function Get-WingetVersionInfo {
    $result = Invoke-WingetCommand -Arguments @("--version")
    $version = [string](Get-ObjectValue -Object $result -Name "output" -Default "")

    return [pscustomobject]@{
        available = [bool](Get-ObjectValue -Object $result -Name "success" -Default $false)
        version   = $version.Trim()
        raw       = $version
    }
}

function ConvertFrom-WingetUpgradeOutput {
    param([Parameter(Mandatory = $true)][string]$Text)

    $lines = @($Text -split "\r?\n")
    $headerIndex = -1
    $headerLine = $null
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $candidate = [string]$lines[$i]
        if ($candidate -match 'Name\s{2,}Id\s{2,}Version\s{2,}Available\s{2,}Source') {
            $headerIndex = $i
            $nameStart = $candidate.IndexOf("Name")
            if ($nameStart -lt 0) {
                $nameStart = 0
            }
            $headerLine = $candidate.Substring($nameStart).TrimEnd()
            break
        }
    }

    if ($headerIndex -lt 0) {
        return @()
    }

    $idStart = $headerLine.IndexOf("Id")
    $versionStart = $headerLine.IndexOf("Version")
    $availableStart = $headerLine.IndexOf("Available")
    $sourceStart = $headerLine.IndexOf("Source")

    $items = @()
    for ($i = $headerIndex + 1; $i -lt $lines.Count; $i++) {
        $line = ([string]$lines[$i]).TrimStart()
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        if ($line -match '^\s*\d+\s+upgrades?\s+available\.?\s*$') {
            break
        }

        if ($line -match '^[\-\s]+$') {
            continue
        }

        if ($line.Length -lt $sourceStart) {
            continue
        }

        $items += [pscustomobject]@{
            Name      = $line.Substring(0, $idStart).Trim()
            Id        = $line.Substring($idStart, $versionStart - $idStart).Trim()
            Version   = $line.Substring($versionStart, $availableStart - $versionStart).Trim()
            Available = $line.Substring($availableStart, $sourceStart - $availableStart).Trim()
            Source    = $line.Substring($sourceStart).Trim()
        }
    }

    return @($items | Where-Object { -not [string]::IsNullOrWhiteSpace($_.Id) })
}

function Get-WindowsUpdateCapability {
    $module = Get-Module -ListAvailable PSWindowsUpdate | Sort-Object Version -Descending | Select-Object -First 1

    return [pscustomobject]@{
        module_available = ($null -ne $module)
        module_name      = if ($module) { $module.Name } else { $null }
        module_version   = if ($module) { [string]$module.Version } else { $null }
        supported        = ($null -ne $module)
        notes            = if ($module) {
            @("PSWindowsUpdate is installed, so Windows Update automation can be added later if you explicitly want it.")
        }
        else {
            @("Windows package updates are supported through winget right now. Windows Update automation is intentionally not enabled by default.")
        }
    }
}

function Test-UpdateValueMatch {
    param(
        [string]$Value,
        [string[]]$Patterns,
        [switch]$Exact
    )

    if ([string]::IsNullOrWhiteSpace([string]$Value)) {
        return $false
    }

    foreach ($pattern in @($Patterns)) {
        if ([string]::IsNullOrWhiteSpace([string]$pattern)) {
            continue
        }

        if ($Exact) {
            if ([string]::Equals($Value, [string]$pattern, [System.StringComparison]::OrdinalIgnoreCase)) {
                return $true
            }
        }
        elseif ($Value -like [string]$pattern) {
            return $true
        }
    }

    return $false
}

function Get-GuardedUpdateSets {
    param(
        [Parameter(Mandatory = $true)]$Packages,
        [Parameter(Mandatory = $true)]$Settings
    )

    $updatesSettings = Get-ObjectValue -Object $Settings -Name "updates" -Default ([pscustomobject]@{})
    $allowIds = @(Get-ObjectValue -Object $updatesSettings -Name "allowPackageIds" -Default @())
    $allowNamePatterns = @(Get-ObjectValue -Object $updatesSettings -Name "allowNamePatterns" -Default @())
    $denyIds = @(Get-ObjectValue -Object $updatesSettings -Name "denyPackageIds" -Default @())
    $denyNamePatterns = @(Get-ObjectValue -Object $updatesSettings -Name "denyNamePatterns" -Default @())

    $allowed = @()
    $blocked = @()

    foreach ($package in @($Packages)) {
        $id = [string](Get-ObjectValue -Object $package -Name "Id" -Default "")
        $name = [string](Get-ObjectValue -Object $package -Name "Name" -Default "")

        $explicitlyAllowed = (Test-UpdateValueMatch -Value $id -Patterns $allowIds -Exact) -or
            (Test-UpdateValueMatch -Value $name -Patterns $allowNamePatterns)
        $blockedById = Test-UpdateValueMatch -Value $id -Patterns $denyIds -Exact
        $blockedByName = Test-UpdateValueMatch -Value $name -Patterns $denyNamePatterns

        if ($explicitlyAllowed -or (-not $blockedById -and -not $blockedByName)) {
            $allowed += [pscustomobject]@{
                Name      = $name
                Id        = $id
                Version   = Get-ObjectValue -Object $package -Name "Version" -Default $null
                Available = Get-ObjectValue -Object $package -Name "Available" -Default $null
                Source    = Get-ObjectValue -Object $package -Name "Source" -Default $null
                decision  = if ($explicitlyAllowed) { "allowed_by_override" } else { "allowed" }
            }
        }
        else {
            $reason = if ($blockedById) {
                "blocked by denyPackageIds"
            }
            else {
                "blocked by denyNamePatterns"
            }

            $blocked += [pscustomobject]@{
                Name      = $name
                Id        = $id
                Version   = Get-ObjectValue -Object $package -Name "Version" -Default $null
                Available = Get-ObjectValue -Object $package -Name "Available" -Default $null
                Source    = Get-ObjectValue -Object $package -Name "Source" -Default $null
                decision  = "blocked"
                reason    = $reason
            }
        }
    }

    return [pscustomobject]@{
        allow_ids           = @($allowIds)
        allow_name_patterns = @($allowNamePatterns)
        deny_ids            = @($denyIds)
        deny_name_patterns  = @($denyNamePatterns)
        allowed             = @($allowed)
        blocked             = @($blocked)
    }
}

function Get-UpdateReport {
    param([Parameter(Mandatory = $true)]$Settings)

    $versionInfo = Get-WingetVersionInfo
    if (-not $versionInfo.available) {
        return [pscustomobject]@{
            generated_at               = (Get-Date).ToString("o")
            winget_available           = $false
            winget_version             = $null
            total_updates             = 0
            packages                  = @()
            windows_update_capability = Get-WindowsUpdateCapability
            notes                     = @("winget is not available in the current environment.")
        }
    }

    $result = Invoke-WingetCommand -Arguments @("upgrade", "--accept-source-agreements", "--disable-interactivity")
    $packages = @(ConvertFrom-WingetUpgradeOutput -Text ([string](Get-ObjectValue -Object $result -Name "output" -Default "")))
    $guarded = Get-GuardedUpdateSets -Packages $packages -Settings $Settings

    $notes = @()
    if ($packages.Count -eq 0) {
        $notes += "No winget-managed package upgrades were detected."
    }
    else {
        $notes += ("{0} winget-managed package upgrade(s) available." -f $packages.Count)
        if ($guarded.blocked.Count -gt 0) {
            $notes += ("{0} upgrade(s) are currently blocked by update policy." -f $guarded.blocked.Count)
        }
    }

    return [pscustomobject]@{
        generated_at               = (Get-Date).ToString("o")
        winget_available           = $true
        winget_version             = $versionInfo.version
        total_updates              = $packages.Count
        packages                   = @($packages)
        allowed_updates            = @($guarded.allowed)
        blocked_updates            = @($guarded.blocked)
        allowed_update_count       = @($guarded.allowed).Count
        blocked_update_count       = @($guarded.blocked).Count
        policy                     = [pscustomobject]@{
            allow_ids           = @($guarded.allow_ids)
            allow_name_patterns = @($guarded.allow_name_patterns)
            deny_ids            = @($guarded.deny_ids)
            deny_name_patterns  = @($guarded.deny_name_patterns)
        }
        windows_update_capability  = Get-WindowsUpdateCapability
        notes                      = @($notes)
    }
}

function Invoke-Updates {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [switch]$Silent
    )

    $before = Get-UpdateReport -Settings $Settings
    if (-not (Get-ObjectValue -Object $before -Name "winget_available" -Default $false)) {
        return [pscustomobject]@{
            applied         = $false
            success         = $false
            generated_at    = (Get-Date).ToString("o")
            message         = "winget is not available."
            updates_before  = $before
            updates_after   = $before
        }
    }

    $packages = @(Get-ObjectValue -Object $before -Name "allowed_updates" -Default @())
    $blocked = @(Get-ObjectValue -Object $before -Name "blocked_updates" -Default @())
    if ($packages.Count -eq 0) {
        return [pscustomobject]@{
            applied         = $false
            success         = $true
            generated_at    = (Get-Date).ToString("o")
            message         = if ($blocked.Count -gt 0) { "All detected package upgrades are blocked by policy." } else { "No package upgrades are currently available." }
            updates_before  = $before
            updates_after   = $before
            blocked_updates = @($blocked)
        }
    }

    if ($WhatIfPreference) {
        return [pscustomobject]@{
            applied         = $false
            success         = $true
            generated_at    = (Get-Date).ToString("o")
            message         = "WhatIf: would apply all policy-approved winget upgrades."
            approved_update_ids = @($packages | Select-Object -ExpandProperty Id)
            blocked_update_ids  = @($blocked | Select-Object -ExpandProperty Id)
            updates_before  = $before
            updates_after   = $before
        }
    }

    $results = @()
    foreach ($package in $packages) {
        $args = @(
            "upgrade",
            "--id", ([string](Get-ObjectValue -Object $package -Name "Id" -Default "")),
            "-e",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--disable-interactivity"
        )

        $source = [string](Get-ObjectValue -Object $package -Name "Source" -Default "")
        if (-not [string]::IsNullOrWhiteSpace($source)) {
            $args += @("--source", $source)
        }

        if ($Silent) {
            $args += "--silent"
        }

        $result = Invoke-WingetCommand -Arguments $args
        $results += [pscustomobject]@{
            id       = Get-ObjectValue -Object $package -Name "Id" -Default $null
            name     = Get-ObjectValue -Object $package -Name "Name" -Default $null
            source   = $source
            success  = [bool](Get-ObjectValue -Object $result -Name "success" -Default $false)
            exitCode = Get-ObjectValue -Object $result -Name "exitCode" -Default -1
            output   = [string](Get-ObjectValue -Object $result -Name "output" -Default "")
        }
    }

    $after = Get-UpdateReport -Settings $Settings
    $failures = @($results | Where-Object { -not $_.success })

    return [pscustomobject]@{
        applied         = $true
        success         = ($failures.Count -eq 0)
        generated_at    = (Get-Date).ToString("o")
        message         = if ($failures.Count -eq 0) { "Policy-approved winget upgrades completed." } else { "One or more policy-approved winget upgrades failed." }
        updates_before  = $before
        updates_after   = $after
        approved_update_ids = @($packages | Select-Object -ExpandProperty Id)
        blocked_update_ids  = @($blocked | Select-Object -ExpandProperty Id)
        results         = @($results)
    }
}
