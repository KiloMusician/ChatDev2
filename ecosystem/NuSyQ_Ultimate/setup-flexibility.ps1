# NuSyQ Flexibility Enhancement and GitHub Authentication Setup
# ============================================================

Write-Host "🔧 NuSyQ Flexibility Enhancement" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# 1. Install GitHub CLI if not present
Write-Host "1. Checking GitHub CLI..." -ForegroundColor Yellow
try {
    gh --version | Out-Null
    Write-Host "   ✅ GitHub CLI is installed" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Installing GitHub CLI..." -ForegroundColor Yellow
    winget install --id GitHub.cli -e
    Write-Host "   ✅ GitHub CLI installed" -ForegroundColor Green
}

# 2. Authenticate with GitHub as KiloMusician
Write-Host "2. GitHub Authentication..." -ForegroundColor Yellow
try {
    $authStatus = gh auth status 2>&1
    if ($authStatus -match "Logged in") {
        Write-Host "   ✅ Already authenticated with GitHub" -ForegroundColor Green
    } else {
        Write-Host "   🔐 Please authenticate with GitHub..." -ForegroundColor Cyan
        Write-Host "   Use your KiloMusician account when prompted" -ForegroundColor Cyan
        gh auth login
    }
} catch {
    Write-Host "   🔐 Setting up GitHub authentication..." -ForegroundColor Cyan
    gh auth login
}

# 3. Create flexible configuration system
Write-Host "3. Creating flexible configuration system..." -ForegroundColor Yellow

# Environment Configuration
$envConfig = @{
    "GITHUB_USER" = "KiloMusician"
    "NUSYQ_ROOT" = $PWD.Path
    "PYTHON_PATH" = (Get-Command python -ErrorAction SilentlyContinue).Source
    "NODE_PATH" = (Get-Command node -ErrorAction SilentlyContinue).Source
    "DOCKER_AVAILABLE" = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)
    "KUBECTL_AVAILABLE" = $null -ne (Get-Command kubectl -ErrorAction SilentlyContinue)
}

# Save environment configuration
$envConfig | ConvertTo-Json -Depth 3 | Out-File -FilePath "config/environment.json" -Encoding UTF8
Write-Host "   ✅ Environment configuration saved" -ForegroundColor Green

# 4. Update VS Code settings with GitHub authentication
Write-Host "4. Configuring VS Code extensions..." -ForegroundColor Yellow

$vscodeSettings = Get-Content ".vscode/settings.json" -Raw | ConvertFrom-Json -AsHashtable

# Add GitHub-specific settings
$vscodeSettings["github.copilot.enable"]["*"] = $true
$vscodeSettings["github.username"] = "KiloMusician"
$vscodeSettings["git.defaultRemote"] = "origin"
$vscodeSettings["git.rememberCredentials"] = $true

# Add flexible path configurations
$vscodeSettings["python.defaultInterpreterPath"] = "${workspaceFolder}/.venv/Scripts/python.exe"
$vscodeSettings["python.analysis.extraPaths"] += @(
    "${workspaceFolder}/config",
    "${workspaceFolder}/mcp_server"
)

# Enhanced AI orchestration
$vscodeSettings["continue.models"] = @{
    "default" = "ollama/codellama:latest"
    "tabAutocomplete" = "ollama/deepseek-coder:latest"
}

# Save updated settings
$vscodeSettings | ConvertTo-Json -Depth 10 | Out-File -FilePath ".vscode/settings.json" -Encoding UTF8
Write-Host "   ✅ VS Code settings updated" -ForegroundColor Green

# 5. Install and configure essential extensions
Write-Host "5. Installing essential extensions..." -ForegroundColor Yellow

$extensions = @(
    "ms-python.python",
    "ms-toolsai.jupyter",
    "GitHub.copilot",
    "GitHub.copilot-chat",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "ms-vscode.powershell",
    "continue.continue",
    "anthropic.claude-dev",
    "ms-kubernetes-tools.vscode-kubernetes-tools",
    "ms-vscode-remote.remote-containers",
    "GitKraken.gitlens"
)

foreach ($ext in $extensions) {
    try {
        code --install-extension $ext --force
        Write-Host "   ✅ $ext installed" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️ Failed to install $ext" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Restart VS Code to apply all settings" -ForegroundColor White
Write-Host "2. Extensions will authenticate automatically" -ForegroundColor White
Write-Host "3. GitHub Copilot should be linked to KiloMusician account" -ForegroundColor White
Write-Host "4. Run the flexibility validation script" -ForegroundColor White
