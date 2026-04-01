#!/usr/bin/env pwsh
<#
.SYNOPSIS
    NuSyQ System Health Check - Agent-invokable version
    
.DESCRIPTION
    Checks status of all AI systems (Ollama, ChatDev, MCP Server, etc.)
    Designed for agent invocation via Copilot/Claude tasks.
#>

param(
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$systemScore = 0
$totalChecks = 5

Write-Host "`n=== NuSyQ System Health Check ===" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor DarkGray

# ============================================================================
# 1. PYTHON ENVIRONMENT
# ============================================================================
Write-Host "[1/5] Python Environment..." -NoNewline
$PythonOK = $false
try {
    $venvActivate = Join-Path $RepoRoot ".venv\Scripts\Activate.ps1"
    if (Test-Path $venvActivate) {
        & $venvActivate
        $PythonVersion = python --version 2>&1
        # Check for Python 3.12+
        if ($PythonVersion -match 'Python 3\.1[2-9]' -or $PythonVersion -match 'Python 3\.[2-9][0-9]') {
            Write-Host " [OK] $PythonVersion" -ForegroundColor Green
            $PythonOK = $true
            $systemScore += 1
        } else {
            Write-Host " [WARN] $PythonVersion (need 3.12+)" -ForegroundColor Yellow
        }
    } else {
        Write-Host " [FAIL] .venv not found" -ForegroundColor Red
    }
} catch {
    Write-Host " [FAIL] Python check error" -ForegroundColor Red
}

# ============================================================================
# 2. OLLAMA (LOCAL LLM)
# ============================================================================
Write-Host "[2/5] Ollama (Local LLM)..." -NoNewline
$OllamaOK = $false
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        if ($data.models) {
            Write-Host " [OK] $($data.models.Count) models" -ForegroundColor Green
            $OllamaOK = $true
            $systemScore += 1
        } else {
            Write-Host " [WARN] Running but no models" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host " [FAIL] Not running (port 11434)" -ForegroundColor Red
}

# ============================================================================
# 3. CHATDEV
# ============================================================================
Write-Host "[3/5] ChatDev Path..." -NoNewline
$ChatDevOK = $false
$chatdevPath = $env:CHATDEV_PATH
if ([string]::IsNullOrEmpty($chatdevPath)) {
    $chatdevPath = "C:\Users\keath\NuSyQ\ChatDev"
}
if (Test-Path $chatdevPath) {
    Write-Host " [OK] Found" -ForegroundColor Green
    $ChatDevOK = $true
    $systemScore += 1
} else {
    Write-Host " [FAIL] Path not found" -ForegroundColor Red
}

# ============================================================================
# 4. MCP SERVER
# ============================================================================
Write-Host "[4/5] MCP Server..." -NoNewline
$mcpRunning = $false
try {
    # Check if MCP is listening on port 5000
    $tcpClient = [System.Net.Sockets.TcpClient]::new()
    $tcpClient.ConnectAsync("127.0.0.1", 5000) | Out-Null
    if ($tcpClient.Connected) {
        Write-Host " [OK] Running" -ForegroundColor Green
        $mcpRunning = $true
        $systemScore += 1
    }
    $tcpClient.Close()
} catch {
    Write-Host " [FAIL] Not running" -ForegroundColor Red
}

# ============================================================================
# 5. QUEST SYSTEM
# ============================================================================
Write-Host "[5/5] Quest System..." -NoNewline
$questLogPath = Join-Path $RepoRoot "src\Rosetta_Quest_System\quest_log.jsonl"
if (Test-Path $questLogPath) {
    Write-Host " [OK] Found" -ForegroundColor Green
    $systemScore += 1
} else {
    Write-Host " [FAIL] Not found" -ForegroundColor Yellow
}

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host "`nHealth Score: $systemScore / $totalChecks" -ForegroundColor Cyan
if ($systemScore -ge 4) {
    Write-Host "Status: OPERATIONAL" -ForegroundColor Green
    exit 0
} elseif ($systemScore -ge 2) {
    Write-Host "Status: DEGRADED" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "Status: CRITICAL" -ForegroundColor Red
    exit 1
}
