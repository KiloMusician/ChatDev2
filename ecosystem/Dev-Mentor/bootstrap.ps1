<#
    .SYNOPSIS
    Terminal Depths + Dev-Mentor + SimulatedVerse Bootstrap

    .DESCRIPTION
    Comprehensive startup orchestrator for the local multi-repo agent workspace.
    Handles:
      - Environment validation (Docker, Python, Node)
      - Workspace initialization
      - Docker Compose orchestration (optional — use -SkipDocker for normal dev)
      - CLI client launch
      - LM Studio / Ollama integration

    NOTE: Does NOT require administrator privileges. Docker operations warn
    gracefully if unavailable. Use -SkipDocker for standard VS Code startup.

    .PARAMETER Mode
    'full' = everything (default) | 'dev' = dev services only | 'cli' = CLI client only | 'stop' = shutdown

    .PARAMETER Profile
    'lite' | 'balanced' | 'architect' | 'vision' (default: 'balanced')

    .PARAMETER SkipDocker
    Skip Docker services, use local servers only (recommended for daily dev)

    .EXAMPLE
    .\bootstrap.ps1 -Mode full -Profile balanced -SkipDocker
    .\bootstrap.ps1 -Mode cli -SkipDocker
    .\bootstrap.ps1 -Mode stop
#>

param(
    [ValidateSet('full', 'dev', 'cli', 'stop')]
    [string]$Mode = 'full',
    
    [ValidateSet('lite', 'balanced', 'architect', 'vision')]
    [string]$Profile = 'balanced',
    
    [switch]$SkipDocker,
    [switch]$NoWait
)

$ErrorActionPreference = 'Continue'
$WarningPreference = 'SilentlyContinue'

# Colors
$c_title = [System.ConsoleColor]::Cyan
$c_ok = [System.ConsoleColor]::Green
$c_warn = [System.ConsoleColor]::Yellow
$c_err = [System.ConsoleColor]::Red
$c_info = [System.ConsoleColor]::Blue

function Write-Title { Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $c_title; Write-Host $args[0] -ForegroundColor $c_title; Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $c_title }
function Write-OK { Write-Host "✓" -ForegroundColor $c_ok -NoNewline; Write-Host " $($args[0])" }
function Write-Warn { Write-Host "⚠" -ForegroundColor $c_warn -NoNewline; Write-Host " $($args[0])" }
function Write-Err { Write-Host "✗" -ForegroundColor $c_err -NoNewline; Write-Host " $($args[0])" }
function Write-Info { Write-Host "ℹ" -ForegroundColor $c_info -NoNewline; Write-Host " $($args[0])" }

# ============================================================
# Utility Functions
# ============================================================

function Test-Command {
    param([string]$Command)
    try { Get-Command $Command -ErrorAction Stop | Out-Null; return $true } catch { return $false }
}

function Test-Port {
    param([int]$Port)
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", $Port)
        $tcp.Close()
        return $true
    } catch { return $false }
}

function Get-DockerStatus {
    try {
        docker info | Out-Null
        return $true
    } catch { return $false }
}

# ============================================================
# Bootstrap Sequence
# ============================================================

Write-Title "Terminal Depths Bootstrap v2.1"

# 1. Environment Check
Write-Host ""
Write-Info "Stage 1: Environment Validation"

$env_ok = $true

if (Test-Command 'docker') {
    if (Get-DockerStatus) {
        Write-OK "Docker: running"
    } else {
        Write-Err "Docker: not running (start Docker Desktop)"
        $env_ok = $false
    }
} else {
    if ($SkipDocker) {
        Write-Warn "Docker: not installed (continuing with -SkipDocker)"
    } else {
        Write-Err "Docker: not installed or not in PATH"
        $env_ok = $false
    }
}

if (Test-Command 'python') {
    $py_ver = python --version 2>&1
    Write-OK "Python: $py_ver"
} else {
    Write-Err "Python: not found"
    $env_ok = $false
}

if (Test-Command 'node') {
    $node_ver = node --version
    Write-OK "Node.js: $node_ver"
} else {
    Write-Warn "Node.js: not found (SimulatedVerse may not run)"
}

if (-not $env_ok) {
    Write-Host ""
    Write-Err "Environment validation failed. Fix issues and try again."
    exit 1
}

# 2. Set up Environment Variables
Write-Host ""
Write-Info "Stage 2: Environment Configuration"

$env:TERMINAL_DEPTHS_PROFILE = $Profile
$env:TD_ENDPOINT = "http://127.0.0.1:11434/api/generate"
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONDONTWRITEBYTECODE = "1"

Write-OK "Profile: $Profile"
Write-OK "TD_ENDPOINT: $env:TD_ENDPOINT"

