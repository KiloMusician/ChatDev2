#!/usr/bin/env pwsh
# NuSyQ Front-End Health Check
# Version: 1.0.0

param(
    [switch]$CI,
    [switch]$JSON,
    [switch]$Verbose
)

$SimulatedVersePort = 5000
$ChatDevPort = 8000
$ModularWindowPort = 8080

$results = @{
    timestamp = (Get-Date -Format "o")
    overall_status = "healthy"
    servers = @()
}

if (-not $JSON) {
    Write-Host ""
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host "  NuSyQ Front-End Health Monitor" -ForegroundColor Cyan
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Server {
    param(
        [string]$Name,
        [int]$Port,
        [string]$URL
    )

    $result = @{
        name = $Name
        port = $Port
        url = $URL
    }

    # Check port
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        $result.port_status = "listening"
        $result.process = $proc.ProcessName

        if (-not $JSON) {
            Write-Host "  OK Port listening ($($proc.ProcessName))" -ForegroundColor Green
        }
    } else {
        $result.port_status = "not_listening"
        if (-not $JSON) {
            Write-Host "  ERROR Port not listening" -ForegroundColor Red
        }
        $script:overallHealth = "unhealthy"
    }

    # Check HTTP
    try {
        $start = Get-Date
        $response = Invoke-WebRequest -Uri $URL -TimeoutSec 5 -UseBasicParsing
        $elapsed = (Get-Date) - $start

        $result.http_status = "healthy"
        $result.status_code = $response.StatusCode
        $result.response_time_ms = [int]$elapsed.TotalMilliseconds

        if (-not $JSON) {
            Write-Host "  OK HTTP $($response.StatusCode) ($($result.response_time_ms)ms)" -ForegroundColor Green
        }
    } catch {
        $result.http_status = "unreachable"
        $result.error = $_.Exception.Message

        if (-not $JSON) {
            Write-Host "  ERROR HTTP unreachable" -ForegroundColor Red
        }
        $script:overallHealth = "unhealthy"
    }

    return $result
}

$script:overallHealth = "healthy"

if (-not $JSON) {
    Write-Host "[1/3] SimulatedVerse (Port $SimulatedVersePort)" -ForegroundColor Yellow
}
$sv = Test-Server -Name "SimulatedVerse" -Port $SimulatedVersePort -URL "http://localhost:$SimulatedVersePort/api/health"
$results.servers += $sv

if (-not $JSON) {
    Write-Host ""
    Write-Host "[2/3] ChatDev Visualizers (Port $ChatDevPort)" -ForegroundColor Yellow
}
$cd = Test-Server -Name "ChatDev Visualizers" -Port $ChatDevPort -URL "http://localhost:$ChatDevPort/static/index.html"
$results.servers += $cd

if (-not $JSON) {
    Write-Host ""
    Write-Host "[3/3] Modular Window (Port $ModularWindowPort)" -ForegroundColor Yellow
}
$mw = Test-Server -Name "Modular Window" -Port $ModularWindowPort -URL "http://localhost:$ModularWindowPort"
$results.servers += $mw

$results.overall_status = $script:overallHealth

if ($JSON) {
    Write-Host ($results | ConvertTo-Json -Depth 10)
} else {
    Write-Host ""
    if ($script:overallHealth -eq "healthy") {
        Write-Host "=========================================================" -ForegroundColor Green
        Write-Host "  Overall Status: HEALTHY" -ForegroundColor Green
        Write-Host "=========================================================" -ForegroundColor Green
    } else {
        Write-Host "=========================================================" -ForegroundColor Red
        Write-Host "  Overall Status: UNHEALTHY" -ForegroundColor Red
        Write-Host "=========================================================" -ForegroundColor Red
    }
    Write-Host ""
}

if ($CI) {
    exit $(if ($script:overallHealth -eq "healthy") { 0 } else { 1 })
}
