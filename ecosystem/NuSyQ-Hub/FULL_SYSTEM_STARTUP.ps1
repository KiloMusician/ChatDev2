<#
.SYNOPSIS
🚀 Full NuSyQ-Hub System Startup Script

.DESCRIPTION
Comprehensive system activation script that:
1. Activates Python environment
2. Loads .env configuration
3. Verifies all dependencies
4. Starts Docker Desktop if needed
5. Deploys full-stack AI orchestration
6. Validates all services
7. Displays system status

.NOTES
Run with: .\FULL_SYSTEM_STARTUP.ps1
#>

[CmdletBinding()]
param(
    [switch]$SkipDocker,
    [switch]$QuickStart,
    [string]$Mode = "full"  # full, minimal, dev
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Color output functions
function Write-Status { param($Message) Write-Host "🔍 $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️ $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Header { param($Message) Write-Host "`n$('=' * 80)`n$Message`n$('=' * 80)" -ForegroundColor Magenta }

# Project root
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

Write-Header "🚀 NUSYQ-HUB FULL SYSTEM STARTUP"

# =============================================================================
# STEP 1: ACTIVATE PYTHON ENVIRONMENT
# =============================================================================
Write-Status "Activating Python virtual environment..."
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"

if (Test-Path $VenvActivate) {
    & $VenvActivate
    Write-Success "Python environment activated"
} else {
    Write-Warning "Virtual environment not found - creating..."
    python -m venv .venv
    & $VenvActivate
    Write-Status "Installing dependencies..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Write-Success "Environment created and dependencies installed"
}

# =============================================================================
# STEP 2: VERIFY .ENV CONFIGURATION
# =============================================================================
Write-Status "Verifying .env configuration..."
$EnvFile = Join-Path $ProjectRoot ".env"

if (-not (Test-Path $EnvFile)) {
    Write-Error ".env file not found! Please create one from .env.example"
    exit 1
}

# Load and count env vars
$EnvVars = Get-Content $EnvFile | Where-Object { $_ -match '^\s*[A-Z]' -and $_ -notmatch '^\s*#' }
Write-Success "Loaded configuration: $($EnvVars.Count) environment variables"

# =============================================================================
# STEP 3: CHECK OLLAMA SERVICE
# =============================================================================
Write-Status "Checking Ollama service..."
try {
    $OllamaResponse = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5 -ErrorAction Stop
    $ModelCount = $OllamaResponse.models.Count
    Write-Success "Ollama running: $ModelCount models available"

    # Display models
    Write-Host "`n📚 Available Models:" -ForegroundColor Cyan
    $OllamaResponse.models | ForEach-Object {
        $sizeMB = [math]::Round($_.size / 1MB, 1)
        Write-Host "  - $($_.name) ($($_.details.parameter_size), ${sizeMB}MB)" -ForegroundColor Gray
    }
} catch {
    Write-Warning "Ollama not responding on port 11434"
    Write-Status "Attempting to start Ollama service..."

    # Try to start Ollama
    try {
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 5
        $OllamaResponse = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5
        Write-Success "Ollama service started successfully"
    } catch {
        Write-Warning "Could not auto-start Ollama - please start manually"
    }
}

# =============================================================================
# STEP 4: RUN PYTHON SYSTEM ACTIVATION
# =============================================================================
Write-Status "Running Python system activation..."
try {
    $ActivationOutput = python ACTIVATE_SYSTEM.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "System activation completed successfully"
        # Display key lines from output
        $ActivationOutput | Select-String -Pattern "(✅|⚠️|📊|🎯)" | ForEach-Object {
            Write-Host "  $_" -ForegroundColor Gray
        }
    } else {
        Write-Error "System activation failed with code $LASTEXITCODE"
        $ActivationOutput
        exit $LASTEXITCODE
    }
} catch {
    Write-Error "Failed to run activation: $_"
    exit 1
}

