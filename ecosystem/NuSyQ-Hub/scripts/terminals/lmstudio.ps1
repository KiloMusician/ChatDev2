# LM Studio Terminal - Local LLM Monitor
# Shows: Running models + API status + recent generations + server info

param(
    [switch]$Watch,
    [int]$IntervalSeconds = 7,
    [switch]$NoClear,
    [int]$ApiTimeoutSec = 2,
    [switch]$ProbeAllUrls
)

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot
$logFile = Join-Path $RepoRoot "data\terminal_logs\lmstudio.log"
# Try both localhost and known network address
$apiUrls = @("http://localhost:1234", "http://10.0.0.172:1234")
$runMode = if ($Watch) { "WATCH" } else { "ONE-SHOT" }
$lastSuccessfulUrl = $null

do {
    if (-not $NoClear) {
        Clear-Host
    }
    Write-Host "=== LM STUDIO (Local LLM GUI Platform) ===" -ForegroundColor Blue
    Write-Host "Run Mode: $runMode | Timeout: ${ApiTimeoutSec}s | Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkGray
    Write-Host "Script: $PSCommandPath" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "--- API Status -----------------------------------------------" -ForegroundColor Yellow
    $connected = $false
    $activeUrl = $null
    $models = @()
    $probeResults = @()

    $probeOrder = if ($lastSuccessfulUrl -and ($apiUrls -contains $lastSuccessfulUrl)) {
        @($lastSuccessfulUrl) + @($apiUrls | Where-Object { $_ -ne $lastSuccessfulUrl })
    } else {
        @($apiUrls)
    }

    foreach ($url in $probeOrder) {
        $probe = [ordered]@{
            url = $url
            ok = $false
            status_code = $null
            latency_ms = $null
            model_count = 0
            error = $null
        }
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $response = Invoke-WebRequest -Uri "$url/v1/models" -Method GET -TimeoutSec $ApiTimeoutSec -UseBasicParsing -ErrorAction Stop
            $sw.Stop()
            $probe.ok = $true
            $probe.status_code = $response.StatusCode
            $probe.latency_ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 1)

            $parsed = $response.Content | ConvertFrom-Json
            $probe.model_count = @($parsed.data).Count
            $probeResults += [PSCustomObject]$probe

            if (-not $connected) {
                $models = @($parsed.data)
                Write-Host "  LM Studio API: ONLINE " -NoNewline -ForegroundColor Green
                Write-Host "$url" -ForegroundColor Cyan
                Write-Host "  Models Available: $($models.Count)" -ForegroundColor White
                Write-Host "  Response Time: $($probe.latency_ms) ms (HTTP $($probe.status_code))" -ForegroundColor DarkGray
                $connected = $true
                $activeUrl = $url
                $lastSuccessfulUrl = $url
            }

            if ($connected -and -not $ProbeAllUrls) {
                break
            }
        } catch {
            $sw.Stop()
            $probe.latency_ms = [math]::Round($sw.Elapsed.TotalMilliseconds, 1)
            $probe.error = $_.Exception.Message
            $probeResults += [PSCustomObject]$probe
            # Try next URL
        }
    }

    if (-not $connected) {
        Write-Host "  LM Studio API: OFFLINE" -ForegroundColor Red
        Write-Host "  Start LM Studio GUI and load a model" -ForegroundColor Yellow
        Write-Host "  Checked URLs: $($apiUrls -join ', ')" -ForegroundColor DarkGray
    }
    Write-Host ""

    Write-Host "--- Probe Details --------------------------------------------" -ForegroundColor Yellow
    foreach ($probe in $probeResults) {
        if ($probe.ok) {
            Write-Host "  [OK]   $($probe.url)/v1/models | HTTP $($probe.status_code) | $($probe.latency_ms) ms | models=$($probe.model_count)" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] $($probe.url)/v1/models | $($probe.latency_ms) ms | $($probe.error)" -ForegroundColor Red
        }
    }
    Write-Host ""

    if ($models.Count -gt 0) {
        Write-Host "--- Loaded Models --------------------------------------------" -ForegroundColor Yellow
        $models | Select-Object -First 5 | ForEach-Object {
            Write-Host "  - $($_.id)" -ForegroundColor White
            if ($_.owned_by) {
                Write-Host "    Owner: $($_.owned_by)" -ForegroundColor DarkGray
            }
        }
        if ($models.Count -gt 5) {
            Write-Host "  ... and $($models.Count - 5) more" -ForegroundColor DarkGray
        }
        Write-Host ""
    }

    Write-Host "--- Recent Activity ------------------------------------------" -ForegroundColor Yellow
    if (Test-Path $logFile) {
        Get-Content $logFile -Tail 8 -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "  $_" -ForegroundColor White
        }
    } else {
        Write-Host "  (no activity logged yet)" -ForegroundColor DarkGray
    }
    Write-Host ""

    Write-Host "--- Quick Reference ------------------------------------------" -ForegroundColor Yellow
    Write-Host "  OpenAI-compatible API @ " -NoNewline -ForegroundColor Gray
    if ($activeUrl) {
        Write-Host "$activeUrl/v1" -ForegroundColor Cyan
    } else {
        Write-Host "http://localhost:1234/v1" -ForegroundColor DarkGray
    }
    $baseForTest = if ($activeUrl) { $activeUrl } else { "http://localhost:1234" }
    Write-Host "  Test endpoint: " -NoNewline -ForegroundColor Gray
    Write-Host "python scripts/test_lmstudio.py --base $baseForTest" -ForegroundColor Cyan
        Write-Host "  Watch mode: " -NoNewline -ForegroundColor Gray
        Write-Host "powershell -File scripts/terminals/lmstudio.ps1 -Watch -IntervalSeconds 7" -ForegroundColor Cyan
        Write-Host "  Full probe mode: " -NoNewline -ForegroundColor Gray
        Write-Host "powershell -File scripts/terminals/lmstudio.ps1 -Watch -ProbeAllUrls" -ForegroundColor Cyan

    if (-not $connected) {
        Write-Host ""
        Write-Host "--- Troubleshooting ------------------------------------------" -ForegroundColor Yellow
        Write-Host "  1. In LM Studio, enable Local Server (OpenAI-compatible)." -ForegroundColor White
        Write-Host "  2. Ensure at least one model is loaded in memory." -ForegroundColor White
        Write-Host "  3. Verify host/port match one of: $($apiUrls -join ', ')." -ForegroundColor White
        Write-Host "  4. Check firewall/network permissions for port 1234." -ForegroundColor White
    }

    if ($Watch) {
        Write-Host ""
        Write-Host "Refreshing in $IntervalSeconds`s... (Ctrl+C to stop)" -ForegroundColor DarkGray
        Start-Sleep -Seconds $IntervalSeconds
    } else {
        Write-Host ""
        Write-Host "One-shot complete. Re-run with -Watch for continuous refresh." -ForegroundColor DarkGray
    }
} while ($Watch)
