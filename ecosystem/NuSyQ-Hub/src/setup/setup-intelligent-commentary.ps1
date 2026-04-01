# Intelligent Commentary System Setup

Write-Host "🧠 Setting up KILO-FOOLISH Intelligent Commentary System..." -ForegroundColor Magenta

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

# Run initial commentary session
Write-Host "🧠 Running initial commentary session..." -ForegroundColor Cyan
.\src\core\IntelligentCommentary.ps1 -Session

# Set up background commentary job
Write-Host "🚀 Setting up background commentary..." -ForegroundColor Cyan
Start-CommentaryJob

Write-Host "`n✅ Intelligent Commentary setup complete!" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "🎯 What's now active:" -ForegroundColor Cyan
Write-Host "  🧠 Intelligent code analysis and commentary" -ForegroundColor White
Write-Host "  ✨ AI-enhanced comment generation" -ForegroundColor White
Write-Host "  🔄 Continuous 5-minute enhancement cycles" -ForegroundColor White
Write-Host "  📊 Commentary intelligence learning system" -ForegroundColor White
Write-Host "  🎯 Copilot-optimized code insights" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "🚀 Management commands:" -ForegroundColor Yellow
Write-Host "  Get-Job -Name '*Commentary*'  # Check status" -ForegroundColor White
Write-Host "  .\src\core\IntelligentCommentary.ps1 -Status" -ForegroundColor White
Write-Host "  .\src\core\IntelligentCommentary.ps1 -Stop" -ForegroundColor White
