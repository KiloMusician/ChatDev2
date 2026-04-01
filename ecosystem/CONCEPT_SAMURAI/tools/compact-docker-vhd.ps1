[CmdletBinding()]
param(
    [string]$DockerDataPath = "C:\Users\keath\AppData\Local\Docker\wsl\disk\docker_data.vhdx",
    [switch]$IncludeWslDisks,
    [switch]$ReportOnly,
    [switch]$SkipDockerShutdown
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "compact-docker-vhd.ps1 must run on Windows."
}

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-VhdTargets {
    param(
        [string]$PrimaryDockerPath,
        [switch]$IncludeExtraWslDisks
    )

    $targets = [System.Collections.Generic.List[string]]::new()
    if (Test-Path -LiteralPath $PrimaryDockerPath) {
        $targets.Add((Resolve-Path -LiteralPath $PrimaryDockerPath).Path)
    }

    if ($IncludeExtraWslDisks) {
        $extra = Get-ChildItem -Path "C:\Users\keath\AppData\Local\Packages" -Filter ext4.vhdx -Recurse -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty FullName
        foreach ($path in $extra) {
            if (-not $targets.Contains($path)) {
                $targets.Add($path)
            }
        }
    }

    return @($targets)
}

function Get-VhdReport {
    param([string[]]$Paths)

    return @(
        foreach ($path in $Paths) {
            if (-not (Test-Path -LiteralPath $path)) { continue }
            $item = Get-Item -LiteralPath $path
            [pscustomobject]@{
                path    = $item.FullName
                size_gb = [math]::Round($item.Length / 1GB, 2)
            }
        }
    )
}

function Invoke-DiskPartCompact {
    param([string]$Path)

    $scriptPath = Join-Path $env:TEMP ("compact-vhd-" + [guid]::NewGuid().ToString("N") + ".txt")
    try {
        @(
            "select vdisk file=`"$Path`""
            "attach vdisk readonly"
            "compact vdisk"
            "detach vdisk"
            "exit"
        ) | Set-Content -LiteralPath $scriptPath -Encoding ASCII

        $output = & diskpart /s $scriptPath 2>&1
        return ($output | Out-String)
    }
    finally {
        Remove-Item -LiteralPath $scriptPath -Force -ErrorAction SilentlyContinue
    }
}

$targets = @(Get-VhdTargets -PrimaryDockerPath $DockerDataPath -IncludeExtraWslDisks:$IncludeWslDisks)
if (-not $targets.Count) {
    throw "No VHD targets were found."
}

$before = Get-VhdReport -Paths $targets
$before | Format-Table -AutoSize

if ($ReportOnly) {
    return
}

if (-not (Test-IsAdmin)) {
    throw "Administrator rights are required to compact VHD files. Re-run from an elevated PowerShell session or use tools\keeper-compact-vhd-admin.cmd."
}

if (-not $SkipDockerShutdown) {
    Write-Host "Stopping Docker Desktop processes and shutting down WSL..."
    Get-Process -Name "Docker Desktop", "com.docker.backend", "com.docker.build" -ErrorAction SilentlyContinue |
        Stop-Process -Force -ErrorAction SilentlyContinue
    & wsl.exe --shutdown | Out-Null
    Start-Sleep -Seconds 3
}

$optimizeVhd = Get-Command Optimize-VHD -ErrorAction SilentlyContinue

foreach ($target in $targets) {
    Write-Host "Compacting $target"
    if ($optimizeVhd) {
        Optimize-VHD -Path $target -Mode Full
    }
    else {
        $diskPartOutput = Invoke-DiskPartCompact -Path $target
        Write-Host $diskPartOutput
    }
}

$after = Get-VhdReport -Paths $targets
$joined = for ($i = 0; $i -lt $before.Count; $i++) {
    $beforeItem = $before[$i]
    $afterItem = $after | Where-Object path -EQ $beforeItem.path | Select-Object -First 1
    [pscustomobject]@{
        path         = $beforeItem.path
        before_gb    = $beforeItem.size_gb
        after_gb     = $afterItem.size_gb
        reclaimed_gb = [math]::Round(($beforeItem.size_gb - $afterItem.size_gb), 2)
    }
}

Write-Host ""
Write-Host "Compaction summary:"
$joined | Format-Table -AutoSize
Write-Host ""
Write-Host "If Docker Desktop was stopped, restart it after compaction completes."
