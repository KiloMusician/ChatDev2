#Requires -Version 5.1
<#
.SYNOPSIS
    DevMentor / Terminal Depths — Windows PowerShell Launcher
.DESCRIPTION
    Works in: PowerShell 5.1+, PowerShell 7+, VS Code integrated terminal,
    Windows Terminal, CMD (via devmentor.bat), Docker Desktop
.EXAMPLE
    .\devmentor.ps1 serve
    .\devmentor.ps1 play MyAgentName
    .\devmentor.ps1 docker
    .\devmentor.ps1 mcp
#>

param(
    [ValidateSet('serve','s','play','p','docker','d','docker-full','df','stop','status','st','mcp','agent','a','help','h')]
    [string]$Mode = 'serve',
    [string]$Session = "",
    [int]$Port = ($env:TD_PORT ?? 7337),
    [string]$Host = ($env:TD_HOST ?? "0.0.0.0")
)

$Root = $PSScriptRoot
Push-Location $Root

# Prevent stale .pyc bytecode from masking code changes
$env:PYTHONDONTWRITEBYTECODE = "1"

function Write-Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   Terminal Depths — DevMentor Launcher       ║" -ForegroundColor Cyan
    Write-Host ("║   Mode: {0,-36}║" -f $Mode) -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Command($cmd) {
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

switch ($Mode) {
    { $_ -in 'serve','s' } {
        Write-Banner
        if (-not (Test-Command 'python')) { Write-Error "Python not found"; exit 1 }
        Write-Host "→ Starting API server on http://${Host}:${Port}" -ForegroundColor Green
        Write-Host "→ Browser: http://localhost:${Port}/game/" -ForegroundColor Green
        python -m cli.devmentor serve --host $Host --port $Port
    }
    { $_ -in 'play','p' } {
        Write-Banner
        $sid = if ($Session) { $Session } else { "player-$env:USERNAME" }
        Write-Host "→ Interactive REPL (session: $sid)" -ForegroundColor Green
        python -m cli.devmentor play --session-id $sid
    }
    { $_ -in 'docker','d' } {
        Write-Banner
        if (-not (Test-Command 'docker')) { Write-Error "Docker not found"; exit 1 }
        Write-Host "→ Docker Compose (base stack)" -ForegroundColor Green
        docker compose -f docker-compose.yml up -d
        Write-Host "→ API: http://localhost:7337  |  Game: http://localhost:7337/game/" -ForegroundColor Cyan
    }
    { $_ -in 'docker-full','df' } {
        Write-Banner
        docker compose -f docker-compose.full.yml up -d
    }
    'stop' {
        Write-Host "Stopping all DevMentor containers..." -ForegroundColor Yellow
        docker compose -f docker-compose.yml down 2>$null
        docker compose -f docker-compose.full.yml down 2>$null
    }
    { $_ -in 'status','st' } {
        python -m cli.devmentor status
    }
    'mcp' {
        Write-Banner
        Write-Host "→ MCP server on stdio (for Claude Desktop / Copilot)" -ForegroundColor Green
        python mcp/server.py
    }
    { $_ -in 'agent','a' } {
        $sid = if ($Session) { $Session } else { "agent-$env:COMPUTERNAME" }
        Write-Banner
        python -m cli.devmentor agent --session-id $sid
    }
    { $_ -in 'help','h' } {
        Write-Host @"
Usage: .\devmentor.ps1 [Mode] [-Session name] [-Port 7337]

Modes:
  serve (s)          Start API server (default)
  play  (p)          Interactive REPL
  docker (d)         Docker Compose base stack
  docker-full (df)   Full stack with Redis/Ollama
  stop               Stop all containers
  status (st)        System status
  mcp                MCP stdio server (Claude Desktop / Copilot)
  agent (a)          Run as named agent

Environment variables:
  `$env:TD_PORT = 7337
  `$env:TD_HOST = "0.0.0.0"
  `$env:OPENAI_API_KEY = "sk-..."
  `$env:NUSYQ_PASSKEY  = "..."
"@ -ForegroundColor White
    }
}

Pop-Location
