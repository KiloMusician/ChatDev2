#!/usr/bin/env pwsh
<#
.SYNOPSIS
Full-Stack Ecosystem Activation & Orchestration Script
Activates: Dev-Mentor, NuSyQ Hub, ChatDev, SimulatedVerse, Ollama, and all supporting services

.DESCRIPTION
This script orchestrates the complete Terminal Depths + NuSyQ + ChatDev ecosystem:
1. Validates all repositories and configurations
2. Activates Ollama with model suite
3. Starts Dev-Mentor backend + RimWorld/noVNC
4. Activates NuSyQ Hub integration
5. Launches ChatDev autonomous dev company
6. Wires MCP server and bridges
7. Tests complete system integration
8. Generates status reports

.PARAMETER Profile
The Docker Compose profile to activate (full, ai-agents, data, etc.)

.PARAMETER Verbose
Enable detailed logging

.EXAMPLE
.\activate-ecosystem.ps1 -Profile full
.\activate-ecosystem.ps1 -Profile ai-agents -Verbose
#>

param(
    [ValidateSet('full', 'ai-agents', 'data', 'games', 'automation', 'dev', 'lm-studio', 'mcp')]
    [string]$Profile = 'full',
    
    [switch]$Verbose
)

# ============================================================================
# CONFIGURATION
# ============================================================================

$ErrorActionPreference = 'Stop'
$VerbosePreference = if ($Verbose) { 'Continue' } else { 'SilentlyContinue' }

$DEV_MENTOR_ROOT = Get-Location
$NUSYQ_ROOT = Join-Path (Split-Path $DEV_MENTOR_ROOT -Parent) 'NuSyQ'
$COMPOSE_FILE = Join-Path $DEV_MENTOR_ROOT 'docker-compose.full.yml'

$TIMESTAMP = Get-Date -Format 'yyyyMMdd_HHmmss'
$LOG_DIR = Join-Path $DEV_MENTOR_ROOT 'Logs'
$LOG_FILE = Join-Path $LOG_DIR "activation_$TIMESTAMP.log"

# ============================================================================
# FUNCTIONS
# ============================================================================

function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    
    $timestamp = Get-Date -Format 'HH:mm:ss'
    $output = "[$timestamp] [$Level] $Message"
    
    Write-Host $output
    Add-Content $LOG_FILE $output
}

function Test-Repository {
    param([string]$Path, [string]$Name)
    
    if (-not (Test-Path $Path)) {
        Write-Log "⚠ Repository not found: $Name → $Path" 'WARNING'
        return $false
    }
    Write-Log "✓ Repository found: $Name" 'SUCCESS'
    return $true
}

function Test-DockerCommand {
    try {
        $null = docker ps -q
        Write-Log "✓ Docker daemon accessible" 'SUCCESS'
        return $true
    }
    catch {
        Write-Log "✗ Docker daemon not accessible: $_" 'ERROR'
        return $false
    }
}

function Test-DockerNetwork {
    param([string]$NetworkName)
    
    $network = docker network ls --filter "name=$NetworkName" -q
    if ($network) {
        Write-Log "✓ Docker network exists: $NetworkName" 'SUCCESS'
        return $true
    }
    Write-Log "✗ Docker network missing: $NetworkName" 'ERROR'
    return $false
}

function Activate-Ollama {
    Write-Log "========== ACTIVATING OLLAMA ==========" 'INFO'
    
    # Check if Ollama container exists
    $container = docker ps -aq -f "name=terminal-depths-ollama"
    
    if ($container) {
        Write-Log "Ollama container already exists, checking status..." 'INFO'
        $status = docker inspect $container --format '{{.State.Status}}'
        if ($status -eq 'running') {
            Write-Log "✓ Ollama already running" 'SUCCESS'
            return $true
        }
    }
    
    Write-Log "Starting Ollama service..." 'INFO'
    docker compose -f $COMPOSE_FILE up -d ollama
    
    # Wait for Ollama to be ready
    $maxAttempts = 30
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Log "✓ Ollama API responding" 'SUCCESS'
                return $true
            }
        }
        catch { }
        
        $attempt++
        Write-Log "  Waiting for Ollama... ($attempt/$maxAttempts)" 'INFO'
        Start-Sleep -Seconds 2
    }
    
    Write-Log "✗ Ollama failed to start" 'ERROR'
    return $false
}

