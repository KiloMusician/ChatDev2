<#
.SYNOPSIS
  Lightweight Docker cleanup helper: stops & removes exited containers, prunes dangling images

.DESCRIPTION
  Intended as a safe, interactive helper to tidy up local Docker state during development.
  It lists stopped containers and dangling images, prompts for confirmation, then removes them.
#>

param(
    [switch]$Force
)

Write-Host "Docker cleanup helper" -ForegroundColor Cyan

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "docker CLI not found on PATH. Install Docker Desktop and ensure 'docker' is available." -ForegroundColor Red
    exit 1
}

# List stopped containers
$stopped = docker ps -a --filter "status=exited" --format "{{.ID}} {{.Image}} {{.Status}} {{.Names}}"
if ($stopped) {
    Write-Host "Stopped containers:" -ForegroundColor Yellow
    $stopped | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "No stopped containers found." -ForegroundColor Green
}

# List dangling images
$dangling = docker images --filter "dangling=true" --format "{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}"
if ($dangling) {
    Write-Host "Dangling images:" -ForegroundColor Yellow
    $dangling | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "No dangling images found." -ForegroundColor Green
}

if (-not $Force) {
    Write-Host "`nRun cleanup? This will remove stopped containers and dangling images. (y/N)" -NoNewline
    $ans = Read-Host
    if ($ans.ToLower() -ne 'y') {
        Write-Host "Aborting cleanup." -ForegroundColor Yellow
        exit 0
    }
}

# Remove stopped containers
if ($stopped) {
    Write-Host "Removing stopped containers..." -ForegroundColor Cyan
    docker ps -a --filter "status=exited" -q | ForEach-Object { docker rm $_ } | ForEach-Object { Write-Host "Removed container $_" }
}

# Prune dangling images
if ($dangling) {
    Write-Host "Pruning dangling images..." -ForegroundColor Cyan
    docker image prune -f
}

Write-Host "Docker cleanup complete." -ForegroundColor Green
Write-Host "You can run 'docker system df' to inspect reclaimed space." -ForegroundColor Cyan
