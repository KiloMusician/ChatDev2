#!/usr/bin/env pwsh
param(
    [switch]$ForceInstall
)
Set-StrictMode -Version Latest

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " SIMULATEDVERSE AGENT LAUNCHER" -ForegroundColor Cyan
Write-Host " Safe launcher (non-mutating, minimal-first startup)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

function Resolve-PythonCmd {
    if ($env:PYTHON_EXE -and (Test-Path $env:PYTHON_EXE)) { return @($env:PYTHON_EXE) }
    if (Get-Command py -ErrorAction SilentlyContinue) { return @("py", "-3") }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @("python") }
    if (Get-Command python3 -ErrorAction SilentlyContinue) { return @("python3") }
    return @()
}

function Invoke-HealthProbe {
    param(
        [string]$BaseUrl,
        [int]$TimeoutSec = 2
    )
    $baseCandidates = @($BaseUrl)
    if ($BaseUrl -match "^(https?://[^:]+):(\d+)$") {
        $hostBase = $Matches[1]
        $currentPort = [int]$Matches[2]
        foreach ($port in @(5001, 5000, 5002)) {
            if ($port -ne $currentPort) {
                $baseCandidates += "$hostBase`:$port"
            }
        }
    }
    $pathCandidates = @("/api/health", "/health", "/healthz", "/readyz", "/status")
    foreach ($candidateBase in $baseCandidates | Select-Object -Unique) {
        foreach ($candidatePath in $pathCandidates) {
            $uri = "$candidateBase$candidatePath"
            try {
                Invoke-WebRequest -Uri $uri -TimeoutSec $TimeoutSec -ErrorAction Stop | Out-Null
                return $true
            } catch {
                $wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
                if ($wsl) {
                    try {
                        & $wsl.Source bash -lc "curl -fsS '$uri' >/dev/null"
                        if ($LASTEXITCODE -eq 0) {
                            return $true
                        }
                    } catch {
                        continue
                    }
                }
            }
        }
    }
    return $false
}

$SimulatedVersePath = $env:SIMULATEDVERSE_PATH
if (-not $SimulatedVersePath) {
    $SimulatedVersePath = Join-Path $env:USERPROFILE "Desktop\SimulatedVerse\SimulatedVerse"
}
$SimverseHost = $env:SIMULATEDVERSE_HOST
if (-not $SimverseHost) {
    $SimverseHost = "http://127.0.0.1"
}
$SimversePort = $env:SIMULATEDVERSE_PORT
if (-not $SimversePort) {
    $SimversePort = "5002"
}
$SimverseBase = "$SimverseHost`:$SimversePort"
$DaemonScript = $env:SIMULATEDVERSE_DAEMON_SCRIPT
if (-not $DaemonScript) {
    $DaemonScript = "/mnt/c/Users/keath/Dev-Mentor/scripts/simulatedverse_daemon.sh"
}

if (-not (Test-Path $SimulatedVersePath)) {
    Write-Error "SimulatedVerse path not found: $SimulatedVersePath"
    exit 1
}

if (Invoke-HealthProbe -BaseUrl $SimverseBase -TimeoutSec 2) {
    Write-Host "[OK] SimulatedVerse already running at $SimverseBase" -ForegroundColor Green
    exit 0
}

$minimalLauncher = Join-Path $PSScriptRoot "start_simulatedverse_minimal.py"
$pythonCmd = @(Resolve-PythonCmd)
if ((Test-Path $minimalLauncher) -and (@($pythonCmd).Count -gt 0)) {
    Write-Host "[INFO] Attempting Python minimal launcher..." -ForegroundColor Yellow
    $env:SIMULATEDVERSE_PATH = $SimulatedVersePath
    $env:SIMULATEDVERSE_PORT = $SimversePort
    $env:NUSYQ_SIMULATEDVERSE_DETACH = "1"
    $env:NUSYQ_SIMULATEDVERSE_START_PROFILE = "minimal"

    $exe = $pythonCmd[0]
    $prefixArgs = @()
    if (@($pythonCmd).Count -gt 1) {
        $prefixArgs = $pythonCmd[1..(@($pythonCmd).Count - 1)]
    }
    & $exe @prefixArgs $minimalLauncher
    if ($LASTEXITCODE -eq 0 -and (Invoke-HealthProbe -BaseUrl $SimverseBase -TimeoutSec 3)) {
        Write-Host "[OK] SimulatedVerse started via minimal launcher." -ForegroundColor Green
        exit 0
    }
}

$nodeModulesPath = Join-Path $SimulatedVersePath "node_modules"
if ($ForceInstall -or (-not (Test-Path $nodeModulesPath))) {
    Write-Host "[INFO] Installing SimulatedVerse dependencies..." -ForegroundColor Yellow
    Push-Location $SimulatedVersePath
    try {
        npm install --no-audit
        if ($LASTEXITCODE -ne 0) {
            Write-Error "npm install failed"
            exit 1
        }
    } finally {
        Pop-Location
    }
}

$startProfile = ("" + $env:NUSYQ_SIMULATEDVERSE_START_PROFILE).ToLowerInvariant()
$npmScript = if ($startProfile -in @("full", "always_on", "dev")) { "dev:full" } elseif ($startProfile -eq "degraded") { "dev:degraded" } else { "dev:fallback" }
$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if ($wsl -and (Test-Path $DaemonScript)) {
    Write-Host "[INFO] Starting SimulatedVerse via detached WSL daemon launcher..." -ForegroundColor Yellow
    $daemonCommand = "SIMVERSE_DIR='$SimulatedVersePath' SIMULATEDVERSE_PORT='$SimversePort' bash '$DaemonScript'"
    Start-Process -FilePath $wsl.Source `
        -ArgumentList "-e", "bash", "-lc", $daemonCommand `
        -WindowStyle Hidden
} else {
    Write-Host "[INFO] Fallback npm launch: npm run $npmScript" -ForegroundColor Yellow
    Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c", "set PORT=$SimversePort && set SIMULATEDVERSE_PORT=$SimversePort && npm run $npmScript" `
        -WorkingDirectory $SimulatedVersePath `
        -WindowStyle Normal
}

for ($i = 0; $i -lt 45; $i++) {
    Start-Sleep -Seconds 1
    if (Invoke-HealthProbe -BaseUrl $SimverseBase -TimeoutSec 2) {
        Write-Host ""
        Write-Host "[OK] SimulatedVerse operational at $SimverseBase" -ForegroundColor Green
        Write-Host "  Health: $SimverseBase/api/health" -ForegroundColor Gray
        Write-Host "  Agents: $SimverseBase/api/agents" -ForegroundColor Gray
        exit 0
    }
    if ($i % 5 -eq 0) {
        Write-Host ("   Waiting for startup... ({0}s)" -f $i) -ForegroundColor Gray
    }
}

Write-Warning "SimulatedVerse did not report healthy within timeout."
exit 1
