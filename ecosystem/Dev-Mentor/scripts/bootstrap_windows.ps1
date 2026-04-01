# =============================================================================
#  bootstrap_windows.ps1 — Bootstrap for Windows PowerShell / pwsh
#  Detects surface, shows ecosystem status, gives quickstart instructions.
# =============================================================================
param(
    [switch]$AutoStart,
    [int]$Port = 5000
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

# ─── Banner ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   TERMINAL DEPTHS · DEVMENTOR ECOSYSTEM                  ║" -ForegroundColor Cyan
Write-Host "║   Offline-First · AI-Optional · Self-Aware              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─── Surface detection ────────────────────────────────────────────────────────
$Surface = "windows"
if ($env:REPL_ID -or $env:REPLIT_DEV_DOMAIN) { $Surface = "replit" }
elseif (Test-Path "/.dockerenv")              { $Surface = "docker" }
elseif ($env:TERM_PROGRAM -eq "vscode")       { $Surface = "vscode" }
elseif ($env:CODESPACES)                      { $Surface = "codespaces" }

$PythonVer = (python --version 2>&1) -replace "Python ", ""
Write-Host "  Surface  : $($Surface.ToUpper())" -ForegroundColor White
Write-Host "  Python   : $PythonVer" -ForegroundColor Gray
Write-Host "  Host     : $env:COMPUTERNAME" -ForegroundColor Gray
Write-Host ""

# ─── Python check ─────────────────────────────────────────────────────────────
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "  ERROR: python not found. Install Python 3.10+ from python.org" -ForegroundColor Red
    Write-Host "  Or use WSL: wsl --install" -ForegroundColor Yellow
    exit 1
}

# ─── Sibling repo scan ────────────────────────────────────────────────────────
Write-Host "  Sibling Repositories:" -ForegroundColor Cyan
$Parent = Split-Path -Parent $Root
foreach ($Repo in @("NuSyQ-Hub", "SimulatedVerse", "CyberTerminal", "NuSyQ")) {
    $RepoPath = Join-Path $Parent $Repo
    if (Test-Path $RepoPath) {
        Write-Host "    [OK] $Repo" -ForegroundColor Green
    } else {
        Write-Host "    [ ] $Repo (not found)" -ForegroundColor Gray
    }
}
Write-Host ""

# ─── Port status ─────────────────────────────────────────────────────────────
Write-Host "  Service Status:" -ForegroundColor Cyan
$PortMapPath = Join-Path $Root "config\port_map.json"
if (Test-Path $PortMapPath) {
    $PortMap = Get-Content $PortMapPath | ConvertFrom-Json
    $Ports = $PortMap.ports.PSObject.Properties
    foreach ($P in $Ports) {
        $Info = $P.Value
        $LocalPort = $Info.local_port
        $Name = $Info.name
        $Alive = $false
        try {
            $Tcp = New-Object System.Net.Sockets.TcpClient
            $Task = $Tcp.ConnectAsync("localhost", $LocalPort)
            $Task.Wait(800) | Out-Null
            $Alive = $Tcp.Connected
            $Tcp.Close()
        } catch {}
        $Icon  = if ($Alive) { "[OK]" } else { "[--]" }
        $Color = if ($Alive) { "Green" } else { "Gray" }
        Write-Host "    $Icon :$LocalPort  $Name" -ForegroundColor $Color
    }
} else {
    Write-Host "    (config/port_map.json not found)" -ForegroundColor Gray
}
Write-Host ""

# ─── WSL recommendation ───────────────────────────────────────────────────────
Write-Host "  WINDOWS QUICKSTART:" -ForegroundColor Cyan
Write-Host "    • For full Linux compatibility: WSL2 is recommended" -ForegroundColor White
Write-Host "      wsl --install" -ForegroundColor Yellow
Write-Host "    • Start server (PowerShell):" -ForegroundColor White
Write-Host "      python -m cli.devmentor serve --host 0.0.0.0 --port $Port" -ForegroundColor Yellow
Write-Host "    • CLI client:" -ForegroundColor White
Write-Host "      python scripts/td.py" -ForegroundColor Yellow
Write-Host "    • Port watcher:" -ForegroundColor White
Write-Host "      python scripts/port_watcher.py --fix" -ForegroundColor Yellow
Write-Host ""

# ─── Surface-specific tips ────────────────────────────────────────────────────
if ($Surface -eq "vscode") {
    Write-Host "  VS CODE DETECTED:" -ForegroundColor Cyan
    Write-Host "    • Ctrl+Shift+B — DevMentor task panel" -ForegroundColor White
    Write-Host "    • Open: DevMentorWorkspace.workspace.json" -ForegroundColor White
}

# ─── Auto-start option ────────────────────────────────────────────────────────
if ($AutoStart) {
    $TcpTest = $false
    try {
        $Tcp = New-Object System.Net.Sockets.TcpClient
        $Task = $Tcp.ConnectAsync("localhost", $Port)
        $Task.Wait(500) | Out-Null
        $TcpTest = $Tcp.Connected
        $Tcp.Close()
    } catch {}

    if (-not $TcpTest) {
        Write-Host "  Starting game server on :$Port ..." -ForegroundColor Yellow
        Start-Process python -ArgumentList "-m", "cli.devmentor", "serve", "--host", "0.0.0.0", "--port", "$Port" -WindowStyle Hidden
        Start-Sleep 3
        Write-Host "  Server launched. Check http://localhost:$Port/api/health" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Game server already running on :$Port" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "  Environment report: python core/environment.py" -ForegroundColor DarkGray
Write-Host "  Activation plan:    python core/environment.py --plan" -ForegroundColor DarkGray
Write-Host "  In-game commands:   context  plan  surface" -ForegroundColor DarkGray
Write-Host ""
