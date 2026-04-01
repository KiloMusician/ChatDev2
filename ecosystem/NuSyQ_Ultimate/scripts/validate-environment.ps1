# NuSyQ Environment Validation Script
# Validates the complete NuSyQ multi-AI orchestration environment
# Purpose: Pre-flight checks before running orchestrator

<#
.SYNOPSIS
    Validate NuSyQ ecosystem environment and dependencies

.DESCRIPTION
    Comprehensive health check for the NuSyQ multi-AI environment including:
    - Python environment and packages
    - Ollama models availability (37.5GB collection)
    - MCP server connectivity
    - Configuration file integrity
    - Agent coordination readiness

.PARAMETER Quick
    Run quick validation only (skip heavy checks)

.PARAMETER Verbose
    Show detailed output for all checks

.EXAMPLE
    .\validate-environment.ps1
    Full environment validation

.EXAMPLE
    .\validate-environment.ps1 -Quick -Verbose
    Quick validation with detailed output
#>

param(
    [switch]$Quick,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$NuSyQRoot = Split-Path -Parent $ScriptDir

# Colors for output
function Write-Success { param($msg) Write-Host " $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host " $msg" -ForegroundColor Red }
function Write-Warn { param($msg) Write-Host "  $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "  $msg" -ForegroundColor Cyan }
function Write-Detail { param($msg) if ($Verbose) { Write-Host "  -- $msg" -ForegroundColor DarkGray } }

$script:ErrorCount = 0
$script:WarningCount = 0
$script:CheckCount = 0

function Record-Error { $script:ErrorCount++ }
function Record-Warning { $script:WarningCount++ }
function Record-Check { $script:CheckCount++ }

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " NuSyQ Environment Validation" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# ═══════════════════════════════════════════════════════════
# 1. Python Environment Check
# ═══════════════════════════════════════════════════════════
Write-Info "Checking Python environment..."
Record-Check

try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python installed: $pythonVersion"
        Write-Detail "Path: $(Get-Command python | Select-Object -ExpandProperty Source)"
    } else {
        Write-Fail "Python not found or not in PATH"
        Record-Error
    }
} catch {
    Write-Fail "Python check failed: $_"
    Record-Error
}

# Check for virtual environment
if (Test-Path "$NuSyQRoot\.venv\Scripts\python.exe") {
    Write-Success "Virtual environment found: .venv"
    Write-Detail "$NuSyQRoot\.venv"
} else {
    Write-Warn "Virtual environment not found at .venv"
    Write-Detail "Run: python -m venv .venv"
    Record-Warning
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# 2. Configuration Files Check
# ═══════════════════════════════════════════════════════════
Write-Info "Validating configuration files..."
Record-Check

$configFiles = @(
    @{Name="Manifest"; Path="nusyq.manifest.yaml"; Required=$true},
    @{Name="Knowledge Base"; Path="knowledge-base.yaml"; Required=$true},
    @{Name="Config Manager"; Path="config\config_manager.py"; Required=$true},
    @{Name="Environment"; Path=".env"; Required=$false}
)

foreach ($config in $configFiles) {
    $fullPath = Join-Path $NuSyQRoot $config.Path
    if (Test-Path $fullPath) {
        Write-Success "$($config.Name): Found"
        Write-Detail $config.Path
    } else {
        if ($config.Required) {
            Write-Fail "$($config.Name): Missing (REQUIRED)"
            Write-Detail "Expected: $($config.Path)"
            Record-Error
        } else {
            Write-Warn "$($config.Name): Not found (optional)"
            Record-Warning
        }
    }
}

# Validate config using Python
try {
    $validationOutput = & python "$NuSyQRoot\config\config_manager.py" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Configuration validation passed"
        Write-Detail "config_manager.py executed successfully"
    } else {
        Write-Warn "Configuration validation returned warnings"
        if ($Verbose) { Write-Host $validationOutput -ForegroundColor DarkGray }
        Record-Warning
    }
} catch {
    Write-Fail "Configuration validation failed: $_"
    Record-Error
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# 3. Ollama Installation and Models Check
# ═══════════════════════════════════════════════════════════
Write-Info "Checking Ollama installation and models..."
Record-Check

try {
    $ollamaVersion = ollama --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Ollama installed: $ollamaVersion"
        Write-Detail "Path: $(Get-Command ollama -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)"

        # Check for running Ollama service
        try {
            $ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
            if ($ollamaProcess) {
                Write-Success "Ollama service running"
                Write-Detail "PID: $($ollamaProcess.Id)"
            } else {
                Write-Warn "Ollama service not running - start with: ollama serve"
                Record-Warning
            }
        } catch {
            Write-Warn "Could not check Ollama service status"
            Record-Warning
        }

        # List installed models (skip if Quick mode)
        if (-not $Quick) {
            Write-Info "Checking installed models (37.5GB collection)..."
            try {
                $models = ollama list 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $modelCount = ($models -split "`n" | Where-Object { $_ -match "^\w" }).Count - 1
                    if ($modelCount -gt 0) {
                        Write-Success "Found $modelCount Ollama models"
                        if ($Verbose) {
                            Write-Host $models -ForegroundColor DarkGray
                        }

                        # Check for key models
                        $keyModels = @("qwen2.5-coder", "starcoder2", "gemma2", "codellama")
                        foreach ($model in $keyModels) {
                            if ($models -match $model) {
                                Write-Detail " $model installed"
                            } else {
                                Write-Detail " $model not found"
                            }
                        }
                    } else {
                        Write-Warn "No Ollama models installed"
                        Write-Detail "Run NuSyQ.Orchestrator.ps1 to install models"
                        Record-Warning
                    }
                }
            } catch {
                Write-Warn "Could not list Ollama models: $_"
                Record-Warning
            }
        }
    } else {
        Write-Fail "Ollama not installed or not in PATH"
        Write-Detail "Install from: https://ollama.ai"
        Record-Error
    }
} catch {
    Write-Fail "Ollama check failed: $_"
    Record-Error
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# 4. MCP Server Check
# ═══════════════════════════════════════════════════════════
Write-Info "Checking MCP server..."
Record-Check

$mcpServerPath = Join-Path $NuSyQRoot "mcp_server\main.py"
if (Test-Path $mcpServerPath) {
    Write-Success "MCP server found"
    Write-Detail $mcpServerPath

    # Check if MCP server is running
    $mcpProcess = Get-Process -Name "python" -ErrorAction SilentlyContinue |
                  Where-Object { $_.CommandLine -like "*mcp_server*" }
    if ($mcpProcess) {
        Write-Success "MCP server running"
        Write-Detail "PID: $($mcpProcess.Id)"
    } else {
        Write-Warn "MCP server not running"
        Write-Detail "Start with VS Code task or: python mcp_server\main.py"
        Record-Warning
    }
} else {
    Write-Warn "MCP server not found"
    Record-Warning
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# 5. ChatDev Integration Check
# ═══════════════════════════════════════════════════════════
Write-Info "Checking ChatDev integration..."
Record-Check

$chatDevPath = Join-Path $NuSyQRoot "ChatDev"
if (Test-Path $chatDevPath) {
    Write-Success "ChatDev directory found"
    Write-Detail $chatDevPath

    # Check for key ChatDev files
    $chatDevMain = Join-Path $chatDevPath "run.py"
    if (Test-Path $chatDevMain) {
        Write-Detail " run.py found"
    } else {
        Write-Warn "ChatDev run.py not found"
        Record-Warning
    }
} else {
    Write-Warn "ChatDev not found - multi-agent features unavailable"
    Record-Warning
}

Write-Host ""

# ═══════════════════════════════════════════════════════════
# 6. Agent Coordination Check
# ═══════════════════════════════════════════════════════════
if (-not $Quick) {
    Write-Info "Checking agent coordination files..."
    Record-Check

    $agentFiles = @(
        "nusyq_chatdev.py",
        "consensus_orchestrator.py",
        "orchestrator_launcher.py"
    )

    foreach ($file in $agentFiles) {
        $fullPath = Join-Path $NuSyQRoot $file
        if (Test-Path $fullPath) {
            Write-Detail " $file"
        } else {
            Write-Warn "Missing: $file"
            Record-Warning
        }
    }
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════
# 7. Summary
# ═══════════════════════════════════════════════════════════
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "� Validation Summary" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Checks performed: $script:CheckCount" -ForegroundColor White
Write-Host "Errors: $script:ErrorCount" -ForegroundColor $(if ($script:ErrorCount -gt 0) { "Red" } else { "Green" })
Write-Host "Warnings: $script:WarningCount" -ForegroundColor $(if ($script:WarningCount -gt 0) { "Yellow" } else { "Green" })
Write-Host ""

if ($script:ErrorCount -eq 0) {
    Write-Host " Environment validation PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ready to run:" -ForegroundColor Cyan
    Write-Host "  .\NuSyQ.Orchestrator.ps1" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host " Environment validation FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Fix errors above before running orchestrator" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
