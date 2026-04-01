#Requires -Version 7.0
<#
    .SYNOPSIS
    NuSyQ DevMentor Unified Bootstrap — Manifest-Driven Multi-Service Orchestration
    
    .DESCRIPTION
    Reads DevMentorWorkspace.workspace.json and orchestrates:
      • Ollama (local LLM inference with vision models)
      • LM Studio (optional compatibility layer)
      • Terminal Depths backend (FastAPI game server)
      • SimulatedVerse (Node.js autonomous world)
      • NuSyQ MCP (tool orchestration)
      • Model Router (intelligent model selection)
    
    Supports:
      • Health checks and dependency resolution
      • Environment variable propagation
      • Hot-reload and debugging
      • Cross-surface access (VS Code, terminal, Docker, web)
    
    .PARAMETER ManifestPath
    Path to workspace manifest JSON (default: ./DevMentorWorkspace.workspace.json)
    
    .PARAMETER Services
    Comma-separated list of services to start (default: all required)
    
    .PARAMETER ForceRestart
    Force restart even if services are running
    
    .PARAMETER SkipHealthChecks
    Skip health checks (fast startup, risky)
    
    .PARAMETER Verbose
    Enable verbose logging
    
    .EXAMPLE
    .\bootstrap-manifest.ps1 -ManifestPath ".\DevMentorWorkspace.workspace.json"
    .\bootstrap-manifest.ps1 -Services "ollama,terminal-depths-backend" -ForceRestart
    .\bootstrap-manifest.ps1 -Verbose
#>

param(
    [string]$ManifestPath = ".\DevMentorWorkspace.workspace.json",
    [string]$Services = "",
    [switch]$ForceRestart,
    [switch]$SkipHealthChecks,
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'

# ============================================================
# Utility Functions
# ============================================================

function Write-Stage { 
    Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║ $($args[0].PadRight(48)) ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}

function Write-Step { Write-Host "  → $($args[0])" -ForegroundColor Cyan }
function Write-OK { Write-Host "  ✓ $($args[0])" -ForegroundColor Green }
function Write-Warn { Write-Host "  ⚠ $($args[0])" -ForegroundColor Yellow }
function Write-Err { Write-Host "  ✗ $($args[0])" -ForegroundColor Red }
function Write-Vv { if ($Verbose) { Write-Host "    ℹ $($args[0])" -ForegroundColor DarkGray } }

function Test-Port {
    param([int]$Port, [int]$Timeout = 2)
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $task = $tcp.ConnectAsync("127.0.0.1", $Port)
        $task.Wait($Timeout * 1000) | Out-Null
        $tcp.Close()
        return $task.IsCompleted
    } catch { 
        return $false 
    }
}

function Test-HealthEndpoint {
    param([string]$Url, [int]$Timeout = 5)
    $elapsed = 0
    while ($elapsed -lt $Timeout) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -ErrorAction SilentlyContinue -TimeoutSec 2
            if ($response.StatusCode -eq 200) { return $true }
        } catch { }
        Start-Sleep -Milliseconds 500
        $elapsed += 0.5
    }
    return $false
}

function Expand-ManifestPath {
    param([string]$Path, [PSCustomObject]$Manifest)
    
    $Path -replace '\$\{workspace:([^}]+)\}', {
        $folderName = $matches[1]
        $folder = $Manifest.folders | Where-Object { $_.name -eq $folderName } | Select-Object -First 1
        if (-not $folder) { 
            throw "Workspace '$folderName' not found in manifest"
        }
        $folder.path
    }
}

function Start-ManagedService {
    param(
        [string]$ServiceName,
        [PSCustomObject]$ServiceDef,
        [PSCustomObject]$Manifest
    )
    
    Write-Step "Starting $ServiceName (priority: $($ServiceDef.startup_priority))"
    
    $port = $ServiceDef.port
    $healthUrl = $ServiceDef.health_endpoint
    $cwd = if ($ServiceDef.cwd) { Expand-ManifestPath $ServiceDef.cwd $Manifest } else { $null }
    $cmd = $ServiceDef.command
    
    # Expand environment variables in command
    $cmd = Expand-ManifestPath $cmd $Manifest
    
    # Check if already running
    if ($port -and (Test-Port $port 1)) {
        Write-OK "$ServiceName already running (port $port open)"
        return @{ Success = $true; AlreadyRunning = $true; Port = $port }
    }
    
    Write-Vv "Working directory: $cwd"
    Write-Vv "Command: $cmd"
    
    # Set service-specific environment variables
    if ($ServiceDef.environment) {
        foreach ($key in $ServiceDef.environment.PSObject.Properties.Name) {
            $value = Expand-ManifestPath $ServiceDef.environment.$key $Manifest
            Set-Item -Path "env:$key" -Value $value
            Write-Vv "Set env:$key = $value"
        }
    }
    
    # Start process
    try {
        $processParams = @{
            FilePath = "powershell"
            ArgumentList = "-NoProfile -Command", "`$cd '$cwd'; $cmd"
            PassThru = $true
            NoNewWindow = $true
            ErrorAction = 'Stop'
        }
        
        if ($cwd) {
            $processParams.ArgumentList = "-NoProfile -Command", "Set-Location '$cwd'; $cmd"
        }
        
        $process = Start-Process @processParams
        
        Write-Vv "Process started (PID: $($process.Id))"
    } catch {
        Write-Err "Failed to start: $_"
        return @{ Success = $false; Error = $_ }
    }
    
    # Wait for health if not skipping checks
    if (-not $SkipHealthChecks -and $healthUrl) {
        Write-Step "Waiting for health check: $healthUrl"
        $timeout = 30
        $elapsed = 0
        
        while ($elapsed -lt $timeout) {
            if (Test-HealthEndpoint $healthUrl 2) {
                Write-OK "$ServiceName is healthy"
                return @{ Success = $true; Process = $process; Port = $port }
            }
            Start-Sleep -Milliseconds 1000
            $elapsed++
        }
        
        Write-Warn "$ServiceName did not become healthy within $timeout seconds (may still be starting)"
        return @{ Success = $false; Timeout = $true; Process = $process }
    } else {
        Start-Sleep -Milliseconds 500
        Write-OK "$ServiceName started (port $port)"
        return @{ Success = $true; Process = $process; Port = $port }
    }
}

