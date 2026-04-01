<#
PowerShell helper to stop the development stack and optionally prune volumes/images.
Usage:
  .\scripts\dev_stop.ps1            # stop minimal
  .\scripts\dev_stop.ps1 -Profile full -Prune # stop full stack and prune volumes
#>
param(
  [ValidateSet('minimal','full')]
  [string]$Profile = 'minimal',
  [switch]$Prune
)

Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Definition)
$repoRoot = Resolve-Path ..
$composeFile = Join-Path $repoRoot 'deploy/docker-compose.dev.yml'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Error "Docker CLI not found in PATH."
  exit 2
}

if ($Profile -eq 'full') {
  Write-Host "Stopping full dev stack..."
  $cmd = "docker compose -f '$composeFile' --profile full down"
} else {
  Write-Host "Stopping minimal dev stack..."
  $cmd = "docker compose -f '$composeFile' down"
}

Write-Host "Running: $cmd"
Invoke-Expression $cmd

if ($Prune) {
  Write-Host "Pruning unused volumes and images..."
  docker volume prune -f
  docker image prune -f
}
