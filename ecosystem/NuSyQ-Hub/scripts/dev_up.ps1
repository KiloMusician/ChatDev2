<#
PowerShell helper to bring up the development stack.

Usage:
  # Minimal (app container only)
  .\scripts\dev_up.ps1

  # Full stack (app + postgres + redis + ollama-mock)
  .\scripts\dev_up.ps1 -Profile full
#>
param(
  [ValidateSet("minimal","full")]
  [string]$Profile = "minimal",

  [switch]$Build
)

Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Definition)
$repoRoot = Resolve-Path ..
$composeFile = Join-Path $repoRoot "deploy/docker-compose.dev.yml"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Error "Docker CLI not found in PATH. Please install Docker Desktop or make sure 'docker' is available."
  exit 2
}

if ($Profile -eq 'full') {
  Write-Host "Starting full dev stack (profile 'full')..."
  $cmd = "docker compose -f '$composeFile' --profile full up"
} else {
  Write-Host "Starting minimal dev stack (app container only)..."
  $cmd = "docker compose -f '$composeFile' up"
}

if ($Build) { $cmd += " --build" }

Write-Host "Running: $cmd"
Invoke-Expression $cmd
