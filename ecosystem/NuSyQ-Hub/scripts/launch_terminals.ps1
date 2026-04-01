# Terminal Launcher - NuSyQ Multi-Console Cockpit
# Opens all operational monitoring terminals

param(
    [switch]$All,
    [switch]$Core,
    [switch]$AI,
    [switch]$Quality
)

$RepoRoot = Split-Path $PSScriptRoot -Parent
$pwshCmd = Get-Command pwsh -ErrorAction SilentlyContinue
$powershellCmd = Get-Command powershell -ErrorAction SilentlyContinue
$ShellPath = if ($pwshCmd) { $pwshCmd.Path } elseif ($powershellCmd) { $powershellCmd.Path } else { $null }

if (-not $ShellPath) {
    Write-Host "No PowerShell executable found (pwsh or powershell)." -ForegroundColor Red
    exit 1
}

Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          🚀 NuSyQ Terminal Cockpit Launcher                       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repo Root: $RepoRoot" -ForegroundColor DarkGray
Write-Host "Shell: $ShellPath" -ForegroundColor DarkGray
Write-Host ""

# Ensure directories exist
$logsDir = Join-Path $RepoRoot "state\logs"
if (-not (Test-Path $logsDir)) {
    Write-Host "Creating $logsDir..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
}

# Define terminal groups
$coreTerminals = @(
    @{Name="Main"; Path="scripts/terminals/main.ps1"; Icon="🏠"},
    @{Name="Errors"; Path="scripts/terminals/errors.ps1"; Icon="🔥"},
    @{Name="Metrics"; Path="scripts/terminals/metrics.ps1"; Icon="📊"}
)

$aiTerminals = @(
    @{Name="Agents"; Path="scripts/terminals/agents.ps1"; Icon="🤖"},
    @{Name="Council"; Path="scripts/terminals/council.ps1"; Icon="🏛️"},
    @{Name="ChatDev"; Path="scripts/terminals/chatdev.ps1"; Icon="🏗️"},
    @{Name="Culture Ship"; Path="scripts/terminals/culture_ship.ps1"; Icon="🛸"},
    @{Name="Moderator"; Path="scripts/terminals/moderator.ps1"; Icon="🔗"}
)

$qualityTerminals = @(
    @{Name="Tests"; Path="scripts/terminals/tests.ps1"; Icon="🧪"},
    @{Name="Suggestions"; Path="scripts/terminals/suggestions.ps1"; Icon="💡"},
    @{Name="Anomalies"; Path="scripts/terminals/anomalies.ps1"; Icon="⚡"}
)

# Function to launch a terminal
function Launch-Terminal {
    param($Terminal)

    $terminalPath = Join-Path $RepoRoot $Terminal.Path

    if (Test-Path $terminalPath) {
        Write-Host "Launching $($Terminal.Icon) $($Terminal.Name)..." -ForegroundColor Green
        Start-Process $ShellPath -ArgumentList "-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $terminalPath
        Start-Sleep -Milliseconds 300  # Stagger launches
    } else {
        Write-Host "Missing: $terminalPath" -ForegroundColor Red
    }
}

# Determine which terminals to launch
if ($All) {
    Write-Host "Launching ALL terminals..." -ForegroundColor Cyan
    Write-Host ""

    Write-Host "Core Terminals:" -ForegroundColor Yellow
    $coreTerminals | ForEach-Object { Launch-Terminal $_ }

    Write-Host ""
    Write-Host "AI System Terminals:" -ForegroundColor Yellow
    $aiTerminals | ForEach-Object { Launch-Terminal $_ }

    Write-Host ""
    Write-Host "Quality Terminals:" -ForegroundColor Yellow
    $qualityTerminals | ForEach-Object { Launch-Terminal $_ }

} elseif ($Core) {
    Write-Host "Launching CORE terminals..." -ForegroundColor Cyan
    $coreTerminals | ForEach-Object { Launch-Terminal $_ }

} elseif ($AI) {
    Write-Host "Launching AI SYSTEM terminals..." -ForegroundColor Cyan
    $aiTerminals | ForEach-Object { Launch-Terminal $_ }

} elseif ($Quality) {
    Write-Host "Launching QUALITY terminals..." -ForegroundColor Cyan
    $qualityTerminals | ForEach-Object { Launch-Terminal $_ }

} else {
    # Default: launch minimal set
    Write-Host "Launching DEFAULT terminals (Main, Errors, Agents, ChatDev)..." -ForegroundColor Cyan
    Write-Host ""

    @($coreTerminals[0], $coreTerminals[1], $aiTerminals[0], $aiTerminals[2]) | ForEach-Object {
        Launch-Terminal $_
    }

    Write-Host ""
    Write-Host "Use flags to launch more:" -ForegroundColor Yellow
    Write-Host "  -Core     : Main + Errors + Metrics" -ForegroundColor Gray
    Write-Host "  -AI       : All AI system terminals" -ForegroundColor Gray
    Write-Host "  -Quality  : Tests + Suggestions + Anomalies" -ForegroundColor Gray
    Write-Host "  -All      : Launch everything" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ Terminal cockpit launched!" -ForegroundColor Green
Write-Host ""
Write-Host "To stop all terminals: Get-Process pwsh | Where-Object {`$_.MainWindowTitle -match 'Terminal'} | Stop-Process" -ForegroundColor DarkGray