function Pull-OllamaModels {
    Write-Log "========== PULLING OLLAMA MODELS ==========" 'INFO'
    
    $models = @(
        'qwen2.5-coder:14b',
        'qwen2.5-coder:7b',
        'codellama:7b',
        'deepseek-coder:6.7b',
        'starcoder2:15b',
        'gemma2:9b',
        'phi4'
    )
    
    foreach ($model in $models) {
        Write-Log "  Pulling model: $model" 'INFO'
        $result = docker exec terminal-depths-ollama ollama pull $model 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "  ✓ Model pulled: $model" 'SUCCESS'
        }
        else {
            Write-Log "  ⚠ Model pull warning: $model" 'WARNING'
        }
    }
    
    Write-Log "✓ Ollama models activation complete" 'SUCCESS'
}

function Activate-DevMentor {
    Write-Log "========== ACTIVATING DEV-MENTOR ==========" 'INFO'
    
    Write-Log "Starting Dev-Mentor backend..." 'INFO'
    docker compose -f $COMPOSE_FILE up -d dev-mentor
    
    # Wait for backend
    $maxAttempts = 30
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:7337/" -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Log "✓ Dev-Mentor API responding" 'SUCCESS'
                return $true
            }
        }
        catch { }
        
        $attempt++
        Write-Log "  Waiting for Dev-Mentor... ($attempt/$maxAttempts)" 'INFO'
        Start-Sleep -Seconds 2
    }
    
    Write-Log "✗ Dev-Mentor failed to start" 'ERROR'
    return $false
}

function Activate-ChatDev {
    Write-Log "========== ACTIVATING CHATDEV ==========" 'INFO'
    
    if (-not (Test-Path $NUSYQ_ROOT)) {
        Write-Log "✗ NuSyQ repository not found at $NUSYQ_ROOT" 'ERROR'
        return $false
    }
    
    Write-Log "Starting ChatDev orchestrator..." 'INFO'
    docker compose -f $COMPOSE_FILE up -d chatdev
    
    # Wait for ChatDev
    $maxAttempts = 20
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:7338/health" -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Log "✓ ChatDev API responding" 'SUCCESS'
                return $true
            }
        }
        catch { }
        
        $attempt++
        Write-Log "  Waiting for ChatDev... ($attempt/$maxAttempts)" 'INFO'
        Start-Sleep -Seconds 3
    }
    
    Write-Log "⚠ ChatDev startup timeout (will retry)" 'WARNING'
    return $false
}

function Activate-NuSyQBridge {
    Write-Log "========== ACTIVATING NUSYQ BRIDGE ==========" 'INFO'
    
    Write-Log "Starting NuSyQ bridge service..." 'INFO'
    docker compose -f $COMPOSE_FILE up -d nusyq-bridge
    
    # Wait for bridge
    $maxAttempts = 15
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:9876/health" -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $health = $response.Content | ConvertFrom-Json
                Write-Log "✓ NuSyQ Bridge healthy: $($health.status)" 'SUCCESS'
                Write-Log "  Connected services: $($health.connections | ConvertTo-Json -Compress)" 'INFO'
                return $true
            }
        }
        catch { }
        
        $attempt++
        Write-Log "  Waiting for NuSyQ Bridge... ($attempt/$maxAttempts)" 'INFO'
        Start-Sleep -Seconds 2
    }
    
    Write-Log "⚠ NuSyQ Bridge startup timeout" 'WARNING'
    return $false
}

