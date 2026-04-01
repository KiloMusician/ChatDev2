<#
.SYNOPSIS
    Lightweight system monitor that samples CPU, memory, top processes and (if available) NVIDIA GPU stats and writes CSV logs.

.DESCRIPTION
    Useful to run while reproducing audio stutter so you can correlate CPU/GPU/process spikes with glitches.

.EXAMPLE
    pwsh -ExecutionPolicy Bypass -File .\\monitor-usage.ps1 -DurationSeconds 300 -IntervalSeconds 2 -Output .\\gaming-monitor.csv
#>

param(
    [int]$IntervalSeconds = 2,
    [int]$DurationSeconds = 300,
    [string]$Output = '.\\gaming-monitor.csv'
)]

function Get-GpuInfoNvidia {
    $cmd = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if (-not $cmd) { return $null }
    try {
        $out = & nvidia-smi --query-gpu=index,name,utilization.gpu,temperature.gpu,memory.used --format=csv,noheader,nounits 2>$null
        return $out -join ' | '
    } catch { return $null }
}

function Get-SafeTopProcesses {
    param([int]$Top = 5)

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
            ProcessName = $_.ProcessName
            Id          = $_.Id
            CPUSeconds  = $cpuSeconds
            PMMB        = [math]::Round($_.PM / 1MB, 2)
        }
    } |
    Sort-Object @{ Expression = { if ($null -ne $_.CPUSeconds) { [double]$_.CPUSeconds } else { -1 } } } -Descending |
    Select-Object -First $Top)
}

function Sample-Once {
    $ts = Get-Date -Format o
    $cpu = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
    $availMem = (Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue
    $top = Get-SafeTopProcesses -Top 5

    $topStr = ($top | ForEach-Object { "{0}(#{1}):CPU={2}:PM={3}" -f $_.ProcessName, $_.Id, $_.CPUSeconds, $_.PMMB }) -join ';'
    $gpu = Get-GpuInfoNvidia

    return "$ts,$([math]::Round($cpu,2)),$([math]::Round($availMem,2)),""$topStr"",""$gpu"""
}

Write-Host "Starting monitor: interval=${IntervalSeconds}s, duration=${DurationSeconds}s, output=$Output"

"Timestamp,CPU_percent,AvailMB,TopProcesses,GPUSnapshot" | Out-File -FilePath $Output -Encoding utf8

$end = (Get-Date).AddSeconds($DurationSeconds)
while ((Get-Date) -lt $end) {
    $line = Sample-Once
    $line | Out-File -FilePath $Output -Append -Encoding utf8
    Start-Sleep -Seconds $IntervalSeconds
}

Write-Host "Monitoring complete. Log saved to: $Output"
