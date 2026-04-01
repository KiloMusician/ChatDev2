<#
.SYNOPSIS
  Safely list processes along with a truncated CommandLine field.
#>

param(
    [int]$Truncate = 240
)

try {
    $procs = Get-CimInstance -ClassName Win32_Process -ErrorAction Stop
} catch {
    Write-Error "Failed to query Win32_Process: $_"
    exit 2
}

foreach ($p in $procs) {
    $cmd = ''
    if ($p.CommandLine) { $cmd = [string]$p.CommandLine }
    if ($cmd.Length -gt $Truncate) { $short = $cmd.Substring(0,$Truncate) + '...' } else { $short = $cmd }

    $obj = [PSCustomObject]@{
        ProcessId = $p.ProcessId
        Name = $p.Name
        ExecutablePath = ($p.ExecutablePath -as [string])
        CommandLine = $short
        RawCommandLineLength = ($cmd.Length)
    }

    $obj | ConvertTo-Json -Compress
}
<#
. Get-ProcessesByCmdline.ps1
.
Purpose: Safely enumerate Windows processes and print one JSON object per process
containing ProcessId, Name and CommandLine. CommandLine newlines are normalized so
the output never begins with a leading dot token like ".CommandLine" which can
accidentally be parsed as a PowerShell command in some contexts.

Usage:
  pwsh -NoProfile -File .\scripts\pwsh_helpers\Get-ProcessesByCmdline.ps1
  pwsh -NoProfile -File .\scripts\pwsh_helpers\Get-ProcessesByCmdline.ps1 -Max 50
#>

param(
    [int]$Max = 0
)

# Defensive: prefer CIM over Get-Process for the CommandLine property
try {
    $procs = Get-CimInstance Win32_Process -ErrorAction Stop
} catch {
    Write-Error "Failed to query Win32_Process: $_"
    exit 2
}

if ($Max -gt 0) { $procs = $procs | Select-Object -First $Max }

foreach ($p in $procs) {
    # Normalize CommandLine to a single-line string and remove CR/LF characters
    $cmd = $p.CommandLine
    if ($null -eq $cmd) { $cmd = '' }
    else { $cmd = ($cmd -replace "\r|\n", ' ') }

    # Build a safe object and write as compact JSON (one object per line)
    $obj = [PSCustomObject]@{
        ProcessId  = $p.ProcessId
        Name       = $p.Name
        CommandLine = $cmd
    }

    $obj | ConvertTo-Json -Compress
}
