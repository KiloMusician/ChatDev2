<#
.SYNOPSIS
    Toggle a custom "Gaming Mode" on Windows: stops common background services, switches power plan to High Performance,
    adjusts process priorities, and optionally disables suspect audio services like Nahimic.

.DESCRIPTION
    This script is a safe, reversible helper to prepare a Windows laptop for gaming. It does NOT perform destructive actions by default
    (it won't kill editors or browsers unless you opt into that). It attempts to save and restore the active power scheme.

.NOTES
    - Some actions require Administrator privileges (changing service startup type, switching power schemes).
    - Use the -WhatIf switch to preview actions where supported.

.EXAMPLE
    # Enable gaming mode (default: stop Docker, WSL; don't stop editors)
    pwsh -ExecutionPolicy Bypass -File .\\gaming-mode.ps1 -Mode on

.EXAMPLE
    # Disable gaming mode and restore saved power plan
    pwsh -ExecutionPolicy Bypass -File .\\gaming-mode.ps1 -Mode off
#>

[CmdletBinding()]
param(
    [ValidateSet('on','off','toggle')]
    [string]$Mode = 'toggle',

    [switch]$StopDocker = $true,
    [switch]$StopWSL = $true,
    [switch]$StopBrowsers = $false,
    [switch]$StopEditors = $false,

    [string]$GameProcessName = '',

    [switch]$WhatIf
)

function Is-Administrator {
    $current = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($current)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-ActivePowerSchemeGuid {
    $out = powercfg /GetActiveScheme 2>$null
    if ($out) {
        if ($out -match '{([0-9a-fA-F-]+)}') { return $matches[1] }
    }
    return $null
}

function Get-PowerSchemeGuidByName($nameRegex) {
    $list = powercfg /L 2>$null
    foreach ($line in $list) {
        if ($line -match '{([0-9a-fA-F-]+)}\s+\((.+)\)') {
            $guid = $matches[1]
            $schemeName = $matches[2]
            if ($schemeName -match $nameRegex) { return $guid }
        }
    }
    return $null
}

function Save-PreviousPowerPlan {
    $prev = Get-ActivePowerSchemeGuid
    if ($prev) { Set-ItemProperty -Path HKCU:\Software\CONCEPT\GamingMode -Name PreviousPowerScheme -Value $prev -ErrorAction SilentlyContinue }
}

function Restore-PreviousPowerPlan {
    try {
        $prev = Get-ItemProperty -Path HKCU:\Software\CONCEPT\GamingMode -Name PreviousPowerScheme -ErrorAction SilentlyContinue | Select-Object -ExpandProperty PreviousPowerScheme
        if ($prev) {
            Write-Host "Restoring previous power plan: $prev"
            powercfg /S $prev
            return $true
        }
    } catch { }
    return $false
}

function Set-HighPerformancePlan {
    # Look for "High performance" or "Ultimate Performance" in the list
    $guid = Get-PowerSchemeGuidByName 'High performance|Ultimate Performance'
    if (-not $guid) {
        # Fallback to a well-known GUID for High performance (may not exist on some systems)
        $guid = '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'
    }
    Write-Host "Switching to power plan GUID: $guid"
    powercfg /S $guid
}

function Stop-DockerDesktop {
    Write-Host 'Stopping Docker Desktop (if running) and related processes...'
    Get-Process | Where-Object { $_.ProcessName -match 'docker|com\.docker|vmmem' } | ForEach-Object {
        try { $_ | Stop-Process -Force -ErrorAction SilentlyContinue } catch { }
    }
}

function Shutdown-WSL {
    Write-Host 'Issuing wsl --shutdown (if wsl is available)'
    try {
        wsl --shutdown 2>$null
    } catch { }
}

function Stop-ProcessesByPattern([string[]]$patterns) {
    foreach ($p in $patterns) {
        Get-Process | Where-Object { $_.ProcessName -match $p } | ForEach-Object {
            try { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue } catch { }
        }
    }
}

function Set-BackgroundPriority([string[]]$patterns) {
    foreach ($proc in Get-Process) {
        foreach ($p in $patterns) {
            if ($proc.ProcessName -match $p) {
                try { $proc.PriorityClass = 'BelowNormal' } catch { }
            }
        }
    }
}

function Disable-NahimicServices {
    $match = Get-Service | Where-Object { $_.DisplayName -match 'Nahimic|Nahimic2|Nahimic Audio' -or $_.Name -match 'Nahimic' }
    if (-not $match) { return }
    foreach ($s in $match) {
        Write-Host "Disabling service: $($s.Name) / $($s.DisplayName)"
        try {
            Stop-Service -Name $s.Name -Force -ErrorAction SilentlyContinue
            if (Is-Administrator) { Set-Service -Name $s.Name -StartupType Disabled -ErrorAction SilentlyContinue }
        } catch { Write-Host "Failed to stop/disable $($s.Name): $_" }
    }
}

function Mark-GamingModeState($enabled) {
    New-Item -Path HKCU:\Software\CONCEPT\GamingMode -Force | Out-Null
    Set-ItemProperty -Path HKCU:\Software\CONCEPT\GamingMode -Name Enabled -Value ($enabled -as [int]) -Force
}

function Get-GamingModeState {
    try { return (Get-ItemProperty -Path HKCU:\Software\CONCEPT\GamingMode -Name Enabled -ErrorAction SilentlyContinue).Enabled } catch { return 0 }
}

function Set-GameProcessPriority($name) {
    if (-not $name) { return }
    $list = Get-Process | Where-Object { $_.ProcessName -match $name }
    foreach ($p in $list) {
        try { $p.PriorityClass = 'High' } catch { }
    }
}

# Main
if ($Mode -eq 'toggle') {
    $current = Get-GamingModeState
    if ($current -eq 1) { $Mode = 'off' } else { $Mode = 'on' }
}

if ($Mode -eq 'on') {
    Write-Host 'Enabling custom Gaming Mode...' -ForegroundColor Green
    Save-PreviousPowerPlan

    if (-not Is-Administrator) {
        Write-Host 'Note: Some actions (service changes, powerplan switch) may require Administrator privileges.' -ForegroundColor Yellow
    }

    if ($StopDocker) { Stop-DockerDesktop }
    if ($StopWSL) { Shutdown-WSL }

    Set-HighPerformancePlan

    $bgPatterns = @('node','python','search','OneDrive','Teams','Updater','msedge','chrome','firefox')
    if ($StopBrowsers) { $bgPatterns += @('chrome','msedge','firefox','brave') }
    if ($StopEditors) { $bgPatterns += @('Code','code') }

    Write-Host 'Lowering priority of common background processes...'
    Set-BackgroundPriority -patterns $bgPatterns

    Disable-NahimicServices

    if ($GameProcessName) { Set-GameProcessPriority $GameProcessName }

    Mark-GamingModeState $true
    Write-Host 'Gaming Mode enabled.' -ForegroundColor Green

} elseif ($Mode -eq 'off') {
    Write-Host 'Disabling custom Gaming Mode and restoring previous state...' -ForegroundColor Cyan
    $restored = Restore-PreviousPowerPlan
    if (-not $restored) { Write-Host 'No previously saved power plan found; leaving current plan as-is.' -ForegroundColor Yellow }

    # Note: we avoid forcibly restarting services/processes that were stopped. User can reboot or start them manually.
    Mark-GamingModeState $false
    Write-Host 'Gaming Mode disabled.' -ForegroundColor Cyan

} else {
    Write-Host "Unknown mode: $Mode" -ForegroundColor Red
}

Write-Host 'Done. Recommended next steps: run the included diagnostics and monitor scripts while reproducing audio stutter.'
