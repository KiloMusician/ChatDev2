# SimulatedVerse Terminal - Consciousness Engine Monitor
# Shows: Dev server status + Temple knowledge + PU queue + consciousness logs

param(
    [switch]$Watch,
    [int]$IntervalSeconds = 5,
    [switch]$NoClear
)

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot
$logFile = Join-Path $RepoRoot "data\terminal_logs\simulatedverse.log"
$simverseCandidates = @()
if ($env:SIMULATEDVERSE_ROOT) {
    $simverseCandidates += $env:SIMULATEDVERSE_ROOT
}
$simverseCandidates += @(
    (Join-Path (Split-Path $RepoRoot -Parent) "SimulatedVerse\SimulatedVerse"),
    (Join-Path $env:USERPROFILE "Desktop\SimulatedVerse\SimulatedVerse")
)
$simversePath = $simverseCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $simversePath) {
    $simversePath = $simverseCandidates | Select-Object -First 1
}
$runMode = if ($Watch) { "WATCH" } else { "ONE-SHOT" }

do {
    if (-not $NoClear) { Clear-Host }
    Write-Host "=== SIMULATEDVERSE (Consciousness Engine) ===" -ForegroundColor Magenta
    Write-Host "Run Mode: $runMode" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "--- Server Status --------------------------------------------" -ForegroundColor Yellow
    # Check if dev server is running on ports 5000 (Express) or 3000 (React)
    $expressRunning = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue
    $reactRunning = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
    
    if ($expressRunning) {
        Write-Host "  Express Server: ONLINE " -NoNewline -ForegroundColor Green
        Write-Host "http://localhost:5000" -ForegroundColor Cyan
    } else {
        Write-Host "  Express Server: OFFLINE" -ForegroundColor Red
    }
    
    if ($reactRunning) {
        Write-Host "  React UI: ONLINE " -NoNewline -ForegroundColor Green
        Write-Host "http://localhost:3000" -ForegroundColor Cyan
    } else {
        Write-Host "  React UI: OFFLINE" -ForegroundColor Red
    }
    Write-Host ""

    Write-Host "--- Temple Knowledge Status ----------------------------------" -ForegroundColor Yellow
    if (Test-Path "$simversePath\temple_state.json") {
        $temple = Get-Content "$simversePath\temple_state.json" -Raw | ConvertFrom-Json
        Write-Host "  Current Floor: $($temple.current_floor)" -ForegroundColor White
        Write-Host "  Knowledge Level: $($temple.knowledge_level)" -ForegroundColor White
    } else {
        Write-Host "  (temple_state.json not found - run dev server)" -ForegroundColor DarkGray
    }
    Write-Host ""

    Write-Host "--- Recent Consciousness Events ------------------------------" -ForegroundColor Yellow
    if (Test-Path $logFile) {
        Get-Content $logFile -Tail 8 -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "  $_" -ForegroundColor White
        }
    } else {
        Write-Host "  (no consciousness events logged yet)" -ForegroundColor DarkGray
    }
    Write-Host ""

    Write-Host "--- Environment ---------------------------------------------" -ForegroundColor Yellow
    if ($simversePath -and (Test-Path (Join-Path $simversePath ".env"))) {
        $envLines = Get-Content (Join-Path $simversePath ".env") | Select-String -Pattern "DATABASE_URL|PU_RUN|CHATDEV" | ForEach-Object { $_.Line }
        $envLines | ForEach-Object {
            Write-Host "  $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "  SimulatedVerse path not found (set SIMULATEDVERSE_ROOT to override)" -ForegroundColor DarkGray
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