# =============================================================================
# STEP 5: DOCKER DEPLOYMENT (Optional)
# =============================================================================
if (-not $SkipDocker) {
    Write-Status "Checking Docker availability..."

    try {
        $DockerVersion = docker version --format '{{.Server.Version}}' 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Docker Desktop running (v$DockerVersion)"

            if (-not $QuickStart) {
                Write-Status "Would you like to deploy the full-stack AI orchestration? (Y/N)"
                $Deploy = Read-Host

                if ($Deploy -eq 'Y' -or $Deploy -eq 'y') {
                    Write-Status "Deploying full-stack services..."
                    Write-Host "`n📦 Services to deploy:" -ForegroundColor Cyan
                    docker-compose -f deploy/docker-compose.full-stack.yml config --services | ForEach-Object {
                        Write-Host "  - $_" -ForegroundColor Gray
                    }

                    Write-Status "`nStarting deployment..."
                    docker-compose -f deploy/docker-compose.full-stack.yml up -d --build

                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "Full-stack deployment initiated"
                        Write-Status "Waiting for services to stabilize..."
                        Start-Sleep -Seconds 10

                        # Show service status
                        Write-Host "`n📊 Service Status:" -ForegroundColor Cyan
                        docker-compose -f deploy/docker-compose.full-stack.yml ps
                    } else {
                        Write-Warning "Deployment encountered issues - check logs with:"
                        Write-Host "  docker-compose -f deploy/docker-compose.full-stack.yml logs" -ForegroundColor Yellow
                    }
                } else {
                    Write-Status "Skipping Docker deployment"
                }
            }
        }
    } catch {
        Write-Warning "Docker Desktop not running"
        Write-Status "To enable full-stack deployment:"
        Write-Host "  1. Start Docker Desktop" -ForegroundColor Yellow
        Write-Host "  2. Re-run this script" -ForegroundColor Yellow
    }
} else {
    Write-Status "Docker deployment skipped (--SkipDocker flag)"
}

# =============================================================================
# STEP 6: SYSTEM STATUS SUMMARY
# =============================================================================
Write-Header "📊 SYSTEM STATUS SUMMARY"

# Check each component
$Status = @{
    "Python Environment" = Test-Path $VenvActivate
    ".env Configuration" = Test-Path $EnvFile
    "Ollama Service" = try { Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop | Out-Null; $true } catch { $false }
    "Quest System" = Test-Path "src/Rosetta_Quest_System/quest_engine.py"
    "AI Orchestrator" = Test-Path "src/orchestration/unified_ai_orchestrator.py"
    "Intelligent Timeouts" = Test-Path "src/utils/intelligent_timeout_manager.py"
    "Docker Available" = try { docker version 2>&1 | Out-Null; $LASTEXITCODE -eq 0 } catch { $false }
}

foreach ($Component in $Status.GetEnumerator() | Sort-Object Name) {
    $Icon = if ($Component.Value) { "✅" } else { "❌" }
    $Color = if ($Component.Value) { "Green" } else { "Red" }
    Write-Host "$Icon $($Component.Key)" -ForegroundColor $Color
}

# =============================================================================
# STEP 7: NEXT STEPS
# =============================================================================
Write-Header "🎯 NEXT STEPS"

Write-Host @"

📚 Documentation:
  - AI Agent Instructions: docs\AI_AGENT_INSTRUCTIONS.md
  - System Manifest: docs\SYSTEM_MANIFEST.json
  - Operations Runbook: docs\OPERATIONS_RUNBOOK.md

🚀 Quick Commands:
  - Quest System:      python -m src.Rosetta_Quest_System.quest_engine
  - Run Orchestrator:  python -m src.orchestration.unified_ai_orchestrator
  - ChatDev Project:   python -m src.orchestration.chatdev_development_orchestrator
  - System Health:     python src/diagnostics/system_health_assessor.py

🐳 Docker Management:
  - View logs:         docker-compose -f deploy/docker-compose.full-stack.yml logs -f
  - Stop services:     docker-compose -f deploy/docker-compose.full-stack.yml down
  - Service status:    docker-compose -f deploy/docker-compose.full-stack.yml ps

🔧 Development:
  - Run tests:         pytest -v
  - Check coverage:    pytest --cov=src --cov-report=term-missing
  - Lint code:         python scripts/lint_test_check.py

"@ -ForegroundColor Cyan

Write-Header "✨ SYSTEM READY FOR AI AGENT OPERATIONS"

# Return status code
$ReadyCount = ($Status.Values | Where-Object { $_ }).Count
$TotalCount = $Status.Count
$ReadyPercent = [math]::Round(($ReadyCount / $TotalCount) * 100)

Write-Host "`n🎯 System Readiness: $ReadyPercent% ($ReadyCount/$TotalCount components ready)" -ForegroundColor $(if ($ReadyPercent -ge 80) { "Green" } else { "Yellow" })

if ($ReadyPercent -lt 80) {
    Write-Warning "Some components need attention - review status above"
    exit 1
}

exit 0
