#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Agent-invokable system startup and health check for NuSyQ multi-AI ecosystem.

.DESCRIPTION
    Checks status of all AI systems (Ollama, ChatDev, MCP Server, Consciousness Bridge)
    and provides actionable health dashboard. Designed to be invoked by Copilot/Claude
    agents on behalf of the user, NOT run manually.

.EXAMPLE
    .\scripts\start_system.ps1
#>

param(
    [switch]$Verbose,
    [switch]$QuietMode  # Suppress interactive prompts for agent invocation
)

$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path $PSScriptRoot -Parent

# Emit terminal routing hint (routes output to 📊 Metrics terminal)
Write-Host "[ROUTE METRICS] 📊" -ForegroundColor DarkGray

Write-Host "`n🧠 NuSyQ System Health Check" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

# ============================================================================
# 1. DOCKER DAEMON CHECK
# ============================================================================
Write-Host "`n[1/8] Docker Daemon..." -NoNewline
$DockerOK = $false
try {
    $dockerVersion = docker --version 2>&1
    if ($dockerVersion -match "Docker version") {
        # Check if daemon is accessible
        $dockerPS = docker ps 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host " [OK] Running" -ForegroundColor Green
            $DockerOK = $true
        } else {
            Write-Host " [!]  Installed but daemon not running" -ForegroundColor Yellow
            Write-Host "   => Start Docker Desktop" -ForegroundColor DarkGray
        }
    }
} catch {
    Write-Host " [X] Not installed" -ForegroundColor Red
    Write-Host "   => Install from https://docker.com/products/docker-desktop" -ForegroundColor DarkGray
}

# ============================================================================
# 2. PYTHON ENVIRONMENT CHECK
# ============================================================================
Write-Host "[2/8] Python Environment..." -NoNewline
$PythonOK = $false
try {
    $venvActivate = Join-Path $RepoRoot ".venv\Scripts\Activate.ps1"
    if (Test-Path $venvActivate) {
        & $venvActivate
        $PythonVersion = python --version 2>&1
        if ($PythonVersion -match 'Python 3\.(1[2-9]|[2-9][0-9])') {
            Write-Host " [OK] $PythonVersion" -ForegroundColor Green
            $PythonOK = $true
        } else {
            Write-Host " [!] $PythonVersion - need 3.12+" -ForegroundColor Yellow
        }
    } else {
        Write-Host " [X] .venv not found" -ForegroundColor Red
        Write-Host "   => Run: python -m venv .venv ; .venv\Scripts\pip install -e ." -ForegroundColor DarkGray
    }
} catch {
    Write-Host " [X] Python check failed" -ForegroundColor Red
}

# ============================================================================
# 3. OLLAMA LOCAL LLM CHECK (from NuSyQ repo)
# ============================================================================
Write-Host "[3/8] Ollama (Local LLM)..." -NoNewline
$OllamaOK = $false
$OllamaModels = @()
try {
    # Try HTTP first (faster)
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        if ($data.models) {
            $OllamaOK = $true
            $OllamaModels = $data.models.name
            Write-Host " [OK] $($OllamaModels.Count) models loaded" -ForegroundColor Green
            if ($Verbose) {
                $OllamaModels | ForEach-Object { Write-Host "   - $_" -ForegroundColor DarkGray }
            }
        } else {
            Write-Host " [!]  Running but no models" -ForegroundColor Yellow
            $OllamaOK = $true  # Still consider it OK if service is running
        }
    }
} catch {
    Write-Host " [X] Not running (port 11434)" -ForegroundColor Red
    Write-Host "   => Launch: ollama serve (in separate terminal)" -ForegroundColor DarkGray
}

# ============================================================================
# 4. CHATDEV MULTI-AGENT SYSTEM CHECK
# ============================================================================
Write-Host "[4/8] ChatDev (Multi-Agent)..." -NoNewline
$ChatDevOK = $false
$ChatDevPath = $null