# 3. Docker Compose Operations
if (-not $SkipDocker -and $Mode -in @('full', 'dev')) {
    Write-Host ""
    Write-Info "Stage 3: Docker Compose Services"
    
    $compose_file = Join-Path $PSScriptRoot "docker-compose.yml"
    if (-not (Test-Path $compose_file)) {
        Write-Err "docker-compose.yml not found at $compose_file"
        exit 1
    }
    
    Write-Info "Starting services (this may take 1-2 minutes)..."
    
    docker compose -f $compose_file up -d 2>&1 | Select-String -Pattern "Starting|Created|running"
    
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Docker services: starting"
    } else {
        Write-Err "Docker Compose failed. Check docker-compose.yml and logs."
        exit 1
    }
    
    # Wait for services
    if (-not $NoWait) {
        Write-Info "Waiting for service health checks..."
        $timeout = 60
        $start = [datetime]::Now
        
        while (([datetime]::Now - $start).TotalSeconds -lt $timeout) {
            $ollama_ok = Test-Port 11434
            $dev_mentor_ok = Test-Port 7337
            
            if ($ollama_ok -and $dev_mentor_ok) {
                Write-OK "All services healthy"
                break
            }
            
            if (-not $ollama_ok) { Write-Warn "Waiting for Ollama..." }
            if (-not $dev_mentor_ok) { Write-Warn "Waiting for Dev-Mentor..." }
            
            Start-Sleep -Seconds 3
        }
        
        if (-not (Test-Port 7337)) {
            Write-Warn "Services may not be fully ready; continuing anyway"
        }
    }
}

# 4. Local LM Studio Check (optional fallback)
if ($env:LM_STUDIO_PORT) {
    if (Test-Port $env:LM_STUDIO_PORT) {
        Write-OK "LM Studio: reachable on :$env:LM_STUDIO_PORT"
        $env:TD_ENDPOINT = "http://127.0.0.1:$env:LM_STUDIO_PORT/v1/chat/completions"
    }
}

# 5. Python environment setup
Write-Host ""
Write-Info "Stage 4: Python Environment"

$dev_mentor_path = Join-Path $PSScriptRoot ""
if (-not (Test-Path "$dev_mentor_path\.venv")) {
    Write-Info "Creating Python virtual environment..."
    python -m venv "$dev_mentor_path\.venv" 2>&1 | Out-Null
    Write-OK "Virtual environment: created"
} else {
    Write-OK "Virtual environment: exists"
}

# Activate venv and install deps
& "$dev_mentor_path\.venv\Scripts\Activate.ps1"
Write-OK "Virtual environment: activated"

if (Test-Path "$dev_mentor_path\pyproject.toml") {
    Write-Info "Installing Python dependencies (if needed)..."
    pip install -q -e . 2>&1 | Out-Null
    Write-OK "Python dependencies: ready"
}

# 6. Handle Modes
Write-Host ""

switch ($Mode) {
    'full' {
        Write-Info "Mode: FULL (services + CLI client)"
        
        if ($SkipDocker) {
            Write-Warn "Skipping Docker services; using local/external servers only"
        }
        
        Write-OK "Workspace ready. Services running on:"
        Write-Host "  🎮 Terminal Depths CLI:   cd $dev_mentor_path && python -m cli.devmentor play"
        Write-Host "  🌍 SimulatedVerse UI:     http://localhost:5000"
        Write-Host "  📡 Dev-Mentor API:        http://localhost:7337/docs"
        Write-Host "  🧠 Ollama:                http://localhost:11434"
        Write-Host ""
        Write-Host "Launch CLI in new terminal (the workspace handles hot-reload)."
    }
    
    'dev' {
        Write-Info "Mode: DEV (services only, no client)"
        Write-OK "Services are running. Attach clients as needed."
    }
    
    'cli' {
        Write-Info "Mode: CLI (client only)"
        
        # Ensure backend is reachable
        if (-not (Test-Port 7337)) {
            Write-Err "Dev-Mentor backend not reachable on :7337"
            Write-Info "Run 'bootstrap.ps1 -Mode dev' first, or check docker-compose logs"
            exit 1
        }
        
        Write-OK "Launching Terminal Depths CLI..."
        Write-Host ""
        
        cd $dev_mentor_path
        python -m cli.devmentor play
    }
    
    'stop' {
        Write-Info "Mode: STOP (shutting down)"
        
        if (-not $SkipDocker) {
            $compose_file = Join-Path $PSScriptRoot "docker-compose.yml"
            docker compose -f $compose_file down 2>&1 | Select-String -Pattern "Stopping|Removed"
            Write-OK "Docker services: stopped"
        }
        
        Write-OK "Shutdown complete."
    }
}

Write-Host ""
Write-OK "Bootstrap complete."
Write-Host ""
