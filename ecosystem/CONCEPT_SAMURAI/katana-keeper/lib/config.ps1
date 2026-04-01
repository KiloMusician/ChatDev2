# lib/config.ps1
# Config loading, JSON utilities, and object merge helpers.
# Depends on: nothing. Dot-sourced first by keeper.ps1.
# All $script:*Path variables must be set by the caller before dot-sourcing.

function Write-Log {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [ValidateSet("INFO","WARN","ERROR","DEBUG")][string]$Level = "INFO"
    )
    if ($Quiet -and $Level -eq "INFO") { return }
    if ($Level -eq "DEBUG" -and -not $DebugMode) { return }
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
    param([Parameter(Mandatory = $true)][string]$Path, $Default = $null)
    if (-not (Test-Path -LiteralPath $Path)) { return $Default }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw
        if ([string]::IsNullOrWhiteSpace($raw)) { return $Default }
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
    if ($WhatIfPreference) { return }
    $parent = Split-Path -Parent $Path
    if ($parent) { Ensure-Directory -Path $parent }
    $Object | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-PropertyNames {
    param($Object)
    if ($null -eq $Object) { return @() }
    if ($Object -is [hashtable]) { return @($Object.Keys) }
    return @($Object.PSObject.Properties | ForEach-Object { $_.Name })
}

function Get-ObjectValue {
    param($Object, [Parameter(Mandatory = $true)][string]$Name, $Default = $null)
    if ($null -eq $Object) { return $Default }
    if ($Object -is [hashtable]) {
        if ($Object.ContainsKey($Name)) { return $Object[$Name] }
        return $Default
    }
    $prop = $Object.PSObject.Properties[$Name]
    if ($null -ne $prop) { return $prop.Value }
    return $Default
}

function Is-MergeableObject {
    param($Value)
    if ($null -eq $Value) { return $false }
    if ($Value -is [string] -or $Value -is [int] -or $Value -is [bool] -or $Value -is [double]) { return $false }
    if ($Value -is [System.Array]) { return $false }
    if ($Value -is [hashtable]) { return $true }
    if ($Value -is [pscustomobject]) { return $true }
    return $false
}

function Merge-Objects {
    param($Base, $Override)
    if ($null -eq $Base)     { return $Override }
    if ($null -eq $Override) { return $Base }
    $result = [ordered]@{}
    foreach ($name in @(Get-PropertyNames -Object $Base)) { $result[$name] = Get-ObjectValue -Object $Base -Name $name }
    foreach ($name in @(Get-PropertyNames -Object $Override)) {
        $baseVal     = Get-ObjectValue -Object $Base     -Name $name -Default $null
        $overrideVal = Get-ObjectValue -Object $Override -Name $name -Default $null
        if ((Is-MergeableObject -Value $baseVal) -and (Is-MergeableObject -Value $overrideVal)) {
            $result[$name] = Merge-Objects -Base $baseVal -Override $overrideVal
        } else {
            $result[$name] = $overrideVal
        }
    }
    return [pscustomobject]$result
}

function Get-Settings {
    $defaults        = Read-JsonFile -Path $script:DefaultsPath -Default ([pscustomobject]@{})
    $machine         = Read-JsonFile -Path $script:MachinePath  -Default ([pscustomobject]@{})
    $machineSettings = Get-ObjectValue -Object $machine -Name "settings" -Default ([pscustomobject]@{})
    return Merge-Objects -Base $defaults -Override $machineSettings
}

function Get-Profiles {
    $profiles        = Read-JsonFile -Path $script:ProfilesPath -Default ([pscustomobject]@{})
    $machine         = Read-JsonFile -Path $script:MachinePath  -Default ([pscustomobject]@{})
    $machineProfiles = Get-ObjectValue -Object $machine -Name "profiles" -Default ([pscustomobject]@{})
    return Merge-Objects -Base $profiles -Override $machineProfiles
}
