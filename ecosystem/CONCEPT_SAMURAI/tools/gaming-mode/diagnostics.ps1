<#
.SYNOPSIS
    Quick diagnostics to collect system info relevant to audio stutter: OS, CPU, GPU, audio devices, installed audio drivers, running dev processes and common suspect services.

.DESCRIPTION
    Run this script and attach the output when reporting issues. It helps identify likely culprits (Nahimic, Realtek, old GPU drivers, lingering WSL/docker processes).
#>

Write-Host 'Collecting system diagnostics for audio stutter troubleshooting...' -ForegroundColor Cyan

function Safe-Write {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [object[]]$Parts
    )

    Write-Host (($Parts | ForEach-Object { [string]$_ }) -join ' ')
}

function Get-SafeProcessSnapshot {
    param([int]$Top = 10)

    return @(Get-Process | ForEach-Object {
        $cpuSeconds = $null
        try {
            if ($null -ne $_.CPU) {
                $cpuSeconds = [math]::Round([double]$_.CPU, 2)
            }
        }
        catch {
            $cpuSeconds = $null
        }

        if ($null -eq $cpuSeconds) {
            try {
                $cpuSeconds = [math]::Round($_.TotalProcessorTime.TotalSeconds, 2)
            }
            catch {
                $cpuSeconds = $null
            }
        }

        [pscustomobject]@{
            Id           = $_.Id
            ProcessName  = $_.ProcessName
            CPUSeconds   = $cpuSeconds
            WorkingSetMB = [math]::Round($_.WorkingSet64 / 1MB, 2)
        }
    } |
    Sort-Object @{ Expression = { if ($null -ne $_.CPUSeconds) { [double]$_.CPUSeconds } else { -1 } } } -Descending |
    Select-Object -First $Top)
}

Safe-Write 'Timestamp:' (Get-Date -Format o)

Safe-Write "OS:"
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber | Format-List

Safe-Write "CPU:"
Get-CimInstance Win32_Processor | Select-Object Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | Format-List

Safe-Write "GPU(s):"
Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,Status | Format-List

Safe-Write "Audio devices (Win32_SoundDevice):"
Get-CimInstance Win32_SoundDevice | Select-Object Name,Manufacturer,Status,DeviceID | Format-List

Safe-Write "Installed PnP audio drivers (sample):"
Get-WmiObject Win32_PnPSignedDriver | Where-Object { $_.DeviceClass -match 'MEDIA|SOUND' } | Select-Object DeviceName,DriverVersion,Manufacturer,InfName | Format-Table -AutoSize

Safe-Write "Installed services that look like Nahimic/Dolby/Realtek or audio enhancers:"
Get-Service | Where-Object { $_.DisplayName -match 'Nahimic|Dolby|Realtek|Audio' -or $_.Name -match 'Nahimic|Dolby|Realtek|Audio' } | Select-Object Name,DisplayName,Status,StartType | Format-Table -AutoSize

Safe-Write "Top CPU-consuming processes (snapshot):"
Get-SafeProcessSnapshot -Top 10 | Format-Table -AutoSize

Safe-Write "MSI-specific common apps (MSI Center / Nahimic) installed? Check Program Files x86:"
Get-ChildItem 'C:\Program Files (x86)' -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'MSI|Nahimic|Nahimic2|Dragon Center|MSI Center' } | Select-Object Name,FullName | Format-Table -AutoSize

Safe-Write "Running WSL / Docker related processes (if any):"
Get-SafeProcessSnapshot -Top 200 | Where-Object { $_.ProcessName -match 'wsl|vmmem|docker|com.docker' } | Select-Object Id,ProcessName,CPUSeconds | Format-Table -AutoSize

Safe-Write "Power profile (active):"
powercfg /GetActiveScheme 2>$null

Safe-Write "Energy report suggestion:"
Safe-Write "If you can run as Administrator, run: powercfg /energy /output %USERPROFILE%\\energy-report.html  (takes ~60s)"

Safe-Write "LatencyMon suggestion:"
Safe-Write "Download and run LatencyMon (https://www.resplendence.com/latencymon) while reproducing the audio stutter for best DPC/driver root cause info. Attach report when available."

Write-Host 'Diagnostics collection complete.' -ForegroundColor Green