function Activate-MCP {
    Write-Log "========== ACTIVATING MCP SERVER ==========" 'INFO'
    
    Write-Log "Starting MCP server..." 'INFO'
    docker compose -f $COMPOSE_FILE up -d mcp-server
    
    # Wait for MCP
    $maxAttempts = 15
    $attempt = 0
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8765/health" -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Log "✓ MCP Server responding" 'SUCCESS'
                return $true
            }
        }
        catch { }
        
        $attempt++
        Write-Log "  Waiting for MCP Server... ($attempt/$maxAttempts)" 'INFO'
        Start-Sleep -Seconds 2
    }
    
    Write-Log "⚠ MCP Server startup timeout" 'WARNING'
    return $false
}

function Test-Integration {
    Write-Log "========== TESTING INTEGRATION ==========" 'INFO'
    
    $tests = @{
        'Dev-Mentor API' = 'http://localhost:7337/'
        'Ollama API' = 'http://localhost:11434/api/tags'
        'ChatDev API' = 'http://localhost:7338/health'
        'NuSyQ Bridge' = 'http://localhost:9876/health'
        'MCP Server' = 'http://localhost:8765/health'
        'RimWorld noVNC' = 'http://localhost:9000/'
    }
    
    $passed = 0
    $failed = 0
    
    foreach ($test in $tests.GetEnumerator()) {
        try {
            $response = Invoke-WebRequest -Uri $test.Value -ErrorAction SilentlyContinue -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Log "✓ $($test.Name)" 'SUCCESS'
                $passed++
            }
            else {
                Write-Log "✗ $($test.Name) - HTTP $($response.StatusCode)" 'ERROR'
                $failed++
            }
        }
        catch {
            Write-Log "✗ $($test.Name) - Unreachable" 'ERROR'
            $failed++
        }
    }
    
    Write-Log "Integration Tests: $passed passed, $failed failed" 'INFO'
    return ($failed -eq 0)
}

function Test-InterServiceComm {
    Write-Log "========== TESTING INTER-SERVICE COMMUNICATION ==========" 'INFO'
    
    # Test Dev-Mentor → Ollama
    Write-Log "Testing Dev-Mentor → Ollama..." 'INFO'
    $result = docker exec terminal-depths-backend python -c "import urllib.request; print(urllib.request.urlopen('http://terminal-depths-ollama:11434/api/tags').read().decode())" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✓ Dev-Mentor can reach Ollama" 'SUCCESS'
    }
    else {
        Write-Log "✗ Dev-Mentor → Ollama communication failed" 'ERROR'
    }
    
    # Test NuSyQ Bridge health
    Write-Log "Testing NuSyQ Bridge service health..." 'INFO'
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:9876/health"
        Write-Log "✓ NuSyQ Bridge status: $($health.status)" 'SUCCESS'
        foreach ($service in $health.connections.GetEnumerator()) {
            $status = if ($service.Value) { '✓' } else { '✗' }
            Write-Log "  $status $($service.Name)" 'INFO'
        }
    }
    catch {
        Write-Log "✗ Failed to get NuSyQ Bridge health" 'ERROR'
    }
}

