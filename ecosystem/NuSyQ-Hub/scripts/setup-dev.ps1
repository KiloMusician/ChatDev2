<#
Simple dev environment setup script for local development.
This script ensures dev deps are installed and optionally installs workspace recommended extensions.
#>
param (
    [switch]$InstallExtensions = $false,
    [switch]$InstallDevRequirements = $true,
    [switch]$AutoInstallLocalExtensions = $false,
    [switch]$InstallRecommendedOptional = $false
)

if ($InstallDevRequirements) {
    Write-Host "Install dev packages (dev-requirements.txt)" -ForegroundColor Cyan
    python -m pip install --upgrade pip
    if (Test-Path "dev-requirements.txt") {
        python -m pip install -r dev-requirements.txt
    } else {
        Write-Warning "dev-requirements.txt not found; skipping pip install."
    }
}

if ($InstallExtensions) {
    Write-Host "Installing recommended VS Code extensions for workspace" -ForegroundColor Cyan
    $script = Join-Path -Path $PSScriptRoot -ChildPath "install-vscode-extensions.ps1"
    if (Test-Path $script) {
        $args = "-WorkspaceRoot", (Get-Location)
        if ($InstallRecommendedOptional) { $args += "-InstallOptional" }
        & $script @args
    } else {
        Write-Warning "Extension installer script not found: $script"
    }
}

Write-Host "Checking for local LLM tooling (Ollama & ChatDev)" -ForegroundColor Cyan
if (Get-Command -Name ollama -ErrorAction SilentlyContinue) {
    Write-Host "✔ ollama CLI found." -ForegroundColor Green
} else {
    Write-Warning "ollama CLI not found. Install from https://ollama.com or set up local models if required."
}

$chatdevPath = $env:CHATDEV_PATH
if ($chatdevPath) {
    if (Test-Path $chatdevPath) {
        Write-Host "✔ CHATDEV_PATH set and found: $chatdevPath" -ForegroundColor Green
    } else {
        Write-Warning "CHATDEV_PATH set but path not found: $chatdevPath"
    }
} else {
    Write-Host "CHATDEV_PATH not set. To be able to use ChatDev integration, set CHATDEV_PATH in your environment." -ForegroundColor Yellow
}

if ($AutoInstallLocalExtensions) {
    Write-Host "Attempting to install local extensions (packaging with vsce if needed)..." -ForegroundColor Cyan
    $script = Join-Path -Path $PSScriptRoot -ChildPath "install-vscode-extensions.ps1"
    if (Test-Path $script) {
        & $script -WorkspaceRoot (Get-Location)
    } else {
        Write-Warning "Extension installer script not found: $script"
    }
}

# If .devcontainer/.env.example exists, assist by creating .devcontainer/.env from example (without secrets)
if ((Test-Path ".devcontainer/.env.example") -and -not (Test-Path ".devcontainer/.env")) {
    Copy-Item -Path ".devcontainer/.env.example" -Destination ".devcontainer/.env" -Force
    Write-Host "Created .devcontainer/.env from example. Update it with any secrets you need." -ForegroundColor Green
}

Write-Host "Setup complete. Remember to configure secrets and APIs in .env or config/secrets.json." -ForegroundColor Green
