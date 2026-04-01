function Write-Log {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,

        [ValidateSet("INFO", "WARN", "ERROR", "DEBUG")]
        [string]$Level = "INFO"
    )

    if ($Quiet -and $Level -eq "INFO") {
        return
    }

    if ($Level -eq "DEBUG" -and -not $DebugMode) {
        return
    }

    $timestamp = Get-Date -Format "s"
    Write-Host ("[{0}] [{1}] {2}" -f $timestamp, $Level, $Message)
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Read-JsonFile {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Path,
        $Default = $null
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $Default
    }

    if (-not (Test-Path -LiteralPath $Path)) {
        return $Default
    }

    try {
        $raw = Get-Content -LiteralPath $Path -Raw
        if ([string]::IsNullOrWhiteSpace($raw)) {
            return $Default
        }
        return $raw | ConvertFrom-Json
    }
    catch {
        Write-Log "Failed to parse JSON file '$Path': $($_.Exception.Message)" "WARN"
        return $Default
    }
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Object
    )

    if ($WhatIfPreference) {
        return
    }

    $parent = Split-Path -Parent $Path
    if ($parent) {
        Ensure-Directory -Path $parent
    }

    $Object |
        ConvertTo-Json -Depth 10 |
        Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-PropertyNames {
    param($Object)

    if ($null -eq $Object) {
        return @()
    }

    if ($Object -is [hashtable]) {
        return @($Object.Keys)
    }

    return @($Object.PSObject.Properties | ForEach-Object { $_.Name })
}

function Get-ObjectValue {
    param(
        $Object,
        [Parameter(Mandatory = $true)][string]$Name,
        $Default = $null
    )

    if ($null -eq $Object) {
        return $Default
    }

    if ($Object -is [hashtable]) {
        if ($Object.ContainsKey($Name)) {
            return $Object[$Name]
        }
        return $Default
    }

    $property = $Object.PSObject.Properties[$Name]
    if ($null -ne $property) {
        return $property.Value
    }

    return $Default
}

function Is-MergeableObject {
    param($Value)

    if ($null -eq $Value) {
        return $false
    }

    if ($Value -is [string] -or $Value -is [ValueType] -or $Value -is [array]) {
        return $false
    }

    return ($Value -is [hashtable]) -or ($Value -is [psobject])
}

function Merge-Objects {
    param(
        $Base,
        $Override
    )

    if ($null -eq $Base) {
        return $Override
    }

    if ($null -eq $Override) {
        return $Base
    }

    if ((-not (Is-MergeableObject -Value $Base)) -or (-not (Is-MergeableObject -Value $Override))) {
        return $Override
    }

    $merged = [ordered]@{}
    $baseNames = @(Get-PropertyNames -Object $Base)
    $overrideNames = @(Get-PropertyNames -Object $Override)
    $allNames = @(($baseNames + $overrideNames) | Sort-Object -Unique)

    foreach ($name in $allNames) {
        $baseValue = Get-ObjectValue -Object $Base -Name $name
        $overrideValue = Get-ObjectValue -Object $Override -Name $name

        if ((Is-MergeableObject -Value $baseValue) -and (Is-MergeableObject -Value $overrideValue)) {
            $merged[$name] = Merge-Objects -Base $baseValue -Override $overrideValue
        }
        elseif ($null -ne $overrideValue) {
            $merged[$name] = $overrideValue
        }
        else {
            $merged[$name] = $baseValue
        }
    }

    return [pscustomobject]$merged
}

function Resolve-ConfigPath {
    param(
        [Parameter(Mandatory = $true)][string]$VariableName,
        [Parameter(Mandatory = $true)][string]$FileName
    )

    $resolvedPath = Get-Variable -Scope Script -Name $VariableName -ValueOnly -ErrorAction SilentlyContinue
    if (-not [string]::IsNullOrWhiteSpace($resolvedPath)) {
        return $resolvedPath
    }

    $configDir = Get-Variable -Scope Script -Name "ConfigDir" -ValueOnly -ErrorAction SilentlyContinue
    if ([string]::IsNullOrWhiteSpace($configDir)) {
        $root = Get-Variable -Scope Script -Name "Root" -ValueOnly -ErrorAction SilentlyContinue
        if (-not [string]::IsNullOrWhiteSpace($root)) {
            $configDir = Join-Path $root "config"
        }
    }

    if ([string]::IsNullOrWhiteSpace($configDir)) {
        return $null
    }

    return (Join-Path $configDir $FileName)
}

function Get-Settings {
    $defaultsPath = Resolve-ConfigPath -VariableName "DefaultsPath" -FileName "defaults.json"
    $machinePath = Resolve-ConfigPath -VariableName "MachinePath" -FileName "machine.local.json"
    $defaults = Read-JsonFile -Path $defaultsPath -Default ([pscustomobject]@{})
    $machine = Read-JsonFile -Path $machinePath -Default ([pscustomobject]@{})
    $machineSettings = Get-ObjectValue -Object $machine -Name "settings" -Default ([pscustomobject]@{})

    return Merge-Objects -Base $defaults -Override $machineSettings
}

function Get-Profiles {
    $profilesPath = Resolve-ConfigPath -VariableName "ProfilesPath" -FileName "profiles.json"
    $machinePath = Resolve-ConfigPath -VariableName "MachinePath" -FileName "machine.local.json"
    $profiles = Read-JsonFile -Path $profilesPath -Default ([pscustomobject]@{})
    $machine = Read-JsonFile -Path $machinePath -Default ([pscustomobject]@{})
    $machineProfiles = Get-ObjectValue -Object $machine -Name "profiles" -Default ([pscustomobject]@{})

    return Merge-Objects -Base $profiles -Override $machineProfiles
}
