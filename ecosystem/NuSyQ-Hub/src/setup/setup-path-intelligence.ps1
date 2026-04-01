# Path Intelligence Setup

Write-Host "🛣️ Setting up KILO-FOOLISH Path Intelligence..." -ForegroundColor Magenta

# Create required directories
$directories = @(
    ".\src\core",
    ".\data\logs"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force
        Write-Host "✅ Created: $dir" -ForegroundColor Green
    }
}

# Run initial path analysis
Write-Host "🔍 Running initial path intelligence analysis..." -ForegroundColor Cyan
.\src\core\PathIntelligence.ps1 -Report

# Create smart aliases
Write-Host "🎯 Creating smart path aliases..." -ForegroundColor Cyan
.\src\core\PathIntelligence.ps1 -Aliases

Write-Host "`n✅ Path Intelligence setup complete!" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "🎯 What's now available:" -ForegroundColor Cyan
Write-Host "  🔍 Intelligent path searching" -ForegroundColor White
Write-Host "  🛣️ Smart path resolution with context" -ForegroundColor White
Write-Host "  🎯 Automatic smart aliases" -ForegroundColor White
Write-Host "  🚀 Path optimization analysis" -ForegroundColor White
Write-Host "  📊 Comprehensive path reporting" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "🚀 Usage:" -ForegroundColor Yellow
Write-Host "  Find-KILOPath 'coordinator'" -ForegroundColor White
Write-Host "  Resolve-KILOPath 'config.json'" -ForegroundColor White
Write-Host "  . .\PathAliases.ps1  # Load smart aliases" -ForegroundColor White