# Check environment variable first
if ($env:CHATDEV_PATH -and (Test-Path $env:CHATDEV_PATH)) {
    $ChatDevPath = $env:CHATDEV_PATH
}
# Check config/secrets.json
elseif (Test-Path "$RepoRoot\config\secrets.json") {
    try {
        $secrets = Get-Content "$RepoRoot\config\secrets.json" | ConvertFrom-Json
        if ($secrets.chatdev_path -and (Test-Path $secrets.chatdev_path)) {
            $ChatDevPath = $secrets.chatdev_path
        }
    } catch {}
}
# Fallback to sibling directory
elseif (Test-Path "C:\Users\keath\NuSyQ\ChatDev") {
    $ChatDevPath = "C:\Users\keath\NuSyQ\ChatDev"
}

if ($ChatDevPath) {
    $ChatDevOK = $true
    Write-Host " [OK] Found at $ChatDevPath" -ForegroundColor Green
} else {
    Write-Host " [X] Not found" -ForegroundColor Red
    Write-Host "   => Set CHATDEV_PATH env var or add to config/secrets.json" -ForegroundColor DarkGray
}

# ============================================================================
# 5. MCP SERVER CHECK (from NuSyQ repo)
# ============================================================================
Write-Host "[5/8] MCP Server..." -NoNewline
$MCPServerOK = $false
$MCPServerPath = "C:\Users\keath\NuSyQ\mcp_server\main.py"
if (Test-Path $MCPServerPath) {
    # Check if process is running (basic heuristic)
    $mcpProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match "mcp_server"
    }
    if ($mcpProcess) {
        Write-Host " [OK] Running" -ForegroundColor Green
        $MCPServerOK = $true
    } else {
        Write-Host " [!]  Installed but not running" -ForegroundColor Yellow
        Write-Host "   => Start from NuSyQ repo task or run: python $MCPServerPath" -ForegroundColor DarkGray
    }
} else {
    Write-Host " [X] Not found at expected path" -ForegroundColor Red
}

# ============================================================================
# 6. PRE-COMMIT HOOKS CHECK
# ============================================================================
Write-Host "[6/8] Pre-commit Hooks..." -NoNewline
$PrecommitOK = $false
try {
    $precommitVersion = pre-commit --version 2>&1
    if ($precommitVersion -match "pre-commit") {
        Write-Host " [OK] Installed" -ForegroundColor Green
        $PrecommitOK = $true
    }
} catch {
    Write-Host " [X] Not installed" -ForegroundColor Red
    Write-Host "   => Run: pip install pre-commit ; pre-commit install" -ForegroundColor DarkGray
}

# ============================================================================
# 7. QUEST SYSTEM CHECK
# ============================================================================
Write-Host "[7/8] Quest System..." -NoNewline
$QuestSystemOK = $false
$questLogPath = Join-Path $RepoRoot "src\Rosetta_Quest_System\quest_log.jsonl"
if (Test-Path $questLogPath) {
    Write-Host " [OK] Active" -ForegroundColor Green
    $QuestSystemOK = $true
} else {
    Write-Host " [!]  Log file missing" -ForegroundColor Yellow
    Write-Host "   => Will auto-initialize on first use" -ForegroundColor DarkGray
}

# ============================================================================
# 8. CONSCIOUSNESS BRIDGE & ORCHESTRATION CHECK
# ============================================================================
Write-Host "[8/8] Orchestration Systems..." -NoNewline
$OrchestrationOK = $false
$orchestrationFiles = @(
    "src\orchestration\multi_ai_orchestrator.py",
    "src\orchestration\unified_ai_orchestrator.py",
    "src\integration\consciousness_bridge.py"
)

$missingFiles = @()
foreach ($file in $orchestrationFiles) {
    if (-not (Test-Path (Join-Path $RepoRoot $file))) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -eq 0) {
    Write-Host " [OK] All core modules present" -ForegroundColor Green
    $OrchestrationOK = $true
} else {
    Write-Host " [!]  $($missingFiles.Count) modules missing" -ForegroundColor Yellow
    $missingFiles | ForEach-Object { Write-Host "   - $_" -ForegroundColor DarkGray }
}

