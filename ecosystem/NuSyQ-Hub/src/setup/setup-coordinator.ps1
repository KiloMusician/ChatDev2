# Repository Coordinator Setup

Write-Host "🧭 Setting up KILO-FOOLISH Repository Coordinator..." -ForegroundColor Magenta

# Install Python dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
# Remove these - they're built-in to Python:
# pip install hashlib pathlib datetime

# Only install external dependencies if needed:
# pip install watchdog  # Only if using file watching

# Create required directories
$directories = @(
    ".\src\core",
    ".\data\logs",
    ".\data\backups",
    ".\docs\architecture"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force
        Write-Host "✅ Created: $dir" -ForegroundColor Green
    }
}

# Run initial coordination scan
Write-Host "🔍 Running initial repository scan..." -ForegroundColor Cyan
.\src\core\RepositoryCoordinator.ps1 -Scan

Write-Host "`n✅ Repository Coordinator setup complete!" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "🎯 What's now available:" -ForegroundColor Cyan
Write-Host "  🧭 Intelligent file organization" -ForegroundColor White
Write-Host "  🔍 Duplicate detection and cleanup" -ForegroundColor White
Write-Host "  📝 Naming convention enforcement" -ForegroundColor White
Write-Host "  📊 Repository health monitoring" -ForegroundColor White
Write-Host "  🤖 Automated coordination suggestions" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "🚀 Usage:" -ForegroundColor Yellow
Write-Host "  .\src\core\RepositoryCoordinator.ps1 -Scan" -ForegroundColor White
Write-Host "  .\src\core\RepositoryCoordinator.ps1 -Organize -AutoFix" -ForegroundColor White
Write-Host "  .\src\core\RepositoryCoordinator.ps1 -Report" -ForegroundColor White