# ============================================================
# Main Bootstrap Sequence
# ============================================================

Write-Stage "NuSyQ DevMentor Unified Bootstrap"

# 1. Load Manifest
Write-Step "Loading workspace manifest..."
if (-not (Test-Path $ManifestPath)) {
    Write-Err "Manifest not found: $ManifestPath"
    exit 1
}

$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
Write-OK "Manifest loaded: $($manifest.name)"
Write-Vv "Version: $($manifest.version)"

# 2. Set Global Environment Variables
Write-Stage "Setting Environment Variables"

foreach ($key in $manifest.environment.global.PSObject.Properties.Name) {
    $value = $manifest.environment.global.$key
    Set-Item -Path "env:$key" -Value $value
    Write-OK "env:$key = $value"
}

# Model config
foreach ($key in $manifest.environment.model_config.PSObject.Properties.Name) {
    $value = $manifest.environment.model_config.$key
    Set-Item -Path "env:$key" -Value $value
    Write-OK "env:$key = $value"
}

# 3. Parse Services to Start
Write-Stage "Service Orchestration"

$servicesToStart = if ($Services) {
    $Services -split ',' | ForEach-Object { $_.Trim() }
} else {
    # Default: all required services + optional (if force restart)
    $manifest.services.PSObject.Properties | 
        Where-Object { $_.Value.required -or $ForceRestart } | 
        ForEach-Object { $_.Name }
}

Write-Step "Services to start: $($servicesToStart -join ', ')"

# 4. Start Services in Priority Order
$startResults = @{}
$servicesByPriority = $manifest.services.PSObject.Properties | 
    Where-Object { $servicesToStart -contains $_.Name } |
    Sort-Object { $_.Value.startup_priority }

foreach ($svc in $servicesByPriority) {
    $name = $svc.Name
    $def = $svc.Value
    
    Write-Step "Starting $name..."
    
    # Check dependencies
    if ($def.dependencies) {
        foreach ($dep in $def.dependencies) {
            if (-not $startResults[$dep].Success) {
                Write-Warn "$name depends on $dep (not started); skipping $name"
                $startResults[$name] = @{ Success = $false; Reason = "Dependency not started" }
                continue
            }
        }
    }
    
    $result = Start-ManagedService $name $def $manifest
    $startResults[$name] = $result
    
    if (-not $result.Success -and -not $result.AlreadyRunning) {
        Write-Warn "$name failed to start"
    }
}

# 5. Summary
Write-Stage "Bootstrap Summary"

$successCount = ($startResults.Values | Where-Object { $_.Success }).Count
$totalCount = $startResults.Count

Write-OK "$successCount / $totalCount services running"

foreach ($svc in $startResults.Keys) {
    $result = $startResults[$svc]
    if ($result.Success) {
        if ($result.AlreadyRunning) {
            Write-OK "$svc (already running)"
        } else {
            Write-OK "$svc (port $($result.Port))"
        }
    } else {
        Write-Warn "$svc (failed: $($result.Reason // $result.Error // 'unknown'))"
    }
}

# 6. Next Steps
Write-Stage "Next Steps"

Write-Host ""
Write-Host "Services are running. You can now:"
Write-Host ""
Write-Host "  1. Play Terminal Depths:"
Write-Host "     cd C:\Users\keath\Dev-Mentor"
Write-Host "     python -m cli.devmentor play"
Write-Host ""
Write-Host "  2. Open SimulatedVerse UI:"
Write-Host "     http://localhost:3030"
Write-Host ""
Write-Host "  3. Access Dev-Mentor API:"
Write-Host "     http://localhost:7337/docs"
Write-Host ""
Write-Host "  4. Check Ollama models:"
Write-Host "     http://localhost:11434"
Write-Host ""
Write-Host "  5. Debug in VS Code:"
Write-Host "     code Dev-Mentor-Complete.code-workspace"
Write-Host ""
Write-Host "Environment variables are set for this session."
Write-Host ""
# Keep terminal open