function Generate-Report {
    Write-Log "========== GENERATING ECOSYSTEM REPORT ==========" 'INFO'
    
    $report = @"
╔════════════════════════════════════════════════════════════════════════════╗
║            TERMINAL DEPTHS + NUSYQ ECOSYSTEM ACTIVATION REPORT             ║
║                          Timestamp: $(Get-Date)                       ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 SERVICE STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"@
    
    $services = docker compose -f $COMPOSE_FILE ps --format "{{.Service}}\t{{.Status}}"
    $report += "Service Statuses:`n"
    $report += $services + "`n`n"
    
    $report += @"
🌐 ACCESS POINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Dev-Mentor API:        http://localhost:7337/
Ollama LLM Server:     http://localhost:11434/api/tags
ChatDev Orchestrator:  http://localhost:7338/
NuSyQ Bridge:          http://localhost:9876/health
MCP Server:            http://localhost:8765/health
RimWorld/noVNC:        http://localhost:9000/
Jupyter Lab:           http://localhost:8888/

🔌 NETWORK TOPOLOGY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Primary Network:       dev-mentor_terminal-depths-net (172.27.0.0/16)
Integration Network:   deploy_nusyq-net (shared with NuSyQ Hub ecosystem)

🚀 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Pull LLM Models:
   docker exec terminal-depths-ollama ollama pull qwen2.5-coder:14b

2. Submit ChatDev Tasks:
   curl -X POST http://localhost:9876/api/v1/task \
     -H "Content-Type: application/json" \
     -d '{"description":"Your task","task_type":"CODE_GENERATION","priority":1}'

3. Monitor System:
   docker compose -f docker-compose.full.yml logs -f

4. Access Dashboards:
   - Dev-Mentor Dashboard: http://localhost:7337/
   - NuSyQ Hub: http://localhost:8000/
   - Jupyter Lab: http://localhost:8888/

╔════════════════════════════════════════════════════════════════════════════╗
║                      System Activation Complete                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"@
    
    $reportPath = Join-Path $LOG_DIR "ecosystem_report_$TIMESTAMP.txt"
    $report | Out-File $reportPath -Encoding UTF8
    Write-Log "✓ Report saved: $reportPath" 'SUCCESS'
    
    Write-Host $report
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Write-Log "╔════════════════════════════════════════════════════════════════════════════╗" 'INFO'
Write-Log "║     TERMINAL DEPTHS + NUSYQ FULL-STACK ECOSYSTEM ACTIVATION              ║" 'INFO'
Write-Log "║                    Profile: $Profile                                       ║" 'INFO'
Write-Log "╚════════════════════════════════════════════════════════════════════════════╝" 'INFO'

# Create log directory
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR | Out-Null
}

Write-Log "Log file: $LOG_FILE" 'INFO'

# ============= PRE-CHECKS =============
Write-Log "========== PRE-ACTIVATION CHECKS ==========" 'INFO'

if (-not (Test-DockerCommand)) {
    Write-Log "✗ Docker is not accessible. Exiting." 'ERROR'
    exit 1
}

if (-not (Test-Path $COMPOSE_FILE)) {
    Write-Log "✗ docker-compose.full.yml not found at $COMPOSE_FILE" 'ERROR'
    exit 1
}

Test-Repository $DEV_MENTOR_ROOT "Dev-Mentor"
Test-Repository $NUSYQ_ROOT "NuSyQ"
Test-DockerNetwork "dev-mentor_terminal-depths-net"
Test-DockerNetwork "deploy_nusyq-net"

# ============= ACTIVATION =============
$allSuccess = $true

if ($Profile -in @('full', 'ai-agents', 'data')) {
    if (-not (Activate-Ollama)) { $allSuccess = $false }
    Pull-OllamaModels
}

if ($Profile -in @('full', 'ai-agents')) {
    if (-not (Activate-DevMentor)) { $allSuccess = $false }
    if (-not (Activate-ChatDev)) { $allSuccess = $false }
    if (-not (Activate-NuSyQBridge)) { $allSuccess = $false }
    if (-not (Activate-MCP)) { $allSuccess = $false }
}

# ============= TESTING =============
Write-Log "========== POST-ACTIVATION VALIDATION ==========" 'INFO'
Start-Sleep -Seconds 5

Test-Integration
Test-InterServiceComm

# ============= REPORTING =============
Generate-Report

if ($allSuccess) {
    Write-Log "✓ ACTIVATION COMPLETE - All critical services running" 'SUCCESS'
    exit 0
}
else {
    Write-Log "⚠ ACTIVATION COMPLETE WITH WARNINGS - Check log for details" 'WARNING'
    exit 0
}