# ============================================================================
# OVERALL SYSTEM STATUS
# ============================================================================
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
$systemScore = ($DockerOK ? 1 : 0) + ($PythonOK ? 1 : 0) + ($OllamaOK ? 1 : 0) + ($ChatDevOK ? 1 : 0) + ($MCPServerOK ? 1 : 0) + ($PrecommitOK ? 1 : 0) + ($QuestSystemOK ? 1 : 0) + ($OrchestrationOK ? 1 : 0)

if ($systemScore -eq 8) {
    Write-Host "[OK] SPINE ALIVE: All systems operational ($systemScore/8)" -ForegroundColor Green
    $spineStatus = "HEALTHY"
} elseif ($systemScore -ge 5) {
    Write-Host "[!]  SPINE FUNCTIONAL: Partial systems ($systemScore/8)" -ForegroundColor Yellow
    $spineStatus = "DEGRADED"
} else {
    Write-Host "[X] SPINE OFFLINE: Critical failures ($systemScore/8)" -ForegroundColor Red
    $spineStatus = "CRITICAL"
}

# ============================================================================
# SAVE STATUS TO JSON (for agent consumption)
# ============================================================================
$statusReport = @{
    timestamp = (Get-Date -Format "o")
    spine_status = $spineStatus
    score = $systemScore
    components = @{
        docker = @{
            healthy = $DockerOK
            details = if ($DockerOK) { "daemon running" } else { "not running" }
        }
        python = @{
            healthy = $PythonOK
            details = if ($PythonOK) { $PythonVersion } else { "venv missing or wrong version" }
        }
        ollama = @{
            healthy = $OllamaOK
            details = if ($OllamaOK) { "$($OllamaModels.Count) models" } else { "not running on localhost:11434" }
            models = $OllamaModels
        }
        chatdev = @{
            healthy = $ChatDevOK
            details = if ($ChatDevOK) { $ChatDevPath } else { "path not configured" }
        }
        mcp_server = @{
            healthy = $MCPServerOK
            details = if ($MCPServerOK) { "running" } else { "not running or not found" }
        }
        precommit = @{
            healthy = $PrecommitOK
            details = if ($PrecommitOK) { "hooks installed" } else { "not installed" }
        }
        quest_system = @{
            healthy = $QuestSystemOK
            details = if ($QuestSystemOK) { "log active" } else { "log missing" }
        }
        orchestration = @{
            healthy = $OrchestrationOK
            details = if ($OrchestrationOK) { "all modules present" } else { "$($missingFiles.Count) missing" }
        }
    }
}

$statusPath = Join-Path $RepoRoot "logs\system_health_status.json"
$logsDir = Split-Path $statusPath -Parent
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}
$statusReport | ConvertTo-Json -Depth 5 | Set-Content $statusPath -Encoding UTF8

Write-Host "`n📊 Status saved to: logs\system_health_status.json" -ForegroundColor DarkGray

# ============================================================================
# NEXT ACTIONS (if not in quiet mode for agents)
# ============================================================================
if (-not $QuietMode) {
    Write-Host "`n>> Next Actions:" -ForegroundColor Cyan
    if (-not $DockerOK) {
        Write-Host "  1. Start Docker: Launch Docker Desktop" -ForegroundColor Yellow
    }
    if (-not $OllamaOK) {
        Write-Host "  2. Start Ollama: Run NuSyQ.Orchestrator.ps1 from NuSyQ repo" -ForegroundColor Yellow
    }
    if (-not $ChatDevOK) {
        Write-Host "  3. Configure ChatDev: Add CHATDEV_PATH to config/secrets.json" -ForegroundColor Yellow
    }
    if (-not $MCPServerOK) {
        Write-Host "  4. Start MCP Server: Run 'Start MCP Server' task from NuSyQ workspace" -ForegroundColor Yellow
    }
    if (-not $PrecommitOK) {
        Write-Host "  5. Install Pre-commit: pip install pre-commit ; pre-commit install" -ForegroundColor Yellow
    }
    Write-Host "`n# To route tasks: Ask Copilot/Claude to 'route this to Ollama/ChatDev'" -ForegroundColor DarkGray
}

# Exit code 1 if critical (score < 5), 0 if functional
if ($systemScore -lt 5) {
    exit 1
} else {
    exit 0
}
